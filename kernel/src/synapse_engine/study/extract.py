"""Extract study artifacts from the vault.

Turns retrieved vault material into **flashcards**, **quiz items**, **interview
(STAR) prompts**, or a **key-point summary**. This is the capability the AR
glasses surface consumes (via the REST edge → `apps/glasses-bridge`) to power a
walking quiz / interview drill on the G2's heads-up display.

It mirrors `reason.answer()` exactly (§1, "degradation floors"):

    retrieve top-k chunks  →  try the LLM seam (generative, structured JSON)
                           →  on any miss, fall back to the extractive floor

The generative rung asks the model for strict JSON and parses it; *any* failure
(no `litellm`, dead model, unparseable output) degrades to the floor. The floor
**never fabricates**: flashcard backs are verbatim source sentences, and the
kinds that can't be made honestly offline (quiz distractors, STAR model answers)
degrade to grounded key points rather than inventing content.
"""

from __future__ import annotations

import json
import re

from contracts.models import (
    Citation,
    ExtractResult,
    Flashcard,
    KeyPoint,
    QuizItem,
    STARPrompt,
    StudyKind,
)

from synapse_engine.kb import search
from synapse_engine.llm import complete

# A chunk's source label, reused as the `source` field on every produced item.
_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


# --------------------------------------------------------------------------- #
# Retrieval (shared by both rungs)
# --------------------------------------------------------------------------- #
def _citations(topic: str, k: int) -> list[Citation]:
    return [
        Citation(source=f"{h.title} · {h.path}", score=h.score, snippet=h.snippet)
        for h in search(topic, k=k)
    ]


def _context_block(citations: list[Citation]) -> str:
    return "\n\n".join(f"[{i}] {c.snippet}" for i, c in enumerate(citations, start=1))


def _sentences(citations: list[Citation]) -> list[tuple[str, str]]:
    """Flatten citations into (sentence, source) pairs — the floor's raw material."""
    out: list[tuple[str, str]] = []
    for c in citations:
        for s in _SENTENCE.split(c.snippet):
            s = s.strip().rstrip("…").strip()
            if len(s) >= 25:  # skip fragments too short to be a useful card
                out.append((s, c.source))
    return out


# --------------------------------------------------------------------------- #
# Generative rung — ask the model for strict JSON, parse, or signal a miss
# --------------------------------------------------------------------------- #
_SYSTEM = (
    "You are Synapse, a study-material generator. Using ONLY the numbered context "
    "passages from the user's vault, produce study artifacts grounded in that "
    "material. Never invent facts the context does not support. Respond with ONLY "
    "valid JSON matching the requested schema — no prose, no markdown fences."
)

_SCHEMAS: dict[StudyKind, str] = {
    StudyKind.FLASHCARDS: (
        'a JSON array of {"front": str, "back": str} objects — front is a recall '
        "prompt, back is the concise answer drawn from the context"
    ),
    StudyKind.QUIZ: (
        'a JSON array of {"question": str, "options": [str, ...], "answer_index": int} '
        "objects — 4 options each, exactly one correct, answer_index points to it"
    ),
    StudyKind.INTERVIEW: (
        'a JSON array of {"prompt": str, "situation": str, "task": str, "action": '
        'str, "result": str} objects — an interview question and a STAR model answer'
    ),
    StudyKind.SUMMARY: 'a JSON array of {"point": str} objects — the key takeaways',
}


def _loads_array(text: str) -> list[dict] | None:
    """Tolerantly parse a JSON array out of an LLM response, or None on failure."""
    if not text:
        return None
    fenced = _JSON_FENCE.search(text)
    if fenced:
        text = fenced.group(1)
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        return None
    return data if isinstance(data, list) else None


def _generative(
    kind: StudyKind, topic: str, n: int, citations: list[Citation]
) -> ExtractResult | None:
    """Try the model. Returns a populated result, or None to signal 'use the floor'."""
    prompt = (
        f"Context:\n{_context_block(citations)}\n\n"
        f"Produce {n} items about '{topic}' as {_SCHEMAS[kind]}."
    )
    rows = _loads_array(complete(_SYSTEM, prompt) or "")
    if not rows:
        return None

    result = ExtractResult(kind=kind, citations=citations, mode="generative")
    try:
        if kind is StudyKind.FLASHCARDS:
            result.flashcards = [
                Flashcard(front=str(r["front"]), back=str(r["back"])) for r in rows[:n]
            ]
        elif kind is StudyKind.QUIZ:
            result.quiz = [
                QuizItem(
                    question=str(r["question"]),
                    options=[str(o) for o in r["options"]],
                    answer_index=int(r["answer_index"]),
                )
                for r in rows[:n]
            ]
        elif kind is StudyKind.INTERVIEW:
            result.interview = [
                STARPrompt(
                    prompt=str(r["prompt"]),
                    situation=str(r.get("situation", "")),
                    task=str(r.get("task", "")),
                    action=str(r.get("action", "")),
                    result=str(r.get("result", "")),
                )
                for r in rows[:n]
            ]
        else:  # SUMMARY
            result.key_points = [KeyPoint(point=str(r["point"])) for r in rows[:n]]
    except (KeyError, TypeError, ValueError):
        return None  # malformed item — degrade to the floor rather than half-render
    return result if _any_items(result) else None


def _any_items(r: ExtractResult) -> bool:
    return bool(r.flashcards or r.quiz or r.interview or r.key_points)


# --------------------------------------------------------------------------- #
# Extractive floor — honest, offline, never fabricated
# --------------------------------------------------------------------------- #
def _summary_floor(citations: list[Citation], n: int) -> list[KeyPoint]:
    """Key points = the leading source sentences themselves (verbatim, grounded)."""
    return [KeyPoint(point=s, source=src) for s, src in _sentences(citations)[:n]]


def _flashcard_floor(citations: list[Citation], n: int) -> list[Flashcard]:
    """Offline flashcards built from raw vault text — the never-fabricate floor.

    See the design note where this is called: the *back* of every card MUST be
    verbatim (or trivially trimmed) source text — we may shape the *front* (a
    cloze blank, a heading, a "What is X?" stem), but we never invent the answer.

    TODO(you): implement this heuristic. `_sentences(citations)` gives you
    (sentence, source) pairs already filtered to useful length.
    """
    raise NotImplementedError("flashcard extractive floor — your contribution")


def _floor(kind: StudyKind, topic: str, citations: list[Citation], n: int) -> ExtractResult:
    result = ExtractResult(kind=kind, citations=citations, mode="extractive")
    if not citations:
        return result  # empty vault → empty (honest) result; surfaces render the gap

    if kind is StudyKind.FLASHCARDS:
        result.flashcards = _flashcard_floor(citations, n)
    elif kind is StudyKind.SUMMARY:
        result.key_points = _summary_floor(citations, n)
    else:
        # Quiz distractors and STAR model answers can't be made honestly without a
        # model, so we degrade to grounded key points rather than inventing them.
        result.key_points = _summary_floor(citations, n)
    return result


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def extract(
    topic: str, kind: StudyKind = StudyKind.FLASHCARDS, n: int = 8, k: int = 8
) -> ExtractResult:
    """Extract `n` study artifacts of `kind` about `topic` from the vault.

    Generative when a model is reachable; honest extractive floor otherwise.
    """
    citations = _citations(topic, k=k)
    if citations:
        generated = _generative(kind, topic, n, citations)
        if generated is not None:
            return generated
    return _floor(kind, topic, citations, n)

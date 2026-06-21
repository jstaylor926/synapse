"""LLM — a pluggable seam.

`ExtractiveLLM` (default) does NOT generate; it stitches an answer from the
retrieved snippets, so the engine is useful and honest with zero API keys and
never fabricates. `AnthropicLLM` is the real-generation path (optional extra).
"""
from __future__ import annotations

from typing import Protocol

from ..models import Citation


class LLM(Protocol):
    def answer(self, question: str, context: list[Citation]) -> str: ...


class ExtractiveLLM:
    """No-generation baseline: summarize by extracting the top snippets."""

    def answer(self, question: str, context: list[Citation]) -> str:
        if not context:
            return ("I don't have anything in the knowledge base about that yet. "
                    "Ingest some sources first (synapse ingest <path>).")
        top = context[0]
        lines = [
            f"Based on your knowledge base, the most relevant passage for "
            f"\"{question.strip()}\" is:",
            "",
            f"  {top.snippet.strip()}",
        ]
        if len(context) > 1:
            lines += ["", "Related passages:"]
            lines += [f"  - {c.snippet.strip()[:140]}…" for c in context[1:3]]
        lines += ["", "(Extractive mode — set SYNAPSE_LLM_PROVIDER=anthropic for "
                  "synthesized answers.)"]
        return "\n".join(lines)


class AnthropicLLM:  # pragma: no cover - requires network + key
    def __init__(self, model: str) -> None:
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError("pip install -e '.[llm]' to use the Anthropic provider.") from exc
        self._client = anthropic.Anthropic()
        self._model = model

    def answer(self, question: str, context: list[Citation]) -> str:
        ctx = "\n\n".join(f"[{i+1}] {c.snippet}" for i, c in enumerate(context))
        prompt = (
            "Answer the question using ONLY the context. Cite sources as [n]. "
            "If the context is insufficient, say so.\n\n"
            f"Context:\n{ctx}\n\nQuestion: {question}"
        )
        msg = self._client.messages.create(
            model=self._model, max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text


class LiteLLMProvider:  # pragma: no cover - requires litellm + a backend
    """Unified gateway (the locked stack). Routes to Anthropic for quality, or to
    a local Ollama model when offline — same call site either way. Set
    ``SYNAPSE_LLM_MODEL`` to e.g. ``claude-sonnet-4-6`` or ``ollama/llama3``."""

    def __init__(self, model: str) -> None:
        try:
            import litellm  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("pip install litellm to use the litellm gateway.") from exc
        self._model = model

    def answer(self, question: str, context: list[Citation]) -> str:
        import litellm

        ctx = "\n\n".join(f"[{i + 1}] {c.snippet}" for i, c in enumerate(context))
        prompt = (
            "Answer the question using ONLY the context. Cite sources as [n]. "
            "If the context is insufficient, say so.\n\n"
            f"Context:\n{ctx}\n\nQuestion: {question}"
        )
        resp = litellm.completion(
            model=self._model, max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp["choices"][0]["message"]["content"]


def get_llm(config) -> LLM:
    provider = getattr(config, "llm_provider", "extractive")
    if provider == "extractive":
        return ExtractiveLLM()
    if provider == "anthropic":
        return AnthropicLLM(config.llm_model)
    if provider == "litellm":
        return LiteLLMProvider(config.llm_model)
    raise ValueError(f"Unknown SYNAPSE_LLM_PROVIDER={provider!r}.")

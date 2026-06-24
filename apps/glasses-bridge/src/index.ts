/**
 * @synapse/glasses-bridge — adapts the kernel's REST edge into the compact
 * "spec_view" payloads the AR glasses (Even G2) consume.
 *
 * It owns no business logic: the *intelligence* (what to ask, how to ground it)
 * lives in the kernel's `study.extract` capability. The bridge's job is the
 * G2-specific *interaction shape* — turning a rich `ExtractResult` into an
 * ordered list of glance-able **screens** with a progressive reveal, so a
 * flashcard becomes "prompt → tap → answer" on the heads-up display.
 *
 * Run with `bun run dev`.
 */

import { dueCards, extract, grade, saveFlashcards, searchKb } from "@synapse/client";
import type { ExtractResult, Flashcard, SearchHit, StudyKind } from "@synapse/contracts-ts";

const PORT = Number(process.env.GLASSES_BRIDGE_PORT ?? 4317);
const VALID_KINDS: StudyKind[] = ["flashcards", "quiz", "interview", "summary"];
const LETTERS = "ABCDEFGHIJ";

/** One glance-able unit on the G2 HUD. The device taps through these in order. */
interface Screen {
  kind: StudyKind;
  /** 1-based position in the deck. */
  index: number;
  total: number;
  /** Short header line, e.g. "Flashcard 2/8". */
  title: string;
  /** The visible text for this screen — kept short for the HUD. */
  body: string;
  /** True when this screen reveals the answer (the client can style it). */
  reveal: boolean;
  /** Present on gradable flashcard screens — the SR card id to grade. */
  cardId?: string;
}

/** Reshape a rich SearchHit into a minimal card for the glasses display. */
function toSpecView(hit: SearchHit) {
  return { title: hit.title, body: hit.snippet };
}

/**
 * Build the prompt→reveal screen pair for each flashcard, tagging the *reveal*
 * screen with its SR `cardId` so the glasses can grade it. `ids[i]` aligns with
 * `cards[i]`; an empty `ids` (e.g. SR save failed) just yields ungradable cards.
 */
function flashcardScreens(cards: Flashcard[], ids: string[]): Screen[] {
  const screens: Screen[] = [];
  const total = cards.length;
  cards.forEach((c, i) => {
    const title = `Flashcard ${i + 1}/${total}`;
    const cardId = ids[i];
    screens.push({ kind: "flashcards", index: i + 1, total, title, body: c.front, reveal: false, cardId });
    screens.push({ kind: "flashcards", index: i + 1, total, title, body: `${c.front}\n\n→ ${c.back}`, reveal: true, cardId });
  });
  return screens;
}

/**
 * Paginate an `ExtractResult` into ordered HUD screens with progressive reveal.
 * Each kind has its own rhythm; `total` is the number of *source items*, so the
 * device can show "2/8" while a single item may span multiple screens.
 * `ids` (flashcards only) carries the SR card ids onto the reveal screens.
 */
function paginate(result: ExtractResult, ids: string[] = []): Screen[] {
  const screens: Screen[] = [];
  const push = (s: Omit<Screen, "kind">) => screens.push({ kind: result.kind, ...s });

  if (result.kind === "flashcards") {
    return flashcardScreens(result.flashcards, ids);
  } else if (result.kind === "quiz") {
    const total = result.quiz.length;
    result.quiz.forEach((q, i) => {
      const title = `Quiz ${i + 1}/${total}`;
      const opts = q.options.map((o, j) => `${LETTERS[j]}. ${o}`).join("\n");
      push({ index: i + 1, total, title, body: `${q.question}\n${opts}`, reveal: false });
      const correct = q.options[q.answer_index] ?? "";
      push({
        index: i + 1,
        total,
        title,
        body: `Answer: ${LETTERS[q.answer_index] ?? "?"}. ${correct}`,
        reveal: true,
      });
    });
  } else if (result.kind === "interview") {
    const total = result.interview.length;
    result.interview.forEach((p, i) => {
      const title = `Interview ${i + 1}/${total}`;
      push({ index: i + 1, total, title, body: p.prompt, reveal: false });
      // One STAR section per tap — skip any the model (or floor) left empty.
      const star: Array<[string, string]> = [
        ["Situation", p.situation],
        ["Task", p.task],
        ["Action", p.action],
        ["Result", p.result],
      ];
      for (const [label, text] of star) {
        if (text.trim()) {
          push({ index: i + 1, total, title, body: `${label}: ${text}`, reveal: true });
        }
      }
    });
  } else {
    // summary — one key point per screen (also the offline fallback for quiz/STAR)
    const total = result.key_points.length;
    result.key_points.forEach((kp, i) => {
      push({ index: i + 1, total, title: `Key point ${i + 1}/${total}`, body: kp.point, reveal: false });
    });
  }

  return screens;
}

const server = Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);

    if (url.pathname === "/healthz") {
      return Response.json({ status: "ok" });
    }

    if (url.pathname === "/spec_view/search") {
      const q = url.searchParams.get("q") ?? "";
      const hits = await searchKb(q);
      return Response.json({ cards: hits.map(toSpecView) });
    }

    if (url.pathname === "/spec_view/study") {
      const n = Number(url.searchParams.get("n") ?? 8);

      // Review mode: serve cards already due in the SR store (no extraction).
      // `topic` optionally scopes to one deck; absent ⇒ everything due.
      if (url.searchParams.get("mode") === "due") {
        const deck = url.searchParams.get("topic")?.trim() || undefined;
        const due = await dueCards(deck, n);
        if (!due.length) {
          return Response.json({
            topic: deck ?? "due",
            kind: "flashcards",
            mode: "review",
            screens: [{
              kind: "flashcards", index: 1, total: 1,
              title: "All caught up", body: "No cards due right now.\nStudy a topic to add some.",
              reveal: false,
            }],
          });
        }
        const screens = flashcardScreens(
          due.map((c): Flashcard => ({ front: c.front, back: c.back })),
          due.map((c) => c.id),
        );
        return Response.json({ topic: deck ?? "due", kind: "flashcards", mode: "review", screens });
      }

      const topic = url.searchParams.get("topic") ?? "";
      if (!topic.trim()) {
        return Response.json({ error: "missing ?topic" }, { status: 400 });
      }
      const kindParam = url.searchParams.get("kind") ?? "flashcards";
      const kind = (VALID_KINDS as string[]).includes(kindParam)
        ? (kindParam as StudyKind)
        : "flashcards";

      const result = await extract(topic, kind, n);
      // Persist flashcards into the SR store so the deck is gradable; the ids
      // ride back on the reveal screens. Other kinds aren't graded (yet).
      let ids: string[] = [];
      if (result.kind === "flashcards" && result.flashcards.length) {
        try {
          ids = await saveFlashcards(topic, result.flashcards);
        } catch {
          /* SR save failed — fall through with ungradable cards, deck still works */
        }
      }
      const screens = paginate(result, ids);
      // `mode` lets the HUD show whether these are generated or the offline floor.
      return Response.json({ topic, kind, mode: result.mode, screens });
    }

    // Grade a review from the glasses: { card_id, rating: 1..4 } → next due.
    if (url.pathname === "/grade" && req.method === "POST") {
      try {
        const { card_id, rating } = (await req.json()) as { card_id: string; rating: number };
        if (!card_id || !(rating >= 1 && rating <= 4)) {
          return Response.json({ error: "need card_id and rating 1..4" }, { status: 400 });
        }
        return Response.json(await grade(card_id, rating));
      } catch (err) {
        return Response.json({ error: String(err) }, { status: 502 });
      }
    }

    return new Response("Not found", { status: 404 });
  },
});

console.log(`[glasses-bridge] listening on http://localhost:${server.port}`);

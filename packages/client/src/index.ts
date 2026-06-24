/**
 * @synapse/client — the single typed entry point every surface uses to reach
 * the kernel's REST edge (FastAPI, default http://127.0.0.1:8765).
 *
 * Centralizing the base URL and the request/response typing here means the
 * cockpit, CLI, glasses bridge, and editor extensions never hand-roll `fetch`
 * and can't drift from the Pydantic contracts (mirrored in @synapse/contracts-ts).
 */
import type {
  DueResult,
  ExtractResult,
  Flashcard,
  GradeResult,
  ReasonAnswer,
  ReviewCard,
  SaveCardsResult,
  SearchHit,
  StudyKind,
} from "@synapse/contracts-ts";

const DEFAULT_BASE = "http://127.0.0.1:8765";

function detectBase(): string {
  // Vite (browser / Tauri webview) inlines import.meta.env at build time.
  try {
    const env = (import.meta as unknown as { env?: Record<string, string> }).env;
    if (env?.VITE_SYNAPSE_API_BASE) return env.VITE_SYNAPSE_API_BASE;
  } catch {
    // import.meta.env is undefined outside a Vite build — fall through.
  }
  // Bun / Node surfaces (CLI, glasses bridge).
  const proc = (globalThis as { process?: { env?: Record<string, string> } }).process;
  if (proc?.env?.SYNAPSE_API_BASE) return proc.env.SYNAPSE_API_BASE;
  return DEFAULT_BASE;
}

let apiBase = detectBase();

/** The REST edge base URL currently in use. */
export function getApiBase(): string {
  return apiBase;
}

/** Override the REST edge base URL (e.g. when packaging points at a sidecar). */
export function setApiBase(url: string): void {
  apiBase = url.replace(/\/+$/, "");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBase}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(
      `Synapse ${path} → ${res.status} ${res.statusText}${detail ? `: ${detail}` : ""}`,
    );
  }
  return (await res.json()) as T;
}

export interface Health {
  status: string;
  version: string;
  vault_dir: string;
}

/** Liveness + active vault of the kernel REST edge. */
export function health(): Promise<Health> {
  return request<Health>("/health");
}

/** Hybrid (currently BM25-floor) search over the Markdown vault. */
export async function searchKb(query: string, k = 8): Promise<SearchHit[]> {
  const params = new URLSearchParams({ q: query, k: String(k) });
  const { hits } = await request<{ query: string; hits: SearchHit[] }>(`/kb/search?${params}`);
  return hits;
}

/** Grounded, cited answer over the vault (extractive floor until the LLM lands). */
export function ask(question: string, k = 8): Promise<ReasonAnswer> {
  return request<ReasonAnswer>("/reason/ask", {
    method: "POST",
    body: JSON.stringify({ question, k }),
  });
}

/** Grounded coding help over your ingested code + docs — same shape as `ask`. */
export function codeAssist(query: string, k = 8): Promise<ReasonAnswer> {
  return request<ReasonAnswer>("/code/assist", {
    method: "POST",
    body: JSON.stringify({ question: query, k }),
  });
}

/**
 * Extract study artifacts (flashcards / quiz / interview STAR / summary) from
 * vault material on `topic`. Generative when a model is reachable, honest
 * extractive floor otherwise — the AR glasses surface consumes this.
 */
export function extract(
  topic: string,
  kind: StudyKind = "flashcards",
  n = 8,
  k = 8,
): Promise<ExtractResult> {
  return request<ExtractResult>("/study/extract", {
    method: "POST",
    body: JSON.stringify({ topic, kind, n, k }),
  });
}

/**
 * Persist a generated flashcard deck into the spaced-repetition store so its
 * cards become gradable. Idempotent: card ids are a content hash, so re-saving
 * the same deck returns the existing ids and never resets a card's schedule.
 */
export async function saveFlashcards(deck: string, cards: Flashcard[]): Promise<string[]> {
  const { ids } = await request<SaveCardsResult>("/study/save", {
    method: "POST",
    body: JSON.stringify({ deck, cards }),
  });
  return ids;
}

/** Cards due for review now, most-urgent first (optionally scoped to a deck). */
export async function dueCards(deck?: string, limit = 20): Promise<ReviewCard[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (deck) params.set("deck", deck);
  const { cards } = await request<DueResult>(`/study/due?${params}`);
  return cards;
}

/** Grade a review (1=Again, 2=Hard, 3=Good, 4=Easy); returns the next due time. */
export function grade(cardId: string, rating: number): Promise<GradeResult> {
  return request<GradeResult>("/study/grade", {
    method: "POST",
    body: JSON.stringify({ card_id: cardId, rating }),
  });
}

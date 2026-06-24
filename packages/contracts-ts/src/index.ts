/**
 * TypeScript mirror of the kernel's Pydantic contracts.
 *
 * Source of truth: `kernel/contracts/models.py`. Keep these in lockstep — when
 * the Python models change, update this file (or regenerate it; see README).
 * Every surface (cockpit, glasses, CLI, extensions) imports its types from here
 * so the UI and the backend never drift.
 */

export interface SearchHit {
  doc_id: string;
  /** Vault-relative Markdown path. */
  title: string;
  path: string;
  snippet: string;
  score: number;
}

export type JobStatus = "queued" | "running" | "done" | "failed";

export interface Job {
  id: string;
  /** e.g. "ingest_web", "ingest_pdf", "transcribe". */
  kind: string;
  payload: Record<string, unknown>;
  status: JobStatus;
  attempts: number;
  error: string | null;
  created_at: string | null;
}

export interface Task {
  id: string;
  title: string;
  done: boolean;
  due: string | null;
  topic: string | null;
}

export interface ReviewCard {
  id: string;
  front: string;
  back: string;
  due: string | null;
  stability: number;
  difficulty: number;
}

/** A pointer back to a source chunk — one shape wherever a citation appears. */
export interface Citation {
  source: string;
  score: number;
  snippet: string;
}

export interface ReasonAsk {
  question: string;
  k?: number;
}

/** A grounded answer with citations back to source chunks (never fabricated). */
export interface ReasonAnswer {
  answer: string;
  citations: Citation[];
  /** Present only for multi-step reasoning — the decomposed sub-questions. */
  steps?: string[] | null;
  /** Degradation rung: "extractive" (no LLM) or "generative". */
  mode: string;
}

/** The shape of study artifact `study_extract` should produce. */
export type StudyKind = "flashcards" | "quiz" | "interview" | "summary";

/** A front/back recall pair. Front is the prompt, back is the answer. */
export interface Flashcard {
  front: string;
  back: string;
  /** Vault path/title it came from. */
  source?: string | null;
}

/** A multiple-choice question. `options` includes the correct answer. */
export interface QuizItem {
  question: string;
  options: string[];
  /** Index into `options` of the correct answer. */
  answer_index: number;
  source?: string | null;
}

/** An interview prompt with a STAR-structured model answer. */
export interface STARPrompt {
  prompt: string;
  situation: string;
  task: string;
  action: string;
  result: string;
  source?: string | null;
}

/** A single bulleted takeaway from the source material. */
export interface KeyPoint {
  point: string;
  source?: string | null;
}

/** Request body for `study_extract` — turn vault material into study artifacts. */
export interface ExtractRequest {
  /** Topic/query used to retrieve source chunks from the vault. */
  topic: string;
  kind?: StudyKind;
  /** How many items to produce. */
  n?: number;
  /** How many vault chunks to retrieve as source. */
  k?: number;
}

/**
 * Study artifacts extracted from the vault. Exactly one list is populated,
 * matching `kind`. Grounded in `citations`; `mode` is the degradation rung.
 */
export interface ExtractResult {
  kind: StudyKind;
  flashcards: Flashcard[];
  quiz: QuizItem[];
  interview: STARPrompt[];
  key_points: KeyPoint[];
  citations: Citation[];
  mode: string;
}

// --- Spaced repetition (review loop) --------------------------------------- //

/** Persist generated flashcards so they become gradable (idempotent by content). */
export interface SaveCardsRequest {
  /** Deck name — usually the study topic. */
  deck: string;
  cards: Flashcard[];
}

/** The stable card ids for the saved deck, in input order. */
export interface SaveCardsResult {
  ids: string[];
}

/** Grade one review. `rating`: 1=Again, 2=Hard, 3=Good, 4=Easy. */
export interface GradeRequest {
  card_id: string;
  rating: number;
}

/** Outcome of a grade — when the card is next due, with a HUD-ready label. */
export interface GradeResult {
  card_id: string;
  next_due: string;
  /** Human delta until next review, e.g. "10m", "2d". */
  interval: string;
  /** new | learning | review | relearning. */
  state: string;
}

/** Cards due for review now, most-urgent first. */
export interface DueResult {
  cards: ReviewCard[];
}

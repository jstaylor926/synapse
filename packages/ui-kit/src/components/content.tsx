/**
 * Neo-Gonzo Noir — content blocks.
 *
 * Higher-level, still-presentational pieces that compose the primitives into
 * the recurring shapes of the cockpit: chat bubbles, citations, code blocks,
 * flashcards, FSRS rating row, and the newsprint cheatsheet/PDF surface.
 */
import type { ReactNode } from "react";
import { Icon } from "../icons";
import { ProgressBar } from "./primitives";
import { GrainOverlay } from "./effects";

function cx(...parts: (string | false | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

/* --------------------------------- ChatBubble --------------------------------- */

export interface ChatBubbleProps {
  role: "user" | "agent";
  /** Display name for the agent header (defaults to "SYNAPSE"). */
  name?: string;
  children: ReactNode;
  /** Footer slot under an agent message (e.g. grounding note). */
  footer?: ReactNode;
  className?: string;
}

export function ChatBubble({ role, name = "SYNAPSE", children, footer, className }: ChatBubbleProps) {
  return (
    <div className={cx("syn-bubble", `syn-bubble--${role}`, className)}>
      {role === "user" ? (
        <div className="syn-bubble__role">YOU</div>
      ) : (
        <div className="syn-bubble__role" style={{ marginBottom: 11 }}>
          <span className="syn-bubble__dot" />
          <span className="syn-bubble__role-name">{name}</span>
        </div>
      )}
      <div className="syn-bubble__body">{children}</div>
      {footer && (
        <div
          style={{
            marginTop: 14,
            paddingTop: 12,
            borderTop: "1px solid var(--syn-divider)",
            display: "flex",
            alignItems: "center",
            gap: 8,
            fontFamily: "var(--syn-font-mono)",
            fontSize: 10.5,
            color: "var(--syn-text-fainter)",
          }}
        >
          {footer}
        </div>
      )}
    </div>
  );
}

/* -------------------------------- CitationCard -------------------------------- */

export interface CitationCardProps {
  index: number | string;
  source: ReactNode;
  quote: ReactNode;
  /** 0–1 relevance score. */
  score: number;
}

export function CitationCard({ index, source, quote, score }: CitationCardProps) {
  return (
    <div className="syn-citation">
      <div className="syn-citation__head">
        <span className="syn-citation__index">{index}</span>
        <span className="syn-citation__source">{source}</span>
      </div>
      <div className="syn-citation__quote">{quote}</div>
      <div className="syn-citation__score">
        <ProgressBar value={score * 100} />
        <span className="syn-citation__score-val">{score.toFixed(2)}</span>
      </div>
    </div>
  );
}

/* ---------------------------------- CodeBlock --------------------------------- */

export interface CodeBlockProps {
  /** Filename · language shown in the window chrome. */
  filename: ReactNode;
  /** Right-aligned actions in the header (e.g. a "SAVE TO KB" button). */
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function CodeBlock({ filename, actions, children, className }: CodeBlockProps) {
  return (
    <div className={cx("syn-code", className)}>
      <div className="syn-code__head">
        <span className="syn-code__dots">
          <span className="syn-code__dot" />
          <span className="syn-code__dot" />
        </span>
        <span className="syn-code__name">{filename}</span>
        {actions}
      </div>
      <pre className="syn-code__body">{children}</pre>
    </div>
  );
}

/* ---------------------------------- Flashcard --------------------------------- */

export interface FlashcardProps {
  front: ReactNode;
  back: ReactNode;
  source?: ReactNode;
  className?: string;
}

export function Flashcard({ front, back, source, className }: FlashcardProps) {
  return (
    <div className={cx("syn-flashcard", className)}>
      <div className="syn-flashcard__label">FRONT</div>
      <div className="syn-flashcard__front">{front}</div>
      <div className="syn-flashcard__rule" />
      <div className="syn-flashcard__back-label">BACK</div>
      <div className="syn-flashcard__back">{back}</div>
      <div style={{ flex: 1 }} />
      {source && (
        <div className="syn-flashcard__source">
          <span className="syn-dot syn-dot--accent" />
          {source}
        </div>
      )}
    </div>
  );
}

/* -------------------------------- RatingButtons ------------------------------- */
/** The FSRS-6 review row — Again / Hard / Good / Easy with next-interval hints. */

export type FsrsRating = "again" | "hard" | "good" | "easy";

const RATINGS: { id: FsrsRating; key: string }[] = [
  { id: "again", key: "AGAIN" },
  { id: "hard", key: "HARD" },
  { id: "good", key: "GOOD" },
  { id: "easy", key: "EASY" },
];

export interface RatingButtonsProps {
  /** Map of rating → interval label, e.g. `{ again: "< 1m", good: "2d" }`. */
  intervals?: Partial<Record<FsrsRating, ReactNode>>;
  onRate?: (rating: FsrsRating) => void;
}

export function RatingButtons({ intervals = {}, onRate }: RatingButtonsProps) {
  return (
    <div className="syn-ratings">
      {RATINGS.map(({ id, key }) => (
        <button key={id} className={cx("syn-rating", `syn-rating--${id}`)} onClick={() => onRate?.(id)}>
          <div className="syn-rating__key">{key}</div>
          <div className="syn-rating__interval">{intervals[id] ?? "—"}</div>
        </button>
      ))}
    </div>
  );
}

/* -------------------------------- NewsprintCard ------------------------------- */
/** Paper surface for cheatsheets and the PDF viewer — warm stock + multiply grain. */

export interface NewsprintCardProps {
  title?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function NewsprintCard({ title, children, className }: NewsprintCardProps) {
  return (
    <div className={cx("syn-newsprint", className)}>
      <GrainOverlay opacity={0.09} />
      {title && <div className="syn-newsprint__title">{title}</div>}
      <div className="syn-newsprint__body">{children}</div>
    </div>
  );
}

/* A convenience "SAVE TO KB" style action used in the code-block header. */
export function SaveToKbButton({ label = "SAVE TO KB" }: { label?: string }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        fontFamily: "var(--syn-font-mono)",
        fontSize: 10,
        fontWeight: 700,
        color: "var(--syn-text-on-accent)",
        background: "var(--syn-accent)",
        padding: "5px 10px",
        borderRadius: 5,
        boxShadow: "var(--syn-shadow-offset-sm)",
      }}
    >
      <Icon name="save" size={11} strokeWidth={2} />
      {label}
    </span>
  );
}

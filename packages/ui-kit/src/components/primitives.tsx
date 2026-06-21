/**
 * Neo-Gonzo Noir — primitives.
 *
 * The small, composable building blocks: buttons, badges, tags, cards, and the
 * typographic helpers (eyebrow, page header, divider). These are presentational
 * placeholders — interactivity lands in a later milestone.
 */
import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";
import { Icon } from "../icons";

type Tone = "neutral" | "accent" | "success" | "purple" | "danger";

function cx(...parts: (string | false | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

/* ----------------------------------- Button ----------------------------------- */

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md";
  block?: boolean;
}

export function Button({
  variant = "secondary",
  size = "md",
  block = false,
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cx(
        "syn-btn",
        `syn-btn--${variant}`,
        size === "sm" && "syn-btn--sm",
        block && "syn-btn--block",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

/* ----------------------------------- Badge ------------------------------------ */
/** Status pill: a dot + mono label. Used for job/engine/mode chips. */

export interface BadgeProps extends HTMLAttributes<HTMLDivElement> {
  tone?: Tone;
  /** Show a leading status dot. */
  dot?: boolean;
  /** Pulse the dot (e.g. a running job). */
  pulse?: boolean;
}

export function Badge({
  tone = "neutral",
  dot = true,
  pulse = false,
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <div
      className={cx("syn-badge", tone !== "neutral" && `syn-badge--${tone}`, className)}
      {...props}
    >
      {dot && (
        <span
          className={cx("syn-dot", `syn-dot--${tone === "neutral" ? "accent" : tone}`, pulse && "syn-dot--pulse")}
        />
      )}
      {children}
    </div>
  );
}

/* ------------------------------------ Tag ------------------------------------- */
/** Small mono chip — wikilinks, scope items, file-type labels. */

export interface TagProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

export function Tag({ tone = "neutral", className, children, ...props }: TagProps) {
  return (
    <span className={cx("syn-tag", `syn-tag--${tone}`, className)} {...props}>
      {children}
    </span>
  );
}

/* ------------------------------------ Card ------------------------------------ */

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "sunken" | "active" | "accent-edge" | "dashed" | "dashed-purple";
}

export function Card({ variant = "default", className, children, ...props }: CardProps) {
  return (
    <div
      className={cx("syn-card", variant !== "default" && `syn-card--${variant}`, className)}
      {...props}
    >
      {children}
    </div>
  );
}

/* ------------------------------------ Kbd ------------------------------------- */

export function Kbd({ children }: { children: ReactNode }) {
  return <span className="syn-kbd">{children}</span>;
}

/* ----------------------------------- Stamp ------------------------------------ */
/** A rotated rubber-stamp flourish — "DUE · 06·27", etc. */

export interface StampProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: "danger" | "accent";
}

export function Stamp({ tone = "danger", className, children, ...props }: StampProps) {
  return (
    <span className={cx("syn-stamp", tone === "accent" && "syn-stamp--accent", className)} {...props}>
      {children}
    </span>
  );
}

/* --------------------------------- ProgressBar -------------------------------- */

export interface ProgressBarProps {
  /** 0–100 */
  value: number;
  tall?: boolean;
  className?: string;
}

export function ProgressBar({ value, tall = false, className }: ProgressBarProps) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div
      className={cx("syn-progress", tall && "syn-progress--tall", className)}
      role="progressbar"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div className="syn-progress__fill" style={{ width: `${pct}%` }} />
    </div>
  );
}

/* ------------------------------ SegmentedControl ------------------------------ */

export interface SegmentedControlProps {
  options: string[];
  value: string;
  onChange?: (value: string) => void;
  block?: boolean;
  className?: string;
}

export function SegmentedControl({
  options,
  value,
  onChange,
  block = false,
  className,
}: SegmentedControlProps) {
  return (
    <div className={cx("syn-segmented", block && "syn-segmented--block", className)} role="tablist">
      {options.map((opt) => (
        <button
          key={opt}
          role="tab"
          aria-selected={opt === value}
          className={cx("syn-segmented__item", opt === value && "syn-segmented__item--active")}
          onClick={() => onChange?.(opt)}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

/* ----------------------------------- Stepper ---------------------------------- */

export interface StepperProps {
  value: number;
  onChange?: (value: number) => void;
  min?: number;
  max?: number;
  className?: string;
}

export function Stepper({ value, onChange, min = 0, max = 999, className }: StepperProps) {
  return (
    <div className={cx("syn-stepper", className)}>
      <button
        className="syn-stepper__btn"
        aria-label="Decrease"
        onClick={() => onChange?.(Math.max(min, value - 1))}
      >
        −
      </button>
      <span className="syn-stepper__value">{value}</span>
      <button
        className="syn-stepper__btn"
        aria-label="Increase"
        onClick={() => onChange?.(Math.min(max, value + 1))}
      >
        +
      </button>
    </div>
  );
}

/* ----------------------------------- Eyebrow ---------------------------------- */
/** The tracked mono label that sits above sections and headers. */

export function Eyebrow({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cx("syn-eyebrow", className)} {...props}>
      {children}
    </div>
  );
}

/* --------------------------------- PageHeader --------------------------------- */

export interface PageHeaderProps {
  /** Mono eyebrow line — usually the underlying tool pipeline. */
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  /** Right-aligned actions / status. */
  actions?: ReactNode;
  className?: string;
}

export function PageHeader({ eyebrow, title, description, actions, className }: PageHeaderProps) {
  return (
    <div
      className={cx("syn-pageheader", className)}
      style={{ display: "flex", alignItems: "flex-start", gap: 14 }}
    >
      <div style={{ flex: 1 }}>
        {eyebrow && <div className="syn-pageheader__eyebrow">{eyebrow}</div>}
        <div className="syn-pageheader__title">{title}</div>
        {description && <div className="syn-pageheader__desc">{description}</div>}
      </div>
      {actions && (
        <div style={{ display: "flex", alignItems: "center", gap: 8, flex: "none" }}>{actions}</div>
      )}
    </div>
  );
}

/* ---------------------------------- Divider ---------------------------------- */

export function Divider({ label, className }: { label?: ReactNode; className?: string }) {
  if (!label) return <div className={cx("syn-divider__line", className)} />;
  return (
    <div className={cx("syn-divider", className)}>
      <div className="syn-divider__line" />
      <span className="syn-divider__label">{label}</span>
      <div className="syn-divider__line" />
    </div>
  );
}

/* ---------------------------------- StatTile ---------------------------------- */

export interface StatTileProps {
  value: ReactNode;
  label: ReactNode;
  /** Oversized hero numeral. */
  hero?: boolean;
  /** Tint the value. */
  tone?: "default" | "accent" | "success" | "purple";
  className?: string;
}

const STAT_TONE: Record<NonNullable<StatTileProps["tone"]>, string | undefined> = {
  default: undefined,
  accent: "var(--syn-accent)",
  success: "var(--syn-success)",
  purple: "var(--syn-purple-text)",
};

export function StatTile({ value, label, hero = false, tone = "default", className }: StatTileProps) {
  return (
    <div className={cx("syn-stat", className)}>
      <div
        className={cx("syn-stat__value", hero && "syn-stat__value--xl")}
        style={tone !== "default" ? { color: STAT_TONE[tone] } : undefined}
      >
        {value}
      </div>
      <div className="syn-stat__label">{label}</div>
    </div>
  );
}

/* Re-export Icon for convenience so surfaces can `import { Icon } from "@synapse/ui-kit"`. */
export { Icon };

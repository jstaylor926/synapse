/**
 * Neo-Gonzo Noir icon set.
 *
 * Thin stroked line glyphs lifted from the design file. All icons share a
 * 0 0 18 18 viewBox, inherit `currentColor`, and take a `size` prop. Render via
 * the `<Icon name="ask" />` component, or import a single glyph directly.
 */
import type { ReactNode, SVGProps } from "react";

export type IconName =
  | "ask"
  | "code"
  | "capture"
  | "planner"
  | "review"
  | "study"
  | "notes"
  | "vault"
  | "search"
  | "send"
  | "plus"
  | "check"
  | "chevron-down"
  | "save";

type GlyphProps = SVGProps<SVGSVGElement> & { size?: number };

const PATHS: Record<IconName, ReactNode> = {
  ask: <path d="M2.5 4.5h13v8h-7l-3.5 3v-3h-2.5z" />,
  code: <path d="M6.5 4.5L2.5 9l4 4.5M11.5 4.5L15.5 9l-4 4.5" />,
  capture: <path d="M9 2.5v8m0 0l-3-3m3 3l3-3M3 12.5v2.5h12v-2.5" />,
  planner: (
    <>
      <rect x="2.5" y="3.5" width="13" height="12" rx="1" />
      <path d="M2.5 7h13M6 2v3M12 2v3" />
    </>
  ),
  review: (
    <>
      <rect x="2.5" y="5" width="9" height="9.5" rx="1" />
      <path d="M6 5V3.2h9.5V13" />
    </>
  ),
  study: <path d="M10 2L4 10.5h4l-1.2 5.5 7-9.5h-4z" />,
  notes: (
    <>
      <path d="M3 4.5h9M3 8h12M3 11.5h12M3 15h7" />
      <path d="M13.5 3.5l2 2-5 5-2.4.4.4-2.4z" />
    </>
  ),
  vault: <path d="M2.5 5.5v9h13v-8h-6l-2-1.5z" />,
  search: (
    <>
      <circle cx="8" cy="8" r="5" />
      <path d="M12 12l3.5 3.5" />
    </>
  ),
  send: <path d="M3 9h11m-5-5l5 5-5 5" />,
  plus: <path d="M9 3v12M3 9h12" />,
  check: <path d="M3.5 9.5l3.5 3.5 7.5-8.5" />,
  "chevron-down": <path d="M4 7l5 5 5-5" />,
  save: <path d="M9 2.5v8m0 0l-3.5-3.5M9 10.5l3.5-3.5M3.5 13.5v2h11v-2" />,
};

export function Icon({ name, size = 18, ...props }: GlyphProps & { name: IconName }) {
  return (
    <svg
      viewBox="0 0 18 18"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {PATHS[name]}
    </svg>
  );
}

/** Stable nav ordering + tool-name tags, mirroring the design's WORKSPACE rail. */
export const NAV_ICONS: { name: IconName; label: string; tag: string }[] = [
  { name: "ask", label: "Ask", tag: "reason_*" },
  { name: "code", label: "Code Buddy", tag: "code_assist" },
  { name: "capture", label: "Capture", tag: "*_ingest" },
  { name: "planner", label: "Planner", tag: "plan_*" },
  { name: "review", label: "Review", tag: "sr_*" },
  { name: "study", label: "Study", tag: "study_*" },
  { name: "notes", label: "Notes", tag: "notes/" },
  { name: "vault", label: "Vault", tag: "vault" },
];

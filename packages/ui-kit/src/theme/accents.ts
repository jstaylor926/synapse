/**
 * Accent themes for Neo-Gonzo Noir.
 *
 * Set `data-accent="<id>"` on the AppShell (or <html>) to re-tint the whole
 * surface. The CSS lives in `styles/tokens.css`; this module is the typed
 * registry surfaces use to build accent pickers.
 */

export type AccentId =
  | "toxic-blue"
  | "harsh-green"
  | "saturated-crimson"
  | "velvet-purple";

export interface Accent {
  id: AccentId;
  /** Human-facing label (matches the design file's enum). */
  label: string;
  /** The base hex, handy for swatches rendered outside CSS. */
  hex: string;
}

export const ACCENTS: readonly Accent[] = [
  { id: "toxic-blue", label: "Toxic Blue", hex: "#2bc0ff" },
  { id: "harsh-green", label: "Harsh Green", hex: "#5fe572" },
  { id: "saturated-crimson", label: "Saturated Crimson", hex: "#ff4d57" },
  { id: "velvet-purple", label: "Velvet Purple", hex: "#8b5cf0" },
] as const;

export const DEFAULT_ACCENT: AccentId = "toxic-blue";

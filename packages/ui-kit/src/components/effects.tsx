/**
 * Neo-Gonzo Noir — atmospheric effects.
 *
 * The film grain and accent glow that give the cockpit its "noir" depth.
 * Both are purely decorative and pointer-transparent.
 */
import type { CSSProperties } from "react";

let grainSeq = 0;

/**
 * SVG fractal-noise grain laid over a surface with `soft-light` blending.
 * Intensity comes from the `--syn-grain` token (override per-instance via the
 * `opacity` prop). Each instance gets a unique filter id so multiple overlays
 * can coexist.
 */
export function GrainOverlay({ opacity }: { opacity?: number }) {
  const id = `syn-grain-${grainSeq++}`;
  const style: CSSProperties | undefined =
    opacity != null ? ({ ["--syn-grain" as string]: String(opacity) } as CSSProperties) : undefined;
  return (
    <svg className="syn-grain" style={style} aria-hidden="true">
      <filter id={id}>
        <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={2} stitchTiles="stitch" />
      </filter>
      <rect width="100%" height="100%" filter={`url(#${id})`} />
    </svg>
  );
}

/**
 * A soft radial accent glow — drop behind a header to bloom the accent color.
 * Position it with the standard CSS inset props via `style`.
 */
export function GlowAccent({
  width = 360,
  height = 200,
  opacity = 0.45,
  style,
}: {
  width?: number;
  height?: number;
  opacity?: number;
  style?: CSSProperties;
}) {
  return <div className="syn-glow" style={{ width, height, opacity, ...style }} aria-hidden="true" />;
}

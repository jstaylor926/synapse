/**
 * Text wrapping for the G2 study HUD — pulled out of main.ts so it can be unit
 * tested without the SDK / DOM (see wrap.test.ts: `bun test`).
 */

// === The piece you implement ===============================================
/**
 * Word-wrap a screen body into display lines no wider than `cols` characters.
 *
 * The body arrives from the bridge with `\n` already separating logical parts
 * (a question from its options, a flashcard front from its `→ back`). Those
 * newlines must be preserved as line breaks. Within each logical line, long
 * text must be broken to fit the narrow HUD — but *where* you break is a design
 * choice that decides how readable a glanced answer is:
 *
 *   - Greedy word wrap (break at spaces) reads best, but a single token longer
 *     than `cols` (a URL, a long identifier) then overflows the row.
 *   - Falling back to a hard character break for over-long tokens guarantees
 *     nothing is clipped, at the cost of an ugly mid-word split.
 *   - Preserve blank lines? They cost a precious row but separate prompt from
 *     answer visually.
 *
 * @param text the screen body (may contain `\n`)
 * @param cols max characters per display line
 * @returns the wrapped lines, in order, ready to window with `scroll`
 *
 * TODO(you): replace this placeholder. It hard-chops at `cols` and so breaks
 * mid-word — runnable, but not glanceable. Implement greedy word wrapping with
 * a character-break fallback for tokens longer than `cols`. The cases in
 * wrap.test.ts encode the target behavior — run `bun test` and make them green.
 */
export function wrapBody(text: string, cols: number): string[] {
  const out: string[] = [];
  for (const logical of text.split("\n")) {
    if (logical === "") {
      out.push("");
      continue;
    }
    for (let i = 0; i < logical.length; i += cols) {
      out.push(logical.slice(i, i + cols));
    }
  }
  return out;
}
// ===========================================================================

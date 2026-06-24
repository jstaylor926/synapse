/**
 * Unit harness for `wrapBody` — run with `bun test` from apps/glasses-study.
 *
 * These cases are the SPEC for the function you're implementing. With the
 * current hard-chop placeholder, the "greedy word wrap" and "over-long token"
 * groups FAIL (it splits mid-word); the newline/invariant groups already pass.
 * Make them all green, then flash to the sim with confidence.
 */

import { expect, test, describe } from "bun:test";
import { wrapBody } from "./wrap";

describe("invariants (true for any correct wrap)", () => {
  const bodies = [
    "alpha beta gamma delta epsilon zeta eta theta",
    "Which optimizer uses momentum?\nA. SGD\nB. Adam\nC. RMSProp",
    "Answer: B. Adam — combines momentum with per-parameter adaptive rates.",
    "see https://averylongurl.example.com/some/deep/path?q=1 now",
  ];
  for (const cols of [8, 20, 46]) {
    for (const body of bodies) {
      test(`no line exceeds cols=${cols} :: ${body.slice(0, 24)}…`, () => {
        for (const line of wrapBody(body, cols)) {
          expect(line.length).toBeLessThanOrEqual(cols);
        }
      });
    }
  }
});

describe("greedy word wrap (break at spaces, don't split words that fit)", () => {
  test("packs words up to the limit", () => {
    expect(wrapBody("alpha beta", 8)).toEqual(["alpha", "beta"]);
  });

  test("keeps a line that exactly fits", () => {
    expect(wrapBody("a b c", 10)).toEqual(["a b c"]);
  });

  test("wraps a sentence greedily", () => {
    // "one two" = 7 ≤ 7; adding "three" (→13) overflows, so it starts a new line.
    expect(wrapBody("one two three four", 7)).toEqual(["one two", "three", "four"]);
  });
});

describe("explicit newlines & blank lines are preserved", () => {
  test("each \\n starts a new display line", () => {
    expect(wrapBody("Q?\nA. x\nB. y", 46)).toEqual(["Q?", "A. x", "B. y"]);
  });

  test("a blank line (prompt/answer separator) survives", () => {
    expect(wrapBody("front\n\n→ back", 12)).toEqual(["front", "", "→ back"]);
  });
});

describe("over-long tokens fall back to a character break", () => {
  test("a single word longer than cols is hard-split, never clipped", () => {
    expect(wrapBody("supercalifragilistic", 8)).toEqual(["supercal", "ifragili", "stic"]);
  });

  test("a long token mixed with words still respects the limit", () => {
    for (const line of wrapBody("go https://averylongurl.example/path end", 10)) {
      expect(line.length).toBeLessThanOrEqual(10);
    }
  });
});

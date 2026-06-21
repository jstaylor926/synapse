/**
 * Split a markdown answer into ordered prose / fenced-code segments so the view
 * can render prose as text and each ``` code block in an editable CodeEditor.
 */
export type AnswerSegment =
  | { kind: "prose"; text: string }
  | { kind: "code"; lang: string; text: string };

// ```lang\n … \n``` — lang optional, non-greedy body, tolerant of trailing newline.
const FENCE = /```([\w+-]*)\n?([\s\S]*?)```/g;

export function splitAnswer(markdown: string): AnswerSegment[] {
  const segments: AnswerSegment[] = [];
  let last = 0;

  for (let m = FENCE.exec(markdown); m !== null; m = FENCE.exec(markdown)) {
    const prose = markdown.slice(last, m.index).trim();
    if (prose) segments.push({ kind: "prose", text: prose });
    segments.push({ kind: "code", lang: (m[1] || "python").toLowerCase(), text: m[2].replace(/\n$/, "") });
    last = m.index + m[0].length;
  }

  const tail = markdown.slice(last).trim();
  if (tail) segments.push({ kind: "prose", text: tail });

  // No fences at all → one prose segment (keeps callers simple).
  return segments.length ? segments : [{ kind: "prose", text: markdown.trim() }];
}

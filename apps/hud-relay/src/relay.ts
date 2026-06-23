/**
 * @synapse/hud-relay — a tiny line buffer that bridges *anything on your Mac*
 * to the G2 heads-up display.
 *
 * Two feeders push lines in:
 *   - `<cmd> | hud`         → ad-hoc terminal output (src/hud.ts)
 *   - Claude Code hooks     → Claude's replies + tool activity (src/claude-hud.ts)
 *
 * The glasses app (`@synapse/glasses-hub`) pulls lines out by polling
 * `GET /tail?since=<seq>` — a monotonic sequence number lets it ask for "only
 * what's new since I last looked", so a glance shows the live tail and a swipe
 * pages back through history.
 *
 * Why polling, not SSE: the glasses load the app through Vite's dev proxy, and
 * SSE streams buffer unpredictably through proxies. A 1s poll of a seq'd ring
 * buffer is bulletproof and plenty fresh for a glance-able HUD.
 *
 * Run: `bun run dev` (from apps/hud-relay) or `bun run dev:hud` (repo root).
 */

const PORT = Number(process.env.HUD_RELAY_PORT ?? 4318);
const MAX_LINES = Number(process.env.HUD_RELAY_MAX ?? 2000);

/** One line on the HUD feed. `seq` is globally monotonic and gap-free. */
interface Line {
  seq: number;
  source: string; // "claude" | "term" | …  (lets the HUD tag/colour lines)
  text: string;
  ts: number;
}

// The ring buffer. We keep the last MAX_LINES entries; `seq` keeps climbing
// even as old entries fall off, so clients can detect a gap (missed lines).
const buffer: Line[] = [];
let seq = 0;

// Strip ANSI escape / colour codes so the HUD shows clean text, not `\x1b[31m`.
// eslint-disable-next-line no-control-regex
const ANSI = /\x1b\[[0-9;?]*[ -/]*[@-~]/g;

function append(rawText: string, source: string): number {
  // Split on newlines; keep blank lines (terminal fidelity) but drop a single
  // trailing newline's empty tail so each push doesn't add a phantom line.
  const lines = rawText.replace(/\r\n?/g, "\n").split("\n");
  if (lines.length > 1 && lines[lines.length - 1] === "") lines.pop();
  for (const line of lines) {
    buffer.push({ seq: ++seq, source, text: line.replace(ANSI, ""), ts: Date.now() });
  }
  while (buffer.length > MAX_LINES) buffer.shift();
  return seq;
}

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...CORS },
  });

const server = Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);

    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });

    if (url.pathname === "/healthz") {
      return json({ status: "ok", seq, lines: buffer.length });
    }

    // Feeders push here. Body is raw text, or JSON {text, source}.
    if (url.pathname === "/push" && req.method === "POST") {
      const ctype = req.headers.get("content-type") ?? "";
      let text = "";
      let source = url.searchParams.get("source") ?? "term";
      if (ctype.includes("application/json")) {
        const body = (await req.json()) as { text?: string; source?: string };
        text = body.text ?? "";
        source = body.source ?? source;
      } else {
        text = await req.text();
      }
      const latest = append(text, source);
      return json({ seq: latest });
    }

    // The glasses poll here: everything with seq > since.
    if (url.pathname === "/tail") {
      const sinceParam = url.searchParams.get("since");
      const max = Number(url.searchParams.get("max") ?? 500);
      const oldest = buffer.length ? buffer[0]!.seq : 0;
      let lines: Line[];
      let dropped = false;
      if (sinceParam === null) {
        // First poll: hand back the tail end of the buffer.
        lines = buffer.slice(-max);
      } else {
        const since = Number(sinceParam);
        // If the client is further behind than the buffer reaches, it missed lines.
        dropped = since > 0 && since < oldest - 1;
        lines = buffer.filter((l) => l.seq > since).slice(-max);
      }
      return json({ seq, oldest, lines, dropped });
    }

    return new Response("Not found", { status: 404, headers: CORS });
  },
});

console.log(`[hud-relay] listening on http://localhost:${server.port}  (push → /push, tail → /tail)`);

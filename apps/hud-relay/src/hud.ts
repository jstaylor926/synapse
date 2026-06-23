#!/usr/bin/env bun
/**
 * `hud` — pipe any terminal output to the G2 heads-up display.
 *
 *   echo "hello glasses" | hud
 *   npm test | hud
 *   claude -p "explain this file" | hud
 *   hud "a one-off message"          # message from args, no pipe
 *
 * It "tees": stdin is mirrored straight back to stdout, so piping through `hud`
 * never swallows your normal terminal output — it just *also* sends each line to
 * the relay (src/relay.ts), which the glasses tail.
 *
 * Override the relay with HUD_RELAY_URL (default http://localhost:4318).
 */

const RELAY = process.env.HUD_RELAY_URL ?? "http://localhost:4318";
const SOURCE = process.env.HUD_SOURCE ?? "term";

async function push(text: string): Promise<void> {
  if (!text) return;
  try {
    await fetch(`${RELAY}/push`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, source: SOURCE }),
      // Never let a down relay block the pipeline.
      signal: AbortSignal.timeout(1500),
    });
  } catch {
    // Relay down / unreachable — fail silently; the pipe keeps flowing.
  }
}

// --- Mode 1: message from args -------------------------------------------------
const args = process.argv.slice(2);
if (args.length > 0) {
  await push(args.join(" "));
  process.exit(0);
}

// --- Mode 2: tee stdin → stdout + relay ---------------------------------------
// Batch lines and flush on a short interval so a noisy command doesn't fire one
// HTTP request per line.
let pending = "";
let flushing: Promise<void> = Promise.resolve();

function flush(): void {
  if (!pending) return;
  const batch = pending;
  pending = "";
  flushing = flushing.then(() => push(batch));
}

const timer = setInterval(flush, 250);
const decoder = new TextDecoder();

for await (const chunk of Bun.stdin.stream()) {
  const str = decoder.decode(chunk, { stream: true });
  Bun.write(Bun.stdout, str); // tee through, unbuffered
  pending += str;
  // Flush eagerly on line boundaries so output feels live on the HUD.
  if (pending.includes("\n")) flush();
}

clearInterval(timer);
flush();
await flushing;

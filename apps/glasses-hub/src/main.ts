/**
 * @synapse/glasses-hub — Claude Code "terminal mode" on the G2 HUD.
 *
 * The app polls the HUD relay (`@synapse/hud-relay`, proxied at /relay) for new
 * lines and renders them on the heads-up display:
 *
 *   - LIVE tail (default): the newest lines, auto-advancing as output arrives.
 *   - SCROLL-BACK: swipe up to page through history (pauses live); swipe down
 *     (or single-tap) to jump back to the live tail.
 *   - Double-tap to exit.
 *
 * Feeders into the relay: `<cmd> | hud` and Claude Code hooks (source="claude").
 *
 * Hardware: 576 x 288 px, 4-bit greyscale, touchpad input. See handle-input
 * for the event model (swipe → textEvent, tap → sysEvent, protobuf 0→undefined).
 */

import {
  waitForEvenAppBridge,
  TextContainerProperty,
  CreateStartUpPageContainer,
  TextContainerUpgrade,
} from "@evenrealities/even_hub_sdk";

// --- The 576 x 288 HUD grid -------------------------------------------------
const SCREEN_W = 576;
const SCREEN_H = 288;
const TITLE_H = 40;
/** Visible body lines. Tunable once verified against the real font metrics. */
const ROWS = 6;
const POLL_MS = 1000;
const MAX_BUFFER = 1000;

// --- Local mirror of the relay buffer ---------------------------------------
interface Line {
  seq: number;
  source: string;
  text: string;
}
const lines: Line[] = [];
let sinceSeq = 0;
let mode: "live" | "scroll" = "live";
/** In scroll mode: how many lines above the live tail the window is anchored. */
let scrollUp = 0;

// --- Containers -------------------------------------------------------------
const TITLE_ID = 1;
const BODY_ID = 2;
const INIT_TITLE = "Claude Code";
const INIT_BODY = "Connecting to relay…";

const titleC = new TextContainerProperty({
  containerID: TITLE_ID,
  containerName: "title",
  xPosition: 0,
  yPosition: 0,
  width: SCREEN_W,
  height: TITLE_H,
  paddingLength: 4,
  borderWidth: 0,
  borderColor: 8,
  content: INIT_TITLE,
  isEventCapture: 0,
});

const bodyC = new TextContainerProperty({
  containerID: BODY_ID,
  containerName: "body",
  xPosition: 0,
  yPosition: TITLE_H,
  width: SCREEN_W,
  height: SCREEN_H - TITLE_H,
  paddingLength: 4,
  borderWidth: 0,
  borderColor: 5,
  content: INIT_BODY,
  isEventCapture: 1, // the body captures swipes (scroll) and taps (sysEvent)
});

const bridge = await waitForEvenAppBridge();

await bridge.createStartUpPageContainer(
  new CreateStartUpPageContainer({ containerTotalNum: 2, textObject: [titleC, bodyC] }),
);

// Track current on-screen text length so textContainerUpgrade can replace it.
let titleLen = INIT_TITLE.length;
let bodyLen = INIT_BODY.length;

// Serialize HUD writes — polls and input events both trigger renders.
let chain: Promise<void> = Promise.resolve();
function scheduleRender(): void {
  chain = chain.then(render).catch(() => {});
}

async function setText(
  id: number,
  name: string,
  prevLen: number,
  text: string,
): Promise<number> {
  await bridge.textContainerUpgrade(
    new TextContainerUpgrade({
      containerID: id,
      containerName: name,
      contentOffset: 0,
      contentLength: prevLen,
      content: text,
    }),
  );
  return text.length;
}

function visibleSlice(): Line[] {
  if (lines.length === 0) return [];
  // Bottom of the window: live → end of buffer; scroll → `scrollUp` lines above.
  const end = Math.max(ROWS, lines.length - (mode === "scroll" ? scrollUp : 0));
  const start = Math.max(0, end - ROWS);
  return lines.slice(start, end);
}

async function render(): Promise<void> {
  const slice = visibleSlice();
  const bodyText = slice.length
    ? slice.map((l) => l.text).join("\n")
    : "Waiting for output…";
  const titleText =
    mode === "live"
      ? "Claude Code · live"
      : `Claude Code · ↑${scrollUp}`;

  titleLen = await setText(TITLE_ID, "title", titleLen, titleText);
  bodyLen = await setText(BODY_ID, "body", bodyLen, bodyText);
}

// --- Poll the relay ---------------------------------------------------------
async function poll(): Promise<void> {
  try {
    const url = sinceSeq > 0 ? `/relay/tail?since=${sinceSeq}` : `/relay/tail`;
    const res = await fetch(url, { signal: AbortSignal.timeout(POLL_MS + 500) });
    if (!res.ok) return;
    const data = (await res.json()) as { seq: number; lines: Line[] };
    if (data.lines?.length) {
      lines.push(...data.lines);
      if (lines.length > MAX_BUFFER) lines.splice(0, lines.length - MAX_BUFFER);
      // In scroll mode, keep the user anchored to the same lines as new ones
      // arrive below; in live mode, follow the tail.
      if (mode === "scroll") scrollUp += data.lines.length;
      scheduleRender();
    }
    sinceSeq = data.seq ?? sinceSeq;
  } catch {
    /* relay unreachable — keep showing what we have, retry next tick */
  }
}

setInterval(poll, POLL_MS);
void poll();

// --- Input ------------------------------------------------------------------
bridge.onEvenHubEvent((event) => {
  if (event.textEvent) {
    const type = event.textEvent.eventType ?? 0;
    if (type === 1) {
      // Swipe up → page back through history.
      mode = "scroll";
      scrollUp = Math.min(scrollUp + ROWS, Math.max(0, lines.length - ROWS));
      scheduleRender();
    } else if (type === 2) {
      // Swipe down → page toward newest; reaching the bottom resumes live.
      scrollUp = Math.max(0, scrollUp - ROWS);
      if (scrollUp === 0) mode = "live";
      scheduleRender();
    }
    return;
  }
  if (event.sysEvent) {
    const type = event.sysEvent.eventType ?? 0;
    if (type === 3) {
      // Double-tap → system exit dialog.
      void bridge.shutDownPageContainer(1);
    } else if (type === 0) {
      // Single tap → snap back to the live tail.
      mode = "live";
      scrollUp = 0;
      scheduleRender();
    }
    return;
  }
});

console.log("[glasses-hub] terminal mode ready — polling /relay/tail");

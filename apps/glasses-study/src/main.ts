/**
 * @synapse/glasses-study — scrollable flashcard / quiz study mode on the G2 HUD.
 *
 * Where terminal mode (`@synapse/glasses-hub`) tails a live log, study mode walks
 * a *deck*: the glasses-bridge (`@synapse/glasses-bridge`, proxied at /bridge)
 * turns a kernel `ExtractResult` into ordered, reveal-able screens —
 * "prompt → tap → answer" — and this app renders them one at a time.
 *
 * The deck is chosen by URL query (the glasses have no keyboard), e.g.
 *   evenhub qr --url "http://<lan-ip>:5174/?topic=transformers&kind=quiz&n=8"
 *
 * Interaction model (touchpad):
 *   - SINGLE TAP  → next screen (prompt → answer → next prompt …). Loops at end.
 *   - SWIPE UP    → scroll down through a long answer (reveal lines below).
 *   - SWIPE DOWN  → scroll back up through the answer.
 *   - DOUBLE TAP  → exit.
 *
 * The "scrollable" part: a quiz/flashcard answer can be far longer than the ~7
 * visible rows of a 576×288 HUD. Each screen's body is word-wrapped into display
 * lines (see `wrapBody`) and a ROWS-tall window slides over them with swipes.
 *
 * Hardware: 576 × 288 px, 4-bit greyscale, touchpad input.
 */

import {
  waitForEvenAppBridge,
  TextContainerProperty,
  CreateStartUpPageContainer,
  TextContainerUpgrade,
} from "@evenrealities/even_hub_sdk";
import { wrapBody } from "./wrap";

// --- The 576 x 288 HUD grid -------------------------------------------------
const SCREEN_W = 576;
const SCREEN_H = 288;
const TITLE_H = 40;
/** Visible body rows. Tunable once verified against the real font metrics. */
const ROWS = 7;
/** Characters that fit on one body row at the HUD font. Tune against hardware. */
const COLS = 46;

// --- Deck model (mirrors glasses-bridge `Screen`) ---------------------------
interface Screen {
  kind: string;
  index: number;
  total: number;
  title: string;
  body: string;
  reveal: boolean;
}
interface Deck {
  topic: string;
  kind: string;
  mode: string;
  screens: Screen[];
}

// --- Navigation state -------------------------------------------------------
let deck: Deck | null = null;
let screenIdx = 0;
/** First wrapped display line visible in the body window (the scroll anchor). */
let scroll = 0;
/** Wrapped display lines for the *current* screen, recomputed on each move. */
let displayLines: string[] = [];

// --- Containers -------------------------------------------------------------
const TITLE_ID = 1;
const BODY_ID = 2;
const INIT_TITLE = "Synapse Study";
const INIT_BODY = "Loading deck…";

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
  isEventCapture: 1, // the body captures swipes (scroll) and taps (navigation)
});

const bridge = await waitForEvenAppBridge();

await bridge.createStartUpPageContainer(
  new CreateStartUpPageContainer({ containerTotalNum: 2, textObject: [titleC, bodyC] }),
);

// Track current on-screen text length so textContainerUpgrade can replace it.
let titleLen = INIT_TITLE.length;
let bodyLen = INIT_BODY.length;

// Serialize HUD writes — the fetch and input events both trigger renders.
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

/** Re-wrap the current screen and clamp scroll into range. Call on every move. */
function relayout(): void {
  const screen = deck?.screens[screenIdx];
  displayLines = screen ? wrapBody(screen.body, COLS) : [];
  const maxScroll = Math.max(0, displayLines.length - ROWS);
  scroll = Math.min(Math.max(0, scroll), maxScroll);
}

async function render(): Promise<void> {
  const screen = deck?.screens[screenIdx];
  if (!deck || !screen) {
    titleLen = await setText(TITLE_ID, "title", titleLen, "Synapse Study");
    bodyLen = await setText(BODY_ID, "body", bodyLen, INIT_BODY);
    return;
  }

  const window = displayLines.slice(scroll, scroll + ROWS);
  const more = scroll + ROWS < displayLines.length; // is there text below?
  const up = scroll > 0; // is there text above?
  // A two-arrow gutter cue so a wearer knows an answer continues off-screen.
  const cue = `${up ? "↑" : " "}${more ? "↓" : " "}`;

  // Title: "Quiz 2/8 · gen ↑↓"  — position, degradation mode, and scroll cues.
  const modeTag = deck.mode === "generative" ? "gen" : "floor";
  const titleText = `${screen.title} · ${modeTag} ${cue}`.trimEnd();

  titleLen = await setText(TITLE_ID, "title", titleLen, titleText);
  bodyLen = await setText(BODY_ID, "body", bodyLen, window.join("\n") || " ");
}

// --- Load the deck ----------------------------------------------------------
async function loadDeck(): Promise<void> {
  const params = new URLSearchParams(location.search);
  const topic = params.get("topic") ?? "";
  const kind = params.get("kind") ?? "flashcards";
  const n = params.get("n") ?? "8";

  if (!topic.trim()) {
    deck = {
      topic: "",
      kind,
      mode: "floor",
      screens: [
        {
          kind,
          index: 1,
          total: 1,
          title: "No topic",
          body: "Launch with a deck, e.g.\n?topic=transformers&kind=quiz",
          reveal: false,
        },
      ],
    };
    relayout();
    scheduleRender();
    return;
  }

  try {
    const url = `/bridge/spec_view/study?topic=${encodeURIComponent(topic)}&kind=${encodeURIComponent(kind)}&n=${encodeURIComponent(n)}`;
    const res = await fetch(url, { signal: AbortSignal.timeout(15000) });
    const data = (await res.json()) as Deck & { error?: string };
    if (!res.ok || data.error || !data.screens?.length) {
      throw new Error(data.error ?? `bridge ${res.status}`);
    }
    deck = data;
    screenIdx = 0;
    scroll = 0;
  } catch (err) {
    deck = {
      topic,
      kind,
      mode: "floor",
      screens: [
        {
          kind,
          index: 1,
          total: 1,
          title: "Bridge offline",
          body: `Couldn't load "${topic}".\nIs the glasses-bridge running on :4317?\n\n${String(err)}`,
          reveal: false,
        },
      ],
    };
  }
  relayout();
  scheduleRender();
}

void loadDeck();

// --- Navigation helpers -----------------------------------------------------
function nextScreen(): void {
  if (!deck) return;
  // Loop the deck so a wearer can keep cycling hands-free.
  screenIdx = (screenIdx + 1) % deck.screens.length;
  scroll = 0;
  relayout();
  scheduleRender();
}

function scrollBy(rows: number): void {
  const before = scroll;
  scroll += rows;
  relayout(); // clamps scroll into [0, maxScroll]
  if (scroll !== before) scheduleRender();
}

// --- Input ------------------------------------------------------------------
bridge.onEvenHubEvent((event) => {
  if (event.textEvent) {
    const type = event.textEvent.eventType ?? 0;
    if (type === 1) {
      // Swipe up → scroll down through a long answer (reveal lines below).
      scrollBy(ROWS - 1); // overlap one row for reading continuity
    } else if (type === 2) {
      // Swipe down → scroll back up.
      scrollBy(-(ROWS - 1));
    }
    return;
  }
  if (event.sysEvent) {
    const type = event.sysEvent.eventType ?? 0;
    if (type === 3) {
      // Double-tap → system exit dialog.
      void bridge.shutDownPageContainer(1);
    } else if (type === 0) {
      // Single tap → advance (prompt → answer → next prompt …).
      nextScreen();
    }
    return;
  }
});

console.log("[glasses-study] study mode ready — fetching deck from /bridge");

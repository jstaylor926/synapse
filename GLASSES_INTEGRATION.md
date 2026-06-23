# Glasses Integration — Update & Opinion Log

> Surface: **Even Realities G2** AR glasses → `apps/glasses-bridge` → kernel REST edge.
> Goal: extract study artifacts (flashcards, quiz, interview/STAR prep, summaries)
> from vault material and drive a *walking quiz / interview drill* on the G2 HUD.
>
> Status as of **2026-06-22**. This is a living log — append updates, don't rewrite.

---

## 1. What shipped this round (the extraction slice)

A full vertical slice from glasses surface → kernel capability, following the
repo's two invariants (degrade-never-fabricate; surfaces never touch kernel
internals).

```
glasses-bridge /spec_view/study?topic=…&kind=…   ← G2 taps through HUD screens
   → @synapse/client.extract()                    ← single typed edge path
   → POST /study/extract                          ← thin REST adapter
   → study.extract()  →  kb.search() (vault BM25 floor)
        ├─ generative: llm.complete() → strict JSON → typed items
        └─ floor:      honest, never-fabricated
```

| Piece | File | State |
|---|---|---|
| Contracts (4 kinds + request/result) | `kernel/contracts/models.py`, `packages/contracts-ts/src/index.ts` | ✅ in sync |
| Extract capability | `kernel/src/synapse_engine/study/extract.py` | ✅ generative + 3/4 floors |
| REST route `POST /study/extract` | `kernel/src/synapse_engine/api_server.py` | ✅ |
| Typed client `extract()` | `packages/client/src/index.ts` | ✅ |
| HUD pagination + progressive reveal | `apps/glasses-bridge/src/index.ts` | ✅ `/spec_view/study` |

Verified: all TS workspaces typecheck; kernel smoke tests pass; JSON parser and
summary/quiz/interview floors exercised manually.

**Kinds supported:** `flashcards`, `quiz`, `interview` (STAR), `summary`.
**Source (v1 decision):** vault material selected by `topic` (reuses `kb.search`).

---

## 2. Known gaps / immediate TODOs

1. **Flashcard extractive floor is unimplemented** — `extract.py::_flashcard_floor`
   raises `NotImplementedError`. This is the *only* path that currently raises;
   with no LLM reachable, `kind=flashcards` will error instead of degrading.
   **This violates the never-raise invariant until filled.** (Left deliberately
   as a design decision — see §4.1.) Quiz/STAR floors already degrade to grounded
   key points; flashcards should degrade to a real card built from verbatim text.
2. **No pytest for the extract paths** — the generative parse, the floor
   dispatch, and pagination are untested in CI. Add `tests/test_extract.py`.
3. **Bridge has no pytest/bun-test** — `paginate()` reveal logic is pure and
   easily unit-tested; worth locking down before the device app depends on it.
4. **`mode` is surfaced but unused on-device** — the bridge returns
   `mode: "generative" | "extractive"` so the HUD can show "(offline)" but no
   client renders it yet.

---

## 3. Remaining steps to a working G2 demo (ordered)

The bridge speaks plain HTTP+JSON today. What stands between that and glasses on
your face, roughly in dependency order:

### 3.1 Close the floor + tests (½ day) — *do first*
Implement `_flashcard_floor`, add kernel + bridge tests. After this, the whole
extraction slice is correct and offline-safe end to end.

### 3.2 The on-device app (the real unknown — see §5)
The G2 runs **Even Realities' own firmware**; there is no general "load a web
app onto the lens" yet. Two realistic paths:
- **(a) Companion phone app + BLE.** A small app (the Even SDK / a community BLE
  lib) pairs to the glasses, calls our `/spec_view/study` endpoint over the LAN,
  and pushes text frames to the HUD. The bridge already emits exactly the
  screen shapes such an app needs.
- **(b) Even's app ecosystem**, if/when it exposes a way to register a custom
  "app"/teleprompter feed. Lower control, possibly faster.

Either way **the bridge contract (`screens[]`) is the seam** and shouldn't need
to change. Pin down which path is real *before* building UI on top.

### 3.3 Interaction wiring
- Map **tap → next screen**, **long-press / swipe → grade (again/good/easy)**.
- The grade is the hook into FSRS (`features/sr.py`) — close the loop so a
  walking quiz actually schedules reviews.

### 3.4 Voice capture (the "both, voice next" seam — deferred from v1)
Add a `transcribe` job (already a named job kind in the contracts) so the G2 mic
can capture a lecture → transcript → `extract(text=…)`. Requires making
`extract()` source-agnostic (accept raw text, not just a vault topic).

### 3.5 Polish for the HUD constraints
- **Width/line wrapping** to the G2's actual character grid (currently we emit
  unwrapped text and assume the device wraps — verify on hardware).
- **Length caps** per screen; long STAR sections may need their own pagination.
- **Latency**: generative extraction can be multi-second; pre-warm or pre-extract
  a deck before the walk starts rather than per-tap.

---

## 4. Open decisions & opinions

### 4.1 Flashcard floor heuristic — *recommend cloze deletion*
Three honest options (back must be verbatim source text):
- **Cloze** — blank a salient term: `front="BM25 is a ___ function"`, `back="ranking"`.
- **First-sentence definition** — `front="What is BM25?"`, `back=<sentence>`.
- **Heading → body** — chunk title as front, lead sentence as back.

**Opinion:** cloze gives the best active-recall value and reuses the same salient
-term selection we'll want for quiz distractors later. Downside: term selection
is the hard part; a naive "blank the longest noun" is a fine v1.

### 4.2 Source-agnostic extractor — *do it at 3.4, not now*
Today `extract(topic)` retrieves from the vault. Voice/transcript will want
`extract(text=…)`. Keep the public signature stable by adding an optional
`text` param that, when present, skips retrieval and treats the text as the sole
"citation". Don't refactor preemptively — wait until the transcribe job is real.

### 4.3 Generation timing — *pre-extract a deck, don't generate per-tap*
The HUD reveal is tap-paced (sub-second expectation); LLM extraction is not.
Extract the whole deck up front (one request), cache the `screens[]`, tap
through locally. The bridge already returns the full deck in one call — lean into
that.

### 4.4 Grading → FSRS — *the feature isn't "done" until this loops*
Extraction without scheduling is a demo, not a study tool. The payoff of glasses
is *frictionless review during dead time*; that only compounds if grades feed
FSRS. Treat 3.3's grade hook as core scope, not polish.

---

## 5. Risks / unknowns

- **G2 programmability is the biggest open risk.** Confirm the actual SDK/BLE
  surface and whether arbitrary text frames + tap events are accessible to a
  third-party app. Everything in §3.2+ depends on this. *Validate before building.*
- **No camera on Even glasses** (deliberate privacy stance) ⇒ no "look at this
  page and OCR it." Input is voice or vault only. This shaped the v1 source choice.
- **HUD real estate is tiny.** Our screen-splitting assumptions (lines, width,
  reveal granularity) are unvalidated against hardware — expect to tune §3.5.
- **Latency + offline.** On a walk, connectivity and model availability vary; the
  extractive floor must be genuinely good, not a fallback afterthought.

---

## 6. Quick reference — try it without glasses

```bash
bun run dev:api          # kernel REST edge on :8765
bun run --filter '@synapse/glasses-bridge' dev   # bridge on :4317

# Extract a flashcard deck as HUD screens:
curl 'http://127.0.0.1:4317/spec_view/study?topic=bm25&kind=flashcards&n=5'
# kind ∈ flashcards | quiz | interview | summary
```

> Note: `kind=flashcards` will error until §2.1 (the floor) is implemented *if*
> no LLM is reachable. `summary`/`quiz`/`interview` work offline today.

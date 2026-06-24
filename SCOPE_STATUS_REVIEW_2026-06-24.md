# SYNAPSE — SCOPE & STATUS REVIEW

> **Architect's field report.** Dated **2026-06-24**. Ground truth: `main` @ `48e7394`
> ("glasses update"). Method: read the standing docs, then walked the kernel, the edges,
> the contracts, and the cockpit and **confirmed every claim against the code**. Where the
> docs and the repo disagree, the repo wins — and I name the gap.
>
> **Verdict:** the foundation is sound and the plumbing pattern is now proven three times,
> not two. But the living scoreboard is two commits stale, and the newest slice shipped with
> **two live invariant breaches** — both small, both worth closing before anything stacks on top.

---

## 1. SCOPE — WHAT SYNAPSE IS

One thing said five ways: a **local-first personal tooling platform** that consolidates
**study, reasoning, document processing, and planning** into a single self-hosted backend.

- A Python **kernel** owns every capability.
- It exposes them over **two edges** — an **MCP** edge (primary; FastMCP over stdio) and a
  **thin REST** edge (FastAPI on `:8765`).
- The **surfaces** — Tauri cockpit, AR glasses, Obsidian, code editors, CLI — consume an edge
  and **never** reach into kernel internals.
- All knowledge is **Markdown in an Obsidian vault** (`data/vault`). The SQLite indexes
  (`data/db`) are **derived and rebuildable** — the vault is the truth.

Two principles shape the whole codebase: **degradation floors** (every capability has an
offline, dependency-free floor behind the same signature — *never fabricate, never raise*) and
**vault write-safety** (writes go through a serialized single-writer **GATEKEEPER**, not yet
built). Contracts cross the edges as Pydantic (`kernel/contracts/models.py`), manually mirrored
to TypeScript (`packages/contracts-ts`), and surfaces touch REST only through the typed
`@synapse/client`.

---

## 2. THE SHAPE — AS BUILT

```
SURFACES        cockpit (Tauri+React) · AR glasses · Obsidian · Zed · CLI
                       │  (consume an edge — never the internals)
EDGES           MCP (FastMCP/stdio, primary)   REST (FastAPI :8765, thin)
                       │  validate vs contract → call same in-proc capability → .model_dump()
KERNEL          kb · reason · code · study · ingest · features/{sr,planner,capture,pdf}
                       │  every capability degrades to a floor (None / [] / extractive)
                  jobs/queue (SQLite) → worker loop → handlers
DATA            data/vault/*.md  (truth)   ·   data/db/*.db  (derived, rebuildable)
```

---

## 3. STATUS — WHAT'S ACTUALLY WIRED (verified @ `48e7394`)

| Track | Real | Total | Reality at HEAD |
|---|---|---|---|
| Cockpit views wired to kernel | 2 | 8 | **Ask** ✅, **Code Buddy** ✅ — six still mock |
| End-to-end vertical slices | **3** | — | Ask, Code Buddy, **+ Glasses `study.extract`** (serves AR, not the cockpit) |
| REST routes | **5** | ~25 | `/health`, `/kb/search`, `/reason/ask`, `/code/assist`, **`/study/extract`** |
| MCP tools | 4 | ~31 | `health`, `kb_search`, `ingest_url` ◐, `code_assist` — **`study_extract` missing** |
| Real kernel bodies | **4** | 8 | `kb`, `reason`, `code`, **`study.extract`** (`study.due_cards` still stub) |
| Reasoning rung | 2 | 3 | extractive floor ✅ + generative (litellm→Ollama/Anthropic) ✅; embeddings/rerank pending |
| Async infra | 2 | 2 | job queue ✅ + worker loop ✅ (ingest handlers stub) |
| Other surfaces | — | — | cli ✅, glasses-bridge ✅, **+ glasses-hub / glasses-study / hud-relay (new)**; obsidian ⚠, zed skeleton |
| Kernel reconciliation (**M0**) | 0 | 1 | two kernels still coexist — the blocker |

**Real in the kernel:** `kb` (BM25 lexical floor over the vault), `reason` (generative when a
model answers, extractive floor otherwise), `code` (read-only tutor wrapper over `reason`),
**`study.extract`** (flashcards / quiz / STAR / summary — generative + floors), the `llm.py`
seam, the SQLite job queue, the worker loop, and `config.py`.

**Stubbed (raise `NotImplementedError`):** `study.due_cards`, `features/sr` (real FSRS-6 in
legacy), `features/planner` (real ontology + gatekeeper in legacy), `features/capture` (needs
the gatekeeper), `features/pdf`, `ingest.{web,pdf,audio}`, and the worker's `ingest_*` handlers.

**The proven slices:**
```
AskView       → @synapse/client.ask()       → POST /reason/ask    → reason.answer() → kb.search()
CodeBuddyView → @synapse/client.codeAssist()→ POST /code/assist   → code.assist()   → kb.search()
glasses-bridge→ @synapse/client.extract()   → POST /study/extract → study.extract() → kb.search()
```

---

## 4. DRIFT — THE DOC VS THE REPO (flagged on purpose)

`IMPLEMENTATION_STATUS.md` is the living scoreboard — and right now it's a **photograph two
commits old**. Its header reads "*As of `eb87a36` (code buddys), 2026-06-21*," but HEAD is
`48e7394`, past the Jun-22 **glasses** work. The newer `GLASSES_INTEGRATION.md` (2026-06-22) does
document that slice well; the *scoreboard* just never absorbed it. The gaps:

- **REST routes say 4 — there are 5.** `POST /study/extract` is live and missing from §4.2.
- **`study` is listed `⛔ stub` — it's now `◐` partial.** `study/extract.py` is a real 213-line
  body (generative + floors); only `due_cards` still stubs.
- **"Other surfaces 2/4" undercounts.** Three new surfaces landed — `glasses-hub`,
  `glasses-study`, `hud-relay` — none on the board.
- **MCP "4 tools" is numerically right but hides a new parity gap** (see §5, Law #5).

**Fix one of them on purpose:** reconcile the `IMPLEMENTATION_STATUS.md` scoreboard up to HEAD
(it's the cheap half-hour that stops the next session from re-discovering all of the above).

---

## 5. THE LAW — INVARIANT STATUS

| # | Invariant | State | Note |
|---|---|---|---|
| 1 | TWO KERNELS, ONE TARGET | ⛔ open | **M0** not started. Legacy tree (`synapse-engine/` + top-level `contracts\|features\|jobs\|workers/`) still holds the richer bodies. Unblocks everything once ported. |
| 2 | DEGRADATION FLOORS — NEVER FABRICATE / NEVER RAISE | ⚠ **breached** | `study/extract.py::_flashcard_floor` raises `NotImplementedError`. With no model reachable, `kind=flashcards` **errors instead of degrading**. Deliberate-but-open (GLASSES §2.1). The other three kinds floor honestly. |
| 3 | VAULT WRITE-SAFETY — GATEKEEPER ONLY | ⛔ not built | No safe writes until the serialized single-writer exists. Blocks Capture, Planner writes, Notes. Reference body is in legacy. |
| 4 | CONTRACTS IN SYNC — TYPED CLIENT ONLY | ✅ holds | The study slice mirrors cleanly: `ExtractRequest/Result`, `Flashcard`, `QuizItem`, `STARPrompt`, `KeyPoint`, `StudyKind` present **both** sides; `@synapse/client.extract()` typed. |
| 5 | EDGES CAN'T DRIFT | ⚠ **breached** | `study.extract` is wired on **REST** but **not registered on the MCP edge**. The edges now disagree — exactly the failure this law names. |
| 6 | INVARIANTS BEFORE FEATURES | — | The mandate for §6: close 2/4/5 and M0 before wiring the sixth mock view. |

Two breaches, both cheap to close. Neither is a design flaw — they're the loose ends of a slice
that shipped fast.

---

## 6. WHAT TO DO NEXT — SEQUENCED

**A. Close the live breaches first (hours, not days):**
1. Implement `_flashcard_floor` — cloze-deletion over verbatim source text (GLASSES §4.1). Restores **Law #2**; makes `kind=flashcards` offline-safe.
2. Register `study_extract` on the MCP edge (`mcp_server.py`). Restores **Law #5** parity.
3. Reconcile the `IMPLEMENTATION_STATUS.md` scoreboard to HEAD. Kills the **§4** drift.
4. Add the missing tests the glasses log already names (extract paths + bridge `paginate()`).

**B. M0 — RECONCILE THE KERNELS (the real unlock):** port from legacy into `kernel/`, one
capability at a time, then delete the legacy copy — `sr` (FSRS-6), `planner` + ontology +
**GATEKEEPER**, `capture` + `ingest_web`, `study.due_cards`. The **gatekeeper is the long pole**:
it gates every write path. Quarantine `additional_features/`; keep `editor_core/` out.

**C. Then the mechanical backlog** — the four-move recipe per remaining view (Review → Study →
Planner → Capture → Notes → Vault). Read-path views (Review, Study, Vault) can go as soon as
their capability is ported; **write-path views (Capture, Planner, Notes) wait on the gatekeeper.**

**D. Quality rungs, behind the same signatures** — embeddings (`fastembed`) + `sqlite-vec`/FTS5/RRF,
reranker, structure-aware chunking, real ingest handlers (`pymupdf4llm` / `faster-whisper` /
`trafilatura`), Google Calendar read-only for the planner.

**E. Packaging** — Tauri sidecar: PyInstaller-bundle the kernel, spawn api+worker from Rust on
launch for a self-contained desktop app.

**Loose end worth a quick fix now:** `extensions/obsidian-synapse` calls `GET /study/due`, which
doesn't exist — either ship `/sr/due` (part of M0) or repoint the extension.

---

*Foundation's solid. Two floors need patching and the doc needs to catch up — then M0 opens the
rest of the city. Build it local-first; keep the floors under it.*

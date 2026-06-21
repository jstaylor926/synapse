# Gap-Closure Plan — code → PROJECT_ARCHITECTURE.md (v3)

> Companion to `PROJECT_ARCHITECTURE.md`. The architecture is the **target** ("design
> locked, pre-implementation"). This plan is the **route** from the current skeleton to
> that target, milestone-ordered, with files / libraries / exit criteria per item.
>
> **Status of the code today:** a working M0 kernel happy-path (offline ingest → KB →
> extractive answer, CLI + FastMCP) plus real sync PDF ops. ~8 of ~30 §4 tools exist. The
> three differentiating regimes (good hybrid retrieval, async queue, vault write-safety)
> are unbuilt, and three locked decisions are currently contradicted.
>
> **Sequencing principle:** fix the invariant violations *before* adding features. A missing
> feature is honest; a present feature that breaks an invariant (the vault writer) is a trap.

---

## Scorecard (what this plan closes)

| Regime | Architecture ref | Now | Target milestone |
|---|---|---|---|
| Extractive floor (offline, no keys) | §12, P8 | ✅ works | — |
| Kernel MCP boundary (8 tools) | §4.1 | ✅ works | — |
| Sync PDF ops (merge/split/rotate/redact/extract) | §4.2 | ✅ works | — |
| Vault write-safety (gatekeeper) | §7, §16.4 | ❌ violates | **M0 → M2** |
| One pydantic contracts package | §13 | ❌ split | **M0** |
| Hybrid retrieval (sqlite-vec+FTS5+RRF+rerank) | §8 | ❌ JSON cosine | **M1** |
| Async job queue + `job_status` protocol | §6, §4.6 | ❌ façade | **M2** |
| `sr_*`, `plan_*`, planning ontology | §4.3/4.5, §9 | ❌ absent | **M2** |
| Capture (`web_/audio_/mail_ingest`) | §4.4 | ❌ absent | **M1/M4** |
| Google Calendar read-only | §10 | ❌ absent | **M2** |
| Surfaces (cockpit/tui/glasses) | §2 | ➖ later | **M3/M4** |

---

## M0 — Foundation corrections (close the invariant gaps the doc says are already true)

The doc's M0 exit says *"every kernel tool callable over MCP with typed I/O; extractive floor
works offline; a minimal serialized vault writer lands now."* Two of those three are met; the
writer is not, and the contract is split.

### 0.1 Real serialized vault writer  ⟵ **load-bearing**
- **Now:** `synapse-engine/src/synapse_engine/kb/vault.py:write_note()` does a bare
  `path.write_text()`. `ingest/pipeline.py` calls it directly. Non-atomic, unserialized, no
  external-edit check — exactly the §16.4 "unsafeguarded write."
- **Target (§7 layers 1–2 for M0):** one serialized writer + atomic write (temp in same dir →
  `fsync` → `os.replace`).
- **Files:** new `kb/gatekeeper.py` exposing a `VaultWriter` (single worker thread draining a
  `queue.Queue`, or a process-wide lock for M0). Add an `atomic_write(path, text)` helper.
  Re-point every write site (`vault.write_note`, ingest pipeline, future study/worker writes)
  through it.
- **Libraries:** stdlib only (`os`, `tempfile`, `threading`/`queue`, `hashlib`).
- **Exit:** all programmatic vault writes funnel through one writer; a concurrency test
  (N threads writing) shows zero interleaving/corruption; no half-written file ever visible.
- **Decision you own (carry to §7.2 at M2):** on external-edit conflict, *abort-and-retry against
  new content* vs *surface a conflict*. The doc leaves this "or" — pick the policy.

### 0.2 One pydantic `contracts/` package (single source of truth)
- **Now:** kernel uses `dataclass` models (`models.py`) and returns `c.__dict__`; root
  `contracts/` is pydantic; `mcp_server.py` reaches them via a `sys.path.insert` hack.
- **Target (§13):** one `contracts/` pydantic package imported by *both* the MCP boundary and the
  in-proc call sites, so external and internal interfaces can't drift.
- **Files:** grow top-level `contracts/` → `kb.py`, `reason.py`, `study.py` (join existing
  `jobs.py`, `pdf.py`). Kernel imports these; MCP tools validate input into a model and return
  `.model_dump()` (drop `__dict__`). Make `kernel + features + contracts` one installable package.
- **Libraries:** `pydantic>=2`.
- **Exit:** no `__dict__` returns at the boundary; `pip install -e .` then `import` of
  `mcp_server` works with **no** `sys.path` manipulation.

### 0.3 Packaging / repo coherence
- **Now:** `synapse-engine` is vendored in-tree (not the `kernel/` submodule §14 describes);
  `features/pdf/sync_ops.py` imports `fitz`/`pikepdf` that appear in **no** `pyproject`.
- **Target:** one install surface; honest dependency declaration.
- **Files:** unify under one `pyproject` (or a small workspace); declare `pymupdf`, `pikepdf`,
  `mcp`, `pydantic`. Decide: keep vendored or restore `kernel/` as a submodule per §14.
- **Exit:** fresh clone → one documented install → kernel + features import cleanly.

---

## M1 — Retrieval that's actually good (highest day-one value)

Doc M1 exit: *"ask / flashcards / quiz over your real material, with citations, fast."*

### 1.1 Storage swap → sqlite-vec + FTS5
- **Now:** `kb/store.py` = single JSON file, pure-Python cosine.
- **Target (§11):** one SQLite file — `sqlite-vec` virtual table (vectors) + FTS5 table (BM25),
  behind the *same* `add/search/save` interface so callers don't move.
- **Files:** rewrite `kb/store.py`; add schema + a `rebuild_from_vault()` (index is derived).
- **Libraries:** `sqlite-vec`; stdlib `sqlite3`. **Risk to verify first:** macOS stock Python's
  `sqlite3` may lack FTS5 — confirm `SELECT * FROM pragma_compile_options` includes
  `ENABLE_FTS5`, else ship a bundled SQLite or `pysqlite3-binary`.
- **Exit:** vectors + lexical queryable from one file; delete file → rebuild from vault.

### 1.2 RRF hybrid retriever
- **Now:** `reason/retriever.py` is vector-only top-k.
- **Target (§8):** vector top-K + lexical top-K → RRF merge → candidate set (~20–50).
- **Files:** `reason/retriever.py` gains `hybrid()`; new `kb/rrf.py` (small pure function).
  Degradation (§12): no embedder → lexical-only; RRF degenerates to BM25.
- **Exit:** hybrid beats vector-only on the real CS7641 docs; lexical-only path returns when
  embeddings are absent.

### 1.3 Cross-encoder reranker (inline, bounded)
- **Target (§8):** rerank a *capped* candidate set (20→5) with a hard timeout, **inline in the
  sync query path** (not queued); missing model → fall back to RRF order.
- **Files:** new `reason/rerank.py`; config for cap + timeout.
- **Libraries:** `fastembed` rerank model (`bge-reranker-base`) or a sentence-transformers
  cross-encoder.
- **Exit:** p95 ≲ 2s on CPU at the cap; model unavailable → RRF order, query still returns.

### 1.4 Real embeddings (fastembed) behind the existing Protocol
- **Files:** add `FastEmbedEmbedder` to `kb/embeddings.py`; `SYNAPSE_EMBED_PROVIDER=fastembed`.
  Keep `HashEmbedder` as the offline floor.
- **Libraries:** `fastembed`.
- **Exit:** provider switch is one env var; hash remains the zero-config default.

### 1.5 litellm gateway + Ollama offline
- **Now:** `reason/llm.py` calls the `anthropic` SDK directly.
- **Target (§16 stack):** route through `litellm`; offline → Ollama if present, else extractive.
- **Files:** add `LiteLLMProvider` to `reason/llm.py`; keep `ExtractiveLLM` default.
- **Libraries:** `litellm` (+ local Ollama optional).
- **Exit:** key present → Anthropic via litellm; offline → Ollama/extractive; never fabricates.

### 1.6 Structure-aware chunking
- **Now:** `ingest/chunk.py` = character window (~800/150) on blank lines; no structure.
- **Target (§8):** markdown headers/AST for prose, tree-sitter for code.
- **Files:** `ingest/chunk.py` add a header splitter + a tree-sitter code path.
- **Libraries:** `tree-sitter` + `tree-sitter-languages`.
- **Exit:** chunks respect section/function boundaries; code chunks don't split mid-function.

### 1.7 PDF parse — native path wired (sync half of the router)
- **Now:** `ingest/loaders.py` does raw `fitz ... page.get_text()`; `features/pdf/async_ops.py`
  mentions `pymupdf4llm` but the worker is a `pass` stub.
- **Target (§4.2):** native `pymupdf4llm` → markdown for the sync-eligible path; Docling routes
  async (M2).
- **Files:** `ingest/loaders.py` use `pymupdf4llm.to_markdown`; route heavy parses to the queue
  once M2 exists.
- **Libraries:** `pymupdf4llm`.
- **Exit:** real CS7641 + job-search PDFs ingest to good markdown; ask/flashcards/quiz cite them.

---

## M2 — Proactive layer + async queue (the differentiator)

Doc M2 exit: *"drop an assignment → heavy ingest runs async → task plan bound to resources +
tools → scheduled against real deadlines."*

### 2.1 Persistent job queue (huey/SQLite) + worker process  ⟵ **load-bearing**
- **Now:** `async_ops.pdf_ingest_submit` returns a throwaway `uuid4`; never enqueues; workers are
  `pass` stubs; there is **no `workers/` dir**. The async regime is a façade.
- **Target (§6):** huey on the SQLite backend; a separate `workers/` consumer process;
  idempotency by content hash; bounded retry w/ backoff; results land via index (direct) or vault
  (gatekeeper).
- **Files:** new `workers/` package (Docling · Whisper · ocrmypdf · reindex consumers); a
  `job/` module (submit + status store) in the kernel; wire `async_ops` to truly enqueue.
- **Libraries:** `huey`.
- **Exit:** submit returns a *persisted* job_id; kill the kernel mid-job → job survives; worker
  drains; states `queued→running→done|failed`; re-submit of same input dedupes.

### 2.2 `job_status` / `job_list` / `job_cancel` MCP tools
- **Now:** `contracts/jobs.py` has the model; **no tool is registered**.
- **Target (§4.6):** one generic protocol for all async work.
- **Files:** register 3 tools in `mcp_server.py`, backed by the huey result store.
- **Exit:** a surface polls any async job through the one protocol.

### 2.3 Promote writer → full gatekeeper (§7 layers 3–4)
- **Adds to M0's serialize+atomic:** optimistic-concurrency (mtime+hash recheck on read-modify-
  write of frontmatter) + write-ownership partitioning (system-owned `tasks/blocks/cards/
  resources/` vs human-owned `notes/`).
- **Exit:** all four §7.2 layers present; an Obsidian edit mid-write triggers the chosen conflict
  policy (0.1), never a clobber.

### 2.4 `sr/` — spaced repetition (py-fsrs, FSRS-6)
- **Files:** `features/sr/` (`sr_add/sr_due/sr_review/sr_stats`); `contracts/sr.py`; FSRS state in
  SQLite or card frontmatter; register 4 MCP tools.
- **Libraries:** `py-fsrs`; optional Anki `.apkg` interop.
- **Exit:** rate a card → next interval via FSRS-6; due/stats query correctly.

### 2.5 `planner/` — thin orchestrator
- **Files:** `features/planner/` (`plan_breakdown/plan_schedule/plan_agenda/plan_bind/plan_run/
  plan_sync_external`); `contracts/planner.py`; register 6 MCP tools. Keep it thin — `plan_run`
  is a dispatcher to capabilities (§4.5 keep-thin rule), not a worker.
- **Exit:** assignment → tasks (bound to resources + tools) → scheduled against deadlines/review
  load.

### 2.6 Planning ontology in the vault (§9)
- **Now:** no `vault/` dir exists.
- **Files:** create `vault/{courses,assignments,tasks,topics,resources,notes,blocks,cards}/`;
  entity templates (frontmatter + `[[wikilinks]]` + an Obsidian Tasks line); **all writes via the
  gatekeeper**.
- **Exit:** entities render + Dataview-query in Obsidian; a job application models as an
  `assignment` with no new types (§9.3).

### 2.7 Google Calendar — read-only
- **Files:** a calendar reader in capture/planner; `plan_sync_external` pulls deadlines + free/busy;
  optional one-way read-only `.ics` out.
- **Libraries:** `google-api-python-client`, `calendar.readonly` scope, local OAuth token.
- **Exit:** free/busy pulled to place blocks; **never** writes back (§16.2).

---

## M3 — Surfaces
- **Glasses (`spec_view`, submodule present):** agenda + walking-quiz / STAR delivery over MCP.
- **Obsidian:** confirm vault + Tasks render; optional FSRS plugin.
- **CLI:** `plan` / `study` verbs.
- **Exit:** review on glasses + in Obsidian without touching code.

## M4 — Google services & on-demand ops
- `mail_ingest` (Gmail read-only, per-thread/label) · `web_ingest` (trafilatura) ·
  `audio_ingest` (faster-whisper) · PDF physical ops polish (`pdf_ocr` async via ocrmypdf) ·
  Tauri cockpit + TipTap card review · Textual TUI. Build each when the need is hit.

---

## Cross-cutting cleanup (decisions, not milestones)

### C1 — `additional_features/pdf` conflicts with §16.5
Implements ~25 PDF ops (`compress`, `watermark`, `sign`, `sanitize`, `office_to_pdf`,
`pdf_to_office`, `flatten`, …). §16.5 explicitly rejects *"all ~100 PDF operations (only the
handful you use)."* The handful the doc *does* want already live in `features/pdf`.
**Recommend:** quarantine or remove `additional_features/`; if any single op is genuinely used,
promote just that one into `features/pdf`. Decide before it accretes surface area.

### C2 — `editor_core/` conflicts with §1.7 / §16.5
A Python operational-transform editor engine (`model/operation/transform.py`, `differ`,
`history`, `writer`) — structurally a reverse-engineered CKEditor-style engine, which the doc
*explicitly forbids* ("reverse-engineering CKEditor's engine"). The intended editor surface is
**TipTap** at M4. **Recommend:** don't invest here; treat as experimentation and keep it out of
the kernel's dependency path.

---

## Suggested execution order (why this sequence)
1. **M0.1 + M0.2 + M0.3** — make the foundation honest (safe writes, one contract, one install).
   Nothing else should be built on top of an unsafe writer or a split contract.
2. **M1.1 → 1.3** — the retrieval swap is the single highest day-one-value change.
3. **M1.4 → 1.7** — real models + structure-aware ingest, behind the seams just hardened.
4. **M2.1 + 2.2 + 2.3** — make async real and finish the gatekeeper, *before* the features that
   depend on them.
5. **M2.4 → 2.7** — sr / planner / ontology / calendar.
6. **M3–M4** — surfaces and on-demand ops, as needs arrive.

*When reality and `PROJECT_ARCHITECTURE.md` disagree, fix one of them on purpose.*

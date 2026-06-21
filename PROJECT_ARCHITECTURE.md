# the-project — Architecture & Build Plan (v4)

> Canonical reference for the unified personal tooling platform. Crystallizes the
> design and now tracks what is actually built. Supersedes the v1–v3 drafts.
>
> **Status:** **as-built.** The kernel and its three differentiating regimes —
> good hybrid retrieval, an async job queue, and vault write-safety — exist in
> code and run offline on a fresh clone. Spaced repetition, the planner, the
> vault ontology, and most capture tools have landed. External integrations
> (Google Calendar, Gmail) and the rich surfaces (Tauri cockpit, glasses) are the
> remaining frontier.
>
> **Revision:** v4 — reconciled with the implementation. Marks each capability
> built vs. seam-stubbed, records two new realities (a second REST edge for the
> glasses; an in-house SQLite job queue instead of huey), redraws the repo layout,
> and recasts the old "locked decisions" as *current working decisions* — this is
> a personal project still being shaped, not a frozen spec.
>
> **Audience:** the builder (me), plus anyone reviewing process topology,
> contracts, and failure modes. §0 orients; §3–§13 are the detail.

A single, self-hosted, local-first platform that consolidates study, reasoning,
document processing, and planning into one system. One **kernel** (knowledge base
+ reasoning + generators) exposes capabilities to external surfaces over **MCP**
(and a thin **REST** adapter for surfaces that can't speak MCP); internal
capabilities talk over plain in-process calls, and heavy compute is pushed to an
asynchronous job queue. **Surfaces** (desktop cockpit, G2 glasses, Obsidian, Zed,
CLI) consume the edge, never the internals. School and job-search are the same
machine pointed at two vaults.

---

## 0. Executive summary (read this first)

**What it is.** A personal "second brain + planner" you run on your own machine. It
reads your study material and job-search documents, answers questions about them
with citations, makes flashcards and quizzes, and turns an assignment (or a job
application) into a scheduled plan that respects your real calendar.

**Why one system.** A class assignment and a job application are the same shape of
problem: a deadline, a pile of source material, and a set of tasks. Modeling them
identically means one engine serves both — no duplicate tooling.

**Where it stands now.** The hard structural pieces are built and run with **zero
configuration, fully offline**:

| Regime | State |
|---|---|
| Kernel MCP boundary (~31 tools) | ✅ built |
| Hybrid retrieval (SQLite FTS5 + vector + RRF, optional rerank) | ✅ built |
| Async job queue (persistent SQLite) + `job_*` protocol + worker process | ✅ built |
| Vault write-safety gatekeeper (all four §7 layers) | ✅ built |
| Spaced repetition (`sr_*`, FSRS + offline floor) | ✅ built |
| Planner + vault ontology (`plan_*`, gatekeeper-routed entities) | ✅ built (LLM/calendar seams stubbed) |
| Capture: `web_ingest` ✅ · `audio_ingest` ✅ (worker) · `mail_ingest` ⛔ (M4 seam) | partial |
| REST edge for the glasses (`api_server.py`) | ✅ built (narrow) |
| Google Calendar / Gmail read-only | ⛔ seam only |
| Surfaces: cockpit design, glasses, Obsidian, CLI | ➖ design + CLI; rich UIs later |

**The design philosophy that actually shipped.** Every quality dependency is an
*opt-in seam over an offline floor*: hash embeddings → fastembed; extractive
answers → Anthropic/litellm; a simple interval scheduler → FSRS-6; Python cosine →
sqlite-vec; rerank off → cross-encoder on. A fresh clone with no keys and no
network still does something useful, and you turn on quality one env var at a time.

**What's deliberately *not* being built** (so scope stays honest): no
multi-user/auth/cloud, no two-way calendar writing, no heavyweight agent
frameworks, no reverse-engineered editors. Rationale in §16. (These are current
working decisions, not immutable laws — the project is still being shaped.)

**Timeline shape.** Five milestones (§15). M0–M2 are largely done; the proactive
external integrations and the glasses/Obsidian/cockpit surfaces are next.

---

## 1. Principles (the invariants — revisit deliberately, not casually)

1. **Vault-as-truth.** Knowledge lives as plain markdown you can open in Obsidian,
   grep, and diff. The vector/lexical index is a *derived, rebuildable* cache —
   never the source. *(Built: `kb/store.py` is a disposable SQLite index; delete it
   and rebuild from the vault via the `reindex` job.)*
2. **The edge is a stable, typed contract.** Surfaces depend on stable tool names +
   typed I/O, never on internals. MCP is the primary edge; a thin REST adapter
   serves surfaces that can't speak MCP (the glasses). *(Built: `mcp_server.py`,
   `api_server.py`.)*
3. **External edge, internal plain calls.** The edge (MCP/REST) is *only* for
   surfaces. Internal capabilities are reached by direct in-process calls — no MCP
   internally, and no internal network either unless a capability earns its own
   process. *(Built: `features/*` are imported and called directly with shared
   pydantic contracts.)*
4. **Kernel-first.** Build the kernel + contract before any surface. Capabilities
   are modules; surfaces are thin consumers.
5. **Asynchronous heavy compute.** Anything that touches an ML model (Whisper,
   Docling, OCR) or has unbounded latency returns a `job_id` and is polled. Bounded
   sub-second→~2s work stays synchronous (§3 for the line). *(Built: `jobs/` +
   `workers/`.)*
6. **Vault write safety (single serialized gatekeeper).** The filesystem is not
   ACID. *All* programmatic writes to the vault pass through one serialized writer
   using atomic file operations, with optimistic-concurrency checks against
   external (Obsidian) edits. Reads are freely concurrent. *(Built:
   `kb/gatekeeper.py`, all four layers; §7.)*
7. **Lift algorithms, adopt embeddable libraries.** Reuse *patterns and algorithms*
   from reference repos; depend on libraries built to be embedded. Don't transplant
   organs from systems not built for donation (Stirling's server, CKEditor's
   engine).
8. **Single-user, local-first, offline-capable.** Works on a fresh clone with no
   keys (extractive floor). The MCP boundary targets localhost. *(See §16.5 for the
   current REST-binding caveat to tighten.)*
9. **Two shapes of tool.** *Operations* are stateless (inputs → outputs, e.g.
   `pdf_merge`). *Surfaces* are stateful (persistent, interactive, e.g. the editor).
   The contract and registry model both.
10. **Never fabricate.** Extractive mode answers only from retrieved text;
    generative answers carry citations back to sources. *(Built: `ExtractiveLLM` is
    the default; generated answers cite source chunks.)*

---

## 2. Architecture

```
 SURFACES   Tauri cockpit · G2 glasses (spec_view) · Obsidian · Zed · Claude Code · CLI · TUI
 (consume the edge)                       │
            ══ MCP (stable tool names) ════╪══ REST (thin, for non-MCP surfaces) ══ THE EDGE ══
 KERNEL     synapse-engine (Python)        │
            FastMCP server  +  FastAPI api_server  (the two edge adapters)
            ingest · KB [vault = truth, index = derived] · reasoning · generators · job dispatcher
            ── in-process calls (typed pydantic contracts, no transport) ────────────────────
 INTERNAL   pdf_* [parse + ops] · sr_* [FSRS] · capture [web/audio/mail] · plan_* [orchestrator]
 CAPABILITIES   (Python packages in features/, imported in-proc; a local REST/RPC seam only
                where a capability ever needs its own process — see §5)
                                          │
            ── persistent job queue (submit / poll) ─────────────────────────────────────────
 ASYNC      pdf_ingest (pymupdf4llm → Docling) · audio_ingest (faster-whisper) · pdf_ocr
 WORKERS    (ocrmypdf) · reindex   —  in-proc thread by default, or a separate workers/ process;
            results land in the index directly, in the vault via the gatekeeper
                                          │
            ──────────────────────────────┼──────────────────────────────────────────────────
 DATA       markdown vault (truth, single-writer gatekeeper)
            + SQLite index (FTS5 + vector blobs; sqlite-vec when available — derived/rebuildable)
            + SQLite job store + SQLite sr store
 EXTERNAL   Google Calendar (read-only, time source) · Gmail (read-only, on-demand) — seams, M2/M4
```

### 2.1 Three communication regimes (plus a glasses bridge)

A single-user, local-first system needs far less machinery than a distributed one.
There are **three** internal communication regimes, each with one right tool — and,
at the edge, **two** adapters because not every surface can speak MCP:

| Regime | Who | Transport | State |
|---|---|---|---|
| **Edge — MCP** | MCP surface → kernel | FastMCP | ✅ all §4 tools registered |
| **Edge — REST** | non-MCP surface (glasses) → kernel | FastAPI (`api_server.py`) | ✅ built, narrow (flashcards today) |
| **Internal sync** | kernel ↔ capability | **direct in-process call** (shared pydantic contracts) | ✅ no transport at all — the strongest "no MCP internally" |
| **Internal async** | kernel → heavy worker | **persistent job queue** (submit/poll) | ✅ SQLite-backed, in-proc thread or separate process |

The REST adapter exists because the **G2 glasses web apps can't act as MCP
clients** — they need plain HTTP. It is deliberately thin: a read-oriented shim
that calls the *same* capabilities the MCP tools do. (Current caveat: it binds
`0.0.0.0` with permissive CORS for development; tighten to localhost / explicit
origins before it's anything but a dev convenience — §16.5.)

A network REST/RPC seam *between internal capabilities* is still introduced **only**
when one earns a process boundary (independent restart, a hard RAM cap, a
non-Python dep). Until then capabilities are packages in the kernel process. The
async workers are already out-of-process-capable by construction (`workers/run.py`),
so the heavy stuff is isolated regardless.

---

## 3. Process & concurrency topology

What runs in what process, what is synchronous, and where the locks are.

```
┌─────────────────────────────────────────────────────────────────────┐
│ PROCESS A — kernel (synapse-engine)                                   │
│   • FastMCP server  (the MCP edge)                                    │
│   • FastAPI api_server  (the REST edge, for the glasses)             │
│   • sync capabilities in-proc: kb_search, reason_ask, study_*,        │
│       code_assist, pdf_merge/split/rotate/extract/redact, sr_*, plan_*│
│   • job dispatcher: submits to the SQLite job store; by default also  │
│       runs an in-proc worker thread (offline, zero-infra)             │
│   • vault gatekeeper runs here as a daemon thread (Process C-as-thread)│
│   • read path: SQLite index (WAL, shared); write path: via gatekeeper │
└─────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────┐
│ PROCESS B — async worker(s)  (optional, for crash isolation)          │
│   • python -m workers.run  → blocking consume loop on the same store  │
│   • pymupdf4llm/Docling, faster-whisper, ocrmypdf, reindex            │
│   • crash-isolated from the kernel; jobs survive a restart (persisted)│
│   • writes index rows directly; routes vault writes via the gatekeeper│
└─────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────┐
│ PROCESS C — vault writer / gatekeeper  (single serialized owner)      │
│   • the ONLY writer to .md files in the vault                         │
│   • single worker thread draining an ordered queue                    │
│   • atomic write (temp in same dir → fsync → os.replace)             │
│   • optimistic-concurrency guard vs Obsidian edits (mtime + sha256)   │
│   • runs as a daemon thread inside A today; the same serialized owner  │
│     becomes a true separate process the moment that's warranted       │
└─────────────────────────────────────────────────────────────────────┘

 EXTERNAL (read-only):  Google Calendar API · Gmail API   ← pulled, never written (seam)
 OBSIDIAN: opens the vault directly; an uncontrolled concurrent writer (see §7)
```

### 3.1 The sync/async dividing line (the rule)

- **Synchronous** (result on the same call): latency is *bounded* and small — target
  p95 ≲ 2 s. `kb_search`, `reason_ask` (bounded rerank, §8), `study_flashcards`,
  `pdf_merge`, every `plan_*` orchestration, `sr_review`.
- **Asynchronous** (returns `{job_id, status:"queued"}`): latency is *unbounded* or
  model-heavy. `pdf_ingest` (parse), `audio_ingest` (Whisper), `pdf_ocr`, full
  reindex. Polled via the one `job_status` tool (§4.6).

> **Reranking is synchronous, not queued.** A cross-encoder over a *capped*
> candidate set with a hard timeout runs **inline** in the query hot path (§8). A
> query that returned a job ticket would break the feel of asking a question. The
> queue is for **ingest-time** heavy compute, not **query-time** ranking. *(Built:
> `reason/rerank.py`, off by default, RRF-order fallback.)*

---

## 4. The edge contract (tool catalog — the spine)

Stable names, typed I/O. Status legend: **✅ built** · **◐ built with a stubbed
seam** (contract frozen, body pending) · **⛔ seam only** (raises / returns empty,
contract frozen per §13). The MCP boundary registers every tool below; internal
calls reuse the same pydantic models in `contracts/`.

### 4.1 Kernel — `synapse-engine`
| Tool | Sync? | State | Purpose |
|---|---|---|---|
| `kb_ingest` | async if heavy | ✅ | Ingest file/folder (md/txt/pdf) → chunk → embed → store; mirror to vault (gatekeeper). |
| `kb_search` | sync | ✅ | Hybrid semantic + lexical search (RRF). |
| `reason_ask` | sync | ✅ | RAG answer with cited sources (extractive floor / Anthropic / litellm). |
| `reason_multistep` | sync | ✅ | Decompose → retrieve per part → answer. |
| `study_flashcards` | sync | ✅ | Generate flashcards from the KB. |
| `study_quiz` | sync | ✅ | Generate quiz items. |
| `study_cheatsheet` | sync | ✅ | Compact markdown cheat sheet. |
| `code_assist` | sync | ✅ | Coding help grounded in ingested code/docs. |

> *Known debt:* the kernel's own kb/reason/study/code tools still return dataclass
> `__dict__` and `mcp_server.py` keeps a `sys.path.insert` shim to reach root
> `contracts/`. The pdf/sr/capture/planner/jobs tools already validate and return
> pydantic models. Finishing the migration (§13) removes both warts.

### 4.2 PDF — `features/pdf`
| Tool | Sync? | State | Notes |
|---|---|---|---|
| `pdf_ingest` | **async** | ◐ | Native `pymupdf4llm` → markdown → KB wired in the worker; Docling (math/tables) is the documented escalation behind the same handler. |
| `pdf_extract_text` | sync | ✅ | Native text extract. |
| `pdf_merge` / `pdf_split` / `pdf_rotate` | sync | ✅ | Structural ops (pikepdf/pymupdf). |
| `pdf_ocr` | **async** | ✅ | ocrmypdf via subprocess (memory isolation). |
| `pdf_redact` | sync | ✅ | Content removal. |

### 4.3 Spaced repetition — `features/sr`
| Tool | Sync? | State | Notes |
|---|---|---|---|
| `sr_add` / `sr_due` / `sr_review` / `sr_stats` | sync | ✅ | SQLite store; `SimpleScheduler` interval-ladder floor by default, FSRS-6 (`py-fsrs`) via `SYNAPSE_SR_SCHEDULER=fsrs`. |

### 4.4 Capture — `features/capture`
| Tool | Sync? | State | Notes |
|---|---|---|---|
| `web_ingest` | sync | ✅ | URL → clean markdown → KB (trafilatura). |
| `audio_ingest` | **async** | ✅ | Submits a job; faster-whisper transcribes in the worker → KB. |
| `mail_ingest` | sync | ⛔ | Contract frozen; Gmail read-only client lands in M4 (raises `NotImplementedError` today). On-demand per thread/label only — never inbox-wide. |

### 4.5 Planner — `features/planner` (orchestrator; calls capabilities in-proc)
| Tool | Sync? | State | Notes |
|---|---|---|---|
| `plan_breakdown` | sync | ◐ | Writes tasks/topics to the vault ontology; decomposition is a deterministic scaffold today (the `reason_*` LLM call is the seam). |
| `plan_schedule` | sync | ◐ | Greedy placement into free slots; `_free_slots` is the Calendar seam (one evening slot/day offline). |
| `plan_agenda` | sync | ✅ | Blocks + tasks for a date, read from the ontology. |
| `plan_bind` | sync | ✅ | Attach/edit a tool binding on a task. |
| `plan_run` | sync or async | ✅ | Dispatch table → capability; inherits its sync/async shape. |
| `plan_sync_external` | sync | ⛔ | Read-only Calendar pull; returns empty until M2.7. **Never** writes back. |

> **Planner keep-thin rule:** the planner *sequences and binds*; the work lives in
> the capability modules. `plan_run` is a dispatcher, not a worker. *(Held in code:
> `_dispatch_table` routes to `study_flashcards`/`reason_ask`/`pdf_ingest`.)*

### 4.6 Async job protocol (one protocol for all heavy work)
| Tool | State | I/O |
|---|---|---|
| `job_status` | ✅ | `(job_id)` → `{status: queued\|running\|done\|failed, progress?, result?, error?}` |
| `job_list` | ✅ | `()` → `{jobs:[{job_id, kind, status, started}]}` |
| `job_cancel` | ✅ | `(job_id)` → `{cancelled}` (best-effort; queued jobs only) |

Submission is implicit: any async tool returns `{job_id, status:"queued"}`; the
surface polls `job_status` until `done`/`failed`. Re-submitting the same input
dedupes by content hash (§6.2).

---

## 5. Internal capability interfaces

Capabilities expose the **same pydantic contracts** as the edge tools, reached by
typed Python calls — not MCP, not (by default) HTTP.

- **Default — in-process.** `features/*` are Python packages imported by the kernel
  (e.g. `pdf_merge(PdfMergeInput(...)) -> PdfMergeOutput`). Zero serialization, zero
  transport, one process to supervise. The pydantic model *is* the interface; the
  MCP/REST layers are thin adapters that validate external input and call the same
  function. *(Built: `features/__init__.py` documents this; the MCP tools are
  one-line adapters.)*
- **Escape hatch — local REST/RPC.** If a capability earns a process boundary,
  wrap *that one* behind a localhost endpoint; the contract is unchanged. No
  capability gets a network seam speculatively.
- **No MCP internally** (§16.1). MCP is an LLM-negotiation protocol with
  serialization and client-runtime overhead on both ends; deterministic
  machine-to-machine calls don't need it.

This keeps the system a single deployable by default, with a clean,
contract-preserving path to split a process when one is warranted.

---

## 6. Async compute & the job queue

Heavy, model-bound, or unbounded work runs behind a **persistent** job queue.
Persistence matters: a 20-minute Whisper transcription must survive a kernel
restart, not vanish.

### 6.1 Queue selection (what actually shipped)
v3 recommended huey/SQLite. v4 ships something even leaner: a **hand-rolled SQLite
job store + dispatcher** (`jobs/`), stdlib only, zero extra dependencies. It honors
the minimal-infra invariant harder than huey would — no new package at all — while
keeping the *exact* swap-out seam huey/RQ would have used (the §4.6 protocol).

| Option | Infra | Status |
|---|---|---|
| **In-house SQLite queue** (`jobs/store.py` + `jobs/queue.py`) | none beyond the SQLite file | ✅ **current default.** Persistent, idempotent dedupe, claim/progress/retry, in-proc thread *or* separate `workers/` process. |
| **huey (SQLite backend)** | none beyond SQLite | documented upgrade if a battle-tested scheduler/retry/cron layer is wanted. |
| **RQ (Redis)** | Redis daemon | documented upgrade for concurrent multi-worker throughput or pub/sub eventing. |

The choice sits entirely behind the job protocol, so surfaces are unaffected by any
later swap.

### 6.2 Job lifecycle & semantics (built)
- **States:** `queued → running → done | failed` (+ best-effort `cancelled`), via
  `job_status`.
- **Idempotency:** jobs key on a SHA-256 content hash of `(kind, payload)`; a
  re-submit dedupes onto the existing live job rather than reprocessing.
- **Retries:** an `attempts` counter is tracked per claim; a hard failure surfaces
  `{status:"failed", error}` with a truncated traceback — never a silent drop.
- **Results land via the right door:** workers write index rows directly (the index
  is rebuildable); any *vault* mutation goes through the gatekeeper (§7).
- **Progress:** handlers report coarse progress via `ctx.progress(fraction)` (e.g.
  pages parsed, transcription segments).

---

## 7. Vault write safety — the gatekeeper

The vault is the **truth**, and the filesystem is **not** ACID. A single mutex is
necessary but **not sufficient** — Obsidian is an uncontrolled concurrent writer to
the same files. *(All four layers below are implemented in `kb/gatekeeper.py`.)*

### 7.1 What a single writer does and does not protect
- **Protects against self-collision (fully).** All programmatic writes — frontmatter
  updates, captured notes, generated tasks/blocks/cards, worker results — funnel
  through **one serialized writer** (Process C). No two of *our* writers ever touch
  a file at once.
- **Does *not* stop Obsidian.** Obsidian writes files directly, outside our process.
  This is the real hazard and needs more than serialization.

### 7.2 The full strategy (four layers, all built)
1. **Serialize own writes.** `VaultGatekeeper` runs a single worker thread draining
   an ordered `queue.Queue`; `write()` blocks until applied.
2. **Atomic file writes.** `atomic_write` writes a temp file in the same directory,
   `fsync`s, then `os.replace`s over the target (+ a best-effort directory fsync).
   A reader never sees a half-written file; worst case is whole-file
   last-writer-wins, never mid-file corruption.
3. **Optimistic concurrency vs external edits.** `read_with_signature` records a
   `(mtime_ns, sha256)` fingerprint hashed from the *same bytes* it returns;
   `read_modify_write` re-checks at write time and, on a `WriteConflict` (Obsidian
   saved underneath us), **re-reads and retries against the new content** — never a
   blind clobber.
4. **Write-ownership classification.** `classify_owner` tags a path system-owned
   (`tasks/ blocks/ cards/ resources/` — blind atomic write is fine) vs human-owned
   (`notes/` — read-modify-write) vs unknown, so callers pick the right strategy.

Net: **writes are serialized + atomic + conflict-checked + ownership-aware; reads
stay fully concurrent.** `kb/vault.py` and `features/planner/ontology.py` both route
through the singleton gatekeeper — nothing writes the vault directly.

---

## 8. Retrieval pipeline

The school/work payoff. Hybrid retrieval with an optional reranking stage, all
degradable (§12). *(Built: `reason/retriever.py`, `kb/store.py`, `kb/rrf.py`,
`reason/rerank.py`.)*

```
 query
   │  embed (hash floor / fastembed)            ┌─ vector top-K  (cosine; sqlite-vec seam)
   ├─────────────────────────────────────────── ┤
   │  tokenize                                   └─ lexical top-K (FTS5 / BM25)
   │
   ├─ merge → RRF  → candidate set (≈ candidate_k, default 20)
   │
   ├─ cross-encoder rerank  (bge-reranker / ms-marco MiniLM)   ← INLINE, BOUNDED, OFF by default
   │     rerank candidates → top-N (default 5)
   │
   ├─ inject top-N → LLM  (extractive floor / Anthropic / litellm → Ollama offline)
   │
   └─ answer + citations back to source chunks
```

- **Storage (built):** one SQLite file — an FTS5 table (real BM25 lexical) plus
  chunk rows carrying vectors as float blobs. Vector search is a correct
  pure-Python cosine scan by default (fine at personal scale, §11); `sqlite-vec` is
  a documented fast-path seam loaded when the extension is present.
- **Hybrid + degradation (built):** vector top-K and lexical top-K are fused with
  RRF. If embeddings are absent → lexical-only; if the lexical match is empty →
  vector-only; the query always returns.
- **Reranking is inline, bounded, optional (built).** A cross-encoder over a capped
  candidate set with a hard timeout (default 2 s); over budget or model missing →
  RRF order. Off by default (`SYNAPSE_RERANK=0`) so the fresh-clone floor needs no
  model.
- **Chunking:** character-window splitter today (`ingest/chunk.py`); structure-aware
  chunking (markdown headers/AST + tree-sitter for code) is the planned upgrade.
- **Citations always.** Generative answers cite source chunks; extractive answers
  *are* source chunks. Never fabricate (§1.10).

---

## 9. The planning ontology (vault-native)

Time + work modeled as typed markdown entities with YAML frontmatter and
`[[wikilinks]]` as edges — in the vault. Actionable items also carry an **Obsidian
Tasks** line so they render and query (Dataview) in Obsidian for free. The two
edges that answer "map tasks to resources or tools" are `resources:` and
`binding:`. All mutations go through the gatekeeper (§7). *(Built:
`features/planner/ontology.py` — entity CRUD, frontmatter (de)serialization with
lists/dicts as JSON flow-YAML, gatekeeper-routed writes.)*

### 9.1 Entity types & frontmatter

```yaml
# assignments/cs7641-a2.md
type: assignment
id: cs7641-a2
course: "[[CS7641]]"
due: 2026-06-27
status: open
spec: "[[resources/cs7641-a2-spec]]"
```

```yaml
# tasks/a2-t3.md
type: task
id: a2-t3
assignment: "[[cs7641-a2]]"
topic:     ["[[topics/randomized-optimization]]"]               # what it's about
resources: ["[[resources/lecture-07]]", "[[notes/sa-vs-ga]]"]   # ← RESOURCE mapping
binding:   {"tool": "study_flashcards", "args": {"topic": "randomized optimization", "n": 15}}  # ← TOOL mapping
estimate: 45m
scheduled: 2026-06-22T18:00
status: todo
---
- [ ] Drill RO flashcards 📅 2026-06-22 ⏫
```

```yaml
# topics/randomized-optimization.md
type: topic
id: randomized-optimization
course: "[[CS7641]]"
resources: ["[[resources/lecture-07]]"]
```

```yaml
# resources/lecture-07.md
type: resource
id: lecture-07
kind: pdf            # pdf | note | url | deck | transcript | mail
source: lecture-07.pdf
doc_id: kb:abc123    # link into the KB index (derived)
```

```yaml
# blocks/blk-0622-1800.md
type: studyblock
id: blk-0622-1800
when: 2026-06-22T18:00
duration: 45m
tasks: ["[[a2-t3]]"]
calendar_ref: gcal:xyz   # read-only back-reference to the busy/free source
```

### 9.2 Edge conventions
| Edge | Frontmatter key | Meaning |
|---|---|---|
| assignment → course | `course:` | belongs to |
| assignment → spec | `spec:` | the source document |
| task → topic(s) | `topic:` | what it covers |
| **task → resource(s)** | `resources:` | **material it uses (resource mapping)** |
| **task → binding** | `binding:` | **feature tool that services it (tool mapping)** |
| studyblock → task(s) | `tasks:` | what you'll do in this block |
| topic/resource → KB | `doc_id:` | link into the derived index |

**Calendar = time axis (read-only).** Deadlines and free/busy come *in* from
Calendar/syllabus (seam); scheduled `studyblock`s are projected and, if mobile
visibility is wanted, published *out* only as a one-way read-only `.ics` feed (§10).
**Schedule** is tasks projected onto free time. **Breakdown** is how tasks get
created from an assignment (`plan_breakdown`).

### 9.3 Both faces, same ontology
A job application *is* an `assignment` (apply-by `due`) with tasks — tailor resume,
research company, drill stories — `binding`-mapped to tools (resume gen,
`web_ingest`/`mail_ingest` the JD and recruiter thread, `sr`-scheduled STAR
rehearsal). No new model.

---

## 10. External integrations (read-only by contract)

Google Calendar and Gmail are **upstream, read-only constraints** — never write
targets. *Currently seams:* `plan_sync_external` returns empty and `mail_ingest`
raises until wired (M2.7 / M4); the contracts are frozen so surfaces are stable.

| System | Direction | Scope | Behavior |
|---|---|---|---|
| **Google Calendar** | read-only in | `calendar.readonly` | Pull deadlines + free/busy to find study blocks. Optionally publish the local plan *out* as a stateless, one-way read-only `.ics` feed. Never create/edit/delete events. |
| **Gmail** | read-only, on-demand in | `gmail.readonly` | `mail_ingest` pulls a *specific* thread/label on request → clean markdown → KB. No inbox-wide polling; no sending; no labels written. |

**Trust & credentials.** OAuth tokens stored locally, read-only scopes only.
Nothing leaves the machine except explicit, user-initiated API reads. Ingested mail
is opt-in per item (per thread/label), not a mailbox slurp.

---

## 11. Storage model

- **Vault (truth):** markdown + frontmatter. Hand-editable, Obsidian-native. All
  programmatic writes via the gatekeeper (§7). Default runtime location
  `data/vault/` (`SYNAPSE_VAULT_DIR`); `Projects/` is a configured Obsidian vault in
  the repo for experimentation.
- **Index (derived, rebuildable):** one SQLite file (`data/index.db`) — FTS5 (BM25)
  + chunk vectors as blobs, fused via RRF. Vector scan is Python cosine; sqlite-vec
  loads as the fast path when present. Delete and rebuild any time (the `reindex`
  job, or `kb_ingest` on the vault).
- **Feature state:** FSRS/interval review state in `data/sr.db`; job state in
  `data/jobs.db`. Plan state lives in the vault as entities.
- **Time & inbox:** Google Calendar + Gmail, both external, read-only, never sources
  of truth.

---

## 12. Failure modes & graceful degradation

The "extractive floor" is a hard requirement and it is *built*: a fresh clone with
no keys and no network does something useful. Each step degrades independently.

| Condition | Behavior | Built? |
|---|---|---|
| **No LLM key** | Extractive mode: retrieval returns ranked source chunks as the answer, with citations. No generation, no fabrication. | ✅ default |
| **No embeddings model** | `HashEmbedder` floor (deterministic bag-of-words); flip to fastembed for quality. | ✅ default |
| **Reranker model unavailable** | Skip rerank; return RRF order. Query returns within budget. | ✅ (off by default anyway) |
| **No FSRS** | `SimpleScheduler` interval ladder; `py-fsrs` is the opt-in quality path. | ✅ default |
| **sqlite-vec absent** | Pure-Python cosine scan over vector blobs. | ✅ default |
| **Offline** | Route LLM to Ollama (via litellm) if present; otherwise extractive. Embeddings local regardless. | ✅ (litellm seam) |
| **Async worker down** | Sync tools unaffected. Submissions persist as `queued`; drain when a worker returns. | ✅ |
| **Index corrupted / missing** | Rebuild from the vault (it's derived). No data loss. | ✅ |
| **External API (GCal/Gmail) unreachable** | Planner proceeds with stub free/busy; capture reports failure. Core study/RAG unaffected. | ✅ (seam returns empty) |
| **Obsidian edited a file mid-write** | Optimistic-concurrency guard aborts + retries against new content; never a corrupt or clobbered file. | ✅ |

---

## 13. Contract evolution & versioning

- **Additive by default.** New capabilities are new tools or new *optional* fields.
- **No silent breaking changes.** A breaking change ships as a new name (e.g.
  `reason_ask` → `reason_ask_v2`); the old tool stays through a deprecation window.
- **Contracts are the single source.** pydantic models in `contracts/` define every
  tool's I/O; the edge adapters and the in-process call sites import the *same*
  models so the external contract and the internal interface can't drift.
  *(Largely built: pdf/sr/capture/planner/jobs use shared contracts; finishing the
  kernel's own kb/reason/study tools — still on dataclasses — is open debt.)*
- **Surfaces pin to tool names + field presence**, never to internals — so kernel
  refactors (swapping the queue, splitting a capability into its own process,
  wiring sqlite-vec) are invisible to them.

---

## 14. Repo layout (actual)

```
the-project/
├── synapse-engine/              # THE KERNEL (vendored in-tree)
│   └── src/synapse_engine/
│       ├── config.py · cli.py · models.py
│       ├── mcp_server.py        # MCP edge (FastMCP) — registers all §4 tools
│       ├── api_server.py        # REST edge (FastAPI) — thin, for the glasses
│       ├── ingest/              # loaders · chunk · pipeline (ingest_path/_markdown_text)
│       ├── kb/                  # store [SQLite FTS5+vec] · embeddings · vault · gatekeeper · rrf
│       ├── reason/              # retriever · rerank · engine · llm
│       ├── study/               # flashcards · quiz · cheatsheet
│       └── code/                # assistant
├── contracts/                   # shared pydantic models: kb·reason·study·pdf·sr·capture·planner·jobs
├── features/                    # in-process capabilities (§5)
│   ├── pdf/                     # sync_ops · async_ops
│   ├── sr/                      # service · scheduler (FSRS|simple) · store
│   ├── capture/                 # web · audio · mail
│   └── planner/                 # service · ontology
├── jobs/                        # persistent SQLite job queue: store · queue · registry
├── workers/                     # async worker process: handlers · run  (python -m workers.run)
├── Design_System/               # Tauri cockpit design — Synapse Cockpit.dc.html + screens (code/notes/planner/study)
├── Projects/                    # Obsidian vault (.obsidian configured)
├── spec_view/                   # G2 glasses app (git submodule)
├── ZedExtension/                # Zed PDF-tools extension (git submodule)
├── additional_features/         # ~25 extra PDF ops — QUARANTINE (conflicts §16.5; see C1)
├── editor_core/                 # OT editor engine — EXPERIMENTAL, out of kernel path (conflicts §16.5/§1.7; see C2)
├── PROJECT_ARCHITECTURE.md      # this file
├── GAP_CLOSURE_PLAN.md          # the code → architecture route (companion)
├── readme.md
└── (dev harness, not runtime)   # commands/ · contexts/ · hooks/ · personas/ · scripts/ · skills/ · schemas/
```

- **`synapse-engine` is vendored in-tree** (not a `kernel/` submodule). One install
  surface; `pip install -e` it with extras `[pdf]`/`[mcp]`/`[llm]`. *Note:* feature
  deps (`pymupdf`, `pikepdf`, `trafilatura`, `faster-whisper`, `fastembed`,
  `py-fsrs`, `litellm`, `fastapi`/`uvicorn`) are imported lazily and not all yet
  declared in `pyproject.toml` — declaring them is open packaging work.
- **The dev harness** (`commands/`, `contexts/`, `personas/`, `hooks/`, `scripts/`,
  `skills/`, `schemas/`) is Claude Code agent/automation tooling for *building* the
  project, not part of the runtime product. Kept separate by intent.
- **`additional_features/` and `editor_core/`** are present but **out of the kernel's
  dependency path** — see the cross-cutting cleanup below.

Multi-machine sync is out of scope — later via git/Syncthing/Obsidian Sync if ever
needed.

---

## 15. Build order & current status

**M0 — Kernel + contract (foundation).** ✅ **Done.** FastMCP server with the full
tool catalog; extractive floor works offline with no keys; the serialized vault
writer landed (and was promoted straight to the full gatekeeper). *Open:* finish
migrating the kernel's own kb/reason/study tools off dataclass `__dict__` and remove
the `sys.path` shim; declare lazy deps in `pyproject`.

**M1 — Retrieval that's actually good.** ✅ **Largely done.** SQLite store (FTS5 +
vector blobs) + RRF hybrid + inline bounded reranker, with the full degradation
ladder; fastembed + Anthropic/litellm wired behind seams; native PDF parse
(`pymupdf4llm`) in the worker. *Open:* structure-aware chunking (markdown AST +
tree-sitter); wire sqlite-vec as the fast vector path; ingest the real CS7641 +
job-search corpus.

**M2 — Proactive layer + async queue.** ✅ **Largely done.** Persistent SQLite job
queue + `job_*` protocol + separate worker process; the full gatekeeper; `sr/`
(FSRS + floor); `planner/` (`breakdown`/`schedule`/`agenda`/`bind`/`run`); the vault
ontology. *Open:* real LLM decomposition in `plan_breakdown`; read-only Google
Calendar in `plan_sync_external` (M2.7); Docling routing for math/tables.

**M3 — Surfaces.** ➖ **In progress.** CLI verbs exist (`ingest`/`ask`/`reason`/
`search`/`flashcards`/`quiz`/`cheatsheet`/`assist`/`stats`/`serve-mcp`); the cockpit
has a design (`Design_System/`); the glasses app (`spec_view`) and REST edge exist.
*Open:* wire the glasses to live agenda + walking-quiz/STAR; confirm Obsidian
render; `plan`/`study`/`sr` CLI verbs.

**M4 — Google services & on-demand ops.** ⛔ **Next.** `mail_ingest` (Gmail
read-only, per-thread/label); Docling/Marker polish; Tauri cockpit + TipTap card
review; Textual TUI. Build each when the need is hit.

> See `GAP_CLOSURE_PLAN.md` for the file-level route on every remaining item.

---

## 16. Current working decisions & stack

These are the decisions in force *right now*. The project is still being shaped — if
reality and a decision diverge, change one of them on purpose.

| Layer | Pick |
|---|---|
| Kernel / edge | Python · FastMCP (MCP edge) · FastAPI (REST edge for glasses) · pydantic contracts |
| Internal transport | **In-process typed calls** by default; localhost REST/RPC only where a capability needs process isolation. No MCP internally. |
| Async queue | **In-house SQLite queue** (stdlib, zero-dep) by default → huey/SQLite or RQ/Redis if a richer scheduler or concurrency demands it |
| Retrieval | SQLite **FTS5** + vector blobs, **RRF** hybrid; pure-Python cosine (sqlite-vec when available) + **cross-encoder rerank** (inline, bounded, opt-in) |
| Embeddings / LLM | `HashEmbedder` floor → `fastembed` local · extractive floor → `litellm`/Anthropic (Ollama offline) |
| PDF parse | `pymupdf4llm` (native) → Docling (math/tables, async); Marker only with GPU (GPL-3/RAIL-M) |
| Chunking | character window today → tree-sitter (code) + markdown headers/AST (planned) |
| Spaced repetition | `SimpleScheduler` floor → `py-fsrs` (FSRS-6); Anki `.apkg` interop later |
| Capture | `trafilatura` (web) · `faster-whisper` (audio) · Gmail API read-only (mail, M4) |
| Time / mail | Google Calendar (read-only, time source) · Gmail (read-only, on-demand) — seams |
| Vault / tasks | markdown + Obsidian Tasks convention; single-writer gatekeeper; Obsidian as a surface |
| Editor surface | TipTap (card review) — *not* a CKEditor-engine extraction |
| GUI / TUI | Tauri + React (design in `Design_System/`) · Textual TUI (optional) |

---

## Current "not now" list (rejected temptations, with reasoning)

Recorded so the reasoning survives — but, again, these are *working* decisions on a
personal project, not immutable law.

### 16.1 Internal server-to-server MCP routing
- **The trap.** Treating MCP as a universal microservice bus because it's already
  the external edge.
- **The reality.** MCP is for human-to-LLM and LLM-to-tool negotiation: heavy
  serialization, JSON-RPC, an MCP client runtime on *both* ends. Deterministic
  machine-to-machine calls gain nothing and pay for all of it.
- **The call.** Internal communication uses **direct in-process calls**; a
  lightweight standard transport (REST/RPC) *only* where a capability earns a
  process boundary. The MCP/REST edges expose the kernel to surfaces — never an
  internal transport. *(Held in code.)*

### 16.2 Two-way external syncing (writing back to Google Calendar)
- **The trap.** A seamless bi-directional relationship where the planner creates/
  edits/deletes external events.
- **The reality.** Two-way calendar sync is an engineering black hole: state
  machines, timezones, DST, recurring-event mutations, offline conflict resolution.
- **The call.** External systems are **upstream, read-only constraints**. The planner
  *pulls* busy blocks and **never** writes back. Mobile visibility, if wanted, is a
  **stateless, one-way, read-only `.ics` feed** — not API writes.

### 16.3 LangChain / LlamaIndex as core routing (borrow libs, don't adopt frameworks)
- **The trap.** Adopting mega-frameworks to stand up RAG/agentic routing fast.
- **The reality.** Thick abstractions obscure control flow and churn their APIs;
  debugging through wrapper classes is harder than raw Python.
- **The call.** Keep full ownership of orchestration and routing. **Borrow specific
  utilities** (a chunker, a BM25 routine, a loader); don't inherit orchestrators or
  base classes. No heavy agent frameworks in the kernel — `reason_multistep` + the
  edge suffice. *(Held: retrieval/rerank/planner are all hand-written.)*

### 16.4 Concurrent unsafeguarded writes to the `.md` vault
- **The trap.** Letting async workers, tools, and a live Obsidian session each
  read/write the `.md` files whenever they finish.
- **The reality.** The filesystem is not ACID; concurrent appends/updates race into
  corrupted markdown.
- **The call.** **All** programmatic writes pass through the **single-threaded
  gatekeeper** with **atomic operations**, **optimistic-concurrency** checks against
  Obsidian, and **ownership partitioning** by directory (§7). Reads stay concurrent.
  *(Built and load-bearing.)*

### 16.5 Other "not now"s (carried forward)
- Auth, multi-user, cloud sync, k8s, observability stacks.
- **Edge binding caveat (active to-do).** The intent is localhost-only. The MCP
  server is fine; the **REST `api_server.py` currently binds `0.0.0.0` with CORS `*`
  for dev** — tighten to localhost / explicit origins (and consider a shared-secret)
  before it's used as anything but a local convenience.
- Two-way or inbox-wide Gmail — read-only, per-thread/label, on demand; never sends.
- Per-capability poll tools — one generic `job_status` protocol (§4.6) instead.
- LangChain/LlamaIndex as *core* deps; all ~100 PDF operations (only the handful you
  use — see C1); reverse-engineering CKEditor's engine (see C2), or shipping a JVM
  for PDF.

### Cross-cutting cleanup (open)
- **C1 — `additional_features/pdf`** implements ~25 PDF ops (compress, watermark,
  sign, sanitize, office↔pdf, flatten, …) that §16.5 deprioritizes. The handful the
  design wants already live in `features/pdf`. **Plan:** quarantine; promote a single
  op only if genuinely used.
- **C2 — `editor_core/`** is a Python operational-transform editor engine —
  structurally the CKEditor-style engine §1.7 avoids. The intended editor surface is
  **TipTap** (M4). **Plan:** treat as experimentation; keep it out of the kernel's
  dependency path.

---

*This document tracks the build. When reality and this doc disagree, fix one of them
on purpose.*

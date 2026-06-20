# the-project — Architecture & Build Plan (v3)

> Canonical reference for the unified personal tooling platform. Crystallizes the
> design decisions; supersedes ad-hoc notes and the v1/v2 drafts. Drop at repo root or
> under `docs/`.
>
> **Status:** design locked, kernel-first. Pre-implementation.
> **Revision:** v3 — concurrency model, internal-transport sharpening, vault write safety,
> query-time reranking, graceful-degradation ladder, and contract-evolution policy made
> explicit for review.
>
> **Audience:** business owner (scope, value, timeline, risk) + technical consultant
> (process topology, contracts, failure modes). §0 orients the former; §3–§13 are for the latter.

A single, self-hosted, local-first platform that consolidates study, reasoning, document
processing, and planning into one system. One **kernel** (knowledge base + reasoning +
generators) exposes capabilities over **MCP** to external surfaces; internal capabilities
talk over plain in-process calls (or a lightweight local transport where process isolation
is genuinely needed), and heavy compute is pushed to an asynchronous job queue. **Surfaces**
(desktop, glasses, Obsidian, CLI) only ever speak MCP. School and job-search are the same
machine pointed at two vaults.

---

## 0. Executive summary (read this first)

**What it is.** A personal "second brain + planner" you run on your own machine. It reads your
study material and job-search documents, answers questions about them with citations, makes
flashcards and quizzes, and turns an assignment (or a job application) into a scheduled plan
that respects your real calendar.

**Why one system.** A class assignment and a job application are the same shape of problem:
a deadline, a pile of source material, and a set of tasks. Modeling them identically means one
engine serves both — no duplicate tooling.

**What changed in this revision (v1 → v3).** Three structural corrections, all driven by how
the system behaves under real use:

| # | Change | Plain-language reason |
|---|---|---|
| 1 | **MCP only at the edge.** Internal pieces no longer talk to each other in the LLM protocol. | The LLM protocol is heavy and slow for machine-to-machine chatter. It belongs at the boundary, not inside. |
| 2 | **Heavy work runs in the background.** OCR, audio transcription, and large-document parsing return a job ticket you poll, instead of freezing the app. | A 20-minute transcription must not lock up the interface. |
| 3 | **One writer owns the notes folder.** All automated edits to your markdown are serialized and made crash-safe. | Two processes writing the same file at once corrupts it. Obsidian is often open at the same time. |

**What's deliberately *not* being built** (so scope stays honest): no multi-user/auth/cloud,
no two-way calendar writing, no heavyweight agent frameworks, no reverse-engineered editors.
Full rationale in §16.

**Timeline shape.** Five milestones (§14). The first two (a working kernel + genuinely good
retrieval over real documents) deliver the bulk of day-one value; the proactive planner and
the glasses/Obsidian surfaces follow.

---

## 1. Principles (the invariants — don't violate these without revisiting this doc)

1. **Vault-as-truth.** Knowledge lives as plain markdown you can open in Obsidian, grep, and
   diff. The vector/lexical index is a *derived, rebuildable* cache — never the source.
2. **MCP tool names are the contract.** Surfaces and orchestrators depend on stable tool
   names + typed I/O, never on internals. This is the spine; everything plugs into it.
3. **External MCP, internal plain calls.** MCP is *strictly* the boundary for surfaces (UI,
   Claude, glasses, CLI). Internal capabilities are reached by direct in-process calls, or — only
   where process isolation is justified — a lightweight local transport. **Never** MCP internally.
4. **Kernel-first.** Build the kernel + contract before any surface. Capabilities are modules
   (or feature-servers); surfaces are thin consumers.
5. **Asynchronous heavy compute.** Any operation that touches an ML model (Whisper, Docling OCR)
   or whose latency is unbounded must not block a synchronous MCP call. It returns a `job_id`
   and is polled. Bounded sub-second→~2s work stays synchronous (see §3 for the dividing line).
6. **Vault write safety (single-threaded gatekeeper).** The filesystem is not ACID. *All*
   programmatic writes to the vault pass through one serialized writer using atomic file
   operations, with optimistic-concurrency checks against external (Obsidian) edits. Reads are
   freely concurrent. (§7.)
7. **Lift algorithms, adopt embeddable libraries.** Reuse *patterns and algorithms* from
   reference repos; depend on libraries built to be embedded. Don't transplant organs from
   systems not built for donation (e.g. Stirling's server, CKEditor's engine).
8. **Single-user, local-first, offline-capable.** Works on a fresh clone with no keys
   (extractive floor). The MCP boundary binds to localhost only. No auth, no multi-user, no cloud.
9. **Two shapes of tool.** *Operations* are stateless (inputs → outputs, fire-and-forget, e.g.
   `pdf_merge`). *Surfaces* are stateful (persistent, interactive, e.g. the editor). The
   contract and registry must model both.
10. **Never fabricate.** Extractive mode answers only from retrieved text; generative answers
    carry citations back to sources.

---

## 2. Architecture

```
 SURFACES   Tauri cockpit · G2 glasses (spec_view) · Obsidian · Zed · Claude Code · CLI · TUI
 (consume MCP only)                       │
            ══ MCP · stable tool names  =  THE BOUNDARY ════════════ (localhost only) ══════
 KERNEL     synapse-engine (Python · FastMCP)        │
            ingest · KB [vault = truth, index = derived] · reasoning · generators
            · unified gateway · async-job dispatcher
            ── in-process calls (typed, no transport) ────────────────────────────────────
 INTERNAL   pdf_* [parse + ops] · sr_* [FSRS] · capture [web/audio/mail] · plan_* [orchestrator]
 CAPABILITIES   (Python modules in-proc by default; a local REST/RPC seam only where a
                capability needs its own process — see §5)
                                          │
            ── persistent job queue (submit / poll) ─────────────────────────────────────
 ASYNC      Docling (math/tables) · faster-whisper (audio) · ocrmypdf · full reindex
 WORKERS    (separate process; the queue is the transport; results land in the index/vault
            via the gatekeeper)
                                          │
            ──────────────────────────────┼──────────────────────────────────────────────
 DATA       markdown vault (truth, single-writer gatekeeper)
            + SQLite index (sqlite-vec vectors + FTS5, derived/rebuildable)
 EXTERNAL   Google Calendar (read-only, time source) · Gmail (read-only, on-demand capture)
```

### 2.1 The headline shift: three communication regimes, not one

The v2 draft correctly separated the **boundary** from an **internal mesh**, but left the
internal transport as "REST / gRPC / ZeroMQ." For a single-user, local-first system that is
more machinery than the problem needs. v3 makes the distinction sharper by recognizing that
there are **three** communication regimes, each with one right tool:

| Regime | Who | Transport | Why |
|---|---|---|---|
| **Boundary** | surface → kernel | **MCP** (FastMCP, localhost) | Surfaces and LLM clients negotiate over a stable, typed tool contract. This is the *only* network seam. |
| **Internal sync** | kernel ↔ capability | **direct in-process call** (shared pydantic contracts as typed Python interfaces) | Deterministic, fast, sub-2s work. No serialization, no extra process, no network hop. The strongest possible form of "no MCP internally": no transport at all. |
| **Internal async** | kernel → heavy worker | **persistent job queue** (submit/poll) | Model-heavy or unbounded work runs out-of-band so the synchronous call returns immediately. The queue *is* the transport. |

A network REST/RPC seam between feature servers is introduced **only** when a specific
capability earns a process boundary: independent restart, a hard resource cap (e.g. pinning a
model worker's memory), or a non-Python dependency. Until then, capabilities are packages in
the kernel process. This honors the Locked NO on internal MCP (§16.1) and goes one step
further — no unnecessary internal network either.

> **Open question for review (consultant):** Does any capability need an isolated process *now*
> (e.g. to bound Docling's RAM independently, or to restart the audio worker without bouncing
> the kernel)? If yes, we stand up a single local REST seam for that capability at M2; if no,
> in-process is the M0–M2 default and REST stays an escape hatch. The async workers are already
> out-of-process by construction, so the heavy stuff is isolated regardless.

---

## 3. Process & concurrency topology

The single most important thing a reviewer should be able to see at a glance: **what runs in
what process, what is synchronous, and where the locks are.**

```
┌─────────────────────────────────────────────────────────────────────┐
│ PROCESS A — kernel (synapse-engine)                                   │
│   • FastMCP server  (localhost socket; the boundary)                  │
│   • sync capabilities in-proc: kb_search, reason_ask (bounded),       │
│       study_*, code_assist, pdf_merge/split/rotate, sr_*, plan_*      │
│   • async-job dispatcher: enqueues jobs, exposes job_status           │
│   • read path: opens SQLite index read-only / shared                  │
│   • write path: routes ALL vault writes to PROCESS C (gatekeeper)     │
└─────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────┐
│ PROCESS B — async worker(s)  (1+ consumer processes)                  │
│   • Docling, faster-whisper, ocrmypdf, full reindex                   │
│   • writes results into the index; routes vault writes via PROCESS C  │
│   • crash-isolated from the kernel; jobs survive a worker restart      │
└─────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────┐
│ PROCESS C — vault writer / gatekeeper  (single thread)                │
│   • the ONLY writer to .md files in the vault                         │
│   • serialized write queue + atomic write (temp → fsync → rename)     │
│   • optimistic-concurrency guard vs Obsidian edits (mtime/hash)       │
│   (may run as a thread inside A; conceptually a single serialized     │
│    owner regardless of where it lives)                                │
└─────────────────────────────────────────────────────────────────────┘

 EXTERNAL (read-only):  Google Calendar API · Gmail API   ← pulled, never written
 OBSIDIAN: opens the vault directly; an uncontrolled concurrent writer (see §7)
```

### 3.1 The sync/async dividing line (the rule)

The rule that decides whether a tool blocks or returns a `job_id`:

- **Synchronous** (returns a result on the same MCP call): latency is *bounded* and small —
  target p95 ≲ 2 s. Examples: `kb_search`, `reason_ask` (with bounded reranking, §8),
  `study_flashcards`, `pdf_merge`, every `plan_*` orchestration, `sr_review`.
- **Asynchronous** (returns `{job_id, status:"queued"}`): latency is *unbounded* or
  model-heavy. Examples: `pdf_ingest` routed to Docling, `audio_ingest` (Whisper), `pdf_ocr`,
  full index rebuild. Polled via a single `job_status` tool (§4.6).

> **Correction to v2:** v2 listed "semantic reranking" under async workers. Reranking is part
> of the *synchronous query response* — a query that returns a job ticket breaks the
> interactive feel of asking a question. Reranking therefore runs **inline but bounded** in the
> query hot path (small candidate set + hard timeout, §8), *not* on the job queue. The async
> queue is for **ingest-time** heavy compute, not **query-time** ranking.

---

## 4. The boundary contract (MCP tool catalog — the spine)

Stable names. Typed I/O (pydantic models in `contracts/`). `[E]` = exists in synapse-engine,
`[N]` = new. Inputs/outputs are sketches, firmed in `contracts/`. This catalog is the complete
external surface; internal calls reuse the same pydantic models as typed Python interfaces.

### 4.1 Kernel — `synapse-engine`
| Tool | Sync? | Purpose | I/O sketch |
|---|---|---|---|
| `kb_ingest` `[E]` | async if heavy | Ingest file/folder (md/txt/pdf) → chunk → embed → store; mirror to vault. Heavy parses route to the queue. | `(path)` → `{doc_id, chunks}` *or* `{job_id}` |
| `kb_search` `[E]` | sync | Hybrid semantic + keyword search (RRF) | `(query, k)` → `{hits:[{text, source, score}]}` |
| `reason_ask` `[E]` | sync | RAG answer with reranked citations | `(question)` → `{answer, citations}` |
| `reason_multistep` `[E]` | sync | Decompose → retrieve per part → answer | `(question)` → `{answer, steps, citations}` |
| `study_flashcards` `[E]` | sync | Generate flashcards from KB | `(topic, n)` → `{cards:[{front, back, source}]}` |
| `study_quiz` `[E]` | sync | Generate quiz items (+ grading) | `(topic, n)` → `{items:[{q, choices?, answer, source}]}` |
| `study_cheatsheet` `[E]` | sync | Compact markdown cheat sheet | `(topic)` → `{markdown}` |
| `code_assist` `[E]` | sync | Coding help grounded in ingested code/docs | `(query)` → `{answer, sources}` |

### 4.2 PDF — `features/pdf`
| Tool | Sync? | Purpose | I/O sketch |
|---|---|---|---|
| `pdf_ingest` `[N]` | **async** | Parse PDF → markdown → KB. Heuristic router: `pymupdf4llm` (native, sync-eligible) → Docling (math/tables, queued) | `(path\|url)` → `{job_id}` → (poll) `{doc_id, markdown, pages}` |
| `pdf_extract_text` `[N]` | sync | Raw/structured text extract (native path only) | `(path, pages?)` → `{text}` |
| `pdf_merge` / `pdf_split` / `pdf_rotate` `[N]` | sync | Structural ops (the handful you use) | `(inputs, args)` → `{out_path}` |
| `pdf_ocr` `[N]` | **async** | OCR scanned PDFs (ocrmypdf/Tesseract) | `(path)` → `{job_id}` → `{out_path}` |
| `pdf_redact` `[N]` | sync | True content removal | `(path, areas\|patterns)` → `{out_path}` |

### 4.3 Spaced repetition — `features/sr`
| Tool | Sync? | Purpose | I/O sketch |
|---|---|---|---|
| `sr_add` `[N]` | sync | Add cards to a deck | `(deck, cards)` → `{added}` |
| `sr_due` `[N]` | sync | Cards due now / on a date | `(deck?, on?)` → `{due:[card_id]}` |
| `sr_review` `[N]` | sync | Record a rating, get next interval (py-fsrs FSRS-6) | `(card_id, rating)` → `{next_due}` |
| `sr_stats` `[N]` | sync | Retention + review load | `(deck?)` → `{retention, load}` |

### 4.4 Capture — `features/capture`
| Tool | Sync? | Purpose | I/O sketch |
|---|---|---|---|
| `web_ingest` `[N]` | sync | URL → clean markdown → KB (trafilatura). JDs, dossiers, articles | `(url)` → `{doc_id, markdown}` |
| `audio_ingest` `[N]` | **async** | Audio/lecture → transcript → KB (faster-whisper) | `(path)` → `{job_id}` → `{doc_id, transcript}` |
| `mail_ingest` `[N]` | sync | Read-only pull of a *specific* Gmail thread/label → clean markdown → KB (flight receipts, project updates, recruiter threads). On-demand, never inbox-wide polling. | `(thread_id\|query)` → `{doc_id, markdown}` |

### 4.5 Planner — `features/planner` (orchestrator; calls capabilities in-proc)
| Tool | Sync? | Purpose | I/O sketch |
|---|---|---|---|
| `plan_breakdown` `[N]` | sync | LLM decomposes an assignment → tasks + topics; RAG finds resources; proposes tool bindings | `(assignment_ref)` → `{tasks, topics, resources, proposed_bindings}` |
| `plan_schedule` `[N]` | sync | Place tasks + due reviews into free study blocks, backward from deadlines | `(scope, horizon)` → `{scheduled_blocks}` |
| `plan_agenda` `[N]` | sync | What to do now / next block (drives glasses + cockpit) | `(date?)` → `{blocks, tasks}` |
| `plan_bind` `[N]` | sync | Attach/edit a tool binding on a task | `(task_ref, tool, args)` → `{binding_id}` |
| `plan_run` `[N]` | sync or async | Execute a task's bound tool (dispatches to the capability; inherits that tool's sync/async shape) | `(task_ref)` → `{result}` *or* `{job_id}` |
| `plan_sync_external` `[N]` | sync | **Read-only** pull of deadlines + free/busy from Google Calendar; optionally publish a one-way read-only `.ics` feed. Never writes back. | `()` → `{pulled, ics_url?}` |

> **Planner keep-thin rule:** the planner *sequences and binds*; the actual work lives in the
> capability modules. `plan_run` is a dispatcher, not a worker.

> **Renamed from v1/v2:** `plan_sync` → `plan_sync_external`, and its contract is now
> explicitly read-only (no push of scheduled blocks back to Google). Rationale in §10 and §16.2.

### 4.6 Async job protocol (one protocol for all heavy work)
Rather than per-capability poll tools (`pdf_poll`, `audio_poll`, …), v3 defines **one** generic
job protocol that every async tool participates in. DRY, and surfaces learn it once.

| Tool | Purpose | I/O sketch |
|---|---|---|
| `job_status` `[N]` | Status/result of any async job | `(job_id)` → `{status: queued\|running\|done\|failed, progress?, result?, error?}` |
| `job_list` `[N]` | In-flight + recent jobs (for surfaces to render activity) | `()` → `{jobs:[{job_id, kind, status, started}]}` |
| `job_cancel` `[N]` | Best-effort cancel (optional) | `(job_id)` → `{cancelled}` |

Submission is implicit: any async tool (`pdf_ingest`, `audio_ingest`, `pdf_ocr`, full reindex)
returns `{job_id, status:"queued"}`; the surface polls `job_status` until `done`/`failed`.

---

## 5. Internal capability interfaces

Internal capabilities expose the **same pydantic contracts** as the MCP tools, but are reached
by typed Python calls — not MCP, not (by default) HTTP.

- **Default — in-process.** `features/*` are Python packages imported by the kernel. The kernel
  calls e.g. `pdf.merge(MergeInput(...)) -> MergeOutput`. Zero serialization, zero transport,
  one process to supervise. The pydantic model *is* the interface; the MCP layer is a thin
  adapter that validates external input and calls the same function.
- **Escape hatch — local REST/RPC.** If a capability earns a process boundary (independent
  restart, RAM cap, non-Python dep), wrap *that one* capability behind a localhost REST (FastAPI)
  or RPC endpoint. The contract is unchanged; only the call site swaps a function call for a
  localhost request. No capability gets a network seam speculatively.
- **Never MCP internally** (§16.1). MCP is an LLM-negotiation protocol with serialization and
  client-runtime overhead on both ends; deterministic machine-to-machine calls don't need it.

This keeps the system a single deployable by default, while leaving a clean, contract-preserving
path to split a process the moment one is actually warranted.

---

## 6. Async compute & the job queue

Heavy, model-bound, or unbounded work runs in a separate **worker process** fed by a
**persistent** job queue. Persistence matters: a 20-minute Whisper transcription must survive a
kernel restart, not vanish.

### 6.1 Queue selection (a real tension — flagged for review)
The platform's invariants push hard toward *minimal infrastructure* ("one SQLite file," no
daemons, no k8s, offline-capable). A Redis-backed queue (RQ/Celery) adds a daemon and cuts
against that.

| Option | Infra | Fit |
|---|---|---|
| **huey (SQLite backend)** — *recommended default* | none beyond the SQLite file already in the stack | Single user, a handful of jobs, persistent, no daemon. Most consistent with the invariants. |
| **RQ (Redis)** — *documented upgrade path* | Redis daemon | Adopt only if concurrent multi-worker throughput or pub/sub eventing becomes necessary. Redis would then also be available as a lock backend (§7) and an optional internal bus. |
| Celery (Redis/RabbitMQ) | broker + (often) result backend | More machinery than a single-user tool needs; not recommended unless RQ proves insufficient. |

**Recommendation:** start on **huey/SQLite** to honor the minimal-infra invariant; escalate to
**RQ/Redis** only on a demonstrated concurrency need. This is a reversible decision behind the
job protocol (§4.6), so surfaces are unaffected by the choice.

### 6.2 Job lifecycle & semantics
- **States:** `queued → running → done | failed` (plus best-effort `cancelled`). Surfaced via
  `job_status`.
- **Idempotency:** jobs key on a content hash of inputs (e.g. file digest + tool + args) so a
  re-submitted ingest dedupes to the existing/result job rather than reprocessing.
- **Retries:** bounded retry with backoff for transient failures (I/O, model load); a hard
  failure surfaces `{status:"failed", error}` — never a silent drop.
- **Results land via the right door:** workers write index rows directly (the index is derived
  and rebuildable); any *vault* mutation goes through the gatekeeper (§7), never straight to disk.
- **Progress (optional):** long jobs may report coarse progress (e.g. pages parsed) for the UI.

---

## 7. Vault write safety — the gatekeeper

The vault is the **truth**, and the filesystem is **not** ACID. v3 specifies the full strategy,
because a single mutex is necessary but **not sufficient** — Obsidian is an uncontrolled
concurrent writer to the same files.

### 7.1 What a single writer does and does not protect
- **Protects against self-collision (fully).** All programmatic writes — frontmatter updates,
  captured notes, generated tasks/blocks/cards, worker results — are funneled through **one
  serialized writer** (§3, Process C). No two of *our* writers ever touch a file at once.
- **Does *not* stop Obsidian.** Obsidian writes files directly, outside our process. A mutex we
  hold means nothing to it. This is the real hazard and needs more than serialization.

### 7.2 The full strategy (four layers)
1. **Serialize own writes.** Single-threaded write queue; every mutation is one ordered job.
2. **Atomic file writes.** Write to a temp file in the same directory, `fsync`, then atomic
   `rename` over the target. A reader (including Obsidian) never sees a half-written file;
   worst case is whole-file last-writer-wins, never corruption mid-file.
3. **Optimistic concurrency vs external edits.** Before a read-modify-write (e.g. patching
   YAML), record the file's mtime+hash. At write time, re-check; if it changed underneath us
   (Obsidian saved), **abort and retry** the modify against the new content, or surface a
   conflict — never blindly overwrite an external edit.
4. **Write-ownership partitioning (the strongest mitigation).** Partition the vault by who owns
   writes:
   - **System-owned, generated:** `tasks/`, `blocks/`, `cards/`, `resources/` (frontmatter/index
     links) — the human rarely hand-edits these, so collision surface is near zero.
   - **Human-owned, authored:** `notes/`, prose in course pages — the system *appends* (e.g. a
     linked block) but avoids rewriting human prose.
   This drops the realistic collision probability far more than locking ever could.

Net: **writes are serialized + atomic + conflict-checked + partitioned; reads stay fully
concurrent.** Layer 4 is the design's actual safety; layers 1–3 are the guarantees underneath it.

---

## 8. Retrieval pipeline

The school/work payoff. Hybrid retrieval with a reranking stage, all degradable (§12).

```
 query
   │  embed (fastembed, local, fast)            ┌─ vector top-K  (sqlite-vec)
   ├───────────────────────────────────────────┤
   │  tokenize                                   └─ lexical top-K (FTS5 / BM25)
   │
   ├─ merge → RRF  → candidate set (≈ top 20–50)
   │
   ├─ cross-encoder rerank  (bge-reranker-base)   ← BOUNDED + TIMEOUT, inline (not queued)
   │     rerank candidates → top-N (≈ 5)
   │
   ├─ inject top-N → LLM  (litellm → Anthropic; or extractive floor)
   │
   └─ answer + citations back to source chunks
```

- **Chunking:** tree-sitter for code, markdown headers/AST for prose — so chunks respect
  structure (function boundaries, sections) rather than arbitrary windows.
- **Reranking is inline, bounded, and optional.** A cross-encoder over a *capped* candidate set
  (e.g. 20→5) with a hard timeout keeps the query interactive (target ≲ 2 s). On CPU the cap is
  what bounds latency. If the reranker model is unavailable, fall back to RRF order — the query
  still returns. (This is the v2 correction: rerank lives in the sync query path, not the async
  queue.)
- **Citations always.** Generative answers cite source chunks; extractive answers *are* source
  chunks. Never fabricate (§1.10).

---

## 9. The planning ontology (vault-native)

Time + work modeled as typed markdown entities with YAML frontmatter and `[[wikilinks]]` as
edges — Foundry-style, but in the vault. Actionable items also carry an **Obsidian Tasks** line
so they render and query (Dataview) in Obsidian for free. The two edges that answer "map tasks
to resources or tools" are `resources:` (resource mapping) and `binding:` (tool mapping). All
mutations to these files go through the gatekeeper (§7).

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
binding:   { tool: study_flashcards, args: { topic: "randomized optimization", n: 15 } }  # ← TOOL mapping
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

**Calendar = time axis (read-only).** Deadlines and free/busy come *in* from Calendar/syllabus;
scheduled `studyblock`s are projected and, if mobile visibility is wanted, published *out* only
as a one-way read-only `.ics` feed (§10). **Schedule** is just tasks projected onto free time.
**Breakdown** is how tasks get created from an assignment (`plan_breakdown`).

### 9.3 Both faces, same ontology
A job application *is* an `assignment` (apply-by `due`) with tasks — tailor resume, research
company, drill stories — `binding`-mapped to tools (resume gen, `web_ingest`/`mail_ingest` the
JD and recruiter thread, `sr`-scheduled STAR rehearsal). No new model.

---

## 10. External integrations (read-only by contract)

Google Calendar and Gmail are **upstream, read-only constraints** — never write targets. This
is a deliberate boundary, not a missing feature (rationale in §16.2).

| System | Direction | Scope | Behavior |
|---|---|---|---|
| **Google Calendar** | read-only in | `calendar.readonly` | Pull deadlines + free/busy to find study blocks. Optionally publish the local plan *out* as a stateless, one-way read-only `.ics` feed for mobile visibility. Never create/edit/delete events via the API. |
| **Gmail** | read-only, on-demand in | `gmail.readonly` | `mail_ingest` pulls a *specific* thread/label on request → clean markdown → KB. No inbox-wide polling; no sending; no labels written. |

**Trust & credentials.** OAuth tokens stored locally, read-only scopes only. Nothing leaves the
machine except the explicit, user-initiated API reads. Ingested mail becomes searchable in the
KB by design — the user controls exactly what is ingested (per thread/label), so this is
opt-in per item, not a mailbox slurp.

---

## 11. Storage model

- **Vault (truth):** markdown + frontmatter. Hand-editable, Obsidian-native. **All programmatic
  writes via the single-writer gatekeeper** (§7).
- **Index (derived, rebuildable):** one SQLite file — `sqlite-vec` vectors + FTS5 (BM25), merged
  via RRF for hybrid retrieval. Delete and rebuild any time. (LanceDB only if brute-force is ever
  outgrown, which a personal vault won't.)
- **Feature state:** FSRS review logs in SQLite (or card frontmatter). Plan state lives in the
  vault as entities.
- **Jobs:** persistent queue store (huey/SQLite by default; §6).
- **Time & inbox:** Google Calendar (time constraints) + Gmail (communications), both external,
  read-only, never sources of truth.

---

## 12. Failure modes & graceful degradation

The "extractive floor" is a hard requirement: a fresh clone with **no keys and no network**
must still do something useful. The system degrades in well-defined steps rather than failing.

| Condition | Behavior |
|---|---|
| **No LLM key** | Extractive mode: retrieval returns ranked source chunks as the answer, with citations. No generation, no fabrication. |
| **No embeddings model** | Lexical-only retrieval (FTS5/BM25). Vector half of the hybrid is skipped; RRF degenerates to BM25 order. |
| **Reranker model unavailable** | Skip rerank; return RRF order (§8). Query still returns within budget. |
| **Offline** | Route LLM to local Ollama if present; otherwise extractive. fastembed runs locally regardless. |
| **Async worker down / queue unavailable** | Sync tools unaffected. Async submissions fail fast with a clear `failed` status (no silent loss); jobs drain when the worker returns. |
| **Index corrupted / missing** | Rebuild from the vault (it's derived). No data loss — the vault is truth. |
| **External API (GCal/Gmail) unreachable** | Planner uses last-pulled constraints / proceeds without them; capture tools report the failure. Core study/RAG unaffected. |
| **Obsidian edited a file mid-write** | Optimistic-concurrency guard aborts+retries against new content (§7.2); never a corrupt or clobbered file. |

---

## 13. Contract evolution & versioning

"MCP tool names are the contract" (§1.2) implies a discipline for changing them without breaking
surfaces.

- **Additive by default.** New capabilities are new tools or new *optional* fields. Existing
  tool signatures don't change shape under a surface that depends on them.
- **No silent breaking changes.** A breaking change to a tool ships as a new name
  (e.g. `reason_ask` → `reason_ask_v2`); the old tool is kept through a deprecation window.
- **Contracts are the single source.** pydantic models in `contracts/` define every tool's I/O;
  the MCP boundary and the in-process call sites import the *same* models, so the external
  contract and the internal interface can never drift apart.
- **Surfaces pin to tool names + field presence**, never to internals — so kernel refactors
  (e.g. swapping huey for RQ, or splitting a capability into its own process) are invisible to
  them.

---

## 14. Repo layout

```
the-project/
├── kernel/                # synapse-engine (git submodule) — the MCP boundary + sync capabilities
├── features/
│   ├── pdf/               # pdf_*  (pymupdf4llm · Docling · pikepdf · ocrmypdf)
│   ├── sr/                # sr_*   (py-fsrs, FSRS-6)
│   ├── capture/           # web_* · audio_* · mail_*  (trafilatura · faster-whisper · Gmail API)
│   └── planner/           # plan_* orchestrator (in-proc client of the others)
├── workers/               # async consumers (Docling · Whisper · ocrmypdf · reindex)
├── surfaces/
│   ├── spec_view/         # G2 glasses (git submodule) — agenda + quiz/STAR delivery
│   ├── cockpit/           # Tauri + React + TipTap (later)
│   └── tui/               # Textual TUI (optional)
├── contracts/             # pydantic models for every tool — the shared spine (boundary + internal)
├── vault/                 # markdown source-of-truth (local; Obsidian opens this directly)
│   └── courses/ assignments/ tasks/ topics/ resources/ notes/ blocks/ cards/
├── docs/ARCHITECTURE.md   # this file
└── readme.md
```

`vault/` is local-first (gitignored or a separate Obsidian vault path). Multi-machine sync is
out of scope — later via git/Syncthing/Obsidian Sync if ever needed.

---

## 15. Build order (kernel-first; the three things that matter first lead)

**M0 — Kernel + contract (foundation).**
Harden `synapse-engine`; freeze the tool catalog (§4) as pydantic models in `contracts/`; serve
it via FastMCP (localhost). Stand up the in-process capability call convention. Land a **minimal
serialized vault writer** now (even before the full gatekeeper) so nothing ever writes the vault
unguarded.
*Exit:* every kernel tool callable over MCP with typed I/O; extractive floor works offline, no keys.

**M1 — Retrieval that's actually good (the school payoff — highest leverage).**
Swap JSON store → `sqlite-vec` + FTS5 + RRF hybrid. Add the inline, bounded **cross-encoder
reranker** before context injection. Parsing router (`pymupdf4llm` native → Docling). Heading/AST
chunking (tree-sitter + markdown headers). Ingest your *real* CS7641 + job-search docs. Wire real
embeddings (`fastembed`) + Anthropic LLM (via `litellm`) behind the seams.
*Exit:* ask / flashcards / quiz over your real material, with citations, fast.

**M2 — Proactive layer + async queue (the differentiator).**
Stand up the persistent job queue (huey/SQLite) + worker process for Docling/Whisper/OCR, behind
the `job_status` protocol. Promote the vault writer to the full **gatekeeper** (atomic writes +
optimistic concurrency + ownership partitioning). `sr/` server (py-fsrs FSRS-6). `planner/`
(`plan_breakdown` + `plan_schedule` + `plan_agenda`). Read-only Google Calendar sync. The planning
ontology in the vault.
*Exit:* drop an assignment → heavy ingest runs async → get a task plan bound to resources + tools
→ scheduled against your real deadlines and review load.

**M3 — Surfaces.**
Glasses (`spec_view`): agenda + walking-quiz / STAR delivery. Obsidian: confirm vault + Tasks
render; optional FSRS plugin. CLI: `plan` / `study` verbs.
*Exit:* review on glasses + in Obsidian without touching code.

**M4 — Google services & on-demand ops.**
`mail_ingest` for specific thread/label processing. PDF physical ops (`pdf_merge`/`split`/`ocr`/
`redact`). `web_ingest` / `audio_ingest` polish. Tauri cockpit + TipTap card review. Textual TUI.
Build each only when you hit the need.

---

## 16. Locked decisions & stack

| Layer | Pick |
|---|---|
| Kernel / boundary | Python · FastMCP (localhost) · pydantic contracts |
| Internal transport | **In-process typed calls** by default; localhost REST/RPC only where a capability needs process isolation. **No MCP internally.** |
| Async queue | **huey (SQLite backend)** by default → RQ/Redis if concurrency demands it |
| Retrieval | `sqlite-vec` + SQLite FTS5, RRF hybrid (LanceDB if outgrown) + **cross-encoder rerank** (inline, bounded) |
| PDF parse | `pymupdf4llm` (native, sync-eligible) → Docling (math/tables, async); Marker only with GPU (note GPL-3 / RAIL-M license) |
| Chunking | tree-sitter (code) + markdown headers/AST |
| Embeddings / LLM | `fastembed` local · `litellm` gateway · Ollama offline · Anthropic for quality; extractive default as floor |
| Spaced repetition | `py-fsrs` (FSRS-6); Anki `.apkg` interop |
| Capture | `trafilatura` (web) · `faster-whisper` (audio) · Gmail API (read-only mail) |
| Time / mail | Google Calendar (read-only, time source) · Gmail (read-only, on-demand) |
| Vault / tasks | markdown + Obsidian Tasks convention; single-writer gatekeeper; Obsidian as a surface |
| Editor surface | TipTap (card review) — *not* a CKEditor-engine extraction |
| GUI / TUI | Tauri + React (later) · Textual TUI (optional) |

---

## Explicitly out of scope (Locked NO)

These are not omissions; they are rejected architectural temptations. Each entry records the
**trap**, the **reality**, and the **ruling**, so the reasoning survives long after the urge to
revisit it.

### 16.1 Internal server-to-server MCP routing
- **The trap.** Treating MCP as a universal microservice bus, just because it's already used for
  the external boundary.
- **The reality.** MCP is designed for human-to-LLM and LLM-to-tool negotiation. It carries heavy
  serialization, relies on stringified JSON-RPC (often over `stdio` or SSE), and requires an MCP
  client runtime on *both* ends of every request. Deterministic machine-to-machine calls between
  feature modules gain nothing from that and pay for all of it.
- **The ruling.** Internal communication uses **direct in-process calls** by default, and a
  lightweight standard transport (REST / gRPC / a message bus) *only* where a capability earns a
  process boundary. **MCP is strictly the boundary** that exposes the unified kernel to external
  surfaces (Claude, UI, glasses, CLI) — never an internal transport.

### 16.2 Two-way external syncing (writing back to Google Calendar)
- **The trap.** Building a seamless bi-directional relationship where the local planner creates,
  edits, or deletes events on an external platform.
- **The reality.** Two-way calendar sync is a notorious engineering black hole: complex state
  machines, timezone offsets, daylight-saving transitions, recurring-event mutations, and conflict
  resolution when an event is modified locally and on mobile offline at once.
- **The ruling.** External systems (Calendar, Gmail) are **upstream, read-only constraints**. The
  planner *pulls* "busy" blocks to schedule against, and **never** writes back to the external API.
  If mobile visibility of the local schedule is wanted, the system publishes a **stateless,
  one-way, read-only `.ics` feed** — not API writes.

### 16.3 LangChain / LlamaIndex as core routing (borrow libs, don't adopt frameworks)
- **The trap.** Adopting mega-frameworks to stand up RAG and agentic routing fast, assuming they
  save time.
- **The reality.** Heavyweight frameworks introduce thick abstraction layers, obscure the control
  flow, and change their APIs frequently. When a router hallucinates or a retrieval pipeline fails,
  debugging through framework-specific wrapper classes is much harder than debugging raw Python.
- **The ruling.** We keep full ownership of orchestration and routing. We happily **borrow specific
  utilities** — a text chunker, a BM25 scoring routine, a reference loader — but we do **not**
  inherit their orchestrators or base classes. Control flow stays explicit and transparent.
  (Corollary: no heavy agent frameworks — LangGraph / CrewAI / smolagents — in the kernel;
  `reason_multistep` + MCP suffices.)

### 16.4 Concurrent unsafeguarded writes to the `.md` vault
- **The trap.** Letting async workers, tools, and the user's live Obsidian session each read and
  write the `.md` files whenever they happen to finish.
- **The reality.** The local filesystem is not an ACID database. If an async Docling parse finishes
  and appends YAML frontmatter at the same millisecond the planner updates that file's task status,
  you get race conditions, file-lock collisions, and corrupted markdown.
- **The ruling.** Vault write safety is paramount. **All** programmatic writes pass through a
  **single-threaded gatekeeper** (serialized write queue) using **atomic file operations**, with
  **optimistic-concurrency** checks against external (Obsidian) edits and **write-ownership
  partitioning** by directory (§7). Reads stay highly concurrent; writes are serialized to
  guarantee the integrity of the plaintext truth.

### 16.5 Other locked NOs (carried forward)
- Auth, multi-user, cloud sync, k8s, observability stacks.
- Remote/network exposure of the MCP boundary — it binds to **localhost only**.
- Two-way or inbox-wide Gmail integration — read-only, per-thread/label, on demand; **never sends**.
- Per-capability poll tools — one generic `job_status` protocol (§4.6) instead.
- LangChain / LlamaIndex as *core* dependencies; all ~100 PDF operations (only the handful you use);
  a custom vector index (`sqlite-vec` exists); reverse-engineering CKEditor's engine, or shipping a
  JVM for PDF.

---

*This document is the contract. When reality and this doc disagree, fix one of them on purpose.*

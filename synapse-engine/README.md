# Synapse Engine

A **personal study + reasoning engine**. Ingest your material (notes, course PDFs,
code), build a queryable knowledge base, and **study and reason over it with
citations** — from a CLI or over **MCP**.

It fuses two ideas from the portfolio into one runnable thing:

- **Code Study Buddy** — ingest course/code material, then generate flashcards,
  quizzes, cheat sheets, and grounded coding help.
- **Personal Reasoning Engine** — retrieval-augmented Q&A and multi-step reasoning
  over *your own* archive, answers tied back to sources.

> **Status: runnable skeleton.** The core path runs **fully offline, no API keys**,
> using deterministic hash embeddings + an extractive answerer. Every model is a
> pluggable seam you swap for a real embedder / LLM / vector DB via config.

---

## Why it's built this way

Two design rules keep the skeleton honest and the upgrade path clean:

1. **Markdown vault is the source of truth; the vector index is derived.** Your
   knowledge lives as plain markdown you can open in Obsidian, grep, and diff. The
   store is a throwaway index you can rebuild. (Same "model is truth, views are
   disposable" principle as the rest of the portfolio.)
2. **Offline-first, with seams everywhere.** It works on a fresh clone with zero
   setup, and it **never fabricates** — extractive mode answers only from retrieved
   text. Point `*_PROVIDER` settings at real models when you want quality.

---

## Architecture

```
  CLI  ·  MCP server  ────────────────  surfaces / clients
                  │
                  ▼
        ReasoningEngine  ─────────────  ask · multi-step reason
          │          │
   Retriever      study/ + code/  ────  flashcards · quiz · cheatsheet · code help
          │          │
          ▼          ▼
     VectorStore   (all read the same KB)
          ▲
          │  embed + index
     Ingest pipeline  ───────────────   load → chunk → embed → store
          ▲                                         │ mirror
          │                                         ▼
   sources (md/txt/pdf)              Markdown vault  (source of truth)
```

| Layer | Module | Job |
|---|---|---|
| Ingest | `ingest/` | load md/txt/pdf → chunk → embed → store; mirror sources into the vault |
| Knowledge base | `kb/` | embeddings (pluggable), JSON vector store (cosine), markdown vault |
| Reasoning | `reason/` | retriever, pluggable LLM (extractive default), RAG + multi-step engine |
| Study | `study/` | flashcards, quizzes (+ grading), cheat sheets |
| Code buddy | `code/` | coding help grounded in your ingested code/docs |
| Surfaces | `cli.py`, `mcp_server.py` | a CLI and an MCP server over the same engine |

---

## Quickstart (offline, no keys)

```bash
cd synapse-engine
pip install -e .                      # core is dependency-free

# the CLI entrypoint is `synapse`; if it isn't on PATH, use the module form:
python -m synapse_engine.cli ingest examples/sample_notes
python -m synapse_engine.cli ask "what is backpropagation?"
python -m synapse_engine.cli flashcards backpropagation -n 5
python -m synapse_engine.cli quiz "sliding window" -n 3
python -m synapse_engine.cli cheatsheet backpropagation
python -m synapse_engine.cli assist "longest substring without repeating characters"
python -m synapse_engine.cli stats
```

Or via `make`: `make install && make ingest-sample && make ask Q="what is backpropagation?"`.

Run the test suite with `pip install -e ".[dev]" && pytest -q` (6 tests, ~0.03s).

---

## MCP contract (the portfolio seam)

`pip install -e ".[mcp]"` then `python -m synapse_engine.cli serve-mcp`. Any MCP
client — Claude Code (`claude-reference`), a glasses app (`spec_view`), the Zed
agent panel (`ZedExtension`) — can call:

| Tool | Purpose |
|---|---|
| `kb_ingest(path)` | Ingest a file/folder (md/txt/pdf) |
| `kb_search(query, k)` | Semantic search |
| `reason_ask(question)` | RAG answer with citations |
| `reason_multistep(question)` | Decompose → retrieve per part → answer |
| `study_flashcards(topic, n)` | Generate flashcards |
| `study_quiz(topic, n)` | Generate quiz items |
| `study_cheatsheet(topic)` | Compact markdown cheat sheet |
| `code_assist(query)` | Coding help grounded in your KB |

These tool names are the stable contract — surfaces depend on them, not on the
internals.

## Swapping in real models

| Want | Do | Touches |
|---|---|---|
| Better retrieval | set `SYNAPSE_EMBED_PROVIDER` + add a class | `kb/embeddings.py` |
| Synthesized answers | `pip install -e ".[llm]"`, set `SYNAPSE_LLM_PROVIDER=anthropic` + `ANTHROPIC_API_KEY` | `reason/llm.py` |
| Real vector DB (Chroma/Qdrant/pgvector) | implement the `add/search/save` interface | `kb/store.py` |
| PDF ingest | `pip install -e ".[pdf]"` (PyMuPDF) | `ingest/loaders.py` |

Each is a single-file change behind an existing interface — nothing else moves.

---

## How it maps to the two source ideas

| Source concept | Where it lives |
|---|---|
| **Code Study Buddy** — study + coding help | `study/` (flashcards, quiz, cheatsheet) + `code/assistant.py` |
| **Personal Reasoning Engine** — RAG over your archive | `reason/engine.py` (`ask`, `reason`) + `kb/` |

Same backend, two faces — which is exactly how the portfolio is meant to compose.

## Project layout

```
synapse-engine/
├── src/synapse_engine/
│   ├── config.py · models.py
│   ├── ingest/  (loaders · chunk · pipeline)
│   ├── kb/      (embeddings · store · vault)
│   ├── reason/  (retriever · llm · engine)
│   ├── study/   (flashcards · quiz · cheatsheet)
│   ├── code/    (assistant)
│   ├── cli.py · mcp_server.py
├── examples/sample_notes/   (bundled demo material)
├── tests/                   (pytest)
└── data/                    (vault + store — gitignored, local)
```

---

## Roadmap

- **Now (skeleton):** offline ingest → KB → RAG + study generators, CLI + MCP. ✅
- **Next:** real embeddings + a real vector DB; LLM-backed flashcard/quiz quality;
  PDF + code-aware chunking (respect function/heading boundaries).
- **Then:** incremental re-index + a file watcher on the vault; a lightweight web
  review surface (CKEditor) over generated cards.
- **Portfolio:** ship as a standalone Synapse Faster tool *and* wire its MCP server
  into `claude-reference`, `spec_view`, and `ZedExtension` — standalone-first,
  network-effects-second.

## License

MIT

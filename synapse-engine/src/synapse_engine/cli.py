"""Command-line interface for Synapse Engine."""
from __future__ import annotations

import argparse
import sys

from .config import Config
from .code.assistant import assist
from .ingest.pipeline import ingest_path
from .reason.engine import ReasoningEngine
from .reason.retriever import Retriever
from .study.cheatsheet import make_cheatsheet
from .study.flashcards import make_flashcards
from .study.quiz import make_quiz


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="synapse", description="Personal study + reasoning engine.")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("ingest", help="ingest a file or folder")
    s.add_argument("path")

    s = sub.add_parser("ask", help="answer a question from the KB")
    s.add_argument("question")
    s.add_argument("-k", type=int, default=None)

    s = sub.add_parser("reason", help="multi-step answer from the KB")
    s.add_argument("question")

    s = sub.add_parser("search", help="semantic search")
    s.add_argument("query")
    s.add_argument("-k", type=int, default=5)

    s = sub.add_parser("flashcards", help="make flashcards for a topic")
    s.add_argument("topic")
    s.add_argument("-n", type=int, default=8)

    s = sub.add_parser("quiz", help="make a quiz for a topic")
    s.add_argument("topic")
    s.add_argument("-n", type=int, default=5)

    s = sub.add_parser("cheatsheet", help="make a cheat sheet for a topic")
    s.add_argument("topic")

    s = sub.add_parser("assist", help="coding help grounded in your KB")
    s.add_argument("query")

    sub.add_parser("stats", help="knowledge-base stats")
    sub.add_parser("serve-mcp", help="run the MCP server")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    config = Config.load()

    if args.cmd == "ingest":
        result = ingest_path(args.path, config)
        print(f"Ingested {result['files']} file(s), added {result['chunks_added']} chunk(s).")
        for src in result["sources"]:
            print(f"  + {src}")
        return 0

    if args.cmd == "ask":
        print(ReasoningEngine(config).ask(args.question, args.k).render())
        return 0

    if args.cmd == "reason":
        print(ReasoningEngine(config).reason(args.question).render())
        return 0

    if args.cmd == "search":
        for c in Retriever(config).citations(args.query, args.k):
            print(f"[{c.score:.2f}] {c.source}\n    {c.snippet[:160]}…")
        return 0

    if args.cmd == "flashcards":
        cards = make_flashcards(config, args.topic, args.n)
        if not cards:
            print("No flashcards — ingest sources first.")
        for i, c in enumerate(cards, 1):
            print(f"{i}. Q: {c.front}\n   A: {c.back}\n")
        return 0

    if args.cmd == "quiz":
        items = make_quiz(config, args.topic, args.n)
        if not items:
            print("No quiz items — ingest sources first.")
        for i, it in enumerate(items, 1):
            print(f"{i}. {it.question}\n   (answer: {it.answer})\n")
        return 0

    if args.cmd == "cheatsheet":
        print(make_cheatsheet(config, args.topic))
        return 0

    if args.cmd == "assist":
        print(assist(config, args.query).render())
        return 0

    if args.cmd == "stats":
        from .kb.store import VectorStore
        store = VectorStore(config.store_path)
        print(f"chunks: {store.size}")
        print(f"sources: {len(store.sources())}")
        print(f"vault:  {config.vault_dir}")
        print(f"store:  {config.store_path}")
        print(f"embed:  {config.embed_provider} (dim {config.embed_dim})  llm: {config.llm_provider}")
        return 0

    if args.cmd == "serve-mcp":
        from .mcp_server import main as serve
        serve()
        return 0

    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

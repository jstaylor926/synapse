"""Synapse Engine — a personal study + reasoning engine.

Fuses two ideas:
  * "Code Study Buddy"        — ingest course/code material, then generate
                                flashcards, quizzes, cheat sheets, and code help.
  * "Personal Reasoning Engine" — retrieval-augmented reasoning over your own
                                archive (notes, PDFs, code), with citations.

The core path runs fully offline (no API keys) using deterministic hash
embeddings + an extractive answerer, and every model is a pluggable seam you can
swap for a real embedder / LLM via config. MCP-native so it plugs into the
Synapse Faster portfolio.
"""

__version__ = "0.1.0"

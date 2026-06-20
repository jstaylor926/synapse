"""Reasoning over the knowledge base.

LLM-backed question answering and synthesis grounded in retrieved vault
context. Routes through litellm so it runs locally on Ollama by default and
upgrades to Anthropic when a key is configured.
"""

from __future__ import annotations


def answer(question: str, k: int = 8) -> str:
    """Answer a question grounded in the top-`k` retrieved chunks. Stub."""
    raise NotImplementedError

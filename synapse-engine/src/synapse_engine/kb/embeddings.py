"""Embeddings — a pluggable seam.

Default `HashEmbedder` is deterministic, offline, and dependency-free: it hashes
tokens into a fixed-dimension bag-of-words vector and L2-normalizes. Good enough
to make retrieval *work* out of the box; swap in a real model for quality.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

_TOKEN = re.compile(r"[a-z0-9]+")


class Embedder(Protocol):
    dim: int
    def embed(self, text: str) -> list[float]: ...


class HashEmbedder:
    """Deterministic, offline floor. Good enough to make retrieval *work* with
    zero deps; swap to fastembed for quality."""

    def __init__(self, dim: int = 512) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in _TOKEN.findall(text.lower()):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            vec[h % self.dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm:
            vec = [v / norm for v in vec]
        return vec


class FastEmbedEmbedder:  # pragma: no cover - exercised only when fastembed present
    """Local sentence embeddings via fastembed (the locked stack). Runs on CPU,
    no API key, downloads the model once. Quality path for vector retrieval."""

    def __init__(self, model_name: str) -> None:
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=model_name)
        # Probe the dimension once with a throwaway embedding.
        self.dim = len(next(iter(self._model.embed(["_"]))))

    def embed(self, text: str) -> list[float]:
        return list(next(iter(self._model.embed([text]))))


def get_embedder(config) -> Embedder:
    provider = getattr(config, "embed_provider", "hash")
    if provider == "hash":
        return HashEmbedder(dim=config.embed_dim)
    if provider == "fastembed":
        return FastEmbedEmbedder(getattr(config, "embed_model", "BAAI/bge-small-en-v1.5"))
    raise ValueError(
        f"Unknown SYNAPSE_EMBED_PROVIDER={provider!r}. "
        "Use 'hash' (offline) or 'fastembed' (local quality)."
    )

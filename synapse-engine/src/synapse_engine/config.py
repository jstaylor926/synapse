"""Configuration — loaded from environment / a local .env file.

Every setting has a default that keeps the engine fully offline, so a fresh
clone runs with zero configuration. Point the *_PROVIDER settings at real
models when you're ready.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (no dependency). KEY=VALUE per line, # comments."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


@dataclass(frozen=True)
class Config:
    data_dir: Path
    vault_dir: Path
    store_path: Path
    embed_provider: str
    embed_dim: int
    embed_model: str
    llm_provider: str
    llm_model: str
    top_k: int
    # Hybrid retrieval (§8)
    candidate_k: int          # RRF candidate pool size before rerank
    rerank_enabled: bool
    rerank_model: str
    rerank_candidates: int    # hard cap on candidates fed to the cross-encoder
    rerank_timeout: float     # seconds; over budget → RRF order

    @classmethod
    def load(cls, root: Path | None = None) -> "Config":
        root = root or Path.cwd()
        _load_dotenv(root / ".env")
        data_dir = Path(os.environ.get("SYNAPSE_DATA_DIR", root / "data")).resolve()
        vault_dir = Path(os.environ.get("SYNAPSE_VAULT_DIR", data_dir / "vault")).resolve()
        data_dir.mkdir(parents=True, exist_ok=True)
        vault_dir.mkdir(parents=True, exist_ok=True)

        def _flag(name: str, default: str = "0") -> bool:
            return os.environ.get(name, default).lower() in ("1", "true", "yes", "on")

        return cls(
            data_dir=data_dir,
            vault_dir=vault_dir,
            # SQLite index (sqlite-vec + FTS5), derived & rebuildable (§11).
            store_path=data_dir / "index.db",
            embed_provider=os.environ.get("SYNAPSE_EMBED_PROVIDER", "hash"),
            embed_dim=int(os.environ.get("SYNAPSE_EMBED_DIM", "512")),
            embed_model=os.environ.get("SYNAPSE_EMBED_MODEL", "BAAI/bge-small-en-v1.5"),
            llm_provider=os.environ.get("SYNAPSE_LLM_PROVIDER", "extractive"),
            llm_model=os.environ.get("SYNAPSE_LLM_MODEL", "claude-sonnet-4-6"),
            top_k=int(os.environ.get("SYNAPSE_TOP_K", "5")),
            candidate_k=int(os.environ.get("SYNAPSE_CANDIDATE_K", "20")),
            # Rerank is off by default so the fresh-clone floor needs no model;
            # flip SYNAPSE_RERANK=1 once a cross-encoder is installed.
            rerank_enabled=_flag("SYNAPSE_RERANK", "0"),
            rerank_model=os.environ.get("SYNAPSE_RERANK_MODEL", "Xenova/ms-marco-MiniLM-L-6-v2"),
            rerank_candidates=int(os.environ.get("SYNAPSE_RERANK_CANDIDATES", "20")),
            rerank_timeout=float(os.environ.get("SYNAPSE_RERANK_TIMEOUT", "2.0")),
        )

"""Runtime configuration for the kernel.

All paths default to the repo-local `data/` tree so the platform is fully
local-first out of the box. Override any value with a `SYNAPSE_`-prefixed
environment variable (or a `.env` file), e.g. `SYNAPSE_VAULT_DIR=/path/to/vault`.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# kernel/src/synapse_engine/config.py -> repo root is four parents up.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DATA = _REPO_ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SYNAPSE_",
        env_file=".env",
        extra="ignore",
    )

    # --- Storage -----------------------------------------------------------
    vault_dir: Path = Field(default=_DATA / "vault", description="Obsidian-compatible Markdown vault (the source of truth).")
    db_dir: Path = Field(default=_DATA / "db", description="Derived, rebuildable SQLite indexes.")

    # --- Edges -------------------------------------------------------------
    api_host: str = "127.0.0.1"
    api_port: int = 8765

    # --- Models ------------------------------------------------------------
    # Local-first defaults; gracefully upgrade to cloud when a key is present.
    llm_model: str = "ollama/llama3.1"
    anthropic_api_key: str | None = None
    embed_model: str = "BAAI/bge-small-en-v1.5"

    @property
    def index_db(self) -> Path:
        return self.db_dir / "index.db"

    @property
    def jobs_db(self) -> Path:
        return self.db_dir / "jobs.db"

    @property
    def sr_db(self) -> Path:
        return self.db_dir / "sr.db"

    def ensure_dirs(self) -> None:
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.db_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()

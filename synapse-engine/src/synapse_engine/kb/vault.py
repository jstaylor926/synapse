"""The markdown vault — the human-readable source of truth.

Ingested sources and generated study material are written here as plain
markdown with YAML frontmatter, so the knowledge base stays tool-independent
(open it in Obsidian, grep it, diff it). The vector store is a derived index.

All programmatic writes route through the single-writer gatekeeper (§7) — this
module never touches the filesystem directly.
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Any

from .gatekeeper import get_gatekeeper


def _slug(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s or "note"


def _render_note(title: str, body: str, frontmatter: dict[str, Any] | None) -> str:
    fm = {"title": title, "created": _dt.date.today().isoformat()}
    fm.update(frontmatter or {})
    lines = ["---"]
    for key, value in fm.items():
        lines.append(f"{key}: {value}")
    lines += ["---", "", body.strip(), ""]
    return "\n".join(lines)


def write_note(vault_dir: Path, title: str, body: str,
               frontmatter: dict[str, Any] | None = None) -> Path:
    """Write a generated mirror/study note. These are system-owned (§7.2 layer
    4), so a blind atomic write through the gatekeeper is correct."""
    path = Path(vault_dir) / f"{_slug(title)}.md"
    get_gatekeeper().blind_write(path, _render_note(title, body, frontmatter))
    return path


def list_notes(vault_dir: Path) -> list[Path]:
    return sorted(Path(vault_dir).glob("*.md"))

"""Vault planning ontology (§9) — typed markdown entities, gatekeeper-safe.

Entities are markdown files with YAML frontmatter and ``[[wikilinks]]`` as edges.
Complex frontmatter values (lists, the ``binding`` mapping) are emitted as JSON,
which is valid YAML *flow* syntax — so files stay Obsidian-native and round-trip
without a YAML dependency.

Writes route through the gatekeeper (§7). Generated entities (tasks/blocks/cards/
resources) are system-owned: created with a blind atomic write, mutated with a
read-modify-write so an Obsidian edit underneath us is never clobbered.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from synapse_engine.kb.gatekeeper import get_gatekeeper

from .. import data_dir

# entity type → vault subdirectory (matches §14 / §7.2 ownership partitioning).
_DIRS = {
    "assignment": "assignments",
    "task": "tasks",
    "topic": "topics",
    "resource": "resources",
    "studyblock": "blocks",
}


def vault_dir() -> Path:
    d = Path(os.environ.get("SYNAPSE_VAULT_DIR", data_dir() / "vault")).resolve()
    return d


def entity_path(kind: str, entity_id: str) -> Path:
    if kind not in _DIRS:
        raise ValueError(f"unknown entity kind: {kind!r}")
    return vault_dir() / _DIRS[kind] / f"{entity_id}.md"


# -- frontmatter (de)serialization ----------------------------------------
def dump_frontmatter(fm: Dict[str, Any], body: str = "", tasks_line: Optional[str] = None) -> str:
    lines = ["---"]
    for key, value in fm.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            lines.append(f"{key}: {value}")
        else:  # list / dict → JSON (valid YAML flow form)
            lines.append(f"{key}: {json.dumps(value)}")
    lines.append("---")
    if tasks_line:  # Obsidian Tasks line so it renders/queries for free (§9)
        lines += ["", tasks_line]
    if body:
        lines += ["", body.strip()]
    lines.append("")
    return "\n".join(lines)


def parse_frontmatter(text: str) -> tuple[Dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    _, _, rest = text.partition("---\n")
    fm_block, _, body = rest.partition("\n---")
    fm: Dict[str, Any] = {}
    for line in fm_block.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, _, raw = line.partition(":")
        raw = raw.strip()
        try:
            fm[key.strip()] = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            fm[key.strip()] = raw
    # Strip only the leading blank lines after the closing delimiter — NOT
    # leading '-', which would eat an Obsidian Tasks checkbox ("- [ ] …").
    return fm, body.lstrip("\n")


# -- entity CRUD (gatekeeper-routed) ---------------------------------------
def write_entity(kind: str, entity_id: str, frontmatter: Dict[str, Any],
                 body: str = "", tasks_line: Optional[str] = None) -> Path:
    path = entity_path(kind, entity_id)
    fm = {"type": kind, "id": entity_id, **frontmatter}
    content = dump_frontmatter(fm, body=body, tasks_line=tasks_line)
    get_gatekeeper().blind_write(path, content)
    return path


def read_entity(kind: str, entity_id: str) -> Optional[Dict[str, Any]]:
    path = entity_path(kind, entity_id)
    if not path.exists():
        return None
    fm, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
    return fm


def update_frontmatter(kind: str, entity_id: str, changes: Dict[str, Any]) -> Path:
    """Conflict-safe frontmatter patch (§7.2 layer 3). Re-reads + re-applies if
    Obsidian saved underneath us."""
    path = entity_path(kind, entity_id)

    def transform(current: Optional[str]) -> str:
        if current is None:
            fm: Dict[str, Any] = {"type": kind, "id": entity_id}
            body, tasks_line = "", None
        else:
            fm, body = parse_frontmatter(current)
            tasks_line = None
        fm.update(changes)
        return dump_frontmatter(fm, body=body, tasks_line=tasks_line)

    get_gatekeeper().read_modify_write(path, transform)
    return path


def list_entities(kind: str) -> List[Dict[str, Any]]:
    folder = vault_dir() / _DIRS[kind]
    if not folder.exists():
        return []
    out = []
    for path in sorted(folder.glob("*.md")):
        fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        if fm:
            out.append(fm)
    return out

"""Quick capture into the vault.

All writes go through the Vault Gatekeeper (a serialized single-writer) so
concurrent internal writes never corrupt the non-ACID Markdown vault, and
optimistic concurrency checks guard against clobbering direct Obsidian edits.
"""

from __future__ import annotations


def capture_note(text: str, *, folder: str = "inbox") -> str:
    """Append a captured note to the vault; returns its vault-relative path. Stub."""
    raise NotImplementedError

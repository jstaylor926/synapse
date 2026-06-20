# data/

Machine-local data. **Not committed** (only the `.gitkeep` placeholders are).

- `vault/` — the Obsidian-compatible Markdown vault. This is the source of truth.
  Point Obsidian at this folder, or set `SYNAPSE_VAULT_DIR` to an existing vault.
- `db/` — derived, rebuildable SQLite indexes: `index.db` (FTS5 + sqlite-vec),
  `jobs.db` (job queue), `sr.db` (FSRS-6 spaced-repetition state).

Because the indexes are derived, you can delete `db/` at any time and the kernel
will rebuild it from the vault.

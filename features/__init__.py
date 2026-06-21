"""Internal capabilities (§5).

Python packages imported by the kernel and reached by typed in-process calls —
never MCP internally. Each capability binds to the shared ``contracts`` models.
"""
from __future__ import annotations

import os
from pathlib import Path


def data_dir() -> Path:
    """Resolve the local data directory (feature state, job store, indexes).

    Mirrors the kernel's ``Config`` resolution so a capability invoked
    standalone lands in the same place as one invoked by the kernel.
    """
    d = Path(os.environ.get("SYNAPSE_DATA_DIR", Path.cwd() / "data")).resolve()
    d.mkdir(parents=True, exist_ok=True)
    return d


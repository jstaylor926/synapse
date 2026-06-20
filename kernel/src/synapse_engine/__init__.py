"""Synapse kernel.

The kernel exposes platform capabilities over two edges:

- **FastMCP** (`synapse_engine.mcp_server`) — the primary edge consumed by the
  desktop cockpit, Obsidian, and code editors.
- **FastAPI** (`synapse_engine.api_server`) — a thin REST edge for surfaces that
  cannot speak MCP (e.g. the AR glasses bridge).

Surfaces talk only to these edges; they never reach into the internals.
"""

__version__ = "0.1.0"

"""web_ingest (§4.4) — URL → clean markdown → KB (trafilatura).

Sync and bounded (one fetch + extract). JDs, dossiers, articles. The extracted
markdown lands in the KB + vault through the kernel ingest path.
"""
from __future__ import annotations

from contracts.capture import WebIngestInput, WebIngestOutput


def web_ingest(inp: WebIngestInput) -> WebIngestOutput:
    try:
        import trafilatura
    except ImportError as exc:
        raise RuntimeError("web_ingest needs trafilatura (pip install trafilatura)") from exc

    downloaded = trafilatura.fetch_url(inp.url)
    if not downloaded:
        raise RuntimeError(f"could not fetch {inp.url}")
    markdown = trafilatura.extract(downloaded, output_format="markdown", url=inp.url)
    if not markdown:
        raise RuntimeError(f"no extractable content at {inp.url}")

    from synapse_engine.config import Config
    from synapse_engine.ingest.pipeline import ingest_markdown_text

    doc_id = ingest_markdown_text(markdown, source=inp.url, kind="url", config=Config.load())
    return WebIngestOutput(doc_id=doc_id, markdown=markdown)

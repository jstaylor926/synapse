"""mail_ingest (§4.4, §10) — read-only pull of a *specific* Gmail thread/label.

On-demand only: never inbox-wide polling, never sending, never writing labels
(§16.5). The user controls exactly what is ingested (per thread/label), so this
is opt-in per item. Cleaned to markdown and ingested into the KB.
"""
from __future__ import annotations

from contracts.capture import MailIngestInput, MailIngestOutput


def mail_ingest(inp: MailIngestInput) -> MailIngestOutput:
    if not (inp.thread_id or inp.query):
        raise ValueError("mail_ingest requires a thread_id or a query")

    # SEAM: Gmail API, gmail.readonly scope, local OAuth token (§10).
    #   service = _gmail_service()                      # read-only client
    #   thread  = _resolve_thread(service, inp)         # thread_id or first query hit
    #   markdown = _thread_to_markdown(thread)          # headers + bodies, cleaned
    # Wired in M4; the contract + call site are fixed now so surfaces are stable.
    raise NotImplementedError(
        "mail_ingest: Gmail read-only client lands in M4; contract is frozen (§13)."
    )

    # When wired, the tail mirrors web_ingest:
    #   from synapse_engine.config import Config
    #   from synapse_engine.ingest.pipeline import ingest_markdown_text
    #   doc_id = ingest_markdown_text(markdown, source=f"gmail:{thread_id}",
    #                                 kind="mail", config=Config.load())
    #   return MailIngestOutput(doc_id=doc_id, markdown=markdown)

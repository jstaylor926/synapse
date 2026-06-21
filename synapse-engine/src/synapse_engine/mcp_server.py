"""MCP server — exposes the engine as tools any MCP client (Claude Code, the
glasses app, the Zed agent panel) can call. This is the portfolio seam.

Run:  synapse serve-mcp        (needs `pip install -e '.[mcp]'`)
"""
from __future__ import annotations

from .config import Config
from .code.assistant import assist
from .ingest.pipeline import ingest_path
from .reason.engine import ReasoningEngine
from .reason.retriever import Retriever
from .study.cheatsheet import make_cheatsheet
from .study.flashcards import make_flashcards
from .study.quiz import make_quiz

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))


def build_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("MCP server needs the extra: pip install -e '.[mcp]'") from exc

    config = Config.load()
    mcp = FastMCP("synapse-engine")

    @mcp.tool()
    def kb_ingest(path: str) -> dict:
        """Ingest a file or folder (md/txt/pdf) into the knowledge base."""
        return ingest_path(path, config)

    @mcp.tool()
    def kb_search(query: str, k: int = 5) -> list[dict]:
        """Semantic search over the knowledge base."""
        return [
            {"source": c.source, "score": round(c.score, 3), "snippet": c.snippet}
            for c in Retriever(config).citations(query, k)
        ]

    @mcp.tool()
    def reason_ask(question: str) -> dict:
        """Answer a question from the knowledge base, with citations."""
        a = ReasoningEngine(config).ask(question)
        return {"answer": a.answer, "citations": [c.__dict__ for c in a.citations]}

    @mcp.tool()
    def reason_multistep(question: str) -> dict:
        """Decompose a multi-part question, retrieve per part, then answer."""
        a = ReasoningEngine(config).reason(question)
        return {"answer": a.answer, "citations": [c.__dict__ for c in a.citations]}

    @mcp.tool()
    def study_flashcards(topic: str, n: int = 8) -> list[dict]:
        """Generate flashcards for a topic from the knowledge base."""
        return [c.__dict__ for c in make_flashcards(config, topic, n)]

    @mcp.tool()
    def study_quiz(topic: str, n: int = 5) -> list[dict]:
        """Generate quiz questions for a topic."""
        return [q.__dict__ for q in make_quiz(config, topic, n)]

    @mcp.tool()
    def study_cheatsheet(topic: str) -> str:
        """Generate a compact markdown cheat sheet for a topic."""
        return make_cheatsheet(config, topic)

    @mcp.tool()
    def code_assist(query: str) -> dict:
        """Coding help grounded in your ingested code/docs."""
        a = assist(config, query)
        return {"answer": a.answer, "citations": [c.__dict__ for c in a.citations]}

    @mcp.tool()
    def pdf_ingest(path_or_url: str) -> dict:
        """Ingest a PDF file or URL. Runs asynchronously and returns a job_id."""
        from features.pdf.async_ops import pdf_ingest_submit
        from contracts.pdf import PdfIngestInput
        return pdf_ingest_submit(PdfIngestInput(path_or_url=path_or_url)).model_dump()

    @mcp.tool()
    def pdf_extract_text(path: str, pages: list[int] | None = None) -> dict:
        """Extract raw text from a PDF."""
        from features.pdf.sync_ops import pdf_extract_text
        from contracts.pdf import PdfExtractTextInput
        return pdf_extract_text(PdfExtractTextInput(path=path, pages=pages)).model_dump()

    @mcp.tool()
    def pdf_merge(input_paths: list[str], output_path: str | None = None) -> dict:
        """Merge multiple PDFs into one."""
        from features.pdf.sync_ops import pdf_merge
        from contracts.pdf import PdfMergeInput
        return pdf_merge(PdfMergeInput(input_paths=input_paths, output_path=output_path)).model_dump()

    @mcp.tool()
    def pdf_split(path: str, page_ranges: list[str], output_dir: str | None = None) -> dict:
        """Split a PDF into multiple parts."""
        from features.pdf.sync_ops import pdf_split
        from contracts.pdf import PdfSplitInput
        return pdf_split(PdfSplitInput(path=path, page_ranges=page_ranges, output_dir=output_dir)).model_dump()

    @mcp.tool()
    def pdf_rotate(path: str, angle: int, pages: list[int] | None = None, output_path: str | None = None) -> dict:
        """Rotate specific pages of a PDF."""
        from features.pdf.sync_ops import pdf_rotate
        from contracts.pdf import PdfRotateInput
        return pdf_rotate(PdfRotateInput(path=path, angle=angle, pages=pages, output_path=output_path)).model_dump()

    @mcp.tool()
    def pdf_ocr(path: str, output_path: str | None = None, languages: list[str] | None = None) -> dict:
        """Perform OCR on a PDF. Runs asynchronously and returns a job_id."""
        from features.pdf.async_ops import pdf_ocr_submit
        from contracts.pdf import PdfOcrInput
        return pdf_ocr_submit(PdfOcrInput(path=path, output_path=output_path, languages=languages)).model_dump()

    @mcp.tool()
    def pdf_redact(path: str, patterns: list[str] | None = None, output_path: str | None = None) -> dict:
        """Redact text matching patterns from a PDF."""
        from features.pdf.sync_ops import pdf_redact
        from contracts.pdf import PdfRedactInput
        return pdf_redact(PdfRedactInput(path=path, patterns=patterns, output_path=output_path)).model_dump()

    # -- spaced repetition (features/sr) -----------------------------------
    @mcp.tool()
    def sr_add(deck: str, cards: list[dict]) -> dict:
        """Add cards to a deck (cards: [{front, back}])."""
        from features.sr import sr_add as _sr_add
        from contracts.sr import SrAddInput
        return _sr_add(SrAddInput(deck=deck, cards=cards)).model_dump()

    @mcp.tool()
    def sr_due(deck: str | None = None, on: str | None = None) -> dict:
        """Cards due now (or on an ISO date)."""
        from features.sr import sr_due as _sr_due
        from contracts.sr import SrDueInput
        return _sr_due(SrDueInput(deck=deck, on=on)).model_dump()

    @mcp.tool()
    def sr_review(card_id: str, rating: int) -> dict:
        """Record a review rating (1=Again..4=Easy), get the next interval (FSRS)."""
        from features.sr import sr_review as _sr_review
        from contracts.sr import SrReviewInput
        return _sr_review(SrReviewInput(card_id=card_id, rating=rating)).model_dump()

    @mcp.tool()
    def sr_stats(deck: str | None = None) -> dict:
        """Retention + review load for a deck."""
        from features.sr import sr_stats as _sr_stats
        from contracts.sr import SrStatsInput
        return _sr_stats(SrStatsInput(deck=deck)).model_dump()

    # -- capture (features/capture) ----------------------------------------
    @mcp.tool()
    def web_ingest(url: str) -> dict:
        """URL → clean markdown → KB (trafilatura)."""
        from features.capture import web_ingest as _web_ingest
        from contracts.capture import WebIngestInput
        return _web_ingest(WebIngestInput(url=url)).model_dump()

    @mcp.tool()
    def audio_ingest(path: str) -> dict:
        """Audio/lecture → transcript → KB. Async; returns a job_id."""
        from features.capture import audio_ingest_submit
        from contracts.capture import AudioIngestInput
        return audio_ingest_submit(AudioIngestInput(path=path)).model_dump()

    @mcp.tool()
    def mail_ingest(thread_id: str | None = None, query: str | None = None) -> dict:
        """Read-only pull of a specific Gmail thread/label → markdown → KB."""
        from features.capture import mail_ingest as _mail_ingest
        from contracts.capture import MailIngestInput
        return _mail_ingest(MailIngestInput(thread_id=thread_id, query=query)).model_dump()

    # -- planner (features/planner) ----------------------------------------
    @mcp.tool()
    def plan_breakdown(assignment_ref: str) -> dict:
        """Decompose an assignment → tasks + topics; propose tool bindings."""
        from features.planner import plan_breakdown as _fn
        from contracts.planner import PlanBreakdownInput
        return _fn(PlanBreakdownInput(assignment_ref=assignment_ref)).model_dump()

    @mcp.tool()
    def plan_schedule(scope: str, horizon: str = "2w") -> dict:
        """Place tasks into free study blocks, backward from deadlines."""
        from features.planner import plan_schedule as _fn
        from contracts.planner import PlanScheduleInput
        return _fn(PlanScheduleInput(scope=scope, horizon=horizon)).model_dump()

    @mcp.tool()
    def plan_agenda(date: str | None = None) -> dict:
        """What to do now / next block (drives glasses + cockpit)."""
        from features.planner import plan_agenda as _fn
        from contracts.planner import PlanAgendaInput
        return _fn(PlanAgendaInput(date=date)).model_dump()

    @mcp.tool()
    def plan_bind(task_ref: str, tool: str, args: dict | None = None) -> dict:
        """Attach/edit a tool binding on a task."""
        from features.planner import plan_bind as _fn
        from contracts.planner import PlanBindInput
        return _fn(PlanBindInput(task_ref=task_ref, tool=tool, args=args or {})).model_dump()

    @mcp.tool()
    def plan_run(task_ref: str) -> dict:
        """Execute a task's bound tool (sync result or async job_id)."""
        from features.planner import plan_run as _fn
        from contracts.planner import PlanRunInput
        return _fn(PlanRunInput(task_ref=task_ref)).model_dump()

    @mcp.tool()
    def plan_sync_external() -> dict:
        """Read-only pull of deadlines + free/busy from Google Calendar."""
        from features.planner import plan_sync_external as _fn
        return _fn().model_dump()

    # -- async job protocol (§4.6) -----------------------------------------
    @mcp.tool()
    def job_status(job_id: str) -> dict:
        """Status/result of any async job."""
        from jobs import get_default_queue
        return get_default_queue().status(job_id).model_dump()

    @mcp.tool()
    def job_list() -> dict:
        """In-flight + recent jobs."""
        from jobs import get_default_queue
        return get_default_queue().list().model_dump()

    @mcp.tool()
    def job_cancel(job_id: str) -> dict:
        """Best-effort cancel of a queued job."""
        from jobs import get_default_queue
        return get_default_queue().cancel(job_id).model_dump()

    return mcp


def main() -> None:  # pragma: no cover
    build_server().run()


if __name__ == "__main__":  # pragma: no cover
    main()

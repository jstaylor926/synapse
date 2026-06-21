"""Planner service (§4.5) — orchestration over the ontology + capabilities.

Real control flow with explicit seams: assignment decomposition is the LLM seam
(``_decompose``), free/busy is the calendar seam (``_free_slots``). The dispatch
table in ``plan_run`` is the keep-thin boundary — it routes to capabilities and
inherits their sync/async shape, never doing the work itself.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any, Callable, Dict, List

from contracts.planner import (
    Binding,
    PlanAgendaInput,
    PlanAgendaOutput,
    PlanBindInput,
    PlanBindOutput,
    PlanBreakdownInput,
    PlanBreakdownOutput,
    PlanRunInput,
    PlanRunOutput,
    PlanScheduleInput,
    PlanScheduleOutput,
    PlanSyncExternalOutput,
    ScheduledBlock,
    Task,
    Topic,
)

from . import ontology


# -- breakdown -------------------------------------------------------------
def _decompose(assignment_ref: str, assignment_fm: Dict[str, Any]) -> tuple[
    List[Task], List[Topic], List[Binding]
]:
    """SEAM: an LLM decomposes the assignment + RAG finds resources. For now a
    deterministic scaffold so the ontology + scheduling path is exercisable;
    swap the body for a ``reason_*`` call without changing the signature."""
    base = assignment_ref
    tasks = [
        Task(id=f"{base}-t1", title="Gather + read source material", assignment=base,
             estimate="45m", status="todo",
             binding=Binding(tool="reason_ask", args={"question": f"summarize {base}"})),
        Task(id=f"{base}-t2", title="Draft", assignment=base, estimate="90m",
             status="todo"),
        Task(id=f"{base}-t3", title="Drill key concepts", assignment=base,
             estimate="30m", status="todo",
             binding=Binding(tool="study_flashcards", args={"topic": base, "n": 15})),
    ]
    topics = [Topic(id=f"{base}-topic", course=assignment_fm.get("course"))]
    proposed = [t.binding for t in tasks if t.binding]
    return tasks, topics, proposed


def plan_breakdown(inp: PlanBreakdownInput) -> PlanBreakdownOutput:
    fm = ontology.read_entity("assignment", inp.assignment_ref) or {}
    tasks, topics, proposed = _decompose(inp.assignment_ref, fm)
    for task in tasks:
        ontology.write_entity(
            "task", task.id,
            {k: v for k, v in task.model_dump().items()
             if k not in ("id",) and v not in (None, [], {})},
            tasks_line=f"- [ ] {task.title}",
        )
    for topic in topics:
        ontology.write_entity("topic", topic.id,
                              {k: v for k, v in topic.model_dump().items()
                               if k != "id" and v not in (None, [], {})})
    return PlanBreakdownOutput(tasks=tasks, topics=topics, proposed_bindings=proposed)


# -- schedule --------------------------------------------------------------
def _parse_estimate(estimate: str | None) -> int:
    """'45m' / '2h' → minutes (default 45)."""
    if not estimate:
        return 45
    estimate = estimate.strip().lower()
    try:
        if estimate.endswith("h"):
            return int(float(estimate[:-1]) * 60)
        if estimate.endswith("m"):
            return int(estimate[:-1])
        return int(estimate)
    except ValueError:
        return 45


def _free_slots(horizon_days: int) -> List[_dt.datetime]:
    """SEAM: pull free/busy from Google Calendar (read-only, §10). Stub yields one
    evening study slot per day so the scheduler is exercisable offline."""
    today = _dt.datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
    return [today + _dt.timedelta(days=d) for d in range(horizon_days)]


def plan_schedule(inp: PlanScheduleInput) -> PlanScheduleOutput:
    tasks = [
        t for t in ontology.list_entities("task")
        if t.get("status", "todo") == "todo"
        and (inp.scope in ("all", t.get("assignment")) or inp.scope == t.get("id"))
    ]
    horizon_days = max(1, _parse_estimate(inp.horizon) // (60 * 24) or 14)
    slots = _free_slots(horizon_days)
    blocks: List[ScheduledBlock] = []
    for task, slot in zip(tasks, slots):  # one task per slot (simple greedy)
        block_id = f"blk-{slot.strftime('%m%d-%H%M')}"
        minutes = _parse_estimate(task.get("estimate"))
        block = ScheduledBlock(id=block_id, when=slot.replace(microsecond=0).isoformat(),
                               duration=f"{minutes}m", tasks=[task["id"]])
        blocks.append(block)
        ontology.write_entity("studyblock", block_id,
                              {"when": block.when, "duration": block.duration,
                               "tasks": block.tasks})
        ontology.update_frontmatter("task", task["id"], {"scheduled": block.when})
    return PlanScheduleOutput(scheduled_blocks=blocks)


def plan_agenda(inp: PlanAgendaInput) -> PlanAgendaOutput:
    target = inp.date or _dt.date.today().isoformat()
    blocks = [
        ScheduledBlock(**{k: b.get(k) for k in ("id", "when", "duration", "tasks", "calendar_ref")
                          if k in b})
        for b in ontology.list_entities("studyblock")
        if str(b.get("when", "")).startswith(target)
    ]
    task_ids = {tid for b in blocks for tid in b.tasks}
    tasks = [Task(**{k: t.get(k) for k in Task.model_fields if k in t})
             for t in ontology.list_entities("task") if t.get("id") in task_ids]
    return PlanAgendaOutput(blocks=blocks, tasks=tasks)


# -- bind + run ------------------------------------------------------------
def plan_bind(inp: PlanBindInput) -> PlanBindOutput:
    ontology.update_frontmatter("task", inp.task_ref,
                               {"binding": {"tool": inp.tool, "args": inp.args}})
    return PlanBindOutput(binding_id=f"{inp.task_ref}:{inp.tool}")


def _dispatch_table() -> Dict[str, Callable[[Dict[str, Any]], PlanRunOutput]]:
    """Maps a bound tool to its capability. Sync tools return a result; async
    tools return a job ticket (§4.5: plan_run inherits the tool's shape)."""
    def sync(fn):  # adapt a capability call into a PlanRunOutput(result=…)
        return lambda args: PlanRunOutput(result=fn(args))

    def study_flashcards(args):
        from synapse_engine.config import Config
        from synapse_engine.study.flashcards import make_flashcards
        cards = make_flashcards(Config.load(), args.get("topic", ""), args.get("n", 8))
        return {"cards": [c.__dict__ for c in cards]}

    def reason_ask(args):
        from synapse_engine.config import Config
        from synapse_engine.reason.engine import ReasoningEngine
        a = ReasoningEngine(Config.load()).ask(args.get("question", ""))
        return {"answer": a.answer}

    def pdf_ingest(args):
        from contracts.pdf import PdfIngestInput
        from features.pdf.async_ops import pdf_ingest_submit
        return PlanRunOutput(job_id=pdf_ingest_submit(PdfIngestInput(**args)).job_id)

    return {
        "study_flashcards": sync(study_flashcards),
        "reason_ask": sync(reason_ask),
        "pdf_ingest": pdf_ingest,  # already returns PlanRunOutput (async)
    }


def plan_run(inp: PlanRunInput) -> PlanRunOutput:
    task = ontology.read_entity("task", inp.task_ref)
    if not task or not task.get("binding"):
        raise ValueError(f"task {inp.task_ref!r} has no binding to run")
    binding = task["binding"]
    tool, args = binding["tool"], binding.get("args", {})
    table = _dispatch_table()
    if tool not in table:
        raise ValueError(f"plan_run cannot dispatch tool={tool!r} yet")
    return table[tool](args)


def plan_sync_external() -> PlanSyncExternalOutput:
    """SEAM: read-only Google Calendar pull (§10). Never writes back."""
    # from features.capture.calendar import pull_freebusy  (M2.7)
    return PlanSyncExternalOutput(pulled=0, ics_url=None)

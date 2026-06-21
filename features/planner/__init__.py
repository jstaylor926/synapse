"""Planner (§4.5) — orchestrator over the vault planning ontology (§9).

Keep-thin rule: the planner *sequences and binds*; the real work lives in the
capability modules. ``plan_run`` is a dispatcher, not a worker.
"""
from .service import (
    plan_agenda,
    plan_bind,
    plan_breakdown,
    plan_run,
    plan_schedule,
    plan_sync_external,
)

__all__ = [
    "plan_breakdown",
    "plan_schedule",
    "plan_agenda",
    "plan_bind",
    "plan_run",
    "plan_sync_external",
]

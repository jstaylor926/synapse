"""Planner & ontology.

Tracks vault-native entities (tasks, assignments, topics) and dynamically
schedules study/work blocks against real-world deadlines, reading availability
from Google Calendar (read-only).
"""

from __future__ import annotations

from contracts.models import Task


def open_tasks() -> list[Task]:
    """Return all open tasks parsed from the vault ontology. Stub."""
    raise NotImplementedError


def schedule_blocks(tasks: list[Task]) -> list[dict]:
    """Schedule blocks for `tasks` against free time before each deadline. Stub."""
    raise NotImplementedError

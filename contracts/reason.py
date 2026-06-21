"""Reasoning tool contracts (§4.1).

`reason_ask` and `reason_multistep` share one answer shape; multistep adds the
sub-question trail. `Citation` is defined here and reused across study/code
contracts so a "source pointer" means exactly one thing everywhere.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class Citation(BaseModel):
    source: str
    score: float
    snippet: str


class ReasonAskInput(BaseModel):
    question: str
    k: Optional[int] = None


class ReasonAnswer(BaseModel):
    answer: str
    citations: List[Citation] = []
    # Present only for reason_multistep — the decomposed sub-questions.
    steps: Optional[List[str]] = None

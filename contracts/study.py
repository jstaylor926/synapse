"""Study + code-assist tool contracts (§4.1).

Flashcards, quizzes, cheat sheets, and grounded coding help. Each generated
item carries a `source` back to the KB chunk it came from — never fabricate
(§1.10).
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from .reason import Citation


class Flashcard(BaseModel):
    front: str
    back: str
    source: Optional[str] = None


class FlashcardsInput(BaseModel):
    topic: str
    n: int = 8


class FlashcardsOutput(BaseModel):
    cards: List[Flashcard] = []


class QuizItem(BaseModel):
    q: str
    choices: Optional[List[str]] = None  # None ⇒ free-response
    answer: str
    source: Optional[str] = None


class QuizInput(BaseModel):
    topic: str
    n: int = 5


class QuizOutput(BaseModel):
    items: List[QuizItem] = []


class CheatsheetInput(BaseModel):
    topic: str


class CheatsheetOutput(BaseModel):
    markdown: str


class CodeAssistInput(BaseModel):
    query: str


class CodeAssistOutput(BaseModel):
    answer: str
    citations: List[Citation] = []

"""Tiny text-mining helpers shared by the study generators (stdlib only)."""
from __future__ import annotations

import re

_STOP = set(
    "the a an of to and or is are was were be been being in on at for with as by "
    "that this these those it its from into than then so such can may will would "
    "your you they we he she them his her their our".split()
)


def sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 25]


def definition_pairs(text: str) -> list[tuple[str, str]]:
    """Pull 'Term: definition' and 'Term — definition' lines."""
    pairs = []
    for line in text.splitlines():
        m = re.match(r"\s*[-*#> ]*\s*([A-Z][\w /+-]{2,40})\s*[:—-]\s+(.{15,})", line)
        if m:
            pairs.append((m.group(1).strip(), m.group(2).strip()))
    return pairs


def key_term(sentence: str) -> str | None:
    """Best single content word to blank out for a quiz."""
    words = re.findall(r"[A-Za-z][A-Za-z-]{3,}", sentence)
    cands = [w for w in words if w.lower() not in _STOP]
    if not cands:
        return None
    return max(cands, key=len)

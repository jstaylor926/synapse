"""Gatekeeper guarantees (§7): serialization, atomicity, optimistic concurrency."""
from __future__ import annotations

import threading

import pytest

from synapse_engine.kb.gatekeeper import (
    VaultGatekeeper,
    WriteConflict,
    atomic_write,
    classify_owner,
    file_signature,
    read_with_signature,
)


@pytest.fixture
def gk():
    g = VaultGatekeeper()
    yield g
    g.shutdown()


def test_atomic_write_leaves_no_temp(tmp_path):
    target = tmp_path / "note.md"
    atomic_write(target, "hello")
    assert target.read_text() == "hello"
    # No stray temp files from the temp→rename dance.
    assert [p.name for p in tmp_path.iterdir()] == ["note.md"]


def test_blind_write_is_last_writer_wins(gk, tmp_path):
    target = tmp_path / "gen.md"
    gk.blind_write(target, "v1")
    gk.blind_write(target, "v2")
    assert target.read_text() == "v2"


def test_occ_detects_external_edit(gk, tmp_path):
    target = tmp_path / "doc.md"
    gk.blind_write(target, "original")
    _, stale_sig = read_with_signature(target)

    # Simulate Obsidian saving underneath us.
    atomic_write(target, "edited by obsidian")

    with pytest.raises(WriteConflict):
        gk.write(target, "our update", expect=stale_sig)
    # The external edit is preserved, not clobbered.
    assert target.read_text() == "edited by obsidian"


def test_read_modify_write_serializes_under_contention(gk, tmp_path):
    """50 threads each append a line; with OCC + retry the final file must have
    exactly 50 lines — no lost updates."""
    target = tmp_path / "counter.md"
    n = 50

    def append_one(_i):
        gk.read_modify_write(
            target,
            lambda cur: (cur or "") + "x\n",
            retries=100,  # generous: contention, not failure, drives retries
        )

    threads = [threading.Thread(target=append_one, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    lines = [ln for ln in target.read_text().splitlines() if ln]
    assert len(lines) == n


def test_create_only_blocks_double_create(gk, tmp_path):
    target = tmp_path / "new.md"
    sig = gk.write(target, "first", require_absent=True)
    assert sig is not None
    with pytest.raises(WriteConflict):
        gk.write(target, "second", require_absent=True)


def test_classify_owner(tmp_path):
    vault = tmp_path / "vault"
    assert classify_owner(vault / "tasks" / "t1.md", vault) == "system"
    assert classify_owner(vault / "notes" / "n1.md", vault) == "human"
    assert classify_owner(vault / "misc" / "x.md", vault) == "unknown"


def test_signature_changes_with_content(tmp_path):
    target = tmp_path / "f.md"
    atomic_write(target, "a")
    s1 = file_signature(target)
    atomic_write(target, "b")
    s2 = file_signature(target)
    assert s1 != s2
    assert file_signature(tmp_path / "missing.md") is None

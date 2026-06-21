"""Vault writer / gatekeeper — Process C (§3, §7, §16.4).

The vault is the *truth* and the filesystem is **not** ACID, so every
programmatic write funnels through ONE serialized writer. This module is that
writer. It guarantees:

1. **Serialized own writes** — a single worker thread drains an ordered queue;
   no two of *our* writes ever touch a file at once (§7.2 layer 1).
2. **Atomic file writes** — temp file in the same dir → ``fsync`` → atomic
   ``os.replace``. A reader (including Obsidian) never sees a half-written file;
   worst case is whole-file last-writer-wins, never mid-file corruption
   (§7.2 layer 2).
3. **Optimistic concurrency vs external edits** — a read-modify-write records the
   target's signature (mtime + content hash) and re-checks it at write time; if
   Obsidian changed the file underneath us, the write is a ``WriteConflict``
   instead of a silent clobber (§7.2 layer 3).
4. **Write-ownership classification** — ``classify_owner`` tags a path
   system-owned vs human-owned by directory, so callers can pick the right
   strategy (blind last-writer-wins for generated files, read-modify-write for
   human prose) (§7.2 layer 4).

Reads stay fully concurrent — only writes are serialized.

For now the gatekeeper runs as a daemon thread inside the kernel process (the
in-process default of §5). When workers become a separate process (M2.1), this
same serialized owner is the seam that becomes Process C proper; callers do not
change.
"""
from __future__ import annotations

import hashlib
import os
import queue
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

# Directories whose files the system generates and rarely hand-edits — safe for
# blind last-writer-wins. Everything authored by the human (notes/, course prose)
# is appended to, not rewritten (§7.2 layer 4).
SYSTEM_OWNED_DIRS = {"tasks", "blocks", "cards", "resources"}
HUMAN_OWNED_DIRS = {"notes"}


class WriteConflict(RuntimeError):
    """Raised when the target changed (e.g. Obsidian saved) since the caller's
    read — the write is aborted rather than clobbering an external edit."""


@dataclass(frozen=True)
class Signature:
    """Cheap fingerprint of a file's state for optimistic-concurrency checks."""
    mtime_ns: int
    sha256: str


def file_signature(path: Path) -> Optional[Signature]:
    """Signature of ``path``, or ``None`` if it does not exist."""
    path = Path(path)
    try:
        data = path.read_bytes()
        st = path.stat()
    except FileNotFoundError:
        return None
    return Signature(mtime_ns=st.st_mtime_ns,
                     sha256=hashlib.sha256(data).hexdigest())


def read_with_signature(path: Path) -> tuple[Optional[str], Optional[Signature]]:
    """Read text + signature from the SAME bytes (reads are freely concurrent).

    Critical: the signature must hash exactly the bytes we return as text. A
    naive "read text, then separately read for the hash" can fingerprint
    *different* content if a write lands between the two reads — the stale read
    would then pass the optimistic-concurrency check and silently lose an
    update. Hashing the one buffer we read makes the signature track the text,
    so any divergence from the real file is caught as a conflict instead.
    """
    path = Path(path)
    try:
        data = path.read_bytes()
        st = path.stat()
    except FileNotFoundError:
        return None, None
    return data.decode("utf-8"), Signature(
        mtime_ns=st.st_mtime_ns, sha256=hashlib.sha256(data).hexdigest()
    )


def atomic_write(path: Path, text: str) -> Signature:
    """Write ``text`` to ``path`` atomically: temp in the same dir → fsync →
    ``os.replace``. Same-directory temp keeps the rename on one filesystem so it
    is truly atomic. Returns the resulting signature."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)  # atomic on the same filesystem
    except BaseException:
        # Never leave a stray temp behind on failure.
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    _fsync_dir(path.parent)
    sig = file_signature(path)
    assert sig is not None  # we just wrote it
    return sig


def _fsync_dir(directory: Path) -> None:
    """Best-effort durability of the rename itself (no-op where unsupported)."""
    try:
        dfd = os.open(directory, os.O_DIRECTORY)
    except (OSError, AttributeError):
        return
    try:
        os.fsync(dfd)
    except OSError:
        pass
    finally:
        os.close(dfd)


def classify_owner(path: Path, vault_dir: Path) -> str:
    """'system' | 'human' | 'unknown' by the path's top-level vault directory."""
    try:
        rel = Path(path).resolve().relative_to(Path(vault_dir).resolve())
    except ValueError:
        return "unknown"
    top = rel.parts[0] if rel.parts else ""
    if top in SYSTEM_OWNED_DIRS:
        return "system"
    if top in HUMAN_OWNED_DIRS:
        return "human"
    return "unknown"


@dataclass
class _Job:
    path: Path
    content: str
    expect: Optional[Signature]   # required current signature, or None to skip
    require_absent: bool          # target must not exist (create-only)
    done: threading.Event
    result: Optional[Signature] = None
    error: Optional[BaseException] = None


class VaultGatekeeper:
    """Single serialized writer. Submit jobs from any thread; one worker applies
    them in order. ``write`` blocks until the job is applied (or fails)."""

    def __init__(self) -> None:
        self._q: "queue.Queue[Optional[_Job]]" = queue.Queue()
        self._worker = threading.Thread(
            target=self._run, name="vault-gatekeeper", daemon=True
        )
        self._worker.start()

    # -- worker loop -------------------------------------------------------
    def _run(self) -> None:
        while True:
            job = self._q.get()
            if job is None:  # shutdown sentinel
                self._q.task_done()
                return
            try:
                job.result = self._apply(job)
            except BaseException as exc:  # surfaced to the submitter
                job.error = exc
            finally:
                job.done.set()
                self._q.task_done()

    def _apply(self, job: _Job) -> Signature:
        current = file_signature(job.path)
        if job.require_absent and current is not None:
            raise WriteConflict(f"{job.path} was created by another writer")
        if job.expect is not None and current != job.expect:
            raise WriteConflict(f"{job.path} changed underneath us (external edit)")
        return atomic_write(job.path, job.content)

    # -- public API --------------------------------------------------------
    def write(self, path: Path, content: str, *,
              expect: Optional[Signature] = None,
              require_absent: bool = False) -> Signature:
        """Serialized, atomic write. With ``expect`` set, fails with
        ``WriteConflict`` if the file changed since that signature."""
        job = _Job(path=Path(path), content=content, expect=expect,
                   require_absent=require_absent, done=threading.Event())
        self._q.put(job)
        job.done.wait()
        if job.error is not None:
            raise job.error
        assert job.result is not None
        return job.result

    def blind_write(self, path: Path, content: str) -> Signature:
        """Last-writer-wins write with no conflict check — for system-owned,
        generated files where collision surface is near zero (§7.2 layer 4)."""
        return self.write(path, content)

    def read_modify_write(
        self,
        path: Path,
        transform: Callable[[Optional[str]], str],
        *,
        retries: int = 3,
    ) -> Signature:
        """Conflict-safe update of human-owned files.

        Reads the current content + signature, computes the new content via
        ``transform(current)``, and writes only if nothing changed in between.
        On a ``WriteConflict`` (Obsidian saved underneath us) it re-reads and
        retries against the *new* content — abort-and-retry, never clobber
        (§7.2 layer 3). ``transform`` receives ``None`` when the file is absent.
        """
        last: Optional[WriteConflict] = None
        for _ in range(retries + 1):
            current, sig = read_with_signature(path)
            new_content = transform(current)
            try:
                return self.write(
                    path,
                    new_content,
                    expect=sig,
                    require_absent=(sig is None),
                )
            except WriteConflict as exc:
                last = exc
                continue
        assert last is not None
        raise last

    def shutdown(self) -> None:
        """Drain and stop the worker (mainly for tests)."""
        self._q.put(None)
        self._worker.join(timeout=5)


# Module-level singleton — one serialized owner per process (§3 Process C).
_GATEKEEPER: Optional[VaultGatekeeper] = None
_LOCK = threading.Lock()


def get_gatekeeper() -> VaultGatekeeper:
    global _GATEKEEPER
    if _GATEKEEPER is None:
        with _LOCK:
            if _GATEKEEPER is None:
                _GATEKEEPER = VaultGatekeeper()
    return _GATEKEEPER

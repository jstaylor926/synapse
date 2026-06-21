"""Worker process entrypoint (§3 Process B).

    python -m workers.run

Runs a blocking consume loop against the shared SQLite job store, crash-isolated
from the kernel. Jobs submitted by the kernel survive a worker restart because
they live in the store, not in memory.
"""
from __future__ import annotations

from jobs import JobQueue, JobStore, default_db_path
import workers.handlers  # noqa: F401 — registers handlers via @register


def main() -> None:  # pragma: no cover
    queue = JobQueue(JobStore(default_db_path()))
    print(f"[worker] consuming jobs from {default_db_path()} … (Ctrl-C to stop)")
    try:
        queue.run_forever()
    except KeyboardInterrupt:
        queue.stop()
        print("\n[worker] stopped.")


if __name__ == "__main__":  # pragma: no cover
    main()

"""Source loaders: markdown / text natively, PDF via PyMuPDF (optional extra)."""
from __future__ import annotations

from pathlib import Path


def load_text(path: Path) -> tuple[str, dict]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt", ".markdown", ".rst"}:
        return path.read_text(encoding="utf-8", errors="ignore"), {"kind": "text"}
    if suffix == ".pdf":
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:  # pragma: no cover - optional dep
            raise RuntimeError(
                "PDF ingest needs PyMuPDF. Install with: pip install -e '.[pdf]'"
            ) from exc
        doc = fitz.open(path)
        text = "\n\n".join(page.get_text() for page in doc)
        return text, {"kind": "pdf", "pages": doc.page_count}
    raise ValueError(f"Unsupported file type: {suffix} ({path})")


def iter_source_files(root: Path) -> list[Path]:
    root = Path(root)
    if root.is_file():
        return [root]
    exts = {".md", ".txt", ".markdown", ".rst", ".pdf"}
    return sorted(p for p in root.rglob("*") if p.suffix.lower() in exts)

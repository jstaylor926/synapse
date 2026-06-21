from pathlib import Path

from synapse_engine.config import Config
from synapse_engine.ingest.pipeline import ingest_path
from synapse_engine.reason.engine import ReasoningEngine
from synapse_engine.study.flashcards import make_flashcards
from synapse_engine.study.quiz import make_quiz


def _cfg(tmp_path: Path) -> Config:
    return Config(
        data_dir=tmp_path, vault_dir=tmp_path / "vault",
        store_path=tmp_path / "index.db",
        embed_provider="hash", embed_dim=256, embed_model="x",
        llm_provider="extractive", llm_model="x", top_k=5,
        candidate_k=20, rerank_enabled=False, rerank_model="x",
        rerank_candidates=20, rerank_timeout=2.0,
    )


def _samples() -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / "sample_notes"


def test_ingest_and_ask(tmp_path):
    cfg = _cfg(tmp_path)
    (cfg.vault_dir).mkdir(parents=True, exist_ok=True)
    result = ingest_path(_samples(), cfg)
    assert result["chunks_added"] > 0
    ans = ReasoningEngine(cfg).ask("what is backpropagation?")
    assert ans.citations
    assert "backpropagation" in ans.citations[0].snippet.lower()


def test_study_generators(tmp_path):
    cfg = _cfg(tmp_path)
    (cfg.vault_dir).mkdir(parents=True, exist_ok=True)
    ingest_path(_samples(), cfg)
    assert make_flashcards(cfg, "backpropagation", 5)
    assert make_quiz(cfg, "sliding window", 3)

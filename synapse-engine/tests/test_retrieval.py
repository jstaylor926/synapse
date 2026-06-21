"""Hybrid retrieval (§8): SQLite store, FTS5 lexical, RRF, degradation, chunking."""
from synapse_engine.ingest.chunk import chunk_text
from synapse_engine.kb.embeddings import HashEmbedder
from synapse_engine.kb.rrf import reciprocal_rank_fusion
from synapse_engine.kb.store import VectorStore
from synapse_engine.models import Chunk


def _store(tmp_path):
    emb = HashEmbedder(dim=256)
    store = VectorStore(tmp_path / "index.db")
    docs = {
        "a": "backpropagation computes gradients with the chain rule",
        "b": "a recipe for chocolate chip cookies and butter",
        "c": "gradient descent updates weights using the learning rate",
    }
    store.add([Chunk(id=k, text=v, source=k, vector=emb.embed(v)) for k, v in docs.items()])
    return store, emb


def test_vector_search_ranks_relevant_first(tmp_path):
    store, emb = _store(tmp_path)
    hits = store.vector_search(emb.embed("how are gradients computed"), k=2)
    assert hits[0][0].id in {"a", "c"}
    assert hits[0][1] >= hits[1][1]


def test_lexical_search_bm25(tmp_path):
    store, _ = _store(tmp_path)
    hits = store.lexical_search("chocolate cookies", k=3)
    assert hits and hits[0][0].id == "b"


def test_lexical_search_empty_query(tmp_path):
    store, _ = _store(tmp_path)
    assert store.lexical_search("!!! ???", k=3) == []


def test_rrf_rewards_agreement():
    chunks = {c: Chunk(id=c, text=c, source=c) for c in "abc"}
    vec = [(chunks["a"], 0.9), (chunks["b"], 0.8), (chunks["c"], 0.1)]
    lex = [(chunks["b"], 5.0), (chunks["a"], 4.0), (chunks["c"], 1.0)]
    fused = reciprocal_rank_fusion([vec, lex])
    # a and b rank high in both → ahead of c; no duplicates.
    ids = [c.id for c, _ in fused]
    assert ids[:2] == ["a", "b"] or ids[:2] == ["b", "a"]
    assert ids[-1] == "c"
    assert len(ids) == 3


def test_rrf_single_list_preserves_order():
    chunks = [(Chunk(id=c, text=c, source=c), 1.0) for c in "abc"]
    fused = reciprocal_rank_fusion([chunks])
    assert [c.id for c, _ in fused] == ["a", "b", "c"]


def test_persistence_roundtrip(tmp_path):
    emb = HashEmbedder(dim=64)
    path = tmp_path / "index.db"
    VectorStore(path).add([Chunk(id="x", text="hello world", source="x", vector=emb.embed("hi"))])
    assert VectorStore(path).size == 1


def test_chunk_text_is_header_aware():
    md = (
        "# Title\n\nintro paragraph\n\n"
        "## Section A\n\nalpha body text here\n\n"
        "## Section B\n\nbeta body text here\n"
    )
    chunks = chunk_text(md)
    # Each section chunk carries its heading trail for retrieval context.
    assert any("Title > Section A" in c and "alpha" in c for c in chunks)
    assert any("Title > Section B" in c and "beta" in c for c in chunks)

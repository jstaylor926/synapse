from synapse_engine.kb.embeddings import HashEmbedder
from synapse_engine.kb.store import VectorStore
from synapse_engine.models import Chunk


def test_search_ranks_relevant_first(tmp_path):
    emb = HashEmbedder(dim=256)
    store = VectorStore(tmp_path / "store.json")
    docs = {
        "a": "backpropagation computes gradients with the chain rule",
        "b": "a recipe for chocolate chip cookies and butter",
    }
    store.add([Chunk(id=k, text=v, source=k, vector=emb.embed(v)) for k, v in docs.items()])
    hits = store.search(emb.embed("how does backpropagation compute gradients"), k=2)
    assert hits[0][0].id == "a"
    assert hits[0][1] > hits[1][1]


def test_persistence_roundtrip(tmp_path):
    emb = HashEmbedder(dim=64)
    path = tmp_path / "store.json"
    VectorStore(path).add([Chunk(id="x", text="hello world", source="x", vector=emb.embed("hello world"))])
    assert VectorStore(path).size == 1

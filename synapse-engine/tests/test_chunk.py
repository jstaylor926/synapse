from synapse_engine.ingest.chunk import chunk_text


def test_chunk_splits_long_text():
    text = "\n\n".join(f"Paragraph {i} with some content." for i in range(40))
    chunks = chunk_text(text, size=200, overlap=20)
    assert len(chunks) > 1
    assert all(c.strip() for c in chunks)


def test_chunk_short_text_single():
    assert chunk_text("just one short paragraph") == ["just one short paragraph"]

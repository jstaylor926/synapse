# Synapse Engine — convenience targets
PY ?= python3

.PHONY: install install-all ingest-sample ask flashcards quiz test serve-mcp stats clean

install:            ## editable install, core (offline) only
	$(PY) -m pip install -e .

install-all:        ## editable install with pdf + mcp + llm + dev extras
	$(PY) -m pip install -e ".[all]"

ingest-sample:      ## ingest the bundled example notes
	$(PY) -m synapse_engine.cli ingest examples/sample_notes

ask:                ## ask a question (make ask Q="what is backpropagation?")
	$(PY) -m synapse_engine.cli ask "$(Q)"

flashcards:         ## make flashcards (make flashcards T="backpropagation")
	$(PY) -m synapse_engine.cli flashcards "$(T)"

quiz:               ## make a quiz (make quiz T="backpropagation")
	$(PY) -m synapse_engine.cli quiz "$(T)"

stats:              ## show knowledge-base stats
	$(PY) -m synapse_engine.cli stats

serve-mcp:          ## run the MCP server (needs .[mcp])
	$(PY) -m synapse_engine.cli serve-mcp

test:               ## run the test suite (needs .[dev])
	$(PY) -m pytest -q

clean:              ## remove local data + caches
	rm -rf data/store.json data/vault/*.md .pytest_cache **/__pycache__

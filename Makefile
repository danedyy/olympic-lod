# Olympic LOD — common tasks. Run `make` (or `make help`) to list them.

VENV    := .venv
PYTHON  := $(VENV)/bin/python

.DEFAULT_GOAL := help
.PHONY: help setup run test check fetch-wikidata clean distclean

help: ## List the available tasks
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-15s %s\n", $$1, $$2}'

$(PYTHON): requirements.txt
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install --quiet --upgrade pip
	$(PYTHON) -m pip install --quiet -r requirements.txt
	@touch $(PYTHON)

setup: $(PYTHON) ## Create .venv and install the pinned dependencies

run: $(PYTHON) ## Rebuild data/rdf/ from the CSVs (fails on any SHACL violation)
	$(PYTHON) pipeline/run.py

test: $(PYTHON) ## Run the test suite
	$(PYTHON) -m pytest -q tests

check: run test ## Before a release: rebuild, test, and confirm data/rdf/ matches what git has
	@if git rev-parse --verify -q HEAD >/dev/null; then \
		git diff --exit-code --stat -- data/rdf && echo "data/rdf/ matches the last commit"; \
	else echo "no commit yet: skipped the comparison with git"; fi

fetch-wikidata: $(PYTHON) ## Refresh the Wikidata snapshot (network); then run `make check`
	$(PYTHON) pipeline/fetch_wikidata.py

clean: ## Remove caches
	rm -rf .pytest_cache
	find . -name __pycache__ -not -path './$(VENV)/*' -prune -exec rm -rf {} +

distclean: clean ## Also remove .venv
	rm -rf $(VENV)

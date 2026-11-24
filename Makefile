SHELL := /bin/bash
PYTHON := python3
EG_VERSION ?= 0.1.0
VENV := .venv
EG := $(VENV)/bin/exposuregate
EG_SRC ?= ../exposuregate

.PHONY: help install test test-json scaffold clean

help: ## Show this help
	@grep -E '^[a-zA-Z_%-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: $(EG) ## Create .venv and install exposuregate==$(EG_VERSION) from PyPI

$(EG):
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --quiet exposuregate==$(EG_VERSION)

test: install ## Run every project in every mode and check the results
	$(PYTHON) test_runner.py --exposuregate $(EG)

test-json: install ## Same, and write results.json
	$(PYTHON) test_runner.py --exposuregate $(EG) --json results.json

test-%: install ## Run one project (e.g. make test-eg-npm-direct-kev)
	$(PYTHON) test_runner.py --exposuregate $(EG) --only $*

scaffold: ## Regenerate eg-* and data/ from an exposuregate checkout at v$(EG_VERSION) (EG_SRC=path)
	$(PYTHON) scripts/scaffold.py $(EG_SRC)

clean: ## Remove .venv and results.json
	rm -rf $(VENV) results.json

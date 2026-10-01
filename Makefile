# OpenSource Atlas — build & validation
.PHONY: help build check check-links check-sample install hooks clean

help:            ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	 awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n",$$1,$$2}'

install:         ## Install Python dependencies
	python -m pip install -r requirements.txt

build:           ## Regenerate README.md from data/projects.yaml
	python tools/generate.py

check:           ## Validate schema, ordering, and README freshness (offline)
	python tools/check.py --strict

check-sample:    ## Validate + HTTP-check a random sample of 60 links
	python tools/check.py --strict --links --sample 60

check-links:     ## Validate + HTTP-check every link (slow)
	python tools/check.py --strict --links

hooks:           ## Install the pre-commit hook (runs build + check)
	@mkdir -p .git/hooks
	@printf '#!/bin/sh\nmake build && git add README.md && make check\n' > .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "pre-commit hook installed."

clean:           ## Remove generated caches
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

.PHONY: lint test

test: test-unit

test-unit:
	uv run --dev pytest -m unit

lint:
	uv run --dev ruff check src
	uv run --dev pyrefly check src
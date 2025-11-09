.PHONY: lint test

test: test-unit

test-unit:
	uv run --extra dev pytest -m unit

lint:
	uv run --extra dev ruff check src
	uv run --extra dev pyrefly check src
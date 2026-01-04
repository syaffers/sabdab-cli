.PHONY: lint test


clean:
	@rm -rf dist

build: clean
	@uv build

test:
	@uv run --dev pytest

test-unit:
	@uv run --dev pytest -m unit

test-asyncio:
	@uv run --dev pytest -m asyncio

lint:
	@uv run --dev ruff check src
	@uv run --dev pyrefly check src
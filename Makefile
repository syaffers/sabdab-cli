.PHONY: lint test


clean-build:
	@rm -rf dist

clean: clean-build
	@rm -rf output

build: clean-build
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

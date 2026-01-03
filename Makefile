.PHONY: lint test

test: test-unit

clean:
	rm -rf dist

build: clean
	uv build

test-unit:
	uv run --dev pytest -m unit

lint:
	uv run --dev ruff check src
	uv run --dev pyrefly check src
.PHONY: help install install-dev test lint format type-check clean build all

help:
	@echo "Available commands:"
	@echo "  make install      - Install the package"
	@echo "  make install-dev  - Install with development dependencies"
	@echo "  make test         - Run unit tests"
	@echo "  make lint         - Run flake8 linter"
	@echo "  make format       - Format code with black"
	@echo "  make type-check   - Run mypy type checker"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make build        - Build the package"
	@echo "  make all          - Run format, lint, type-check, and test"

install:
	uv sync

install-dev:
	uv sync --dev
	pre-commit install

test:
	uv run pytest

lint:
	uv run flake8 pybinclock tests

format:
	uv run black pybinclock tests

type-check:
	uv run mypy pybinclock

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	uv build

all: format lint type-check test
# Project Variables
PACKAGE := itdepends
TESTS   := tests
PYTHON  := poetry run python
PYTEST  := poetry run pytest

.PHONY: all help install clean format lint test unit integration coverage

# Default target
all: install lint test

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies via Poetry
	poetry install

clean: ## Remove build artifacts, cache, and temporary files
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@rm -rf .pytest_cache .coverage htmlcov dist build .mypy_cache

test: ## Run all tests
	$(PYTEST) -v $(TESTS)

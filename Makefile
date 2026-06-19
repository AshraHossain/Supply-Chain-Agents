.PHONY: help install dev test lint format clean docker run-api

help:
	@echo "Supply Chain Agents - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies"
	@echo "  make dev              Install dev dependencies"
	@echo "  make pre-commit       Install pre-commit hooks"
	@echo ""
	@echo "Development:"
	@echo "  make test             Run tests with mock LLM"
	@echo "  make test-coverage    Run tests with coverage report"
	@echo "  make lint             Run linting checks"
	@echo "  make format           Auto-format code"
	@echo "  make clean            Clean build artifacts"
	@echo ""
	@echo "Running:"
	@echo "  make run-demo         Run demo with mock LLM"
	@echo "  make run-api          Start API server with mock LLM"
	@echo "  make docker-build     Build Docker image"
	@echo "  make docker-run       Run Docker container"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

pre-commit:
	pip install pre-commit
	pre-commit install
	pre-commit run --all-files

test:
	LLM_PROVIDER=mock pytest tests/ -v

test-coverage:
	LLM_PROVIDER=mock pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
	@echo "Coverage report: htmlcov/index.html"

lint:
	black --check app tests
	isort --check-only app tests
	flake8 app tests

format:
	black app tests
	isort app tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .coverage -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name build -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name *.egg-info -exec rm -rf {} + 2>/dev/null || true

run-demo:
	LLM_PROVIDER=mock python run_demo.py

run-api:
	LLM_PROVIDER=mock uvicorn app.main:app --reload --port 8000

docker-build:
	docker build -t supply-chain-agents:latest .

docker-run:
	docker run -it \
		-e LLM_PROVIDER=mock \
		-p 8000:8000 \
		supply-chain-agents:latest

docker-compose-up:
	docker compose up --build

docker-compose-down:
	docker compose down

all: clean install dev test lint

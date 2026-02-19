ifeq ($(OS),Windows_NT)
    PYTHON_VENV := venv/Scripts/python
else
    PYTHON_VENV := venv/bin/python
endif

.PHONY: help install start stop logs test test-unit test-e2e lint format clean

GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m

help:
	@echo "$(GREEN)Available commands:$(NC)"
	@echo "  $(YELLOW)make install$(NC)      - Install all dependencies"
	@echo "  $(YELLOW)make start$(NC)        - Start all services with Docker"
	@echo "  $(YELLOW)make stop$(NC)         - Stop all services"
	@echo "  $(YELLOW)make logs$(NC)         - View logs"
	@echo "  $(YELLOW)make test$(NC)         - Run all tests (lint + unit + e2e)"
	@echo "  $(YELLOW)make test-unit$(NC)    - Run unit tests only"
	@echo "  $(YELLOW)make test-e2e$(NC)     - Run E2E tests"
	@echo "  $(YELLOW)make lint$(NC)         - Run code linting"
	@echo "  $(YELLOW)make format$(NC)       - Format code"
	@echo "  $(YELLOW)make clean$(NC)        - Clean everything"

install:
	@echo "$(GREEN)Installing dependencies from root...$(NC)"
	pip install -r requirements.txt
	playwright install chromium
	@echo "$(GREEN)Installing frontend dependencies...$(NC)"
	cd frontend && npm install

start:
	@echo "$(GREEN)Starting services...$(NC)"
	docker-compose up --build -d
	@echo "$(GREEN)✓ Services running:$(NC)"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:3000"

stop:
	@echo "$(YELLOW)Stopping services...$(NC)"
	docker-compose down

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

test: lint test-unit test-e2e

test-unit:
	@echo "$(GREEN)Running unit tests (excluding Playwright plugin)...$(NC)"
	pytest tests/unit -p no:playwright -v --tb=short

test-e2e:
	@echo "$(GREEN)Running E2E tests...$(NC)"
	pytest tests/e2e -v --tb=short

lint:
	@echo "$(GREEN)Linting code...$(NC)"
	ruff check .
	@echo "$(GREEN)✓ Linting passed$(NC)"

format:
	@echo "$(GREEN)Formatting code...$(NC)"
	ruff format .
	@echo "$(GREEN)✓ Code formatted$(NC)"

ruff-fix:
	@echo "$(GREEN)Running ruff with --fix...$(NC)"
	ruff check . --fix
	@echo "$(GREEN)✓ Ruff fixes applied$(NC)"

clean:
	@echo "$(YELLOW)Cleaning up...$(NC)"
	docker-compose down -v
	docker-compose -f docker-compose.test.yml down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"
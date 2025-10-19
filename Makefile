# New Music Scout - Development Commands

.PHONY: help install dev test lint format clean db-up db-down db-reset

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt

dev:  ## Start development server
	cd src && python -m music_scout.main

test:  ## Run tests
	pytest tests/ -v

test-cov:  ## Run tests with coverage
	pytest tests/ -v --cov=src/music_scout --cov-report=html

lint:  ## Run linting checks
	flake8 src/ tests/
	mypy src/

format:  ## Format code
	black src/ tests/

clean:  ## Clean temporary files
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

db-up:  ## Start database containers
	docker-compose up -d postgres redis

db-down:  ## Stop database containers
	docker-compose down

db-reset:  ## Reset database (WARNING: destroys all data)
	docker-compose down -v
	docker-compose up -d postgres redis

db-logs:  ## Show database logs
	docker-compose logs -f postgres

setup:  ## Initial project setup
	cp .env.example .env
	make db-up
	sleep 5
	make install

cli-ingest:  ## Run CLI ingestion tool
	cd src && python -m music_scout.cli.ingest
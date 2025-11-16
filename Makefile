.PHONY: help install setup init test clean lint format run-example validate metrics docker-build docker-up docker-down

# Default target
help:
	@echo "AI Complaint Resolution System - Available Commands"
	@echo "===================================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install        Install dependencies"
	@echo "  make setup          Create .env file from template"
	@echo "  make init           Initialize database with dummy data"
	@echo ""
	@echo "Running:"
	@echo "  make run-example    Run example workflow"
	@echo "  make validate       Validate system configuration"
	@echo "  make metrics        Display system metrics"
	@echo "  make list           List all complaints"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   Build Docker image"
	@echo "  make docker-up      Start Docker containers"
	@echo "  make docker-down    Stop Docker containers"
	@echo ""
	@echo "Development:"
	@echo "  make test           Run tests"
	@echo "  make lint           Run linter"
	@echo "  make format         Format code"
	@echo "  make clean          Clean generated files"
	@echo ""

# Installation and setup
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Installation complete"

setup:
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file from template..."; \
		cp .env.example .env; \
		echo "✅ .env created - please edit and add your ANTHROPIC_API_KEY"; \
	else \
		echo "⚠️  .env already exists"; \
	fi

init:
	@echo "🌱 Initializing database with dummy data..."
	python cli.py init
	@echo "✅ Initialization complete"

# Running examples
run-example:
	@echo "🚀 Running example workflow..."
	python cli.py process COMP-2024-001 --save
	@echo "✅ Example complete"

validate:
	@echo "🔍 Validating system configuration..."
	python cli.py validate

metrics:
	@echo "📊 Displaying system metrics..."
	python cli.py metrics

list:
	@echo "📋 Listing complaints..."
	python cli.py list

# Docker commands
docker-build:
	@echo "🐳 Building Docker image..."
	docker-compose build
	@echo "✅ Docker image built"

docker-up:
	@echo "🐳 Starting Docker containers..."
	docker-compose up -d
	@echo "✅ Containers started"
	@echo "Run: docker-compose exec complaint-resolution /bin/bash"

docker-down:
	@echo "🐳 Stopping Docker containers..."
	docker-compose down
	@echo "✅ Containers stopped"

# Testing and quality
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v
	@echo "✅ Tests complete"

lint:
	@echo "🔍 Running linter..."
	@if command -v flake8 > /dev/null; then \
		flake8 src/ scripts/ --max-line-length=100 --ignore=E501,W503; \
	else \
		echo "⚠️  flake8 not installed. Run: pip install flake8"; \
	fi

format:
	@echo "✨ Formatting code..."
	@if command -v black > /dev/null; then \
		black src/ scripts/ cli.py; \
	else \
		echo "⚠️  black not installed. Run: pip install black"; \
	fi

# Cleanup
clean:
	@echo "🧹 Cleaning generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	find . -name "complaint_*.json" -delete
	rm -f complaint_resolution.db
	@echo "✅ Cleanup complete"

# Quick start (all-in-one)
quickstart: setup install init run-example
	@echo ""
	@echo "✅ Quick start complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  - Edit .env and add your ANTHROPIC_API_KEY"
	@echo "  - Run: make list"
	@echo "  - Run: make metrics"
	@echo ""

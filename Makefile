.PHONY: setup run ingest test clean build test-connection deploy deploy-prod deploy-stop deploy-logs deploy-test

# Default target
all: setup ingest run

# Install dependencies
setup:
	python -m pip install -r requirements.txt

# Run the API server locally
run:
	uvicorn app.api.main:app --reload --port 8000

# Run the API server without reload (production-like)
run-prod:
	uvicorn app.api.main:app --host 0.0.0.0 --port 8000

# Ingest default documents into vector database
ingest:
	python -m app.ingestion --default

# Ingest specific documents
ingest-docs:
	python -m app.ingestion --docs "data/ai_test_bug_report.txt" "data/ai_test_user_feedback.txt"

# Test API connection
test-connection:
	@echo "Testing API connection..."
	@python -c "from app.llm_client import llm_client; print('Model Info:', llm_client.get_model_info()); success = llm_client.test_connection(); print(f'Connection Test: {\"✅ PASSED\" if success else \"❌ FAILED\"}')"

# Reset and ingest all documents
reset-ingest:
	python -m app.ingestion --reset --default

# Run unit tests
test:
	pytest -q

# Run tests with coverage
test-coverage:
	pytest --cov=app --cov-report=html --cov-report=term-missing

# Run tests with verbose output
test-verbose:
	pytest -v

# Lint code (if flake8 is installed)
lint:
	flake8 app/ --max-line-length=88 --extend-ignore=E203,W503

# Format code (if black is installed)
format:
	black app/

# Build Docker image
build:
	docker build -t internal-assistant:latest .

# Quick Docker deployment (development)
deploy:
	@echo " Deploying with Docker (development)..."
	@if [ ! -f .env ]; then cp .env.example .env && echo "⚠️  Please edit .env with your OpenRouter API key"; fi
	./deploy.sh -e dev -t

# Production Docker deployment
deploy-prod:
	@echo " Deploying with Docker (production)..."
	@if [ ! -f .env.production ]; then cp .env.production.example .env.production && echo "⚠️  Please edit .env.production with production settings"; fi
	./deploy.sh -e prod -b -t

# Stop Docker containers
deploy-stop:
	@echo " Stopping Docker containers..."
	./deploy.sh -s

# Restart Docker containers
deploy-restart:
	@echo " Restarting Docker containers..."
	./deploy.sh -r

# Show Docker logs
deploy-logs:
	@echo " Showing Docker logs..."
	./deploy.sh -l

# Test Docker deployment
deploy-test:
	@echo " Testing Docker deployment..."
	./deploy.sh -t

# Clean up Docker resources
deploy-cleanup:
	@echo " Cleaning up Docker resources..."
	./deploy.sh -c

# Verify deployment prerequisites
deploy-verify:
	@echo " Verifying deployment prerequisites..."
	./deploy.sh -v

# Full production deployment with verification
deploy-full:
	@echo " Full Production Deployment..."
	./deploy.sh -v
	./deploy.sh -e prod -b -t

# Development setup with Docker
dev-docker:
	@echo " Setting up development environment with Docker..."
	make build
	./deploy.sh -e dev -b

# Clean up generated files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/
	rm -rf .pytest_cache/

# Full clean including Docker
clean-all: clean
	docker-compose down --rmi all --volumes --remove-orphans
	docker system prune -f
	./deploy.sh -c

# Development setup
dev-setup: setup
	@echo "Development setup complete. Choose your deployment method:"
	@echo "  Local:    make run"
	@echo "  Docker:   make dev-docker"
	@echo "  Test API: make test-connection"

# Production setup
prod-setup: build
	@echo "Production setup complete. Run: make deploy-prod"
	@echo "Before deployment:"
	@echo "  1. Edit .env.production with your production OpenRouter API key"
	@echo "  2. Set CORS_ORIGINS to your domain"
	@echo "  3. Run: make deploy-prod"

# Show help
help:
	@echo "Available targets:"
	@echo "  Local Development:"
	@echo "    setup          - Install Python dependencies"
	@echo "    run            - Run the API server locally with auto-reload"
	@echo "    run-prod       - Run the API server in production mode"
	@echo "    ingest         - Ingest default documents into vector database"
	@echo "    ingest-docs    - Ingest specific documents"
	@echo "    reset-ingest   - Reset database and ingest all documents"
	@echo "    test           - Run unit tests"
	@echo "    test-coverage  - Run tests with coverage report"
	@echo "    test-verbose   - Run tests with verbose output"
	@echo "    test-connection - Test API connection and show model info"
	@echo "    lint           - Lint code (requires flake8)"
	@echo "    format         - Format code (requires black)"
	@echo ""
	@echo "  Docker Deployment:"
	@echo "    build          - Build Docker image"
	@echo "    deploy         - Quick Docker deployment (development)"
	@echo "    deploy-prod    - Production Docker deployment"
	@echo "    deploy-stop    - Stop Docker containers"
	@echo "    deploy-restart - Restart Docker containers"
	@echo "    deploy-logs    - Show Docker logs"
	@echo "    deploy-test    - Test Docker deployment"
	@echo "    deploy-cleanup - Clean up Docker resources"
	@echo "    deploy-verify  - Verify deployment prerequisites"
	@echo "    deploy-full    - Full production deployment with verification"
	@echo "    dev-docker     - Development setup with Docker"
	@echo ""
	@echo "  Utilities:"
	@echo "    clean          - Clean Python cache and test files"
	@echo "    clean-all      - Full clean including Docker"
	@echo "    dev-setup      - Complete development setup"
	@echo "    prod-setup     - Complete production setup"
	@echo "    help           - Show this help message"
	@echo ""
	@echo "API Providers:"
	@echo "  OpenRouter: Set OPENROUTER_API_KEY, OPENROUTER_MODEL_NAME"
	@echo "  OpenAI: Set OPENAI_API_KEY, OPENAI_MODEL"
	@echo "  Test connection: make test-connection"
	@echo ""
	@echo "Docker Examples:"
	@echo "  make deploy          # Quick development deployment"
	@echo "  make deploy-prod     # Production deployment"
	@echo "  make deploy-test     # Test running deployment"
	@echo "  make deploy-logs     # View logs"
	@echo "  make deploy-full      # Full production workflow"

# Makefile for Bybit Grid Trading Bot

.PHONY: help setup install test run status stop clean lint format docs

# Default target
help:
	@echo "Bybit Grid Trading Bot - Available Commands:"
	@echo ""
	@echo "Setup and Installation:"
	@echo "  setup          - Run initial setup"
	@echo "  install        - Install dependencies"
	@echo "  install-dev    - Install development dependencies"
	@echo ""
	@echo "Running the Bot:"
	@echo "  run            - Start the trading bot"
	@echo "  status         - Show bot status"
	@echo "  stop           - Emergency stop"
	@echo "  reset          - Reset emergency stop"
	@echo ""
	@echo "Web Interface:"
	@echo "  web            - Start web interface"
	@echo "  web-dev        - Start web interface in development mode"
	@echo ""
	@echo "Testing:"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-coverage  - Run tests with coverage"
	@echo "  test-performance - Run performance tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint           - Run linting checks"
	@echo "  format         - Format code"
	@echo "  type-check     - Run type checking"
	@echo "  security       - Run security checks"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean          - Clean temporary files"
	@echo "  backup-config  - Backup configuration"
	@echo "  logs           - Show recent logs"
	@echo "  docs           - Generate documentation"

# Setup and Installation
setup:
	@echo "🚀 Running initial setup..."
	python scripts/setup.py

install:
	@echo "📦 Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt

install-dev:
	@echo "📦 Installing development dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov flake8 black isort mypy bandit safety

# Running the Bot
run:
	@echo "🤖 Starting the trading bot..."
	python main.py

run-debug:
	@echo "🐛 Starting the trading bot in debug mode..."
	python main.py --log-level DEBUG

status:
	@echo "📊 Checking bot status..."
	python main.py --mode status

stop:
	@echo "🛑 Emergency stop..."
	python main.py --mode stop

reset:
	@echo "🔄 Resetting emergency stop..."
	python main.py --mode reset

# Web Interface
web:
	@echo "🌐 Starting web interface..."
	python web_server.py

web-dev:
	@echo "🌐 Starting web interface in development mode..."
	python web_server.py --reload --log-level DEBUG

# Testing
test:
	@echo "🧪 Running all tests..."
	python scripts/run_tests.py --type all

test-unit:
	@echo "🧪 Running unit tests..."
	python scripts/run_tests.py --type unit --verbose

test-integration:
	@echo "🧪 Running integration tests..."
	python scripts/run_tests.py --type integration --verbose

test-coverage:
	@echo "📊 Running tests with coverage..."
	python scripts/run_tests.py --type coverage

test-performance:
	@echo "⚡ Running performance tests..."
	python scripts/run_tests.py --type performance

# Code Quality
lint:
	@echo "🔍 Running linting checks..."
	python scripts/run_tests.py --type lint

format:
	@echo "✨ Formatting code..."
	black .
	isort .

type-check:
	@echo "🔍 Running type checking..."
	python scripts/run_tests.py --type type-check

security:
	@echo "🔒 Running security checks..."
	python scripts/run_tests.py --type security

# Maintenance
clean:
	@echo "🧹 Cleaning temporary files..."
	python scripts/run_tests.py --type clean
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.pyd" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

backup-config:
	@echo "💾 Backing up configuration..."
	@mkdir -p backups
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	cp config/config.yaml "backups/config_$$timestamp.yaml"; \
	if [ -f config/.env ]; then \
		cp config/.env "backups/env_$$timestamp.backup"; \
	fi; \
	echo "✅ Configuration backed up to backups/ with timestamp $$timestamp"

logs:
	@echo "📋 Showing recent logs..."
	@if [ -f logs/trading.log ]; then \
		tail -50 logs/trading.log; \
	else \
		echo "No log file found. Run the bot first."; \
	fi

logs-follow:
	@echo "📋 Following logs (Ctrl+C to stop)..."
	@if [ -f logs/trading.log ]; then \
		tail -f logs/trading.log; \
	else \
		echo "No log file found. Run the bot first."; \
	fi

logs-errors:
	@echo "❌ Showing recent errors..."
	@if [ -f logs/trading.log ]; then \
		grep -i error logs/trading.log | tail -20; \
	else \
		echo "No log file found."; \
	fi

# Documentation
docs:
	@echo "📚 Generating documentation..."
	@echo "Available documentation:"
	@echo "  - README.md"
	@echo "  - docs/STRATEGY_GUIDE.md"
	@echo "  - docs/API_REFERENCE.md"
	@echo "  - docs/TROUBLESHOOTING.md"

# Development helpers
dev-setup: install-dev
	@echo "🛠️ Setting up development environment..."
	pre-commit install 2>/dev/null || echo "pre-commit not available"

check-config:
	@echo "⚙️ Checking configuration..."
	@python -c "from utils.config import load_config, validate_config; config = load_config(); validate_config(config); print('✅ Configuration is valid')"

check-api:
	@echo "🔗 Testing API connection..."
	@python -c "import asyncio; from api import BybitClient; from utils.config import load_config; config = load_config(); client = BybitClient(config.api_key, config.api_secret, config.testnet); asyncio.run(client.connect()); print('✅ API connection successful'); asyncio.run(client.disconnect())"

# Monitoring
monitor:
	@echo "📊 Starting monitoring (Ctrl+C to stop)..."
	@while true; do \
		clear; \
		echo "=== Bybit Grid Trading Bot Status ==="; \
		echo "Time: $$(date)"; \
		echo ""; \
		python main.py --mode status 2>/dev/null || echo "Bot not responding"; \
		echo ""; \
		echo "Press Ctrl+C to stop monitoring"; \
		sleep 30; \
	done

# Quick commands
quick-test: test-unit lint

quick-check: check-config check-api

# Installation verification
verify:
	@echo "🔍 Verifying installation..."
	@python --version
	@python -c "import sys; print(f'Python path: {sys.executable}')"
	@python -c "from utils.config import load_config; print('✅ Config module works')"
	@python -c "from api import BybitClient; print('✅ API module works')"
	@python -c "from strategy import GridStrategy; print('✅ Strategy module works')"
	@python -c "from core import TradingEngine; print('✅ Core module works')"
	@echo "✅ All modules imported successfully"

# Performance monitoring
perf:
	@echo "⚡ Performance monitoring..."
	@python -c "
import psutil
import time
print('System Performance:')
print(f'CPU Usage: {psutil.cpu_percent()}%')
print(f'Memory Usage: {psutil.virtual_memory().percent}%')
print(f'Disk Usage: {psutil.disk_usage(\"/\").percent}%')
"

# Database operations (if using database)
db-backup:
	@echo "💾 Backing up database..."
	@if [ -f trading.db ]; then \
		timestamp=$$(date +%Y%m%d_%H%M%S); \
		cp trading.db "backups/trading_$$timestamp.db"; \
		echo "✅ Database backed up to backups/trading_$$timestamp.db"; \
	else \
		echo "No database file found"; \
	fi

# Environment management
env-check:
	@echo "🌍 Checking environment..."
	@echo "Python version: $$(python --version)"
	@echo "Pip version: $$(pip --version)"
	@echo "Working directory: $$(pwd)"
	@echo "Virtual environment: $${VIRTUAL_ENV:-Not activated}"
	@echo "Environment variables:"
	@env | grep -E "(BYBIT|LOG)" || echo "No relevant environment variables set"

# Help for specific topics
help-config:
	@echo "⚙️ Configuration Help:"
	@echo ""
	@echo "Configuration files:"
	@echo "  config/config.yaml - Main configuration"
	@echo "  config/.env        - API credentials (create from .env.example)"
	@echo ""
	@echo "Key settings:"
	@echo "  trading.symbol     - Trading pair (e.g., BTCUSDT)"
	@echo "  trading.grid_levels - Number of grid levels"
	@echo "  trading.tp_percentage - Take profit percentage"
	@echo "  risk_management.max_positions - Maximum positions"
	@echo ""
	@echo "See docs/STRATEGY_GUIDE.md for detailed configuration guide"

help-trading:
	@echo "📈 Trading Help:"
	@echo ""
	@echo "Commands:"
	@echo "  make run           - Start trading"
	@echo "  make status        - Check status"
	@echo "  make stop          - Emergency stop"
	@echo "  make logs          - View logs"
	@echo "  make monitor       - Real-time monitoring"
	@echo ""
	@echo "Safety:"
	@echo "  - Always test on testnet first"
	@echo "  - Start with small amounts"
	@echo "  - Monitor regularly"
	@echo "  - Have stop-loss plan"
	@echo ""
	@echo "See docs/TROUBLESHOOTING.md for common issues"

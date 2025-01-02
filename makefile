# Makefile

# Variables
PROJECT_NAME := zexporta
VENV_DIR := .venv
POETRY := poetry
PRE_COMMIT := pre-commit

# Default target
all: init

# Initialize the project
init: poetry-install pre-commit-install

# Install dependencies with Poetry and create virtual environment in the project folder
poetry-install:
	@echo "Setting up Poetry and installing dependencies..."
	$(POETRY) config virtualenvs.in-project true
	$(POETRY) install

# Install pre-commit hooks
pre-commit-install:
	@echo "Installing pre-commit hooks..."
	$(PRE_COMMIT) install

# Run pre-commit hooks on all files
pre-commit-run:
	@echo "Running pre-commit hooks on all files..."
	$(PRE_COMMIT) run --all-files

# Clean up the project (remove virtual environment and pre-commit hooks)
clean:
	@echo "Cleaning up..."
	rm -rf $(VENV_DIR)
	$(PRE_COMMIT) uninstall

# Help target to display available commands
help:
	@echo "Available commands:"
	@echo "  make init         - Initialize the project (install dependencies and pre-commit hooks)"
	@echo "  make poetry-install - Install dependencies with Poetry"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make pre-commit-run - Run pre-commit hooks on all files"
	@echo "  make clean        - Clean up the project (remove virtual environment and pre-commit hooks)"
	@echo "  make help         - Display this help message"

.PHONY: all init poetry-install pre-commit-install pre-commit-run clean help

PYTHON   := venv/bin/python
PIP      := venv/bin/pip
PYTEST   := venv/bin/pytest
ALEMBIC  := venv/bin/alembic

.DEFAULT_GOAL := help

.PHONY: help install run \
        test test-v test-cov \
        migrate migrate-down migrate-create \
        seed seed-list \
        cmd-list cmd-schedule \
        docker-build docker-up docker-down docker-logs docker-restart

# -----------------------------------------------------------------------
# Help
# -----------------------------------------------------------------------

help:
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@printf "  \033[36m%-22s\033[0m %s\n" "install"          "Create venv and install all dependencies"
	@printf "  \033[36m%-22s\033[0m %s\n" "run"              "Start the development server"
	@echo ""
	@printf "  \033[36m%-22s\033[0m %s\n" "test"             "Run the test suite"
	@printf "  \033[36m%-22s\033[0m %s\n" "test-v"           "Run tests with verbose output"
	@printf "  \033[36m%-22s\033[0m %s\n" "test-cov"         "Run tests with coverage report"
	@echo ""
	@printf "  \033[36m%-22s\033[0m %s\n" "migrate"          "Apply all pending migrations"
	@printf "  \033[36m%-22s\033[0m %s\n" "migrate-down"     "Revert the last migration"
	@printf "  \033[36m%-22s\033[0m %s\n" "migrate-create"   "Generate a new migration  NAME=<slug>"
	@printf "  \033[36m%-22s\033[0m %s\n" "seed"             "Run all seeders"
	@printf "  \033[36m%-22s\033[0m %s\n" "seed-list"        "List available seeders"
	@echo ""
	@printf "  \033[36m%-22s\033[0m %s\n" "cmd-list"         "List all management commands"
	@printf "  \033[36m%-22s\033[0m %s\n" "cmd-schedule"     "Run commands due right now (cron)"
	@echo ""
	@printf "  \033[36m%-22s\033[0m %s\n" "docker-build"     "Build the production image"
	@printf "  \033[36m%-22s\033[0m %s\n" "docker-up"        "Start all services (detached)"
	@printf "  \033[36m%-22s\033[0m %s\n" "docker-down"      "Stop and remove containers"
	@printf "  \033[36m%-22s\033[0m %s\n" "docker-logs"      "Follow app container logs"
	@printf "  \033[36m%-22s\033[0m %s\n" "docker-restart"   "Rebuild image and restart all services"
	@echo ""

# -----------------------------------------------------------------------
# Development
# -----------------------------------------------------------------------

install:
	python3 -m venv venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ../fastapi-role-permission
	$(PIP) install -r requirements-dev.txt

run:
	$(PYTHON) run.py

# -----------------------------------------------------------------------
# Testing
# -----------------------------------------------------------------------

test:
	$(PYTEST) --tb=short -q

test-v:
	$(PYTEST) -v --tb=short

test-cov:
	$(PYTEST) --tb=short -q --cov=app --cov-report=term-missing

# -----------------------------------------------------------------------
# Database / Migrations
# -----------------------------------------------------------------------

migrate:
	$(ALEMBIC) upgrade head

migrate-down:
	$(ALEMBIC) downgrade -1

migrate-create:
ifndef NAME
	$(error NAME is required — usage: make migrate-create NAME=create_posts_table)
endif
	$(ALEMBIC) revision --autogenerate -m "$(NAME)"

# -----------------------------------------------------------------------
# Seeders
# -----------------------------------------------------------------------

seed:
	$(PYTHON) manage.py seed:run

seed-list:
	$(PYTHON) manage.py seed:list

# -----------------------------------------------------------------------
# Management commands
# -----------------------------------------------------------------------

cmd-list:
	$(PYTHON) manage.py list

cmd-schedule:
	$(PYTHON) manage.py schedule:run

# -----------------------------------------------------------------------
# Docker
# -----------------------------------------------------------------------

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f app

docker-restart: docker-down
	docker compose up -d --build

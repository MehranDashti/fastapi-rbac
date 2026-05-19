# FastAPI RBAC

A role-based access control (RBAC) API built with FastAPI, SQLAlchemy (async), and MySQL. Inspired by the Spatie Laravel permissions model: a user holds a permission if any of their assigned **roles** has it, or if it is **directly assigned** to the user.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Python 3.12 |
| Framework | FastAPI |
| ORM | SQLAlchemy (async) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | python-jose + bcrypt |
| DB (production) | MySQL via aiomysql |
| DB (tests) | SQLite via aiosqlite |
| Testing | pytest + pytest-asyncio + httpx + faker |
| Scheduling | croniter (cron expression matching) |

---

## Prerequisites

- Python 3.12+
- MySQL 8.0+ (for production) — tests use in-memory SQLite, no MySQL required for testing
- `pip` and `venv`

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd fastapi-rbac
```

### 2. Create and activate a virtual environment

```bash
python3.12 -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

### 1. Create your `.env` file from the example

```bash
cp .env.example .env
```

### 2. Edit `.env`

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Async MySQL connection string | `mysql+aiomysql://user:password@localhost:3306/mydb` |
| `SECRET_KEY` | JWT signing key — minimum 32 random characters | `openssl rand -hex 32` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime in minutes | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime in days | `7` |
| `PRODUCTION` | Disables `/docs`, `/redoc`, `/openapi.json` when `true` | `false` |

Generate a secure `SECRET_KEY`:

```bash
openssl rand -hex 32
```

---

## Database Setup

### 1. Create the MySQL database

```sql
CREATE DATABASE mydb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON mydb.* TO 'user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Run migrations

```bash
alembic upgrade head
```

This creates in order:
- `users` (migration `0001`)
- `permissions`, `roles`, `role_permissions`, `user_roles`, `user_permissions` (migration `0002`)

### 3. Seed the database

```bash
python seed.py
```

This runs all registered seeders in sequence:

| Seeder | What it creates |
|--------|----------------|
| `permissions` | 12 system permissions (`users.read`, `users.create`, …, `permissions.delete`) |
| `roles` | `superadmin` role with all 12 permissions assigned |
| `users` | First admin user assigned to the superadmin role |

The seed is **idempotent** — safe to run multiple times. Existing records are left untouched.

Override the default admin credentials via environment variables:

```bash
SEED_ADMIN_EMAIL=you@company.com \
SEED_ADMIN_USERNAME=yourusername \
SEED_ADMIN_PASSWORD=YourSecret123 \
python seed.py
```

---

## Running the Application

```bash
python run.py
```

The server starts on `http://0.0.0.0:8000` by default (configurable via `.env`).

When `PRODUCTION=false` (the default), interactive API documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

---

## Running Tests

Tests use an in-memory SQLite database — **no MySQL or `.env` required**.

```bash
# All tests
venv/bin/pytest

# Verbose output
venv/bin/pytest -v

# Short tracebacks on failure
venv/bin/pytest --tb=short

# Specific area
venv/bin/pytest app/tests/test_repositories/ -v
venv/bin/pytest app/tests/test_services/ -v
venv/bin/pytest app/tests/client/ -v
venv/bin/pytest app/tests/admin/ -v
```

### Test layout

```
app/tests/
├── conftest.py                          # DB infrastructure only (engine, fixtures, admin_headers)
├── factories/                           # Faker + uuid4 test data factories
│   ├── permission_factory.py
│   ├── role_factory.py
│   └── user_factory.py
├── test_repositories/
│   ├── conftest.py                      # permission, role, user fixtures
│   ├── test_user_repository.py
│   ├── test_role_repository.py
│   └── test_permission_repository.py
├── test_services/
│   ├── conftest.py
│   ├── test_user_service.py
│   ├── test_role_service.py
│   └── test_permission_service.py
├── client/
│   ├── conftest.py
│   └── test_auth_routes.py
└── admin/
    ├── conftest.py
    ├── test_admin_user_routes.py
    ├── test_role_routes.py
    └── test_permission_routes.py
```

All test data is generated via Faker + uuid4 — no hardcoded strings. Each test subdirectory has its own `conftest.py` for entity fixtures.

---

## RBAC Design

A user holds a permission if **either** of the following is true:
1. Any of their assigned **roles** carries that permission, **OR**
2. The permission is **directly assigned** to the user

Permission names follow the `resource.action` convention: `users.read`, `roles.update`, `permissions.delete`, etc.

### Protecting routes

```python
from fastapi import Depends
from app.core.permissions import require_permission, require_any_permission

# Single permission required
@router.get("/users", dependencies=[Depends(require_permission("users.read"))])

# Either permission grants access (OR)
@router.delete("/users/{id}", dependencies=[Depends(require_any_permission("users.delete", "admin.all"))])
```

### Checking permissions inside a handler

```python
from app.core.permissions import can
from app.core.exceptions import PermissionDeniedError

async def my_route(user: User = Depends(get_current_user)):
    if not can(user, "orders.refund"):
        raise PermissionDeniedError()
```

---

## Seeder System

Seeders live in `app/seeders/` and are registered in `app/seeders/kernel.py`. Each seeder is an independent class and can be run all at once or individually.

### CLI commands

```bash
# List all registered seeders
python manage.py seed:list

# Run all seeders (same as python seed.py)
python manage.py seed:run

# Run a single seeder by name
python manage.py seed:run permissions
python manage.py seed:run roles
python manage.py seed:run users
```

### Creating a new seeder

1. Create `app/seeders/your_seeder.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.seeders.base import BaseSeeder

class YourSeeder(BaseSeeder):
    name = "your-seeder"
    description = "What this seeder creates"

    async def run(self, db: AsyncSession) -> None:
        # idempotent DB logic here
        pass
```

2. Register it in `app/seeders/kernel.py`:

```python
from .your_seeder import YourSeeder

SEEDERS = [
    PermissionSeeder,
    RoleSeeder,
    UserSeeder,
    YourSeeder,   # append in dependency order
]
```

---

## Command Scheduler

The project includes a Laravel-inspired command scheduler. Commands are plain Python classes run on a cron schedule via a single OS cron entry.

### CLI commands

```bash
# List all registered commands
python manage.py list

# Run a command manually by name
python manage.py run example:run

# Run all commands whose cron expression matches the current time
python manage.py schedule:run
```

### Creating a new command

1. Create `app/commands/your_command.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.commands.base import BaseCommand

class YourCommand(BaseCommand):
    name = "your:command"
    description = "What this command does"

    async def handle(self, db: AsyncSession) -> None:
        pass
```

2. Register it in `app/commands/kernel.py`:

```python
from app.commands.your_command import YourCommand

COMMANDS = [YourCommand]

SCHEDULE = [
    {"command": YourCommand, "cron": "0 0 * * *"},  # daily at midnight
]
```

### Scheduling with OS cron

```
* * * * * cd /path/to/project && venv/bin/python manage.py schedule:run >> /var/log/scheduler.log 2>&1
```

---

## Project Structure

```
fastapi-rbac/
├── app/
│   ├── api/v1/
│   │   ├── router/              # Top-level aggregated API router
│   │   └── routers/
│   │       ├── client/          # Auth / client-facing routes
│   │       │   └── user_router.py
│   │       └── admin/           # Admin routes (require permissions)
│   │           ├── user_router.py
│   │           ├── role_router.py
│   │           └── permission_router.py
│   ├── commands/
│   │   ├── base.py              # BaseCommand abstract class
│   │   ├── kernel.py            # COMMANDS and SCHEDULE registry
│   │   └── example_command.py   # Template — copy to add a new command
│   ├── seeders/
│   │   ├── base.py              # BaseSeeder abstract class
│   │   ├── kernel.py            # SEEDERS ordered list
│   │   ├── permission_seeder.py # 12 system permissions
│   │   ├── role_seeder.py       # superadmin role + permission assignment
│   │   └── user_seeder.py       # first admin user + role assignment
│   ├── core/
│   │   ├── config.py            # Settings (reads .env)
│   │   ├── exceptions.py        # Domain exception hierarchy (AppError subclasses)
│   │   ├── dependencies.py      # get_current_user, service factories
│   │   ├── permissions.py       # RBAC engine + dependency factories
│   │   └── security.py          # JWT and bcrypt helpers
│   ├── db/
│   │   ├── session.py           # Async engine, Base, get_db
│   │   └── pagination.py        # Page[T], PaginationParams
│   ├── filters/
│   │   ├── base.py              # BaseFilter + FilterFn
│   │   ├── user_filter.py       # UserFilter + UserFilterParams
│   │   ├── role_filter.py       # RoleFilter + RoleFilterParams
│   │   └── permission_filter.py # PermissionFilter + PermissionFilterParams
│   ├── models/                  # SQLAlchemy ORM models
│   ├── repositories/            # Data access layer (flush, never commit)
│   ├── services/                # Business logic (raises domain exceptions)
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── migrations/              # Alembic migration scripts
│   └── tests/                   # Full test suite (131 tests)
├── main.py                      # FastAPI app factory
├── manage.py                    # Commands + seeders CLI entry point
├── run.py                       # Uvicorn entry point
├── seed.py                      # Thin runner — delegates to app/seeders/
├── alembic.ini
├── requirements.txt
├── .env.example
└── .env                         # Your local config (not committed)
```

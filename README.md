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

## Quick Start (Docker)

The fastest way to get a fully working stack — app + MySQL — with a single command.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/)

### 1. Clone the repository

```bash
git clone <repository-url>
cd fastapi-rbac
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Set a secure `SECRET_KEY` (minimum 32 characters):

```bash
# generate one and paste it into .env
openssl rand -hex 32
```

### 3. Start the stack

```bash
docker compose up --build
```

On first run this will:
1. Pull the MySQL 8.0 image and start the database
2. Build the application image
3. Wait until MySQL is healthy
4. Run all Alembic migrations automatically
5. Seed the database (12 permissions + superadmin role + admin user)
6. Start the FastAPI server

The app is available at **`http://localhost:8000`** once you see:

```
fastapi-rbac  | → Starting application...
fastapi-rbac  | INFO:     Application startup complete.
```

### 4. Default admin credentials

| Field | Value |
|-------|-------|
| Email | `admin@example.com` |
| Password | `Admin1234` |

Override before first run by editing `SEED_ADMIN_*` variables in `.env`.

### Useful Docker commands

```bash
# Start in background
docker compose up -d

# View logs
docker compose logs -f app

# Stop everything (data is preserved in the db_data volume)
docker compose down

# Stop and wipe all data
docker compose down -v

# Rebuild after code changes
docker compose up --build

# Run a one-off command inside the container
docker compose exec app python manage.py seed:list
docker compose exec app alembic upgrade head
```

### Development mode (live reload)

Uncomment the volume mount in `docker-compose.yml`:

```yaml
    volumes:
      - ./app:/app/app
```

Then restart: `docker compose up`. Code changes in `app/` will trigger an automatic reload.

---

## Manual Setup (without Docker)

Use this path if you prefer to manage MySQL separately or run the app directly on your machine.

### Prerequisites

- Python 3.12+
- MySQL 8.0+
- `pip` and `venv`

### 1. Clone and create a virtual environment

```bash
git clone <repository-url>
cd fastapi-rbac

python3.12 -m venv venv
source venv/bin/activate       # Linux / macOS
# venv\Scripts\activate        # Windows
```

### 2. Install dependencies

```bash
# Production dependencies
pip install -r requirements.txt

# Development + test dependencies
pip install -r requirements-dev.txt
```

### 3. Configure `.env`

```bash
cp .env.example .env
```

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Async MySQL connection string | `mysql+aiomysql://user:password@localhost:3306/mydb` |
| `SECRET_KEY` | JWT signing key — minimum 32 random characters | `openssl rand -hex 32` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `PRODUCTION` | Disables `/docs` and `/redoc` when `true` | `false` |

### 4. Create the MySQL database

```sql
CREATE DATABASE mydb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON mydb.* TO 'user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Run migrations and seed

```bash
alembic upgrade head
python seed.py
```

### 6. Start the server

```bash
python run.py
```

The server starts on `http://0.0.0.0:8000`. When `PRODUCTION=false`:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

---

## Running Tests

Tests use an in-memory SQLite database — **no MySQL, no Docker, no `.env` required**.

```bash
# All tests
venv/bin/pytest

# Verbose
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
├── docker/
│   ├── Dockerfile               # Production image (cache-optimised, non-root)
│   └── entrypoint.sh            # migrate → seed → start on container boot
├── main.py                      # FastAPI app factory
├── manage.py                    # Commands + seeders CLI entry point
├── run.py                       # Uvicorn entry point
├── seed.py                      # Thin runner — delegates to app/seeders/
├── docker-compose.yml           # App + MySQL services with healthcheck
├── .dockerignore
├── alembic.ini
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Test/dev dependencies (extends requirements.txt)
├── .env.example
└── .env                         # Your local config (not committed)
```

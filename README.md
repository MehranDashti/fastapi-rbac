# FastAPI RBAC

A role-based access control (RBAC) API built with FastAPI and SQLAlchemy (async). Permission logic is powered by the [`fastapi-role-permission`](../fastapi-role-permission) package — a Laravel Spatie-inspired RBAC engine purpose-built for async FastAPI applications.

A user holds a permission if any of their assigned **roles** carries it, **or** if it is **directly assigned** to the user.

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
| RBAC | `fastapi-role-permission` (local editable package) |
| DB — production | MySQL via aiomysql |
| DB — tests | SQLite via aiosqlite |
| Testing | pytest + pytest-asyncio + httpx + faker |
| Scheduling | croniter |

---

## Quick Start (Docker)

The fastest way to get a running stack — app + MySQL — with a single command.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/)

### 1. Clone both repositories side by side

The RBAC package is installed as a local editable dependency, so both repos must live in the same parent directory:

```bash
git clone <fastapi-role-permission-url>
git clone <fastapi-rbac-url>
cd fastapi-rbac
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Generate a secure `SECRET_KEY`:

```bash
openssl rand -hex 32
# paste the output into .env as SECRET_KEY=...
```

### 3. Start the stack

```bash
docker compose up --build
# or: make docker-up (after first build)
```

On first run this will:
1. Pull MySQL 8.0 and start the database
2. Build the application image
3. Wait until MySQL is healthy
4. Run all Alembic migrations automatically
5. Seed 12 permissions + superadmin role + admin user
6. Start the FastAPI server

The app is available at **`http://localhost:8000`** once you see:

```
fastapi-rbac  | → Starting application...
fastapi-rbac  | INFO:     Application startup complete.
```

### Default admin credentials

| Field | Value |
|-------|-------|
| Email | `admin@example.com` |
| Password | `Admin1234` |

Override before first run with `SEED_ADMIN_*` variables in `.env`. **Change the password immediately in production.**

### Docker commands

```bash
make docker-up        # start services in background
make docker-logs      # follow app container logs
make docker-down      # stop and remove containers
make docker-restart   # rebuild image and restart
```

Or directly with Docker Compose:

```bash
docker compose up -d
docker compose logs -f app
docker compose down          # data preserved in db_data volume
docker compose down -v       # wipe all data
docker compose exec app python manage.py seed:list
docker compose exec app alembic upgrade head
```

### Development mode (live reload)

Uncomment the volume mount in `docker-compose.yml`:

```yaml
    volumes:
      - ./app:/app/app
```

Then restart: `docker compose up`. Changes in `app/` trigger an automatic reload.

---

## Manual Setup (without Docker)

### Prerequisites

- Python 3.12+
- MySQL 8.0+
- Both repos cloned as siblings (see [Directory layout](#directory-layout) below)

### 1. Install dependencies

```bash
make install
```

This creates `venv/`, installs `fastapi-role-permission` as editable, then installs all other dependencies from `requirements-dev.txt`.

Equivalent manual steps:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ../fastapi-role-permission
pip install -r requirements-dev.txt
```

### 2. Configure `.env`

```bash
cp .env.example .env
```

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Async MySQL URL | `mysql+aiomysql://user:pass@localhost:3306/mydb` |
| `SECRET_KEY` | JWT signing key — min 32 chars | `openssl rand -hex 32` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `PRODUCTION` | Disables `/docs` and `/redoc` | `false` |

### 3. Create the MySQL database

```sql
CREATE DATABASE mydb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON mydb.* TO 'user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. Migrate and seed

```bash
make migrate   # alembic upgrade head
make seed      # 12 permissions + superadmin role + admin user
```

### 5. Run the server

```bash
make run       # starts uvicorn with auto-reload
```

| URL | Description |
|-----|-------------|
| `http://localhost:8000/docs` | Swagger UI (dev only) |
| `http://localhost:8000/redoc` | ReDoc (dev only) |
| `http://localhost:8000/health` | Health check |

---

## Makefile Reference

```bash
make help             # show all available targets

# Development
make install          # create venv, install all deps
make run              # start dev server

# Testing
make test             # run suite (quiet)
make test-v           # verbose output
make test-cov         # with coverage report

# Migrations
make migrate                        # alembic upgrade head
make migrate-down                   # alembic downgrade -1
make migrate-create NAME=add_posts  # auto-generate migration

# Seeders
make seed             # run all seeders
make seed-list        # list registered seeders

# Management commands
make cmd-list         # list all commands
make cmd-schedule     # run commands due now (cron)

# Docker
make docker-build     # build production image
make docker-up        # start services (detached)
make docker-down      # stop services
make docker-logs      # follow app logs
make docker-restart   # rebuild + restart
```

---

## Running Tests

Tests use an in-memory SQLite database — **no MySQL, no Docker, no `.env` required**.

```bash
make test         # all tests, quiet
make test-v       # all tests, verbose
make test-cov     # all tests + coverage in terminal
```

Or by area:

```bash
venv/bin/pytest app/tests/test_repositories/ -v
venv/bin/pytest app/tests/test_services/    -v
venv/bin/pytest app/tests/client/           -v
venv/bin/pytest app/tests/admin/            -v
```

### Test layout

```
app/tests/
├── conftest.py                    # engine, fixtures, admin_headers, user_headers
├── factories/                     # make_*/payload helpers using Faker + uuid4
│   ├── permission_factory.py
│   ├── role_factory.py
│   └── user_factory.py
├── test_repositories/             # repository-layer tests (db_session fixture)
├── test_services/                 # service-layer tests (db_session fixture)
├── client/                        # auth route tests (client fixture)
└── admin/                         # admin route tests (admin_headers fixture)
```

### Fixture offsets

The `admin_headers` fixture pre-seeds rows that count toward pagination totals:

| Entity | Offset |
|--------|--------|
| Permissions | +12 system permissions |
| Roles | +1 superadmin role |
| Users | +1 admin user |

---

## `fastapi-role-permission` Package

This project uses [`fastapi-role-permission`](../fastapi-role-permission) as its entire RBAC layer. The package provides the `Role` and `Permission` models, all junction tables, the `HasRoles` mixin, and the `require_permission` FastAPI dependency.

### How it works

```
User  ←──model_has_roles──→  Role  ←──role_has_permissions──→  Permission
User  ←─model_has_permissions──────────────────────────────→  Permission
```

- **`model_has_roles`** — polymorphic junction: `(model_type, model_id, role_id)`
- **`model_has_permissions`** — polymorphic junction: `(model_type, model_id, permission_id)`
- **`role_has_permissions`** — standard M2M between `roles` and `permissions`

All write operations go through raw `INSERT`/`DELETE` on those tables — never through ORM relationship `.append()` on the viewonly user side.

### Initialization

`init_rbac()` must be called inside `create_app()` **before** any router is imported:

```python
from fastapi_role_permission import init_rbac, PermissionConfig
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User

def create_app() -> FastAPI:
    app = FastAPI(...)

    # MUST come before: from app.api.v1.router import api_router
    init_rbac(
        app,
        get_db=get_db,
        get_current_user=get_current_user,
        user_model=User,
        config=PermissionConfig(guard_name="api"),
    )

    from app.api.v1.router import api_router
    app.include_router(api_router)
    return app
```

`init_rbac` does three things:
1. Injects `.roles` and `.direct_permissions` (both `lazy="selectin"`) onto `User`
2. Wires `require_permission` to your `get_db` and `get_current_user` dependencies
3. Stores the permission registrar on `app.state.rbac`

### User model setup

```python
from app.db.session import Base
from fastapi_role_permission import HasRoles

class User(Base, HasRoles):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    # ... your fields ...

    # .roles and .direct_permissions are injected automatically by init_rbac()
    # Do NOT define them here
```

### Database tables

`create_tables()` must create both metadata objects:

```python
async def create_tables() -> None:
    from fastapi_role_permission.models.base import RBACBase
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)        # users table
        await conn.run_sync(RBACBase.metadata.create_all)    # RBAC tables
```

Alembic's `env.py` also targets both:

```python
from fastapi_role_permission.models.base import RBACBase
target_metadata = [Base.metadata, RBACBase.metadata]
```

### Mixin methods — write operations

All methods perform raw SQL and expire the ORM relationship cache after flushing.

```python
# Roles
await user.assign_role(db, role)              # Role object or name string
await user.remove_role(db, role)
await user.sync_roles(db, [role1, role2])     # replace all roles

# Direct permissions
await user.give_permission_to(db, permission)
await user.revoke_permission_to(db, permission)
await user.sync_permissions(db, [perm1, perm2])
```

> **Never** use `user.roles.append(role)` or `user.direct_permissions.append(perm)` — these relationships are `viewonly=True`.

`Role.permissions` **is** mutable (standard M2M), so `.append()` and `.extend()` work there:

```python
role.permissions.append(permission)
role.permissions.extend([p1, p2])
await db.flush()
```

### Mixin methods — async checks (go to DB)

```python
await user.check_permission_to(db, "posts.read")  # bool — never raises
await user.has_role(db, "admin")                   # bool
await user.has_any_role(db, "admin", "editor")     # bool
await user.has_all_roles(db, "admin", "editor")    # bool
```

### Sync helpers (use preloaded collections)

These work on a user loaded via `get_with_roles_and_permissions()` (which uses `selectinload`). Because both relationships have `lazy="selectin"`, any ORM-loaded User will already have them populated.

```python
from app.core.permissions import get_all_permissions, can, can_any, can_all

perms: set[str] = get_all_permissions(user)   # union of role perms + direct perms
can(user, "posts.read")                        # bool
can_any(user, "posts.read", "posts.write")    # bool — any of
can_all(user, "posts.read", "posts.write")    # bool — all of
```

### Factory classmethods (Role & Permission)

```python
from fastapi_role_permission import Role, Permission

# Safe find-or-raise
role = await Role.find_by_name(db, "editor", guard_name="api")  # raises RoleDoesNotExist if missing
perm = await Permission.find_by_name(db, "posts.read")          # raises PermissionDoesNotExist

# Idempotent create-or-find
role = await Role.find_or_create(db, "editor", guard_name="api")
perm = await Permission.find_or_create(db, "posts.read")

# Explicit create (raises if already exists)
role = await Role.create(db, "editor", guard_name="api")
perm = await Permission.create(db, "posts.read")
```

### Protecting routes

`require_permission` is a FastAPI dependency factory. It resolves `get_db` and `get_current_user` from the wiring done in `init_rbac`.

```python
from fastapi import Depends
from app.core.permissions import require_permission, require_any_permission

# Require exactly one permission
@router.get("/users", dependencies=[Depends(require_permission("users.read"))])

# Require any one of several permissions
@router.get("/reports", dependencies=[Depends(require_any_permission("reports.read", "admin.all"))])

# Require a specific role
from app.core.permissions import require_role
@router.post("/deploy", dependencies=[Depends(require_role("ops"))])
```

Responses when access is denied:

| Condition | Status |
|-----------|--------|
| No `Authorization` header | `401 Unauthenticated` |
| Token invalid or expired | `401 Unauthenticated` |
| Authenticated but missing permission | `403 Unauthorized` |

### Inline permission check inside a handler

```python
from app.core.permissions import can, PermissionDeniedError
from app.core.dependencies import get_current_user
from app.models.user import User

@router.post("/orders/{id}/refund")
async def refund_order(
    id: int,
    current_user: User = Depends(get_current_user),
):
    if not can(current_user, "orders.refund"):
        raise PermissionDeniedError()
    ...
```

---

## RBAC in the Admin API

All admin routes are protected by `require_permission`. The 12 system permissions follow the `resource.action` pattern:

| Permission | Protects |
|-----------|---------|
| `users.read` | `GET /admin/users`, `GET /admin/users/{id}` |
| `users.create` | `POST /admin/users` |
| `users.update` | `PATCH /admin/users/{id}/toggle-active`, role/permission assignment |
| `users.delete` | *(reserved for future delete endpoint)* |
| `roles.read` | `GET /admin/roles`, `GET /admin/roles/{id}` |
| `roles.create` | `POST /admin/roles` |
| `roles.update` | `PATCH /admin/roles/{id}`, permission assignment on roles |
| `roles.delete` | `DELETE /admin/roles/{id}` |
| `permissions.read` | `GET /admin/permissions`, `GET /admin/permissions/{id}` |
| `permissions.create` | `POST /admin/permissions` |
| `permissions.update` | `PATCH /admin/permissions/{id}` |
| `permissions.delete` | `DELETE /admin/permissions/{id}` |

The seeded **superadmin** role holds all 12. The seeded **admin user** holds the superadmin role.

---

## API Reference

### Auth (`/api/v1/auth`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/signup` | Public | Register a new user |
| `POST` | `/login` | Public | Returns `access_token` + `refresh_token` |
| `POST` | `/refresh` | Public | Issue a new access token from a refresh token |
| `POST` | `/logout` | Bearer | Client-side token discard |
| `GET` | `/profile` | Bearer | Current user profile with roles + permissions |
| `PATCH` | `/profile` | Bearer | Update `full_name` or `password` |

### Admin — Users (`/api/v1/admin/users`)

| Method | Path | Permission |
|--------|------|-----------|
| `GET` | `/` | `users.read` |
| `GET` | `/{id}` | `users.read` |
| `POST` | `/` | `users.create` |
| `PATCH` | `/{id}/toggle-active` | `users.update` |
| `POST` | `/{id}/roles` | `users.update` |
| `DELETE` | `/{id}/roles/{rid}` | `users.update` |
| `POST` | `/{id}/permissions` | `users.update` |
| `DELETE` | `/{id}/permissions/{pid}` | `users.update` |

### Admin — Roles (`/api/v1/admin/roles`)

| Method | Path | Permission |
|--------|------|-----------|
| `GET` | `/` | `roles.read` |
| `GET` | `/{id}` | `roles.read` |
| `POST` | `/` | `roles.create` |
| `PATCH` | `/{id}` | `roles.update` |
| `DELETE` | `/{id}` | `roles.delete` |
| `POST` | `/{id}/permissions` | `roles.update` |
| `DELETE` | `/{id}/permissions/{pid}` | `roles.update` |

### Admin — Permissions (`/api/v1/admin/permissions`)

| Method | Path | Permission |
|--------|------|-----------|
| `GET` | `/` | `permissions.read` |
| `GET` | `/{id}` | `permissions.read` |
| `POST` | `/` | `permissions.create` |
| `PATCH` | `/{id}` | `permissions.update` |
| `DELETE` | `/{id}` | `permissions.delete` |

### Response envelope

Every response is wrapped in a consistent envelope:

```json
{ "success": true,  "code": 200, "message": "Ok",        "data": { ... } }
{ "success": false, "code": 404, "message": "Not Found",  "error": { "detail": "..." } }
```

---

## Seeder System

Seeders are idempotent classes in `app/seeders/`, registered in `app/seeders/kernel.py`.

```bash
make seed              # run all seeders in order
make seed-list         # list registered seeders
python manage.py seed:run permissions   # run one by name
```

### Creating a seeder

```python
# app/seeders/your_seeder.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.seeders.base import BaseSeeder

class YourSeeder(BaseSeeder):
    name = "your-seeder"
    description = "What this creates"

    async def run(self, db: AsyncSession) -> None:
        # idempotent logic — use find_or_create patterns
        pass
```

Register in `app/seeders/kernel.py`:

```python
SEEDERS = [PermissionSeeder, RoleSeeder, UserSeeder, YourSeeder]
```

> **Note:** `Role.find_by_name()` and `Permission.find_by_name()` raise exceptions if the entity doesn't exist. Use `find_or_create()` for idempotent seeders, or catch `RoleDoesNotExist` / `PermissionDoesNotExist`.

---

## Command Scheduler

```bash
make cmd-list          # list all commands
make cmd-schedule      # run commands due now
python manage.py run example:run   # run one manually
```

### Creating a command

```python
# app/commands/your_command.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.commands.base import BaseCommand

class YourCommand(BaseCommand):
    name = "your:command"
    description = "What this does"

    async def handle(self, db: AsyncSession) -> None:
        pass
```

Register in `app/commands/kernel.py`:

```python
from app.commands.your_command import YourCommand

COMMANDS = [YourCommand]

SCHEDULE = [
    {"command": YourCommand, "cron": "0 * * * *"},  # every hour
]
```

OS cron entry (runs every minute, croniter matches expressions):

```
* * * * * cd /path/to/project && venv/bin/python manage.py schedule:run >> /var/log/scheduler.log 2>&1
```

---

## Project Structure

```
fastapi-rbac/             ← this repo
../fastapi-role-permission/  ← sibling repo (editable install)

fastapi-rbac/
├── app/
│   ├── api/v1/
│   │   ├── router/              # top-level APIRouter
│   │   └── routers/
│   │       ├── client/          # auth routes
│   │       └── admin/           # permission-protected admin routes
│   ├── commands/                # BaseCommand, kernel, example_command
│   ├── core/
│   │   ├── config.py            # pydantic-settings
│   │   ├── dependencies.py      # get_current_user, service factories
│   │   ├── exceptions.py        # AppError hierarchy
│   │   ├── permissions.py       # get_all_permissions, can, require_permission re-exports
│   │   └── security.py          # JWT + bcrypt helpers
│   ├── db/
│   │   ├── session.py           # engine, Base, get_db, create_tables
│   │   └── pagination.py        # Page[T], PaginationParams
│   ├── filters/                 # BaseFilter, *Filter, *FilterParams
│   ├── models/                  # User(Base, HasRoles); Role/Permission from package
│   ├── repositories/            # BaseRepository[T], UserRepo, RoleRepo, PermissionRepo
│   ├── services/                # BaseService[T] + domain services
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── seeders/                 # BaseSeeder, kernel, 3 system seeders
│   ├── migrations/              # Alembic env.py + 3 migration versions
│   └── tests/                   # 125 tests across 10 files
├── docker/
│   ├── Dockerfile               # cache-optimised, non-root, python:3.12-slim
│   └── entrypoint.sh            # migrate → seed → uvicorn
├── .github/
│   └── workflows/ci.yml         # GitHub Actions: test on push/PR to master/develop
├── main.py                      # create_app() — init_rbac before router imports
├── manage.py                    # seeders + commands CLI
├── run.py                       # uvicorn entry point
├── seed.py                      # run all seeders
├── Makefile                     # developer shortcuts
├── docker-compose.yml           # app + MySQL with healthcheck
├── requirements.txt             # production deps
├── requirements-dev.txt         # + aiosqlite, httpx, pytest, pytest-cov, faker
└── .env.example
```

---

## Directory Layout

Both repositories must be cloned as siblings for the editable install to work:

```
parent/
├── fastapi-role-permission/   ← git clone <package-repo-url>
└── fastapi-rbac/              ← git clone <this-repo-url>
```

`make install` handles the editable install automatically:

```bash
pip install -e ../fastapi-role-permission
pip install -r requirements-dev.txt
```

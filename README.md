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
| Testing | pytest + pytest-asyncio + httpx |

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

Open `.env` and set the values for your environment. The most important fields:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Async MySQL connection string | `mysql+aiomysql://user:password@localhost:3306/mydb` |
| `SECRET_KEY` | JWT signing key — must be at least 32 random characters | `openssl rand -hex 32` |
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

This creates the following tables in order:
- `users` (migration `0001`)
- `permissions`, `roles`, `role_permissions`, `user_roles`, `user_permissions` (migration `0002`)

### 3. Seed the database

```bash
python seed.py
```

This creates:
- 12 system permissions (`users.read`, `users.create`, ..., `permissions.delete`)
- A `superadmin` role with all 12 permissions
- An admin user assigned to the superadmin role

The seed is **idempotent** — safe to run multiple times.

You can override the default admin credentials via environment variables:

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

### Run all tests

```bash
venv/bin/pytest
```

### Run with verbose output

```bash
venv/bin/pytest -v
```

### Run a specific file

```bash
# Repository tests
venv/bin/pytest app/tests/test_repositories/ -v

# Service tests
venv/bin/pytest app/tests/test_services/ -v

# API route tests — auth
venv/bin/pytest app/tests/client/ -v

# API route tests — admin
venv/bin/pytest app/tests/admin/ -v
```

### Run with short traceback on failure

```bash
venv/bin/pytest --tb=short
```

### Test layout

```
app/tests/
├── conftest.py                          # shared fixtures, in-memory SQLite setup
├── test_repositories/
│   ├── test_user_repository.py          # UserRepository unit tests
│   ├── test_role_repository.py          # RoleRepository unit tests
│   └── test_permission_repository.py    # PermissionRepository unit tests
├── test_services/
│   ├── test_user_service.py             # UserService unit tests
│   ├── test_role_service.py             # RoleService unit tests
│   └── test_permission_service.py       # PermissionService unit tests
├── client/
│   └── test_auth_routes.py              # Auth API route tests
└── admin/
    ├── test_admin_user_routes.py         # Admin user route tests
    ├── test_role_routes.py               # Admin role route tests
    └── test_permission_routes.py         # Admin permission route tests
```

---

## API Overview

### Auth endpoints (public / authenticated)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/auth/signup` | Public | Register a new user |
| `POST` | `/api/v1/auth/login` | Public | Login, receive access + refresh tokens |
| `POST` | `/api/v1/auth/refresh` | Public | Issue new access token via refresh token |
| `POST` | `/api/v1/auth/logout` | Bearer | Logout (client-side token discard) |
| `GET` | `/api/v1/auth/profile` | Bearer | Get current user profile with roles and permissions |
| `PATCH` | `/api/v1/auth/profile` | Bearer | Update current user's name or password |

### Admin — Users

| Method | Path | Permission |
|--------|------|-----------|
| `GET` | `/api/v1/admin/users` | `users.read` |
| `GET` | `/api/v1/admin/users/{id}` | `users.read` |
| `POST` | `/api/v1/admin/users` | `users.create` |
| `PATCH` | `/api/v1/admin/users/{id}/toggle-active` | `users.update` |
| `POST` | `/api/v1/admin/users/{id}/roles` | `users.update` |
| `DELETE` | `/api/v1/admin/users/{id}/roles/{rid}` | `users.update` |
| `POST` | `/api/v1/admin/users/{id}/permissions` | `users.update` |
| `DELETE` | `/api/v1/admin/users/{id}/permissions/{pid}` | `users.update` |

### Admin — Roles

| Method | Path | Permission |
|--------|------|-----------|
| `GET` | `/api/v1/admin/roles` | `roles.read` |
| `GET` | `/api/v1/admin/roles/{id}` | `roles.read` |
| `POST` | `/api/v1/admin/roles` | `roles.create` |
| `PATCH` | `/api/v1/admin/roles/{id}` | `roles.update` |
| `DELETE` | `/api/v1/admin/roles/{id}` | `roles.delete` |
| `POST` | `/api/v1/admin/roles/{id}/permissions` | `roles.update` |
| `DELETE` | `/api/v1/admin/roles/{id}/permissions/{pid}` | `roles.update` |

### Admin — Permissions

| Method | Path | Permission |
|--------|------|-----------|
| `GET` | `/api/v1/admin/permissions` | `permissions.read` |
| `GET` | `/api/v1/admin/permissions/{id}` | `permissions.read` |
| `POST` | `/api/v1/admin/permissions` | `permissions.create` |
| `PATCH` | `/api/v1/admin/permissions/{id}` | `permissions.update` |
| `DELETE` | `/api/v1/admin/permissions/{id}` | `permissions.delete` |

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
from app.core.permissions import can, can_any

async def my_route(user: User = Depends(get_current_user)):
    if not can(user, "orders.refund"):
        raise HTTPException(status_code=403, detail="Permission denied.")
```

---

## Project Structure

```
fastapi-rbac/
├── app/
│   ├── api/v1/
│   │   ├── router/          # Aggregated API router
│   │   └── routers/         # Individual route modules
│   ├── core/
│   │   ├── config.py        # Settings (reads .env)
│   │   ├── dependencies.py  # get_current_user, service factories
│   │   ├── permissions.py   # RBAC engine + dependency factories
│   │   └── security.py      # JWT and bcrypt helpers
│   ├── db/
│   │   ├── session.py       # Async engine, Base, get_db
│   │   └── pagination.py    # Page[T], PaginationParams
│   ├── models/              # SQLAlchemy ORM models
│   ├── repositories/        # Data access layer (flush, never commit)
│   ├── services/            # Business logic (raises HTTPException)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── migrations/          # Alembic migration scripts
│   └── tests/               # Full test suite
├── main.py                  # FastAPI app factory
├── run.py                   # Uvicorn entry point
├── seed.py                  # DB bootstrap (permissions + admin user)
├── alembic.ini
├── requirements.txt
├── .env.example
└── .env                     # Your local config (not committed)
```

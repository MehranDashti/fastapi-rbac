# CLAUDE.md — FastAPI RBAC Project

Full context for continuing this project via Claude Code.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Python 3.12 |
| Framework | FastAPI |
| ORM | SQLAlchemy (async) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | python-jose[cryptography] + passlib[bcrypt] |
| DB (prod) | MySQL via aiomysql |
| DB (tests) | SQLite via aiosqlite |
| Testing | pytest + pytest-asyncio + httpx |

---

## Requirements

```
fastapi
uvicorn[standard]
pydantic-settings
pydantic[email]
python-dotenv
sqlalchemy
alembic
aiomysql
aiosqlite
python-jose[cryptography]
passlib[bcrypt]
httpx
pytest
pytest-asyncio
```

---

## Directory Structure

```
project/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router/
│   │       │   └── __init__.py               # api_router aggregator
│   │       └── routers/
│   │           ├── __init__.py
│   │           ├── client_user_router.py      # /api/v1/auth/*
│   │           ├── admin_user_router.py       # /api/v1/admin/users/*
│   │           ├── role_router.py             # /api/v1/admin/roles/*
│   │           └── permission_router.py       # /api/v1/admin/permissions/*
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                          # pydantic-settings, reads .env
│   │   ├── logging.py                         # syslog + console logging
│   │   ├── middleware.py                      # RequestLoggingMiddleware
│   │   ├── security.py                        # JWT access+refresh tokens, bcrypt
│   │   ├── dependencies.py                    # get_current_user, service factories
│   │   └── permissions.py                     # RBAC engine + dependency factories
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py                         # async engine, get_db, Base
│   │   └── pagination.py                      # PaginationParams, Page[T], paginate()
│   ├── models/
│   │   ├── __init__.py                        # imports all models for Alembic
│   │   ├── user.py                            # User + user_roles + user_permissions tables
│   │   ├── role.py                            # Role + role_permissions table
│   │   └── permission.py                      # Permission model
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py                            # BaseRepository[T]
│   │   ├── user_repository.py
│   │   ├── role_repository.py
│   │   └── permission_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── role_service.py
│   │   └── permission_service.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── role.py
│   │   └── permission.py
│   ├── migrations/
│   │   ├── env.py                             # async Alembic env
│   │   └── versions/
│   │       ├── 0001_create_users.py           # users table
│   │       └── 0002_create_rbac.py            # permissions, roles, junction tables
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                        # in-memory SQLite, app overrides
│       ├── client/                            # TODO: auth route tests
│       └── admin/                             # TODO: admin route tests
├── main.py                                    # app factory, lifespan, middleware
├── run.py                                     # uvicorn entry point
├── seed.py                                    # bootstrap permissions + superadmin + first user
├── alembic.ini
├── .env
├── CLAUDE.md
└── requirements.txt
```

---

## Environment Variables (.env)

```env
APP_NAME=MyApp
APP_VERSION=1.0.0
PRODUCTION=false
DEBUG=false
SERVER_LISTEN_IP=0.0.0.0
SERVER_LISTEN_PORT=8000
SERVER_WORKERS=1
CORS_ORIGINS=["http://localhost:3000"]
CORS_ALLOW_CREDENTIALS=true
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/mydb
LOG_LEVEL=INFO
SYSLOG_HOST=localhost
SYSLOG_PORT=514
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Seed overrides (optional, used by `seed.py`):
```env
SEED_ADMIN_EMAIL=admin@example.com
SEED_ADMIN_USERNAME=admin
SEED_ADMIN_FULLNAME=System Administrator
SEED_ADMIN_PASSWORD=Admin1234
```

---

## Database Schema

### Tables

```
permissions
  id, name, display_name, guard_name (default "api"), created_at, updated_at
  UNIQUE (name, guard_name)

roles
  id, name, display_name, guard_name (default "api"), created_at, updated_at
  UNIQUE (name, guard_name)

users
  id, email, username, full_name, hashed_password, is_active, created_at, updated_at

role_permissions   (M2M: roles ↔ permissions)
  role_id FK → roles.id CASCADE
  permission_id FK → permissions.id CASCADE

user_roles         (M2M: users ↔ roles)
  user_id FK → users.id CASCADE
  role_id FK → roles.id CASCADE

user_permissions   (M2M: users ↔ permissions — direct grants, no role intermediary)
  user_id FK → users.id CASCADE
  permission_id FK → permissions.id CASCADE
```

### Migration chain

```
0001_create_users  →  0002_create_rbac
```

Run with: `alembic upgrade head`

---

## RBAC Design (Spatie-inspired)

A user holds a permission if **either**:
1. Any of their assigned **roles** has that permission, **OR**
2. The permission is **directly assigned** to the user

### Permission naming convention

`resource.action` — e.g. `users.read`, `roles.update`, `permissions.delete`

### System permissions (seeded by seed.py)

```
users.read        users.create        users.update        users.delete
roles.read        roles.create        roles.update        roles.delete
permissions.read  permissions.create  permissions.update  permissions.delete
```

### Permission engine — app/core/permissions.py

Pure helpers (no FastAPI, fully testable):
```python
get_all_permissions(user)            → set[str]   # union of role perms + direct perms
can(user, "perm")                    → bool
can_any(user, "p1", "p2")           → bool       # OR
can_all(user, "p1", "p2")           → bool       # AND
has_role(user, "role")               → bool
has_any_role(user, "r1", "r2")      → bool
has_all_roles(user, "r1", "r2")     → bool
```

FastAPI dependency factories (use in route `dependencies=[]`):
```python
require_permission("users.read")
require_any_permission("users.read", "admin.all")
require_all_permissions("posts.create", "posts.publish")
require_role("superadmin")
require_any_role("admin", "manager")
require_active_user()
```

### Usage examples

```python
# in a route — single permission
@router.get("/users", dependencies=[Depends(require_permission("users.read"))])

# in a route — OR logic
@router.delete("/users/{id}", dependencies=[Depends(require_any_permission("users.delete", "admin.all"))])

# inside a handler — conditional logic
async def my_route(user: User = Depends(get_current_user)):
    if not can(user, "orders.refund"):
        raise PermissionDeniedError()
```

---

## Authentication Flow

1. Client sends `POST /api/v1/auth/login` → receives `access_token` + `refresh_token`
2. Client sends `Authorization: Bearer <access_token>` on protected routes
3. `get_current_user` dependency:
   - Decodes JWT → extracts `user_id`
   - Loads `User` from DB with **all roles + their permissions + direct permissions** in one query
   - Raises `401` if token invalid / user not found
   - Raises `403` if `is_active == False`
4. Permission factories wrap `get_current_user` — auth + permission check in one `Depends()`

Token types stored in JWT payload as `"type": "access"` or `"type": "refresh"`.
Logout is currently client-side (token discard). Redis blacklist is a planned next step.

---

## Key Implementation Patterns

### Repositories never commit
All repository methods call `flush()` not `commit()`. The `get_db` session manager in `db/session.py` owns commit/rollback.

### Service dependency injection
```python
# in dependencies.py
async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(
        user_repo=UserRepository(db),
        role_repo=RoleRepository(db),
        permission_repo=PermissionRepository(db),
    )
```

### lazy="selectin" on all relationships
All ORM relationships use `lazy="selectin"` for async-safe eager loading. Never use `lazy="select"` (default) with async SQLAlchemy — it fires sync queries.

### UserDetailResponse.from_user()
`all_permissions` is a computed field built in the router, not Pydantic:
```python
return UserDetailResponse.from_user(user, service.get_all_permissions(user))
```

### Idempotent assign/revoke
Repository assignment methods check before mutating (`if role not in user.roles`). Service layer raises `409 CONFLICT` on duplicate assign or missing-on-revoke.

---

## All Endpoints

### Auth (public / authenticated)

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/v1/auth/signup` | Public |
| POST | `/api/v1/auth/login` | Public |
| POST | `/api/v1/auth/refresh` | Public |
| POST | `/api/v1/auth/logout` | Authenticated |
| GET | `/api/v1/auth/profile` | Authenticated |
| PATCH | `/api/v1/auth/profile` | Authenticated |

### Admin — Users

| Method | Path | Permission |
|--------|------|-----------|
| GET | `/api/v1/admin/users` | `users.read` |
| GET | `/api/v1/admin/users/{id}` | `users.read` |
| POST | `/api/v1/admin/users` | `users.create` |
| PATCH | `/api/v1/admin/users/{id}/toggle-active` | `users.update` |
| POST | `/api/v1/admin/users/{id}/roles` | `users.update` |
| DELETE | `/api/v1/admin/users/{id}/roles/{rid}` | `users.update` |
| POST | `/api/v1/admin/users/{id}/permissions` | `users.update` |
| DELETE | `/api/v1/admin/users/{id}/permissions/{pid}` | `users.update` |

### Admin — Roles

| Method | Path | Permission |
|--------|------|-----------|
| GET | `/api/v1/admin/roles` | `roles.read` |
| GET | `/api/v1/admin/roles/{id}` | `roles.read` |
| POST | `/api/v1/admin/roles` | `roles.create` |
| PATCH | `/api/v1/admin/roles/{id}` | `roles.update` |
| DELETE | `/api/v1/admin/roles/{id}` | `roles.delete` |
| POST | `/api/v1/admin/roles/{id}/permissions` | `roles.update` |
| DELETE | `/api/v1/admin/roles/{id}/permissions/{pid}` | `roles.update` |

### Admin — Permissions

| Method | Path | Permission |
|--------|------|-----------|
| GET | `/api/v1/admin/permissions` | `permissions.read` |
| GET | `/api/v1/admin/permissions/{id}` | `permissions.read` |
| POST | `/api/v1/admin/permissions` | `permissions.create` |
| PATCH | `/api/v1/admin/permissions/{id}` | `permissions.update` |
| DELETE | `/api/v1/admin/permissions/{id}` | `permissions.delete` |

### Health

| Method | Path | Auth |
|--------|------|------|
| GET | `/health` | Public |

---

## Bootstrap (run once on fresh DB)

```bash
alembic upgrade head
python seed.py

# optional env overrides
SEED_ADMIN_EMAIL=you@company.com SEED_ADMIN_PASSWORD=YourSecret1 python seed.py
```

Seed is idempotent — safe to re-run.

---

## What Is NOT Done Yet

| Item | Notes |
|------|-------|
| Tests | `app/tests/client/` and `app/tests/admin/` are empty. `conftest.py` has in-memory SQLite + app overrides ready. |
| Redis token blacklist | Logout is client-side only. `POST /auth/logout` has a `# TODO` comment. |
| Pagination on admin list endpoints | `Page[T]` + `PaginationParams` + `paginate()` exist in `db/pagination.py` but list endpoints return plain `list[]` for now. |
| Wildcard permissions | e.g. `users.*` matching all `users.x` permissions — not implemented. |
| Password reset flow | No forgot-password / reset-password endpoints. |
| Email verification | No email confirmation on signup. |

---

## Coding Conventions

- All new models go in `app/models/`, registered in `app/models/__init__.py`
- Every new model needs a migration in `app/migrations/versions/` following the `NNNN_description.py` naming pattern
- Repository methods use `flush()` never `commit()`
- Services raise `HTTPException` directly — no custom exception hierarchy (yet)
- Permission names follow `resource.action` convention — add new ones to `seed.py`
- All relationships use `lazy="selectin"`
- Schemas use `model_config = {"from_attributes": True}` on all response models
- `UserDetailResponse.from_user(user, permissions_set)` is the pattern for building detailed user responses
# Import all models here so SQLAlchemy's metadata (and Alembic autogenerate)
# can see every table in one place.
#
# Order matters for forward-reference resolution:
#   Permission and Role have no FK to User, so they come first.
#   User references both via association tables defined inside user.py.

from app.models.permission import Permission
from app.models.role import Role, role_permissions
from app.models.user import User, user_roles, user_permissions

__all__ = [
    "Permission",
    "Role",
    "role_permissions",
    "User",
    "user_roles",
    "user_permissions",
]
import fastapi_role_permission.models.permission  # registers RBACBase tables with metadata  # noqa: F401
import fastapi_role_permission.models.role  # noqa: F401
from fastapi_role_permission import Permission, Role

from app.models.user import User

__all__ = [
    "Permission",
    "Role",
    "User",
]

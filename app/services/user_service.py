from typing import TYPE_CHECKING, Any

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    InactiveAccountError,
    NotFoundError,
)
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService

if TYPE_CHECKING:
    from app.db.pagination import PaginationParams


class UserService(BaseService[User]):
    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
        permission_repo: PermissionRepository,
    ) -> None:
        super().__init__(user_repo)
        self.repo: UserRepository
        self.role_repo = role_repo
        self.permission_repo = permission_repo

    async def get_by_id_with_roles_and_permissions(self, user_id: int) -> User:
        user = await self.repo.get_with_roles_and_permissions(user_id)
        if not user:
            raise NotFoundError(f"User with id {user_id} not found.")
        return user

    async def get_by_email(self, email: str) -> User:
        user = await self.repo.get_by_email(email)
        if not user:
            raise NotFoundError("User not found.")
        return user

    async def register(
        self,
        email: str,
        username: str,
        full_name: str,
        password: str,
    ) -> User:
        if await self.repo.email_exists(email):
            raise ConflictError("A user with this email already exists.")
        if await self.repo.username_exists(username):
            raise ConflictError("A user with this username already exists.")
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=get_password_hash(password),
        )
        return await self.repo.create(user)

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")
        if not user.is_active:
            raise InactiveAccountError("Account is inactive.")
        return user

    async def update_profile(
        self,
        user: User,
        full_name: str | None = None,
        password: str | None = None,
    ) -> User:
        if full_name is not None:
            user.full_name = full_name
        if password is not None:
            user.hashed_password = get_password_hash(password)
        return await self._flush_refresh(user)

    async def toggle_active(self, user_id: int) -> User:
        user = await self.get_by_id(user_id)
        user.is_active = not user.is_active
        return await self._flush_refresh(user)

    async def assign_role(self, user_id: int, role_id: int) -> User:
        user = await self.get_by_id_with_roles_and_permissions(user_id)
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise NotFoundError(f"Role with id {role_id} not found.")
        if role in user.roles:
            raise ConflictError(f"Role '{role.name}' is already assigned to this user.")
        await self.repo.assign_role(user, role)
        return user

    async def revoke_role(self, user_id: int, role_id: int) -> User:
        user = await self.get_by_id_with_roles_and_permissions(user_id)
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise NotFoundError(f"Role with id {role_id} not found.")
        if role not in user.roles:
            raise ConflictError(f"Role '{role.name}' is not assigned to this user.")
        await self.repo.revoke_role(user, role)
        return user

    async def sync_roles(self, user_id: int, role_ids: list[int]) -> User:
        user = await self.get_by_id_with_roles_and_permissions(user_id)
        roles = []
        for role_id in role_ids:
            role = await self.role_repo.get_by_id(role_id)
            if not role:
                raise NotFoundError(f"Role with id {role_id} not found.")
            roles.append(role)
        await self.repo.sync_roles(user, roles)
        return user

    async def assign_direct_permission(self, user_id: int, permission_id: int) -> User:
        user = await self.get_by_id_with_roles_and_permissions(user_id)
        permission = await self.permission_repo.get_by_id(permission_id)
        if not permission:
            raise NotFoundError(f"Permission with id {permission_id} not found.")
        if permission in user.direct_permissions:
            raise ConflictError(
                f"Permission '{permission.name}' is already directly assigned to this user."
            )
        await self.repo.assign_direct_permission(user, permission)
        return user

    async def revoke_direct_permission(self, user_id: int, permission_id: int) -> User:
        user = await self.get_by_id_with_roles_and_permissions(user_id)
        permission = await self.permission_repo.get_by_id(permission_id)
        if not permission:
            raise NotFoundError(f"Permission with id {permission_id} not found.")
        if permission not in user.direct_permissions:
            raise ConflictError(
                f"Permission '{permission.name}' is not directly assigned to this user."
            )
        await self.repo.revoke_direct_permission(user, permission)
        return user

    async def sync_direct_permissions(self, user_id: int, permission_ids: list[int]) -> User:
        user = await self.get_by_id_with_roles_and_permissions(user_id)
        permissions = []
        for permission_id in permission_ids:
            permission = await self.permission_repo.get_by_id(permission_id)
            if not permission:
                raise NotFoundError(f"Permission with id {permission_id} not found.")
            permissions.append(permission)
        await self.repo.sync_direct_permissions(user, permissions)
        return user

    async def get_paginated(
        self,
        filters: dict[str, Any],
        sort_by: str | None,
        sort_order: str,
        pagination: "PaginationParams",
    ) -> tuple[list[User], int]:
        return await self.repo.get_filtered_paginated(filters, sort_by, sort_order, pagination)

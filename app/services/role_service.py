from fastapi import HTTPException, status

from app.models.role import Role
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository


class RoleService:
    def __init__(self, role_repo: RoleRepository, permission_repo: PermissionRepository) -> None:
        self.role_repo = role_repo
        self.permission_repo = permission_repo

    async def get_all(self) -> list[Role]:
        return await self.role_repo.get_all()

    async def get_by_id(self, role_id: int) -> Role:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id {role_id} not found.",
            )
        return role

    async def get_by_id_with_permissions(self, role_id: int) -> Role:
        role = await self.role_repo.get_with_permissions(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id {role_id} not found.",
            )
        return role

    async def get_by_name(self, name: str, guard_name: str = "api") -> Role:
        role = await self.role_repo.get_by_name(name, guard_name)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{name}' not found.",
            )
        return role

    async def create(
        self,
        name: str,
        display_name: str,
        guard_name: str = "api",
    ) -> Role:
        if await self.role_repo.exists(name, guard_name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role '{name}' already exists for guard '{guard_name}'.",
            )
        role = Role(
            name=name,
            display_name=display_name,
            guard_name=guard_name,
        )
        return await self.role_repo.create(role)

    async def update(self, role_id: int, display_name: str) -> Role:
        role = await self.get_by_id(role_id)
        role.display_name = display_name
        await self.role_repo.db.flush()
        await self.role_repo.db.refresh(role)
        return role

    async def delete(self, role_id: int) -> None:
        role = await self.get_by_id(role_id)
        await self.role_repo.delete(role)

    # ── permission assignment ─────────────────────────────────────────────────

    async def assign_permission(self, role_id: int, permission_id: int) -> Role:
        role = await self.get_by_id_with_permissions(role_id)
        permission = await self.permission_repo.get_by_id(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission with id {permission_id} not found.",
            )
        if permission in role.permissions:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Permission '{permission.name}' is already assigned to role '{role.name}'.",
            )
        await self.role_repo.assign_permission(role, permission)
        return role

    async def revoke_permission(self, role_id: int, permission_id: int) -> Role:
        role = await self.get_by_id_with_permissions(role_id)
        permission = await self.permission_repo.get_by_id(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission with id {permission_id} not found.",
            )
        if permission not in role.permissions:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Permission '{permission.name}' is not assigned to role '{role.name}'.",
            )
        await self.role_repo.revoke_permission(role, permission)
        return role
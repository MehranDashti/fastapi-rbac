from fastapi import HTTPException, status

from app.models.permission import Permission
from app.repositories.permission_repository import PermissionRepository


class PermissionService:
    def __init__(self, repo: PermissionRepository) -> None:
        self.repo = repo

    async def get_all(self, guard_name: str = "api") -> list[Permission]:
        return await self.repo.get_all_by_guard(guard_name)

    async def get_by_id(self, permission_id: int) -> Permission:
        permission = await self.repo.get_by_id(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission with id {permission_id} not found.",
            )
        return permission

    async def get_by_name(self, name: str, guard_name: str = "api") -> Permission:
        permission = await self.repo.get_by_name(name, guard_name)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission '{name}' not found.",
            )
        return permission

    async def create(
        self,
        name: str,
        display_name: str,
        guard_name: str = "api",
    ) -> Permission:
        if await self.repo.exists(name, guard_name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Permission '{name}' already exists for guard '{guard_name}'.",
            )
        permission = Permission(
            name=name,
            display_name=display_name,
            guard_name=guard_name,
        )
        return await self.repo.create(permission)

    async def delete(self, permission_id: int) -> None:
        permission = await self.get_by_id(permission_id)
        await self.repo.delete(permission)
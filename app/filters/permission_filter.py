from fastapi import Query

from app.filters.base import BaseFilter, FilterFn


class PermissionFilter(BaseFilter):
    def filters(self) -> dict[str, FilterFn]:
        from fastapi_role_permission import Permission
        return {
            "name":       lambda q, v: q.where(Permission.name.ilike(f"%{v}%")),
            "guard_name": lambda q, v: q.where(Permission.guard_name == v),
        }

    def sortable_fields(self) -> set[str]:
        return {"id", "name", "guard_name", "created_at"}


class PermissionFilterParams:
    def __init__(
        self,
        name: str | None = Query(default=None, description="Partial name match"),
        guard_name: str | None = Query(default=None, description="Exact guard name match"),
        sort_by: str | None = Query(default=None, description="Column to sort by"),
        sort_order: str = Query(default="asc", pattern="^(asc|desc)$", description="asc or desc"),
    ):
        self.name = name
        self.guard_name = guard_name
        self.sort_by = sort_by
        self.sort_order = sort_order

    def to_dict(self) -> dict:
        return {"name": self.name, "guard_name": self.guard_name}

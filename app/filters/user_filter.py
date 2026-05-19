from fastapi import Query

from app.filters.base import BaseFilter, FilterFn


class UserFilter(BaseFilter):
    def filters(self) -> dict[str, FilterFn]:
        from app.models.user import User
        return {
            "email":     lambda q, v: q.where(User.email.ilike(f"%{v}%")),
            "username":  lambda q, v: q.where(User.username.ilike(f"%{v}%")),
            "full_name": lambda q, v: q.where(User.full_name.ilike(f"%{v}%")),
            "is_active": lambda q, v: q.where(User.is_active == v),
        }

    def sortable_fields(self) -> set[str]:
        return {"id", "email", "username", "full_name", "created_at", "is_active"}


class UserFilterParams:
    def __init__(
        self,
        email: str | None = Query(default=None, description="Partial email match"),
        username: str | None = Query(default=None, description="Partial username match"),
        full_name: str | None = Query(default=None, description="Partial full-name match"),
        is_active: bool | None = Query(default=None, description="Filter by active status"),
        sort_by: str | None = Query(default=None, description="Column to sort by"),
        sort_order: str = Query(default="asc", pattern="^(asc|desc)$", description="asc or desc"),
    ):
        self.email = email
        self.username = username
        self.full_name = full_name
        self.is_active = is_active
        self.sort_by = sort_by
        self.sort_order = sort_order

    def to_dict(self) -> dict:
        return {
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "is_active": self.is_active,
        }

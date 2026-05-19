from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Table, Column, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

# M2M: roles ↔ permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "permission_id",
        Integer,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4",
    mysql_collate="utf8mb4_unicode_ci",
)


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("name", "guard_name", name="uq_roles_name_guard"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(125), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    guard_name: Mapped[str] = mapped_column(String(125), nullable=False, default="api", server_default="api")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # M2M → permissions
    permissions: Mapped[list["Permission"]] = relationship(  # noqa: F821
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin",
    )

    # M2M → users (back-populated from User)
    users: Mapped[list["User"]] = relationship(  # noqa: F821
        "User",
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin",
    )
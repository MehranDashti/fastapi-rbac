from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("name", "guard_name", name="uq_permissions_name_guard"),
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

    # relationships (back-populated from Role and User)
    roles: Mapped[list["Role"]] = relationship(  # noqa: F821
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
        lazy="selectin",
    )
    users: Mapped[list["User"]] = relationship(  # noqa: F821
        "User",
        secondary="user_permissions",
        back_populates="direct_permissions",
        lazy="selectin",
    )
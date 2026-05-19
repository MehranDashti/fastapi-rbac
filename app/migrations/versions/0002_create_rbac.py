"""create RBAC tables: permissions, roles, role_permissions, user_roles, user_permissions

Revision ID: 0002_create_rbac
Revises: 0001_create_users
Create Date: 2024-01-01 00:00:01.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_create_rbac"
down_revision: Union[str, None] = "0001_create_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE_OPTS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    # ── 1. permissions ────────────────────────────────────────────────────────
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=125), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("guard_name", sa.String(length=125), nullable=False, server_default="api"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "guard_name", name="uq_permissions_name_guard"),
        **_TABLE_OPTS,
    )
    op.create_index("ix_permissions_id", "permissions", ["id"])

    # ── 2. roles ──────────────────────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=125), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("guard_name", sa.String(length=125), nullable=False, server_default="api"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "guard_name", name="uq_roles_name_guard"),
        **_TABLE_OPTS,
    )
    op.create_index("ix_roles_id", "roles", ["id"])

    # ── 3. role_permissions  (M2M: roles ↔ permissions) ──────────────────────
    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            sa.Integer(),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "permission_id",
            sa.Integer(),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        **_TABLE_OPTS,
    )

    # ── 4. user_roles  (M2M: users ↔ roles) ──────────────────────────────────
    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "role_id",
            sa.Integer(),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        **_TABLE_OPTS,
    )

    # ── 5. user_permissions  (M2M: users ↔ permissions, direct grants) ───────
    op.create_table(
        "user_permissions",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "permission_id",
            sa.Integer(),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        **_TABLE_OPTS,
    )


def downgrade() -> None:
    # drop junction tables first (they hold the FKs)
    op.drop_table("user_permissions")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")

    op.drop_index("ix_roles_id", table_name="roles")
    op.drop_table("roles")

    op.drop_index("ix_permissions_id", table_name="permissions")
    op.drop_table("permissions")
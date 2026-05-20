"""migrate RBAC schema: replace custom tables with fastapi-role-permission package tables

Revision ID: 0003_migrate_rbac_schema
Revises: 0002_create_rbac
Create Date: 2026-05-20 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_migrate_rbac_schema"
down_revision: Union[str, None] = "0002_create_rbac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. drop old junction tables (hold FKs to roles/permissions) ───────────
    op.drop_table("user_permissions")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")

    # ── 2. drop old roles and permissions tables ───────────────────────────────
    op.drop_index("ix_roles_id", table_name="roles")
    op.drop_table("roles")
    op.drop_index("ix_permissions_id", table_name="permissions")
    op.drop_table("permissions")

    # ── 3. create new permissions table (package schema) ──────────────────────
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(125), nullable=False),
        sa.Column("guard_name", sa.String(125), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name", "guard_name", name="uq_permissions_name_guard"),
    )

    # ── 4. create new roles table (package schema — adds description, team_id) ─
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(125), nullable=False),
        sa.Column("guard_name", sa.String(125), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name", "guard_name", name="uq_roles_name_guard"),
    )

    # ── 5. role_has_permissions (package M2M: roles ↔ permissions) ─────────────
    op.create_table(
        "role_has_permissions",
        sa.Column(
            "permission_id",
            sa.Integer(),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            sa.Integer(),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # ── 6. model_has_roles (polymorphic: any model ↔ roles) ────────────────────
    op.create_table(
        "model_has_roles",
        sa.Column(
            "role_id",
            sa.Integer(),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("model_type", sa.String(125), nullable=False),
        sa.Column("model_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_mhr_model", "model_has_roles", ["model_type", "model_id"])
    op.create_index("ix_mhr_team", "model_has_roles", ["team_id"])

    # ── 7. model_has_permissions (polymorphic: any model ↔ permissions) ────────
    op.create_table(
        "model_has_permissions",
        sa.Column(
            "permission_id",
            sa.Integer(),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("model_type", sa.String(125), nullable=False),
        sa.Column("model_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_mhp_model", "model_has_permissions", ["model_type", "model_id"])
    op.create_index("ix_mhp_team", "model_has_permissions", ["team_id"])


def downgrade() -> None:
    # drop package tables
    op.drop_index("ix_mhp_team", table_name="model_has_permissions")
    op.drop_index("ix_mhp_model", table_name="model_has_permissions")
    op.drop_table("model_has_permissions")

    op.drop_index("ix_mhr_team", table_name="model_has_roles")
    op.drop_index("ix_mhr_model", table_name="model_has_roles")
    op.drop_table("model_has_roles")

    op.drop_table("role_has_permissions")
    op.drop_table("roles")
    op.drop_table("permissions")

    # re-create original tables
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
    )
    op.create_index("ix_permissions_id", "permissions", ["id"])

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
    )
    op.create_index("ix_roles_id", "roles", ["id"])

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"),
                  primary_key=True, nullable=False),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id", ondelete="CASCADE"),
                  primary_key=True, nullable=False),
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"),
                  primary_key=True, nullable=False),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"),
                  primary_key=True, nullable=False),
    )
    op.create_table(
        "user_permissions",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"),
                  primary_key=True, nullable=False),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id", ondelete="CASCADE"),
                  primary_key=True, nullable=False),
    )

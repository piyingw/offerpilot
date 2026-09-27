"""add applications and application_events tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=True),
        sa.Column("company", sa.String(length=120), nullable=False),
        sa.Column("position", sa.String(length=120), nullable=False),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("jd_url", sa.String(length=512), nullable=True),
        sa.Column("salary", sa.String(length=60), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("current_status", sa.String(length=20), nullable=False),
        sa.Column("applied_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_applications_user_id"), "applications", ["user_id"], unique=False)
    op.create_index(op.f("ix_applications_company"), "applications", ["company"], unique=False)
    op.create_index(
        op.f("ix_applications_current_status"), "applications", ["current_status"], unique=False
    )

    op.create_table(
        "application_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(length=20), nullable=True),
        sa.Column("to_status", sa.String(length=20), nullable=False),
        sa.Column("happened_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["application_id"], ["applications.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_application_events_application_id"),
        "application_events",
        ["application_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("application_events")
    op.drop_index(op.f("ix_applications_current_status"), table_name="applications")
    op.drop_index(op.f("ix_applications_company"), table_name="applications")
    op.drop_index(op.f("ix_applications_user_id"), table_name="applications")
    op.drop_table("applications")

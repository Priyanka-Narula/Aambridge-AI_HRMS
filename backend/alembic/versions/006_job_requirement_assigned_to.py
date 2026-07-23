"""Add assigned_to on job_requirements.

Revision ID: 006_job_requirement_assigned_to
Revises: 005_add_personal_email_to_users
Create Date: 2026-07-13
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "006_job_requirement_assigned_to"
down_revision = "005_add_personal_email_to_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Skipped when already present via 001 create_all with current models.
    bind = op.get_bind()
    inspector = inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("job_requirements")}
    indexes = {ix["name"] for ix in inspector.get_indexes("job_requirements")}
    fks = {fk["name"] for fk in inspector.get_foreign_keys("job_requirements")}

    if "assigned_to" not in cols:
        op.add_column(
            "job_requirements",
            sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True),
        )
    if "ix_job_requirements_assigned_to" not in indexes:
        op.create_index(
            "ix_job_requirements_assigned_to",
            "job_requirements",
            ["assigned_to"],
        )
    if "fk_job_requirements_assigned_to_users" not in fks:
        op.create_foreign_key(
            "fk_job_requirements_assigned_to_users",
            "job_requirements",
            "users",
            ["assigned_to"],
            ["id"],
        )


def downgrade() -> None:
    op.drop_constraint(
        "fk_job_requirements_assigned_to_users",
        "job_requirements",
        type_="foreignkey",
    )
    op.drop_index("ix_job_requirements_assigned_to", table_name="job_requirements")
    op.drop_column("job_requirements", "assigned_to")

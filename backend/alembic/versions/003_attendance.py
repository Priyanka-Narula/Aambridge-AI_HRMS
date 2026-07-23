"""Add attendance_records table."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "003_attendance"
down_revision = "002_seed_defaults"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 001_initial_schema uses Base.metadata.create_all(), which already
    # creates this table when the AttendanceRecord model is present.
    inspector = inspect(op.get_bind())
    if "attendance_records" in inspector.get_table_names():
        return

    op.create_table(
        "attendance_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False, index=True),
        sa.Column("check_in", sa.DateTime(timezone=True), nullable=True),
        sa.Column("check_out", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "date", name="uq_attendance_user_date"),
    )


def downgrade() -> None:
    op.drop_table("attendance_records")

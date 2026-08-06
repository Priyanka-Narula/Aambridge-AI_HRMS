"""merge dashboard indexes and remove screening

Revision ID: 21fa9ae5d99c
Revises: 011_dashboard_indexes, 012_remove_screening
Create Date: 2026-08-04 11:08:07.476269

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21fa9ae5d99c'
down_revision: Union[str, Sequence[str], None] = ('011_dashboard_indexes', '012_remove_screening')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

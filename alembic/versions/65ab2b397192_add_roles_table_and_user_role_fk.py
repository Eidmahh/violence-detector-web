"""add roles table and user→role_fk

Revision ID: 65ab2b397192
Revises: 069ffc12fbbf
Create Date: 2025-05-15 15:53:07.694136

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65ab2b397192'
down_revision: Union[str, None] = '069ffc12fbbf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

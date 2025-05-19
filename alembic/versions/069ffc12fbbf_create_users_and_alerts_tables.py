"""create users and alerts tables

Revision ID: 069ffc12fbbf
Revises: 
Create Date: 2025-05-13 20:42:38.924551

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '069ffc12fbbf'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(), nullable=False, unique=True),
      # and so on
    )
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), primary_key=True),
    
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass

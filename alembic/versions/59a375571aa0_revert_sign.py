"""revert sign

Revision ID: 59a375571aa0
Revises: 4fb34d22bcad
Create Date: 2024-09-09 22:31:14.613117

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '59a375571aa0'
down_revision: Union[str, None] = '4fb34d22bcad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('signconfig')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('signconfig',
    sa.Column('group', sa.INTEGER(), nullable=False),
    sa.Column('enabled', sa.BOOLEAN(), nullable=False),
    sa.PrimaryKeyConstraint('group')
    )
    # ### end Alembic commands ###
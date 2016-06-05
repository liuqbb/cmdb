"""empty message

Revision ID: 8c600384959c
Revises: 33fc336561ba
Create Date: 2016-06-05 11:58:32.915394

"""

# revision identifiers, used by Alembic.
revision = '8c600384959c'
down_revision = '33fc336561ba'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('logs', sa.Column('logobj_id', sa.Integer(), nullable=True))
    op.add_column('logs', sa.Column('logobjtype', sa.String(length=64), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('logs', 'logobjtype')
    op.drop_column('logs', 'logobj_id')
    ### end Alembic commands ###
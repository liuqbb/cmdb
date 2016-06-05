"""empty message

Revision ID: 33fc336561ba
Revises: None
Create Date: 2016-06-04 15:58:53.759844

"""

# revision identifiers, used by Alembic.
revision = '33fc336561ba'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('logs', sa.Column('action', sa.String(length=32), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('logs', 'action')
    ### end Alembic commands ###

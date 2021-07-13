"""empty message

Revision ID: 4df4248d2abe
Revises: 38395b979b79
Create Date: 2021-07-11 20:10:55.356770

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4df4248d2abe'
down_revision = '38395b979b79'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('fedi_auth', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'fedi_auth')
    # ### end Alembic commands ###

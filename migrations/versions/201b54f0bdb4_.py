"""empty message

Revision ID: 201b54f0bdb4
Revises: 9bda3a5366a0
Create Date: 2021-07-08 17:11:51.682756

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '201b54f0bdb4'
down_revision = '9bda3a5366a0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('form_logs', 'form_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.drop_constraint('form_logs_form_id_fkey', 'form_logs', type_='foreignkey')
    op.create_foreign_key(None, 'form_logs', 'forms', ['form_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'form_logs', type_='foreignkey')
    op.create_foreign_key('form_logs_form_id_fkey', 'form_logs', 'forms', ['form_id'], ['id'])
    op.alter_column('form_logs', 'form_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###

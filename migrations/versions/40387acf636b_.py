"""empty message

Revision ID: 40387acf636b
Revises: e850bb5c6c8b
Create Date: 2020-04-15 19:58:59.328582

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '40387acf636b'
down_revision = 'e850bb5c6c8b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('role', sa.Column('permissions', sa.Integer(), nullable=True))
    op.drop_column('role', 'permission_value')
    op.add_column('user', sa.Column('about_me', sa.Text(), nullable=True))
    op.add_column('user', sa.Column('age', sa.Integer(), nullable=True))
    op.add_column('user', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('gender', sa.Enum('MALE', 'FEMALE', name='gender'), nullable=True))
    op.add_column('user', sa.Column('last_seen', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('location', sa.String(length=64), nullable=True))
    op.add_column('user', sa.Column('phone_number', sa.String(length=32), nullable=True))
    op.create_unique_constraint(None, 'user', ['phone_number'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='unique')
    op.drop_column('user', 'phone_number')
    op.drop_column('user', 'location')
    op.drop_column('user', 'last_seen')
    op.drop_column('user', 'gender')
    op.drop_column('user', 'created_at')
    op.drop_column('user', 'age')
    op.drop_column('user', 'about_me')
    op.add_column('role', sa.Column('permission_value', mysql.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('role', 'permissions')
    # ### end Alembic commands ###

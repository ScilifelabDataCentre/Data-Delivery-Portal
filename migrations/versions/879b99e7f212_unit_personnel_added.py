"""unit_personnel_added

Revision ID: 879b99e7f212
Revises: b976f6cda95c
Create Date: 2023-05-29 07:51:05.491352

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "879b99e7f212"
down_revision = "b976f6cda95c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        table_name="reporting",
        column_name="unituser_count",
        nullable=False,
        new_column_name="unit_personnel_count",
        type_=sa.Integer(),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "reporting",
        "unit_personnel_count",
        nullable=False,
        new_column_name="unituser_count",
        type_=sa.Integer(),
    )
    # ### end Alembic commands ###

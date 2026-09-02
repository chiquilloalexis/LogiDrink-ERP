"""Agregar stock anterior y nuevo a movimientos

Revision ID: dfd43721435f
Revises: 2ef395aa8c57
Create Date: 2026-08-28
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "dfd43721435f"
down_revision = "2ef395aa8c57"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
        "movimientos_inventario",
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "stock_anterior",
                sa.Integer(),
                nullable=False,
                server_default="0"
            )
        )

        batch_op.add_column(
            sa.Column(
                "stock_nuevo",
                sa.Integer(),
                nullable=False,
                server_default="0"
            )
        )


def downgrade():
    with op.batch_alter_table(
        "movimientos_inventario",
        schema=None
    ) as batch_op:

        batch_op.drop_column("stock_nuevo")
        batch_op.drop_column("stock_anterior")
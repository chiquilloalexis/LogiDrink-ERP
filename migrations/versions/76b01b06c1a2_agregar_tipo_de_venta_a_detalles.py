"""Agregar tipo de venta a detalles

Revision ID: 76b01b06c1a2
Revises: 7e40ee0f1298
Create Date: 2026-08-28 22:33:56.647168

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '76b01b06c1a2'
down_revision = '7e40ee0f1298'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('detalles_ventas', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'tipo_venta',
                sa.String(length=20),
                nullable=False,
                server_default='unidad'
            )
        )


def downgrade():
    with op.batch_alter_table('detalles_ventas', schema=None) as batch_op:
        batch_op.drop_column('tipo_venta')
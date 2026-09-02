"""Agregar manejo de cajas y unidades a productos

Revision ID: 7e40ee0f1298
Revises: 71acf7f0fd43
Create Date: 2026-08-28 12:49:02.383492

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e40ee0f1298'
down_revision = '71acf7f0fd43'
branch_labels = None
depends_on = None


def upgrade():
    # ==========================================================
    # AGREGAR COLUMNAS DE CAJAS
    # ==========================================================

    with op.batch_alter_table('productos', schema=None) as batch_op:

        batch_op.add_column(
            sa.Column(
                'precio_compra_caja',
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                server_default='0'
            )
        )

        batch_op.add_column(
            sa.Column(
                'precio_venta_caja',
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                server_default='0'
            )
        )

        batch_op.add_column(
            sa.Column(
                'unidades_por_caja',
                sa.Integer(),
                nullable=False,
                server_default='1'
            )
        )

        batch_op.add_column(
            sa.Column(
                'maneja_cajas',
                sa.Boolean(),
                nullable=False,
                server_default=sa.false()
            )
        )

    # ==========================================================
    # QUITAR DEFAULTS DEL SERVIDOR
    # ==========================================================
    #
    # Los valores anteriores solo se necesitan para poder
    # crear las columnas cuando ya existen productos.
    # Después dejamos que los valores por defecto los maneje
    # el modelo de Flask/SQLAlchemy.
    #

    with op.batch_alter_table('productos', schema=None) as batch_op:

        batch_op.alter_column(
            'precio_compra_caja',
            server_default=None
        )

        batch_op.alter_column(
            'precio_venta_caja',
            server_default=None
        )

        batch_op.alter_column(
            'unidades_por_caja',
            server_default=None
        )

        batch_op.alter_column(
            'maneja_cajas',
            server_default=None
        )


def downgrade():

    with op.batch_alter_table('productos', schema=None) as batch_op:

        batch_op.drop_column('maneja_cajas')
        batch_op.drop_column('unidades_por_caja')
        batch_op.drop_column('precio_venta_caja')
        batch_op.drop_column('precio_compra_caja')
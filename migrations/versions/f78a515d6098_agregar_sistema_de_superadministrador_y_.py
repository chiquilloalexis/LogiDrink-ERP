"""Agregar sistema de superadministrador y modulos

Revision ID: f78a515d6098
Revises: d96d0683bc6a
Create Date: 2026-08-31 01:11:00.029148

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f78a515d6098"
down_revision = "d96d0683bc6a"
branch_labels = None
depends_on = None


def upgrade():

    # ============================================================
    # TABLA MODULOS
    # ============================================================

    # La tabla puede existir porque una ejecución anterior
    # alcanzó a crearla antes de fallar.
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    tablas = inspector.get_table_names()

    if "modulos" not in tablas:
        op.create_table(
            "modulos",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("nombre", sa.String(length=100), nullable=False),
            sa.Column("descripcion", sa.String(length=255), nullable=True),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("nombre", name="uq_modulo_nombre"),
        )


    # ============================================================
    # TABLA EMPRESA_MODULOS
    # ============================================================

    inspector = sa.inspect(bind)
    tablas = inspector.get_table_names()

    if "empresa_modulos" not in tablas:
        op.create_table(
            "empresa_modulos",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("empresa_id", sa.Integer(), nullable=False),
            sa.Column("modulo_id", sa.Integer(), nullable=False),
            sa.Column(
                "activo",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            ),
            sa.ForeignKeyConstraint(
                ["empresa_id"],
                ["empresas.id"],
                name="fk_empresa_modulo_empresa",
            ),
            sa.ForeignKeyConstraint(
                ["modulo_id"],
                ["modulos.id"],
                name="fk_empresa_modulo_modulo",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "empresa_id",
                "modulo_id",
                name="uq_empresa_modulo",
            ),
        )


    # ============================================================
    # MODIFICAR TABLA USUARIOS
    # ============================================================

    inspector = sa.inspect(bind)

    columnas_usuarios = {
        columna["name"]
        for columna in inspector.get_columns("usuarios")
    }

    # ------------------------------------------------------------
    # es_superadmin
    # ------------------------------------------------------------

    if "es_superadmin" not in columnas_usuarios:

        with op.batch_alter_table("usuarios", schema=None) as batch_op:

            batch_op.add_column(
                sa.Column(
                    "es_superadmin",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                )
            )

    # ------------------------------------------------------------
    # empresa_id nullable
    # ------------------------------------------------------------

    with op.batch_alter_table("usuarios", schema=None) as batch_op:

        batch_op.alter_column(
            "empresa_id",
            existing_type=sa.INTEGER(),
            nullable=True,
        )

    # ------------------------------------------------------------
    # rol_id nullable
    # ------------------------------------------------------------

    with op.batch_alter_table("usuarios", schema=None) as batch_op:

        batch_op.alter_column(
            "rol_id",
            existing_type=sa.INTEGER(),
            nullable=True,
        )

    # ------------------------------------------------------------
    # UNIQUE email
    #
    # NO usamos create_unique_constraint(None...)
    # porque SQLite necesita que la restricción tenga nombre.
    # ------------------------------------------------------------

    inspector = sa.inspect(bind)

    indices = inspector.get_indexes("usuarios")
    uniques = inspector.get_unique_constraints("usuarios")

    email_unico = False

    for unique in uniques:
        columnas = unique.get("column_names", [])

        if columnas == ["email"]:
            email_unico = True
            break

    if not email_unico:

        for indice in indices:
            columnas = indice.get("column_names", [])

            if (
                columnas == ["email"]
                and indice.get("unique", False)
            ):
                email_unico = True
                break

    if not email_unico:

        with op.batch_alter_table("usuarios", schema=None) as batch_op:

            batch_op.create_unique_constraint(
                "uq_usuario_email",
                ["email"],
            )


def downgrade():

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    tablas = inspector.get_table_names()

    # ============================================================
    # USUARIOS
    # ============================================================

    if "usuarios" in tablas:

        uniques = inspector.get_unique_constraints("usuarios")

        existe_email = False

        for unique in uniques:

            if unique.get("name") == "uq_usuario_email":
                existe_email = True
                break

        with op.batch_alter_table("usuarios", schema=None) as batch_op:

            if existe_email:
                batch_op.drop_constraint(
                    "uq_usuario_email",
                    type_="unique",
                )

            columnas = {
                columna["name"]
                for columna in inspector.get_columns("usuarios")
            }

            if "es_superadmin" in columnas:

                batch_op.drop_column("es_superadmin")

            batch_op.alter_column(
                "rol_id",
                existing_type=sa.INTEGER(),
                nullable=False,
            )

            batch_op.alter_column(
                "empresa_id",
                existing_type=sa.INTEGER(),
                nullable=False,
            )


    # ============================================================
    # EMPRESA_MODULOS
    # ============================================================

    if "empresa_modulos" in tablas:
        op.drop_table("empresa_modulos")


    # ============================================================
    # MODULOS
    # ============================================================

    if "modulos" in tablas:
        op.drop_table("modulos")
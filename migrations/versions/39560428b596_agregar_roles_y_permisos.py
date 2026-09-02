"""
Agregar roles y permisos

Revision ID: 39560428b596
Revises: 594eb73a5b59
Create Date: 2026-08-27 22:17:22.825399

"""

from alembic import op
import sqlalchemy as sa


# ============================================================
# IDENTIFICADORES DE ALEMBIC
# ============================================================

revision = "39560428b596"
down_revision = "594eb73a5b59"
branch_labels = None
depends_on = None


def upgrade():

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    tablas = inspector.get_table_names()

    # ============================================================
    # TABLA ROLES
    # ============================================================

    if "roles" not in tablas:

        op.create_table(
            "roles",

            sa.Column(
                "id",
                sa.Integer(),
                nullable=False
            ),

            sa.Column(
                "nombre",
                sa.String(length=50),
                nullable=False
            ),

            sa.PrimaryKeyConstraint("id"),

            sa.UniqueConstraint(
                "nombre",
                name="uq_rol_nombre"
            )
        )

    # ============================================================
    # TABLA PERMISOS
    # ============================================================

    # Volvemos a consultar las tablas porque roles pudo haber
    # sido creada en el paso anterior.

    inspector = sa.inspect(bind)
    tablas = inspector.get_table_names()

    if "permisos" not in tablas:

        op.create_table(
            "permisos",

            sa.Column(
                "id",
                sa.Integer(),
                nullable=False
            ),

            sa.Column(
                "nombre",
                sa.String(length=100),
                nullable=False
            ),

            sa.PrimaryKeyConstraint("id"),

            sa.UniqueConstraint(
                "nombre",
                name="uq_permiso_nombre"
            )
        )

    # ============================================================
    # MODIFICAR USUARIOS
    # ============================================================

    inspector = sa.inspect(bind)

    columnas_usuarios = {
        columna["name"]
        for columna in inspector.get_columns("usuarios")
    }

    # ------------------------------------------------------------
    # AGREGAR rol_id
    # ------------------------------------------------------------

    if "rol_id" not in columnas_usuarios:

        with op.batch_alter_table(
            "usuarios",
            schema=None
        ) as batch_op:

            batch_op.add_column(
                sa.Column(
                    "rol_id",
                    sa.Integer(),
                    nullable=True
                )
            )

    # ============================================================
    # CREAR FOREIGN KEY usuarios.rol_id -> roles.id
    # ============================================================

    inspector = sa.inspect(bind)

    foreign_keys = inspector.get_foreign_keys("usuarios")

    existe_fk_rol = False

    for fk in foreign_keys:

        columnas = fk.get("constrained_columns", [])
        tabla_referenciada = fk.get("referred_table")

        if (
            columnas == ["rol_id"]
            and tabla_referenciada == "roles"
        ):
            existe_fk_rol = True
            break

    if not existe_fk_rol:

        with op.batch_alter_table(
            "usuarios",
            schema=None
        ) as batch_op:

            batch_op.create_foreign_key(
                "fk_usuarios_rol_id",
                "roles",
                ["rol_id"],
                ["id"]
            )

    # ============================================================
    # ELIMINAR COLUMNA ANTIGUA "rol"
    # ============================================================

    inspector = sa.inspect(bind)

    columnas_usuarios = {
        columna["name"]
        for columna in inspector.get_columns("usuarios")
    }

    if "rol" in columnas_usuarios:

        with op.batch_alter_table(
            "usuarios",
            schema=None
        ) as batch_op:

            batch_op.drop_column("rol")


def downgrade():

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    tablas = inspector.get_table_names()

    # ============================================================
    # USUARIOS
    # ============================================================

    if "usuarios" in tablas:

        inspector = sa.inspect(bind)

        columnas_usuarios = {
            columna["name"]
            for columna in inspector.get_columns("usuarios")
        }

        # --------------------------------------------------------
        # ELIMINAR FOREIGN KEY
        # --------------------------------------------------------

        foreign_keys = inspector.get_foreign_keys("usuarios")

        existe_fk_rol = False

        for fk in foreign_keys:

            if fk.get("name") == "fk_usuarios_rol_id":
                existe_fk_rol = True
                break

        with op.batch_alter_table(
            "usuarios",
            schema=None
        ) as batch_op:

            if existe_fk_rol:

                batch_op.drop_constraint(
                    "fk_usuarios_rol_id",
                    type_="foreignkey"
                )

            # ----------------------------------------------------
            # ELIMINAR rol_id
            # ----------------------------------------------------

            if "rol_id" in columnas_usuarios:

                batch_op.drop_column("rol_id")

            # ----------------------------------------------------
            # RESTAURAR rol
            # ----------------------------------------------------

            if "rol" not in columnas_usuarios:

                batch_op.add_column(
                    sa.Column(
                        "rol",
                        sa.String(length=50),
                        nullable=True
                    )
                )

    # ============================================================
    # ELIMINAR PERMISOS
    # ============================================================

    inspector = sa.inspect(bind)

    tablas = inspector.get_table_names()

    if "permisos" in tablas:

        op.drop_table("permisos")

    # ============================================================
    # ELIMINAR ROLES
    # ============================================================

    inspector = sa.inspect(bind)

    tablas = inspector.get_table_names()

    if "roles" in tablas:

        op.drop_table("roles")
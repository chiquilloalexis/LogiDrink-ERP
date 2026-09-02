from datetime import datetime

from flask_login import UserMixin

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from apps import db


class Usuario(UserMixin, db.Model):

    __tablename__ = "usuarios"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================================================
    # EMPRESA
    # ==========================================================

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id"),
        nullable=True
    )

    empresa = db.relationship(
        "Empresa",
        back_populates="usuarios"
    )

    # ==========================================================
    # INFORMACION DEL USUARIO
    # ==========================================================

    nombre = db.Column(
        db.String(150),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    # ==========================================================
    # FOTO DE PERFIL
    # ==========================================================

    foto_perfil = db.Column(
        db.LargeBinary,
        nullable=True
    )

    foto_perfil_tipo = db.Column(
        db.String(100),
        nullable=True
    )

    # ==========================================================
    # ROL
    # ==========================================================

    rol_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.id"),
        nullable=True
    )

    rol_objeto = db.relationship(
        "Rol",
        back_populates="usuarios"
    )

    # ==========================================================
    # SUPERADMIN
    # ==========================================================

    es_superadmin = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    # ==========================================================
    # ESTADO
    # ==========================================================

    activo = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    fecha_creacion = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ==========================================================
    # CONTRASEÑA
    # ==========================================================

    def establecer_password(self, password):

        self.password_hash = generate_password_hash(
            password
        )

    def verificar_password(self, password):

        return check_password_hash(
            self.password_hash,
            password
        )

    # ==========================================================
    # SUPERADMINISTRADOR
    # ==========================================================

    def es_super_administrador(self):

        return bool(
            self.es_superadmin
        )

    # ==========================================================
    # ADMINISTRADOR DE EMPRESA
    # ==========================================================

    def es_admin_empresa(self):

        if self.es_superadmin:
            return True

        if not self.rol_objeto:
            return False

        return (
            self.rol_objeto.nombre.lower()
            in (
                "administrador",
                "admin"
            )
        )

    # ==========================================================
    # VERIFICAR SI LA EMPRESA TIENE EL MODULO
    # ==========================================================

    def empresa_tiene_modulo(self, nombre_modulo):

        if self.es_superadmin:
            return True

        if not self.empresa:
            return False

        if not self.empresa.activa:
            return False

        nombre_modulo = (
            nombre_modulo
            .strip()
            .lower()
        )

        for asignacion in self.empresa.modulos:

            if not asignacion.activo:
                continue

            if not asignacion.modulo:
                continue

            if not asignacion.modulo.activo:
                continue

            nombre = (
                asignacion.modulo.nombre
                .strip()
                .lower()
            )

            if nombre == nombre_modulo:
                return True

        return False

    # ==========================================================
    # PERMISO
    # ==========================================================

    def tiene_permiso(
        self,
        modulo,
        accion="ver"
    ):

        # ------------------------------------------------------
        # SUPERADMIN
        # ------------------------------------------------------

        if self.es_superadmin:
            return True

        # ------------------------------------------------------
        # LA EMPRESA DEBE TENER EL MODULO ACTIVO
        # ------------------------------------------------------

        if not self.empresa_tiene_modulo(
            modulo
        ):
            return False

        # ------------------------------------------------------
        # ADMINISTRADOR DE EMPRESA
        # ------------------------------------------------------

        if self.es_admin_empresa():

            return True

        # ------------------------------------------------------
        # USUARIOS NORMALES
        # ------------------------------------------------------

        if not self.rol_objeto:
            return False

        for permiso in self.rol_objeto.permisos:

            if not permiso:
                continue

            if (
                permiso.modulo
                and permiso.modulo.strip().lower()
                == modulo.strip().lower()
            ):

                return bool(
                    getattr(
                        permiso,
                        accion,
                        False
                    )
                )

        return False

    # ==========================================================
    # REPRESENTACION
    # ==========================================================

    def __repr__(self):

        return f"<Usuario {self.email}>"
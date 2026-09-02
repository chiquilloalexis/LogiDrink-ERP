from datetime import datetime

from apps import db


class Empresa(db.Model):

    __tablename__ = "empresas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(150),
        nullable=False
    )

    nit = db.Column(
        db.String(30),
        nullable=False,
        unique=True
    )

    direccion = db.Column(
        db.String(200)
    )

    telefono = db.Column(
        db.String(30)
    )

    email = db.Column(
        db.String(150)
    )

    activa = db.Column(
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
    # USUARIOS
    # ==========================================================

    usuarios = db.relationship(
        "Usuario",
        back_populates="empresa",
        cascade="all, delete-orphan"
    )

    # ==========================================================
    # ROLES
    # ==========================================================

    roles = db.relationship(
        "Rol",
        back_populates="empresa",
        cascade="all, delete-orphan"
    )

    # ==========================================================
    # MÓDULOS CONTRATADOS
    # ==========================================================

    modulos = db.relationship(
        "EmpresaModulo",
        back_populates="empresa",
        cascade="all, delete-orphan"
    )

    # ==========================================================
    # REPRESENTACIÓN
    # ==========================================================

    def __repr__(self):

        return f"<Empresa {self.nombre}>"
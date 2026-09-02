
from datetime import datetime

from apps import db


class Proveedor(db.Model):
    __tablename__ = "proveedores"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id"),
        nullable=False
    )

    nombre = db.Column(
        db.String(150),
        nullable=False
    )

    nit = db.Column(
        db.String(50)
    )

    telefono = db.Column(
        db.String(50)
    )

    direccion = db.Column(
        db.String(255)
    )

    correo = db.Column(
        db.String(150)
    )

    contacto = db.Column(
        db.String(150)
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    empresa = db.relationship(
        "Empresa",
        backref=db.backref(
            "proveedores",
            lazy=True
        )
    )

    compras = db.relationship(
        "Compra",
        back_populates="proveedor",
        lazy=True
    )

    def __repr__(self):
        return f"<Proveedor {self.nombre}>"

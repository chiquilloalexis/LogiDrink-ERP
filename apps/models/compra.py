
from datetime import datetime

from apps import db


class Compra(db.Model):
    __tablename__ = "compras"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id"),
        nullable=False
    )

    proveedor_id = db.Column(
        db.Integer,
        db.ForeignKey("proveedores.id"),
        nullable=False
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=True
    )

    numero = db.Column(
        db.String(50),
        nullable=False
    )

    fecha = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    subtotal = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    descuento = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    total = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    estado = db.Column(
        db.String(30),
        nullable=False,
        default="Completada"
    )

    observaciones = db.Column(
        db.Text
    )

    empresa = db.relationship(
        "Empresa",
        backref=db.backref(
            "compras",
            lazy=True
        )
    )

    proveedor = db.relationship(
        "Proveedor",
        back_populates="compras"
    )

    usuario = db.relationship(
        "Usuario",
        backref=db.backref(
            "compras_realizadas",
            lazy=True
        )
    )

    detalles = db.relationship(
        "DetalleCompra",
        back_populates="compra",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<Compra {self.numero}>"

from datetime import datetime

from apps import db


class MovimientoInventario(db.Model):
    __tablename__ = "movimientos_inventario"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id"),
        nullable=False
    )

    producto_id = db.Column(
        db.Integer,
        db.ForeignKey("productos.id"),
        nullable=False
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    tipo = db.Column(
        db.String(20),
        nullable=False
    )

    cantidad = db.Column(
        db.Integer,
        nullable=False
    )

    stock_anterior = db.Column(
        db.Integer,
        nullable=False
    )

    stock_nuevo = db.Column(
        db.Integer,
        nullable=False
    )

    motivo = db.Column(
        db.String(255),
        nullable=True
    )

    fecha = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    empresa = db.relationship(
        "Empresa"
    )

    producto = db.relationship(
        "Producto"
    )

    usuario = db.relationship(
        "Usuario"
    )
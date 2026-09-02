
from apps import db


class DetalleCompra(db.Model):
    __tablename__ = "detalles_compras"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    compra_id = db.Column(
        db.Integer,
        db.ForeignKey("compras.id"),
        nullable=False
    )

    producto_id = db.Column(
        db.Integer,
        db.ForeignKey("productos.id"),
        nullable=False
    )

    tipo_compra = db.Column(
        db.String(20),
        nullable=False,
        default="unidad"
    )

    cantidad = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    unidades_por_caja = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    precio_unitario = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    subtotal = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    unidades_ingresadas = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    compra = db.relationship(
        "Compra",
        back_populates="detalles"
    )

    producto = db.relationship(
        "Producto",
        backref=db.backref(
            "detalles_compras",
            lazy=True
        )
    )

    def __repr__(self):
        return f"<DetalleCompra {self.id}>"
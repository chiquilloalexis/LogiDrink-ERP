from apps import db


class DetalleVenta(db.Model):
    __tablename__ = "detalles_ventas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    venta_id = db.Column(
        db.Integer,
        db.ForeignKey("ventas.id"),
        nullable=False
    )

    producto_id = db.Column(
        db.Integer,
        db.ForeignKey("productos.id"),
        nullable=False
    )

    cantidad = db.Column(
        db.Integer,
        nullable=False
    )

    tipo_venta = db.Column(
        db.String(20),
        nullable=False,
        default="unidad"
    )

    precio_unitario = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    subtotal = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    venta = db.relationship(
        "Venta",
        back_populates="detalles"
    )

    producto = db.relationship(
        "Producto",
        backref=db.backref(
            "detalles_ventas",
            lazy=True
        )
    )

    def __repr__(self):
        return f"<DetalleVenta {self.id}>"
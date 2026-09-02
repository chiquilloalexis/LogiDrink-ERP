from datetime import datetime

from apps import db


class Venta(db.Model):
    __tablename__ = "ventas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id"),
        nullable=False
    )

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id"),
        nullable=True
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
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

    metodo_pago = db.Column(
        db.String(30),
        nullable=False,
        default="efectivo"
    )

    estado = db.Column(
        db.String(30),
        nullable=False,
        default="completada"
    )

    empresa = db.relationship(
        "Empresa",
        backref=db.backref("ventas", lazy=True)
    )

    cliente = db.relationship(
        "Cliente",
        backref=db.backref("ventas", lazy=True)
    )

    usuario = db.relationship(
        "Usuario",
        backref=db.backref("ventas", lazy=True)
    )

    detalles = db.relationship(
        "DetalleVenta",
        back_populates="venta",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Venta {self.id}>"
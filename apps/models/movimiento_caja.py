
from datetime import datetime

from apps import db


class MovimientoCaja(db.Model):
    __tablename__ = "movimientos_caja"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    caja_id = db.Column(
        db.Integer,
        db.ForeignKey("cajas.id"),
        nullable=False
    )

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id"),
        nullable=False
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=True
    )

    tipo = db.Column(
        db.String(20),
        nullable=False
    )

    concepto = db.Column(
        db.String(150),
        nullable=False
    )

    descripcion = db.Column(
        db.Text,
        nullable=True
    )

    valor = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    metodo_pago = db.Column(
        db.String(30),
        nullable=False,
        default="Efectivo"
    )

    referencia = db.Column(
        db.String(100),
        nullable=True
    )

    fecha = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    caja = db.relationship(
        "Caja",
        back_populates="movimientos"
    )

    empresa = db.relationship(
        "Empresa",
        backref=db.backref(
            "movimientos_caja",
            lazy=True
        )
    )

    usuario = db.relationship(
        "Usuario",
        backref=db.backref(
            "movimientos_caja_realizados",
            lazy=True
        )
    )

    def __repr__(self):
        return f"<MovimientoCaja {self.tipo} {self.valor}>"

from datetime import datetime

from apps import db


class Caja(db.Model):
    __tablename__ = "cajas"

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
        db.String(100),
        nullable=False,
        default="Caja principal"
    )

    saldo_inicial = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    saldo_actual = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    estado = db.Column(
        db.String(20),
        nullable=False,
        default="cerrada"
    )

    fecha_apertura = db.Column(
        db.DateTime,
        nullable=True
    )

    fecha_cierre = db.Column(
        db.DateTime,
        nullable=True
    )

    usuario_apertura_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=True
    )

    usuario_cierre_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=True
    )

    observaciones = db.Column(
        db.Text,
        nullable=True
    )

    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    empresa = db.relationship(
        "Empresa",
        backref=db.backref(
            "cajas",
            lazy=True
        )
    )

    usuario_apertura = db.relationship(
        "Usuario",
        foreign_keys=[usuario_apertura_id],
        backref=db.backref(
            "cajas_abiertas",
            lazy=True
        )
    )

    usuario_cierre = db.relationship(
        "Usuario",
        foreign_keys=[usuario_cierre_id],
        backref=db.backref(
            "cajas_cerradas",
            lazy=True
        )
    )

    movimientos = db.relationship(
        "MovimientoCaja",
        back_populates="caja",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<Caja {self.nombre}>"

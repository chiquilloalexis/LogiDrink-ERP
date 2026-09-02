from datetime import datetime

from apps import db


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id"),
        nullable=False
    )

    nombre = db.Column(
        db.String(150),
        nullable=False
    )

    documento = db.Column(
        db.String(50),
        nullable=False
    )

    telefono = db.Column(
        db.String(30)
    )

    direccion = db.Column(
        db.String(200)
    )

    email = db.Column(
        db.String(150)
    )

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

    empresa = db.relationship(
        "Empresa",
        backref=db.backref("clientes", lazy=True)
    )

    def __repr__(self):
        return f"<Cliente {self.nombre}>"
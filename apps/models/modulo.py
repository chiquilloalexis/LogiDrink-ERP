from apps import db


class Modulo(db.Model):

    __tablename__ = "modulos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    descripcion = db.Column(
        db.String(255)
    )

    activo = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    empresas = db.relationship(
        "EmpresaModulo",
        back_populates="modulo",
        cascade="all, delete-orphan"
    )

    def __repr__(self):

        return f"<Modulo {self.nombre}>"
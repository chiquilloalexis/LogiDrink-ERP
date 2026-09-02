from apps import db


class Rol(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id"),
        nullable=False
    )

    nombre = db.Column(
        db.String(100),
        nullable=False
    )

    descripcion = db.Column(
        db.String(255)
    )

    activo = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    empresa = db.relationship(
        "Empresa",
        back_populates="roles"
    )

    permisos = db.relationship(
        "Permiso",
        back_populates="rol",
        cascade="all, delete-orphan"
    )

    usuarios = db.relationship(
        "Usuario",
        back_populates="rol_objeto"
    )

    def __repr__(self):
        return f"<Rol {self.nombre}>"
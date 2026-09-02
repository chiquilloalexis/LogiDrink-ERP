from apps import db


class Permiso(db.Model):
    __tablename__ = "permisos"

    id = db.Column(db.Integer, primary_key=True)

    rol_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.id"),
        nullable=False
    )

    modulo = db.Column(
        db.String(100),
        nullable=False
    )

    ver = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    crear = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    editar = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    eliminar = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    reportes = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    rol = db.relationship(
        "Rol",
        back_populates="permisos"
    )

    def __repr__(self):
        return f"<Permiso {self.modulo}>"
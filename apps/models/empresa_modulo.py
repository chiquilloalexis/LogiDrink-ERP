from apps import db


class EmpresaModulo(db.Model):

    __tablename__ = "empresa_modulos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id"),
        nullable=False
    )

    modulo_id = db.Column(
        db.Integer,
        db.ForeignKey("modulos.id"),
        nullable=False
    )

    activo = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    empresa = db.relationship(
        "Empresa",
        back_populates="modulos"
    )

    modulo = db.relationship(
        "Modulo",
        back_populates="empresas"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "empresa_id",
            "modulo_id",
            name="uq_empresa_modulo"
        ),
    )

    def __repr__(self):

        return (
            f"<EmpresaModulo "
            f"empresa={self.empresa_id} "
            f"modulo={self.modulo_id}>"
        )
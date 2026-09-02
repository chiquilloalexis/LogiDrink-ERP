from datetime import datetime

from apps import db


class Producto(db.Model):
    __tablename__ = "productos"

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
        db.String(150),
        nullable=False
    )

    codigo = db.Column(
        db.String(50),
        nullable=False
    )

    descripcion = db.Column(
        db.String(255)
    )

    categoria = db.Column(
        db.String(100)
    )

    # ==========================================
    # IMAGEN DEL PRODUCTO
    # ==========================================

    imagen = db.Column(
        db.LargeBinary,
        nullable=True
    )

    imagen_tipo = db.Column(
        db.String(100),
        nullable=True
    )

    # ==========================================
    # PRECIOS
    # ==========================================

    precio_compra = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    precio_venta = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    # Precio específico para venta por caja
    precio_compra_caja = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    precio_venta_caja = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    # ==========================================
    # INVENTARIO
    # ==========================================

    # Stock base: SIEMPRE se almacena en unidades
    stock = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    stock_minimo = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    # Cantidad de unidades que contiene una caja
    unidades_por_caja = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    # Indica si el producto puede venderse por caja
    maneja_cajas = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    # ==========================================
    # ESTADO
    # ==========================================

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # ==========================================
    # RELACIONES
    # ==========================================

    empresa = db.relationship(
        "Empresa",
        backref=db.backref("productos", lazy=True)
    )

    # ==========================================
    # PROPIEDADES DE INVENTARIO
    # ==========================================

    @property
    def cajas_disponibles(self):
        """
        Cantidad de cajas completas disponibles.
        """
        if not self.maneja_cajas or self.unidades_por_caja <= 0:
            return 0

        return self.stock // self.unidades_por_caja

    @property
    def unidades_sueltas(self):
        """
        Unidades que quedan fuera de las cajas completas.
        """
        if not self.maneja_cajas or self.unidades_por_caja <= 0:
            return self.stock

        return self.stock % self.unidades_por_caja

    @property
    def stock_formateado(self):
        """
        Ejemplo:
        10 cajas + 5 unidades
        """
        if not self.maneja_cajas:
            return f"{self.stock} unidades"

        cajas = self.cajas_disponibles
        unidades = self.unidades_sueltas

        if cajas and unidades:
            return f"{cajas} cajas + {unidades} unidades"

        if cajas:
            return f"{cajas} cajas"

        return f"{unidades} unidades"

    def __repr__(self):
        return f"<Producto {self.nombre}>"
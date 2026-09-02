from datetime import datetime, time

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import login_required, current_user

from apps import db
from apps.models import Producto, MovimientoInventario


inventario_bp = Blueprint(
    "inventario",
    __name__,
    url_prefix="/inventario"
)


# ==========================================================
# INVENTARIO
# ==========================================================

@inventario_bp.route("/")
@login_required
def index():

    productos = db.session.execute(
        db.select(Producto)
        .where(
            Producto.empresa_id == current_user.empresa_id,
            Producto.activo.is_(True)
        )
        .order_by(Producto.nombre)
    ).scalars().all()

    total_productos = len(productos)

    total_unidades = sum(
        producto.stock or 0
        for producto in productos
    )

    productos_stock_bajo = sum(
        1
        for producto in productos
        if (producto.stock or 0) <= (producto.stock_minimo or 0)
    )

    productos_con_cajas = sum(
        1
        for producto in productos
        if producto.maneja_cajas
    )

    return render_template(
        "inventario/index.html",
        productos=productos,
        total_productos=total_productos,
        total_unidades=total_unidades,
        productos_stock_bajo=productos_stock_bajo,
        productos_con_cajas=productos_con_cajas
    )


# ==========================================================
# ENTRADA DE INVENTARIO
# ==========================================================

@inventario_bp.route("/entrada", methods=["GET", "POST"])
@login_required
def entrada():

    productos = db.session.execute(
        db.select(Producto)
        .where(
            Producto.empresa_id == current_user.empresa_id,
            Producto.activo.is_(True)
        )
        .order_by(Producto.nombre)
    ).scalars().all()

    if request.method == "POST":

        producto_id = request.form.get(
            "producto_id",
            type=int
        )

        cantidad = request.form.get(
            "cantidad",
            type=int
        )

        observacion = request.form.get(
            "observacion",
            ""
        ).strip()

        if (
            not producto_id
            or not cantidad
            or cantidad <= 0
        ):

            flash(
                "Debes seleccionar un producto y una cantidad válida.",
                "error"
            )

            return render_template(
                "inventario/entrada.html",
                productos=productos
            )

        producto = db.session.execute(
            db.select(Producto)
            .where(
                Producto.id == producto_id,
                Producto.empresa_id == current_user.empresa_id,
                Producto.activo.is_(True)
            )
        ).scalar_one_or_none()

        if not producto:

            flash(
                "El producto no existe o no pertenece a esta empresa.",
                "error"
            )

            return render_template(
                "inventario/entrada.html",
                productos=productos
            )

        stock_anterior = producto.stock or 0

        producto.stock = stock_anterior + cantidad

        movimiento = MovimientoInventario(
            empresa_id=current_user.empresa_id,
            producto_id=producto.id,
            usuario_id=current_user.id,
            tipo="entrada",
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=producto.stock,
            motivo=observacion or "Entrada de inventario"
        )

        db.session.add(movimiento)
        db.session.commit()

        flash(
            f"Entrada registrada correctamente. "
            f"El stock de {producto.nombre} ahora es "
            f"{producto.stock} unidades.",
            "success"
        )

        return redirect(
            url_for("inventario.index")
        )

    return render_template(
        "inventario/entrada.html",
        productos=productos
    )


# ==========================================================
# SALIDA DE INVENTARIO
# ==========================================================

@inventario_bp.route("/salida", methods=["GET", "POST"])
@login_required
def salida():

    productos = db.session.execute(
        db.select(Producto)
        .where(
            Producto.empresa_id == current_user.empresa_id,
            Producto.activo.is_(True)
        )
        .order_by(Producto.nombre)
    ).scalars().all()

    if request.method == "POST":

        producto_id = request.form.get(
            "producto_id",
            type=int
        )

        cantidad = request.form.get(
            "cantidad",
            type=int
        )

        observacion = request.form.get(
            "observacion",
            ""
        ).strip()

        if (
            not producto_id
            or not cantidad
            or cantidad <= 0
        ):

            flash(
                "Debes seleccionar un producto y una cantidad válida.",
                "error"
            )

            return render_template(
                "inventario/salida.html",
                productos=productos
            )

        producto = db.session.execute(
            db.select(Producto)
            .where(
                Producto.id == producto_id,
                Producto.empresa_id == current_user.empresa_id,
                Producto.activo.is_(True)
            )
        ).scalar_one_or_none()

        if not producto:

            flash(
                "El producto no existe o no pertenece a esta empresa.",
                "error"
            )

            return render_template(
                "inventario/salida.html",
                productos=productos
            )

        stock_anterior = producto.stock or 0

        if cantidad > stock_anterior:

            flash(
                f"No hay suficiente stock. "
                f"Stock disponible: {stock_anterior} unidades.",
                "error"
            )

            return render_template(
                "inventario/salida.html",
                productos=productos
            )

        producto.stock = stock_anterior - cantidad

        movimiento = MovimientoInventario(
            empresa_id=current_user.empresa_id,
            producto_id=producto.id,
            usuario_id=current_user.id,
            tipo="salida",
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=producto.stock,
            motivo=observacion or "Salida de inventario"
        )

        db.session.add(movimiento)
        db.session.commit()

        flash(
            f"Salida registrada correctamente. "
            f"El stock de {producto.nombre} ahora es "
            f"{producto.stock} unidades.",
            "success"
        )

        return redirect(
            url_for("inventario.index")
        )

    return render_template(
        "inventario/salida.html",
        productos=productos
    )


# ==========================================================
# HISTORIAL DE MOVIMIENTOS
# ==========================================================

@inventario_bp.route("/movimientos")
@login_required
def movimientos():

    productos = db.session.execute(
        db.select(Producto)
        .where(
            Producto.empresa_id == current_user.empresa_id
        )
        .order_by(Producto.nombre)
    ).scalars().all()

    producto_id = request.args.get(
        "producto_id",
        type=int
    )

    tipo = request.args.get(
        "tipo",
        ""
    ).strip().lower()

    fecha_desde = request.args.get(
        "desde",
        ""
    ).strip()

    fecha_hasta = request.args.get(
        "hasta",
        ""
    ).strip()

    consulta = db.select(
        MovimientoInventario
    ).where(
        MovimientoInventario.empresa_id
        == current_user.empresa_id
    )

    if producto_id:

        consulta = consulta.where(
            MovimientoInventario.producto_id
            == producto_id
        )

    if tipo in ("entrada", "salida"):

        consulta = consulta.where(
            MovimientoInventario.tipo == tipo
        )

    if fecha_desde:

        try:

            fecha_desde_obj = datetime.strptime(
                fecha_desde,
                "%Y-%m-%d"
            ).date()

            inicio = datetime.combine(
                fecha_desde_obj,
                time.min
            )

            consulta = consulta.where(
                MovimientoInventario.fecha >= inicio
            )

        except ValueError:

            fecha_desde = ""

    if fecha_hasta:

        try:

            fecha_hasta_obj = datetime.strptime(
                fecha_hasta,
                "%Y-%m-%d"
            ).date()

            fin = datetime.combine(
                fecha_hasta_obj,
                time.max
            )

            consulta = consulta.where(
                MovimientoInventario.fecha <= fin
            )

        except ValueError:

            fecha_hasta = ""

    movimientos = db.session.execute(
        consulta.order_by(
            MovimientoInventario.fecha.desc()
        )
    ).scalars().all()

    total_movimientos = len(movimientos)

    total_entradas = sum(
        movimiento.cantidad
        for movimiento in movimientos
        if movimiento.tipo == "entrada"
    )

    total_salidas = sum(
        movimiento.cantidad
        for movimiento in movimientos
        if movimiento.tipo == "salida"
    )

    return render_template(
        "inventario/movimientos.html",
        movimientos=movimientos,
        productos=productos,
        producto_id=producto_id,
        tipo=tipo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        total_movimientos=total_movimientos,
        total_entradas=total_entradas,
        total_salidas=total_salidas
    )
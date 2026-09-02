from datetime import datetime, time, timedelta

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import func

from apps import db
from apps.models.venta import Venta
from apps.models.detalle_venta import DetalleVenta
from apps.models.producto import Producto
from apps.models.cliente import Cliente


reportes_bp = Blueprint(
    "reportes",
    __name__,
    url_prefix="/reportes"
)


# ==========================================================
# REPORTES
# ==========================================================

@reportes_bp.route("/")
@login_required
def index():

    # ==========================================================
    # FECHA ACTUAL
    # ==========================================================

    hoy = datetime.now().date()

    # ==========================================================
    # FILTRO DE FECHAS
    # ==========================================================

    fecha_desde = request.args.get("fecha_desde")
    fecha_hasta = request.args.get("fecha_hasta")

    try:

        if fecha_desde:
            fecha_desde_obj = datetime.strptime(
                fecha_desde,
                "%Y-%m-%d"
            ).date()
        else:
            fecha_desde_obj = hoy.replace(day=1)

    except (ValueError, TypeError):

        fecha_desde_obj = hoy.replace(day=1)

    try:

        if fecha_hasta:
            fecha_hasta_obj = datetime.strptime(
                fecha_hasta,
                "%Y-%m-%d"
            ).date()
        else:
            fecha_hasta_obj = hoy

    except (ValueError, TypeError):

        fecha_hasta_obj = hoy

    # ==========================================================
    # VALIDAR RANGO
    # ==========================================================

    if fecha_desde_obj > fecha_hasta_obj:

        fecha_desde_obj, fecha_hasta_obj = (
            fecha_hasta_obj,
            fecha_desde_obj
        )

    # ==========================================================
    # RANGO DE FECHAS
    # ==========================================================

    inicio_periodo = datetime.combine(
        fecha_desde_obj,
        time.min
    )

    fin_periodo = datetime.combine(
        fecha_hasta_obj,
        time.max
    )

    # ==========================================================
    # FILTRO BASE DE VENTAS
    # ==========================================================

    ventas_periodo = Venta.query.filter(
        Venta.empresa_id == current_user.empresa_id,
        Venta.fecha >= inicio_periodo,
        Venta.fecha <= fin_periodo,
        Venta.estado == "completada"
    )

    # ==========================================================
    # TOTAL VENDIDO
    # ==========================================================

    total_ventas = db.session.query(
        func.coalesce(
            func.sum(Venta.total),
            0
        )
    ).filter(
        Venta.empresa_id == current_user.empresa_id,
        Venta.fecha >= inicio_periodo,
        Venta.fecha <= fin_periodo,
        Venta.estado == "completada"
    ).scalar()

    total_ventas = float(total_ventas or 0)

    # ==========================================================
    # CANTIDAD DE VENTAS
    # ==========================================================

    cantidad_ventas = ventas_periodo.count()

    # ==========================================================
    # PROMEDIO POR VENTA
    # ==========================================================

    if cantidad_ventas > 0:

        promedio_venta = (
            total_ventas / cantidad_ventas
        )

    else:

        promedio_venta = 0

    ticket_promedio = promedio_venta

    # ==========================================================
    # TOTAL DE PRODUCTOS VENDIDOS
    # ==========================================================

    productos_vendidos_total = db.session.query(
        func.coalesce(
            func.sum(DetalleVenta.cantidad),
            0
        )
    ).join(
        Venta,
        Venta.id == DetalleVenta.venta_id
    ).filter(
        Venta.empresa_id == current_user.empresa_id,
        Venta.fecha >= inicio_periodo,
        Venta.fecha <= fin_periodo,
        Venta.estado == "completada"
    ).scalar()

    productos_vendidos_total = float(
        productos_vendidos_total or 0
    )

    # ==========================================================
    # VENTAS POR DÍA
    # ==========================================================

    ventas_por_dia = []

    fecha_actual = fecha_desde_obj

    while fecha_actual <= fecha_hasta_obj:

        inicio = datetime.combine(
            fecha_actual,
            time.min
        )

        fin = datetime.combine(
            fecha_actual,
            time.max
        )

        total = db.session.query(
            func.coalesce(
                func.sum(Venta.total),
                0
            )
        ).filter(
            Venta.empresa_id == current_user.empresa_id,
            Venta.fecha >= inicio,
            Venta.fecha <= fin,
            Venta.estado == "completada"
        ).scalar()

        cantidad = Venta.query.filter(
            Venta.empresa_id == current_user.empresa_id,
            Venta.fecha >= inicio,
            Venta.fecha <= fin,
            Venta.estado == "completada"
        ).count()

        ventas_por_dia.append({
            "fecha": fecha_actual.strftime("%d/%m"),
            "total": float(total or 0),
            "cantidad": cantidad
        })

        fecha_actual += timedelta(days=1)

    # ==========================================================
    # PRODUCTOS MÁS VENDIDOS
    # ==========================================================

    productos_mas_vendidos = db.session.query(
        Producto.nombre,
        func.coalesce(
            func.sum(DetalleVenta.cantidad),
            0
        ).label("cantidad"),
        func.coalesce(
            func.sum(DetalleVenta.subtotal),
            0
        ).label("total")
    ).join(
        DetalleVenta,
        DetalleVenta.producto_id == Producto.id
    ).join(
        Venta,
        Venta.id == DetalleVenta.venta_id
    ).filter(
        Producto.empresa_id == current_user.empresa_id,
        Venta.empresa_id == current_user.empresa_id,
        Venta.fecha >= inicio_periodo,
        Venta.fecha <= fin_periodo,
        Venta.estado == "completada"
    ).group_by(
        Producto.id,
        Producto.nombre
    ).order_by(
        func.sum(DetalleVenta.cantidad).desc()
    ).limit(10).all()

    # ==========================================================
    # VENTAS POR MÉTODO DE PAGO
    # ==========================================================

    ventas_metodo_pago = db.session.query(
        Venta.metodo_pago,
        func.count(Venta.id).label("cantidad"),
        func.coalesce(
            func.sum(Venta.total),
            0
        ).label("total")
    ).filter(
        Venta.empresa_id == current_user.empresa_id,
        Venta.fecha >= inicio_periodo,
        Venta.fecha <= fin_periodo,
        Venta.estado == "completada"
    ).group_by(
        Venta.metodo_pago
    ).order_by(
        func.sum(Venta.total).desc()
    ).all()

    # ==========================================================
    # INICIALIZAR MÉTODOS DE PAGO
    # ==========================================================

    efectivo = 0
    nequi = 0
    daviplata = 0
    transferencia = 0
    tarjeta = 0
    credito = 0
    otros = 0

    cantidad_efectivo = 0
    cantidad_nequi = 0
    cantidad_daviplata = 0
    cantidad_transferencia = 0
    cantidad_tarjeta = 0
    cantidad_credito = 0

    for metodo in ventas_metodo_pago:

        nombre_metodo = (
            str(metodo.metodo_pago or "")
            .strip()
            .lower()
        )

        total_metodo = float(
            metodo.total or 0
        )

        cantidad_metodo = int(
            metodo.cantidad or 0
        )

        if nombre_metodo == "efectivo":

            efectivo = total_metodo
            cantidad_efectivo = cantidad_metodo

        elif nombre_metodo == "nequi":

            nequi = total_metodo
            cantidad_nequi = cantidad_metodo

        elif nombre_metodo == "daviplata":

            daviplata = total_metodo
            cantidad_daviplata = cantidad_metodo

        elif nombre_metodo == "transferencia":

            transferencia = total_metodo
            cantidad_transferencia = cantidad_metodo

        elif nombre_metodo == "tarjeta":

            tarjeta = total_metodo
            cantidad_tarjeta = cantidad_metodo

        elif nombre_metodo == "credito":

            credito = total_metodo
            cantidad_credito = cantidad_metodo

        else:

            otros += total_metodo

    # ==========================================================
    # DESCUENTOS
    # ==========================================================

    total_descuentos = db.session.query(
        func.coalesce(
            func.sum(Venta.descuento),
            0
        )
    ).filter(
        Venta.empresa_id == current_user.empresa_id,
        Venta.fecha >= inicio_periodo,
        Venta.fecha <= fin_periodo,
        Venta.estado == "completada"
    ).scalar()

    total_descuentos = float(
        total_descuentos or 0
    )

    # ==========================================================
    # CLIENTES CON MÁS COMPRAS
    # ==========================================================

    clientes_mas_compras = db.session.query(
        Cliente.nombre,
        func.count(Venta.id).label("cantidad"),
        func.coalesce(
            func.sum(Venta.total),
            0
        ).label("total")
    ).join(
        Venta,
        Venta.cliente_id == Cliente.id
    ).filter(
        Cliente.empresa_id == current_user.empresa_id,
        Venta.empresa_id == current_user.empresa_id,
        Venta.fecha >= inicio_periodo,
        Venta.fecha <= fin_periodo,
        Venta.estado == "completada"
    ).group_by(
        Cliente.id,
        Cliente.nombre
    ).order_by(
        func.sum(Venta.total).desc()
    ).limit(10).all()

    # ==========================================================
    # PRODUCTOS CON STOCK BAJO
    # ==========================================================

    productos_stock_bajo = Producto.query.filter(
        Producto.empresa_id == current_user.empresa_id,
        Producto.activo.is_(True),
        Producto.stock <= Producto.stock_minimo
    ).order_by(
        Producto.stock.asc()
    ).all()

    # Alias utilizado por el HTML
    productos_bajo_stock = productos_stock_bajo

    # ==========================================================
    # PRODUCTOS AGOTADOS
    # ==========================================================

    productos_agotados = Producto.query.filter(
        Producto.empresa_id == current_user.empresa_id,
        Producto.activo.is_(True),
        Producto.stock <= 0
    ).count()

    # ==========================================================
    # VALOR DEL INVENTARIO
    # ==========================================================

    valor_inventario = db.session.query(
        func.coalesce(
            func.sum(
                Producto.stock * Producto.precio_compra
            ),
            0
        )
    ).filter(
        Producto.empresa_id == current_user.empresa_id,
        Producto.activo.is_(True)
    ).scalar()

    valor_inventario = float(
        valor_inventario or 0
    )

    # ==========================================================
    # ÚLTIMAS VENTAS
    # ==========================================================

    ultimas_ventas = ventas_periodo.order_by(
        Venta.fecha.desc()
    ).limit(20).all()

    # Alias para el HTML
    ventas = ultimas_ventas

    # ==========================================================
    # RENDER
    # ==========================================================

    return render_template(
        "reportes/index.html",

        usuario=current_user,

        # Fechas
        fecha_desde=fecha_desde_obj.strftime(
            "%Y-%m-%d"
        ),

        fecha_hasta=fecha_hasta_obj.strftime(
            "%Y-%m-%d"
        ),

        # Resumen
        total_ventas=total_ventas,
        cantidad_ventas=cantidad_ventas,
        ticket_promedio=ticket_promedio,
        promedio_venta=promedio_venta,

        # Productos
        productos_vendidos_total=productos_vendidos_total,
        productos_mas_vendidos=productos_mas_vendidos,

        # Gráficas
        ventas_por_dia=ventas_por_dia,

        # Métodos de pago
        ventas_metodo_pago=ventas_metodo_pago,
        efectivo=efectivo,
        nequi=nequi,
        daviplata=daviplata,
        transferencia=transferencia,
        tarjeta=tarjeta,
        credito=credito,
        otros=otros,

        cantidad_efectivo=cantidad_efectivo,
        cantidad_nequi=cantidad_nequi,
        cantidad_daviplata=cantidad_daviplata,
        cantidad_transferencia=cantidad_transferencia,
        cantidad_tarjeta=cantidad_tarjeta,
        cantidad_credito=cantidad_credito,

        # Descuentos
        total_descuentos=total_descuentos,

        # Clientes
        clientes_mas_compras=clientes_mas_compras,

        # Inventario
        productos_stock_bajo=productos_stock_bajo,
        productos_bajo_stock=productos_bajo_stock,
        productos_agotados=productos_agotados,
        valor_inventario=valor_inventario,

        # Ventas
        ultimas_ventas=ultimas_ventas,
        ventas=ventas
    )
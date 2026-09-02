from datetime import datetime, time, timedelta

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func

from apps import db
from apps.models.venta import Venta
from apps.models.detalle_venta import DetalleVenta
from apps.models.producto import Producto
from apps.models.cliente import Cliente
from apps.models.usuario import Usuario
from apps.models.empresa import Empresa
from apps.models.modulo import Modulo
from apps.models.empresa_modulo import EmpresaModulo


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard"
)


@dashboard_bp.route("/")
@login_required
def index():

    # ==========================================================
    # SUPERADMINISTRADOR
    #
    # El SuperAdmin NO pertenece a una empresa.
    # Por eso su dashboard debe mostrar información global
    # del sistema y no ventas/inventario de una empresa.
    # ==========================================================

    if current_user.es_superadmin:

        # ------------------------------------------------------
        # EMPRESAS
        # ------------------------------------------------------

        total_empresas = Empresa.query.count()

        empresas_activas = Empresa.query.filter(
            Empresa.activa.is_(True)
        ).count()

        empresas_inactivas = Empresa.query.filter(
            Empresa.activa.is_(False)
        ).count()

        # ------------------------------------------------------
        # USUARIOS
        # ------------------------------------------------------

        total_usuarios = Usuario.query.filter(
            Usuario.es_superadmin.is_(False)
        ).count()

        usuarios_activos = Usuario.query.filter(
            Usuario.es_superadmin.is_(False),
            Usuario.activo.is_(True)
        ).count()

        usuarios_inactivos = Usuario.query.filter(
            Usuario.es_superadmin.is_(False),
            Usuario.activo.is_(False)
        ).count()

        # ------------------------------------------------------
        # MÓDULOS DISPONIBLES EN EL SISTEMA
        # ------------------------------------------------------

        total_modulos = Modulo.query.count()

        modulos_activos = Modulo.query.filter(
            Modulo.activo.is_(True)
        ).count()

        modulos_inactivos = Modulo.query.filter(
            Modulo.activo.is_(False)
        ).count()

        # ------------------------------------------------------
        # ASIGNACIONES DE MÓDULOS
        # ------------------------------------------------------

        total_asignaciones_modulos = EmpresaModulo.query.count()

        modulos_empresa_activos = EmpresaModulo.query.filter(
            EmpresaModulo.activo.is_(True)
        ).count()

        # ------------------------------------------------------
        # EMPRESAS CON MÓDULOS ACTIVOS
        # ------------------------------------------------------

        empresas_con_modulos = db.session.query(
            func.count(
                func.distinct(
                    EmpresaModulo.empresa_id
                )
            )
        ).filter(
            EmpresaModulo.activo.is_(True)
        ).scalar() or 0

        # ------------------------------------------------------
        # EMPRESAS SIN MÓDULOS ACTIVOS
        # ------------------------------------------------------

        empresas_sin_modulos = max(
            empresas_activas - empresas_con_modulos,
            0
        )

        # ------------------------------------------------------
        # USUARIOS POR EMPRESA
        #
        # Sirve para mostrar una pequeña actividad/resumen
        # administrativo del sistema.
        # ------------------------------------------------------

        usuarios_por_empresa = db.session.query(
            Empresa.nombre,
            func.count(Usuario.id).label("cantidad")
        ).outerjoin(
            Usuario,
            Usuario.empresa_id == Empresa.id
        ).group_by(
            Empresa.id,
            Empresa.nombre
        ).order_by(
            func.count(Usuario.id).desc()
        ).limit(8).all()

        # ------------------------------------------------------
        # MÓDULOS MÁS ASIGNADOS
        # ------------------------------------------------------

        modulos_mas_asignados = db.session.query(
            Modulo.nombre,
            func.count(EmpresaModulo.id).label("cantidad")
        ).join(
            EmpresaModulo,
            EmpresaModulo.modulo_id == Modulo.id
        ).filter(
            EmpresaModulo.activo.is_(True)
        ).group_by(
            Modulo.id,
            Modulo.nombre
        ).order_by(
            func.count(EmpresaModulo.id).desc()
        ).limit(8).all()

        # ------------------------------------------------------
        # EMPRESAS RECIENTES
        # ------------------------------------------------------

        empresas_recientes = Empresa.query.order_by(
            Empresa.id.desc()
        ).limit(5).all()

        # ------------------------------------------------------
        # RENDER SUPERADMIN
        # ------------------------------------------------------

        return render_template(
            "dashboard/index.html",
            usuario=current_user,

            es_dashboard_superadmin=True,

            total_empresas=total_empresas,
            empresas_activas=empresas_activas,
            empresas_inactivas=empresas_inactivas,

            total_usuarios=total_usuarios,
            usuarios_activos=usuarios_activos,
            usuarios_inactivos=usuarios_inactivos,

            total_modulos=total_modulos,
            modulos_activos=modulos_activos,
            modulos_inactivos=modulos_inactivos,

            total_asignaciones_modulos=total_asignaciones_modulos,
            modulos_empresa_activos=modulos_empresa_activos,

            empresas_con_modulos=empresas_con_modulos,
            empresas_sin_modulos=empresas_sin_modulos,

            usuarios_por_empresa=usuarios_por_empresa,
            modulos_mas_asignados=modulos_mas_asignados,
            empresas_recientes=empresas_recientes
        )

    # ==========================================================
    # DASHBOARD DE EMPRESA
    #
    # DESDE AQUÍ HACIA ABAJO CONSERVAMOS LA LÓGICA QUE YA
    # TENÍAS FUNCIONANDO.
    # ==========================================================

    # ==========================================================
    # FECHA ACTUAL
    # ==========================================================

    hoy = datetime.now().date()

    inicio_dia = datetime.combine(
        hoy,
        time.min
    )

    fin_dia = datetime.combine(
        hoy,
        time.max
    )

    # ==========================================================
    # VENTAS DEL DÍA
    # ==========================================================

    ventas_hoy = db.session.query(
        func.coalesce(func.sum(Venta.total), 0)
    ).filter(
        Venta.empresa_id == current_user.empresa_id,
        Venta.fecha >= inicio_dia,
        Venta.fecha <= fin_dia,
        Venta.estado == "completada"
    ).scalar()

    # ==========================================================
    # CANTIDAD DE PRODUCTOS
    # ==========================================================

    total_productos = Producto.query.filter(
        Producto.empresa_id == current_user.empresa_id,
        Producto.activo.is_(True)
    ).count()

    # ==========================================================
    # CANTIDAD DE CLIENTES
    # ==========================================================

    total_clientes = Cliente.query.filter(
        Cliente.empresa_id == current_user.empresa_id,
        Cliente.activo.is_(True)
    ).count()

    # ==========================================================
    # PRODUCTOS CON STOCK BAJO
    # ==========================================================

    productos_stock_bajo = Producto.query.filter(
        Producto.empresa_id == current_user.empresa_id,
        Producto.activo.is_(True),
        Producto.stock <= Producto.stock_minimo
    ).count()

    # ==========================================================
    # VENTAS DE LOS ÚLTIMOS 7 DÍAS
    # ==========================================================

    ventas_7_dias = []

    for i in range(6, -1, -1):

        fecha = hoy - timedelta(days=i)

        inicio = datetime.combine(
            fecha,
            time.min
        )

        fin = datetime.combine(
            fecha,
            time.max
        )

        total = db.session.query(
            func.coalesce(func.sum(Venta.total), 0)
        ).filter(
            Venta.empresa_id == current_user.empresa_id,
            Venta.fecha >= inicio,
            Venta.fecha <= fin,
            Venta.estado == "completada"
        ).scalar()

        ventas_7_dias.append({
            "fecha": fecha.strftime("%d/%m"),
            "total": float(total or 0)
        })

    # ==========================================================
    # PRODUCTOS MÁS VENDIDOS
    # ==========================================================

    productos_mas_vendidos = db.session.query(
        Producto.nombre,
        func.coalesce(
            func.sum(DetalleVenta.cantidad),
            0
        ).label("cantidad")
    ).join(
        DetalleVenta,
        DetalleVenta.producto_id == Producto.id
    ).join(
        Venta,
        Venta.id == DetalleVenta.venta_id
    ).filter(
        Producto.empresa_id == current_user.empresa_id,
        Venta.empresa_id == current_user.empresa_id,
        Venta.estado == "completada"
    ).group_by(
        Producto.id,
        Producto.nombre
    ).order_by(
        func.sum(DetalleVenta.cantidad).desc()
    ).limit(5).all()

    # ==========================================================
    # LISTA DE PRODUCTOS CON STOCK BAJO
    # ==========================================================

    lista_stock_bajo = Producto.query.filter(
        Producto.empresa_id == current_user.empresa_id,
        Producto.activo.is_(True),
        Producto.stock <= Producto.stock_minimo
    ).order_by(
        Producto.stock.asc()
    ).limit(5).all()

    # ==========================================================
    # ÚLTIMAS VENTAS
    # ==========================================================

    ultimas_ventas = Venta.query.filter(
        Venta.empresa_id == current_user.empresa_id
    ).order_by(
        Venta.fecha.desc()
    ).limit(10).all()

    # ==========================================================
    # RENDER DASHBOARD EMPRESA
    # ==========================================================

    return render_template(
        "dashboard/index.html",
        usuario=current_user,

        es_dashboard_superadmin=False,

        ventas_hoy=ventas_hoy,
        total_productos=total_productos,
        total_clientes=total_clientes,
        productos_stock_bajo=productos_stock_bajo,
        ventas_7_dias=ventas_7_dias,
        productos_mas_vendidos=productos_mas_vendidos,
        lista_stock_bajo=lista_stock_bajo,
        ultimas_ventas=ultimas_ventas
    )
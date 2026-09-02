from decimal import Decimal

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
from apps.models import (
    Producto,
    Cliente,
    Venta,
    DetalleVenta,
    Caja,
    MovimientoCaja
)


# ==========================================================
# BLUEPRINT
# ==========================================================

facturacion_bp = Blueprint(
    "facturacion",
    __name__,
    url_prefix="/facturacion"
)


# ==========================================================
# HISTORIAL DE FACTURAS
# ==========================================================

@facturacion_bp.route("/")
@login_required
def index():

    ventas = db.session.execute(
        db.select(Venta)
        .where(
            Venta.empresa_id == current_user.empresa_id
        )
        .order_by(
            Venta.fecha.desc()
        )
    ).scalars().all()

    return render_template(
        "facturacion/index.html",
        ventas=ventas
    )


# ==========================================================
# PUNTO DE VENTA
# ==========================================================

@facturacion_bp.route("/pos", methods=["GET", "POST"])
@login_required
def pos():

    if request.method == "POST":

        cliente_id = request.form.get("cliente_id")

        metodo_pago = (
            request.form.get("metodo_pago")
            or "efectivo"
        ).strip().lower()

        productos_ids = request.form.getlist("producto_id")
        cantidades = request.form.getlist("cantidad")
        tipos_venta = request.form.getlist("tipo_venta")

        if not productos_ids:

            flash(
                "Debes agregar al menos un producto.",
                "danger"
            )

            return redirect(
                url_for("facturacion.pos")
            )

        try:

            # ==================================================
            # CAJA ABIERTA
            # ==================================================

            caja = db.session.execute(
                db.select(Caja)
                .where(
                    Caja.empresa_id == current_user.empresa_id,
                    Caja.estado == "abierta"
                )
                .order_by(
                    Caja.id.desc()
                )
            ).scalars().first()

            if caja is None:

                raise ValueError(
                    "No hay una caja abierta. "
                    "Debes abrir la caja antes de registrar ventas."
                )

            # ==================================================
            # MÉTODO DE PAGO
            # ==================================================

            metodos_validos = (
                "efectivo",
                "nequi",
                "daviplata",
                "transferencia",
                "tarjeta",
                "credito"
            )

            if metodo_pago not in metodos_validos:
                metodo_pago = "efectivo"

            # ==================================================
            # CLIENTE
            # ==================================================

            cliente = None

            if cliente_id:

                try:
                    cliente_id_int = int(cliente_id)
                except (ValueError, TypeError):
                    raise ValueError(
                        "El cliente seleccionado no es válido."
                    )

                cliente = db.session.execute(
                    db.select(Cliente)
                    .where(
                        Cliente.id == cliente_id_int,
                        Cliente.empresa_id == current_user.empresa_id
                    )
                ).scalar_one_or_none()

                if cliente is None:

                    raise ValueError(
                        "El cliente seleccionado no existe."
                    )

            # ==================================================
            # CREAR VENTA
            # ==================================================

            venta = Venta(
                empresa_id=current_user.empresa_id,
                cliente_id=cliente.id if cliente else None,
                usuario_id=current_user.id,
                metodo_pago=metodo_pago,
                subtotal=Decimal("0.00"),
                descuento=Decimal("0.00"),
                total=Decimal("0.00"),
                estado="completada"
            )

            db.session.add(venta)

            # Necesitamos que la venta tenga ID
            # para usarlo en los movimientos de caja.

            db.session.flush()

            subtotal_total = Decimal("0.00")

            # ==================================================
            # PROCESAR PRODUCTOS
            # ==================================================

            for indice, producto_id in enumerate(productos_ids):

                # ------------------------------------------------
                # PRODUCTO
                # ------------------------------------------------

                try:
                    producto_id_int = int(producto_id)
                except (ValueError, TypeError):

                    raise ValueError(
                        "Uno de los productos seleccionados "
                        "no es válido."
                    )

                producto = db.session.execute(
                    db.select(Producto)
                    .where(
                        Producto.id == producto_id_int,
                        Producto.empresa_id == current_user.empresa_id
                    )
                ).scalar_one_or_none()

                if producto is None:

                    raise ValueError(
                        "Uno de los productos seleccionados "
                        "no existe."
                    )

                # ------------------------------------------------
                # CANTIDAD
                # ------------------------------------------------

                if indice >= len(cantidades):

                    raise ValueError(
                        f"Falta la cantidad de {producto.nombre}."
                    )

                try:

                    cantidad = int(
                        cantidades[indice]
                    )

                except (ValueError, TypeError):

                    raise ValueError(
                        f"La cantidad de {producto.nombre} "
                        "no es válida."
                    )

                if cantidad <= 0:

                    raise ValueError(
                        "La cantidad debe ser mayor que cero."
                    )

                # ------------------------------------------------
                # TIPO DE VENTA
                # ------------------------------------------------

                if indice < len(tipos_venta):

                    tipo_venta = (
                        tipos_venta[indice]
                        or "unidad"
                    ).strip().lower()

                else:

                    tipo_venta = "unidad"

                if tipo_venta not in (
                    "unidad",
                    "caja"
                ):

                    tipo_venta = "unidad"

                # ==================================================
                # VENTA POR UNIDAD
                # ==================================================

                if tipo_venta == "unidad":

                    unidades_a_descontar = cantidad

                    precio = Decimal(
                        str(
                            producto.precio_venta or 0
                        )
                    )

                    if precio <= 0:

                        raise ValueError(
                            f"{producto.nombre} no tiene "
                            "precio de venta por unidad."
                        )

                    stock_actual = int(
                        producto.stock or 0
                    )

                    if stock_actual < unidades_a_descontar:

                        raise ValueError(
                            f"Stock insuficiente para "
                            f"{producto.nombre}. "
                            f"Disponible: "
                            f"{stock_actual} unidades."
                        )

                # ==================================================
                # VENTA POR CAJA
                # ==================================================

                else:

                    if not producto.maneja_cajas:

                        raise ValueError(
                            f"{producto.nombre} no está "
                            "configurado para venderse por caja."
                        )

                    if not producto.unidades_por_caja:

                        raise ValueError(
                            f"{producto.nombre} no tiene "
                            "configurada la cantidad de "
                            "unidades por caja."
                        )

                    if producto.unidades_por_caja <= 0:

                        raise ValueError(
                            f"{producto.nombre} tiene una "
                            "configuración inválida."
                        )

                    unidades_a_descontar = (
                        cantidad
                        * producto.unidades_por_caja
                    )

                    precio = Decimal(
                        str(
                            producto.precio_venta_caja or 0
                        )
                    )

                    if precio <= 0:

                        raise ValueError(
                            f"{producto.nombre} no tiene "
                            "precio de venta por caja."
                        )

                    stock_actual = int(
                        producto.stock or 0
                    )

                    if stock_actual < unidades_a_descontar:

                        cajas_disponibles = (
                            stock_actual
                            // producto.unidades_por_caja
                        )

                        raise ValueError(
                            f"Stock insuficiente para "
                            f"{producto.nombre}. "
                            f"Solo hay "
                            f"{cajas_disponibles} "
                            "cajas completas disponibles."
                        )

                # ==================================================
                # SUBTOTAL
                # ==================================================

                subtotal = (
                    precio
                    * Decimal(cantidad)
                )

                # ==================================================
                # DETALLE
                # ==================================================

                detalle = DetalleVenta(
                    venta_id=venta.id,
                    producto_id=producto.id,
                    cantidad=cantidad,
                    tipo_venta=tipo_venta,
                    precio_unitario=precio,
                    subtotal=subtotal
                )

                db.session.add(detalle)

                # ==================================================
                # DESCONTAR INVENTARIO
                # ==================================================

                producto.stock = (
                    int(producto.stock or 0)
                    - unidades_a_descontar
                )

                subtotal_total += subtotal

            # ==================================================
            # TOTALES
            # ==================================================

            venta.subtotal = subtotal_total
            venta.descuento = Decimal("0.00")
            venta.total = subtotal_total

            # ==================================================
            # MOVIMIENTO DE CAJA
            # ==================================================

            movimiento = MovimientoCaja(
                caja_id=caja.id,
                empresa_id=current_user.empresa_id,
                usuario_id=current_user.id,
                tipo="ingreso",
                concepto=f"Venta #{venta.id}",
                descripcion=(
                    f"Factura #{venta.id} - Venta de mercancía"
                ),
                valor=subtotal_total,
                metodo_pago=metodo_pago,
                referencia=f"VENTA-{venta.id}"
            )

            db.session.add(movimiento)

            # ==================================================
            # ACTUALIZAR CAJA
            # ==================================================

            saldo_actual = Decimal(
                str(
                    caja.saldo_actual or 0
                )
            )

            caja.saldo_actual = (
                saldo_actual
                + subtotal_total
            )

            # ==================================================
            # GUARDAR
            # ==================================================

            db.session.commit()

            flash(
                f"Factura #{venta.id} creada correctamente.",
                "success"
            )

            return redirect(
                url_for(
                    "facturacion.detalle",
                    id=venta.id
                )
            )

        except (ValueError, TypeError) as error:

            db.session.rollback()

            flash(
                str(error),
                "danger"
            )

            return redirect(
                url_for("facturacion.pos")
            )

        except Exception as error:

            db.session.rollback()

            print(
                "ERROR EN FACTURACIÓN:",
                repr(error)
            )

            flash(
                "Ocurrió un error al crear la factura.",
                "danger"
            )

            return redirect(
                url_for("facturacion.pos")
            )

    # ==========================================================
    # PRODUCTOS
    # ==========================================================

    productos = db.session.execute(
        db.select(Producto)
        .where(
            Producto.empresa_id == current_user.empresa_id,
            Producto.activo == True
        )
        .order_by(
            Producto.nombre
        )
    ).scalars().all()

    # ==========================================================
    # CLIENTES
    # ==========================================================

    clientes = db.session.execute(
        db.select(Cliente)
        .where(
            Cliente.empresa_id == current_user.empresa_id,
            Cliente.activo == True
        )
        .order_by(
            Cliente.nombre
        )
    ).scalars().all()

    # ==========================================================
    # CAJA ABIERTA
    # ==========================================================

    caja_abierta = db.session.execute(
        db.select(Caja)
        .where(
            Caja.empresa_id == current_user.empresa_id,
            Caja.estado == "abierta"
        )
        .order_by(
            Caja.id.desc()
        )
    ).scalars().first()

    return render_template(
        "facturacion/pos.html",
        productos=productos,
        clientes=clientes,
        caja_abierta=caja_abierta
    )


# ==========================================================
# VER FACTURA
# ==========================================================

@facturacion_bp.route("/<int:id>")
@login_required
def detalle(id):

    venta = db.session.execute(
        db.select(Venta)
        .where(
            Venta.id == id,
            Venta.empresa_id == current_user.empresa_id
        )
    ).scalar_one_or_none()

    if venta is None:

        flash(
            "La factura no existe.",
            "danger"
        )

        return redirect(
            url_for("facturacion.index")
        )

    # ==========================================================
    # AGRUPAR PRODUCTOS
    # ==========================================================

    productos_factura = {}

    for detalle in venta.detalles:

        producto_id = detalle.producto_id

        if producto_id not in productos_factura:

            productos_factura[producto_id] = {

                "producto": detalle.producto,

                "cajas": 0,

                "unidades": 0,

                "precio_caja": Decimal("0.00"),

                "precio_unidad": Decimal("0.00"),

                "total": Decimal("0.00")
            }

        item = productos_factura[producto_id]

        # ------------------------------------------------------
        # CAJAS
        # ------------------------------------------------------

        if detalle.tipo_venta == "caja":

            item["cajas"] += detalle.cantidad

            item["precio_caja"] = Decimal(
                str(
                    detalle.precio_unitario or 0
                )
            )

        # ------------------------------------------------------
        # UNIDADES
        # ------------------------------------------------------

        else:

            item["unidades"] += detalle.cantidad

            item["precio_unidad"] = Decimal(
                str(
                    detalle.precio_unitario or 0
                )
            )

        # ------------------------------------------------------
        # TOTAL
        # ------------------------------------------------------

        item["total"] += Decimal(
            str(
                detalle.subtotal or 0
            )
        )

    productos_factura = list(
        productos_factura.values()
    )

    # ==========================================================
    # EMPRESA
    # ==========================================================

    empresa = current_user.empresa

    return render_template(
        "facturacion/detalle.html",
        venta=venta,
        productos_factura=productos_factura,
        empresa=empresa
    )


# ==========================================================
# ANULAR FACTURA
# ==========================================================

@facturacion_bp.route(
    "/<int:id>/anular",
    methods=["POST"]
)
@login_required
def anular(id):

    venta = db.session.execute(
        db.select(Venta)
        .where(
            Venta.id == id,
            Venta.empresa_id == current_user.empresa_id
        )
    ).scalar_one_or_none()

    if venta is None:

        flash(
            "La factura no existe.",
            "danger"
        )

        return redirect(
            url_for("facturacion.index")
        )

    # ==========================================================
    # YA ESTÁ ANULADA
    # ==========================================================

    if venta.estado == "anulada":

        flash(
            "Esta factura ya se encuentra anulada.",
            "warning"
        )

        return redirect(
            url_for(
                "facturacion.detalle",
                id=venta.id
            )
        )

    try:

        # ======================================================
        # DEVOLVER INVENTARIO
        # ======================================================

        for detalle in venta.detalles:

            producto = detalle.producto

            if producto is None:
                continue

            if detalle.tipo_venta == "caja":

                unidades = (
                    detalle.cantidad
                    * int(
                        producto.unidades_por_caja or 0
                    )
                )

            else:

                unidades = detalle.cantidad

            producto.stock = (
                int(producto.stock or 0)
                + unidades
            )

        # ======================================================
        # ANULAR
        # ======================================================

        venta.estado = "anulada"

        # ======================================================
        # REVERSAR CAJA
        # ======================================================

        movimiento_original = db.session.execute(
            db.select(MovimientoCaja)
            .where(
                MovimientoCaja.empresa_id == current_user.empresa_id,
                MovimientoCaja.referencia == f"VENTA-{venta.id}"
            )
        ).scalar_one_or_none()

        if movimiento_original:

            caja = db.session.execute(
                db.select(Caja)
                .where(
                    Caja.id == movimiento_original.caja_id,
                    Caja.empresa_id == current_user.empresa_id
                )
            ).scalar_one_or_none()

            if caja:

                saldo_actual = Decimal(
                    str(
                        caja.saldo_actual or 0
                    )
                )

                caja.saldo_actual = (
                    saldo_actual
                    - Decimal(
                        str(
                            venta.total or 0
                        )
                    )
                )

            movimiento_anulacion = MovimientoCaja(
                caja_id=movimiento_original.caja_id,
                empresa_id=current_user.empresa_id,
                usuario_id=current_user.id,
                tipo="egreso",
                concepto=f"Anulación factura #{venta.id}",
                descripcion=(
                    f"Reversión de factura #{venta.id}"
                ),
                valor=Decimal(
                    str(
                        venta.total or 0
                    )
                ),
                metodo_pago=venta.metodo_pago,
                referencia=f"ANULACION-{venta.id}"
            )

            db.session.add(
                movimiento_anulacion
            )

        db.session.commit()

        flash(
            f"Factura #{venta.id} anulada correctamente.",
            "success"
        )

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR AL ANULAR FACTURA:",
            repr(error)
        )

        flash(
            "No fue posible anular la factura.",
            "danger"
        )

    return redirect(
        url_for(
            "facturacion.detalle",
            id=venta.id
        )
    )
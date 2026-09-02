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
from apps.models import Caja, MovimientoCaja


# ==========================================================
# BLUEPRINT
# ==========================================================

caja_bp = Blueprint(
    "caja",
    __name__,
    url_prefix="/caja"
)


# ==========================================================
# CAJA PRINCIPAL
# ==========================================================

@caja_bp.route("/")
@login_required
def index():

    cajas = db.session.execute(
        db.select(Caja)
        .where(
            Caja.empresa_id == current_user.empresa_id
        )
        .order_by(
            Caja.id.desc()
        )
    ).scalars().all()

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
        "caja/index.html",
        cajas=cajas,
        caja_abierta=caja_abierta
    )


# ==========================================================
# ABRIR CAJA
# ==========================================================

@caja_bp.route("/abrir", methods=["GET", "POST"])
@login_required
def abrir():

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

    if caja_abierta:

        flash(
            f"Ya existe una caja abierta: {caja_abierta.nombre}.",
            "warning"
        )

        return redirect(
            url_for("facturacion.pos")
        )

    if request.method == "POST":

        nombre = (
            request.form.get("nombre")
            or "Caja principal"
        ).strip()

        saldo_inicial_raw = (
            request.form.get("saldo_inicial")
            or "0"
        ).strip()

        observaciones = (
            request.form.get("observaciones")
            or ""
        ).strip()

        try:

            saldo_inicial = Decimal(
                saldo_inicial_raw
            )

            if saldo_inicial < 0:

                raise ValueError(
                    "El saldo inicial no puede ser negativo."
                )

            caja = Caja(
                empresa_id=current_user.empresa_id,
                nombre=nombre,
                saldo_inicial=saldo_inicial,
                saldo_actual=saldo_inicial,
                estado="abierta",
                fecha_apertura=db.func.now(),
                usuario_apertura_id=current_user.id,
                observaciones=observaciones
            )

            db.session.add(caja)

            db.session.flush()

            # ==================================================
            # REGISTRAR SALDO INICIAL
            #
            # Se guarda como movimiento para tener historial,
            # pero NO será considerado una venta/ingreso del día.
            # ==================================================

            movimiento = MovimientoCaja(
                caja_id=caja.id,
                empresa_id=current_user.empresa_id,
                usuario_id=current_user.id,
                tipo="ingreso",
                concepto="Apertura de caja",
                descripcion="Saldo inicial de caja",
                valor=saldo_inicial,
                metodo_pago="Efectivo",
                referencia=f"APERTURA-{caja.id}"
            )

            db.session.add(movimiento)

            db.session.commit()

            flash(
                f"Caja '{caja.nombre}' abierta correctamente.",
                "success"
            )

            return redirect(
                url_for("facturacion.pos")
            )

        except (ValueError, TypeError) as error:

            db.session.rollback()

            flash(
                str(error),
                "danger"
            )

        except Exception as error:

            db.session.rollback()

            print(
                "ERROR AL ABRIR CAJA:",
                repr(error)
            )

            flash(
                "Ocurrió un error al abrir la caja.",
                "danger"
            )

    return render_template(
        "caja/abrir.html"
    )


# ==========================================================
# MOVIMIENTO MANUAL
# ==========================================================

@caja_bp.route("/movimiento", methods=["GET", "POST"])
@login_required
def movimiento():

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

        flash(
            "No hay una caja abierta.",
            "warning"
        )

        return redirect(
            url_for("caja.index")
        )

    if request.method == "POST":

        tipo = (
            request.form.get("tipo")
            or ""
        ).strip().lower()

        concepto = (
            request.form.get("concepto")
            or ""
        ).strip()

        descripcion = (
            request.form.get("descripcion")
            or ""
        ).strip()

        metodo_pago = (
            request.form.get("metodo_pago")
            or "Efectivo"
        ).strip()

        referencia = (
            request.form.get("referencia")
            or ""
        ).strip()

        valor_raw = (
            request.form.get("valor")
            or "0"
        ).strip()

        try:

            valor = Decimal(
                valor_raw
            )

            if valor <= 0:

                raise ValueError(
                    "El valor debe ser mayor que cero."
                )

            if tipo not in (
                "ingreso",
                "egreso"
            ):

                raise ValueError(
                    "El tipo de movimiento no es válido."
                )

            if not concepto:

                raise ValueError(
                    "Debes indicar el concepto."
                )

            saldo_actual = Decimal(
                str(
                    caja.saldo_actual or 0
                )
            )

            # ==================================================
            # EGRESO
            # ==================================================

            if tipo == "egreso":

                if saldo_actual < valor:

                    raise ValueError(
                        "La caja no tiene saldo suficiente "
                        "para realizar este egreso."
                    )

                caja.saldo_actual = (
                    saldo_actual - valor
                )

            # ==================================================
            # INGRESO
            # ==================================================

            else:

                caja.saldo_actual = (
                    saldo_actual + valor
                )

            movimiento = MovimientoCaja(
                caja_id=caja.id,
                empresa_id=current_user.empresa_id,
                usuario_id=current_user.id,
                tipo=tipo,
                concepto=concepto,
                descripcion=descripcion,
                valor=valor,
                metodo_pago=metodo_pago,
                referencia=referencia
            )

            db.session.add(
                movimiento
            )

            db.session.commit()

            flash(
                "Movimiento registrado correctamente.",
                "success"
            )

            return redirect(
                url_for("caja.index")
            )

        except (ValueError, TypeError) as error:

            db.session.rollback()

            flash(
                str(error),
                "danger"
            )

        except Exception as error:

            db.session.rollback()

            print(
                "ERROR EN MOVIMIENTO DE CAJA:",
                repr(error)
            )

            flash(
                "Ocurrió un error al registrar el movimiento.",
                "danger"
            )

    return render_template(
        "caja/movimiento.html",
        caja=caja
    )


# ==========================================================
# MOVIMIENTOS DE UNA CAJA
# ==========================================================

@caja_bp.route("/<int:id>/movimientos")
@login_required
def movimientos(id):

    caja = db.session.execute(
        db.select(Caja)
        .where(
            Caja.id == id,
            Caja.empresa_id == current_user.empresa_id
        )
    ).scalar_one_or_none()

    if caja is None:

        flash(
            "La caja no existe.",
            "danger"
        )

        return redirect(
            url_for("caja.index")
        )

    movimientos = db.session.execute(
        db.select(MovimientoCaja)
        .where(
            MovimientoCaja.caja_id == caja.id,
            MovimientoCaja.empresa_id == current_user.empresa_id
        )
        .order_by(
            MovimientoCaja.fecha.desc()
        )
    ).scalars().all()

    return render_template(
        "caja/movimientos.html",
        caja=caja,
        movimientos=movimientos
    )


# ==========================================================
# CERRAR CAJA
# ==========================================================

@caja_bp.route(
    "/<int:id>/cerrar",
    methods=["GET", "POST"]
)
@login_required
def cerrar(id):

    # ==========================================================
    # BUSCAR CAJA
    # ==========================================================

    caja = db.session.execute(
        db.select(Caja)
        .where(
            Caja.id == id,
            Caja.empresa_id == current_user.empresa_id
        )
    ).scalar_one_or_none()

    if caja is None:

        flash(
            "La caja no existe.",
            "danger"
        )

        return redirect(
            url_for("caja.index")
        )

    # ==========================================================
    # VERIFICAR ESTADO
    # ==========================================================

    if caja.estado != "abierta":

        flash(
            "Esta caja ya está cerrada.",
            "warning"
        )

        return redirect(
            url_for("caja.index")
        )

    # ==========================================================
    # OBTENER MOVIMIENTOS
    # ==========================================================

    movimientos = db.session.execute(
        db.select(MovimientoCaja)
        .where(
            MovimientoCaja.caja_id == caja.id,
            MovimientoCaja.empresa_id == current_user.empresa_id
        )
        .order_by(
            MovimientoCaja.fecha.asc()
        )
    ).scalars().all()

    # ==========================================================
    # TOTALES
    # ==========================================================

    total_ventas = Decimal("0.00")

    total_ingresos_manuales = Decimal("0.00")

    total_egresos = Decimal("0.00")

    # ==========================================================
    # RECORRER MOVIMIENTOS
    # ==========================================================

    for movimiento in movimientos:

        valor = Decimal(
            str(
                movimiento.valor or 0
            )
        )

        referencia = (
            movimiento.referencia
            or ""
        ).strip().upper()

        concepto = (
            movimiento.concepto
            or ""
        ).strip().lower()

        # ======================================================
        # APERTURA
        #
        # NO se cuenta como ingreso del día.
        # ======================================================

        if (
            referencia.startswith("APERTURA-")
            or concepto == "apertura de caja"
        ):

            continue

        # ======================================================
        # VENTA
        # ======================================================

        if (
            movimiento.tipo == "ingreso"
            and referencia.startswith("VENTA-")
        ):

            total_ventas += valor

        # ======================================================
        # INGRESO MANUAL
        # ======================================================

        elif movimiento.tipo == "ingreso":

            total_ingresos_manuales += valor

        # ======================================================
        # EGRESO
        # ======================================================

        elif movimiento.tipo == "egreso":

            total_egresos += valor

    # ==========================================================
    # DINERO GENERADO SEGÚN MOVIMIENTOS
    #
    # NO incluye el saldo inicial.
    # ==========================================================

    generado_por_movimientos = (
        total_ventas
        + total_ingresos_manuales
        - total_egresos
    )

    # ==========================================================
    # SALDO ACTUAL
    #
    # Este sí incluye el saldo inicial.
    # ==========================================================

    saldo_actual = Decimal(
        str(
            caja.saldo_actual or 0
        )
    )

    # ==========================================================
    # VALOR INICIAL REGISTRADO
    # ==========================================================

    saldo_inicial = Decimal(
        str(
            caja.saldo_inicial or 0
        )
    )

    # ==========================================================
    # DINERO GENERADO SEGÚN SALDO DE CAJA
    #
    # Ejemplo:
    #
    # Inicial: 100.000
    # Actual:  450.000
    #
    # Generado: 350.000
    # ==========================================================

    generado_por_saldo = (
        saldo_actual
        - saldo_inicial
    )

    # ==========================================================
    # POST
    # ==========================================================

    if request.method == "POST":

        # ------------------------------------------------------
        # VALOR INICIAL QUE EL USUARIO DICE QUE DEJÓ
        # ------------------------------------------------------

        valor_inicial_raw = (
            request.form.get(
                "valor_inicial"
            )
            or ""
        ).strip()

        # ------------------------------------------------------
        # DINERO CONTADO
        # ------------------------------------------------------

        dinero_contado_raw = (
            request.form.get(
                "dinero_contado"
            )
            or ""
        ).strip()

        # ------------------------------------------------------
        # OBSERVACIONES
        # ------------------------------------------------------

        observaciones = (
            request.form.get(
                "observaciones"
            )
            or ""
        ).strip()

        try:

            # ==================================================
            # VALIDACIONES
            # ==================================================

            if not valor_inicial_raw:

                raise ValueError(
                    "Debes ingresar el valor con el que "
                    "abriste la caja."
                )

            if not dinero_contado_raw:

                raise ValueError(
                    "Debes ingresar el dinero que tienes "
                    "físicamente al cerrar."
                )

            valor_inicial = Decimal(
                valor_inicial_raw
            )

            dinero_contado = Decimal(
                dinero_contado_raw
            )

            if valor_inicial < 0:

                raise ValueError(
                    "El valor inicial no puede ser negativo."
                )

            if dinero_contado < 0:

                raise ValueError(
                    "El dinero contado no puede ser negativo."
                )

            # ==================================================
            # COMPROBAR QUE EL VALOR INICIAL SEA CORRECTO
            # ==================================================

            if valor_inicial != saldo_inicial:

                raise ValueError(
                    "El valor ingresado como saldo inicial "
                    f"(${valor_inicial:,.2f}) no coincide con "
                    "el valor con el que realmente se abrió "
                    f"la caja (${saldo_inicial:,.2f})."
                )

            # ==================================================
            # RESTAR EL SALDO INICIAL
            # ==================================================

            saldo_generado = (
                dinero_contado
                - valor_inicial
            )

            # ==================================================
            # DIFERENCIA
            #
            # Comparamos lo generado físicamente contra
            # los movimientos registrados.
            # ==========================================================

            diferencia = (
                saldo_generado
                - generado_por_movimientos
            )

            # ==================================================
            # GUARDAR RESULTADO
            # ==================================================

            caja.saldo_actual = dinero_contado

            caja.estado = "cerrada"

            caja.fecha_cierre = db.func.now()

            caja.usuario_cierre_id = current_user.id

            if observaciones:

                caja.observaciones = observaciones

            db.session.commit()

            # ==================================================
            # MENSAJE
            # ==================================================

            if diferencia > 0:

                mensaje_diferencia = (
                    f"Sobrante: ${diferencia:,.2f}."
                )

            elif diferencia < 0:

                mensaje_diferencia = (
                    f"Faltante: ${abs(diferencia):,.2f}."
                )

            else:

                mensaje_diferencia = (
                    "La caja cuadra exactamente."
                )

            flash(
                "Caja cerrada correctamente. "
                f"Saldo inicial: ${valor_inicial:,.2f}. "
                f"Dinero generado: ${saldo_generado:,.2f}. "
                f"{mensaje_diferencia}",
                "success"
            )

            return redirect(
                url_for("caja.index")
            )

        except (ValueError, TypeError) as error:

            db.session.rollback()

            flash(
                str(error),
                "danger"
            )

        except Exception as error:

            db.session.rollback()

            print(
                "ERROR AL CERRAR CAJA:",
                repr(error)
            )

            flash(
                "Ocurrió un error al cerrar la caja.",
                "danger"
            )

    # ==========================================================
    # RENDER
    # ==========================================================

    return render_template(
        "caja/cerrar.html",
        caja=caja,
        movimientos=movimientos,
        saldo_inicial=saldo_inicial,
        saldo_actual=saldo_actual,
        total_ventas=total_ventas,
        total_ingresos_manuales=total_ingresos_manuales,
        total_egresos=total_egresos,
        generado_por_movimientos=generado_por_movimientos,
        generado_por_saldo=generado_por_saldo
    )
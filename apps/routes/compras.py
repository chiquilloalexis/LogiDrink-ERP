
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from apps import db
from apps.models import Compra, DetalleCompra, Producto, Proveedor


compras_bp = Blueprint(
    "compras",
    __name__,
    url_prefix="/compras"
)


@compras_bp.route("/")
@login_required
def index():
    compras = (
        Compra.query
        .filter_by(empresa_id=current_user.empresa_id)
        .order_by(Compra.fecha.desc())
        .all()
    )

    return render_template(
        "compras/index.html",
        compras=compras
    )


@compras_bp.route("/nueva", methods=["GET", "POST"])
@login_required
def nueva():
    proveedores = (
        Proveedor.query
        .filter_by(
            empresa_id=current_user.empresa_id,
            activo=True
        )
        .order_by(Proveedor.nombre.asc())
        .all()
    )

    productos = (
        Producto.query
        .filter_by(
            empresa_id=current_user.empresa_id,
            activo=True
        )
        .order_by(Producto.nombre.asc())
        .all()
    )

    if request.method == "POST":

        proveedor_id = request.form.get("proveedor_id", type=int)
        numero = request.form.get("numero", "").strip()
        observaciones = request.form.get("observaciones", "").strip()

        if not proveedor_id:
            flash("Debes seleccionar un proveedor.", "error")
            return render_template(
                "compras/nueva.html",
                proveedores=proveedores,
                productos=productos
            )

        proveedor = Proveedor.query.filter_by(
            id=proveedor_id,
            empresa_id=current_user.empresa_id
        ).first()

        if not proveedor:
            flash("El proveedor seleccionado no es válido.", "error")
            return render_template(
                "compras/nueva.html",
                proveedores=proveedores,
                productos=productos
            )

        if not numero:
            numero = f"COMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        compra = Compra(
            empresa_id=current_user.empresa_id,
            proveedor_id=proveedor.id,
            usuario_id=current_user.id,
            numero=numero,
            fecha=datetime.utcnow(),
            subtotal=0,
            descuento=0,
            total=0,
            estado="Completada",
            observaciones=observaciones
        )

        db.session.add(compra)
        db.session.flush()

        productos_ids = request.form.getlist("producto_id[]")
        tipos = request.form.getlist("tipo_compra[]")
        cantidades = request.form.getlist("cantidad[]")
        precios = request.form.getlist("precio_unitario[]")

        subtotal_general = 0
        detalles_creados = 0

        try:

            for i, producto_id in enumerate(productos_ids):

                if not producto_id:
                    continue

                producto = Producto.query.filter_by(
                    id=int(producto_id),
                    empresa_id=current_user.empresa_id,
                    activo=True
                ).first()

                if not producto:
                    continue

                tipo_compra = (
                    tipos[i]
                    if i < len(tipos) and tipos[i]
                    else "unidad"
                )

                cantidad = int(
                    float(cantidades[i])
                ) if i < len(cantidades) and cantidades[i] else 0

                precio_unitario = float(
                    precios[i]
                ) if i < len(precios) and precios[i] else 0

                if cantidad <= 0:
                    continue

                if precio_unitario < 0:
                    precio_unitario = 0

                if tipo_compra not in ("unidad", "caja"):
                    tipo_compra = "unidad"

                unidades_por_caja = producto.unidades_por_caja or 1

                if tipo_compra == "caja":
                    unidades_ingresadas = (
                        cantidad * unidades_por_caja
                    )
                else:
                    unidades_ingresadas = cantidad

                subtotal = (
                    cantidad * precio_unitario
                )

                detalle = DetalleCompra(
                    compra_id=compra.id,
                    producto_id=producto.id,
                    tipo_compra=tipo_compra,
                    cantidad=cantidad,
                    unidades_por_caja=unidades_por_caja,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal,
                    unidades_ingresadas=unidades_ingresadas
                )

                db.session.add(detalle)

                # Actualizar inventario.
                producto.stock += unidades_ingresadas

                # Actualizar precio de compra.
                if tipo_compra == "caja":
                    producto.precio_compra_caja = precio_unitario

                else:
                    producto.precio_compra = precio_unitario

                subtotal_general += subtotal
                detalles_creados += 1

            if detalles_creados == 0:
                db.session.rollback()

                flash(
                    "Debes agregar al menos un producto válido.",
                    "error"
                )

                return render_template(
                    "compras/nueva.html",
                    proveedores=proveedores,
                    productos=productos
                )

            compra.subtotal = subtotal_general
            compra.total = subtotal_general - (
                compra.descuento or 0
            )

            db.session.commit()

            flash(
                f"Compra {compra.numero} registrada correctamente.",
                "success"
            )

            return redirect(
                url_for(
                    "compras.detalle",
                    id=compra.id
                )
            )

        except Exception as e:
            db.session.rollback()

            flash(
                f"Error al registrar la compra: {str(e)}",
                "error"
            )

    return render_template(
        "compras/nueva.html",
        proveedores=proveedores,
        productos=productos
    )


@compras_bp.route("/<int:id>")
@login_required
def detalle(id):

    compra = Compra.query.filter_by(
        id=id,
        empresa_id=current_user.empresa_id
    ).first_or_404()

    return render_template(
        "compras/detalle.html",
        compra=compra
    )


@compras_bp.route("/<int:id>/anular", methods=["POST"])
@login_required
def anular(id):

    compra = Compra.query.filter_by(
        id=id,
        empresa_id=current_user.empresa_id
    ).first_or_404()

    if compra.estado == "Anulada":
        flash("Esta compra ya está anulada.", "error")
        return redirect(
            url_for(
                "compras.detalle",
                id=compra.id
            )
        )

    try:

        # Revertir las cantidades ingresadas al inventario.
        for detalle in compra.detalles:

            producto = Producto.query.filter_by(
                id=detalle.producto_id,
                empresa_id=current_user.empresa_id
            ).first()

            if producto:
                producto.stock -= detalle.unidades_ingresadas

                # Nunca permitir stock negativo.
                if producto.stock < 0:
                    producto.stock = 0

        compra.estado = "Anulada"

        db.session.commit()

        flash(
            f"Compra {compra.numero} anulada correctamente.",
            "success"
        )

    except Exception as e:
        db.session.rollback()

        flash(
            f"Error al anular la compra: {str(e)}",
            "error"
        )

    return redirect(
        url_for(
            "compras.detalle",
            id=compra.id
        )
    )

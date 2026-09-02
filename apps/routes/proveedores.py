from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from apps import db
from apps.models.proveedor import Proveedor


proveedores_bp = Blueprint(
    "proveedores",
    __name__,
    url_prefix="/proveedores"
)


@proveedores_bp.route("/")
@login_required
def index():

    proveedores = (
        Proveedor.query
        .filter_by(
            empresa_id=current_user.empresa_id,
            activo=True
        )
        .order_by(Proveedor.nombre.asc())
        .all()
    )

    total_proveedores = len(proveedores)

    return render_template(
        "proveedores/index.html",
        proveedores=proveedores,
        total_proveedores=total_proveedores
    )


@proveedores_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        nit = request.form.get("nit", "").strip()
        telefono = request.form.get("telefono", "").strip()
        direccion = request.form.get("direccion", "").strip()
        correo = request.form.get("correo", "").strip()
        contacto = request.form.get("contacto", "").strip()

        if not nombre:
            flash(
                "El nombre del proveedor es obligatorio.",
                "error"
            )

            return render_template(
                "proveedores/nuevo.html"
            )

        proveedor = Proveedor(
            empresa_id=current_user.empresa_id,
            nombre=nombre,
            nit=nit or None,
            telefono=telefono or None,
            direccion=direccion or None,
            correo=correo or None,
            contacto=contacto or None,
            activo=True
        )

        db.session.add(proveedor)
        db.session.commit()

        flash(
            "Proveedor creado correctamente.",
            "success"
        )

        return redirect(
            url_for("proveedores.index")
        )

    return render_template(
        "proveedores/nuevo.html"
    )


@proveedores_bp.route(
    "/editar/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def editar(id):

    proveedor = (
        Proveedor.query
        .filter_by(
            id=id,
            empresa_id=current_user.empresa_id
        )
        .first_or_404()
    )

    if request.method == "POST":

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        if not nombre:

            flash(
                "El nombre del proveedor es obligatorio.",
                "error"
            )

            return render_template(
                "proveedores/editar.html",
                proveedor=proveedor
            )

        proveedor.nombre = nombre

        proveedor.nit = (
            request.form.get("nit", "").strip()
            or None
        )

        proveedor.telefono = (
            request.form.get("telefono", "").strip()
            or None
        )

        proveedor.direccion = (
            request.form.get("direccion", "").strip()
            or None
        )

        proveedor.correo = (
            request.form.get("correo", "").strip()
            or None
        )

        proveedor.contacto = (
            request.form.get("contacto", "").strip()
            or None
        )

        db.session.commit()

        flash(
            "Proveedor actualizado correctamente.",
            "success"
        )

        return redirect(
            url_for("proveedores.index")
        )

    return render_template(
        "proveedores/editar.html",
        proveedor=proveedor
    )


@proveedores_bp.route(
    "/desactivar/<int:id>",
    methods=["POST"]
)
@login_required
def desactivar(id):

    proveedor = (
        Proveedor.query
        .filter_by(
            id=id,
            empresa_id=current_user.empresa_id
        )
        .first_or_404()
    )

    proveedor.activo = False

    db.session.commit()

    flash(
        "Proveedor desactivado correctamente.",
        "success"
    )

    return redirect(
        url_for("proveedores.index")
    )
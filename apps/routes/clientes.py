from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from apps import db
from apps.models import Cliente


clientes_bp = Blueprint(
    "clientes",
    __name__,
    url_prefix="/clientes"
)


@clientes_bp.route("/")
@login_required
def index():

    clientes = Cliente.query.filter_by(
        empresa_id=current_user.empresa_id
    ).order_by(Cliente.id.desc()).all()

    return render_template(
        "clientes/index.html",
        clientes=clientes
    )


@clientes_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        documento = request.form.get("documento", "").strip()
        telefono = request.form.get("telefono", "").strip()
        direccion = request.form.get("direccion", "").strip()
        email = request.form.get("email", "").strip()

        if not nombre:
            flash("El nombre del cliente es obligatorio.", "danger")
            return render_template("clientes/nuevo.html")

        if not documento:
            flash("El documento del cliente es obligatorio.", "danger")
            return render_template("clientes/nuevo.html")

        cliente = Cliente(
            empresa_id=current_user.empresa_id,
            nombre=nombre,
            documento=documento,
            telefono=telefono,
            direccion=direccion,
            email=email
        )

        db.session.add(cliente)
        db.session.commit()

        flash("Cliente registrado correctamente.", "success")

        return redirect(url_for("clientes.index"))

    return render_template("clientes/nuevo.html")


@clientes_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):

    cliente = db.session.get(Cliente, id)

    if cliente is None or cliente.empresa_id != current_user.empresa_id:
        flash("Cliente no encontrado.", "danger")
        return redirect(url_for("clientes.index"))

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        documento = request.form.get("documento", "").strip()
        telefono = request.form.get("telefono", "").strip()
        direccion = request.form.get("direccion", "").strip()
        email = request.form.get("email", "").strip()

        if not nombre:
            flash("El nombre del cliente es obligatorio.", "danger")
            return render_template(
                "clientes/editar.html",
                cliente=cliente
            )

        if not documento:
            flash("El documento del cliente es obligatorio.", "danger")
            return render_template(
                "clientes/editar.html",
                cliente=cliente
            )

        cliente.nombre = nombre
        cliente.documento = documento
        cliente.telefono = telefono
        cliente.direccion = direccion
        cliente.email = email

        db.session.commit()

        flash("Cliente actualizado correctamente.", "success")

        return redirect(url_for("clientes.index"))

    return render_template(
        "clientes/editar.html",
        cliente=cliente
    )


@clientes_bp.route("/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar(id):

    cliente = db.session.get(Cliente, id)

    if cliente is None or cliente.empresa_id != current_user.empresa_id:
        flash("Cliente no encontrado.", "danger")
        return redirect(url_for("clientes.index"))

    cliente.activo = False

    db.session.commit()

    flash("Cliente desactivado correctamente.", "success")

    return redirect(url_for("clientes.index"))
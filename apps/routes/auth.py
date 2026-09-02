from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_user,
    logout_user,
    login_required
)

from apps import db
from apps.models import Usuario


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


# ==========================================================
# LOGIN
# ==========================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = (
            request.form.get(
                "email",
                ""
            )
            .strip()
            .lower()
        )

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            flash(
                "Debes ingresar el correo y la contraseña.",
                "danger"
            )

            return render_template(
                "auth/login.html"
            )

        usuario = db.session.execute(
            db.select(Usuario)
            .where(
                Usuario.email == email
            )
        ).scalar_one_or_none()

        if usuario is None:

            flash(
                "Correo o contraseña incorrectos.",
                "danger"
            )

            return render_template(
                "auth/login.html"
            )

        if not usuario.activo:

            flash(
                "Este usuario está desactivado.",
                "danger"
            )

            return render_template(
                "auth/login.html"
            )

        if not usuario.verificar_password(
            password
        ):

            flash(
                "Correo o contraseña incorrectos.",
                "danger"
            )

            return render_template(
                "auth/login.html"
            )

        # ==================================================
        # VALIDACIÓN EMPRESA
        # ==================================================

        if not usuario.es_superadmin:

            if usuario.empresa is None:

                flash(
                    "El usuario no tiene una empresa asignada.",
                    "danger"
                )

                return render_template(
                    "auth/login.html"
                )

            if not usuario.empresa.activa:

                flash(
                    "La empresa está desactivada.",
                    "danger"
                )

                return render_template(
                    "auth/login.html"
                )

        # ==================================================
        # LOGIN
        # ==================================================

        login_user(usuario)

        return redirect(
            url_for(
                "dashboard.index"
            )
        )

    return render_template(
        "auth/login.html"
    )


# ==========================================================
# LOGOUT
# ==========================================================

@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "Sesión cerrada correctamente.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )
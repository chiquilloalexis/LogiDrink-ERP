from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response
)

from flask_login import (
    login_required,
    current_user
)

from apps import db
from apps.models import Empresa


configuracion_bp = Blueprint(
    "configuracion",
    __name__,
    url_prefix="/configuracion"
)


# ==========================================================
# CONFIGURACION
# ==========================================================

@configuracion_bp.route("/")
@login_required
def index():

    empresa = None

    if current_user.empresa_id:

        empresa = db.session.get(
            Empresa,
            current_user.empresa_id
        )

    return render_template(
        "configuracion/index.html",
        empresa=empresa,
        usuario=current_user
    )


# ==========================================================
# GUARDAR FOTO DE PERFIL
# ==========================================================

@configuracion_bp.route(
    "/foto",
    methods=["POST"]
)
@login_required
def guardar_foto():

    archivo = request.files.get("foto_perfil")

    if archivo is None:
        flash(
            "No se recibió ninguna imagen.",
            "danger"
        )

        return redirect(
            url_for("configuracion.index")
        )

    if not archivo.filename:
        flash(
            "Debes seleccionar una imagen.",
            "danger"
        )

        return redirect(
            url_for("configuracion.index")
        )

    # ------------------------------------------------------
    # TIPOS PERMITIDOS
    # ------------------------------------------------------

    tipos_permitidos = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif"
    }

    if archivo.mimetype not in tipos_permitidos:

        flash(
            "Solo se permiten imágenes JPG, PNG, WEBP o GIF.",
            "danger"
        )

        return redirect(
            url_for("configuracion.index")
        )

    # ------------------------------------------------------
    # LEER ARCHIVO
    # ------------------------------------------------------

    contenido = archivo.read()

    if not contenido:

        flash(
            "La imagen seleccionada está vacía.",
            "danger"
        )

        return redirect(
            url_for("configuracion.index")
        )

    # ------------------------------------------------------
    # LIMITE 5 MB
    # ------------------------------------------------------

    limite = 5 * 1024 * 1024

    if len(contenido) > limite:

        flash(
            "La imagen no puede superar los 5 MB.",
            "danger"
        )

        return redirect(
            url_for("configuracion.index")
        )

    # ------------------------------------------------------
    # GUARDAR FOTO EN EL USUARIO ACTUAL
    # ------------------------------------------------------

    current_user.foto_perfil = contenido
    current_user.foto_perfil_tipo = archivo.mimetype

    db.session.commit()

    flash(
        "Foto de perfil actualizada correctamente.",
        "success"
    )

    return redirect(
        url_for(
            "configuracion.index"
        )
    )


# ==========================================================
# MOSTRAR FOTO DE PERFIL
# ==========================================================

@configuracion_bp.route(
    "/foto/<int:id>"
)
@login_required
def foto(id):

    # ------------------------------------------------------
    # SEGURIDAD
    # Cada usuario solamente puede consultar su propia foto
    # ------------------------------------------------------

    if id != current_user.id:

        return Response(
            "Acceso denegado",
            status=403
        )

    # ------------------------------------------------------
    # VERIFICAR QUE EXISTA FOTO
    # ------------------------------------------------------

    if not current_user.foto_perfil:

        return Response(
            status=404
        )

    # ------------------------------------------------------
    # DEVOLVER IMAGEN
    # ------------------------------------------------------

    return Response(
        current_user.foto_perfil,
        mimetype=(
            current_user.foto_perfil_tipo
            or "image/jpeg"
        ),
        headers={
            "Cache-Control": (
                "no-cache, "
                "no-store, "
                "must-revalidate"
            ),
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


# ==========================================================
# GUARDAR CONFIGURACIÓN DE EMPRESA
# ==========================================================

@configuracion_bp.route(
    "/guardar",
    methods=["POST"]
)
@login_required
def guardar():

    # ------------------------------------------------------
    # SUPERADMIN
    # ------------------------------------------------------

    if not current_user.empresa_id:

        flash(
            "Tu usuario no está asociado a una empresa.",
            "warning"
        )

        return redirect(
            url_for("configuracion.index")
        )

    # ------------------------------------------------------
    # BUSCAR EMPRESA
    # ------------------------------------------------------

    empresa = db.session.get(
        Empresa,
        current_user.empresa_id
    )

    if empresa is None:

        flash(
            "No se encontró la empresa.",
            "danger"
        )

        return redirect(
            url_for("dashboard.index")
        )

    # ------------------------------------------------------
    # DATOS
    # ------------------------------------------------------

    nombre = request.form.get(
        "nombre",
        ""
    ).strip()

    nit = request.form.get(
        "nit",
        ""
    ).strip()

    direccion = request.form.get(
        "direccion",
        ""
    ).strip()

    telefono = request.form.get(
        "telefono",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    # ------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------

    if not nombre:

        flash(
            "El nombre de la empresa es obligatorio.",
            "danger"
        )

        return redirect(
            url_for("configuracion.index")
        )

    if not nit:

        flash(
            "El NIT de la empresa es obligatorio.",
            "danger"
        )

        return redirect(
            url_for("configuracion.index")
        )

    # ------------------------------------------------------
    # ACTUALIZAR
    # ------------------------------------------------------

    empresa.nombre = nombre
    empresa.nit = nit
    empresa.direccion = direccion or None
    empresa.telefono = telefono or None
    empresa.email = email or None

    db.session.commit()

    flash(
        "Configuración actualizada correctamente.",
        "success"
    )

    return redirect(
        url_for("configuracion.index")
    )
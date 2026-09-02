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
from apps.models import Usuario, Rol
from apps.utils.decoradores import verificar_permiso


usuarios_bp = Blueprint(
    "usuarios",
    __name__,
    url_prefix="/usuarios"
)


# ==========================================================
# ROLES PREDETERMINADOS
# ==========================================================

ROLES_PREDETERMINADOS = [
    "Administrador",
    "Cajero",
    "Vendedor",
    "Mesero",
    "Bodeguero"
]


def crear_roles_predeterminados():

    # ------------------------------------------------------
    # Esta función solo se ejecuta para usuarios que ya
    # tienen acceso al módulo de usuarios.
    # ------------------------------------------------------

    if not current_user.empresa_id:
        return

    cambios = False

    for nombre_rol in ROLES_PREDETERMINADOS:

        rol_existente = db.session.execute(
            db.select(Rol)
            .where(
                Rol.empresa_id == current_user.empresa_id,
                db.func.lower(Rol.nombre) == nombre_rol.lower()
            )
        ).scalar_one_or_none()

        if rol_existente is None:

            nuevo_rol = Rol(
                empresa_id=current_user.empresa_id,
                nombre=nombre_rol,
                activo=True
            )

            db.session.add(nuevo_rol)

            cambios = True

    if cambios:
        db.session.commit()


# ==========================================================
# LISTADO DE USUARIOS
# ==========================================================

@usuarios_bp.route("/")
@login_required
@verificar_permiso("usuarios", "ver")
def index():

    usuarios = db.session.execute(
        db.select(Usuario)
        .where(
            Usuario.empresa_id == current_user.empresa_id
        )
        .order_by(
            Usuario.nombre
        )
    ).scalars().all()

    return render_template(
        "usuarios/index.html",
        usuarios=usuarios
    )


# ==========================================================
# NUEVO USUARIO
# ==========================================================

@usuarios_bp.route(
    "/nuevo",
    methods=["GET", "POST"]
)
@login_required
@verificar_permiso("usuarios", "crear")
def nuevo():

    crear_roles_predeterminados()

    roles = db.session.execute(
        db.select(Rol)
        .where(
            Rol.empresa_id == current_user.empresa_id,
            Rol.activo.is_(True)
        )
        .order_by(
            Rol.nombre
        )
    ).scalars().all()

    if request.method == "POST":

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        rol_id = request.form.get(
            "rol_id"
        )

        # ==================================================
        # VALIDACIONES
        # ==================================================

        if not nombre:

            flash(
                "El nombre es obligatorio.",
                "danger"
            )

            return redirect(
                url_for("usuarios.nuevo")
            )

        if not email:

            flash(
                "El correo es obligatorio.",
                "danger"
            )

            return redirect(
                url_for("usuarios.nuevo")
            )

        if not password:

            flash(
                "La contraseña es obligatoria.",
                "danger"
            )

            return redirect(
                url_for("usuarios.nuevo")
            )

        if len(password) < 6:

            flash(
                "La contraseña debe tener al menos 6 caracteres.",
                "danger"
            )

            return redirect(
                url_for("usuarios.nuevo")
            )

        if not rol_id:

            flash(
                "Debes seleccionar un rol.",
                "danger"
            )

            return redirect(
                url_for("usuarios.nuevo")
            )

        try:

            rol_id = int(rol_id)

        except (ValueError, TypeError):

            flash(
                "El rol seleccionado no es válido.",
                "danger"
            )

            return redirect(
                url_for("usuarios.nuevo")
            )

        # ==================================================
        # VERIFICAR ROL
        # ==================================================

        rol = db.session.execute(
            db.select(Rol)
            .where(
                Rol.id == rol_id,
                Rol.empresa_id == current_user.empresa_id,
                Rol.activo.is_(True)
            )
        ).scalar_one_or_none()

        if rol is None:

            flash(
                "El rol seleccionado no pertenece a tu empresa.",
                "danger"
            )

            return redirect(
                url_for("usuarios.nuevo")
            )

        # ==================================================
        # VERIFICAR CORREO
        # ==================================================

        usuario_existente = db.session.execute(
            db.select(Usuario)
            .where(
                Usuario.email == email
            )
        ).scalar_one_or_none()

        if usuario_existente:

            flash(
                "Ya existe un usuario con ese correo.",
                "danger"
            )

            return redirect(
                url_for("usuarios.nuevo")
            )

        # ==================================================
        # CREAR USUARIO
        # ==================================================

        usuario = Usuario(
            empresa_id=current_user.empresa_id,
            nombre=nombre,
            email=email,
            rol_id=rol.id,
            activo=True
        )

        usuario.establecer_password(
            password
        )

        db.session.add(usuario)
        db.session.commit()

        flash(
            f"Usuario {nombre} creado correctamente "
            f"con el rol {rol.nombre}.",
            "success"
        )

        return redirect(
            url_for("usuarios.index")
        )

    return render_template(
        "usuarios/nuevo.html",
        roles=roles
    )


# ==========================================================
# EDITAR USUARIO
# ==========================================================

@usuarios_bp.route(
    "/editar/<int:id>",
    methods=["GET", "POST"]
)
@login_required
@verificar_permiso("usuarios", "editar")
def editar(id):

    crear_roles_predeterminados()

    usuario = db.session.execute(
        db.select(Usuario)
        .where(
            Usuario.id == id,
            Usuario.empresa_id == current_user.empresa_id
        )
    ).scalar_one_or_none()

    if usuario is None:

        flash(
            "El usuario no existe.",
            "danger"
        )

        return redirect(
            url_for("usuarios.index")
        )

    roles = db.session.execute(
        db.select(Rol)
        .where(
            Rol.empresa_id == current_user.empresa_id,
            Rol.activo.is_(True)
        )
        .order_by(
            Rol.nombre
        )
    ).scalars().all()

    if request.method == "POST":

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        rol_id = request.form.get(
            "rol_id"
        )

        password = request.form.get(
            "password",
            ""
        )

        # ==================================================
        # VALIDACIONES
        # ==================================================

        if not nombre:

            flash(
                "El nombre es obligatorio.",
                "danger"
            )

            return redirect(
                url_for(
                    "usuarios.editar",
                    id=id
                )
            )

        if not email:

            flash(
                "El correo es obligatorio.",
                "danger"
            )

            return redirect(
                url_for(
                    "usuarios.editar",
                    id=id
                )
            )

        try:

            rol_id = int(rol_id)

        except (ValueError, TypeError):

            flash(
                "El rol seleccionado no es válido.",
                "danger"
            )

            return redirect(
                url_for(
                    "usuarios.editar",
                    id=id
                )
            )

        # ==================================================
        # VERIFICAR ROL
        # ==================================================

        rol = db.session.execute(
            db.select(Rol)
            .where(
                Rol.id == rol_id,
                Rol.empresa_id == current_user.empresa_id,
                Rol.activo.is_(True)
            )
        ).scalar_one_or_none()

        if rol is None:

            flash(
                "El rol seleccionado no pertenece a tu empresa.",
                "danger"
            )

            return redirect(
                url_for(
                    "usuarios.editar",
                    id=id
                )
            )

        # ==================================================
        # VERIFICAR CORREO
        # ==================================================

        otro_usuario = db.session.execute(
            db.select(Usuario)
            .where(
                Usuario.email == email,
                Usuario.id != usuario.id
            )
        ).scalar_one_or_none()

        if otro_usuario:

            flash(
                "Ese correo ya está utilizado por otro usuario.",
                "danger"
            )

            return redirect(
                url_for(
                    "usuarios.editar",
                    id=id
                )
            )

        # ==================================================
        # ACTUALIZAR
        # ==================================================

        usuario.nombre = nombre
        usuario.email = email
        usuario.rol_id = rol.id

        # ==================================================
        # CAMBIAR CONTRASEÑA
        # ==================================================

        if password:

            if len(password) < 6:

                flash(
                    "La nueva contraseña debe tener al menos 6 caracteres.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "usuarios.editar",
                        id=id
                    )
                )

            usuario.establecer_password(
                password
            )

        db.session.commit()

        flash(
            "Usuario actualizado correctamente.",
            "success"
        )

        return redirect(
            url_for("usuarios.index")
        )

    return render_template(
        "usuarios/editar.html",
        usuario=usuario,
        roles=roles
    )


# ==========================================================
# ACTIVAR / DESACTIVAR
# ==========================================================

@usuarios_bp.route(
    "/activar/<int:id>",
    methods=["POST"]
)
@login_required
@verificar_permiso("usuarios", "editar")
def activar(id):

    usuario = db.session.execute(
        db.select(Usuario)
        .where(
            Usuario.id == id,
            Usuario.empresa_id == current_user.empresa_id
        )
    ).scalar_one_or_none()

    if usuario is None:

        flash(
            "El usuario no existe.",
            "danger"
        )

        return redirect(
            url_for("usuarios.index")
        )

    # ==================================================
    # EVITAR DESACTIVARSE A SÍ MISMO
    # ==================================================

    if usuario.id == current_user.id:

        flash(
            "No puedes desactivar tu propio usuario.",
            "warning"
        )

        return redirect(
            url_for("usuarios.index")
        )

    usuario.activo = not usuario.activo

    db.session.commit()

    if usuario.activo:

        flash(
            f"Usuario {usuario.nombre} activado correctamente.",
            "success"
        )

    else:

        flash(
            f"Usuario {usuario.nombre} desactivado correctamente.",
            "success"
        )

    return redirect(
        url_for("usuarios.index")
    )
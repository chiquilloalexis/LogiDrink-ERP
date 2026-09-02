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
    Rol,
    Permiso,
    EmpresaModulo
)
from apps.utils.decoradores import verificar_admin_empresa


roles_bp = Blueprint(
    "roles",
    __name__,
    url_prefix="/roles"
)


# ==========================================================
# OBTENER MÓDULOS ACTIVOS DE LA EMPRESA
# ==========================================================

def obtener_modulos_empresa():

    asignaciones = db.session.execute(
        db.select(EmpresaModulo)
        .where(
            EmpresaModulo.empresa_id == current_user.empresa_id,
            EmpresaModulo.activo.is_(True)
        )
        .order_by(
            EmpresaModulo.modulo_id
        )
    ).scalars().all()

    modulos = []

    for asignacion in asignaciones:

        if not asignacion.modulo:
            continue

        if not asignacion.modulo.activo:
            continue

        modulos.append(
            asignacion.modulo
        )

    return modulos


# ==========================================================
# LISTADO DE ROLES
# ==========================================================

@roles_bp.route("/")
@login_required
@verificar_admin_empresa
def index():

    roles = db.session.execute(
        db.select(Rol)
        .where(
            Rol.empresa_id == current_user.empresa_id
        )
        .order_by(
            Rol.nombre.asc()
        )
    ).scalars().all()

    return render_template(
        "roles/index.html",
        roles=roles
    )


# ==========================================================
# NUEVO ROL
# ==========================================================

@roles_bp.route(
    "/nuevo",
    methods=["GET", "POST"]
)
@login_required
@verificar_admin_empresa
def nuevo():

    modulos = obtener_modulos_empresa()

    if request.method == "POST":

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        descripcion = request.form.get(
            "descripcion",
            ""
        ).strip()

        if not nombre:

            flash(
                "El nombre del rol es obligatorio.",
                "danger"
            )

            return redirect(
                url_for("roles.nuevo")
            )

        # ==================================================
        # VERIFICAR NOMBRE DUPLICADO
        # ==================================================

        rol_existente = db.session.execute(
            db.select(Rol)
            .where(
                Rol.empresa_id == current_user.empresa_id,
                db.func.lower(Rol.nombre) == nombre.lower()
            )
        ).scalar_one_or_none()

        if rol_existente:

            flash(
                "Ya existe un rol con ese nombre.",
                "danger"
            )

            return redirect(
                url_for("roles.nuevo")
            )

        # ==================================================
        # CREAR ROL
        # ==================================================

        rol = Rol(
            empresa_id=current_user.empresa_id,
            nombre=nombre,
            descripcion=descripcion or None,
            activo=True
        )

        db.session.add(rol)

        db.session.flush()

        # ==================================================
        # CREAR PERMISOS
        # ==================================================

        for modulo in modulos:

            modulo_id = str(
                modulo.id
            )

            permiso = Permiso(
                rol_id=rol.id,
                modulo=modulo.nombre,
                ver=f"ver_{modulo_id}" in request.form,
                crear=f"crear_{modulo_id}" in request.form,
                editar=f"editar_{modulo_id}" in request.form,
                eliminar=f"eliminar_{modulo_id}" in request.form,
                reportes=f"reportes_{modulo_id}" in request.form
            )

            db.session.add(
                permiso
            )

        db.session.commit()

        flash(
            f"El rol {rol.nombre} fue creado correctamente.",
            "success"
        )

        return redirect(
            url_for("roles.index")
        )

    return render_template(
        "roles/nuevo.html",
        modulos=modulos
    )


# ==========================================================
# EDITAR ROL
# ==========================================================

@roles_bp.route(
    "/editar/<int:id>",
    methods=["GET", "POST"]
)
@login_required
@verificar_admin_empresa
def editar(id):

    rol = db.session.execute(
        db.select(Rol)
        .where(
            Rol.id == id,
            Rol.empresa_id == current_user.empresa_id
        )
    ).scalar_one_or_none()

    if rol is None:

        flash(
            "El rol no existe o no pertenece a tu empresa.",
            "danger"
        )

        return redirect(
            url_for("roles.index")
        )

    modulos = obtener_modulos_empresa()

    if request.method == "POST":

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        descripcion = request.form.get(
            "descripcion",
            ""
        ).strip()

        if not nombre:

            flash(
                "El nombre del rol es obligatorio.",
                "danger"
            )

            return redirect(
                url_for(
                    "roles.editar",
                    id=rol.id
                )
            )

        # ==================================================
        # VERIFICAR NOMBRE
        # ==================================================

        rol_existente = db.session.execute(
            db.select(Rol)
            .where(
                Rol.empresa_id == current_user.empresa_id,
                db.func.lower(Rol.nombre) == nombre.lower(),
                Rol.id != rol.id
            )
        ).scalar_one_or_none()

        if rol_existente:

            flash(
                "Ya existe otro rol con ese nombre.",
                "danger"
            )

            return redirect(
                url_for(
                    "roles.editar",
                    id=rol.id
                )
            )

        # ==================================================
        # ACTUALIZAR ROL
        # ==================================================

        rol.nombre = nombre
        rol.descripcion = descripcion or None

        # ==================================================
        # PERMISOS EXISTENTES
        # ==================================================

        permisos_existentes = {
            permiso.modulo.strip().lower(): permiso
            for permiso in rol.permisos
            if permiso.modulo
        }

        nombres_modulos_activos = set()

        # ==================================================
        # ACTUALIZAR PERMISOS
        # ==================================================

        for modulo in modulos:

            nombre_modulo = (
                modulo.nombre
                .strip()
                .lower()
            )

            nombres_modulos_activos.add(
                nombre_modulo
            )

            modulo_id = str(
                modulo.id
            )

            ver = (
                f"ver_{modulo_id}"
                in request.form
            )

            crear = (
                f"crear_{modulo_id}"
                in request.form
            )

            editar = (
                f"editar_{modulo_id}"
                in request.form
            )

            eliminar = (
                f"eliminar_{modulo_id}"
                in request.form
            )

            reportes = (
                f"reportes_{modulo_id}"
                in request.form
            )

            permiso = permisos_existentes.get(
                nombre_modulo
            )

            if permiso is None:

                permiso = Permiso(
                    rol_id=rol.id,
                    modulo=modulo.nombre
                )

                db.session.add(
                    permiso
                )

            permiso.ver = ver
            permiso.crear = crear
            permiso.editar = editar
            permiso.eliminar = eliminar
            permiso.reportes = reportes

        # ==================================================
        # DESACTIVAR PERMISOS DE MÓDULOS NO ACTIVOS
        # ==================================================

        for permiso in rol.permisos:

            if (
                permiso.modulo
                and permiso.modulo.strip().lower()
                not in nombres_modulos_activos
            ):

                permiso.ver = False
                permiso.crear = False
                permiso.editar = False
                permiso.eliminar = False
                permiso.reportes = False

        db.session.commit()

        flash(
            f"El rol {rol.nombre} fue actualizado correctamente.",
            "success"
        )

        return redirect(
            url_for("roles.index")
        )

    # ==================================================
    # MOSTRAR PERMISOS ACTUALES
    # ==================================================

    permisos = {
        permiso.modulo.strip().lower(): permiso
        for permiso in rol.permisos
        if permiso.modulo
    }

    return render_template(
        "roles/editar.html",
        rol=rol,
        modulos=modulos,
        permisos=permisos
    )


# ==========================================================
# ACTIVAR / DESACTIVAR ROL
# ==========================================================

@roles_bp.route(
    "/activar/<int:id>",
    methods=["POST"]
)
@login_required
@verificar_admin_empresa
def activar(id):

    rol = db.session.execute(
        db.select(Rol)
        .where(
            Rol.id == id,
            Rol.empresa_id == current_user.empresa_id
        )
    ).scalar_one_or_none()

    if rol is None:

        flash(
            "El rol no existe.",
            "danger"
        )

        return redirect(
            url_for("roles.index")
        )

    # ==================================================
    # NO DESACTIVAR SI TIENE USUARIOS
    # ==================================================

    if rol.activo:

        usuarios_asignados = len(
            rol.usuarios
        )

        if usuarios_asignados > 0:

            flash(
                "No puedes desactivar este rol porque "
                "tiene usuarios asignados.",
                "warning"
            )

            return redirect(
                url_for("roles.index")
            )

    rol.activo = not rol.activo

    db.session.commit()

    if rol.activo:

        flash(
            f"Rol {rol.nombre} activado correctamente.",
            "success"
        )

    else:

        flash(
            f"Rol {rol.nombre} desactivado correctamente.",
            "success"
        )

    return redirect(
        url_for("roles.index")
    )
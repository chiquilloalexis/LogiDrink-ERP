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
# ROLES PREDETERMINADOS
# ==========================================================

ROLES_PREDETERMINADOS = {
    "administrador",
    "admin",
    "cajero",
    "vendedor",
    "mesero",
    "bodeguero"
}


# ==========================================================
# PERMISOS PREDETERMINADOS
# ==========================================================

PERMISOS_PREDETERMINADOS = {

    "cajero": {
        "ventas": ["ver", "crear"],
        "facturación": ["ver", "crear"],
        "clientes": ["ver", "crear", "editar"],
        "caja": ["ver", "crear"],
    },

    "vendedor": {
        "ventas": ["ver", "crear"],
        "facturación": ["ver", "crear"],
        "clientes": ["ver", "crear", "editar"],
        "productos": ["ver"],
    },

    "mesero": {
        "ventas": ["ver", "crear"],
        "productos": ["ver"],
    },

    "bodeguero": {
        "inventario": ["ver", "crear", "editar"],
        "productos": ["ver", "crear", "editar"],
        "compras": ["ver", "crear", "editar"],
        "proveedores": ["ver", "crear", "editar"],
    }
}


# ==========================================================
# OBTENER MÓDULOS ACTIVOS DE LA EMPRESA
# ==========================================================

def obtener_modulos_empresa():

    if not current_user.empresa_id:
        return []

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
# NORMALIZAR NOMBRE
# ==========================================================

def normalizar_nombre(valor):

    if not valor:
        return ""

    return (
        valor
        .strip()
        .lower()
    )


# ==========================================================
# DETERMINAR SI ES ROL PREDETERMINADO
# ==========================================================

def es_rol_predeterminado(rol):

    return (
        normalizar_nombre(rol.nombre)
        in ROLES_PREDETERMINADOS
    )


# ==========================================================
# CREAR / ACTUALIZAR PERMISOS PREDETERMINADOS
# ==========================================================

def aplicar_permisos_predeterminados(rol, modulos):

    nombre_rol = normalizar_nombre(
        rol.nombre
    )

    permisos_existentes = {
        normalizar_nombre(permiso.modulo): permiso
        for permiso in rol.permisos
        if permiso.modulo
    }

    if nombre_rol in ("administrador", "admin"):

        permisos_por_modulo = {}

        for modulo in modulos:

            nombre_modulo = normalizar_nombre(
                modulo.nombre
            )

            permisos_por_modulo[
                nombre_modulo
            ] = [
                "ver",
                "crear",
                "editar",
                "eliminar",
                "reportes"
            ]

    else:

        permisos_por_modulo = (
            PERMISOS_PREDETERMINADOS.get(
                nombre_rol,
                {}
            )
        )

    for modulo in modulos:

        nombre_modulo = normalizar_nombre(
            modulo.nombre
        )

        acciones = permisos_por_modulo.get(
            nombre_modulo,
            []
        )

        permiso = permisos_existentes.get(
            nombre_modulo
        )

        if permiso is None:

            permiso = Permiso(
                rol_id=rol.id,
                modulo=modulo.nombre,
                ver=False,
                crear=False,
                editar=False,
                eliminar=False,
                reportes=False
            )

            db.session.add(
                permiso
            )

        # --------------------------------------------------
        # SOLO APLICAR AUTOMATICAMENTE A ROLES PREDETERMINADOS
        # --------------------------------------------------

        permiso.ver = "ver" in acciones
        permiso.crear = "crear" in acciones
        permiso.editar = "editar" in acciones
        permiso.eliminar = "eliminar" in acciones
        permiso.reportes = "reportes" in acciones


# ==========================================================
# SINCRONIZAR ADMINISTRADOR
# ==========================================================

def sincronizar_administradores_empresa():

    if not current_user.empresa_id:
        return

    modulos = obtener_modulos_empresa()

    roles = db.session.execute(
        db.select(Rol)
        .where(
            Rol.empresa_id == current_user.empresa_id
        )
    ).scalars().all()

    for rol in roles:

        nombre = normalizar_nombre(
            rol.nombre
        )

        if nombre in (
            "administrador",
            "admin"
        ):

            aplicar_permisos_predeterminados(
                rol,
                modulos
            )

    db.session.commit()


# ==========================================================
# LISTADO DE ROLES
# ==========================================================

@roles_bp.route("/")
@login_required
@verificar_admin_empresa
def index():

    # ------------------------------------------------------
    # ASEGURAR PERMISOS DE ROLES PREDETERMINADOS
    # ------------------------------------------------------

    modulos = obtener_modulos_empresa()

    roles = db.session.execute(
        db.select(Rol)
        .where(
            Rol.empresa_id == current_user.empresa_id
        )
        .order_by(
            Rol.nombre.asc()
        )
    ).scalars().all()

    for rol in roles:

        if es_rol_predeterminado(rol):

            aplicar_permisos_predeterminados(
                rol,
                modulos
            )

    db.session.commit()

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

        rol = Rol(
            empresa_id=current_user.empresa_id,
            nombre=nombre,
            descripcion=descripcion or None,
            activo=True
        )

        db.session.add(rol)

        db.session.flush()

        # --------------------------------------------------
        # PERMISOS SELECCIONADOS MANUALMENTE
        # --------------------------------------------------

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

        rol.nombre = nombre
        rol.descripcion = descripcion or None

        permisos_existentes = {
            normalizar_nombre(permiso.modulo): permiso
            for permiso in rol.permisos
            if permiso.modulo
        }

        nombres_modulos_activos = set()

        for modulo in modulos:

            nombre_modulo = normalizar_nombre(
                modulo.nombre
            )

            nombres_modulos_activos.add(
                nombre_modulo
            )

            modulo_id = str(
                modulo.id
            )

            permiso = permisos_existentes.get(
                nombre_modulo
            )

            if permiso is None:

                permiso = Permiso(
                    rol_id=rol.id,
                    modulo=modulo.nombre,
                    ver=False,
                    crear=False,
                    editar=False,
                    eliminar=False,
                    reportes=False
                )

                db.session.add(
                    permiso
                )

            permiso.ver = (
                f"ver_{modulo_id}"
                in request.form
            )

            permiso.crear = (
                f"crear_{modulo_id}"
                in request.form
            )

            permiso.editar = (
                f"editar_{modulo_id}"
                in request.form
            )

            permiso.eliminar = (
                f"eliminar_{modulo_id}"
                in request.form
            )

            permiso.reportes = (
                f"reportes_{modulo_id}"
                in request.form
            )

        # --------------------------------------------------
        # DESACTIVAR PERMISOS DE MODULOS NO CONTRATADOS
        # --------------------------------------------------

        for permiso in rol.permisos:

            if (
                permiso.modulo
                and normalizar_nombre(
                    permiso.modulo
                ) not in nombres_modulos_activos
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

    permisos = {
        normalizar_nombre(permiso.modulo): permiso
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
# CLONAR ROL
# ==========================================================

@roles_bp.route(
    "/clonar/<int:id>",
    methods=["POST"]
)
@login_required
@verificar_admin_empresa
def clonar(id):

    rol_original = db.session.execute(
        db.select(Rol)
        .where(
            Rol.id == id,
            Rol.empresa_id == current_user.empresa_id
        )
    ).scalar_one_or_none()

    if rol_original is None:

        flash(
            "El rol que intentas clonar no existe.",
            "danger"
        )

        return redirect(
            url_for("roles.index")
        )

    nuevo_nombre = (
        f"{rol_original.nombre} copia"
    )

    contador = 2

    while True:

        existe = db.session.execute(
            db.select(Rol)
            .where(
                Rol.empresa_id == current_user.empresa_id,
                db.func.lower(Rol.nombre)
                == nuevo_nombre.lower()
            )
        ).scalar_one_or_none()

        if not existe:
            break

        nuevo_nombre = (
            f"{rol_original.nombre} copia {contador}"
        )

        contador += 1

    nuevo_rol = Rol(
        empresa_id=current_user.empresa_id,
        nombre=nuevo_nombre,
        descripcion=rol_original.descripcion,
        activo=True
    )

    db.session.add(
        nuevo_rol
    )

    db.session.flush()

    for permiso in rol_original.permisos:

        nuevo_permiso = Permiso(
            rol_id=nuevo_rol.id,
            modulo=permiso.modulo,
            ver=permiso.ver,
            crear=permiso.crear,
            editar=permiso.editar,
            eliminar=permiso.eliminar,
            reportes=permiso.reportes
        )

        db.session.add(
            nuevo_permiso
        )

    db.session.commit()

    flash(
        f"Rol clonado correctamente como '{nuevo_nombre}'.",
        "success"
    )

    return redirect(
        url_for("roles.editar", id=nuevo_rol.id)
    )


# ==========================================================
# ELIMINAR ROL
# ==========================================================

@roles_bp.route(
    "/eliminar/<int:id>",
    methods=["POST"]
)
@login_required
@verificar_admin_empresa
def eliminar(id):

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

    # ------------------------------------------------------
    # PROTEGER ROLES PREDETERMINADOS
    # ------------------------------------------------------

    if es_rol_predeterminado(rol):

        flash(
            "Los roles predeterminados del sistema no se pueden eliminar.",
            "warning"
        )

        return redirect(
            url_for("roles.index")
        )

    # ------------------------------------------------------
    # NO ELIMINAR SI TIENE USUARIOS
    # ------------------------------------------------------

    if len(rol.usuarios) > 0:

        flash(
            "No puedes eliminar este rol porque tiene usuarios asignados.",
            "warning"
        )

        return redirect(
            url_for("roles.index")
        )

    nombre = rol.nombre

    db.session.delete(
        rol
    )

    db.session.commit()

    flash(
        f"El rol '{nombre}' fue eliminado correctamente.",
        "success"
    )

    return redirect(
        url_for("roles.index")
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

    # ------------------------------------------------------
    # PROTEGER ADMINISTRADOR
    # ------------------------------------------------------

    if (
        es_rol_predeterminado(rol)
        and normalizar_nombre(rol.nombre)
        in ("administrador", "admin")
    ):

        flash(
            "El rol Administrador no puede ser desactivado.",
            "warning"
        )

        return redirect(
            url_for("roles.index")
        )

    # ------------------------------------------------------
    # NO DESACTIVAR SI TIENE USUARIOS
    # ------------------------------------------------------

    if rol.activo:

        if len(rol.usuarios) > 0:

            flash(
                "No puedes desactivar este rol porque tiene usuarios asignados.",
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

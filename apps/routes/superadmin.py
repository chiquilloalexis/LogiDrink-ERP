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
    Empresa,
    Usuario,
    Modulo,
    EmpresaModulo
)


superadmin_bp = Blueprint(
    "superadmin",
    __name__,
    url_prefix="/superadmin"
)


# ==========================================================
# VERIFICAR SUPERADMIN
# ==========================================================

def verificar_superadmin():

    return (
        current_user.is_authenticated
        and current_user.es_superadmin
    )


def exigir_superadmin():

    if not verificar_superadmin():
        return "Acceso denegado", 403


# ==========================================================
# DASHBOARD
# ==========================================================

@superadmin_bp.route("/")
@login_required
def index():

    acceso = exigir_superadmin()

    if acceso:
        return acceso

    empresas = Empresa.query.order_by(
        Empresa.id.desc()
    ).all()

    usuarios = Usuario.query.order_by(
        Usuario.id.desc()
    ).all()

    return render_template(
        "superadmin/index.html",
        empresas=empresas,
        usuarios=usuarios
    )


# ==========================================================
# EMPRESAS
# ==========================================================

@superadmin_bp.route("/empresas")
@login_required
def empresas():

    acceso = exigir_superadmin()

    if acceso:
        return acceso

    empresas = Empresa.query.order_by(
        Empresa.id.desc()
    ).all()

    return render_template(
        "superadmin/empresas.html",
        empresas=empresas
    )


# ==========================================================
# NUEVA EMPRESA
# ==========================================================

@superadmin_bp.route(
    "/empresas/nueva",
    methods=["GET", "POST"]
)
@login_required
def nueva_empresa():

    acceso = exigir_superadmin()

    if acceso:
        return acceso

    if request.method == "POST":

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

        # ==================================================
        # VALIDACIONES
        # ==================================================

        if not nombre:

            flash(
                "El nombre de la empresa es obligatorio.",
                "danger"
            )

            return redirect(
                url_for(
                    "superadmin.nueva_empresa"
                )
            )

        if not nit:

            flash(
                "El NIT de la empresa es obligatorio.",
                "danger"
            )

            return redirect(
                url_for(
                    "superadmin.nueva_empresa"
                )
            )

        empresa_existente = Empresa.query.filter_by(
            nit=nit
        ).first()

        if empresa_existente:

            flash(
                "Ya existe una empresa registrada con ese NIT.",
                "danger"
            )

            return redirect(
                url_for(
                    "superadmin.nueva_empresa"
                )
            )

        # ==================================================
        # CREAR EMPRESA
        # ==================================================

        empresa = Empresa(
            nombre=nombre,
            nit=nit,
            direccion=direccion or None,
            telefono=telefono or None,
            email=email or None,
            activa=True
        )

        db.session.add(empresa)

        db.session.commit()

        flash(
            f"La empresa {empresa.nombre} fue creada correctamente.",
            "success"
        )

        return redirect(
            url_for(
                "superadmin.empresas"
            )
        )

    return render_template(
        "superadmin/nueva_empresa.html"
    )


# ==========================================================
# EDITAR EMPRESA
# ==========================================================

@superadmin_bp.route(
    "/empresas/<int:id>/editar",
    methods=["GET", "POST"]
)
@login_required
def editar_empresa(id):

    acceso = exigir_superadmin()

    if acceso:
        return acceso

    empresa = db.session.get(
        Empresa,
        id
    )

    if not empresa:

        flash(
            "La empresa no existe.",
            "danger"
        )

        return redirect(
            url_for(
                "superadmin.empresas"
            )
        )

    if request.method == "POST":

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

        if not nombre or not nit:

            flash(
                "El nombre y el NIT son obligatorios.",
                "danger"
            )

            return redirect(
                url_for(
                    "superadmin.editar_empresa",
                    id=empresa.id
                )
            )

        empresa_con_mismo_nit = Empresa.query.filter(
            Empresa.nit == nit,
            Empresa.id != empresa.id
        ).first()

        if empresa_con_mismo_nit:

            flash(
                "Ese NIT ya pertenece a otra empresa.",
                "danger"
            )

            return redirect(
                url_for(
                    "superadmin.editar_empresa",
                    id=empresa.id
                )
            )

        empresa.nombre = nombre
        empresa.nit = nit
        empresa.direccion = direccion or None
        empresa.telefono = telefono or None
        empresa.email = email or None

        db.session.commit()

        flash(
            "Empresa actualizada correctamente.",
            "success"
        )

        return redirect(
            url_for(
                "superadmin.empresas"
            )
        )

    return render_template(
        "superadmin/editar_empresa.html",
        empresa=empresa
    )


# ==========================================================
# ACTIVAR / DESACTIVAR EMPRESA
# ==========================================================

@superadmin_bp.route(
    "/empresas/<int:id>/cambiar-estado",
    methods=["POST"]
)
@login_required
def cambiar_estado_empresa(id):

    acceso = exigir_superadmin()

    if acceso:
        return acceso

    empresa = db.session.get(
        Empresa,
        id
    )

    if not empresa:

        flash(
            "La empresa no existe.",
            "danger"
        )

        return redirect(
            url_for(
                "superadmin.empresas"
            )
        )

    empresa.activa = not empresa.activa

    db.session.commit()

    estado = (
        "activada"
        if empresa.activa
        else "desactivada"
    )

    flash(
        f"La empresa {empresa.nombre} fue {estado}.",
        "success"
    )

    return redirect(
        url_for(
            "superadmin.empresas"
        )
    )


# ==========================================================
# MÓDULOS
# ==========================================================

@superadmin_bp.route(
    "/modulos",
    methods=["GET", "POST"]
)
@login_required
def modulos():

    acceso = exigir_superadmin()

    if acceso:
        return acceso

    # ======================================================
    # EMPRESAS
    # ======================================================

    empresas = Empresa.query.order_by(
        Empresa.nombre.asc()
    ).all()

    # ======================================================
    # MÓDULOS ACTIVOS DEL SISTEMA
    # ======================================================

    modulos = Modulo.query.filter_by(
        activo=True
    ).order_by(
        Modulo.nombre.asc()
    ).all()

    # ======================================================
    # GUARDAR MÓDULOS
    # ======================================================

    if request.method == "POST":

        empresa_id = request.form.get(
            "empresa_id",
            type=int
        )

        if not empresa_id:

            flash(
                "Debes seleccionar una empresa.",
                "danger"
            )

            return redirect(
                url_for(
                    "superadmin.modulos"
                )
            )

        empresa = db.session.get(
            Empresa,
            empresa_id
        )

        if not empresa:

            flash(
                "La empresa seleccionada no existe.",
                "danger"
            )

            return redirect(
                url_for(
                    "superadmin.modulos"
                )
            )

        try:

            # ==============================================
            # RECORRER TODOS LOS MÓDULOS
            # ==============================================

            for modulo in modulos:

                nombre_campo = (
                    f"modulo_{modulo.id}"
                )

                activado = (
                    nombre_campo in request.form
                )

                asignacion = EmpresaModulo.query.filter_by(
                    empresa_id=empresa.id,
                    modulo_id=modulo.id
                ).first()

                # ==========================================
                # ACTUALIZAR ASIGNACIÓN EXISTENTE
                # ==========================================

                if asignacion:

                    asignacion.activo = activado

                # ==========================================
                # CREAR NUEVA ASIGNACIÓN
                # ==========================================

                elif activado:

                    nueva_asignacion = EmpresaModulo(
                        empresa_id=empresa.id,
                        modulo_id=modulo.id,
                        activo=True
                    )

                    db.session.add(
                        nueva_asignacion
                    )

            db.session.commit()

            flash(
                f"Los módulos de {empresa.nombre} "
                "fueron actualizados correctamente.",
                "success"
            )

        except Exception:

            db.session.rollback()

            flash(
                "Ocurrió un error al guardar los módulos.",
                "danger"
            )

        return redirect(
            url_for(
                "superadmin.modulos",
                empresa_id=empresa.id
            )
        )

    # ======================================================
    # EMPRESA SELECCIONADA
    # ======================================================

    empresa_id = request.args.get(
        "empresa_id",
        type=int
    )

    empresa_seleccionada = None

    modulos_empresa = {}

    if empresa_id:

        empresa_seleccionada = db.session.get(
            Empresa,
            empresa_id
        )

        if empresa_seleccionada:

            asignaciones = EmpresaModulo.query.filter_by(
                empresa_id=empresa_seleccionada.id
            ).all()

            modulos_empresa = {
                asignacion.modulo_id: asignacion.activo
                for asignacion in asignaciones
            }

    # ======================================================
    # MOSTRAR PÁGINA
    # ======================================================

    return render_template(
        "superadmin/modulos.html",
        empresas=empresas,
        modulos=modulos,
        empresa_seleccionada=empresa_seleccionada,
        modulos_empresa=modulos_empresa
    )


# ==========================================================
# USUARIOS DEL SISTEMA
# ==========================================================

@superadmin_bp.route("/usuarios")
@login_required
def usuarios():

    acceso = exigir_superadmin()

    if acceso:
        return acceso

    # ======================================================
    # TODOS LOS USUARIOS
    # ======================================================
    #
    # El SuperAdmin puede consultar los usuarios de todas
    # las empresas.
    #
    # No administra aquí los permisos internos.
    # Eso corresponde al Administrador de cada empresa.
    # ======================================================

    usuarios = Usuario.query.order_by(
        Usuario.id.desc()
    ).all()

    return render_template(
        "superadmin/usuarios.html",
        usuarios=usuarios
    )
from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user, login_required


# ============================================================
# VERIFICAR MODULO
# ============================================================

def verificar_modulo(nombre_modulo):
    """
    Protege una ruta comprobando que:

    1. El usuario esté autenticado.
    2. El usuario esté activo.
    3. El usuario tenga una empresa válida.
    4. La empresa tenga el módulo activo.

    El SuperAdmin tiene acceso global.
    """

    def decorador(func):

        @wraps(func)
        @login_required
        def wrapper(*args, **kwargs):

            # ------------------------------------------------
            # USUARIO ACTIVO
            # ------------------------------------------------

            if not current_user.activo:
                abort(403)

            # ------------------------------------------------
            # SUPERADMIN
            # ------------------------------------------------

            if current_user.es_super_administrador():
                return func(*args, **kwargs)

            # ------------------------------------------------
            # EMPRESA + MODULO
            # ------------------------------------------------

            if not current_user.empresa_tiene_modulo(
                nombre_modulo
            ):
                abort(403)

            return func(*args, **kwargs)

        return wrapper

    return decorador


# ============================================================
# VERIFICAR PERMISO
# ============================================================

def verificar_permiso(
    modulo,
    accion="ver"
):
    """
    Protege una ruta mediante un permiso concreto.

    Ejemplos:

        @verificar_permiso("inventario", "ver")

        @verificar_permiso("inventario", "crear")

        @verificar_permiso("ventas", "editar")

        @verificar_permiso("usuarios", "eliminar")
    """

    def decorador(func):

        @wraps(func)
        @login_required
        def wrapper(*args, **kwargs):

            # ------------------------------------------------
            # USUARIO ACTIVO
            # ------------------------------------------------

            if not current_user.activo:
                abort(403)

            # ------------------------------------------------
            # COMPROBAR PERMISO
            # ------------------------------------------------

            if not current_user.tiene_permiso(
                modulo,
                accion
            ):
                abort(403)

            return func(*args, **kwargs)

        return wrapper

    return decorador


# ============================================================
# ALIAS PROFESIONAL
# ============================================================

def requiere_permiso(
    modulo,
    accion="ver"
):
    """
    Alias de verificar_permiso().

    Permite utilizar una nomenclatura más clara:

        @requiere_permiso("ventas", "crear")
    """

    return verificar_permiso(
        modulo,
        accion
    )


# ============================================================
# VERIFICAR ADMINISTRADOR DE EMPRESA
# ============================================================

def verificar_admin_empresa(func):
    """
    Permite únicamente:

    - SuperAdmin
    - Administrador de empresa
    """

    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):

        if not current_user.activo:
            abort(403)

        if current_user.es_super_administrador():
            return func(*args, **kwargs)

        if current_user.es_admin_empresa():
            return func(*args, **kwargs)

        abort(403)

    return wrapper


# ============================================================
# VERIFICAR SUPERADMIN
# ============================================================

def verificar_superadmin(func):
    """
    Permite únicamente al SuperAdmin.
    """

    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):

        if not current_user.activo:
            abort(403)

        if not current_user.es_super_administrador():
            abort(403)

        return func(*args, **kwargs)

    return wrapper


# ============================================================
# VERIFICAR LICENCIA ACTIVA
# ============================================================

def verificar_licencia_activa():
    """
    Mantiene compatibilidad con las rutas existentes
    que actualmente utilizan:

        @verificar_licencia_activa()

    Si posteriormente se implementa un sistema completo
    de licencias/suscripciones, esta función será el punto
    central para hacerlo.
    """

    def decorador(func):

        @wraps(func)
        @login_required
        def wrapper(*args, **kwargs):

            if not current_user.is_authenticated:
                return redirect(
                    url_for("auth.login")
                )

            if not current_user.activo:
                abort(403)

            return func(*args, **kwargs)

        return wrapper

    return decorador
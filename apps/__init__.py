from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user

from config import Config


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    from apps.models import (
        Empresa,
        Usuario,
        Rol,
        Permiso,
        Cliente,
        Producto,
        Venta,
        DetalleVenta,
        MovimientoInventario,
        Proveedor,
        Compra,
        DetalleCompra,
        Caja,
        MovimientoCaja
    )

    @login_manager.user_loader
    def cargar_usuario(usuario_id):
        return db.session.get(Usuario, int(usuario_id))

    # ==========================================================
    # CAJA DISPONIBLE PARA TODAS LAS PLANTILLAS
    # ==========================================================

    @app.context_processor
    def datos_globales():

        caja_abierta = None

        if current_user.is_authenticated:

            # El superadministrador no necesariamente pertenece
            # a una empresa.
            if current_user.empresa_id:

                caja_abierta = db.session.execute(
                    db.select(Caja)
                    .where(
                        Caja.empresa_id == current_user.empresa_id,
                        Caja.estado == "abierta"
                    )
                    .order_by(
                        Caja.id.desc()
                    )
                ).scalars().first()

        return {
            "caja_abierta": caja_abierta
        }

    # ==========================================================
    # AUTENTICACIÓN
    # ==========================================================

    from apps.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    # ==========================================================
    # DASHBOARD
    # ==========================================================

    from apps.routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    # ==========================================================
    # CLIENTES
    # ==========================================================

    from apps.routes.clientes import clientes_bp
    app.register_blueprint(clientes_bp)

    # ==========================================================
    # PRODUCTOS
    # ==========================================================

    from apps.routes.productos import productos_bp
    app.register_blueprint(productos_bp)

    # ==========================================================
    # INVENTARIO
    # ==========================================================

    from apps.routes.inventario import inventario_bp
    app.register_blueprint(inventario_bp)

    # ==========================================================
    # FACTURACIÓN
    # ==========================================================

    from apps.routes.facturacion import facturacion_bp
    app.register_blueprint(facturacion_bp)

    # ==========================================================
    # PROVEEDORES
    # ==========================================================

    from apps.routes.proveedores import proveedores_bp
    app.register_blueprint(proveedores_bp)

    # ==========================================================
    # COMPRAS
    # ==========================================================

    from apps.routes.compras import compras_bp
    app.register_blueprint(compras_bp)

    # ==========================================================
    # CAJA
    # ==========================================================

    from apps.routes.caja import caja_bp
    app.register_blueprint(caja_bp)

    # ==========================================================
    # REPORTES
    # ==========================================================

    from apps.routes.reportes import reportes_bp
    app.register_blueprint(reportes_bp)

    # ==========================================================
    # USUARIOS
    # ==========================================================

    from apps.routes.usuarios import usuarios_bp
    app.register_blueprint(usuarios_bp)

    # ==========================================================
    # CONFIGURACIÓN
    # ==========================================================

    from apps.routes.configuracion import configuracion_bp
    app.register_blueprint(configuracion_bp)

    # ==========================================================
    # SUPERADMINISTRADOR
    # ==========================================================

    from apps.routes.superadmin import superadmin_bp
    app.register_blueprint(superadmin_bp)

    # ==========================================================
    # ROLES Y PERMISOS
    # ==========================================================

    from apps.routes.roles import roles_bp
    app.register_blueprint(roles_bp)

    # ==========================================================
    # INICIO
    # ==========================================================

    @app.route("/")
    def inicio():
        return "LogiDrink ERP funcionando correctamente"

    return app
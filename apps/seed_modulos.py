from apps import create_app, db
from apps.models import Modulo


MODULOS = [
    {
        "nombre": "Dashboard",
        "descripcion": "Panel principal con estadísticas y resumen del sistema."
    },
    {
        "nombre": "Ventas",
        "descripcion": "Punto de venta y gestión de ventas."
    },
    {
        "nombre": "Facturación",
        "descripcion": "Facturación, facturas y documentos de venta."
    },
    {
        "nombre": "Inventario",
        "descripcion": "Control de productos, existencias, cajas y unidades."
    },
    {
        "nombre": "Productos",
        "descripcion": "Administración de productos y precios."
    },
    {
        "nombre": "Compras",
        "descripcion": "Gestión de compras y entradas de mercancía."
    },
    {
        "nombre": "Clientes",
        "descripcion": "Administración de clientes."
    },
    {
        "nombre": "Proveedores",
        "descripcion": "Administración de proveedores."
    },
    {
        "nombre": "Caja",
        "descripcion": "Control de caja, ingresos, egresos y movimientos."
    },
    {
        "nombre": "Usuarios",
        "descripcion": "Administración de usuarios y accesos."
    },
    {
        "nombre": "Roles y permisos",
        "descripcion": "Administración de roles y permisos de usuarios."
    },
    {
        "nombre": "Reportes",
        "descripcion": "Reportes y estadísticas del sistema."
    },
    {
        "nombre": "Configuración",
        "descripcion": "Configuración general de la empresa."
    }
]


def crear_modulos():

    print("\n========================================")
    print("   CREANDO MÓDULOS DEL SISTEMA")
    print("========================================\n")

    creados = 0
    existentes = 0

    for datos in MODULOS:

        modulo = db.session.execute(
            db.select(Modulo)
            .where(
                Modulo.nombre == datos["nombre"]
            )
        ).scalar_one_or_none()

        if modulo is None:

            modulo = Modulo(
                nombre=datos["nombre"],
                descripcion=datos["descripcion"],
                activo=True
            )

            db.session.add(modulo)

            creados += 1

            print(
                f"[CREADO] {datos['nombre']}"
            )

        else:

            existentes += 1

            if not modulo.descripcion:
                modulo.descripcion = datos["descripcion"]

            modulo.activo = True

            print(
                f"[EXISTE] {datos['nombre']}"
            )

    db.session.commit()

    print("\n========================================")
    print("   PROCESO TERMINADO")
    print("========================================")
    print(f"Módulos creados: {creados}")
    print(f"Módulos existentes: {existentes}")
    print(f"Total de módulos: {len(MODULOS)}")
    print("========================================\n")


if __name__ == "__main__":

    app = create_app()

    with app.app_context():
        crear_modulos()
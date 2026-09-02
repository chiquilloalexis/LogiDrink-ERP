from apps import create_app, db
from apps.models import Empresa, Usuario, Rol


app = create_app()

with app.app_context():

    # Buscar o crear empresa
    empresa = Empresa.query.filter_by(nit="900000000-1").first()

    if not empresa:
        empresa = Empresa(
            nombre="LogiDrink",
            nit="900000000-1",
            direccion="Valledupar",
            telefono="3000000000",
            email="admin@logidrink.com",
            activa=True
        )

        db.session.add(empresa)
        db.session.flush()

        print("Empresa creada.")
    else:
        print("La empresa ya existe.")

    # Buscar o crear rol administrador
    rol = Rol.query.filter_by(
        empresa_id=empresa.id,
        nombre="Administrador"
    ).first()

    if not rol:
        rol = Rol(
            empresa_id=empresa.id,
            nombre="Administrador",
            descripcion="Administrador general del sistema",
            activo=True
        )

        db.session.add(rol)
        db.session.flush()

        print("Rol Administrador creado.")
    else:
        print("El rol Administrador ya existe.")

    # Buscar o crear usuario administrador
    usuario = Usuario.query.filter_by(
        email="admin@logidrink.com"
    ).first()

    if not usuario:

        usuario = Usuario(
            empresa_id=empresa.id,
            rol_id=rol.id,
            nombre="Administrador",
            email="admin@logidrink.com",
            activo=True
        )

        usuario.establecer_password("Admin12345")

        db.session.add(usuario)

        print("Usuario administrador creado.")
    else:
        print("El usuario administrador ya existe.")

    db.session.commit()

    print("")
    print("====================================")
    print(" USUARIO ADMINISTRADOR")
    print("====================================")
    print("Correo: admin@logidrink.com")
    print("Contraseña: Admin12345")
    print("====================================")
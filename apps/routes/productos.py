from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response
)

from flask_login import login_required, current_user

from apps import db
from apps.models import Producto


productos_bp = Blueprint(
    "productos",
    __name__,
    url_prefix="/productos"
)


# ==========================================
# LISTADO DE PRODUCTOS
# ==========================================

@productos_bp.route("/")
@login_required
def index():

    busqueda = request.args.get(
        "buscar",
        ""
    ).strip()

    consulta = db.select(Producto).where(
        Producto.empresa_id == current_user.empresa_id
    )

    if busqueda:

        consulta = consulta.where(
            db.or_(
                Producto.nombre.ilike(
                    f"%{busqueda}%"
                ),
                Producto.codigo.ilike(
                    f"%{busqueda}%"
                ),
                Producto.categoria.ilike(
                    f"%{busqueda}%"
                )
            )
        )

    consulta = consulta.order_by(
        Producto.id.desc()
    )

    productos = db.session.execute(
        consulta
    ).scalars().all()

    return render_template(
        "productos/index.html",
        productos=productos,
        busqueda=busqueda
    )


# ==========================================
# IMAGEN DEL PRODUCTO
# ==========================================

@productos_bp.route("/imagen/<int:id>")
@login_required
def imagen(id):

    producto = db.session.execute(
        db.select(Producto).where(
            Producto.id == id,
            Producto.empresa_id == current_user.empresa_id
        )
    ).scalar_one_or_none()

    if producto is None or not producto.imagen:
        return "", 404

    return Response(
        producto.imagen,
        mimetype=producto.imagen_tipo or "image/jpeg"
    )


# ==========================================
# CREAR PRODUCTO
# ==========================================

@productos_bp.route(
    "/nuevo",
    methods=["GET", "POST"]
)
@login_required
def nuevo():

    if request.method == "POST":

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        codigo = request.form.get(
            "codigo",
            ""
        ).strip()

        descripcion = request.form.get(
            "descripcion",
            ""
        ).strip()

        categoria = request.form.get(
            "categoria",
            ""
        ).strip()

        precio_compra = request.form.get(
            "precio_compra",
            "0"
        )

        precio_venta = request.form.get(
            "precio_venta",
            "0"
        )

        precio_compra_caja = request.form.get(
            "precio_compra_caja",
            "0"
        )

        precio_venta_caja = request.form.get(
            "precio_venta_caja",
            "0"
        )

        stock = request.form.get(
            "stock",
            "0"
        )

        stock_minimo = request.form.get(
            "stock_minimo",
            "0"
        )

        unidades_por_caja = request.form.get(
            "unidades_por_caja",
            "1"
        )

        maneja_cajas = request.form.get(
            "maneja_cajas"
        ) in (
            "1",
            "true",
            "on",
            "si",
            "yes"
        )

        # ==========================================
        # VALIDACIÓN BÁSICA
        # ==========================================

        if not nombre or not codigo:

            flash(
                "El nombre y el código son obligatorios.",
                "danger"
            )

            return render_template(
                "productos/nuevo.html"
            )

        # ==========================================
        # VALIDAR CÓDIGO DUPLICADO
        # ==========================================

        producto_existente = db.session.execute(
            db.select(Producto).where(
                Producto.empresa_id == current_user.empresa_id,
                Producto.codigo == codigo
            )
        ).scalar_one_or_none()

        if producto_existente:

            flash(
                "Ya existe un producto con ese código.",
                "danger"
            )

            return render_template(
                "productos/nuevo.html"
            )

        try:

            # ==========================================
            # CONVERTIR VALORES
            # ==========================================

            precio_compra_valor = float(
                precio_compra or 0
            )

            precio_venta_valor = float(
                precio_venta or 0
            )

            precio_compra_caja_valor = float(
                precio_compra_caja or 0
            )

            precio_venta_caja_valor = float(
                precio_venta_caja or 0
            )

            stock_valor = int(
                stock or 0
            )

            stock_minimo_valor = int(
                stock_minimo or 0
            )

            unidades_por_caja_valor = int(
                unidades_por_caja or 1
            )

            # ==========================================
            # VALIDACIONES
            # ==========================================

            if unidades_por_caja_valor <= 0:

                raise ValueError(
                    "Las unidades por caja deben ser mayores que cero."
                )

            if stock_valor < 0:

                raise ValueError(
                    "El stock no puede ser negativo."
                )

            if stock_minimo_valor < 0:

                raise ValueError(
                    "El stock mínimo no puede ser negativo."
                )

            if precio_compra_valor < 0:

                raise ValueError(
                    "El precio de compra no puede ser negativo."
                )

            if precio_venta_valor < 0:

                raise ValueError(
                    "El precio de venta no puede ser negativo."
                )

            if precio_compra_caja_valor < 0:

                raise ValueError(
                    "El precio de compra por caja no puede ser negativo."
                )

            if precio_venta_caja_valor < 0:

                raise ValueError(
                    "El precio de venta por caja no puede ser negativo."
                )

            # ==========================================
            # IMAGEN
            # ==========================================

            archivo_imagen = request.files.get(
                "imagen"
            )

            imagen_bytes = None
            imagen_tipo = None

            if archivo_imagen and archivo_imagen.filename:

                tipos_permitidos = {
                    "image/jpeg",
                    "image/png",
                    "image/webp",
                    "image/gif"
                }

                if archivo_imagen.mimetype not in tipos_permitidos:

                    raise ValueError(
                        "La imagen debe ser JPG, PNG, WEBP o GIF."
                    )

                imagen_bytes = archivo_imagen.read()

                if not imagen_bytes:

                    raise ValueError(
                        "No se pudo leer la imagen seleccionada."
                    )

                if len(imagen_bytes) > 5 * 1024 * 1024:

                    raise ValueError(
                        "La imagen no puede superar los 5 MB."
                    )

                imagen_tipo = archivo_imagen.mimetype

            # ==========================================
            # CREAR PRODUCTO
            # ==========================================

            producto = Producto(

                empresa_id=current_user.empresa_id,

                nombre=nombre,

                codigo=codigo,

                descripcion=descripcion or None,

                categoria=categoria or None,

                imagen=imagen_bytes,

                imagen_tipo=imagen_tipo,

                precio_compra=precio_compra_valor,

                precio_venta=precio_venta_valor,

                precio_compra_caja=precio_compra_caja_valor,

                precio_venta_caja=precio_venta_caja_valor,

                stock=stock_valor,

                stock_minimo=stock_minimo_valor,

                unidades_por_caja=unidades_por_caja_valor,

                maneja_cajas=maneja_cajas,

                activo=True
            )

            db.session.add(
                producto
            )

            db.session.commit()

            flash(
                "Producto creado correctamente.",
                "success"
            )

            return redirect(
                url_for("productos.index")
            )

        except (ValueError, TypeError) as error:

            db.session.rollback()

            flash(
                str(error),
                "danger"
            )

    return render_template(
        "productos/nuevo.html"
    )


# ==========================================
# EDITAR PRODUCTO
# ==========================================

@productos_bp.route(
    "/editar/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def editar(id):

    producto = db.session.execute(
        db.select(Producto).where(
            Producto.id == id,
            Producto.empresa_id == current_user.empresa_id
        )
    ).scalar_one_or_none()

    if producto is None:

        flash(
            "Producto no encontrado.",
            "danger"
        )

        return redirect(
            url_for("productos.index")
        )

    if request.method == "POST":

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        codigo = request.form.get(
            "codigo",
            ""
        ).strip()

        descripcion = request.form.get(
            "descripcion",
            ""
        ).strip()

        categoria = request.form.get(
            "categoria",
            ""
        ).strip()

        # ==========================================
        # VALIDACIÓN BÁSICA
        # ==========================================

        if not nombre or not codigo:

            flash(
                "El nombre y el código son obligatorios.",
                "danger"
            )

            return render_template(
                "productos/editar.html",
                producto=producto
            )

        # ==========================================
        # VALIDAR CÓDIGO DUPLICADO
        # ==========================================

        producto_existente = db.session.execute(
            db.select(Producto).where(
                Producto.empresa_id == current_user.empresa_id,
                Producto.codigo == codigo,
                Producto.id != producto.id
            )
        ).scalar_one_or_none()

        if producto_existente:

            flash(
                "Ya existe otro producto con ese código.",
                "danger"
            )

            return render_template(
                "productos/editar.html",
                producto=producto
            )

        try:

            # ==========================================
            # CONVERTIR VALORES
            # ==========================================

            precio_compra = float(
                request.form.get(
                    "precio_compra",
                    0
                ) or 0
            )

            precio_venta = float(
                request.form.get(
                    "precio_venta",
                    0
                ) or 0
            )

            precio_compra_caja = float(
                request.form.get(
                    "precio_compra_caja",
                    0
                ) or 0
            )

            precio_venta_caja = float(
                request.form.get(
                    "precio_venta_caja",
                    0
                ) or 0
            )

            stock = int(
                request.form.get(
                    "stock",
                    0
                ) or 0
            )

            stock_minimo = int(
                request.form.get(
                    "stock_minimo",
                    0
                ) or 0
            )

            unidades_por_caja = int(
                request.form.get(
                    "unidades_por_caja",
                    1
                ) or 1
            )

            maneja_cajas = request.form.get(
                "maneja_cajas"
            ) in (
                "1",
                "true",
                "on",
                "si",
                "yes"
            )

            # ==========================================
            # VALIDACIONES
            # ==========================================

            if unidades_por_caja <= 0:

                raise ValueError(
                    "Las unidades por caja deben ser mayores que cero."
                )

            if stock < 0:

                raise ValueError(
                    "El stock no puede ser negativo."
                )

            if stock_minimo < 0:

                raise ValueError(
                    "El stock mínimo no puede ser negativo."
                )

            if precio_compra < 0:

                raise ValueError(
                    "El precio de compra no puede ser negativo."
                )

            if precio_venta < 0:

                raise ValueError(
                    "El precio de venta no puede ser negativo."
                )

            if precio_compra_caja < 0:

                raise ValueError(
                    "El precio de compra por caja no puede ser negativo."
                )

            if precio_venta_caja < 0:

                raise ValueError(
                    "El precio de venta por caja no puede ser negativo."
                )

            # ==========================================
            # IMAGEN
            # ==========================================

            archivo_imagen = request.files.get(
                "imagen"
            )

            if archivo_imagen and archivo_imagen.filename:

                tipos_permitidos = {
                    "image/jpeg",
                    "image/png",
                    "image/webp",
                    "image/gif"
                }

                if archivo_imagen.mimetype not in tipos_permitidos:

                    raise ValueError(
                        "La imagen debe ser JPG, PNG, WEBP o GIF."
                    )

                imagen_bytes = archivo_imagen.read()

                if not imagen_bytes:

                    raise ValueError(
                        "No se pudo leer la imagen seleccionada."
                    )

                if len(imagen_bytes) > 5 * 1024 * 1024:

                    raise ValueError(
                        "La imagen no puede superar los 5 MB."
                    )

                producto.imagen = imagen_bytes

                producto.imagen_tipo = (
                    archivo_imagen.mimetype
                )

            # ==========================================
            # ACTUALIZAR INFORMACIÓN
            # ==========================================

            producto.nombre = nombre

            producto.codigo = codigo

            producto.descripcion = (
                descripcion or None
            )

            producto.categoria = (
                categoria or None
            )

            # ==========================================
            # ACTUALIZAR PRECIOS
            # ==========================================

            producto.precio_compra = (
                precio_compra
            )

            producto.precio_venta = (
                precio_venta
            )

            producto.precio_compra_caja = (
                precio_compra_caja
            )

            producto.precio_venta_caja = (
                precio_venta_caja
            )

            # ==========================================
            # ACTUALIZAR INVENTARIO
            # ==========================================

            producto.stock = stock

            producto.stock_minimo = (
                stock_minimo
            )

            # ==========================================
            # ACTUALIZAR CONFIGURACIÓN DE CAJAS
            # ==========================================

            producto.unidades_por_caja = (
                unidades_por_caja
            )

            producto.maneja_cajas = (
                maneja_cajas
            )

            # ==========================================
            # GUARDAR
            # ==========================================

            db.session.commit()

            flash(
                "Producto actualizado correctamente.",
                "success"
            )

            return redirect(
                url_for("productos.index")
            )

        except (ValueError, TypeError) as error:

            db.session.rollback()

            flash(
                str(error),
                "danger"
            )

    return render_template(
        "productos/editar.html",
        producto=producto
    )


# ==========================================
# ELIMINAR / DESACTIVAR PRODUCTO
# ==========================================

@productos_bp.route(
    "/eliminar/<int:id>",
    methods=["POST"]
)
@login_required
def eliminar(id):

    producto = db.session.execute(
        db.select(Producto).where(
            Producto.id == id,
            Producto.empresa_id == current_user.empresa_id
        )
    ).scalar_one_or_none()

    if producto is None:

        flash(
            "Producto no encontrado.",
            "danger"
        )

        return redirect(
            url_for("productos.index")
        )

    producto.activo = False

    db.session.commit()

    flash(
        "Producto desactivado correctamente.",
        "success"
    )

    return redirect(
        url_for("productos.index")
    )

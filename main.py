from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, Cliente, Empleado, Servicio, Cita
from datetime import datetime, timedelta, time
from functools import wraps
from models import Servicio, Producto, Proveedor, OrdenCompra, DetalleOrdenCompra  # Asegúrate de importar tus modelos
from werkzeug.utils import secure_filename
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from models import db
from urllib.parse import quote_plus
import time, os, logging
from models import Tarea
from pytz import timezone, utc
from babel.numbers import format_currency


import pytz

zona_local = pytz.timezone('America/Costa_Rica')
fecha_local = datetime.now(zona_local)

app = Flask(__name__)

app.secret_key = 'tu_clave_secreta_aqui'  # IMPORTANTE para usar sesiones

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///salon.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Config DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///productos.db'




# Usuario hardcodeado
USUARIO = {
    'username': 'admin',
    'password': 'admin123'
}

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# PÁGINA PÚBLICA, accesible sin login


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USUARIO['username'] and password == USUARIO['password']:
            session['logged_in'] = True
            flash('Has iniciado sesión correctamente', 'success')
            return redirect(url_for('admin_index'))  # Aquí la ruta para la admin
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    # Mostrar plantilla de login (que debería estar en templates/login.html)
    return render_template('login.html')



# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('login'))

# Rutas protegidas, solo para personal logueado
@app.route('/index')
@login_required
def index_admin():
    return render_template('admin/index.html')

@app.route('/citas')
@login_required
def citas():
    citas = Cita.query.order_by(Cita.fecha_hora_inicio).all()
    return render_template('admin/citas.html', citas=citas)

@app.route('/nueva-cita', methods=['GET', 'POST'])
@login_required
def nueva_cita():
    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        servicio_id = int(request.form['servicio'])
        empleado_id = int(request.form['empleado'])
        fecha_hora = datetime.strptime(request.form['fecha_hora'], '%Y-%m-%dT%H:%M')

        cliente = Cliente(nombre=nombre, telefono=telefono)
        db.session.add(cliente)
        db.session.commit()

        servicio = Servicio.query.get(servicio_id)
        fecha_fin = fecha_hora + timedelta(minutes=servicio.duracion_minutos)

        cita = Cita(
            cliente_id=cliente.id,
            servicio_id=servicio.id,
            empleado_id=empleado_id,
            fecha_hora_inicio=fecha_hora,
            fecha_hora_fin=fecha_fin
        )
        db.session.add(cita)
        db.session.commit()

        return redirect(url_for('citas'))

    servicios = Servicio.query.all()
    empleados = Empleado.query.all()
    return render_template('admin/nueva_cita.html', servicios=servicios, empleados=empleados)

@app.route('/api/citas-json')
@login_required
def citas_json():
    citas = Cita.query.all()
    eventos = []
    for cita in citas:
        eventos.append({
            'title': f"{cita.cliente.nombre} - {cita.servicio.nombre}",
            'start': cita.fecha_hora_inicio.isoformat(),
            'end': cita.fecha_hora_fin.isoformat(),
            'description': f"Empleado: {cita.empleado.nombre}"
        })
    return jsonify(eventos)

@app.route('/admin/servicios', methods=['GET', 'POST'])
@login_required
def servicios():
    if request.method == 'POST':
        nombre = request.form['nombre']
        duracion = int(request.form['duracion'])
        precio = float(request.form['precio'])

        nuevo_servicio = Servicio(nombre=nombre, duracion_minutos=duracion, precio=precio)
        db.session.add(nuevo_servicio)
        db.session.commit()

        return redirect(url_for('servicios'))

    lista = Servicio.query.all()
    return render_template('admin/servicios.html', servicios=lista)

@app.route('/servicio/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_servicio(id):
    servicio = Servicio.query.get_or_404(id)

    if request.method == 'POST':
        servicio.nombre = request.form['nombre']
        servicio.duracion_minutos = int(request.form['duracion'])
        servicio.precio = float(request.form['precio'])

        db.session.commit()
        return redirect(url_for('servicios'))

    return render_template('admin/editar_servicio.html', servicio=servicio)

@app.route('/servicio/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_servicio(id):
    servicio = Servicio.query.get_or_404(id)
    db.session.delete(servicio)
    db.session.commit()
    return redirect(url_for('servicios'))

@app.route('/calendario')
@login_required
def calendario():
    return render_template('admin/calendario.html')

@app.route('/empleados', methods=['GET', 'POST'])
@login_required
def empleados():
    if request.method == 'POST':
        nombre = request.form['nombre']
        especialidad = request.form['especialidad']
        telefono = request.form['telefono']

        nuevo = Empleado(nombre=nombre, especialidad=especialidad, telefono=telefono)
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('empleados'))

    lista = Empleado.query.all()
    return render_template('admin/empleados.html', empleados=lista)

@app.route('/empleado/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_empleado(id):
    empleado = Empleado.query.get_or_404(id)
    if request.method == 'POST':
        empleado.nombre = request.form['nombre']
        empleado.especialidad = request.form['especialidad']
        empleado.telefono = request.form['telefono']
        db.session.commit()
        return redirect(url_for('empleados'))
    return render_template('/admin/editar_empleado.html', empleado=empleado)

@app.route('/empleado/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_empleado(id):
    empleado = Empleado.query.get_or_404(id)
    db.session.delete(empleado)
    db.session.commit()
    return redirect(url_for('/admin/empleados'))

@app.route('/cita/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_cita(id):
    cita = Cita.query.get_or_404(id)
    servicios = Servicio.query.all()
    empleados = Empleado.query.all()

    if request.method == 'POST':
        cita.servicio_id = int(request.form['servicio'])
        cita.empleado_id = int(request.form['empleado'])
        cita.fecha_hora_inicio = datetime.strptime(request.form['fecha_hora'], '%Y-%m-%dT%H:%M')

        servicio = Servicio.query.get(cita.servicio_id)
        cita.fecha_hora_fin = cita.fecha_hora_inicio + timedelta(minutes=servicio.duracion_minutos)

        db.session.commit()
        return redirect(url_for('citas'))

    return render_template('editar_cita.html', cita=cita, servicios=servicios, empleados=empleados)

@app.route('/cita/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_cita(id):
    cita = Cita.query.get_or_404(id)
    db.session.delete(cita)
    db.session.commit()
    return redirect(url_for('/admin/citas'))





@app.route('/servicios')
def servicios_publicos():
    servicios = Servicio.query.all()
    return render_template('public/servicios.html', servicios=servicios)

@app.route('/productos')
def productos_publicos():
    # Solo mostrar productos visibles públicamente
    productos = Producto.query.filter_by(visible=True).all()
    
    for prod in productos:
        prod.nombre_url = quote_plus(prod.nombre)
    
    return render_template('public/productos.html', productos=productos)



@app.route('/admin/productos', methods=['GET', 'POST'])
@login_required
def admin_productos():
    if request.method == 'POST':
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        descripcion = request.form.get('descripcion')
        precio = float(request.form['precio'])
        visible = 'visible' in request.form

        # Verificar si el código ya existe
        existe = Producto.query.filter_by(codigo=codigo).first()
        if existe:
            flash('El código ya existe, elige otro.', 'danger')
            return redirect(url_for('admin_productos'))

        imagen = request.files.get('imagen')
        imagen_url = None

        if imagen and allowed_file(imagen.filename):
            filename = secure_filename(imagen.filename)
            filename = f"{int(time.time())}_{filename}"
            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            save_path = os.path.join(upload_folder, filename)
            imagen.save(save_path)
            imagen_url = f'uploads/{filename}'

        nuevo = Producto(
            codigo=codigo,
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            imagen_url=imagen_url,
            visible=visible
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Producto agregado exitosamente', 'success')
        return redirect(url_for('admin_productos'))

    productos = Producto.query.all()
    return render_template('admin/productos_admin.html', productos=productos)






@app.route('/admin/productos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    prod = Producto.query.get_or_404(id)

    if request.method == 'POST':
        codigo = request.form['codigo']
        # Validar que el código no exista en otro producto
        existe = Producto.query.filter(Producto.codigo == codigo, Producto.id != id).first()
        if existe:
            flash('El código ya existe en otro producto.', 'danger')
            return redirect(url_for('editar_producto', id=id))

        prod.codigo = codigo
        prod.nombre = request.form['nombre']
        prod.descripcion = request.form.get('descripcion')
        prod.precio = float(request.form['precio'])
        prod.visible = 'visible' in request.form

        # Manejo de imagen
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and allowed_file(file.filename):
                # Borrar imagen anterior si existe
                if prod.imagen_url:
                    ruta_anterior = os.path.join(app.static_folder, prod.imagen_url.replace('/', os.sep))
                    if os.path.exists(ruta_anterior):
                        os.remove(ruta_anterior)

                # Guardar nueva imagen
                filename = secure_filename(file.filename)
                filename = f"{int(time.time())}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                prod.imagen_url = f"uploads/{filename}"

        db.session.commit()
        flash('Producto actualizado con éxito', 'success')
        return redirect(url_for('admin_productos'))

    return render_template('admin/editar_producto.html', producto=prod)









@app.route('/admin/productos/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_producto(id):
    prod = Producto.query.get_or_404(id)
    db.session.delete(prod)
    db.session.commit()
    flash('Producto eliminado', 'warning')
    return redirect(url_for('admin_productos'))


@app.route('/')
def index():
    servicios = Servicio.query.all()
    productos = Producto.query.all()
    return render_template('publica.html', servicios=servicios, productos=productos)


@app.route('/admin')
@login_required
def admin_index():
    servicios = Servicio.query.all()
    productos = Producto.query.all()
    return render_template('admin/index.html', servicios=servicios, productos=productos)




@app.route('/tareas', methods=['GET', 'POST'])
@login_required
def tareas():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        nueva_tarea = Tarea(titulo=titulo, descripcion=descripcion)
        db.session.add(nueva_tarea)
        db.session.commit()
        return redirect(url_for('tareas'))

    tareas = Tarea.query.order_by(Tarea.estado).all()
    return render_template('admin/tareas.html', tareas=tareas)


@app.route('/admin/tareas/<int:id>/estado', methods=['POST'])
@login_required
def cambiar_estado(id):
    tarea = Tarea.query.get_or_404(id)
    nuevo_estado = request.form['estado']
    tarea.estado = nuevo_estado
    db.session.commit()
    return redirect(url_for('tareas'))

@app.route('/admin/tareas/nueva', methods=['GET', 'POST'])
@login_required
def nueva_tarea():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        estado = request.form['estado']

        tarea = Tarea(titulo=titulo, descripcion=descripcion, estado=estado)
        db.session.add(tarea)
        db.session.commit()
        flash('Tarea creada exitosamente', 'success')
        return redirect(url_for('tareas'))

    return render_template('admin/nueva_tarea.html')



@app.route('/admin/tareas/editar/<int:id>', methods=['GET', 'POST'])
@login_required  # Si usas login requerido
def editar_tarea(id):
    tarea = Tarea.query.get_or_404(id)

    if request.method == 'POST':
        tarea.titulo = request.form['titulo']
        tarea.descripcion = request.form.get('descripcion', '')
        tarea.estado = request.form['estado']

        db.session.commit()
        flash('Tarea actualizada exitosamente', 'success')
        return redirect(url_for('tareas'))

    return render_template('admin/editar_tarea.html', tarea=tarea)


@app.route('/admin/tareas/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_tarea(id):
    tarea = Tarea.query.get_or_404(id)
    try:
        db.session.delete(tarea)
        db.session.commit()
        flash('Tarea eliminada correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar la tarea.', 'danger')
    return redirect(url_for('tareas'))



@app.route("/catalogo")
def catalogo():
    return render_template("catalogo.html")




RUTA_CATALOGO = os.path.join('static', 'pdf', 'catalogo.pdf')

@app.route('/admin/catalogo', methods=['GET'])
@login_required
def panel_catalogo():
    mensaje = request.args.get('mensaje')
    catalogo_existe = os.path.exists(RUTA_CATALOGO)
    return render_template('admin/gestionar_catalogo.html', mensaje=mensaje, catalogo_existe=catalogo_existe)

@app.route('/admin/catalogo/subir', methods=['POST'])
@login_required
def subir_catalogo():
    archivo = request.files.get('pdf')
    if archivo and archivo.filename.endswith('.pdf'):
        archivo.save(RUTA_CATALOGO)
        return redirect(url_for('panel_catalogo', mensaje="Catálogo actualizado correctamente."))
    return redirect(url_for('panel_catalogo', mensaje="Error: archivo no válido."))

@app.route('/admin/catalogo/eliminar', methods=['POST'])
@login_required
def eliminar_catalogo():
    if os.path.exists(RUTA_CATALOGO):
        os.remove(RUTA_CATALOGO)
        return redirect(url_for('panel_catalogo', mensaje="Catálogo eliminado."))
    return redirect(url_for('panel_catalogo', mensaje="No hay catálogo para eliminar."))



@app.route('/admin/proveedores')
@login_required
def vista_proveedores():
    lista_proveedores = Proveedor.query.all()
    return render_template('admin/proveedores.html', proveedores=lista_proveedores)



@app.route('/admin/proveedores/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_proveedor():
    if request.method == 'POST':
        nombre = request.form['nombre']
        contacto = request.form['contacto']
        telefono = request.form['telefono']
        email = request.form['email']
        direccion = request.form['direccion']

        nuevo = Proveedor(
            nombre=nombre,
            contacto=contacto,
            telefono=telefono,
            email=email,
            direccion=direccion
        )

        db.session.add(nuevo)
        db.session.commit()

        return redirect(url_for('vista_proveedores'))

    # Si es GET, simplemente renderiza el formulario
    return render_template('admin/nuevo_proveedor.html')



@app.route('/admin/proveedor/editar/<int:id>', methods=['POST'])
@login_required
def editar_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    proveedor.nombre = request.form['nombre']
    proveedor.contacto = request.form['contacto']
    proveedor.telefono = request.form['telefono']
    proveedor.email = request.form['email']
    proveedor.direccion = request.form['direccion']
    db.session.commit()
    return redirect(url_for('vista_proveedores'))

@app.route('/admin/proveedor/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    db.session.delete(proveedor)
    db.session.commit()
    return redirect(url_for('vista_proveedores'))



@app.route('/ordenes')
@login_required
def listar_ordenes():
    ordenes = OrdenCompra.query.order_by(OrdenCompra.fecha_creacion.desc()).all()
    return render_template('/admin/ordenes.html', ordenes=ordenes)


@app.route('/ordenes/nueva', methods=['GET', 'POST'])
@login_required
def nueva_orden():
    proveedores = Proveedor.query.all()
    productos = Producto.query.all()
    
    if request.method == 'POST':
        proveedor_id = request.form.get('proveedor')
        productos_ids = request.form.getlist('producto[]')
        cantidades = request.form.getlist('cantidad[]')
        precios = request.form.getlist('precio[]')

        if not proveedor_id or not productos_ids or not cantidades or not precios:
            flash('Debe completar todos los campos de la orden', 'error')
            return redirect(url_for('nueva_orden'))

        if len(productos_ids) != len(cantidades) or len(cantidades) != len(precios):
            flash('Datos de productos inconsistentes', 'error')
            return redirect(url_for('nueva_orden'))

        orden = OrdenCompra(proveedor_id=proveedor_id, fecha_creacion=datetime.utcnow())
        db.session.add(orden)
        db.session.flush()

        total = 0
        for pid, cant, precio in zip(productos_ids, cantidades, precios):
            try:
                pid = int(pid)
                cant = int(cant)
                precio = float(precio)
                if cant > 0:
                    detalle = DetalleOrdenCompra(
                        orden_compra_id=orden.id,
                        producto_id=pid,
                        cantidad=cant,
                        precio_unitario=precio
                    )
                    total += cant * precio
                    db.session.add(detalle)
            except (ValueError, TypeError):
                flash('Error en los datos del producto. Verifique los valores ingresados.', 'error')
                return redirect(url_for('nueva_orden'))

        orden.total = total
        db.session.commit()

        flash('Orden creada correctamente', 'success')
        return redirect(url_for('listar_ordenes'))

    productos_json = [
        {'id': p.id, 'codigo': p.codigo, 'nombre': p.nombre, 'precio': float(p.precio)}
        for p in productos
    ]

    return render_template('/admin/nueva_orden.html', proveedores=proveedores, productos_json=productos_json)



from sqlalchemy.orm import joinedload
@app.route('/ordenes/<int:id>')
@login_required
def detalle_orden(id):
    orden = db.session.query(OrdenCompra).options(
        joinedload(OrdenCompra.detalles).joinedload(DetalleOrdenCompra.producto),
        joinedload(OrdenCompra.proveedor)
        
    ).get_or_404(id)
    if orden.fecha_creacion.tzinfo is None:
        fecha_utc = orden.fecha_creacion.replace(tzinfo=utc)
    else:
        fecha_utc = orden.fecha_creacion.astimezone(utc)
        
    tz_cr = timezone('America/Costa_Rica')
    orden.fecha_local = fecha_utc.astimezone(tz_cr)
    return render_template('admin/detalle_orden.html', orden=orden)


@app.route('/ordenes/<int:id>/cambiar_estado', methods=['POST'])
@login_required
def cambiar_estado_orden(id):
    orden = OrdenCompra.query.get_or_404(id)
    nuevo_estado = request.form.get('estado')
    
    if nuevo_estado not in ['pendiente', 'procesada', 'cancelada']:
        flash('Estado inválido', 'error')
        return redirect(url_for('detalle_orden', id=id))

    orden.estado = nuevo_estado
    db.session.commit()
    flash(f'Estado cambiado a {nuevo_estado.capitalize()}', 'success')
    return redirect(url_for('detalle_orden', id=id))




@app.route('/ordenes/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_orden(id):
    orden = OrdenCompra.query.get_or_404(id)

    if orden.estado != 'cancelada':
        flash('Solo se pueden eliminar órdenes canceladas.', 'warning')
        return redirect(url_for('detalle_orden', id=id))

    try:
        db.session.delete(orden)
        db.session.commit()
        flash('Orden eliminada correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ocurrió un error al eliminar la orden.', 'danger')

    return redirect(url_for('listar_ordenes'))


@app.template_filter('formatear_colones')
@login_required
def formatear_colones(valor):
    if valor is None:
        return "₡0,00"
    return format_currency(valor, 'CRC', locale='es_CR')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

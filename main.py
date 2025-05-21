from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, Cliente, Empleado, Servicio, Cita
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  # IMPORTANTE para usar sesiones

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///salon.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

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
@app.route('/')
def publica():
    return render_template('publica.html')

# LOGIN (GET y POST)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USUARIO['username'] and password == USUARIO['password']:
            session['logged_in'] = True
            flash('Has iniciado sesión correctamente', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
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
def index():
    return render_template('index.html')

@app.route('/citas')
@login_required
def citas():
    citas = Cita.query.order_by(Cita.fecha_hora_inicio).all()
    return render_template('citas.html', citas=citas)

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
    return render_template('nueva_cita.html', servicios=servicios, empleados=empleados)

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

@app.route('/servicios', methods=['GET', 'POST'])
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
    return render_template('servicios.html', servicios=lista)

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

    return render_template('editar_servicio.html', servicio=servicio)

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
    return render_template('calendario.html')

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
    return render_template('empleados.html', empleados=lista)

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
    return render_template('editar_empleado.html', empleado=empleado)

@app.route('/empleado/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_empleado(id):
    empleado = Empleado.query.get_or_404(id)
    db.session.delete(empleado)
    db.session.commit()
    return redirect(url_for('empleados'))

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
    return redirect(url_for('citas'))


if __name__ == '__main__':
    app.run(port=5000, debug=True)

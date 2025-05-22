
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)

    citas = db.relationship('Cita', backref='cliente', lazy=True)

    def __repr__(self):
        return f'<Cliente {self.nombre}>'


class Empleado(db.Model):
    __tablename__ = 'empleados'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    especialidad = db.Column(db.String(200), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)  # <-- este campo falta

    citas = db.relationship('Cita', backref='empleado', lazy=True)

    def __repr__(self):
        return f'<Empleado {self.nombre}>'

class Servicio(db.Model):
    __tablename__ = 'servicios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)  # Nuevo
    duracion_minutos = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    imagen_url = db.Column(db.String(255), nullable=True)  # Opcional

    citas = db.relationship('Cita', backref='servicio', lazy=True)

    def __repr__(self):
        return f'<Servicio {self.nombre}>'

class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(255))
    imagen_url = db.Column(db.String(255))  # opcional, para mostrar imágenes

    def __repr__(self):
        return f'<Producto {self.nombre}>'



class Cita(db.Model):
    __tablename__ = 'citas'
    id = db.Column(db.Integer, primary_key=True)
    fecha_hora_inicio = db.Column(db.DateTime, nullable=False)
    fecha_hora_fin = db.Column(db.DateTime, nullable=False)

    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleados.id'), nullable=False)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id'), nullable=False)

    estado = db.Column(db.String(20), default='confirmada')  # confirmada, cancelada, completada
    notas = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Cita {self.fecha_hora_inicio} - Cliente {self.cliente_id}>'



class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    estado = db.Column(db.String(20), nullable=False, default='pendiente')  # pendiente, en_progreso, completada
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
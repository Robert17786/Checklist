import sqlite3

# Crear o conectar a la base de datos
conn = sqlite3.connect("checklist_data_center.db")
cursor = conn.cursor()

# Crear tabla de ingreso
cursor.execute("DROP TABLE IF EXISTS solicitudes_ingreso")

cursor.execute("""
CREATE TABLE IF NOT EXISTS solicitudes_ingreso (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solicitante TEXT NOT NULL,
    fecha_ingreso TEXT NOT NULL,
    cliente TEXT NOT NULL,
    datacenter TEXT NOT NULL,
    ticket TEXT NOT NULL,
    cantidad_equipos INTEGER NOT NULL,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    numero_serie TEXT NOT NULL,
    tipo_equipo TEXT NOT NULL,
    rack_asignado TEXT,
    ubicacion_rack_u TEXT,
    cantidad_u INTEGER,
    propiedad TEXT,
    sala TEXT,
    dual_single TEXT,
    tag TEXT,
    mt2 TEXT,
    estado_inicial TEXT,
    detalles TEXT
)
""")

# Crear tabla de egreso
cursor.execute("DROP TABLE IF EXISTS solicitudes_egreso")

cursor.execute("""
CREATE TABLE IF NOT EXISTS solicitudes_egreso (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solicitante TEXT NOT NULL,
    fecha_egreso TEXT NOT NULL,
    datacenter TEXT NOT NULL,
    ticket TEXT NOT NULL,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    numero_serie TEXT NOT NULL,
    rack_origen TEXT,
    motivo_egreso TEXT NOT NULL,
    estado_salida TEXT NOT NULL
)
""")

# Crear tabla de movimiento interno

cursor.execute("""
CREATE TABLE IF NOT EXISTS movimientos_internos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solicitante TEXT NOT NULL,
    fecha_movimiento TEXT NOT NULL,
    ticket TEXT NOT NULL,
    datacenter_origen TEXT NOT NULL,
    rack_origen TEXT,
    datacenter_destino TEXT NOT NULL,
    rack_destino TEXT,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    numero_serie TEXT NOT NULL,
    estado_equipo TEXT NOT NULL
)
""")

# Crear tabla del catálogo
cursor.execute("""
CREATE TABLE IF NOT EXISTS catalogo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    tipo_equipo TEXT NOT NULL
)
""")

# Guardar cambios y cerrar conexión
conn.commit()
conn.close()

print("Base de datos configurada correctamente.")
import pandas as pd
import sqlite3

# Leer el archivo Excel
catalogo_df = pd.read_excel("Catalogo_full.xlsx")

# Filtrar filas donde marca, modelo y tipo_equipo no estén vacíos
catalogo_df = catalogo_df.dropna(subset=["marca", "modelo", "tipo_equipo"])

# Conectar a la base de datos
conn = sqlite3.connect("checklist_data_center.db")
cursor = conn.cursor()

# Insertar datos en la tabla catalogo
for _, row in catalogo_df.iterrows():
    cursor.execute("""
    INSERT INTO catalogo (marca, modelo, tipo_equipo)
    VALUES (?, ?, ?)
    """, (row["marca"], row["modelo"], row["tipo_equipo"]))

# Guardar cambios y cerrar conexión
conn.commit()
conn.close()

print("Datos del catálogo cargados correctamente.")

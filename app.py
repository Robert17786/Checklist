# 1. Conexión y Configuración Inicial

import streamlit as st
import sqlite3
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import plotly.express as px
import bcrypt
from datetime import date, timedelta



# Inyectar CSS personalizado
st.markdown(
    """
    <style>
    /* Fondo blanco en el cuerpo principal */
    .stApp {
        background-color: #FFFFFF !important;
    }
    /* Títulos en verde */
    h1, h2, h3, h4, h5, h6 {
        color: #2E8B57 !important; 
    }
    /* Textos generales en negro */
    p, label, span {
        color: #000000 !important;
    }
    /* Cambiar el color del texto en métricas generales */
    [data-testid="stMetricValue"] {
        color: #000000 !important; /* Color negro para el valor */
    }
    [data-testid="stMetricLabel"] {
        color: #000000 !important; /* Color negro para el subtítulo */
    }
    /* Fondo de la barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #E7F5E6 !important; 
    }
    /* Cambiar el color de la barra superior */
    header {
        background-color: #E7F5E6 !important; /* Color igual a la barra lateral */
        color: #000000 !important; /* Texto en negro si aplica */
    }
    /* Botones personalizados */
    button {
        background-color: #2E8B57 !important; 
        color: #FFFFFF !important; 
        border-radius: 4px;
        border: none !important;
    }
    /* Ajuste del padding del contenedor principal */
    .block-container {
        padding: 2rem 1rem !important;
    }
    
    </style>
    """,
    unsafe_allow_html=True
)


# Ejemplo visual
#st.title("Prueba de Títulos Verdes y Texto Negro")
#st.write("Este es un párrafo de ejemplo con texto negro.")
#st.sidebar.title("Barra Lateral")
#st.sidebar.write("Este es un ejemplo del área lateral con fondo verde claro.")




# 2. Inicializar claves en st.session_state si no existen (esto se hace UNA VEZ)
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False  # Estado inicial: no autenticado
if "rol" not in st.session_state:
    st.session_state["rol"] = None  # Inicializa el rol como None
if "opcion_seleccionada" not in st.session_state:
    st.session_state["opcion_seleccionada"] = None  # Inicializa la opción seleccionada




# 3. Adaptador para convertir datetime a ISO para SQLite
def adapt_datetime(dt):
    return dt.isoformat()  # Convierte a ISO estándar

def convert_datetime(iso):
    if iso is None:
        return None
    if isinstance(iso, bytes):  # Manejar datos en bytes
        iso = iso.decode("utf-8")
    try:
        return datetime.fromisoformat(iso)  # Intentar convertir desde el formato ISO
    except ValueError:
        try:
            return datetime.strptime(iso, '%Y-%m-%d %H:%M:%S')  # Formato común en SQLite
        except ValueError:
            return None  # Ignorar valores inválidos




# 4. Registrar adaptadores con SQLite
sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("DATETIME", convert_datetime)




# 5. Conectar a la base de datos
def conectar_db():
    conn = sqlite3.connect("checklist_data_center.db", detect_types=sqlite3.PARSE_DECLTYPES)
    return conn




# 6. Función de inicio de sesión
def login():
    # Mostrar el logo de tu empresa en la pantalla de login
    st.image("logo2.png", use_container_width=True)
    st.subheader("Inicio de sesión")
    # Variables de entrada para correo y contraseña
    correo = st.text_input("Correo electrónico:", key="login_email_input")
    contrasena = st.text_input("Contraseña:", type="password", key="login_password_input")
    
    if st.button("Iniciar sesión", key="login_button"):
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT rol FROM usuarios WHERE correo = ? AND contrasena = ?", (correo, contrasena))
        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            # NO llames a st.session_state.clear() aquí para no borrar los datos que acabas de asignar
            st.session_state["rol"] = resultado[0]
            st.session_state["login_email"] = correo  # Guarda el correo del usuario
            st.session_state["logged_in"] = True
            st.success(f"¡Bienvenido! Rol: {resultado[0]}")
            #st.query_params()  # Opcional: redirigir o actualizar la URL
        else:
            st.error("Credenciales incorrectas. Intenta nuevamente.")




# 7. Verificar que el usuario ya haya iniciado sesión.
if not st.session_state.get("logged_in", False):
    login()
    st.stop()  # Detener la ejecución hasta que se inicie sesión




# 8. Para depuración, puedes mostrar el contenido actual de la sesión
#st.write("Estado de la sesión:", st.session_state)




# 9. Limpiar tablas
def limpiar_tablas():
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        # Eliminar registros de todas las tablas
        cursor.execute("DELETE FROM solicitudes_ingreso;")
        cursor.execute("DELETE FROM solicitudes_egreso;")
        cursor.execute("DELETE FROM movimientos_internos;")
        cursor.execute("DELETE FROM dashboard_data;")
        cursor.execute("DELETE FROM historial_cambios;")
        #cursor.execute("DELETE FROM usuarios;")
        
        # Reiniciar los contadores de ID
        cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'solicitudes_ingreso';")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'solicitudes_egreso';")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'movimientos_internos';")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'dashboard_data';")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'historial_cambios';")
        #cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'usuarios';")
        
        conn.commit()
        print("Todas las tablas han sido limpiadas correctamente y los contadores de ID han sido reiniciados.")
    except sqlite3.Error as e:
        print(f"Error al limpiar las tablas: {e}")
    finally:
        conn.close()

# Llamada a la función
#limpiar_tablas()




# 10. Insertar rapidamente usuarios
def insertar_usuarios_iniciales():
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        # Usuario Administrador
        cursor.execute("""
            INSERT INTO usuarios (correo, nombre, rol, contrasena)
            VALUES (?, ?, ?, ?)
        """, ("admin@datacenter.com", "Administrador Principal", "Administrador", "admin123"))

        # Usuario Técnico
        cursor.execute("""
            INSERT INTO usuarios (correo, nombre, rol, contrasena)
            VALUES (?, ?, ?, ?)
        """, ("tecnico@datacenter.com", "Técnico de Soporte", "Tecnico", "tecnico123"))

        conn.commit()
        print("Usuarios iniciales insertados exitosamente.")
    except sqlite3.Error as e:
        print(f"Error al insertar usuarios: {e}")
    finally:
        conn.close()

# Llamar a la función para insertar usuarios
#insertar_usuarios_iniciales()




# 11. Generacion de reportes.
def generar_reporte_ingresos():
    conn = conectar_db()
    try:
        # Consultar datos de ingresos
        df_ingresos = pd.read_sql_query("SELECT * FROM solicitudes_ingreso", conn)
        
        # Validar si hay datos
        if df_ingresos.empty:
            st.warning("No hay datos de ingresos para generar el reporte.")
        else:
            # Exportar a CSV
            st.download_button(
                label="Descargar Reporte de Ingresos",
                data=df_ingresos.to_csv(index=False),
                file_name="reporte_ingresos.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"Error al generar el reporte de ingresos: {e}")
    finally:
        conn.close()

def generar_reporte_egresos():
    conn = conectar_db()
    try:
        # Consultar datos de egresos
        df_egresos = pd.read_sql_query("SELECT * FROM solicitudes_egreso", conn)
        
        # Validar si hay datos
        if df_egresos.empty:
            st.warning("No hay datos de egresos para generar el reporte.")
        else:
            # Exportar a CSV
            st.download_button(
                label="Descargar Reporte de Egresos",
                data=df_egresos.to_csv(index=False),
                file_name="reporte_egresos.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"Error al generar el reporte de egresos: {e}")
    finally:
        conn.close()

def generar_reporte_movimientos():
    conn = conectar_db()
    try:
        # Consultar datos de movimientos internos
        df_movimientos = pd.read_sql_query("SELECT * FROM movimientos_internos", conn)
        
        # Validar si hay datos
        if df_movimientos.empty:
            st.warning("No hay datos de movimientos internos para generar el reporte.")
        else:
            # Exportar a CSV
            st.download_button(
                label="Descargar Reporte de Movimientos Internos",
                data=df_movimientos.to_csv(index=False),
                file_name="reporte_movimientos_internos.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"Error al generar el reporte de movimientos internos: {e}")
    finally:
        conn.close()




# 12. Verificación del Rol del Usuario

if "rol" not in st.session_state:  # Verifica si el usuario ya inició sesión
    rol_usuario = login()  # Llama a la función login() que autentica al usuario
    if not rol_usuario:
        st.stop()  # Detén la ejecución si el login falla
else:
    rol_usuario = st.session_state["rol"]  # Recupera el rol del usuario ya




# 13. Función para convertir fechas a formato ISO
def convertir_fecha_iso(fecha):
    return fecha.strftime("%Y-%m-%d")  # Formato estándar de fecha ISO



# 14. Enviar correo
def enviar_correo(destinatarios, asunto, mensaje):
    # Configuración del servidor de correo
    servidor = "smtp.gmail.com"
    puerto = 587
    # Utiliza un correo fijo autorizado para envíos, en vez del correo del usuario logueado.
    remitente = "robert17786@gmail.com"  # Reemplaza este correo por uno autorizado para el envío SMTP
    contraseña = "tbob sxov zmar hsnq"    # Reemplaza con la contraseña de aplicación correcta

    # Crear el mensaje
    email = MIMEMultipart()
    email["From"] = remitente
    email["To"] = ", ".join(destinatarios)
    email["Subject"] = asunto
    email.attach(MIMEText(mensaje, "plain"))

    try:
        # Conectar al servidor y enviar el correo
        with smtplib.SMTP(servidor, puerto) as smtp:
            smtp.starttls()  # Encriptar conexión
            smtp.login(remitente, contraseña)
            smtp.sendmail(remitente, destinatarios, email.as_string())
        return True
    except Exception as e:
        # Muestra el error detallado para depuración
        print(f"Error al enviar el correo: {e}")
        return False




# 15. Exportar Datos en Formato CSV
# Funcion para extraer datos de la base de datos
def exportar_csv_ingresos():
    conn = conectar_db()
    df = pd.read_sql_query("SELECT * FROM solicitudes_ingreso", conn)
    conn.close()
    return df




# 16. Cálculo de Estadísticas del Dashboard
# Funcion para obtener estadisticas necesarias desde la base de datos
def obtener_datos_dashboard():
    conn = conectar_db()
    cursor = conn.cursor()

    # Contadores generales
    total_ingresos = cursor.execute("SELECT COUNT(*) FROM solicitudes_ingreso").fetchone()[0]
    total_egresos = cursor.execute("SELECT COUNT(*) FROM solicitudes_egreso").fetchone()[0]
    total_movimientos = cursor.execute("SELECT COUNT(*) FROM movimientos_internos").fetchone()[0]

    # Datos por DataCenter
    datacenters_ingresos = cursor.execute("SELECT datacenter, COUNT(*) FROM solicitudes_ingreso GROUP BY datacenter").fetchall()
    datacenters_egresos = cursor.execute("SELECT datacenter, COUNT(*) FROM solicitudes_egreso GROUP BY datacenter").fetchall()
    datacenters_movimientos = cursor.execute("SELECT datacenter_origen, COUNT(*) FROM movimientos_internos GROUP BY datacenter_origen").fetchall()

    conn.close()
    return {
        "total_ingresos": total_ingresos,
        "total_egresos": total_egresos,
        "total_movimientos": total_movimientos,
        "datacenters_ingresos": datacenters_ingresos,
        "datacenters_egresos": datacenters_egresos,
        "datacenters_movimientos": datacenters_movimientos
    }




# 17. Verificación de Duplicados en la Base de Datos
def verificar_duplicado(tabla, campo, valor):
    conn = conectar_db()
    try:
        query = f"SELECT COUNT(*) FROM {tabla} WHERE {campo} = ?"
        cursor = conn.cursor()
        cursor.execute(query, (valor,))
        resultado = cursor.fetchone()[0]
        return resultado > 0
    finally:
        conn.close()




# 18. Función para obtener marcas únicas desde el catálogo
def obtener_marcas():
    conn = conectar_db()
    try:
        marcas_df = pd.read_sql_query("SELECT DISTINCT marca FROM catalogo ORDER BY marca ASC", conn)
        return marcas_df["marca"].tolist()
    finally:
        conn.close()




# 19. Función para obtener modelos en función de la marca seleccionada
def obtener_modelos(marca_seleccionada):
    conn = conectar_db()
    try:
        modelos_df = pd.read_sql_query(
            "SELECT DISTINCT modelo FROM catalogo WHERE marca = ? ORDER BY modelo ASC", 
            conn, params=(marca_seleccionada,))
        return modelos_df["modelo"].tolist()
    finally:
        conn.close()




# 20. Función para obtener clientes
def obtener_clientes():
    return ["Cliente A", "Cliente B", "Cliente C"]




# 21. Función para Exportar Datos en Formato Excel
def exportar_a_excel(tabla, nombre_archivo):
    conn = conectar_db()
    try:
        # Leer los datos de la tabla especificada
        query = f"SELECT * FROM {tabla}"
        df = pd.read_sql_query(query, conn)

        # Exportar los datos a un archivo Excel
        df.to_excel(nombre_archivo, index=False, engine='openpyxl')
        return f"Archivo {nombre_archivo} generado correctamente."
    finally:
        conn.close()




# 22. Validación para Consolidar Datos en el Dashboard
# Validacion para evitar duplicados
def consolidar_datos_dashboard():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dashboard_data")
    cursor.execute("""
        INSERT INTO dashboard_data (fecha, datacenter, accion, cantidad)
        SELECT fecha_ingreso, datacenter, 'Ingreso', COUNT(*)
        FROM solicitudes_ingreso
        GROUP BY fecha_ingreso, datacenter
    """)
    cursor.execute("""
        INSERT INTO dashboard_data (fecha, datacenter, accion, cantidad)
        SELECT fecha_egreso, datacenter, 'Egreso', COUNT(*)
        FROM solicitudes_egreso
        GROUP BY fecha_egreso, datacenter
    """)
    cursor.execute("""
        INSERT INTO dashboard_data (fecha, datacenter, accion, cantidad)
        SELECT fecha_movimiento, datacenter_origen, 'Movimiento Interno', COUNT(*)
        FROM movimientos_internos
        GROUP BY fecha_movimiento, datacenter_origen
    """)
    conn.commit()
    conn.close()




# 23. Función para Registrar Cambios en el Historial
def registrar_cambio(usuario, accion, descripcion):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO historial_cambios (usuario, accion, descripcion)
        VALUES (?, ?, ?)
    """, (usuario, accion, descripcion))
    conn.commit()
    conn.close()




# 24. Verificación del Estado de Sesión
# Verificar si el usuario ha iniciado sesión
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False  # Estado inicial: no autenticado




# 25. Pantalla de Login
if not st.session_state.get("logged_in", False):  # Verifica si el usuario ha iniciado sesión
    st.title("Checklist de Data Center")
    st.subheader("Inicio de sesión")

    # Entradas de usuario para login
    correo = st.text_input("Correo electrónico:")
    contrasena = st.text_input("Contraseña:", type="password")

    if st.button("Iniciar sesión"):
        try:
            # Conexión con la base de datos
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("SELECT rol FROM usuarios WHERE correo = ? AND contrasena = ?", (correo, contrasena))
            resultado = cursor.fetchone()
            conn.close()

            # Validar credenciales
            if resultado:
                # Limpia cualquier estado previo y actualiza la sesión
                st.session_state.clear()
                st.session_state["rol"] = resultado[0]
                st.session_state["logged_in"] = True
                st.success(f"¡Bienvenido! Rol: {resultado[0]} ")

                # Actualizar la URL mediante JavaScript
                script = f"""
                <script>
                const queryParams = new URLSearchParams(window.location.search);
                queryParams.set("logged_in", "true");
                queryParams.set("rol", "{st.session_state['rol']}");
                window.history.replaceState(null, null, "?" + queryParams.toString());
                </script>
                """
                st.markdown(script, unsafe_allow_html=True)
            else:
                st.error("Credenciales incorrectas. Intenta nuevamente.")
        except sqlite3.Error as e:
            st.error(f"Error al conectar con la base de datos: {e}")
        except Exception as e:
            st.error(f"Ha ocurrido un error inesperado: {e}")
else:
    st.title("Checklist de Data Center")
    st.write("Ya has iniciado sesión. Usa el menú para continuar.")




# 26. Menú Lateral (Según Rol del Usuario)
# Menú lateral con acciones según rol
if st.session_state.get("logged_in", False):  # Confirmar autenticación
    st.sidebar.image("logo.png", use_container_width=True)
    if st.session_state["rol"] == "Administrador":
        st.session_state["opcion_seleccionada"] = st.sidebar.selectbox(
            "Seleccione una acción:",
            [
                "Dashboard General",
                "Ingresos",
                "Egresos",
                "Movimientos Internos",
                "Historial de Cambios",
                "Gestión de Usuarios",
                "Gestión de Registros",
                "Gestión de Solicitudes"
            ]
        )
    elif st.session_state["rol"] == "Tecnico":
        st.session_state["opcion_seleccionada"] = st.sidebar.selectbox(
            "Seleccione una acción:",
            ["Ingresos", "Egresos", "Movimientos Internos"]
        )
    elif st.session_state["rol"] == "Invitado":
        st.session_state["opcion_seleccionada"] = st.sidebar.selectbox(
            "Seleccione una acción:",
            ["Ingresos", "Egresos"]
        )
    else:
        st.sidebar.warning("No tienes permisos para ver el menú.")
        st.session_state["opcion_seleccionada"] = None
else:
    st.sidebar.warning("Inicia sesión para acceder a las opciones.")
    st.session_state["opcion_seleccionada"] = None




# 27. Funcionalidad del Botón de Logout
# Botón de Logout
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.clear()  # Limpia todas las variables de sesión
    st.success("Has cerrado sesión correctamente.")

    # Recargar la página para reflejar el estado inicial
    script = """
    <script>
    const queryParams = new URLSearchParams(window.location.search);
    queryParams.delete("logged_in");
    queryParams.delete("rol");
    window.history.replaceState(null, null, "?" + queryParams.toString());
    location.reload();
    </script>
    """
    st.markdown(script, unsafe_allow_html=True)




# 28. Mostrar contenido según la opción seleccionada - Condición Dashboard General
opcion_seleccionada = st.session_state.get("opcion_seleccionada")
if opcion_seleccionada == "Dashboard General" and st.session_state["rol"] == "Administrador":
    st.header("📊 Dashboard General")

    # Filtros Dinámicos
    fecha_inicio = st.date_input("Fecha de inicio", value=date.today())
    fecha_fin = st.date_input("Fecha de fin", value=date.today() + timedelta(days=7))
    datacenter_filter = st.selectbox("DataCenter", ["Todos", "Providencia", "San Bernardo", "Ascentys", "Bodega"])
    accion_filter = st.selectbox("Tipo de Acción", ["Todas", "Ingreso", "Egreso", "Movimiento Interno"])

    # Actualiza la tabla consolidada
    consolidar_datos_dashboard()

    # Validar que las fechas sean válidas
    if not fecha_inicio or not fecha_fin:
        st.error("Por favor, seleccione fechas válidas.")
    else:
        # Convertir fechas a formato ISO
        fecha_inicio_str = fecha_inicio.strftime('%Y-%m-%d')
        fecha_fin_str = fecha_fin.strftime('%Y-%m-%d')

        # Consulta SQL con filtros
        query = """
            SELECT fecha, datacenter, accion, cantidad
            FROM dashboard_data
            WHERE fecha BETWEEN ? AND ?
        """
        params = [fecha_inicio_str, fecha_fin_str]
        if datacenter_filter != "Todos":
            query += " AND datacenter = ?"
            params.append(datacenter_filter)
        if accion_filter != "Todas":
            query += " AND accion = ?"
            params.append(accion_filter)

        # Realizar la consulta
        conn = conectar_db()
        datos_dashboard = pd.read_sql_query(query, conn, params=params)
        conn.close()

        # Convertir columna "fecha" a formato datetime
        datos_dashboard["fecha"] = pd.to_datetime(datos_dashboard["fecha"], errors="coerce")

        # Verificar y manejar fechas inválidas
        if datos_dashboard["fecha"].isnull().any():
            st.warning("Se encontraron valores de fecha inválidos que se ignorarán.")

        # Mostrar los resultados
        if datos_dashboard.empty:
            st.info("No hay datos disponibles para los filtros seleccionados.")
        else:
            st.write("Datos obtenidos de la consulta:", datos_dashboard)

            # Mostrar métricas generales
            st.subheader("Métricas Generales")
            total_ingresos = datos_dashboard[datos_dashboard["accion"] == "Ingreso"]["cantidad"].sum()
            total_egresos = datos_dashboard[datos_dashboard["accion"] == "Egreso"]["cantidad"].sum()
            total_movimientos = datos_dashboard[datos_dashboard["accion"] == "Movimiento Interno"]["cantidad"].sum()

            st.metric("Total de ingresos", total_ingresos)
            st.metric("Total de egresos", total_egresos)
            st.metric("Total de movimientos internos", total_movimientos)

            # Gráficos interactivos
            # Gráfico de barras por DataCenter
            grafico_datacenters = datos_dashboard.groupby("datacenter")["cantidad"].sum()
            fig_bar = px.bar(
                grafico_datacenters.reset_index(),
                x="datacenter",
                y="cantidad",
                title="Cantidad por DataCenter",
                color="datacenter",  # Agrupar colores por DataCenter
                color_discrete_map={
                    "Providencia": "#800080",  # Morado
                    "San Bernardo": "#0000FF",  # Azul
                    "Ascentys": "#FFA500",  # Naranjo
                    "Bodega": "#FFFF00"  # Amarillo
                },
                template="plotly_white"  # Fondo blanco
            )
            fig_bar.update_layout(
                plot_bgcolor="#F5F5F5",  # Fondo gris claro
                paper_bgcolor="#F5F5F5",  # Fondo gris claro para todo el gráfico
                font=dict(color="#000000"),  # Cambiar texto general a color negro
                title_font=dict(color="#000000"),  # Color negro para el título
                xaxis=dict(
                    title_font=dict(color="#000000"),  # Título del eje X en negro
                    tickfont=dict(color="#000000"),  # Valores del eje X en negro
                    gridcolor="#D3D3D3",  # Líneas divisoras en gris claro
                    zerolinecolor="#D3D3D3"  # Línea cero en gris claro
                ),
                yaxis=dict(
                    title_font=dict(color="#000000"),  # Título del eje Y en negro
                    tickfont=dict(color="#000000"),  # Valores del eje Y en negro
                    gridcolor="#D3D3D3",  # Líneas divisoras en gris claro
                    zerolinecolor="#D3D3D3"  # Línea cero en gris claro
                ),
                legend=dict(font=dict(color="#000000"))  # Color negro para la leyenda
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # Gráfico de pie por Acción
            grafico_acciones = datos_dashboard.groupby("accion")["cantidad"].sum()
            fig_pie = px.pie(
                grafico_acciones.reset_index(),
                names="accion",
                values="cantidad",
                title="Distribución de Acciones",
                color="accion",
                color_discrete_map={
                    "Ingreso": "#2E8B57",  # Verde para ingresos
                    "Egreso": "#FF4136",   # Rojo para egresos
                    "Movimiento Interno": "#FFD700"  # Amarillo para movimientos internos
                },
                template="plotly_white"  # Fondo blanco
            )
            fig_pie.update_layout(
                plot_bgcolor="#F5F5F5",  # Fondo gris claro
                paper_bgcolor="#F5F5F5",  # Fondo gris claro para todo el gráfico
                font=dict(color="#000000"),  # Cambiar texto general a color negro
                title_font=dict(color="#000000"),  # Color negro para el título
                legend=dict(font=dict(color="#000000"))  # Color negro para la leyenda
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            # Exportación de datos a CSV
            st.subheader("Exportar Datos")
            st.download_button(
                label="Descargar Dashboard CSV",
                data=datos_dashboard.to_csv(index=False),
                file_name="dashboard_data.csv",
                mime="text/csv"
            )

    # **Visualizar Datos**
    st.subheader("Visualizar datos")
    if st.checkbox("Visualizar datos"):
        tabla_seleccionada = st.selectbox("Seleccione la tabla para analizar:", ["solicitudes_ingreso", "solicitudes_egreso", "movimientos_internos"])
        conn = conectar_db()
        try:
            # Cargar los datos de la tabla seleccionada
            query = f"SELECT * FROM {tabla_seleccionada}"
            df = pd.read_sql_query(query, conn)

            # Mostrar los datos en una tabla interactiva
            st.subheader(f"Tabla: {tabla_seleccionada}")
            st.dataframe(df)

            # Generar gráficos específicos
            if tabla_seleccionada == "solicitudes_ingreso":
                st.subheader("Análisis de Ingresos")
                grafico_ingresos = df["datacenter"].value_counts()
                st.bar_chart(grafico_ingresos)

            elif tabla_seleccionada == "solicitudes_egreso":
                st.subheader("Análisis de Egresos")
                grafico_egresos = df["motivo_egreso"].value_counts()
                st.bar_chart(grafico_egresos)

            elif tabla_seleccionada == "movimientos_internos":
                st.subheader("Análisis de Movimientos Internos")
                grafico_movimientos = df["datacenter_origen"].value_counts()
                st.bar_chart(grafico_movimientos)
        finally:
            conn.close()

    # **Gestión de Registros**
    st.subheader("Gestión de registros")
    if st.checkbox("Gestión de registros"):
        tabla_seleccionada = st.selectbox("Seleccione la tabla para gestionar:", ["solicitudes_ingreso", "solicitudes_egreso", "movimientos_internos"])
        conn = conectar_db()
        try:
            # Cargar los datos de la tabla seleccionada
            query = f"SELECT * FROM {tabla_seleccionada}"
            df = pd.read_sql_query(query, conn)
            st.subheader("Registros disponibles")
            st.dataframe(df)

            # Buscar registros
            st.subheader("Buscar registros")
            campo_busqueda = st.selectbox("Seleccione el campo para buscar:", df.columns)
            valor_busqueda = st.text_input("Ingrese el valor para buscar:")
            if st.button("Buscar"):
                resultados = df[df[campo_busqueda].astype(str).str.contains(valor_busqueda, case=False, na=False)]
                if not resultados.empty:
                    st.write("Resultados encontrados:")
                    st.dataframe(resultados)
                else:
                    st.warning("No se encontraron registros con ese criterio.")

            # Editar registros
            st.subheader("Editar registros")
            id_registro = st.number_input("Ingrese el ID del registro que desea editar:", min_value=1, step=1)
            columna_editar = st.selectbox("Seleccione la columna que desea editar:", df.columns)
            nuevo_valor = st.text_input("Ingrese el nuevo valor:")
            if st.button("Guardar cambios"):
                cursor = conn.cursor()
                cursor.execute(f"UPDATE {tabla_seleccionada} SET {columna_editar} = ? WHERE id = ?", (nuevo_valor, id_registro))
                conn.commit()
                st.success("Registro actualizado correctamente.")

            # Eliminar registros
            st.subheader("Eliminar registros")
            id_eliminar = st.number_input("Ingrese el ID del registro que desea eliminar:", min_value=1, step=1)
            if st.button("Eliminar"):
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {tabla_seleccionada} WHERE id = ?", (id_eliminar,))
                conn.commit()
                st.success("Registro eliminado correctamente.")
        finally:
            conn.close()

    # **Generar Reportes**
    st.subheader("Generar reporte")
    if st.checkbox("Generar reporte"):
        tabla_seleccionada = st.selectbox("Seleccione la tabla para exportar:", ["solicitudes_ingreso", "solicitudes_egreso", "movimientos_internos"])
        nombre_archivo = st.text_input("Nombre del archivo Excel (ejemplo: reporte.xlsx):")

        if st.button("Exportar"):
            if nombre_archivo:
                resultado = exportar_a_excel(tabla_seleccionada, nombre_archivo)
                st.success(resultado)
            else:
                st.error("Por favor, ingrese un nombre de archivo.")




# 29. Mostrar contenido según la opción seleccionada - Condicion Ingresos
elif opcion_seleccionada == "Ingresos" and st.session_state["rol"] in ["Administrador", "Tecnico"]:
    st.header("📥 Checklist de Ingreso")

    # Mostrar filtros y gestión avanzada solo para administradores
    if rol_usuario == "Administrador":
        st.subheader("Filtros (Solo Administradores)")
        fecha_inicio = st.date_input("Fecha de inicio")
        fecha_fin = st.date_input("Fecha de fin")
        data_center_filter = st.selectbox("Filtrar por DataCenter", ["Todos", "Providencia", "San Bernardo", "Ascentys", "Bodega"])
        solicitante_filter = st.text_input("Filtrar por nombre del solicitante (opcional)")
        
        # Filtro por marca y modelo desde el catálogo
        marca_filter = st.selectbox("Filtrar por Marca (opcional)", ["Todos"] + obtener_marcas())
        modelo_filter = st.selectbox("Filtrar por Modelo (opcional)", ["Todos"] + obtener_modelos(marca_filter) if marca_filter != "Todos" else ["Todos"])

        # Consulta con filtros
        conn = conectar_db()
        query = """
            SELECT * FROM solicitudes_ingreso
            WHERE fecha_ingreso BETWEEN ? AND ?
        """
        params = [fecha_inicio, fecha_fin]
        if data_center_filter != "Todos":
            query += " AND datacenter = ?"
            params.append(data_center_filter)
        if solicitante_filter:
            query += " AND LOWER(TRIM(solicitante)) LIKE ?"
            params.append(f"%{solicitante_filter.strip().lower()}%")
        if marca_filter != "Todos":
            query += " AND marca = ?"
            params.append(marca_filter)
        if modelo_filter != "Todos":
            query += " AND modelo = ?"
            params.append(modelo_filter)

        # Ejecutar consulta
        datos_filtrados = pd.read_sql_query(query, conn, params=params)
        conn.close()

        st.subheader("Resultados Filtrados")
        st.dataframe(datos_filtrados)

        # Exportación de datos filtrados en CSV
        st.subheader("Exportar Datos Filtrados")
        if not datos_filtrados.empty:
            st.download_button(
                label="Descargar Ingresos Filtrados CSV",
                data=datos_filtrados.to_csv(index=False),
                file_name="ingresos_filtrados.csv",
                mime="text/csv"
            )
        else:
            st.info("No hay datos para exportar con los filtros seleccionados.")


        #st.markdown("---")
        st.markdown(
    """
    <hr style="border: 1px solid #4F4F4F; margin: 25px 0;">
    """,
    unsafe_allow_html=True
)
        st.subheader("Gestión Avanzada (Solo Administradores)")

        # Exportar todos los datos en CSV
        def exportar_csv_ingresos():
            conn = conectar_db()
            df = pd.read_sql_query("SELECT * FROM solicitudes_ingreso", conn)
            conn.close()
            return df

        if st.button("Descargar todos los ingresos en CSV"):
            datos_csv_ingresos = exportar_csv_ingresos()
            st.download_button(
                label="Descargar Ingresos CSV (Todos)",
                data=datos_csv_ingresos.to_csv(index=False),
                file_name="solicitudes_ingreso.csv",
                mime="text/csv"
            )

        # Visualizar todos los registros
        conn = conectar_db()
        df_ingresos = pd.read_sql_query("SELECT * FROM solicitudes_ingreso", conn)
        conn.close()
        st.subheader("Visualizar todos los registros")
        st.dataframe(df_ingresos)

    # Línea divisoria para separar filtros de solicitudes
    #st.markdown("---")
    st.markdown(
    """
    <hr style="border: 1px solid #4F4F4F; margin: 25px 0;">
    """,
    unsafe_allow_html=True
)


    # Encabezado para nueva solicitud de ingreso (visible para técnicos y administradores)
    if rol_usuario in ["Administrador", "Tecnico"]:
        st.header("📄 Nueva Solicitud de Ingreso")

        # Obtener el correo del usuario logueado desde la sesión
        solicitante = st.session_state.get("login_email", "")
        if not solicitante:
            st.error("No se pudo identificar el correo del solicitante. Por favor, inicia sesión nuevamente.")
            st.stop()  # Detener ejecución si no se encontró el correo

        # Mostrar el correo del usuario logueado (no editable)
        st.text(f"Solicitante (correo): {solicitante}")

        # Resto del formulario
        fecha_ingreso = st.date_input("Fecha de ingreso:", key="fecha_ingreso_unique")
        cliente = st.selectbox("Seleccione el cliente:", obtener_clientes(), key="cliente_ingreso_unique")
        datacenter = st.selectbox("Seleccione el DataCenter:", ["Providencia", "San Bernardo", "Ascentys", "Bodega"],
                                key="datacenter_ingreso_unique")
        ticket = st.text_input("Ticket asociado (o 'Pendiente' si no existe):", key="ticket_ingreso_unique")
        cantidad_equipos = st.number_input("Cantidad de equipos a ingresar:", min_value=1, step=1,
                                            key="cantidad_equipos_ingreso_unique")
        # Campos dinámicos para cada equipo
        equipos = []
        for i in range(1, cantidad_equipos + 1):
            st.subheader(f"Equipo {i}")
            marca = st.selectbox(f"Marca del equipo {i}:", ["Seleccionar"] + obtener_marcas(),
                                key=f"marca_equipo_{i}_unique")
            modelo = st.selectbox(
                f"Modelo del equipo {i}:",
                ["Seleccionar"] + obtener_modelos(marca) if marca != "Seleccionar" else ["Seleccionar"],
                key=f"modelo_equipo_{i}_unique"
            )
            numero_serie = st.text_input(f"Número de serie del equipo {i}:", key=f"serie_equipo_{i}_unique")
            equipos.append({"marca": marca, "modelo": modelo, "serie": numero_serie})
        
        # Validación de duplicados y campos obligatorios
        numeros_serie = [equipo["serie"] for equipo in equipos]
        if len(numeros_serie) != len(set(numeros_serie)):
            st.error("Hay números de serie duplicados en los equipos. Verifique e intente nuevamente.")
        elif not fecha_ingreso or not cliente or not datacenter:
            st.error("Todos los campos obligatorios deben ser completados.")
        elif not all(e["marca"] != "Seleccionar" and e["modelo"] != "Seleccionar" for e in equipos):
            st.error("Por favor, seleccione una marca y modelo válidos para todos los equipos.")
        else:
            if st.button("Guardar solicitud de ingreso", key="guardar_ingreso_unique"):
                if all(e["serie"] for e in equipos):  # Verificar que todos tengan un número de serie
                    conn = conectar_db()
                    try:
                        cursor = conn.cursor()
                        for equipo in equipos:
                            fecha_ingreso_iso = fecha_ingreso.strftime('%Y-%m-%d %H:%M:%S')
                            cursor.execute("""
                                INSERT INTO solicitudes_ingreso (
                                    solicitante, fecha_ingreso, cliente, datacenter, ticket, cantidad_equipos, marca, modelo, numero_serie, estado
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (solicitante, fecha_ingreso_iso, cliente, datacenter, ticket, cantidad_equipos,
                                equipo["marca"], equipo["modelo"], equipo["serie"], "Pendiente"))
                        conn.commit()
                        # Consolidar datos y registrar el cambio, etc.
                        consolidar_datos_dashboard()
                        descripcion_cambio = f"Solicitud de ingreso creada por {solicitante}. Total de equipos: {cantidad_equipos}."
                        registrar_cambio(usuario=solicitante, accion="Creación", descripcion=descripcion_cambio)
                        st.success("¡Solicitud de ingreso guardada correctamente!")
                        # Opcional: envío de correo de notificación
                        mensaje = f"""
                        Hola equipo,
                        
                        Se ha registrado una nueva solicitud de ingreso con los siguientes detalles:
                        - Solicitante: {solicitante}
                        - Fecha de ingreso: {fecha_ingreso.strftime('%d/%m/%Y')}
                        - Cliente: {cliente}
                        - DataCenter: {datacenter}
                        - Ticket: {ticket}
                        - Cantidad de equipos: {cantidad_equipos}
                        
                        Por favor, revisen esta solicitud y confirmen su procesamiento.
                        
                        Saludos cordiales,
                        El equipo de registro de ingresos
                        """
                        destinatarios = ["roberto.chavez@kyndryl.com", "deyanira.cerda@kyndryl.com"]
                        if enviar_correo(destinatarios, "Nueva solicitud de ingreso registrada", mensaje):
                            st.success("Correos de notificación enviados correctamente a los destinatarios.")
                        else:
                            st.error("Error al enviar los correos de notificación.")
                    except sqlite3.Error as e:
                        st.error(f"Error al guardar los datos en la base de datos: {e}")
                    finally:
                        conn.close()




# 30. Mostrar contenido según la opción seleccionada - Condicion Egresos
elif opcion_seleccionada == "Egresos" and st.session_state["rol"] in ["Administrador", "Tecnico"]:
    st.header("📤 Checklist de Egreso")

    # Mostrar filtros y gestión avanzada solo para administradores
    if rol_usuario == "Administrador":
        st.subheader("Filtros (Solo Administradores)")
        fecha_inicio = st.date_input("Fecha de inicio")
        fecha_fin = st.date_input("Fecha de fin")
        datacenter_filter = st.selectbox("Filtrar por DataCenter", ["Todos", "Providencia", "San Bernardo", "Ascentys", "Bodega"])
        solicitante_filter = st.text_input("Filtrar por nombre del solicitante (opcional)")

        # Filtro por marca y modelo desde el catálogo
        marca_filter = st.selectbox("Filtrar por Marca (opcional)", ["Todos"] + obtener_marcas())
        modelo_filter = st.selectbox("Filtrar por Modelo (opcional)", ["Todos"] + obtener_modelos(marca_filter) if marca_filter != "Todos" else ["Todos"])

        # Consulta con filtros
        conn = conectar_db()
        query = """
            SELECT * FROM solicitudes_egreso
            WHERE fecha_egreso BETWEEN ? AND ?
        """
        params = [fecha_inicio, fecha_fin]
        if datacenter_filter != "Todos":
            query += " AND datacenter = ?"
            params.append(datacenter_filter)
        if solicitante_filter:
            query += " AND LOWER(TRIM(solicitante)) LIKE ?"
            params.append(f"%{solicitante_filter.strip().lower()}%")
        if marca_filter != "Todos":
            query += " AND marca = ?"
            params.append(marca_filter)
        if modelo_filter != "Todos":
            query += " AND modelo = ?"
            params.append(modelo_filter)

        # Ejecutar consulta
        datos_filtrados = pd.read_sql_query(query, conn, params=params)
        conn.close()

        st.subheader("Resultados Filtrados")
        st.dataframe(datos_filtrados)

        # Exportación de datos filtrados en CSV
        st.subheader("Exportar Datos Filtrados")
        if not datos_filtrados.empty:
            st.download_button(
                label="Descargar Egresos Filtrados CSV",
                data=datos_filtrados.to_csv(index=False),
                file_name="egresos_filtrados.csv",
                mime="text/csv"
            )
        else:
            st.info("No hay datos para exportar con los filtros seleccionados.")

        #st.markdown("---")
        st.markdown(
    """
    <hr style="border: 1px solid #4F4F4F; margin: 25px 0;">
    """,
    unsafe_allow_html=True
)
        st.subheader("Gestión Avanzada (Solo Administradores)")

        # Exportar todos los datos en CSV
        def exportar_csv_egresos():
            conn = conectar_db()
            df = pd.read_sql_query("SELECT * FROM solicitudes_egreso", conn)
            conn.close()
            return df

        if st.button("Descargar todos los egresos en CSV"):
            datos_csv_egresos = exportar_csv_egresos()
            st.download_button(
                label="Descargar Egresos CSV (Todos)",
                data=datos_csv_egresos.to_csv(index=False),
                file_name="solicitudes_egreso.csv",
                mime="text/csv"
            )

        # Visualizar todos los registros
        conn = conectar_db()
        df_egresos = pd.read_sql_query("SELECT * FROM solicitudes_egreso", conn)
        conn.close()
        st.subheader("Visualizar todos los registros")
        st.dataframe(df_egresos)

    # Línea divisoria para separar filtros de solicitudes
    #st.markdown("---")
    st.markdown(
    """
    <hr style="border: 1px solid #4F4F4F; margin: 25px 0;">
    """,
    unsafe_allow_html=True
)

    # Encabezado para nueva solicitud de egreso (visible para técnicos y administradores)
    if rol_usuario in ["Administrador", "Tecnico"]:
        st.header("📄 Nueva Solicitud de Egreso")

        
        # Formulario de Solicitud
        # Obtener el correo del usuario logueado desde la sesión
        solicitante = st.session_state.get("login_email", "")
        if not solicitante:
            st.error("No se pudo identificar el correo del solicitante. Por favor, inicia sesión nuevamente.")
            st.stop()
        st.text(f"Solicitante (correo): {solicitante}")
        
        # Resto del formulario para egreso:
        fecha_egreso = st.date_input("Fecha de egreso:", key="fecha_egreso_unique")
        datacenter_egreso = st.selectbox(
            "Seleccione el DataCenter de egreso:",
            ["Providencia", "San Bernardo", "Ascentys", "Bodega"], key="datacenter_egreso_unique"
        )
        ticket_egreso = st.text_input("Ticket asociado (o 'Pendiente' si no existe):", key="ticket_egreso_unique")
        cantidad_equipos = st.number_input("Cantidad de equipos a egresar:", min_value=1, step=1, key="cantidad_equipos_egreso_unique")

         # Campos dinámicos para cada equipo en egreso
        equipos = []
        for i in range(1, cantidad_equipos + 1):
            st.subheader(f"Equipo {i}")

            # Buscadores dinámicos de marca y modelo conectados al catálogo
            marca = st.selectbox(f"Marca del equipo {i}:", ["Seleccionar"] + obtener_marcas(), key=f"marca_egreso_{i}_unique")
            modelo = st.selectbox(
                f"Modelo del equipo {i}:",
                ["Seleccionar"] + obtener_modelos(marca) if marca != "Seleccionar" else ["Seleccionar"],
                key=f"modelo_egreso_{i}_unique"
            )
            numero_serie = st.text_input(f"Número de serie del equipo {i}:", key=f"serie_egreso_{i}_unique")
            rack_origen = st.text_input(f"Rack de origen del equipo {i}:", key=f"rack_egreso_{i}_unique")
            motivo_egreso = st.selectbox(f"Motivo del egreso (Equipo {i}):", ["Desinstalación", "Traslado", "Otro"], key=f"motivo_egreso_{i}_unique")
            estado_salida = st.selectbox(f"Estado del equipo al salir (Equipo {i}):", ["Funcional", "Dañado"], key=f"estado_egreso_{i}_unique")

            equipos.append({
                "marca": marca,
                "modelo": modelo,
                "serie": numero_serie,
                "rack_origen": rack_origen,
                "motivo_egreso": motivo_egreso,
                "estado_salida": estado_salida
            })

        # Validación de duplicados en los números de serie
        numeros_serie = [equipo["serie"] for equipo in equipos]
        if len(numeros_serie) != len(set(numeros_serie)):
            st.error("Hay números de serie duplicados en los equipos. Verifique e intente nuevamente.")

        # Validación de campos obligatorios
        if not solicitante or not fecha_egreso or not datacenter_egreso or not ticket_egreso:
            st.error("Todos los campos obligatorios deben ser completados.")
        elif not all(e["marca"] != "Seleccionar" and e["modelo"] != "Seleccionar" for e in equipos):
            st.error("Por favor, seleccione una marca y modelo válidos para todos los equipos.")
        else:
            
            # Confirmación antes de guardar
            if st.button("Guardar solicitud de egreso", key="guardar_egreso_unique"):
                if all(e["serie"] for e in equipos):  # Verificar que todos los equipos tengan número de serie
                    conn = conectar_db()
                    try:
                        cursor = conn.cursor()
                        
                        # Convertir la fecha a formato ISO
                        if isinstance(fecha_egreso, datetime):
                            fecha_egreso_iso = fecha_egreso.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            fecha_egreso_iso = datetime.combine(fecha_egreso, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Inserción de cada equipo en la base de datos
                        for equipo in equipos:
                            cursor.execute("""
                                INSERT INTO solicitudes_egreso (
                                    solicitante, fecha_egreso, datacenter, ticket, marca, modelo, numero_serie, 
                                    rack_origen, motivo_egreso, estado_salida, estado
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (solicitante, fecha_egreso_iso, datacenter_egreso, ticket_egreso, equipo["marca"], 
                                equipo["modelo"], equipo["serie"], equipo["rack_origen"], equipo["motivo_egreso"], 
                                equipo["estado_salida"], "Pendiente"))

                        # Confirmar la operación
                        conn.commit()

                        # Registrar cambio en historial
                        descripcion_cambio = f"Solicitud de egreso creada por {rol_usuario}. Total de equipos: {cantidad_equipos}."
                        registrar_cambio(usuario=rol_usuario, accion="Creación", descripcion=descripcion_cambio)
                        st.success("¡Solicitud de egreso guardada correctamente!")

                        # Enviar correo de notificación
                        mensaje = f"""
                        Hola equipo,

                        Se ha registrado una nueva solicitud de egreso con los siguientes detalles:

                        - Solicitante: {solicitante}
                        - Fecha de egreso: {fecha_egreso.strftime('%d/%m/%Y')}
                        - DataCenter: {datacenter_egreso}
                        - Ticket: {ticket_egreso}
                        - Cantidad de equipos: {cantidad_equipos}

                        Por favor, revisen esta solicitud a la brevedad.

                        Saludos cordiales,
                        El equipo de registro de egresos
                        """
                        destinatarios = ["roberto.chavez@kyndryl.com", "deyanira.cerda@kyndryl.com"]
                        if enviar_correo(destinatarios, "Nueva solicitud de egreso registrada", mensaje):
                            st.success("Correos de notificación enviados correctamente a los destinatarios.")
                        else:
                            st.error("Error al enviar los correos de notificación.")
                    except sqlite3.Error as e:
                        st.error(f"Error al guardar los datos en la base de datos: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("Por favor, complete los números de serie de todos los equipos antes de guardar.")




# 31. Mostrar contenido según la opción seleccionada - Condicion Movimiento Interno
elif opcion_seleccionada == "Movimientos Internos" and st.session_state["rol"] in ["Administrador", "Tecnico"]:
    st.header("🔄 Checklist de Movimientos Internos")

    # Mostrar filtros y gestión avanzada solo para administradores
    if rol_usuario == "Administrador":
        st.subheader("Filtros (Solo Administradores)")
        fecha_inicio = st.date_input("Fecha de inicio")
        fecha_fin = st.date_input("Fecha de fin")
        datacenter_origen_filter = st.selectbox("Filtrar por DataCenter de Origen", ["Todos", "Providencia", "San Bernardo", "Ascentys", "Bodega"])
        datacenter_destino_filter = st.selectbox("Filtrar por DataCenter de Destino", ["Todos", "Providencia", "San Bernardo", "Ascentys", "Bodega"])
        solicitante_filter = st.text_input("Filtrar por nombre del solicitante (opcional)")

        # Filtro por marca y modelo desde el catálogo
        marca_filter = st.selectbox("Filtrar por Marca (opcional)", ["Todos"] + obtener_marcas())
        modelo_filter = st.selectbox("Filtrar por Modelo (opcional)", ["Todos"] + obtener_modelos(marca_filter) if marca_filter != "Todos" else ["Todos"])

        # Consulta con filtros
        conn = conectar_db()
        query = """
            SELECT * FROM movimientos_internos
            WHERE fecha_movimiento BETWEEN ? AND ?
        """
        params = [fecha_inicio, fecha_fin]
        if datacenter_origen_filter != "Todos":
            query += " AND datacenter_origen = ?"
            params.append(datacenter_origen_filter)
        if datacenter_destino_filter != "Todos":
            query += " AND datacenter_destino = ?"
            params.append(datacenter_destino_filter)
        if solicitante_filter:
            query += " AND LOWER(TRIM(solicitante)) LIKE ?"
            params.append(f"%{solicitante_filter.strip().lower()}%")
        if marca_filter != "Todos":
            query += " AND marca = ?"
            params.append(marca_filter)
        if modelo_filter != "Todos":
            query += " AND modelo = ?"
            params.append(modelo_filter)

        # Ejecutar consulta
        datos_filtrados = pd.read_sql_query(query, conn, params=params)
        conn.close()

        st.subheader("Resultados Filtrados")
        st.dataframe(datos_filtrados)

        # Exportación de datos filtrados en CSV
        st.subheader("Exportar Datos Filtrados")
        if not datos_filtrados.empty:
            st.download_button(
                label="Descargar Movimientos Internos Filtrados CSV",
                data=datos_filtrados.to_csv(index=False),
                file_name="movimientos_internos_filtrados.csv",
                mime="text/csv"
            )
        else:
            st.info("No hay datos para exportar con los filtros seleccionados.")

        #st.markdown("---")
        st.markdown(
    """
    <hr style="border: 1px solid #4F4F4F; margin: 25px 0;">
    """,
    unsafe_allow_html=True
)
        st.subheader("Gestión Avanzada (Solo Administradores)")

        # Exportar todos los datos en CSV
        def exportar_csv_movimientos():
            conn = conectar_db()
            df = pd.read_sql_query("SELECT * FROM movimientos_internos", conn)
            conn.close()
            return df

        if st.button("Descargar todos los movimientos internos en CSV"):
            datos_csv_movimientos = exportar_csv_movimientos()
            st.download_button(
                label="Descargar Movimientos Internos CSV (Todos)",
                data=datos_csv_movimientos.to_csv(index=False),
                file_name="movimientos_internos.csv",
                mime="text/csv"
            )

        # Visualizar todos los registros
        conn = conectar_db()
        df_movimientos = pd.read_sql_query("SELECT * FROM movimientos_internos", conn)
        conn.close()
        st.subheader("Visualizar todos los registros")
        st.dataframe(df_movimientos)

    # Línea divisoria para separar filtros de solicitudes
    #st.markdown("---")
    st.markdown(
    """
    <hr style="border: 1px solid #4F4F4F; margin: 25px 0;">
    """,
    unsafe_allow_html=True
)

    # Encabezado para nueva solicitud de movimiento interno (visible para técnicos y administradores)
    if rol_usuario in ["Administrador", "Tecnico"]:
        st.header("📄 Nueva Solicitud de Movimiento Interno")

        # Formulario de Solicitud
        # Obtener el correo del usuario desde la sesión
        solicitante = st.session_state.get("login_email", "")
        if not solicitante:
            st.error("No se pudo identificar el correo del solicitante. Por favor, inicia sesión nuevamente.")
            st.stop()
        st.text(f"Solicitante (correo): {solicitante}")

        fecha_movimiento = st.date_input("Fecha del movimiento:", key="fecha_movimiento_unique")
        ticket_movimiento = st.text_input("Ticket asociado (o 'Pendiente' si no existe):", key="ticket_movimiento_unique")

        datacenter_origen = st.selectbox(
            "Seleccione el DataCenter de origen:",
            ["Providencia", "San Bernardo", "Ascentys", "Bodega"], key="datacenter_origen_unique"
        )
        rack_origen = st.text_input("Rack y ubicación del equipo en el DataCenter de origen:", key="rack_origen_unique")
        datacenter_destino = st.selectbox(
            "Seleccione el DataCenter de destino:",
            ["Providencia", "San Bernardo", "Ascentys", "Bodega"], key="datacenter_destino_unique"
        )
        rack_destino = st.text_input("Rack y ubicación del equipo en el DataCenter de destino:", key="rack_destino_unique")
        cantidad_equipos = st.number_input("Cantidad de equipos a mover:", min_value=1, step=1, key="cantidad_equipos_movimiento_unique")

        equipos = []
        for i in range(1, cantidad_equipos + 1):
            st.subheader(f"Equipo {i}")

            # Buscadores dinámicos de marca y modelo conectados al catálogo
            marca = st.selectbox(f"Marca del equipo {i}:", ["Seleccionar"] + obtener_marcas(), key=f"marca_movimiento_{i}_unique")
            modelo = st.selectbox(
                f"Modelo del equipo {i}:",
                ["Seleccionar"] + obtener_modelos(marca) if marca != "Seleccionar" else ["Seleccionar"],
                key=f"modelo_movimiento_{i}_unique"
            )
            numero_serie = st.text_input(f"Número de serie del equipo {i}:", key=f"serie_movimiento_{i}_unique")
            estado_equipo = st.selectbox(
                f"Estado del equipo antes del movimiento (Equipo {i}):",
                ["Funcional", "Dañado"], key=f"estado_equipo_movimiento_{i}_unique"
            )

            equipos.append({
                "marca": marca,
                "modelo": modelo,
                "serie": numero_serie,
                "estado_equipo": estado_equipo
            })

        # Validación de duplicados en los números de serie
        numeros_serie = [equipo["serie"] for equipo in equipos]
        if len(numeros_serie) != len(set(numeros_serie)):
            st.error("Hay números de serie duplicados en los equipos. Verifique e intente nuevamente.")

        # Validación de campos obligatorios
        if not solicitante or not fecha_movimiento or not ticket_movimiento or not datacenter_origen or not rack_origen or not datacenter_destino or not rack_destino:
            st.error("Todos los campos obligatorios deben ser completados.")
        elif not all(e["marca"] != "Seleccionar" and e["modelo"] != "Seleccionar" for e in equipos):
            st.error("Por favor, seleccione una marca y modelo válidos para todos los equipos.")
        else:
            
            # Confirmación antes de guardar
            if st.button("Guardar solicitud de movimiento interno", key="guardar_movimiento_unique"):
                if all(e["serie"] for e in equipos):  # Verificar que todos los equipos tengan número de serie
                    conn = conectar_db()
                    try:
                        cursor = conn.cursor()
                        
                        # Convertir la fecha de movimiento a formato ISO
                        if isinstance(fecha_movimiento, datetime):
                            fecha_movimiento_iso = fecha_movimiento.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            fecha_movimiento_iso = datetime.combine(fecha_movimiento, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Inserción de cada equipo en la base de datos
                        for equipo in equipos:
                            cursor.execute("""
                                INSERT INTO movimientos_internos (
                                    solicitante, fecha_movimiento, ticket, datacenter_origen, rack_origen,
                                    datacenter_destino, rack_destino, marca, modelo, numero_serie, estado_equipo, estado
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (solicitante, fecha_movimiento_iso, ticket_movimiento, datacenter_origen, rack_origen, 
                                datacenter_destino, rack_destino, equipo["marca"], equipo["modelo"], equipo["serie"], 
                                equipo["estado_equipo"], "Pendiente"))

                        # Confirmar la operación
                        conn.commit()

                        # Registrar cambio en historial
                        descripcion_cambio = f"Solicitud de movimiento interno creada por {rol_usuario}. Total de equipos: {cantidad_equipos}."
                        registrar_cambio(usuario=rol_usuario, accion="Creación", descripcion=descripcion_cambio)
                        st.success("¡Solicitud de movimiento interno guardada correctamente!")

                        # Enviar correo de notificación
                        mensaje = f"""
                        Hola equipo,

                        Se ha registrado una nueva solicitud de Movimiento Interno con los siguientes detalles:

                        - Solicitante: {solicitante}
                        - Fecha del movimiento: {fecha_movimiento.strftime('%d/%m/%Y')}
                        - DataCenter de origen: {datacenter_origen}
                        - Rack origen: {rack_origen}
                        - DataCenter de destino: {datacenter_destino}
                        - Rack destino: {rack_destino}
                        - Cantidad de equipos: {cantidad_equipos}

                        Por favor, revisen esta solicitud a la brevedad.

                        Saludos cordiales,
                        El equipo de registro de movimientos internos
                        """
                        destinatarios = ["roberto.chavez@kyndryl.com", "deyanira.cerda@kyndryl.com"]
                        if enviar_correo(destinatarios, "Nueva solicitud de Movimiento Interno registrada", mensaje):
                            st.success("Correos de notificación enviados correctamente a los destinatarios.")
                        else:
                            st.error("Error al enviar los correos de notificación.")
                    except sqlite3.Error as e:
                        st.error(f"Error al guardar los datos en la base de datos: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("Por favor, complete los números de serie de todos los equipos antes de guardar.")




# 32. Mostrar contenido según la opción seleccionada - Condicion Historial de cambios
elif opcion_seleccionada == "Historial de Cambios" and st.session_state["rol"] == "Administrador":
    st.header("📜 Historial de Cambios")
    #elif opcion_seleccionada == "Historial de Cambios":
     #   if st.session_state.get("rol") == "Administrador":
           # st.header("📜 Historial de Cambios")
            
    # Filtros para el historial
    st.subheader("Filtros")
    fecha_inicio = st.date_input("Fecha de inicio")
    fecha_fin = st.date_input("Fecha de fin")
    usuario_filter = st.text_input("Filtrar por usuario (opcional)")
    accion_filter = st.selectbox("Acción", ["Todas", "Creación", "Actualización", "Eliminación"])

    # Consulta con filtros
    conn = conectar_db()
    query = """
        SELECT fecha, usuario, accion, descripcion
        FROM historial_cambios
        WHERE fecha BETWEEN ? AND ?
    """
    params = [fecha_inicio, fecha_fin]
    if usuario_filter:
        query += " AND usuario LIKE ?"
        params.append(f"%{usuario_filter}%")
    if accion_filter != "Todas":
        query += " AND accion = ?"
        params.append(accion_filter)

    historial = pd.read_sql_query(query, conn, params=params)
    conn.close()

    # Mostrar el historial
    st.subheader("Resultados")
    if not historial.empty:
        st.dataframe(historial)

        # Exportar el historial en CSV
        st.subheader("Exportar Datos")
        st.download_button(
            label="Descargar Historial CSV",
            data=historial.to_csv(index=False),
            file_name="historial_cambios.csv",
            mime="text/csv"
        )

        # Generar Reporte en PDF
        if st.button("Generar Reporte en PDF"):
            from fpdf import FPDF

            class PDF(FPDF):
                def header(self):
                    self.set_font("Arial", "B", 12)
                    self.cell(0, 10, "Historial de Cambios", 0, 1, "C")
                    self.ln(10)

                def footer(self):
                    self.set_y(-15)
                    self.set_font("Arial", "I", 8)
                    self.cell(0, 10, f"Página {self.page_no()}", 0, 0, "C")

            pdf = PDF()
            pdf.add_page()
            pdf.set_font("Arial", size=10)

            # Agregar rango de fechas al reporte
            pdf.cell(0, 10, f"Filtrado desde {fecha_inicio} hasta {fecha_fin}", ln=True)
            pdf.ln(5)

            # Agregar cada registro del historial al PDF
            for index, row in historial.iterrows():
                pdf.cell(0, 10, f"{row['fecha']} - {row['usuario']} - {row['accion']}: {row['descripcion']}", ln=True)

            # Guardar el reporte
            pdf_file = "historial_cambios.pdf"
            pdf.output(pdf_file)

            # Botón para descargar el PDF
            with open(pdf_file, "rb") as f:
                st.download_button(
                    label="Descargar Historial PDF",
                    data=f,
                    file_name="historial_cambios.pdf",
                    mime="application/pdf"
                )
    else:
        st.info("No hay datos disponibles para los filtros seleccionados.")




# 33. Mostrar contenido según la opción seleccionada - Condicion Gestion de Usuarios
elif opcion_seleccionada == "Gestión de Usuarios" and st.session_state["rol"] == "Administrador":
    st.header("👤 Gestión de Usuarios")
    #elif opcion_seleccionada == "Gestión de Usuarios":
     #   if st.session_state.get("rol") == "Administrador":
      #      st.header("👤 Gestión de Usuarios")
            
    # Crear Nuevo Usuario
    st.subheader("Crear Nuevo Usuario")
    nuevo_usuario = st.text_input("Correo Electrónico:")
    nuevo_nombre = st.text_input("Nombre Completo:")
    nuevo_rol = st.selectbox("Rol:", ["Administrador", "Tecnico", "Invitado"])
    nueva_contrasena = st.text_input("Contraseña:", type="password")
    
    if st.button("Crear Usuario"):
        if not nuevo_usuario or not nuevo_nombre or not nueva_contrasena:
            st.error("Todos los campos son obligatorios.")
        else:
            conn = conectar_db()
            cursor = conn.cursor()
            # Validar si el correo ya está registrado
            cursor.execute("SELECT 1 FROM usuarios WHERE correo = ?", (nuevo_usuario,))
            if cursor.fetchone():
                st.error("El correo ya está registrado. Intenta con otro.")
            else:
                # Cifrar la contraseña
                hashed = bcrypt.hashpw(nueva_contrasena.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                try:
                    # Insertar el nuevo usuario
                    cursor.execute("""
                        INSERT INTO usuarios (correo, nombre, rol, contrasena)
                        VALUES (?, ?, ?, ?)
                    """, (nuevo_usuario, nuevo_nombre, nuevo_rol, hashed))
                    conn.commit()
                    st.success(f"Usuario {nuevo_nombre} creado exitosamente.")
                except Exception as e:
                    st.error(f"Error al crear el usuario: {e}")
                finally:
                    conn.close()

    # Listar Usuarios Existentes
    st.subheader("Lista de Usuarios Existentes")
    conn = conectar_db()
    usuarios = pd.read_sql_query("SELECT id, correo, nombre, rol FROM usuarios", conn)
    conn.close()
    st.dataframe(usuarios)

    # Editar Usuario
    st.subheader("Editar Usuario")
    usuario_seleccionado = st.selectbox("Seleccione un usuario para editar:", usuarios["correo"])

    nuevo_rol = st.selectbox("Nuevo Rol:", ["Administrador", "Tecnico", "Invitado"])
    nueva_contrasena = st.text_input("Nueva Contraseña (opcional):", type="password")

    if st.button("Actualizar Usuario"):
        conn = conectar_db()
        cursor = conn.cursor()
        try:
            if nueva_contrasena:
                hashed = bcrypt.hashpw(nueva_contrasena.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute("""
                    UPDATE usuarios
                    SET rol = ?, contrasena = ?
                    WHERE correo = ?
                """, (nuevo_rol, hashed, usuario_seleccionado))
            else:
                cursor.execute("""
                    UPDATE usuarios
                    SET rol = ?
                    WHERE correo = ?
                """, (nuevo_rol, usuario_seleccionado))
            conn.commit()
            st.success(f"Usuario {usuario_seleccionado} actualizado correctamente.")
        except Exception as e:
            st.error(f"Error al actualizar el usuario: {e}")
        finally:
            conn.close()

    # Eliminar Usuario
    st.subheader("Eliminar Usuario")
    usuario_eliminar = st.selectbox("Seleccione un usuario para eliminar:", usuarios["correo"])

    if st.button("Eliminar Usuario"):
        # Solicitar confirmación antes de eliminar
        confirmacion = st.radio(
            f"¿Estás seguro de que deseas eliminar al usuario '{usuario_eliminar}'?",
            ("No", "Sí"),
            horizontal=True
        )

        if confirmacion == "Sí":
            conn = conectar_db()
            cursor = conn.cursor()
            try:
                # Eliminar el usuario de la base de datos
                cursor.execute("DELETE FROM usuarios WHERE correo = ?", (usuario_eliminar,))
                conn.commit()
                st.success(f"Usuario '{usuario_eliminar}' eliminado correctamente.")
            except Exception as e:
                st.error(f"Error al eliminar el usuario: {e}")
            finally:
                conn.close()
        else:
            st.info("La eliminación del usuario ha sido cancelada.")




# 34. Mostrar contenido según la opción seleccionada - Condicion Gestion de Registros
elif opcion_seleccionada == "Gestión de Registros" and st.session_state["rol"] == "Administrador":
    st.header("⚙️ Gestión de Registros")
    #elif opcion_seleccionada == "Gestión de Registros":
     #   if st.session_state.get("rol") == "Administrador":
      #      st.header("⚙️ Gestión de Registros")

    # Opciones avanzadas solo para administradores
    st.subheader("Exportar Datos")
    exportar_opcion = st.selectbox("Seleccione qué exportar:", ["Todos los Ingresos", "Todos los Egresos", "Todos los Movimientos Internos"])

    if exportar_opcion == "Todos los Ingresos":
        conn = conectar_db()
        df_ingresos = pd.read_sql_query("SELECT * FROM solicitudes_ingreso", conn)
        conn.close()
        st.download_button(
            label="Descargar Ingresos CSV",
            data=df_ingresos.to_csv(index=False),
            file_name="todos_los_ingresos.csv",
            mime="text/csv"
        )

    elif exportar_opcion == "Todos los Egresos":
        conn = conectar_db()
        df_egresos = pd.read_sql_query("SELECT * FROM solicitudes_egreso", conn)
        conn.close()
        st.download_button(
            label="Descargar Egresos CSV",
            data=df_egresos.to_csv(index=False),
            file_name="todos_los_egresos.csv",
            mime="text/csv"
        )

    elif exportar_opcion == "Todos los Movimientos Internos":
        conn = conectar_db()
        df_movimientos = pd.read_sql_query("SELECT * FROM movimientos_internos", conn)
        conn.close()
        st.download_button(
            label="Descargar Movimientos Internos CSV",
            data=df_movimientos.to_csv(index=False),
            file_name="todos_los_movimientos_internos.csv",
            mime="text/csv"
        )

    # Visualización de datos
    st.subheader("Visualizar Datos")
    tipo_datos = st.selectbox("Seleccione los datos a visualizar:", ["Ingresos", "Egresos", "Movimientos Internos"])
    
    if tipo_datos == "Ingresos":
        conn = conectar_db()
        df_ingresos = pd.read_sql_query("SELECT * FROM solicitudes_ingreso", conn)
        conn.close()
        st.dataframe(df_ingresos)

    elif tipo_datos == "Egresos":
        conn = conectar_db()
        df_egresos = pd.read_sql_query("SELECT * FROM solicitudes_egreso", conn)
        conn.close()
        st.dataframe(df_egresos)

    elif tipo_datos == "Movimientos Internos":
        conn = conectar_db()
        df_movimientos = pd.read_sql_query("SELECT * FROM movimientos_internos", conn)
        conn.close()
        st.dataframe(df_movimientos)

    # Generar Reporte
    st.subheader("Generar Reporte")
    reporte_opcion = st.radio("Seleccione el tipo de reporte:", ["Ingresos", "Egresos", "Movimientos Internos"])
    if st.button("Generar Reporte"):
        if reporte_opcion == "Ingresos":
            generar_reporte_ingresos()
        elif reporte_opcion == "Egresos":
            generar_reporte_egresos()
        elif reporte_opcion == "Movimientos Internos":
            generar_reporte_movimientos()




# 35. Gestión por Administradores - Respuesta y Detalles de Ejecución
elif st.session_state.get("opcion_seleccionada") == "Gestión de Solicitudes":
    st.header("🔧 Gestión de Solicitudes - Team Data Center")

    # Filtros por solicitante y cliente
    st.subheader("Filtros")
    conn = conectar_db()

    # Cargar lista de solicitantes y clientes únicos
    solicitantes_df = pd.read_sql_query("SELECT DISTINCT solicitante FROM solicitudes_ingreso UNION SELECT DISTINCT solicitante FROM solicitudes_egreso UNION SELECT DISTINCT solicitante FROM movimientos_internos", conn)
    clientes_df = pd.read_sql_query("SELECT DISTINCT cliente FROM solicitudes_ingreso UNION SELECT DISTINCT cliente FROM solicitudes_egreso UNION SELECT DISTINCT cliente FROM movimientos_internos", conn)
    conn.close()

    # Filtros dinámicos
    solicitante_filter = st.selectbox("Filtrar por Solicitante:", ["Todos"] + solicitantes_df["solicitante"].tolist())
    cliente_filter = st.selectbox("Filtrar por Cliente:", ["Todos"] + clientes_df["cliente"].tolist())

    # Seleccionar el tipo de solicitud
    tipo_solicitud = st.selectbox(
        "Seleccione el tipo de solicitud a gestionar:",
        ["Ingreso", "Egreso", "Movimiento Interno"]
    )

    # Filtrar solicitudes según el tipo y filtros seleccionados
    conn = conectar_db()
    if tipo_solicitud == "Ingreso":
        query = "SELECT id, solicitante, fecha_ingreso, cliente, datacenter, ticket, marca, modelo, numero_serie FROM solicitudes_ingreso WHERE estado = 'Pendiente'"
    elif tipo_solicitud == "Egreso":
        query = "SELECT id, solicitante, fecha_egreso, datacenter, ticket, marca, modelo, numero_serie, rack_origen, motivo_egreso, estado_salida FROM solicitudes_egreso WHERE estado = 'Pendiente'"
    elif tipo_solicitud == "Movimiento Interno":
        query = "SELECT id, solicitante, fecha_movimiento, datacenter_origen, rack_origen, rack_destino, marca, modelo, numero_serie, estado_equipo FROM movimientos_internos WHERE estado = 'Pendiente'"

    params = []
    if solicitante_filter != "Todos":
        query += " AND solicitante = ?"
        params.append(solicitante_filter)
    if cliente_filter != "Todos":
        query += " AND cliente = ?"
        params.append(cliente_filter)

    solicitudes_df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if solicitudes_df.empty:
        st.info("No hay solicitudes pendientes para los filtros seleccionados.")
    else:
        st.write("Solicitudes Filtradas:")
        st.dataframe(solicitudes_df)

        solicitud_ids = st.multiselect("Seleccione el/los ID de la(s) solicitud(es) a responder:", solicitudes_df["id"].tolist())

        # Agregar dos inputs para energía y espacio que se aplicarán a todas las solicitudes a responder
        energia_disponible = st.radio("¿Existe disponibilidad de energía?", ["No", "Sí"], key="energia_multi")
        espacio_disponible = st.radio("¿Existe disponibilidad de espacio?", ["No", "Sí"], key="espacio_multi")
        ubicacion_propuesta = st.text_input("Ubicación propuesta:", key="ubicacion_multi")
        comentarios = st.text_area("Comentarios adicionales para el solicitante:", key="comentarios_multi")

        if solicitud_ids and st.button("Responder a las solicitudes"):
            # Crear un diccionario para agrupar solicitudes por correo
            respuestas = {}
            for sol_id in solicitud_ids:
                conn = conectar_db()
                query_email = (
                    "SELECT solicitante FROM solicitudes_ingreso WHERE id = ? "
                    "UNION "
                    "SELECT solicitante FROM solicitudes_egreso WHERE id = ? "
                    "UNION "
                    "SELECT solicitante FROM movimientos_internos WHERE id = ?"
                )
                cursor = conn.cursor()
                cursor.execute(query_email, (sol_id, sol_id, sol_id))
                resultado = cursor.fetchone()
                conn.close()
                if resultado:
                    email_obtenido = resultado[0]
                    # Verificar si el correo es válido (básico)
                    if "@" in email_obtenido and "." in email_obtenido:
                        if email_obtenido in respuestas:
                            respuestas[email_obtenido].append(sol_id)
                        else:
                            respuestas[email_obtenido] = [sol_id]
                    else:
                        st.error(f"El correo del solicitante '{email_obtenido}' para la solicitud {sol_id} no es válido.")
                else:
                    st.error(f"No se pudo encontrar el correo del solicitante para la solicitud {sol_id}.")

            # Una vez agrupados, enviar un único correo por cada destinatario
            for destinatario, ids in respuestas.items():
                # Se puede incluir en el mensaje la lista de IDs respondidos
                ids_str = ", ".join(str(i) for i in ids)
                mensaje = f"""
                Hola,
                Se han evaluado sus solicitudes con ID {ids_str}. Aquí están los detalles de la respuesta:
                - Energía disponible: {energia_disponible}
                - Espacio disponible: {espacio_disponible}
                - Ubicación propuesta: {ubicacion_propuesta}
                - Comentarios adicionales: {comentarios}
                Muchas gracias por su solicitud.
                Saludos cordiales,
                {st.session_state.get("login_email", "Team Data Center")}
                """
                if enviar_correo([destinatario], f"Respuesta a sus solicitudes ({ids_str})", mensaje):
                    st.success(f"Correo enviado correctamente a {destinatario} para las solicitudes {ids_str}.")
                else:
                    st.error(f"Error al enviar el correo para el destinatario {destinatario}.")

            st.write("Respuesta a las solicitudes completada.")

        # Los detalles de ejecución (opcional) se procesan en bloque, aplicando el mismo detalle a todos los registros seleccionados.
        st.subheader("Detalles de Ejecución")
        # Iterar sobre múltiples solicitudes seleccionadas
        solicitud_ids = st.multiselect(
            "Seleccione el/los ID de la(s) solicitud(es) para ejecutar detalles:",
            solicitudes_df["id"].tolist()
        )

        if solicitud_ids:
            st.subheader("Detalles de Ejecución para Solicitudes Seleccionadas")

            # Mostrar los equipos asociados a las solicitudes seleccionadas
            equipos_seleccionados = []
            conn = conectar_db()
            cursor = conn.cursor()
            for solicitud_id in solicitud_ids:
                if tipo_solicitud == "Ingreso":
                    query = "SELECT id, marca, modelo, numero_serie FROM solicitudes_ingreso WHERE id = ?"
                elif tipo_solicitud == "Egreso":
                    query = "SELECT id, marca, modelo, numero_serie FROM solicitudes_egreso WHERE id = ?"
                elif tipo_solicitud == "Movimiento Interno":
                    query = "SELECT id, marca, modelo, numero_serie FROM movimientos_internos WHERE id = ?"
                
                cursor.execute(query, (solicitud_id,))
                resultados = cursor.fetchall()
                equipos_seleccionados.extend(resultados)  # Añadir equipos de esta solicitud

            conn.close()

            if not equipos_seleccionados:
                st.warning("No se encontraron equipos para las solicitudes seleccionadas.")
            else:
                for equipo in equipos_seleccionados:
                    equipo_id, marca, modelo, numero_serie = equipo
                    st.subheader(f"Equipo ID: {equipo_id} - {marca} {modelo} (N° Serie: {numero_serie})")

                    # Campos de ejecución para cada equipo
                    rack_asignado = st.text_input(f"Rack asignado para el equipo ID {equipo_id}:", key=f"rack_{equipo_id}")
                    cantidad_u = st.number_input(f"Cantidad de unidades (U) para el equipo ID {equipo_id}:", min_value=1, step=1, key=f"cantidad_u_{equipo_id}")
                    propiedad = st.selectbox(f"Propiedad del equipo ID {equipo_id}:", ["Cliente", "Kyndryl", "Otro"], key=f"propiedad_{equipo_id}")

                    # Botón para guardar los detalles para cada equipo
                    if st.button(f"Guardar Detalles de Ejecución para Equipo ID {equipo_id}", key=f"guardar_detalle_{equipo_id}"):
                        conn = conectar_db()
                        try:
                            cursor = conn.cursor()

                            # Actualizar los detalles en la base de datos según el tipo de solicitud
                            if tipo_solicitud == "Ingreso":
                                cursor.execute("""
                                    UPDATE solicitudes_ingreso
                                    SET estado = ?, rack_asignado = ?, cantidad_u = ?, propiedad = ?
                                    WHERE id = ?
                                """, ("Ejecutado", rack_asignado, cantidad_u, propiedad, equipo_id))
                            elif tipo_solicitud == "Egreso":
                                cursor.execute("""
                                    UPDATE solicitudes_egreso
                                    SET estado = ?, rack_asignado = ?, cantidad_u = ?, propiedad = ?
                                    WHERE id = ?
                                """, ("Ejecutado", rack_asignado, cantidad_u, propiedad, equipo_id))
                            elif tipo_solicitud == "Movimiento Interno":
                                cursor.execute("""
                                    UPDATE movimientos_internos
                                    SET estado = ?, rack_asignado = ?, cantidad_u = ?, propiedad = ?
                                    WHERE id = ?
                                """, ("Ejecutado", rack_asignado, cantidad_u, propiedad, equipo_id))

                            conn.commit()

                            # Registrar cambio en historial
                            descripcion_cambio = f"Detalles de ejecución guardados para el equipo ID {equipo_id}."
                            registrar_cambio(usuario=st.session_state["rol"], accion="Guardar Detalle de Ejecución", descripcion=descripcion_cambio)
                            st.success(f"¡Detalles de ejecución para el equipo ID {equipo_id} guardados correctamente!")
                        except sqlite3.Error as e:
                            st.error(f"Error al actualizar los datos: {e}")
                        finally:
                            conn.close()
import os
import datetime
import time
import hashlib
import secrets
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pymysql

app = Flask(__name__)
CORS(app)


# ==========================================================
# ARCHIVOS DEL PANEL DE ADMINISTRACIÓN
# ==========================================================

@app.route("/")
def inicio():
    return send_from_directory(".", "admin2.html")


@app.route("/admin2.js")
def admin2_js():
    return send_from_directory(".", "admin2.js")


@app.route("/dashboard.html")
def dashboard():
    return send_from_directory(".", "dashboard.html")


@app.route("/dashboard.js")
def dashboard_js():
    return send_from_directory(".", "dashboard.js")


@app.route("/dashboard.css")
def dashboard_css():
    return send_from_directory(".", "dashboard.css")

# ==========================================================
# CREDENCIALES DEL ADMINISTRADOR
# ==========================================================

ADMIN_USUARIO = "admin"
ADMIN_PASSWORD = "admin"


# ==========================================================
# CONFIGURACIÓN DE LA BASE DE DATOS
# ==========================================================

def conectar_bd():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="cristian7",
        database="muni_db",
        cursorclass=pymysql.cursors.DictCursor
    )


# ==========================================================
# CONFIGURACIÓN DE ARCHIVOS (IMÁGENES)
# ==========================================================

CARPETA_IMAGENES = "static/imagenes"
os.makedirs(CARPETA_IMAGENES, exist_ok=True)

EXTENSIONES_PERMITIDAS = {"png", "jpg", "jpeg", "gif", "webp"}


def extension_valida(nombre_archivo):
    return "." in nombre_archivo and \
        nombre_archivo.rsplit(".", 1)[1].lower() in EXTENSIONES_PERMITIDAS


def guardar_imagen(archivo):
    """Guarda el archivo en disco y devuelve la ruta relativa para la BD (o None)."""
    if archivo and archivo.filename and extension_valida(archivo.filename):
        nombre_seguro = secure_filename(archivo.filename)
        nombre_final = f"{int(time.time())}_{nombre_seguro}"
        ruta_completa = os.path.join(CARPETA_IMAGENES, nombre_final)
        archivo.save(ruta_completa)
        return ruta_completa.replace("\\", "/")
    return None


def borrar_imagen(ruta):
    """Elimina del disco la imagen asociada a un registro (si existe)."""
    if ruta and not ruta.startswith("http"):
        ruta_completa = ruta.replace("/", os.sep)
        if os.path.exists(ruta_completa):
            os.remove(ruta_completa)


def validar_fecha_no_pasada(fecha_str):
    """Verifica que la fecha no sea anterior a hoy. Retorna (ok, mensaje)."""
    if not fecha_str:
        return True, None  # Si no hay fecha, no validar
    try:
        fecha = datetime.date.fromisoformat(fecha_str)
        if fecha < datetime.date.today():
            return False, "La fecha no puede ser anterior a hoy"
        return True, None
    except ValueError:
        return False, "Formato de fecha inválido (usar AAAA-MM-DD)"


def limpiar_expirados(tabla):
    """
    Elimina de la BD los registros cuya fecha ya pasó.
    También borra las imágenes asociadas del disco.
    """
    if tabla not in TABLAS:
        return

    cfg = TABLAS[tabla]
    col_fecha = cfg["cols"]["fecha"]
    col_imagen = cfg["cols"]["imagen"]
    pk = cfg["pk"]
    hoy = datetime.date.today().isoformat()

    conexion = None

    try:
        conexion = conectar_bd()

        with conexion.cursor() as cursor:

            # Buscar registros expirados para borrar sus imágenes
            cursor.execute(
                f"""
                SELECT {pk} AS id, {col_imagen} AS imagen
                FROM {tabla}
                WHERE {col_fecha} IS NOT NULL
                  AND {col_fecha} < %s
                """,
                (hoy,)
            )

            expirados = cursor.fetchall()

            if expirados:
                # Borrar imágenes del disco
                for fila in expirados:
                    borrar_imagen(fila["imagen"])

                # Borrar registros de la BD
                ids = [fila["id"] for fila in expirados]
                placeholders = ", ".join(["%s"] * len(ids))
                cursor.execute(
                    f"DELETE FROM {tabla} WHERE {pk} IN ({placeholders})",
                    ids
                )

                conexion.commit()

                print(
                    f">>> Limpieza: {len(expirados)} registro(s) "
                    f"expirado(s) eliminado(s) de '{tabla}'"
                )

    except Exception as e:
        print(f"Error en limpieza de '{tabla}':", e)

    finally:
        if conexion:
            conexion.close()


# ==========================================================
# AUTENTICACIÓN DEL ADMINISTRADOR
# ==========================================================

# Tokens de sesión activos.
# Se pierden cuando se reinicia Flask.
SESIONES = {}


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def crear_tabla_usuarios():
    """Crea la tabla users si no existe y agrega un admin por defecto."""
    
    conexion = None

    try:
        conexion = conectar_bd()

        with conexion.cursor() as cursor:

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usuario VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(64) NOT NULL
                )
            """)

            cursor.execute("SELECT COUNT(*) AS total FROM users")

            if cursor.fetchone()["total"] == 0:

                cursor.execute(
                    """
                    INSERT INTO users (usuario, password_hash)
                    VALUES (%s, %s)
                    """,
                    (
                        ADMIN_USUARIO,
                        hash_password(ADMIN_PASSWORD)
                    )
                )

                print(
                    f">>> Usuario admin creado: "
                    f"{ADMIN_USUARIO} / {ADMIN_PASSWORD}"
                )

        conexion.commit()

    except Exception as e:

        print("Error inicializando usuarios:", e)

    finally:

        if conexion:
            conexion.close()


def autenticado():
    """
    Comprueba si el request contiene un token válido.
    """

    auth = request.headers.get("Authorization", "")

    if not auth.startswith("Bearer "):
        return False

    token = auth.replace("Bearer ", "").strip()

    return token in SESIONES


# ==========================================================
# LOGIN
# ==========================================================


@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    usuario = data.get("usuario", "").strip()
    password = data.get("password", "")

    # Comprobar que se enviaron ambos campos
    if not usuario or not password:
        return jsonify({
            "ok": False,
            "error": "Usuario y contraseña son obligatorios"
        }), 400

    conexion = None

    try:

        conexion = conectar_bd()

        with conexion.cursor() as cursor:

            cursor.execute(
                """
                SELECT id, usuario, password_hash
                FROM users
                WHERE usuario = %s
                """,
                (usuario,)
            )

            user = cursor.fetchone()

    except Exception as e:

        print("Error en login:", e)

        return jsonify({
            "ok": False,
            "error": "Error del servidor"
        }), 500

    finally:

        if conexion:
            conexion.close()

    # Usuario inexistente o contraseña incorrecta
    if not user or user["password_hash"] != hash_password(password):

        return jsonify({
            "ok": False,
            "error": "Usuario o contraseña incorrectos"
        }), 401

    # Crear token
    token = secrets.token_hex(32)

    # Guardar sesión
    SESIONES[token] = user["id"]

    print(f">>> Login correcto: {usuario}")

    return jsonify({
        "ok": True,
        "token": token,
        "usuario": user["usuario"]
    }), 200


# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/api/logout", methods=["POST"])
def logout():

    auth = request.headers.get("Authorization", "")

    if auth.startswith("Bearer "):

        token = auth.replace("Bearer ", "").strip()

        # Eliminar la sesión
        SESIONES.pop(token, None)

    return jsonify({
        "ok": True,
        "mensaje": "Sesión cerrada"
    }), 200


# ==========================================================
# CONFIG DE TABLAS
# ==========================================================

TABLAS = {
    "noticias": {
        "pk": "id",
        "cols": {
            "nombre": "nombre",
            "imagen": "imagen",
            "descripcion": "descripcion",
            "fecha": "fecha"
        }
    },
    "eventos": {
        "pk": "id_eventos",
        "cols": {
            "nombre": "nombre_eventos",
            "imagen": "imagen_eventos",
            "descripcion": "descripcion_eventos",
            "fecha": "fecha_eventos"
        }
    }
}


# ==========================================================
# NOTICIAS
# ==========================================================

@app.route("/api/noticias", methods=["GET"])
def obtener_noticias():

    # Limpiar registros expirados antes de devolver datos
    limpiar_expirados("noticias")

    conexion = None

    try:

        conexion = conectar_bd()

        with conexion.cursor() as cursor:

            cursor.execute(
                """
                SELECT id, nombre, imagen, descripcion, fecha
                FROM noticias
                """
            )

            resultados = cursor.fetchall()

        return jsonify(resultados), 200

    except Exception as e:

        print("Error al obtener noticias:", e)

        return jsonify({
            "error": "No se pudieron obtener las noticias"
        }), 500

    finally:

        if conexion:
            conexion.close()


@app.route("/api/noticias", methods=["POST"])
def crear_noticia():

    if not autenticado():
        return jsonify({"error": "No autorizado"}), 401

    nombre = request.form.get("nombre")
    descripcion = request.form.get("descripcion")
    fecha = request.form.get("fecha")
    imagen_archivo = request.files.get("imagen")

    if not nombre or not descripcion:
        return jsonify({
            "error": "nombre y descripcion son obligatorios"
        }), 400

    # Validar que la fecha no sea pasada
    fecha_ok, fecha_error = validar_fecha_no_pasada(fecha)
    if not fecha_ok:
        return jsonify({"error": fecha_error}), 400

    ruta_imagen = guardar_imagen(imagen_archivo)

    conexion = None

    try:

        conexion = conectar_bd()

        with conexion.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO noticias
                (nombre, imagen, descripcion, fecha)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    nombre,
                    ruta_imagen,
                    descripcion,
                    fecha
                )
            )

        conexion.commit()

        return jsonify({
            "mensaje": "Noticia creada correctamente"
        }), 201

    except Exception as e:

        print("Error al crear noticia:", e)

        return jsonify({
            "error": "No se pudo guardar la noticia"
        }), 500

    finally:

        if conexion:
            conexion.close()


# ==========================================================
# EVENTOS
# ==========================================================

@app.route("/api/eventos", methods=["GET"])
def obtener_eventos():

    # Limpiar registros expirados antes de devolver datos
    limpiar_expirados("eventos")

    conexion = None

    try:

        conexion = conectar_bd()

        with conexion.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id_eventos AS id,
                    nombre_eventos AS nombre,
                    imagen_eventos AS imagen,
                    descripcion_eventos AS descripcion,
                    fecha_eventos AS fecha
                FROM eventos
                ORDER BY fecha_eventos DESC
                """
            )

            resultados = cursor.fetchall()

        return jsonify(resultados), 200

    except Exception as e:

        print("Error al obtener eventos:", e)

        return jsonify({
            "error": "No se pudieron obtener los eventos"
        }), 500

    finally:

        if conexion:
            conexion.close()


@app.route("/api/eventos", methods=["POST"])
def crear_evento():

    if not autenticado():
        return jsonify({"error": "No autorizado"}), 401

    nombre = request.form.get("nombre")
    descripcion = request.form.get("descripcion")
    fecha = request.form.get("fecha")
    imagen_archivo = request.files.get("imagen")

    if not nombre or not descripcion:
        return jsonify({
            "error": "nombre y descripcion son obligatorios"
        }), 400

    # Validar que la fecha no sea pasada
    fecha_ok, fecha_error = validar_fecha_no_pasada(fecha)
    if not fecha_ok:
        return jsonify({"error": fecha_error}), 400

    ruta_imagen = guardar_imagen(imagen_archivo)

    conexion = None

    try:

        conexion = conectar_bd()

        with conexion.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO eventos
                (
                    nombre_eventos,
                    imagen_eventos,
                    descripcion_eventos,
                    fecha_eventos
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    nombre,
                    ruta_imagen,
                    descripcion,
                    fecha
                )
            )

        conexion.commit()

        return jsonify({
            "mensaje": "Evento creado correctamente"
        }), 201

    except Exception as e:

        print("Error al crear evento:", e)

        return jsonify({
            "error": "No se pudo guardar el evento"
        }), 500

    finally:

        if conexion:
            conexion.close()


# ==========================================================
# EDITAR / ELIMINAR
# ==========================================================

@app.route("/api/<tabla>/<int:item_id>", methods=["PUT"])
def actualizar_item(tabla, item_id):

    if tabla not in TABLAS:
        return jsonify({"error": "Ruta no válida"}), 404

    if not autenticado():
        return jsonify({"error": "No autorizado"}), 401

    cfg = TABLAS[tabla]
    c = cfg["cols"]

    nombre = request.form.get("nombre")
    descripcion = request.form.get("descripcion")
    fecha = request.form.get("fecha")
    imagen_archivo = request.files.get("imagen")

    if not nombre or not descripcion:
        return jsonify({
            "error": "nombre y descripcion son obligatorios"
        }), 400

    # Validar que la fecha no sea pasada
    fecha_ok, fecha_error = validar_fecha_no_pasada(fecha)
    if not fecha_ok:
        return jsonify({"error": fecha_error}), 400

    sets = [
        f"{c['nombre']} = %s",
        f"{c['descripcion']} = %s",
        f"{c['fecha']} = %s"
    ]

    params = [
        nombre,
        descripcion,
        fecha
    ]

    if imagen_archivo and imagen_archivo.filename:

        ruta_imagen = guardar_imagen(imagen_archivo)

        if ruta_imagen:

            sets.append(f"{c['imagen']} = %s")
            params.append(ruta_imagen)

    params.append(item_id)

    sql = f"""
        UPDATE {tabla}
        SET {', '.join(sets)}
        WHERE {cfg['pk']} = %s
    """

    conexion = None

    try:

        conexion = conectar_bd()

        with conexion.cursor() as cursor:

            cursor.execute(sql, params)

        conexion.commit()

        return jsonify({
            "mensaje": "Actualizado correctamente"
        }), 200

    except Exception as e:

        print("Error al actualizar:", e)

        return jsonify({
            "error": "No se pudo actualizar"
        }), 500

    finally:

        if conexion:
            conexion.close()


@app.route("/api/<tabla>/<int:item_id>", methods=["DELETE"])
def eliminar_item(tabla, item_id):

    if tabla not in TABLAS:
        return jsonify({"error": "Ruta no válida"}), 404

    if not autenticado():
        return jsonify({"error": "No autorizado"}), 401

    cfg = TABLAS[tabla]
    c = cfg["cols"]

    conexion = None

    try:

        conexion = conectar_bd()

        with conexion.cursor() as cursor:

            cursor.execute(
                f"""
                SELECT {c['imagen']} AS imagen
                FROM {tabla}
                WHERE {cfg['pk']} = %s
                """,
                (item_id,)
            )

            fila = cursor.fetchone()

            if not fila:
                return jsonify({
                    "error": "No encontrado"
                }), 404

            cursor.execute(
                f"""
                DELETE FROM {tabla}
                WHERE {cfg['pk']} = %s
                """,
                (item_id,)
            )

        conexion.commit()

        borrar_imagen(fila["imagen"])

        return jsonify({
            "mensaje": "Eliminado correctamente"
        }), 200

    except Exception as e:

        print("Error al eliminar:", e)

        return jsonify({
            "error": "No se pudo eliminar"
        }), 500

    finally:

        if conexion:
            conexion.close()


# ==========================================================
# INICIO DEL SERVIDOR
# ==========================================================

if __name__ == "__main__":

    crear_tabla_usuarios()

    app.run(
        debug=True,
        port=5000
    )
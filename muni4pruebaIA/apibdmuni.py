import os
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pymysql

app = Flask(__name__)
CORS(app)  # Habilita CORS para que el frontend pueda hacer fetch sin bloqueos

# ===== CONFIGURACIÓN DE LA BASE DE DATOS =====
def conectar_bd():
    return pymysql.connect(
        host="localhost",
        user="root",        # <-- cambiar por tu usuario de MySQL
        password="cristian7",  # <-- cambiar por tu contraseña
        database="muni_db",
        cursorclass=pymysql.cursors.DictCursor  # Filas como diccionarios (fácil de convertir a JSON)
    )

# ===== CONFIGURACIÓN DE ARCHIVOS (IMÁGENES) =====
CARPETA_IMAGENES = "static/imagenes"
os.makedirs(CARPETA_IMAGENES, exist_ok=True)  # crea la carpeta si no existe

EXTENSIONES_PERMITIDAS = {"png", "jpg", "jpeg", "gif", "webp"}

def extension_valida(nombre_archivo):
    return "." in nombre_archivo and \
        nombre_archivo.rsplit(".", 1)[1].lower() in EXTENSIONES_PERMITIDAS

def guardar_imagen(archivo):
    """Guarda el archivo en disco y devuelve la ruta relativa para la BD (o None)."""
    if archivo and archivo.filename and extension_valida(archivo.filename):
        nombre_seguro = secure_filename(archivo.filename)
        nombre_final = f"{int(time.time())}_{nombre_seguro}"  # evita que se pisen nombres
        ruta_completa = os.path.join(CARPETA_IMAGENES, nombre_final)
        archivo.save(ruta_completa)
        return ruta_completa.replace("\\", "/")  # normaliza separadores para usar como URL
    return None


# ================= NOTICIAS =================

@app.route("/api/noticias", methods=["GET"])
def obtener_noticias():
    conexion = None
    try:
        conexion = conectar_bd()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id, nombre, imagen, descripcion, fecha FROM noticias")
            resultados = cursor.fetchall()
        return jsonify(resultados), 200
    except Exception as e:
        print("Error al obtener noticias:", e)
        return jsonify({"error": "No se pudieron obtener las noticias"}), 500
    finally:
        if conexion:
            conexion.close()


@app.route("/api/noticias", methods=["POST"])
def crear_noticia():
    nombre = request.form.get("nombre")
    descripcion = request.form.get("descripcion")
    fecha = request.form.get("fecha")
    imagen_archivo = request.files.get("imagen")

    if not nombre or not descripcion:
        return jsonify({"error": "nombre y descripcion son obligatorios"}), 400

    ruta_imagen = guardar_imagen(imagen_archivo)

    conexion = None
    try:
        conexion = conectar_bd()
        with conexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO noticias (nombre, imagen, descripcion, fecha) VALUES (%s, %s, %s, %s)",
                (nombre, ruta_imagen, descripcion, fecha)
            )
        conexion.commit()
        return jsonify({"mensaje": "Noticia creada correctamente"}), 201
    except Exception as e:
        print("Error al crear noticia:", e)
        return jsonify({"error": "No se pudo guardar la noticia"}), 500
    finally:
        if conexion:
            conexion.close()


# ================= EVENTOS =================

@app.route("/api/eventos", methods=["GET"])
def obtener_eventos():
    conexion = None
    try:
        conexion = conectar_bd()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id, nombre, imagen, descripcion, fecha FROM eventos")
            resultados = cursor.fetchall()
        return jsonify(resultados), 200
    except Exception as e:
        print("Error al obtener eventos:", e)
        return jsonify({"error": "No se pudieron obtener los eventos"}), 500
    finally:
        if conexion:
            conexion.close()


@app.route("/api/eventos", methods=["POST"])
def crear_evento():
    nombre = request.form.get("nombre")
    descripcion = request.form.get("descripcion")
    fecha = request.form.get("fecha")
    imagen_archivo = request.files.get("imagen")

    if not nombre or not descripcion:
        return jsonify({"error": "nombre y descripcion son obligatorios"}), 400

    ruta_imagen = guardar_imagen(imagen_archivo)

    conexion = None
    try:
        conexion = conectar_bd()
        with conexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO eventos (nombre, imagen, descripcion, fecha) VALUES (%s, %s, %s, %s)",
                (nombre, ruta_imagen, descripcion, fecha)
            )
        conexion.commit()
        return jsonify({"mensaje": "Evento creado correctamente"}), 201
    except Exception as e:
        print("Error al crear evento:", e)
        return jsonify({"error": "No se pudo guardar el evento"}), 500
    finally:
        if conexion:
            conexion.close()


# ===== INICIO DEL SERVIDOR =====
if __name__ == "__main__":
    app.run(debug=True, port=5000)
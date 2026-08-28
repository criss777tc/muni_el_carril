import pymysql


def get_connection():
    """Devuelve una conexión a la base de datos MUNI."""
    return pymysql.connect(
        host="localhost",
        user="root",
        password="cristian7",
        database="MUNI",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

import mysql.connector


# Función para obtener la conexión a la base de datos
def obtener_conexion():
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="123456789",
            database="proyecto"
        )
        return conexion
    except Exception as e:
        print("Error al conectar a la base de datos:", e)
        return None

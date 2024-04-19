from flask import Flask, render_template, jsonify, request
import requests  # type: ignore
from conexion import obtener_conexion
from datetime import datetime, timedelta

app = Flask(__name__)
arduino_ip = "192.168.3.200"  # IP estática del Arduino


@app.route('/')
def index():
    return render_template('inicio.html')


@app.route('/Ventiladores/')
def Encender_Ventiladores():
    return render_template('ventiladores.html')


@app.route('/Datos/')
def Datos():
    try:
        connection = obtener_conexion()  # Obtener la conexión a la base de datos
        cursor = connection.cursor(dictionary=True)
        # Consulta para obtener los datos de la tabla
        sql = "SELECT * FROM Datos"
        cursor.execute(sql)
        datos = cursor.fetchall()
        cursor.close()
        connection.close()

        return render_template('datos.html', datos=datos)
    except Exception as e:
        print("Error al obtener datos:", e)
        return "Error al obtener datos de la base de datos"


@app.route("/encender_ventilador/<int:ventilador>")
def encender_ventilador(ventilador):
    # Hora de encendido
    hora_encendido = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Hacer la petición para encender el ventilador
    requests.get(f"http://{arduino_ip}/?ArduinoPIN{ventilador}=on")

    # Insertar registro en la base de datos
    insertar_registro(ventilador, hora_encendido)

    return "OK"


@app.route("/apagar_ventilador/<int:ventilador>")
def apagar_ventilador(ventilador):
    # Hora de apagado
    hora_apagado = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Hacer la petición para apagar el ventilador
    requests.get(f"http://{arduino_ip}/?ArduinoPIN{ventilador}=off")

    # Calcular duración y actualizar registro en la base de datos
    duracion = calcular_duracion(ventilador, hora_apagado)
    actualizar_registro(ventilador, hora_apagado, duracion)

    return "OK"


# Función para insertar un nuevo registro en la base de datos
def insertar_registro(ventilador, hora_encendido):
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        # Concatenamos "ventilador" con el número para formar el nombre completo
        nombre_ventilador = f"ventilador {ventilador}"

        consulta = "INSERT INTO Datos (ventilador, encendido) VALUES (%s, %s)"
        datos = (nombre_ventilador, hora_encendido)

        cursor.execute(consulta, datos)
        conexion.commit()

        cursor.close()
        conexion.close()
    except Exception as e:
        print("Error al insertar en la base de datos:", e)


# Función para calcular la duración
def calcular_duracion(ventilador, hora_apagado):
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        # Concatenamos "ventilador" con el número para formar el nombre completo
        nombre_ventilador = f"ventilador {ventilador}"

        consulta = "SELECT encendido FROM Datos WHERE ventilador = %s ORDER BY id DESC LIMIT 1"
        cursor.execute(consulta, (nombre_ventilador,))

        resultado = cursor.fetchone()
        if resultado:
            hora_encendido = resultado[0]

            # Verificar si hora_encendido ya es un objeto datetime
            if isinstance(hora_encendido, datetime):
                hora_encendido = hora_encendido
            else:
                hora_encendido = datetime.strptime(
                    hora_encendido, '%Y-%m-%d %H:%M:%S')

            # Convertir hora_apagado a objeto datetime
            hora_apagado = datetime.strptime(hora_apagado, '%Y-%m-%d %H:%M:%S')

            # Calcular duración en segundos
            duracion_segundos = (hora_apagado - hora_encendido).total_seconds()

            # Convertir duración de segundos a formato hh:mm:ss
            duracion_str = str(timedelta(seconds=duracion_segundos))

            cursor.close()
            conexion.close()

            return duracion_str
        else:
            return None
    except Exception as e:
        print("Error al calcular duración:", e)
        return None


# Función para actualizar un registro en la base de datos con la hora de apagado y duración
def actualizar_registro(ventilador, hora_apagado, duracion):
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        # Concatenamos "ventilador" con el número para formar el nombre completo
        nombre_ventilador = f"ventilador {ventilador}"

        consulta = "UPDATE Datos SET apagado = %s, tiempo_encendido = %s WHERE ventilador = %s ORDER BY id DESC LIMIT 1"
        datos = (hora_apagado, duracion, nombre_ventilador)

        cursor.execute(consulta, datos)
        conexion.commit()

        cursor.close()
        conexion.close()
    except Exception as e:
        print("Error al actualizar en la base de datos:", e)


# Ruta para errores
@app.errorhandler(404)
def notFound(error=None):
    message = {
        'message': 'No encontrado ' + request.url,
        'status': '404 Not Found'
    }
    response = jsonify(message)
    response.status_code = 404
    return response


if __name__ == '__main__':
    app.run(debug=True)

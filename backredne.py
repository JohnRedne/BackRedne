# -*- coding: utf-8 -*-
"""Backredne.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1FaaNRmssfKuzNmzSTbVEtrcdcPqxygOe
"""

!pip install obspy

!pip install Flask obspy requests pyngrok

from flask import Flask, request, send_file, jsonify
from obspy import read
import requests
import io
import datetime
import matplotlib.pyplot as plt

app = Flask(__name__)

@app.route('/generate_sismograma', methods=['GET'])
def generate_sismograma():
    try:
        # Obtener los parámetros de la URL
        net = request.args.get('net')
        sta = request.args.get('sta')
        loc = request.args.get('loc')
        cha = request.args.get('cha')
        start = request.args.get('start')
        end = request.args.get('end')

        # Verificar que todos los parámetros requeridos están presentes
        if not all([net, sta, loc, cha, start, end]):
            return jsonify({"error": "Faltan parámetros requeridos"}), 400

        # Construir la URL para descargar el archivo MiniSEED desde Raspberry Shake
        url = f"https://data.raspberryshake.org/fdsnws/dataselect/1/query?starttime={start}&endtime={end}&network={net}&station={sta}&location={loc}&channel={cha}&nodata=404"

        # Realizar la solicitud al servidor para obtener los datos
        response = requests.get(url)
        if response.status_code == 503:
            return jsonify({"error": "El servidor no está disponible en este momento."}), 503
        if response.status_code != 200:
            return jsonify({"error": f"Error al descargar datos: {response.status_code}"}), 500

        # Guardar el archivo MiniSEED en memoria
        mini_seed_data = io.BytesIO(response.content)

        # Procesar el archivo MiniSEED para extraer los datos
        try:
            st = read(mini_seed_data)
        except Exception as e:
            return jsonify({"error": f"Error procesando el archivo MiniSEED: {str(e)}"}), 500

        # Extraer los datos para graficar con Matplotlib
        tr = st[0]
        start_time = tr.stats.starttime.datetime  # Obtener el tiempo de inicio del sismograma
        times = [start_time + datetime.timedelta(seconds=sec) for sec in tr.times()]  # Crear una lista de tiempos absolutos
        data = tr.data  # Amplitud de las lecturas sísmicas

        # Crear el gráfico con Matplotlib
        fig, ax = plt.subplots(figsize=(10, 4))  # Tamaño ajustado para aplicaciones móviles
        ax.plot(times, data, color='black', linewidth=0.8)

        # Configuración de los ejes
        ax.set_title(f"{start} - {end}", fontsize=10, y=1.05)  # Título con rango de tiempo
        ax.set_xlabel("Tiempo")
        ax.set_ylabel("Amplitud")

        # Etiqueta de la estación en la esquina superior izquierda
        ax.text(0.02, 0.98, f"{net}.{sta}.{loc}.{cha}", transform=ax.transAxes,
                fontsize=9, verticalalignment='top', bbox=dict(facecolor='white', edgecolor='black'))

        # Rotar etiquetas de tiempo en el eje X para mayor claridad
        fig.autofmt_xdate()

        # Guardar el gráfico en memoria como imagen PNG
        output_image = io.BytesIO()
        plt.savefig(output_image, format='png', dpi=120, bbox_inches="tight")
        output_image.seek(0)
        plt.close(fig)

        # Devolver la imagen generada como respuesta
        return send_file(output_image, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

# Ejecutar el servidor Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
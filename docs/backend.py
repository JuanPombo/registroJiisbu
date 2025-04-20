from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from datetime import datetime, timedelta
import time

app = Flask(__name__, static_folder='.')
CORS(app)

# Configuración de Google Sheets
SHEET_NAME = "ASISTENCIA - JIISBU 2025"
WORKSHEET_NAME = "ASISTENTES"
COL_CEDULA = 4  # Columna D para cédula
HEADER_ROW = 10

# Columnas por día
DIAS_EVENTO = {
    28: {"asistencia": 8, "hora": 11},  # H y K
    29: {"asistencia": 9, "hora": 12},  # I y L
    30: {"asistencia": 10, "hora": 13}, # J y M
}

def get_credentials():
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if not creds_json:
        raise ValueError("No se configuraron las credenciales en variables de entorno")
    try:
        return Credentials.from_service_account_info(json.loads(creds_json), scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
    except Exception as e:
        raise ValueError(f"Error en credenciales: {str(e)}")

def get_sheet():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            creds = get_credentials()
            client = gspread.authorize(creds)
            return client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
        except Exception as e:
            if attempt == max_retries - 1:
                app.logger.error(f"Error al conectar con Google Sheets: {str(e)}")
                return None
            time.sleep(2 ** attempt)

def hora_colombiana():
    utc_now = datetime.utcnow()
    colombia_now = utc_now - timedelta(hours=5)
    return colombia_now

@app.route('/update_sheet', methods=['POST'])
def update_sheet():
    sheet = get_sheet()
    if not sheet:
        return jsonify({
            "success": False,
            "message": "Error al conectar con la base de datos. Intente nuevamente."
        }), 500

    try:
        data = request.get_json()
        if not data or 'cedula' not in data:
            return jsonify({
                "success": False,
                "message": "Datos de solicitud inválidos"
            }), 400

        cedula = str(data['cedula']).strip()
        if not cedula.isdigit():
            return jsonify({
                "success": False,
                "message": "La cédula debe contener solo números"
            }), 400

        # Buscar la cédula a partir de la fila 11
        try:
            cell = sheet.find(cedula, in_column=COL_CEDULA)
            if cell.row < HEADER_ROW + 1:
                raise gspread.exceptions.CellNotFound()
        except gspread.exceptions.CellNotFound:
            return jsonify({
                "success": False,
                "message": "Cédula no encontrada en el sistema"
            }), 404

        # Fecha actual en hora colombiana
        ahora = hora_colombiana()
        dia_actual = 28

        if dia_actual not in DIAS_EVENTO:
            return jsonify({
                "success": False,
                "message": f"Hoy ({dia_actual}) no es un día de registro válido."
            }), 400

        col_asistencia = DIAS_EVENTO[dia_actual]["asistencia"]
        col_hora = DIAS_EVENTO[dia_actual]["hora"]

        # Verificar si ya está registrada
        if sheet.cell(cell.row, col_asistencia).value == "✓":
            return jsonify({
                "success": False,
                "message": "Esta cédula ya fue registrada hoy"
            }), 400

        # Registrar ✔ y hora
        hora = ahora.strftime("%I:%M %p")  # Ej: 08:20 AM
        sheet.update_cell(cell.row, col_asistencia, "✓")
        sheet.update_cell(cell.row, col_hora, hora)

        # Obtener nombre del asistente
        nombre = sheet.cell(cell.row, 2).value

        return jsonify({
            "success": True,
            "message": "Asistencia registrada exitosamente",
            "nombre": nombre or ""
        })

    except Exception as e:
        app.logger.error(f"Error en update_sheet: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error interno del servidor. Por favor intente más tarde."
        }), 500

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

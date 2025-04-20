from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from datetime import datetime
import time

app = Flask(__name__, static_folder='.')
CORS(app)

# Configuración de Google Sheets
SHEET_NAME = "ASISTENCIA - JIISBU 2025"
WORKSHEET_NAME = "ASISTENTES"
COL_CEDULA = 4  # Columna D para cédula
COL_ASISTENCIA = 8  # Columna H para asistencia
COL_HORA = 9  # Columna I para hora de registro



def get_credentials():
    """Obtiene las credenciales de Google Sheets con manejo de errores"""
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
    """Obtiene la hoja de cálculo con reconexión automática"""
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
            time.sleep(2 ** attempt)  # Espera exponencial

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

        # Buscar la cédula exacta en la columna D
        try:
            cell = sheet.find(cedula, in_column=COL_CEDULA)
        except gspread.exceptions.CellNotFound:
            return jsonify({
                "success": False,
                "message": "Cédula no encontrada en el sistema"
            }), 404

        # Verificar si ya está registrada
        if sheet.cell(cell.row, COL_ASISTENCIA).value == "✓":
            return jsonify({
                "success": False,
                "message": "Esta cédula ya fue registrada"
            }), 400

        # Registrar asistencia
        sheet.update_cell(cell.row, COL_ASISTENCIA, "✓")
        sheet.update_cell(cell.row, COL_HORA, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Obtener nombre del asistente (asumiendo columna B)
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
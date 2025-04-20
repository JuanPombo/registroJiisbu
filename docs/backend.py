from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import os
import json

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Habilita CORS para permitir solicitudes desde el frontend

# Configuración de Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets", 
         "https://www.googleapis.com/auth/drive"]

# Autenticación mejorada
def get_credentials():
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if not creds_json:
        raise ValueError("No se encontraron las credenciales en las variables de entorno")
    try:
        creds_info = json.loads(creds_json)
        return Credentials.from_service_account_info(creds_info, scopes=scope)
    except json.JSONDecodeError:
        raise ValueError("Formato incorrecto de las credenciales JSON")

try:
    creds = get_credentials()
    client = gspread.authorize(creds)
    sheet = client.open("ASISTENCIA - JIISBU 2025").worksheet("ASISTENTES")
except Exception as e:
    print(f"Error inicializando Google Sheets: {str(e)}")
    sheet = None

# Ruta para servir el frontend
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# Ruta para servir archivos estáticos (logo.jpeg, etc)
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

# Ruta para actualizar la hoja de cálculo
@app.route('/update_sheet', methods=['POST'])
def update_sheet():
    if not sheet:
        return jsonify({"success": False, "message": "Error de conexión con Google Sheets"}), 500

    data = request.get_json()
    cedula = data.get("cedula", "").strip()

    if not cedula:
        return jsonify({"success": False, "message": "Cédula no proporcionada."}), 400

    try:
        # Buscar todas las cédulas para evitar múltiples solicitudes a la API
        records = sheet.get_all_records()
        
        for idx, row in enumerate(records, start=2):  # start=2 porque la primera fila es encabezado
            if str(row.get('CEDULA', '')).strip() == cedula:
                # Verificar si ya está marcada la asistencia
                if row.get('ASISTENCIA', '').strip() == "✓":
                    return jsonify({"success": False, "message": "Esta cédula ya fue registrada."}), 400
                
                # Marcar asistencia
                sheet.update_cell(idx, 8, "✓")  # Columna H (8) es ASISTENCIA
                return jsonify({
                    "success": True, 
                    "message": "Asistencia registrada.",
                    "nombre": row.get('NOMBRE', '')  # Asegúrate que coincida con el nombre de la columna
                })

        return jsonify({"success": False, "message": "Cédula no encontrada."}), 404

    except Exception as e:
        return jsonify({"success": False, "message": f"Error del servidor: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
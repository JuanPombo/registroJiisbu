from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import os
import json

app = Flask(__name__, static_folder='.')
CORS(app)

# Configuración de Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets", 
         "https://www.googleapis.com/auth/drive"]

def get_credentials():
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if not creds_json:
        raise ValueError("No se encontraron las credenciales en las variables de entorno")
    try:
        return Credentials.from_service_account_info(json.loads(creds_json), scopes=scope)
    except Exception as e:
        raise ValueError(f"Error cargando credenciales: {str(e)}")

try:
    creds, _ = get_credentials()
    client = gspread.authorize(creds)
    sheet = client.open("ASISTENCIA - JIISBU 2025").worksheet("ASISTENTES")
except Exception as e:
    print(f"Error inicializando Google Sheets: {str(e)}")
    sheet = None

# Servir el frontend
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# Servir archivos estáticos
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# API para registrar asistencia
@app.route('/update_sheet', methods=['POST'])
def update_sheet():
    if not sheet:
        return jsonify({"success": False, "message": "Error de conexión con Google Sheets"}), 500
    
    data = request.get_json()
    if not data or 'cedula' not in data:
        return jsonify({"success": False, "message": "Datos inválidos"}), 400
    
    cedula = str(data['cedula']).strip()
    # ... (resto del código de update_sheet)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
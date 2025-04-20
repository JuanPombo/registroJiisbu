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
        raise ValueError("No se encontraron las credenciales")
    try:
        return Credentials.from_service_account_info(json.loads(creds_json), scopes=scope)
    except Exception as e:
        raise ValueError(f"Error credenciales: {str(e)}")

try:
    creds = get_credentials()
    client = gspread.authorize(creds)
    sheet = client.open("ASISTENCIA - JIISBU 2025").worksheet("ASISTENTES")
    print("✅ Conexión con Google Sheets establecida")
except Exception as e:
    print(f"❌ Error Google Sheets: {str(e)}")
    sheet = None

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/update_sheet', methods=['POST'])
def update_sheet():
    if not sheet:
        return jsonify({"success": False, "message": "Error con Google Sheets"}), 500
    
    try:
        data = request.get_json()
        if not data or 'cedula' not in data:
            return jsonify({"success": False, "message": "Datos inválidos"}), 400
        
        cedula = str(data['cedula']).strip()
        print(f"Buscando cédula: {cedula}")
        
        # Obtener todos los registros
        records = sheet.get_all_records()
        
        for idx, row in enumerate(records, start=2):  # Fila 2 es el primer dato
            if str(row.get('CEDULA', '')).strip() == cedula:
                # Verificar si ya está registrado
                if row.get('ASISTENCIA', '') == "✓":
                    return jsonify({
                        "success": False,
                        "message": "Esta cédula ya fue registrada"
                    }), 400
                
                # Actualizar hoja
                sheet.update_cell(idx, 8, "✓")  # Columna H (8) es ASISTENCIA
                print(f"✅ Registrada cédula: {cedula}")
                return jsonify({
                    "success": True,
                    "message": "Asistencia registrada exitosamente",
                    "nombre": row.get('NOMBRE', '')
                })
        
        return jsonify({"success": False, "message": "Cédula no encontrada"}), 404
    
    except Exception as e:
        print(f"❌ Error en update_sheet: {str(e)}")
        return jsonify({"success": False, "message": f"Error del servidor: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
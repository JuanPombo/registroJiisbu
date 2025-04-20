from flask import Flask, request, jsonify
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import os

app = Flask(__name__)
CORS(app)  # Habilita CORS para permitir solicitudes desde el frontend

# Autenticación con Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Obtener las credenciales desde la variable de entorno
credenciales_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

if credenciales_json:
    creds = Credentials.from_service_account_info(eval(credenciales_json), scopes=scope)
else:
    raise Exception("No se encontraron las credenciales en la variable de entorno.")

client = gspread.authorize(creds)
sheet = client.open("ASISTENCIA - JIISBU 2025").worksheet("ASISTENTES")

@app.route('/update_sheet', methods=['POST'])
def update_sheet():
    data = request.get_json()
    cedula = data.get("cedula", "").strip()

    if not cedula:
        return jsonify({"success": False, "message": "Cédula no proporcionada."}), 400

    try:
        # Buscar la fila con la cédula en la columna D (4)
        celdas = sheet.col_values(4)
        for idx, valor in enumerate(celdas, start=1):
            if valor.strip() == cedula:
                # Marcar asistencia en la columna H (8)
                sheet.update_cell(idx, 8, "✓")
                return jsonify({"success": True, "message": "Asistencia registrada."})

        return jsonify({"success": False, "message": "Cédula no encontrada."}), 404

    except Exception as e:
        return jsonify({"success": False, "message": f"Error del servidor: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")


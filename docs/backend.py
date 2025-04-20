from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from io import StringIO

app = Flask(__name__)

# Autenticación con Google Sheets desde variable de entorno
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
json_creds = os.environ["GOOGLE_CREDS_JSON"]
creds_dict = json.loads(json_creds)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("ASISTENCIA - JIISBU 2025").worksheet("ASISTENTES")

@app.route('/update_sheet', methods=['POST'])
def update_sheet():
    data = request.get_json()
    cedula = data.get("cedula")

    if not cedula:
        return jsonify({"success": False, "message": "Cédula no proporcionada."}), 400

    celdas = sheet.col_values(4)
    fila_encontrada = None
    for idx, valor in enumerate(celdas, start=1):
        if valor.strip() == cedula:
            fila_encontrada = idx
            break

    if fila_encontrada:
        sheet.update_cell(fila_encontrada, 8, "✓")
        return jsonify({"success": True, "message": "Asistencia registrada."})
    else:
        return jsonify({"success": False, "message": "Cédula no encontrada."}), 404

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)

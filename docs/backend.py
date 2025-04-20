from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

app = Flask(__name__)

# Autenticación con Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("registro-jiisbu-d23e447232b1.json", scope)
client = gspread.authorize(creds)
sheet = client.open("ASISTENCIA - JIISBU 2025").worksheet("ASISTENTES")

@app.route('/update_sheet', methods=['POST'])
def update_sheet():
    # Recibe la cédula del QR
    data = request.get_json()
    cedula = data.get("cedula")
    
    if not cedula:
        return jsonify({"success": False, "message": "Cédula no proporcionada."}), 400

    # Buscar la fila con la cédula en la columna D
    celdas = sheet.col_values(4)
    fila_encontrada = None
    for idx, valor in enumerate(celdas, start=1):
        if valor.strip() == cedula:
            fila_encontrada = idx
            break

    if fila_encontrada:
        # Marcar asistencia en la columna correspondiente (por ejemplo, columna 8)
        sheet.update_cell(fila_encontrada, 8, "✓")
        return jsonify({"success": True, "message": "Asistencia registrada."})
    else:
        return jsonify({"success": False, "message": "Cédula no encontrada."}), 404

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)

from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

# Base de datos completa según el comunicado CP9/2026 del BCB
LISTA_NEGRA = {
    "10": [
        (67250001, 67700000), (69050001, 71300000), (76310012, 85139995),
        (86400001, 86850000), (90900001, 91350000), (91800001, 92250000)
    ],
    "20": [
        (87280145, 91646549), (96650001, 97100000), (99800001, 100700000),
        (109250001, 109700000), (110600001, 111500000), (111950001, 113300000),
        (114200001, 115550000), (118700001, 119600000), (120500001, 120950000)
    ],
    "50": [
        (77100001, 77550000), (78000001, 78450000), (78900001, 97250000),
        (98150001, 98600000), (104900001, 105800000), (106700001, 107150000),
        (107600001, 108500000), (109400001, 109850000)
    ]
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/validar', methods=['POST'])
def validar():
    data = request.json
    corte = data.get('corte')
    serie = data.get('serie', '').upper()
    try:
        numero = int(data.get('numero'))
    except:
        return jsonify({"status": "error", "mensaje": "Formato de número inválido"})

    # Lógica de validación
    if serie == "A":
        return jsonify({"status": "legal", "mensaje": "SERIE A: Billete con Valor Legal"})
    
    if serie == "B":
        rangos = LISTA_NEGRA.get(corte, [])
        for inicio, fin in rangos:
            if inicio <= numero <= fin:
                return jsonify({"status": "ilegal", "mensaje": "¡ALERTA! Serie sin valor legal según BCB"})
        return jsonify({"status": "legal", "mensaje": "SERIE B: Billete fuera de lista negra"})

    return jsonify({"status": "error", "mensaje": "Serie no reconocida"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

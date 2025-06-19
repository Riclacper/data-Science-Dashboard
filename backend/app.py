print(">>>>> APP INICIADO: backend/app.py usado com sucesso")

from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from urllib.parse import quote_plus
import joblib
import os
import pandas as pd
import json

app = Flask(__name__)
CORS(app)

# === Conexão MongoDB Atlas ===
USUARIO = quote_plus("icanadareparos")
SENHA = quote_plus("ZzkSH4SSOzGSsnuc")
MONGO_URI = f"mongodb+srv://icanadareparos:ZzkSH4SSOzGSsnuc@dentalbase.hppnmdq.mongodb.net/forense?retryWrites=true&w=majority&appName=DentalBase"
client = MongoClient(MONGO_URI)
db = client["forense"]
colecao = db["ocorrencias"]

# === Carrega o modelo de ML ===
model_path = 'model.pkl'
model = joblib.load(model_path)

# === Recriar codificadores com base nos dados reais ===
dados = list(colecao.find({}, {"tipoCrime": 1, "cidade": 1, "uf": 1, "_id": 0}))
df = pd.DataFrame(dados)

from sklearn.preprocessing import LabelEncoder
le_tipoCrime = LabelEncoder().fit(df["tipoCrime"])
le_cidade = LabelEncoder().fit(df["cidade"])
le_uf = LabelEncoder().fit(df["uf"])


# === ROTA: Página inicial ===
@app.route('/')
def home():
    return "API de análise de casos conectada ao Atlas"


# === ROTA: Retorna todos os casos ===
@app.route('/casos', methods=['GET'])
def listar():
    print(">>> /casos foi chamado!")
    casos = list(colecao.find({}, {'_id': 0}))
    return jsonify(casos)


# === ROTA: Insere novo caso ===
@app.route('/casos', methods=['POST'])
def inserir():
    novo = request.get_json()
    colecao.insert_one(novo)
    return jsonify({'msg': 'inserido com sucesso'})


# === ROTA: Importância das variáveis ===
@app.route('/features', methods=['GET'])
def importancia_variaveis():
    features = ["tipoCrime", "cidade", "uf", "hora_num"]
    importancias = model.feature_importances_
    return jsonify({
        "features": features,
        "importances": importancias.tolist()
    })


# === ROTA: Predição de status ===
@app.route('/predict', methods=['POST'])
def predizer_status():
    dados = request.get_json()
    try:
        tipoCrime = le_tipoCrime.transform([dados['tipoCrime']])[0]
        cidade = le_cidade.transform([dados['cidade']])[0]
        uf = le_uf.transform([dados['uf']])[0]
        hora_num = int(dados['hora'].split(":")[0])

        entrada = pd.DataFrame([[tipoCrime, cidade, uf, hora_num]],
                               columns=['tipoCrime', 'cidade', 'uf', 'hora_num'])

        pred_index = model.predict(entrada)[0]

        with open("classes_labels.json", encoding="utf-8") as f:
            labels = json.load(f)

        label = labels.get(str(pred_index), str(pred_index))
        return jsonify({"previsao_status": label})

    except Exception as e:
        return jsonify({"erro": str(e)})


# === ROTA: Teste simples de conexão ===
@app.route('/teste')
def teste():
    print(">>> Endpoint /teste acessado!")
    doc = colecao.find_one({}, {'_id': 0})
    return jsonify(doc if doc else {"erro": "colecao vazia"})


# === ROTA: Avaliação do modelo ===
@app.route('/avaliar-modelo', methods=['GET'])
def avaliar_modelo():
    try:
        with open("avaliacao_modelo.json", "r", encoding="utf-8") as f:
            avaliacao = json.load(f)
        return jsonify(avaliacao)
    except Exception as e:
        return jsonify({"erro": str(e)})



# === ROTA: Labels legíveis das classes ===
@app.route('/classes', methods=['GET'])
def classes():
    try:
        with open("classes_labels.json", "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({"erro": "Arquivo classes_labels.json não encontrado"}), 404


# === INICIAR SERVIDOR ===
if __name__ == '__main__':
    app.run(debug=True)

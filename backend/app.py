import os
import json
import logging
import datetime
import smtplib
from email.message import EmailMessage

import joblib
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from fpdf import FPDF
from pymongo import MongoClient
from sklearn.preprocessing import LabelEncoder

# === Carregar variáveis de ambiente ===
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# === Conexão MongoDB (via variável de ambiente) ===
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError(
        "Variável de ambiente MONGO_URI não definida. "
        "Copie backend/.env.example para backend/.env e preencha."
    )

client = MongoClient(MONGO_URI)
db = client["forense"]
colecao = db["ocorrencias"]

# === Carrega o modelo de ML ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, '..', 'model', 'model.pkl')
model = joblib.load(model_path)

# === Recriar codificadores com base nos dados reais ===
dados_enc = list(colecao.find({}, {"tipoCrime": 1, "cidade": 1, "uf": 1, "_id": 0}))
df_enc = pd.DataFrame(dados_enc)

le_tipoCrime = LabelEncoder().fit(df_enc["tipoCrime"])
le_cidade = LabelEncoder().fit(df_enc["cidade"])
le_uf = LabelEncoder().fit(df_enc["uf"])


# === ROTA: Página inicial ===
@app.route('/')
def home():
    return "API de análise de casos conectada ao banco de dados"


# === ROTA: Login ===
@app.route('/login', methods=['POST'])
def login():
    dados = request.get_json()
    usuario = dados.get('usuario', '')
    senha = dados.get('senha', '')

    LOGIN_USER = os.getenv('LOGIN_USER')
    LOGIN_PASS = os.getenv('LOGIN_PASS')

    if not LOGIN_USER or not LOGIN_PASS:
        logger.error("Variáveis LOGIN_USER ou LOGIN_PASS não configuradas.")
        return jsonify({"erro": "Credenciais de login não configuradas no servidor."}), 500

    if usuario == LOGIN_USER and senha == LOGIN_PASS:
        return jsonify({"ok": True})
    return jsonify({"ok": False, "erro": "Usuário ou senha incorretos."}), 401


# === ROTA: Retorna todos os casos ===
@app.route('/casos', methods=['GET'])
def listar():
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

        labels_path = os.path.join(BASE_DIR, 'classes_labels.json')
        with open(labels_path, encoding="utf-8") as f:
            labels = json.load(f)

        label = labels.get(str(pred_index), str(pred_index))
        return jsonify({"previsao_status": label})

    except Exception as e:
        logger.exception("Erro ao predizer status")
        return jsonify({"erro": "Erro ao processar predição. Verifique os dados enviados."}), 400


# === ROTA: Teste simples de conexão ===
@app.route('/teste')
def teste():
    doc = colecao.find_one({}, {'_id': 0})
    return jsonify(doc if doc else {"erro": "colecao vazia"})


# === ROTA: Avaliação do modelo ===
@app.route('/avaliar-modelo', methods=['GET'])
def avaliar_modelo():
    try:
        avaliacao_path = os.path.join(BASE_DIR, 'avaliacao_modelo.json')
        with open(avaliacao_path, "r", encoding="utf-8") as f:
            avaliacao = json.load(f)
        return jsonify(avaliacao)
    except FileNotFoundError:
        return jsonify({
            "erro": "avaliacao_modelo.json não encontrado. Execute train_model_avaliado.py primeiro."
        }), 404
    except Exception:
        logger.exception("Erro ao carregar avaliacao_modelo.json")
        return jsonify({"erro": "Erro interno ao carregar avaliação do modelo."}), 500


# === ROTA: Labels legíveis das classes ===
@app.route('/classes', methods=['GET'])
def classes():
    try:
        labels_path = os.path.join(BASE_DIR, 'classes_labels.json')
        with open(labels_path, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({
            "erro": "classes_labels.json não encontrado. Execute train_model_avaliado.py primeiro."
        }), 404


# === ROTA: Enviar relatório por e-mail ===
@app.route('/enviar-relatorio', methods=['POST'])
def enviar_relatorio():
    dados = request.get_json()
    email_destino = dados.get('email', '')

    EMAIL_ORIGEM = os.getenv('EMAIL_ORIGEM')
    SENHA_APP = os.getenv('SENHA_APP')
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))

    if not EMAIL_ORIGEM or not SENHA_APP:
        logger.error("Variáveis EMAIL_ORIGEM ou SENHA_APP não configuradas.")
        return jsonify({"erro": "Credenciais de e-mail não configuradas no servidor."}), 500

    if not email_destino or '@' not in email_destino:
        return jsonify({"erro": "E-mail de destino inválido."}), 400

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Relatório de Avaliação do Modelo", ln=True, align="C")
        pdf.ln(8)

        logo_path = os.path.join(BASE_DIR, 'logo.png')
        if os.path.exists(logo_path):
            pdf.image(logo_path, x=10, y=20, w=40)
            pdf.ln(30)

        pdf.set_font("Helvetica", "", 12)
        data = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        pdf.cell(0, 10, f"Gerado em: {data}", ln=True)
        pdf.ln(8)
        pdf.multi_cell(0, 10,
            "Este é um relatório automático gerado pelo sistema de predição forense.\n"
            "Os dados estão disponíveis no dashboard.")

        pdf_path = os.path.join(BASE_DIR, 'relatorio_avaliacao.pdf')
        pdf.output(pdf_path)

        msg = EmailMessage()
        msg["Subject"] = "Relatório de Avaliação do Modelo"
        msg["From"] = EMAIL_ORIGEM
        msg["To"] = email_destino
        msg.set_content(
            "Olá,\n\nSegue em anexo o relatório automático gerado pelo sistema.\n\nAtt,\nSistema Forense"
        )
        with open(pdf_path, "rb") as f:
            msg.add_attachment(f.read(), maintype="application", subtype="pdf",
                               filename="relatorio_avaliacao.pdf")

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.login(EMAIL_ORIGEM, SENHA_APP)
            smtp.send_message(msg)

        return jsonify({"msg": "Relatório enviado com sucesso!"})

    except Exception:
        logger.exception("Erro ao enviar relatório")
        return jsonify({"erro": "Erro interno ao enviar o relatório."}), 500


# === INICIAR SERVIDOR ===
if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_ENV', 'production') == 'development'
    app.run(debug=debug_mode)

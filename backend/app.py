import os
import json
import hmac
import hashlib
import logging
import datetime
import smtplib
from email.message import EmailMessage
from functools import wraps

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

# === Chave secreta para tokens de sessão ===
SECRET_KEY = os.getenv("SECRET_KEY", "")


def _gerar_token(usuario: str) -> str:
    """Gera um token HMAC-SHA256 simples para a sessão."""
    payload = f"{usuario}:{datetime.date.today().isoformat()}"
    return hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()


def requer_autenticacao(f):
    """Decorator: exige cabeçalho Authorization: ******"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not SECRET_KEY:
            logger.error("Variável SECRET_KEY não configurada.")
            return jsonify({"erro": "Autenticação não configurada no servidor."}), 500

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"erro": "Token de autenticação ausente."}), 401

        token_recebido = auth.split(" ", 1)[1]
        LOGIN_USER = os.getenv("LOGIN_USER", "")
        token_esperado = _gerar_token(LOGIN_USER)

        if not hmac.compare_digest(token_recebido, token_esperado):
            return jsonify({"erro": "Token inválido ou expirado."}), 401

        return f(*args, **kwargs)
    return decorated


# === ROTA: Página inicial ===
@app.route('/')
def home():
    return "API de análise de casos conectada ao banco de dados"


# === ROTA: Login ===
@app.route('/login', methods=['POST'])
def login():
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Corpo da requisição inválido ou ausente."}), 400

    usuario = dados.get('usuario', '')
    senha = dados.get('senha', '')

    LOGIN_USER = os.getenv('LOGIN_USER')
    LOGIN_PASS = os.getenv('LOGIN_PASS')

    if not LOGIN_USER or not LOGIN_PASS:
        logger.error("Variáveis LOGIN_USER ou LOGIN_PASS não configuradas.")
        return jsonify({"erro": "Credenciais de login não configuradas no servidor."}), 500

    if not SECRET_KEY:
        logger.error("Variável SECRET_KEY não configurada.")
        return jsonify({"erro": "Autenticação não configurada no servidor."}), 500

    if usuario == LOGIN_USER and senha == LOGIN_PASS:
        token = _gerar_token(usuario)
        return jsonify({"ok": True, "token": token})
    return jsonify({"ok": False, "erro": "Usuário ou senha incorretos."}), 401


CAMPOS_OBRIGATORIOS_CASO = ["tipoCrime", "status", "data", "hora", "cidade", "uf"]


# === ROTA: Retorna casos com paginação ===
@app.route('/casos', methods=['GET'])
@requer_autenticacao
def listar():
    try:
        pagina = max(1, int(request.args.get('pagina', 1)))
        limite = min(200, max(1, int(request.args.get('limite', 100))))
    except ValueError:
        return jsonify({"erro": "Parâmetros 'pagina' e 'limite' devem ser números inteiros."}), 400

    skip = (pagina - 1) * limite
    total = colecao.count_documents({})
    casos = list(colecao.find({}, {'_id': 0}).skip(skip).limit(limite))

    return jsonify({
        "total": total,
        "pagina": pagina,
        "limite": limite,
        "paginas": -(-total // limite),  # ceil sem math
        "dados": casos
    })


# === ROTA: Insere novo caso ===
@app.route('/casos', methods=['POST'])
@requer_autenticacao
def inserir():
    novo = request.get_json(silent=True)
    if not novo:
        return jsonify({"erro": "Corpo da requisição inválido ou ausente."}), 400

    faltando = [c for c in CAMPOS_OBRIGATORIOS_CASO if not novo.get(c)]
    if faltando:
        return jsonify({"erro": f"Campos obrigatórios ausentes: {', '.join(faltando)}"}), 422

    colecao.insert_one(novo)
    return jsonify({'msg': 'inserido com sucesso'}), 201


# === ROTA: Importância das variáveis ===
@app.route('/features', methods=['GET'])
@requer_autenticacao
def importancia_variaveis():
    features = ["tipoCrime", "cidade", "uf", "hora_num"]
    importancias = model.feature_importances_
    return jsonify({
        "features": features,
        "importances": importancias.tolist()
    })


CAMPOS_OBRIGATORIOS_PREDICT = ["tipoCrime", "cidade", "uf", "hora"]


# === ROTA: Predição de status ===
@app.route('/predict', methods=['POST'])
@requer_autenticacao
def predizer_status():
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Corpo da requisição inválido ou ausente."}), 400

    faltando = [c for c in CAMPOS_OBRIGATORIOS_PREDICT if not dados.get(c)]
    if faltando:
        return jsonify({"erro": f"Campos obrigatórios ausentes: {', '.join(faltando)}"}), 422

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
@requer_autenticacao
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
@requer_autenticacao
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
@requer_autenticacao
def enviar_relatorio():
    dados = request.get_json(silent=True)
    email_destino = dados.get('email', '')

    EMAIL_ORIGEM = os.getenv('EMAIL_ORIGEM')
    SENHA_APP = os.getenv('SENHA_APP')
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    try:
        SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
    except ValueError:
        logger.error("Variável SMTP_PORT contém valor não numérico.")
        return jsonify({"erro": "Configuração de SMTP inválida no servidor."}), 500

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
        data_atual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        pdf.cell(0, 10, f"Gerado em: {data_atual}", ln=True)
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

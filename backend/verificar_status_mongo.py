from pymongo import MongoClient
from urllib.parse import quote_plus
from collections import Counter

# Configuração da conexão
USUARIO = quote_plus("icanadareparos")
SENHA = quote_plus("ZzkSH4SSOzGSsnuc")
MONGO_URI = f"mongodb+srv://icanadareparos:ZzkSH4SSOzGSsnuc@dentalbase.hppnmdq.mongodb.net/forense?retryWrites=true&w=majority&appName=DentalBase"

# Conectar
client = MongoClient(MONGO_URI)
db = client["forense"]
colecao = db["ocorrencias"]

# Buscar todos os registros com campo "status"
dados = list(colecao.find({}, {"_id": 0, "status": 1}))

# Contar quantos existem por status
contagem = Counter(d["status"] for d in dados if "status" in d)

# Exibir resultados
print("📊 Distribuição de status no banco MongoDB:\n")
for status, qtd in contagem.items():
    print(f"✔️ {status}: {qtd} registros")

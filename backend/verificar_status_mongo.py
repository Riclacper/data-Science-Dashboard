import os
from pymongo import MongoClient
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("Variável de ambiente MONGO_URI não definida.")

client = MongoClient(MONGO_URI)
db = client["forense"]
colecao = db["ocorrencias"]

dados = list(colecao.find({}, {"_id": 0, "status": 1}))
contagem = Counter(d["status"] for d in dados if "status" in d)

print("📊 Distribuição de status no banco MongoDB:\n")
for status, qtd in contagem.items():
    print(f"✔️  {status}: {qtd} registros")

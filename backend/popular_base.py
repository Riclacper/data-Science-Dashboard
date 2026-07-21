import os
from pymongo import MongoClient
from random import choice, randint
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("Variável de ambiente MONGO_URI não definida.")

client = MongoClient(MONGO_URI)
db = client["forense"]
colecao = db["ocorrencias"]

tipos = ["Homicídio", "Furto", "Roubo", "Agressão", "Estupro"]
status_options = ["Em análise", "Concluído", "Arquivado", "Em investigação"]
ufs = ["PE", "SP", "RJ", "BA"]
cidades = ["Recife", "Olinda", "Salvador", "Campinas", "Rio de Janeiro"]

novos = []
for _ in range(100):
    doc = {
        "tipoCrime": choice(tipos),
        "status": choice(status_options),
        "data": "2024-06-17",
        "hora": f"{randint(0,23):02d}:{randint(0,59):02d}",
        "descricao": "Simulação de ocorrência",
        "nomeVitima": "Fulano de Tal",
        "local": "Rua Exemplo",
        "cidade": choice(cidades),
        "uf": choice(ufs),
        "coordenadas": "",
        "perito": "Dr. Simulado",
        "fotos": [],
        "anexos": []
    }
    novos.append(doc)

colecao.insert_many(novos)
print("✅ 100 ocorrências simuladas inseridas!")

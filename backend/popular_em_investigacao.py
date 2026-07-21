import os
from pymongo import MongoClient
from random import choice, randint
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("Variável de ambiente MONGO_URI não definida.")

client = MongoClient(MONGO_URI)
db = client["forense"]
colecao = db["ocorrencias"]

tipos = ["Furto", "Roubo", "Homicídio", "Agressão", "Estupro"]
cidades = ["Recife", "Campinas", "Salvador", "Natal"]
ufs = ["PE", "SP", "BA", "RN"]

novos = []
for _ in range(40):
    novos.append({
        "tipoCrime": choice(tipos),
        "status": "Em investigação",
        "data": datetime.today().strftime("%Y-%m-%d"),
        "hora": f"{randint(0, 23):02d}:{randint(0, 59):02d}",
        "descricao": "Inserido automaticamente para representar 'Em investigação'",
        "nomeVitima": "Fulano de Tal",
        "local": "Rua Exemplo",
        "cidade": choice(cidades),
        "uf": choice(ufs),
        "coordenadas": "",
        "perito": "Dr. Simulado",
        "fotos": [],
        "anexos": []
    })

colecao.insert_many(novos)
print("✅ 40 ocorrências com status 'Em investigação' inseridas.")

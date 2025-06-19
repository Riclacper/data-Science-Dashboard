from pymongo import MongoClient
from random import choice, randint
from datetime import datetime
from urllib.parse import quote_plus

# Conexão com Atlas
USUARIO = quote_plus("icanadareparos")
SENHA = quote_plus("ZzkSH4SSOzGSsnuc")
MONGO_URI = f"mongodb+srv://{USUARIO}:{SENHA}@dentalbase.hppnmdq.mongodb.net/forense?retryWrites=true&w=majority&appName=DentalBase"
client = MongoClient(MONGO_URI)

db = client["forense"]
colecao = db["ocorrencias"]

# Dados simulados
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

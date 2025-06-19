from pymongo import MongoClient
from urllib.parse import quote_plus
from random import choice, randint
from datetime import datetime

# Conexão com MongoDB Atlas
USUARIO = quote_plus("icanadareparos")
SENHA = quote_plus("ZzkSH4SSOzGSsnuc")
MONGO_URI = f"mongodb+srv://icanadareparos:ZzkSH4SSOzGSsnuc@dentalbase.hppnmdq.mongodb.net/forense?retryWrites=true&w=majority&appName=DentalBase"
client = MongoClient(MONGO_URI)

db = client["forense"]
colecao = db["ocorrencias"]

# Dados simulados
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
print("✅ 15 ocorrências com status 'Em investigação' inseridas.")

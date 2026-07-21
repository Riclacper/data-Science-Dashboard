import os
import json
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import pymongo
from dotenv import load_dotenv

load_dotenv()

# === Conexão com MongoDB ===
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("Variável de ambiente MONGO_URI não definida.")

client = pymongo.MongoClient(MONGO_URI)
db = client["forense"]
colecao = db["ocorrencias"]

# === Buscar dados da coleção ===
dados = list(colecao.find({}, {
    "_id": 0,
    "tipoCrime": 1,
    "cidade": 1,
    "uf": 1,
    "hora": 1,
    "status": 1
}))
df = pd.DataFrame(dados)

# === Pré-processamento ===
df.dropna(subset=["tipoCrime", "cidade", "uf", "hora", "status"], inplace=True)
df["hora_num"] = pd.to_numeric(df["hora"].str.extract(r"(\d+):")[0], errors="coerce")
df.dropna(subset=["hora_num"], inplace=True)

# === Codificação ===
le_tipoCrime = LabelEncoder()
df["tipoCrime"] = le_tipoCrime.fit_transform(df["tipoCrime"])

le_cidade = LabelEncoder()
df["cidade"] = le_cidade.fit_transform(df["cidade"])

le_uf = LabelEncoder()
df["uf"] = le_uf.fit_transform(df["uf"])

le_status = LabelEncoder()
df["status_encoded"] = le_status.fit_transform(df["status"])

print("📊 Distribuição original das classes:")
print(df["status_encoded"].value_counts())

# === Divisão e treino ===
X = df[["tipoCrime", "cidade", "uf", "hora_num"]]
y = df["status_encoded"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

modelo = RandomForestClassifier(random_state=42)
modelo.fit(X_train, y_train)

# === Avaliação ===
y_pred = modelo.predict(X_test)
relatorio = classification_report(y_test, y_pred, output_dict=True)

print("\n📉 Matriz de Confusão:")
print(confusion_matrix(y_test, y_pred))

# === Caminhos de saída ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, '..', 'model', 'model.pkl')

joblib.dump(modelo, MODEL_PATH)

with open(os.path.join(BASE_DIR, "avaliacao_modelo.json"), "w", encoding="utf-8") as f:
    json.dump(relatorio, f, ensure_ascii=False, indent=2)

with open(os.path.join(BASE_DIR, "classes_labels.json"), "w", encoding="utf-8") as f:
    json.dump({str(i): label for i, label in enumerate(le_status.classes_)}, f, ensure_ascii=False, indent=2)

print("✅ Modelo treinado e salvo com sucesso.")
print(f"📁 Modelo salvo em: {MODEL_PATH}")
print("📊 avaliacao_modelo.json e classes_labels.json salvos em backend/")

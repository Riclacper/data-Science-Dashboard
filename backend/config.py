import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")


def normalize_database_url(database_url: str) -> str:
    """Normaliza URLs do Supabase/PostgreSQL para o driver psycopg 3."""
    database_url = database_url.strip()
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


raw_database_url = os.getenv("DATABASE_URL", "").strip()
if not raw_database_url:
    raise RuntimeError(
        "DATABASE_URL não configurada. Copie .env.example para .env e informe a conexão do PostgreSQL/Supabase."
    )

DATABASE_URL = normalize_database_url(raw_database_url)

parsed_url = urlparse(DATABASE_URL.replace("postgresql+psycopg://", "postgresql://", 1))
if parsed_url.scheme not in {"postgresql", "sqlite"}:
    raise RuntimeError("DATABASE_URL deve apontar para PostgreSQL/Supabase ou SQLite.")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",")
    if origin.strip()
]

FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes", "on"}
MODEL_PATH = BASE_DIR / "model.pkl"
EVALUATION_PATH = BASE_DIR / "avaliacao_modelo.json"

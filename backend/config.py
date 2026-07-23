import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


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
if not (parsed_url.scheme == "postgresql" or parsed_url.scheme.startswith("sqlite")):
    raise RuntimeError("DATABASE_URL deve apontar para PostgreSQL/Supabase ou SQLite.")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000",
    ).split(",")
    if origin.strip()
]

FLASK_DEBUG = env_bool("FLASK_DEBUG", False)
AUTO_SEED_DEMO_DATA = env_bool("AUTO_SEED_DEMO_DATA", True)
DEMO_SAMPLE_SIZE = max(50, int(os.getenv("DEMO_SAMPLE_SIZE", "300")))
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(BASE_DIR / "model.pkl")))
EVALUATION_PATH = Path(
    os.getenv("EVALUATION_PATH", str(BASE_DIR / "avaliacao_modelo.json"))
)

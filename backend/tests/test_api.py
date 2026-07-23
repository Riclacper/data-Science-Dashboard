import importlib
import os
from pathlib import Path

import pytest

TEST_ROOT = Path(__file__).resolve().parent / ".runtime"
TEST_ROOT.mkdir(parents=True, exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_ROOT / 'test.db'}"
os.environ["MODEL_PATH"] = str(TEST_ROOT / "model.pkl")
os.environ["EVALUATION_PATH"] = str(TEST_ROOT / "avaliacao_modelo.json")
os.environ["DEMO_SAMPLE_SIZE"] = "80"
os.environ["AUTO_SEED_DEMO_DATA"] = "true"

app_module = importlib.import_module("app")


@pytest.fixture()
def client():
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()


def test_health_endpoint(client):
    response = client.get("/health")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["database"] == "ok"
    assert payload["registros"] >= 50


def test_paginated_cases(client):
    response = client.get("/casos/paginados?pagina=1&porPagina=10&uf=PE")
    payload = response.get_json()
    assert response.status_code == 200
    assert len(payload["items"]) <= 10
    assert all(item["uf"] == "PE" for item in payload["items"])


def test_incomplete_prediction_payload(client):
    response = client.post("/predict", json={"tipoCrime": "Furto"})
    assert response.status_code == 400
    assert "Campos obrigatórios ausentes" in response.get_json()["erro"]

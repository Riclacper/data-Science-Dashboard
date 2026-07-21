"""
Testes dos endpoints da API Flask.
"""
import json
import pytest


class TestHome:
    def test_home_retorna_200(self, client):
        res = client.get("/")
        assert res.status_code == 200


class TestLogin:
    def test_login_credenciais_corretas(self, client):
        res = client.post(
            "/login",
            data=json.dumps({"usuario": "admin", "senha": "senha_teste"}),
            content_type="application/json",
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data["ok"] is True
        assert "token" in data

    def test_login_credenciais_erradas(self, client):
        res = client.post(
            "/login",
            data=json.dumps({"usuario": "admin", "senha": "errada"}),
            content_type="application/json",
        )
        assert res.status_code == 401
        data = res.get_json()
        assert data["ok"] is False

    def test_login_payload_vazio(self, client):
        res = client.post("/login", content_type="application/json")
        assert res.status_code == 400


class TestCasos:
    def test_listar_sem_autenticacao(self, client):
        res = client.get("/casos")
        assert res.status_code == 401

    def test_listar_com_autenticacao(self, client, auth_headers):
        res = client.get("/casos", headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert "dados" in data
        assert "total" in data
        assert "paginas" in data

    def test_listar_paginacao_invalida(self, client, auth_headers):
        res = client.get("/casos?pagina=abc", headers=auth_headers)
        assert res.status_code == 400

    def test_inserir_sem_autenticacao(self, client):
        res = client.post(
            "/casos",
            data=json.dumps({"tipoCrime": "Furto"}),
            content_type="application/json",
        )
        assert res.status_code == 401

    def test_inserir_campos_faltando(self, client, auth_headers):
        res = client.post(
            "/casos",
            data=json.dumps({"tipoCrime": "Furto"}),
            headers=auth_headers,
        )
        assert res.status_code == 422
        data = res.get_json()
        assert "Campos obrigatórios ausentes" in data["erro"]

    def test_inserir_payload_invalido(self, client, auth_headers):
        res = client.post("/casos", headers=auth_headers)
        assert res.status_code == 400


class TestFeatures:
    def test_features_sem_autenticacao(self, client):
        res = client.get("/features")
        assert res.status_code == 401

    def test_features_com_autenticacao(self, client, auth_headers):
        res = client.get("/features", headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert "features" in data
        assert "importances" in data
        assert len(data["features"]) == len(data["importances"])


class TestPredict:
    def test_predict_sem_autenticacao(self, client):
        res = client.post("/predict", content_type="application/json")
        assert res.status_code == 401

    def test_predict_campos_faltando(self, client, auth_headers):
        res = client.post(
            "/predict",
            data=json.dumps({"tipoCrime": "Furto"}),
            headers=auth_headers,
        )
        assert res.status_code == 422

    def test_predict_payload_invalido(self, client, auth_headers):
        res = client.post("/predict", headers=auth_headers)
        assert res.status_code == 400

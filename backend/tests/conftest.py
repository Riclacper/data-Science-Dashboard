"""
Fixtures e configuração compartilhada para os testes do backend.
"""
import os
import hmac
import hashlib
import datetime

import pytest

# Define variáveis de ambiente mínimas ANTES de importar app
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017/forense_test")
os.environ.setdefault("LOGIN_USER", "admin")
os.environ.setdefault("LOGIN_PASS", "senha_teste")
os.environ.setdefault("SECRET_KEY", "chave_de_teste_super_secreta")


@pytest.fixture
def client(mocker):
    """Flask test client com MongoDB e modelo mockados."""
    mocker.patch("pymongo.MongoClient", autospec=True)

    mock_model = mocker.MagicMock()
    mock_model.feature_importances_ = [0.25, 0.25, 0.25, 0.25]
    mock_model.predict.return_value = [0]
    mocker.patch("joblib.load", return_value=mock_model)

    import pandas as pd
    from sklearn.preprocessing import LabelEncoder

    mock_df = pd.DataFrame({
        "tipoCrime": ["Furto", "Roubo", "Homicidio"],
        "cidade": ["Recife", "Salvador", "Campinas"],
        "uf": ["PE", "BA", "SP"],
    })

    mock_colecao = mocker.MagicMock()
    mock_colecao.find.return_value = mock_df.to_dict("records")
    mock_colecao.count_documents.return_value = 3

    mocker.patch("backend.app.colecao", mock_colecao)
    mocker.patch("backend.app.df_enc", mock_df)
    mocker.patch("backend.app.le_tipoCrime", LabelEncoder().fit(mock_df["tipoCrime"]))
    mocker.patch("backend.app.le_cidade", LabelEncoder().fit(mock_df["cidade"]))
    mocker.patch("backend.app.le_uf", LabelEncoder().fit(mock_df["uf"]))

    from backend.app import app as flask_app
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


@pytest.fixture
def auth_headers():
    """Gera cabecalho Authorization valido para os testes."""
    secret = os.environ["SECRET_KEY"]
    usuario = os.environ["LOGIN_USER"]
    payload = f"{usuario}:{datetime.date.today().isoformat()}"
    token = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return {"Authorization": "Bearer " + token, "Content-Type": "application/json"}

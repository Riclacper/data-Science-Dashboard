from datetime import date, time
from typing import Any

import joblib
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import select

from config import CORS_ORIGINS, EVALUATION_PATH, FLASK_DEBUG, MODEL_PATH
from database import SessionLocal, init_db
from models import Ocorrencia

REQUIRED_FIELDS = {"tipoCrime", "status", "cidade", "uf", "hora"}
FEATURES = ["tipoCrime", "cidade", "uf", "hora_num"]


def load_model_artifact() -> dict[str, Any] | None:
    if not MODEL_PATH.exists():
        return None
    artifact = joblib.load(MODEL_PATH)
    if not isinstance(artifact, dict) or "pipeline" not in artifact or "label_encoder" not in artifact:
        raise RuntimeError("model.pkl incompatível. Execute train_model_avaliado.py novamente.")
    return artifact


def parse_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def parse_time(value: Any) -> time | None:
    if value in (None, ""):
        return None
    if isinstance(value, time):
        return value
    return time.fromisoformat(str(value))


def payload_to_ocorrencia(payload: dict[str, Any]) -> Ocorrencia:
    missing = sorted(field for field in REQUIRED_FIELDS if payload.get(field) in (None, ""))
    if missing:
        raise ValueError(f"Campos obrigatórios ausentes: {', '.join(missing)}")

    uf = str(payload["uf"]).strip().upper()
    if len(uf) != 2:
        raise ValueError("O campo uf deve conter exatamente duas letras.")

    fotos = payload.get("fotos", [])
    anexos = payload.get("anexos", [])
    if not isinstance(fotos, list) or not isinstance(anexos, list):
        raise ValueError("Os campos fotos e anexos devem ser listas.")

    return Ocorrencia(
        tipo_crime=str(payload["tipoCrime"]).strip(),
        status=str(payload["status"]).strip(),
        data=parse_date(payload.get("data")),
        hora=parse_time(payload["hora"]),
        descricao=payload.get("descricao"),
        nome_vitima=payload.get("nomeVitima"),
        local=payload.get("local"),
        cidade=str(payload["cidade"]).strip(),
        uf=uf,
        coordenadas=payload.get("coordenadas"),
        perito=payload.get("perito"),
        fotos=fotos,
        anexos=anexos,
    )


def aggregate_feature_importances(artifact: dict[str, Any]) -> list[float]:
    pipeline = artifact["pipeline"]
    classifier = pipeline.named_steps["classifier"]
    preprocessor = pipeline.named_steps["preprocessor"]
    transformed_names = preprocessor.get_feature_names_out()

    totals = {feature: 0.0 for feature in FEATURES}
    for transformed_name, importance in zip(transformed_names, classifier.feature_importances_):
        if "tipoCrime_" in transformed_name:
            totals["tipoCrime"] += float(importance)
        elif "cidade_" in transformed_name:
            totals["cidade"] += float(importance)
        elif "uf_" in transformed_name:
            totals["uf"] += float(importance)
        elif transformed_name.endswith("hora_num"):
            totals["hora_num"] += float(importance)

    return [totals[feature] for feature in FEATURES]


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": CORS_ORIGINS}})
    init_db()

    try:
        model_artifact = load_model_artifact()
    except Exception as exc:
        model_artifact = None
        app.logger.error("Falha ao carregar o modelo: %s", exc)

    @app.get("/")
    def home():
        return jsonify(
            {
                "api": "Dashboard Forense",
                "database": "PostgreSQL/Supabase",
                "modelo_disponivel": model_artifact is not None,
            }
        )

    @app.get("/casos")
    def listar_casos():
        with SessionLocal() as session:
            casos = session.scalars(select(Ocorrencia).order_by(Ocorrencia.id.desc())).all()
            return jsonify([caso.to_dict() for caso in casos])

    @app.post("/casos")
    def inserir_caso():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"erro": "Envie um objeto JSON válido."}), 400

        try:
            ocorrencia = payload_to_ocorrencia(payload)
            with SessionLocal() as session:
                session.add(ocorrencia)
                session.commit()
                session.refresh(ocorrencia)
            return jsonify({"msg": "inserido com sucesso", "caso": ocorrencia.to_dict()}), 201
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400
        except Exception:
            app.logger.exception("Falha ao inserir ocorrência")
            return jsonify({"erro": "Não foi possível inserir a ocorrência."}), 500

    @app.get("/features")
    def importancia_variaveis():
        if model_artifact is None:
            return jsonify({"erro": "Modelo indisponível. Execute train_model_avaliado.py."}), 503
        return jsonify(
            {
                "features": FEATURES,
                "importances": aggregate_feature_importances(model_artifact),
            }
        )

    @app.post("/predict")
    def predizer_status():
        if model_artifact is None:
            return jsonify({"erro": "Modelo indisponível. Execute train_model_avaliado.py."}), 503

        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"erro": "Envie um objeto JSON válido."}), 400

        required = ["tipoCrime", "cidade", "uf", "hora"]
        missing = [field for field in required if payload.get(field) in (None, "")]
        if missing:
            return jsonify({"erro": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

        try:
            hora_num = int(str(payload["hora"]).split(":", maxsplit=1)[0])
            entrada = pd.DataFrame(
                [
                    {
                        "tipoCrime": str(payload["tipoCrime"]),
                        "cidade": str(payload["cidade"]),
                        "uf": str(payload["uf"]).upper(),
                        "hora_num": hora_num,
                    }
                ]
            )
            pred_index = model_artifact["pipeline"].predict(entrada)[0]
            label = model_artifact["label_encoder"].inverse_transform([int(pred_index)])[0]
            return jsonify({"previsao_status": str(label)})
        except (TypeError, ValueError, KeyError) as exc:
            return jsonify({"erro": f"Dados de predição inválidos: {exc}"}), 400
        except Exception:
            app.logger.exception("Falha na predição")
            return jsonify({"erro": "Não foi possível realizar a predição."}), 500

    @app.get("/teste")
    def teste_conexao():
        with SessionLocal() as session:
            primeiro = session.scalars(select(Ocorrencia).limit(1)).first()
            return jsonify(primeiro.to_dict() if primeiro else {"mensagem": "tabela vazia"})

    @app.get("/avaliar-modelo")
    def avaliar_modelo():
        if not EVALUATION_PATH.exists():
            return jsonify({"erro": "avaliacao_modelo.json não encontrado"}), 404
        return app.response_class(EVALUATION_PATH.read_text(encoding="utf-8"), mimetype="application/json")

    @app.get("/classes")
    def classes():
        if model_artifact is None:
            return jsonify({"erro": "Modelo indisponível. Execute train_model_avaliado.py."}), 503
        labels = model_artifact["label_encoder"].classes_
        return jsonify({str(index): str(label) for index, label in enumerate(labels)})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=FLASK_DEBUG)

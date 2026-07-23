from __future__ import annotations

from datetime import date, time
from math import ceil
from typing import Any

import joblib
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import String, and_, cast, func, or_, select

from config import (
    AUTO_SEED_DEMO_DATA,
    CORS_ORIGINS,
    DEMO_SAMPLE_SIZE,
    EVALUATION_PATH,
    FLASK_DEBUG,
    MODEL_PATH,
)
from database import SessionLocal, init_db
from models import Ocorrencia
from popular_base import DATASET_MARKER, popular
from train_model_avaliado import treinar

REQUIRED_FIELDS = {"tipoCrime", "status", "cidade", "uf", "hora"}
DEFAULT_FEATURES = [
    "tipoCrime",
    "cidade",
    "uf",
    "hora_num",
    "dias_desde_ocorrencia",
]
SORTABLE_FIELDS = {
    "id": Ocorrencia.id,
    "tipoCrime": Ocorrencia.tipo_crime,
    "status": Ocorrencia.status,
    "data": Ocorrencia.data,
    "hora": Ocorrencia.hora,
    "cidade": Ocorrencia.cidade,
    "uf": Ocorrencia.uf,
    "perito": Ocorrencia.perito,
}


def load_model_artifact() -> dict[str, Any] | None:
    if not MODEL_PATH.exists():
        return None
    artifact = joblib.load(MODEL_PATH)
    if not isinstance(artifact, dict) or "pipeline" not in artifact or "label_encoder" not in artifact:
        raise RuntimeError("model.pkl incompatível. Execute train_model_avaliado.py novamente.")
    return artifact


def initialize_production_data(sample_size: int = DEMO_SAMPLE_SIZE) -> dict[str, int | bool]:
    """Inicializa tabela, atualiza a base demonstrativa legada e treina o modelo."""
    init_db()

    with SessionLocal() as session:
        total = session.scalar(select(func.count()).select_from(Ocorrencia)) or 0
        legacy_total = session.scalar(
            select(func.count())
            .select_from(Ocorrencia)
            .where(Ocorrencia.descricao == "Simulação de ocorrência")
        ) or 0
        current_demo_total = session.scalar(
            select(func.count())
            .select_from(Ocorrencia)
            .where(Ocorrencia.descricao.like(f"{DATASET_MARKER}%"))
        ) or 0

    inserted = 0
    upgraded = False
    if AUTO_SEED_DEMO_DATA and total == 0:
        popular(sample_size)
        inserted = sample_size
        total = sample_size
    elif AUTO_SEED_DEMO_DATA and total > 0 and legacy_total == total and current_demo_total == 0:
        popular(sample_size, substituir=True)
        inserted = sample_size
        total = sample_size
        upgraded = True

    model_trained = False
    should_train = total >= 10 and (
        upgraded or not MODEL_PATH.exists() or not EVALUATION_PATH.exists()
    )
    if should_train:
        treinar()
        model_trained = True

    return {
        "total": int(total),
        "inserted": inserted,
        "upgraded": upgraded,
        "model_trained": model_trained,
    }


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


def aggregate_feature_importances(artifact: dict[str, Any]) -> tuple[list[str], list[float]]:
    pipeline = artifact["pipeline"]
    classifier = pipeline.named_steps["classifier"]
    preprocessor = pipeline.named_steps["preprocessor"]
    transformed_names = preprocessor.get_feature_names_out()
    features = artifact.get("features", DEFAULT_FEATURES)

    totals = {feature: 0.0 for feature in features}
    for transformed_name, importance in zip(
        transformed_names,
        classifier.feature_importances_,
        strict=False,
    ):
        for feature in features:
            if feature in transformed_name:
                totals[feature] += float(importance)
                break

    return features, [totals[feature] for feature in features]


def build_case_filters(args: Any) -> list[Any]:
    filters: list[Any] = []

    exact_fields = {
        "tipoCrime": Ocorrencia.tipo_crime,
        "status": Ocorrencia.status,
        "cidade": Ocorrencia.cidade,
        "uf": Ocorrencia.uf,
    }
    for param, column in exact_fields.items():
        value = str(args.get(param, "")).strip()
        if value:
            filters.append(column == value)

    date_from = parse_date(args.get("dataInicial"))
    date_to = parse_date(args.get("dataFinal"))
    if date_from:
        filters.append(Ocorrencia.data >= date_from)
    if date_to:
        filters.append(Ocorrencia.data <= date_to)

    search_term = str(args.get("busca", "")).strip()
    if search_term:
        pattern = f"%{search_term}%"
        filters.append(
            or_(
                Ocorrencia.tipo_crime.ilike(pattern),
                Ocorrencia.status.ilike(pattern),
                Ocorrencia.cidade.ilike(pattern),
                Ocorrencia.uf.ilike(pattern),
                Ocorrencia.descricao.ilike(pattern),
                Ocorrencia.perito.ilike(pattern),
                cast(Ocorrencia.id, String).ilike(pattern),
            )
        )

    return filters


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": CORS_ORIGINS}})

    initialization = initialize_production_data()
    app.logger.info(
        "Inicialização concluída: total=%s, inseridos=%s, atualizado=%s, modelo_treinado=%s",
        initialization["total"],
        initialization["inserted"],
        initialization["upgraded"],
        initialization["model_trained"],
    )

    try:
        model_artifact = load_model_artifact()
    except Exception as exc:  # pragma: no cover - proteção operacional
        model_artifact = None
        app.logger.error("Falha ao carregar o modelo: %s", exc)

    @app.get("/")
    def home():
        return jsonify(
            {
                "api": "Dashboard Forense",
                "versao": "2.0.0",
                "database": "PostgreSQL/Supabase",
                "dataset": "sintético controlado",
                "modelo_disponivel": model_artifact is not None,
                "documentacao": "https://github.com/Riclacper/data-Science-Dashboard",
            }
        )

    @app.get("/health")
    def health():
        with SessionLocal() as session:
            total = session.scalar(select(func.count()).select_from(Ocorrencia)) or 0
        return jsonify(
            {
                "status": "ok",
                "database": "ok",
                "registros": int(total),
                "modelo": "ok" if model_artifact is not None else "indisponível",
            }
        )

    @app.get("/casos")
    def listar_casos():
        with SessionLocal() as session:
            casos = session.scalars(
                select(Ocorrencia).order_by(Ocorrencia.data.desc(), Ocorrencia.id.desc())
            ).all()
            return jsonify([caso.to_dict() for caso in casos])

    @app.get("/casos/paginados")
    def listar_casos_paginados():
        try:
            page = max(1, int(request.args.get("pagina", 1)))
            per_page = min(100, max(5, int(request.args.get("porPagina", 10))))
        except ValueError:
            return jsonify({"erro": "Parâmetros de paginação inválidos."}), 400

        sort_by = request.args.get("ordenarPor", "data")
        sort_column = SORTABLE_FIELDS.get(sort_by, Ocorrencia.data)
        sort_order = request.args.get("ordem", "desc").lower()
        order_expression = sort_column.asc() if sort_order == "asc" else sort_column.desc()

        try:
            filters = build_case_filters(request.args)
        except ValueError as exc:
            return jsonify({"erro": f"Filtro inválido: {exc}"}), 400

        with SessionLocal() as session:
            count_stmt = select(func.count()).select_from(Ocorrencia)
            items_stmt = select(Ocorrencia)
            if filters:
                condition = and_(*filters)
                count_stmt = count_stmt.where(condition)
                items_stmt = items_stmt.where(condition)

            total = session.scalar(count_stmt) or 0
            items = session.scalars(
                items_stmt.order_by(order_expression, Ocorrencia.id.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            ).all()

        pages = ceil(total / per_page) if total else 0
        return jsonify(
            {
                "items": [item.to_dict() for item in items],
                "pagination": {
                    "page": page,
                    "perPage": per_page,
                    "total": int(total),
                    "pages": pages,
                    "hasNext": page < pages,
                    "hasPrevious": page > 1,
                },
                "sorting": {
                    "field": sort_by if sort_by in SORTABLE_FIELDS else "data",
                    "order": "asc" if sort_order == "asc" else "desc",
                },
            }
        )

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
        except Exception:  # pragma: no cover - proteção operacional
            app.logger.exception("Falha ao inserir ocorrência")
            return jsonify({"erro": "Não foi possível inserir a ocorrência."}), 500

    @app.get("/features")
    def importancia_variaveis():
        if model_artifact is None:
            return jsonify({"erro": "Modelo indisponível. Execute o treinamento."}), 503
        features, importances = aggregate_feature_importances(model_artifact)
        return jsonify({"features": features, "importances": importances})

    @app.post("/predict")
    def predizer_status():
        if model_artifact is None:
            return jsonify({"erro": "Modelo indisponível. Execute o treinamento."}), 503

        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"erro": "Envie um objeto JSON válido."}), 400

        required = ["tipoCrime", "cidade", "uf", "hora", "data"]
        missing = [field for field in required if payload.get(field) in (None, "")]
        if missing:
            return jsonify({"erro": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

        try:
            hora_num = int(str(payload["hora"]).split(":", maxsplit=1)[0])
            input_date = parse_date(payload["data"])
            if input_date is None:
                raise ValueError("Data inválida")
            reference_date = parse_date(model_artifact.get("reference_date")) or input_date
            age_days = max(0, (reference_date - input_date).days)
            entrada = pd.DataFrame(
                [
                    {
                        "tipoCrime": str(payload["tipoCrime"]),
                        "cidade": str(payload["cidade"]),
                        "uf": str(payload["uf"]).upper(),
                        "hora_num": hora_num,
                        "dias_desde_ocorrencia": age_days,
                    }
                ]
            )
            pred_index = model_artifact["pipeline"].predict(entrada)[0]
            probabilities = model_artifact["pipeline"].predict_proba(entrada)[0]
            label = model_artifact["label_encoder"].inverse_transform([int(pred_index)])[0]
            confidence = float(max(probabilities))
            return jsonify(
                {
                    "previsao_status": str(label),
                    "confianca": round(confidence, 4),
                    "aviso": "Resultado demonstrativo baseado em dados sintéticos.",
                }
            )
        except (TypeError, ValueError, KeyError) as exc:
            return jsonify({"erro": f"Dados de predição inválidos: {exc}"}), 400
        except Exception:  # pragma: no cover - proteção operacional
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
        return app.response_class(
            EVALUATION_PATH.read_text(encoding="utf-8"),
            mimetype="application/json",
        )

    @app.get("/classes")
    def classes():
        if model_artifact is None:
            return jsonify({"erro": "Modelo indisponível. Execute o treinamento."}), 503
        labels = model_artifact["label_encoder"].classes_
        return jsonify({str(index): str(label) for index, label in enumerate(labels)})

    @app.errorhandler(404)
    def not_found(_: Any):
        return jsonify({"erro": "Endpoint não encontrado."}), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=FLASK_DEBUG)

from __future__ import annotations

import json
from datetime import date

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sqlalchemy import select

from config import EVALUATION_PATH, MODEL_PATH
from database import SessionLocal
from models import Ocorrencia

CATEGORICAL_FEATURES = ["tipoCrime", "cidade", "uf"]
NUMERIC_FEATURES = ["hora_num", "dias_desde_ocorrencia"]
REQUIRED_COLUMNS = CATEGORICAL_FEATURES + ["hora", "data", "status"]


def carregar_dados() -> pd.DataFrame:
    with SessionLocal() as session:
        rows = session.execute(
            select(
                Ocorrencia.tipo_crime,
                Ocorrencia.cidade,
                Ocorrencia.uf,
                Ocorrencia.hora,
                Ocorrencia.data,
                Ocorrencia.status,
            )
        ).all()

    return pd.DataFrame(
        rows,
        columns=["tipoCrime", "cidade", "uf", "hora", "data", "status"],
    )


def preparar_dados(df: pd.DataFrame) -> tuple[pd.DataFrame, date]:
    if df.empty:
        raise RuntimeError("A tabela ocorrencias está vazia. Popule o banco antes de treinar.")

    df = df.dropna(subset=REQUIRED_COLUMNS).copy()
    df["data"] = pd.to_datetime(df["data"])
    reference_timestamp = df["data"].max()
    reference_date = reference_timestamp.date()
    df["hora_num"] = df["hora"].apply(
        lambda value: value.hour if hasattr(value, "hour") else None
    )
    df["dias_desde_ocorrencia"] = (reference_timestamp - df["data"]).dt.days.clip(lower=0)
    df = df.dropna(subset=NUMERIC_FEATURES)

    if len(df) < 10:
        raise RuntimeError("São necessários pelo menos 10 registros válidos para o treinamento.")
    if df["status"].nunique() < 2:
        raise RuntimeError("São necessárias pelo menos duas classes de status.")

    return df, reference_date


def treinar() -> None:
    df, reference_date = preparar_dados(carregar_dados())

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df["status"])
    X = df[CATEGORICAL_FEATURES + NUMERIC_FEATURES]

    class_counts = pd.Series(y).value_counts()
    stratify = y if class_counts.min() >= 2 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        stratify=stratify,
        random_state=42,
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
            ("numeric", "passthrough", NUMERIC_FEATURES),
        ]
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=320,
                    max_depth=10,
                    min_samples_leaf=2,
                    random_state=42,
                    class_weight="balanced",
                ),
            ),
        ]
    )

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    labels = list(range(len(label_encoder.classes_)))

    report = classification_report(
        y_test,
        y_pred,
        labels=labels,
        output_dict=True,
        zero_division=0,
    )
    report["confusion_matrix"] = confusion_matrix(y_test, y_pred, labels=labels).tolist()
    report["metadata"] = {
        "amostras": int(len(df)),
        "treino": int(len(X_train)),
        "teste": int(len(X_test)),
        "data_referencia": reference_date.isoformat(),
        "observacao": "Métricas obtidas sobre dados sintéticos controlados.",
    }

    artifact = {
        "pipeline": pipeline,
        "label_encoder": label_encoder,
        "features": CATEGORICAL_FEATURES + NUMERIC_FEATURES,
        "reference_date": reference_date.isoformat(),
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVALUATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, MODEL_PATH)
    EVALUATION_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Modelo salvo em: {MODEL_PATH}")
    print(f"Avaliação salva em: {EVALUATION_PATH}")


if __name__ == "__main__":
    treinar()

import json

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
NUMERIC_FEATURES = ["hora_num"]
REQUIRED_COLUMNS = CATEGORICAL_FEATURES + ["hora", "status"]


def carregar_dados() -> pd.DataFrame:
    with SessionLocal() as session:
        rows = session.execute(
            select(
                Ocorrencia.tipo_crime,
                Ocorrencia.cidade,
                Ocorrencia.uf,
                Ocorrencia.hora,
                Ocorrencia.status,
            )
        ).all()

    return pd.DataFrame(
        rows,
        columns=["tipoCrime", "cidade", "uf", "hora", "status"],
    )


def preparar_dados(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise RuntimeError("A tabela ocorrencias está vazia. Popule o banco antes de treinar.")

    df = df.dropna(subset=REQUIRED_COLUMNS).copy()
    df["hora_num"] = df["hora"].apply(lambda value: value.hour if hasattr(value, "hour") else None)
    df = df.dropna(subset=["hora_num"])

    if len(df) < 10:
        raise RuntimeError("São necessários pelo menos 10 registros válidos para o treinamento.")
    if df["status"].nunique() < 2:
        raise RuntimeError("São necessárias pelo menos duas classes de status.")

    return df


def treinar() -> None:
    df = preparar_dados(carregar_dados())

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df["status"])
    X = df[CATEGORICAL_FEATURES + NUMERIC_FEATURES]

    class_counts = pd.Series(y).value_counts()
    stratify = y if class_counts.min() >= 2 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
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
                    n_estimators=300,
                    random_state=42,
                    class_weight="balanced",
                ),
            ),
        ]
    )

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    report = classification_report(
        y_test,
        y_pred,
        labels=list(range(len(label_encoder.classes_))),
        target_names=[str(label) for label in label_encoder.classes_],
        output_dict=True,
        zero_division=0,
    )
    report["confusion_matrix"] = confusion_matrix(
        y_test,
        y_pred,
        labels=list(range(len(label_encoder.classes_))),
    ).tolist()

    artifact = {
        "pipeline": pipeline,
        "label_encoder": label_encoder,
        "features": CATEGORICAL_FEATURES + NUMERIC_FEATURES,
    }

    joblib.dump(artifact, MODEL_PATH)
    EVALUATION_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Modelo salvo em: {MODEL_PATH}")
    print(f"Avaliação salva em: {EVALUATION_PATH}")


if __name__ == "__main__":
    treinar()

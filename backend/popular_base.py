from __future__ import annotations

from datetime import date, time, timedelta
from random import Random

from sqlalchemy import delete

from database import SessionLocal, init_db
from models import Ocorrencia

DATASET_MARKER = "dataset-sintetico-v2"
REFERENCE_DATE = date(2026, 7, 22)
TIPOS = ["Homicídio", "Furto", "Roubo", "Agressão", "Estupro"]
CIDADES = {
    "Recife": "PE",
    "Olinda": "PE",
    "Salvador": "BA",
    "Campinas": "SP",
    "Rio de Janeiro": "RJ",
}
PERITOS = ["Equipe Alfa", "Equipe Beta", "Equipe Gama", "Equipe Delta"]
COORDENADAS = {
    "Recife": "-8.0476,-34.8770",
    "Olinda": "-8.0089,-34.8553",
    "Salvador": "-12.9777,-38.5016",
    "Campinas": "-22.9056,-47.0608",
    "Rio de Janeiro": "-22.9068,-43.1729",
}


def escolha_ponderada(rng: Random, opcoes: list[str], pesos: list[float]) -> str:
    return rng.choices(opcoes, weights=pesos, k=1)[0]


def pesos_status(tipo_crime: str, idade_dias: int) -> list[float]:
    if idade_dias <= 70:
        pesos = [0.85, 0.13, 0.01, 0.01]
    elif idade_dias <= 160:
        pesos = [0.05, 0.85, 0.09, 0.01]
    elif idade_dias <= 280:
        pesos = [0.01, 0.09, 0.85, 0.05]
    else:
        pesos = [0.01, 0.02, 0.17, 0.80]

    if tipo_crime in {"Homicídio", "Estupro"}:
        pesos[1] += 0.04
        pesos[2] = max(0.01, pesos[2] - 0.03)
    elif tipo_crime in {"Furto", "Roubo"}:
        pesos[2] += 0.03
        pesos[1] = max(0.01, pesos[1] - 0.02)

    total = sum(pesos)
    return [peso / total for peso in pesos]


def hora_por_tipo(rng: Random, tipo_crime: str) -> time:
    faixas = {
        "Furto": (8, 19),
        "Roubo": (16, 23),
        "Homicídio": (19, 23),
        "Agressão": (17, 23),
        "Estupro": (18, 23),
    }
    inicio, fim = faixas[tipo_crime]
    return time(rng.randint(inicio, fim), rng.choice([0, 10, 20, 30, 40, 50]))


def criar_ocorrencia(indice: int, rng: Random) -> Ocorrencia:
    tipo = escolha_ponderada(rng, TIPOS, [0.10, 0.30, 0.28, 0.22, 0.10])
    cidade = escolha_ponderada(
        rng,
        list(CIDADES),
        [0.32, 0.16, 0.18, 0.16, 0.18],
    )
    idade_dias = rng.randint(1, 365)
    data_ocorrencia = REFERENCE_DATE - timedelta(days=idade_dias)
    status = escolha_ponderada(
        rng,
        ["Em análise", "Em investigação", "Concluído", "Arquivado"],
        pesos_status(tipo, idade_dias),
    )

    return Ocorrencia(
        tipo_crime=tipo,
        status=status,
        data=data_ocorrencia,
        hora=hora_por_tipo(rng, tipo),
        descricao=f"{DATASET_MARKER}: registro {indice:03d} para demonstração técnica.",
        nome_vitima=f"Pessoa anonimizada {indice:03d}",
        local=f"Setor demonstrativo {rng.randint(1, 24):02d}",
        cidade=cidade,
        uf=CIDADES[cidade],
        coordenadas=COORDENADAS[cidade],
        perito=rng.choice(PERITOS),
        fotos=[],
        anexos=[],
    )


def popular(quantidade: int = 300, substituir: bool = False) -> None:
    init_db()
    rng = Random(42)

    with SessionLocal() as session:
        if substituir:
            session.execute(delete(Ocorrencia))
        session.add_all(criar_ocorrencia(indice, rng) for indice in range(1, quantidade + 1))
        session.commit()

    print(f"{quantidade} ocorrências sintéticas inseridas.")


if __name__ == "__main__":
    popular()

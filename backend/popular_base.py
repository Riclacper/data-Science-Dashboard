from datetime import date, time
from random import choice, randint

from database import SessionLocal, init_db
from models import Ocorrencia

TIPOS = ["Homicídio", "Furto", "Roubo", "Agressão", "Estupro"]
STATUS = ["Em análise", "Concluído", "Arquivado", "Em investigação"]
UFS = ["PE", "SP", "RJ", "BA"]
CIDADES = ["Recife", "Olinda", "Salvador", "Campinas", "Rio de Janeiro"]


def criar_ocorrencia() -> Ocorrencia:
    return Ocorrencia(
        tipo_crime=choice(TIPOS),
        status=choice(STATUS),
        data=date(2024, 6, 17),
        hora=time(randint(0, 23), randint(0, 59)),
        descricao="Simulação de ocorrência",
        nome_vitima="Fulano de Tal",
        local="Rua Exemplo",
        cidade=choice(CIDADES),
        uf=choice(UFS),
        coordenadas="",
        perito="Dr. Simulado",
        fotos=[],
        anexos=[],
    )


def popular(quantidade: int = 100) -> None:
    init_db()
    with SessionLocal() as session:
        session.add_all(criar_ocorrencia() for _ in range(quantidade))
        session.commit()
    print(f"{quantidade} ocorrências simuladas inseridas.")


if __name__ == "__main__":
    popular()

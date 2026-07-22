from datetime import date, time
from random import choice, randint

from database import SessionLocal, init_db
from models import Ocorrencia

TIPOS = ["Furto", "Roubo", "Homicídio", "Agressão", "Estupro"]
CIDADES = ["Recife", "Campinas", "Salvador", "Natal"]
UFS = ["PE", "SP", "BA", "RN"]


def criar_ocorrencia() -> Ocorrencia:
    return Ocorrencia(
        tipo_crime=choice(TIPOS),
        status="Em investigação",
        data=date.today(),
        hora=time(randint(0, 23), randint(0, 59)),
        descricao="Inserido automaticamente para representar 'Em investigação'",
        nome_vitima="Fulano de Tal",
        local="Rua Exemplo",
        cidade=choice(CIDADES),
        uf=choice(UFS),
        coordenadas="",
        perito="Dr. Simulado",
        fotos=[],
        anexos=[],
    )


def popular(quantidade: int = 40) -> None:
    init_db()
    with SessionLocal() as session:
        session.add_all(criar_ocorrencia() for _ in range(quantidade))
        session.commit()
    print(f"{quantidade} ocorrências com status 'Em investigação' inseridas.")


if __name__ == "__main__":
    popular()

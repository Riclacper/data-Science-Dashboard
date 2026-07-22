from sqlalchemy import func, select

from database import SessionLocal
from models import Ocorrencia


def verificar() -> None:
    with SessionLocal() as session:
        resultados = session.execute(
            select(Ocorrencia.status, func.count(Ocorrencia.id))
            .group_by(Ocorrencia.status)
            .order_by(Ocorrencia.status)
        ).all()

    print("Distribuição de status no PostgreSQL/Supabase:\n")
    for status, quantidade in resultados:
        print(f"- {status}: {quantidade} registros")


if __name__ == "__main__":
    verificar()

from datetime import date, time
from typing import Any

from sqlalchemy import Date, Integer, JSON, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Ocorrencia(Base):
    __tablename__ = "ocorrencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo_crime: Mapped[str] = mapped_column("tipoCrime", String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    data: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    hora: Mapped[time | None] = mapped_column(Time, nullable=True)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    nome_vitima: Mapped[str | None] = mapped_column("nomeVitima", String(200), nullable=True)
    local: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cidade: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    uf: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    coordenadas: Mapped[str | None] = mapped_column(String(100), nullable=True)
    perito: Mapped[str | None] = mapped_column(String(200), nullable=True)
    fotos: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    anexos: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tipoCrime": self.tipo_crime,
            "status": self.status,
            "data": self.data.isoformat() if self.data else None,
            "hora": self.hora.strftime("%H:%M") if self.hora else None,
            "descricao": self.descricao,
            "nomeVitima": self.nome_vitima,
            "local": self.local,
            "cidade": self.cidade,
            "uf": self.uf,
            "coordenadas": self.coordenadas,
            "perito": self.perito,
            "fotos": self.fotos or [],
            "anexos": self.anexos or [],
        }

from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class DiametroEstimadoSchema(BaseModel):
    minimo_km: float
    maximo_km: float


class AproximacaoSchema(BaseModel):
    data_aproximacao: str
    velocidade_relativa_kms: float
    distancia_perdida_km: float
    corpo_orbitado: str


class AsteroideSchema(BaseModel):
    id: str
    nome: str
    designacao: Optional[str]
    url_nasa: str
    magnitude_absoluta: float
    diametro_estimado: DiametroEstimadoSchema
    potencialmente_perigoso: bool
    aproximacoes_proximas: List[AproximacaoSchema]


class AsteroideResumoSchema(BaseModel):
    id: str
    nome: str


class ListaAsteroidesSchema(BaseModel):
    quantidade_total: int
    data_inicio: date
    data_fim: date
    asteroides: List[AsteroideResumoSchema]

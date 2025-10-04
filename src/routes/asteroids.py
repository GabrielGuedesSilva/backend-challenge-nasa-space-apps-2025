from http import HTTPStatus

import httpx
from fastapi import APIRouter, HTTPException, Request

from src.core.schemas.asteroid_schemas import (
    AproximacaoSchema,
    AsteroideResumoSchema,
    AsteroideSchema,
    DiametroEstimadoSchema,
    ListaAsteroidesSchema,
)

NASA_API_KEY = 'MPo2q666a93llKVNSWPQ0KcUafdvX38SrZ8dMi9T'
NASA_BASE_URL_NEO = 'https://api.nasa.gov/neo/rest/v1/neo'
NASA_BASE_URL_FEED = 'https://api.nasa.gov/neo/rest/v1/feed'


class AsteroidRouter:
    def __init__(self, container):
        self.user_service = container.user_service()
        self.router = APIRouter(
            prefix='/asteroids',
            tags=['asteroids'],
        )

        @self.router.get(
            '/{data_inicio}/{data_fim}/',
            status_code=HTTPStatus.OK,
            response_model=ListaAsteroidesSchema,
        )
        async def get_asteroids(
            request: Request, data_inicio: str, data_fim: str
        ):
            url = f'{NASA_BASE_URL_FEED}?start_date={data_inicio}&end_date={data_fim}&api_key={NASA_API_KEY}'

            async with httpx.AsyncClient(timeout=15.0) as client:
                resposta = await client.get(url)

            if resposta.status_code != 200:
                raise HTTPException(
                    status_code=resposta.status_code,
                    detail='Erro ao consultar API da NASA',
                )

            dados = resposta.json()

            total = dados.get('element_count', 0)
            objetos_por_data = dados.get('near_earth_objects', {})

            asteroides = []
            for data_str, lista in objetos_por_data.items():
                for item in lista:
                    asteroides.append(
                        AsteroideResumoSchema(
                            id=item['id'],
                            nome=item['name'],
                        )
                    )

            return ListaAsteroidesSchema(
                quantidade_total=total,
                data_inicio=data_inicio,
                data_fim=data_fim,
                asteroides=asteroides,
            )

        @self.router.get(
            '/{asteroid_id}',
            status_code=HTTPStatus.OK,
            response_model=AsteroideSchema,
        )
        async def get_asteroid(request: Request, asteroid_id: str):
            url = f'{NASA_BASE_URL_NEO}/{asteroid_id}?api_key={NASA_API_KEY}'
            async with httpx.AsyncClient(timeout=10.0) as client:
                resposta = await client.get(url)

            if resposta.status_code != 200:
                raise HTTPException(
                    status_code=resposta.status_code,
                    detail='Erro ao buscar dados na API da NASA',
                )

            dados = resposta.json()

            # Extrair dados principais
            diametro_km = dados['estimated_diameter']['kilometers']
            aproximacoes = []
            for item in dados.get('close_approach_data', []):
                aproximacoes.append(
                    AproximacaoSchema(
                        data_aproximacao=item['close_approach_date_full'],
                        velocidade_relativa_kms=float(
                            item['relative_velocity']['kilometers_per_second']
                        ),
                        distancia_perdida_km=float(
                            item['miss_distance']['kilometers']
                        ),
                        corpo_orbitado=item['orbiting_body'],
                    )
                )

            asteroide = AsteroideSchema(
                id=dados['id'],
                nome=dados['name'],
                designacao=dados.get('designation'),
                url_nasa=dados['nasa_jpl_url'],
                magnitude_absoluta=dados['absolute_magnitude_h'],
                diametro_estimado=DiametroEstimadoSchema(
                    minimo_km=diametro_km['estimated_diameter_min'],
                    maximo_km=diametro_km['estimated_diameter_max'],
                ),
                potencialmente_perigoso=dados[
                    'is_potentially_hazardous_asteroid'
                ],
                aproximacoes_proximas=aproximacoes,
            )

            return asteroide

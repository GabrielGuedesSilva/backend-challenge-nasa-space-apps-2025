import math
from http import HTTPStatus

import httpx
from fastapi import APIRouter, HTTPException, Query, Request

NASA_API_KEY = 'MPo2q666a93llKVNSWPQ0KcUafdvX38SrZ8dMi9T'
NASA_BASE_URL_NEO = 'https://api.nasa.gov/neo/rest/v1/neo'
EPQS_URL = 'https://epqs.nationalmap.gov/v1/json'
LAND_COVER_IDENTIFY = 'https://gis1.usgs.gov/arcgis/rest/services/gap/GAP_Land_Cover_NVC_Formation_Landuse/MapServer/identify'


class ImpactRouter:
    def __init__(self, container):
        self.router = APIRouter(
            prefix='/impact',
            tags=['impact'],
        )

        @self.router.get('/simulate', status_code=HTTPStatus.OK)
        async def simulate_impact(
            request: Request,
            asteroid_id: str = Query(...),
            lat: float = Query(...),
            lon: float = Query(...),
        ):
            # 1. Asteroide
            asteroid_url = (
                f'{NASA_BASE_URL_NEO}/{asteroid_id}?api_key={NASA_API_KEY}'
            )
            async with httpx.AsyncClient(timeout=15.0) as client:
                asteroid_resp = await client.get(asteroid_url)
            if asteroid_resp.status_code != 200:
                raise HTTPException(
                    status_code=asteroid_resp.status_code,
                    detail='Erro ao buscar dados do asteroide na NASA',
                )
            asteroid_data = asteroid_resp.json()
            diam_data = asteroid_data['estimated_diameter']['meters']
            diameter_m = (
                diam_data['estimated_diameter_min']
                + diam_data['estimated_diameter_max']
            ) / 2

            velocity_kms = 20.0
            if asteroid_data.get('close_approach_data'):
                try:
                    velocity_kms = float(
                        asteroid_data['close_approach_data'][0][
                            'relative_velocity'
                        ]['kilometers_per_second']
                    )
                except Exception:
                    pass

            # 2. Elevação
            elevation_m = None
            async with httpx.AsyncClient(timeout=10.0) as client:
                elev_resp = await client.get(
                    EPQS_URL,
                    params={
                        'x': lon,
                        'y': lat,
                        'units': 'Meters',
                        'output': 'json',
                    },
                )
            if elev_resp.status_code == 200:
                ej = elev_resp.json()
                elevation_m = (
                    ej.get('value')
                    or ej.get('elevation')
                    or ej.get('USGS_Elevation_Point_Query_Service', {})
                    .get('Elevation_Query', {})
                    .get('Elevation')
                )

            # 3. Land Cover (Identify)
            landcover_data = None
            identify_params = {
                'geometry': f'{lon},{lat}',
                'geometryType': 'esriGeometryPoint',
                'sr': 4326,
                'layers': 'all',
                'tolerance': 1,
                'mapExtent': f'{lon - 0.01},{lat - 0.01},{lon + 0.01},{lat + 0.01}',
                'imageDisplay': '512,512,96',
                'returnGeometry': 'false',
                'f': 'json',
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                land_resp = await client.get(
                    LAND_COVER_IDENTIFY, params=identify_params
                )
            if land_resp.status_code == 200:
                landcover_data = land_resp.json()

            # 4. Física do impacto (Collins et al.)
            rho_i = 3000  # densidade impactor
            rho_t = 2500  # densidade alvo média
            radius = diameter_m / 2
            volume = (4 / 3) * math.pi * (radius**3)
            mass = rho_i * volume

            v = velocity_kms * 1000  # m/s
            energy_joules = 0.5 * mass * v**2
            energy_megatons = energy_joules / 4.184e15

            # Diâmetro da cratera (m)
            k = 1.8
            crater_diameter_m = (
                k
                * ((rho_i / rho_t) ** (1 / 3))
                * (diameter_m**0.78)
                * (v**0.44)
            )
            crater_diameter_km = crater_diameter_m / 1000

            return {
                'asteroid': {
                    'id': asteroid_id,
                    'name': asteroid_data['name'],
                    'diameter_m': diameter_m,
                    'velocity_kms': velocity_kms,
                },
                'site': {
                    'lat': lat,
                    'lon': lon,
                    'elevation_m': elevation_m,
                    'land_cover': landcover_data,
                },
                'impact_estimate': {
                    'energy_megatons': energy_megatons,
                    'crater_diameter_km': crater_diameter_km,
                },
            }

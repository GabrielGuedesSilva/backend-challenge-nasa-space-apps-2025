import math
from http import HTTPStatus

import httpx
import requests
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

NASA_API_KEY = 'MPo2q666a93llKVNSWPQ0KcUafdvX38SrZ8dMi9T'
NASA_BASE_URL_NEO = 'https://api.nasa.gov/neo/rest/v1/neo'
EPQS_URL = 'https://epqs.nationalmap.gov/v1/json'
LAND_COVER_IDENTIFY = (
    'https://gis1.usgs.gov/arcgis/rest/services/gap/'
    'GAP_Land_Cover_NVC_Formation_Landuse/MapServer/identify'
)
UA = {'User-Agent': 'meteor-madness-context/1.4 (+spaceapps)'}


# ------------------------------
# Funções auxiliares
# ------------------------------
def elevation_epqs(lat: float, lon: float) -> float | None:
    for url in [EPQS_URL, 'https://elevation.nationalmap.gov/epqs/v1/json']:
        try:
            r = requests.get(
                url,
                params={'x': lon, 'y': lat, 'units': 'Meters'},
                headers=UA,
                timeout=10,
            )
            if r.status_code == 200:
                js = r.json()
                return (
                    js.get('value')
                    or js.get('Elevation')
                    or js.get('USGS_Elevation_Point_Query_Service', {})
                    .get('Elevation_Query', {})
                    .get('Elevation')
                )
        except Exception:
            continue
    return None


def population_at_point(lat: float, lon: float) -> int:
    try:
        fcc_url = 'https://geo.fcc.gov/api/census/block/find'
        fcc_params = {
            'latitude': lat,
            'longitude': lon,
            'format': 'json',
            'showall': 'true',
        }
        fr = requests.get(fcc_url, params=fcc_params, headers=UA, timeout=10)
        fjs = fr.json()
        fips_blk = fjs.get('Block', {}).get('FIPS')
        if not fips_blk or len(fips_blk) != 15:
            return 0
        state, county, tract, block = (
            fips_blk[0:2],
            fips_blk[2:5],
            fips_blk[5:11],
            fips_blk[11:15],
        )
        cen_url = 'https://api.census.gov/data/2020/dec/pl'
        cen_params = {
            'get': 'P1_001N',
            'for': f'block:{block}',
            'in': f'state:{state} county:{county} tract:{tract}',
        }
        cr = requests.get(cen_url, params=cen_params, headers=UA, timeout=10)
        rows = cr.json()
        if len(rows) >= 2:
            return int(rows[1][0])
    except Exception:
        return 0
    return 0


def building_count_overpass(
    lat: float, lon: float, radius_m: int = 1000
) -> int | None:
    try:
        url = 'https://overpass-api.de/api/interpreter'
        query = f"""
        [out:json][timeout:25];
        (
          way["building"](around:{radius_m},{lat},{lon});
          relation["building"](around:{radius_m},{lat},{lon});
        );
        out count;
        """
        r = requests.post(url, data={'data': query}, headers=UA, timeout=25)
        js = r.json()
        elements = js.get('elements', [])
        if elements and 'tags' in elements[0]:
            return int(elements[0]['tags'].get('total', 0))
    except Exception:
        return None
    return None


def calcular_impacto(diameter_m, velocity_kms, rho_i, rho_t):
    radius = diameter_m / 2
    volume = (4 / 3) * math.pi * (radius**3)
    mass = rho_i * volume
    v = velocity_kms * 1000
    energy_joules = 0.5 * mass * v**2
    energy_megatons = energy_joules / 4.184e15
    k = 1.8
    crater_diameter_m = (
        k * ((rho_i / rho_t) ** (1 / 3)) * (diameter_m**0.78) * (v**0.44)
    )
    return mass, energy_megatons, crater_diameter_m / 1000


class ImpactInput(BaseModel):
    diameter_m: float
    velocity_kms: float
    density_kg_m3: float = 3000
    lat: float
    lon: float


# ------------------------------
# Classe principal
# ------------------------------
class ImpactRouter:
    def __init__(self, container):
        self.router = APIRouter(prefix='/impact', tags=['impact'])

        # === ROTA 1 ===
        @self.router.get('/simulate/{asteroid_id}', status_code=HTTPStatus.OK)
        async def simulate_impact(
            request: Request,
            asteroid_id: str,
            lat: float = Query(...),
            lon: float = Query(...),
        ):
            # Dados do asteroide
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f'{NASA_BASE_URL_NEO}/{asteroid_id}?api_key={NASA_API_KEY}'
                )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=resp.status_code, detail='Erro NASA'
                )
            js = resp.json()
            diam = js['estimated_diameter']['meters']
            diameter_m = (
                diam['estimated_diameter_min'] + diam['estimated_diameter_max']
            ) / 2
            velocity_kms = float(
                js['close_approach_data'][0]['relative_velocity'][
                    'kilometers_per_second'
                ]
            )

            # Física
            rho_i, rho_t = 3000, 2500
            mass, energy_mt, crater_km = calcular_impacto(
                diameter_m, velocity_kms, rho_i, rho_t
            )
            crater_radius_m = (crater_km * 1000) / 2  # raio em metros

            # Contexto do local
            elevation_epqs(lat, lon)
            pop_block = population_at_point(lat, lon)
            bld = building_count_overpass(lat, lon, radius_m=crater_radius_m)

            # Estimar população afetada
            crater_radius_km = crater_km / 2
            pop_est = (
                int(pop_block * (math.pi * (crater_radius_km**2) / 0.01))
                if pop_block > 0
                else 0
            )

            return {
                'velocity_kms': round(velocity_kms, 2),
                'mass_kg': mass,
                'energy_megatons_tnt': round(energy_mt, 2),
                'crater_diameter_km': round(crater_km, 2),
                'context': {
                    'population_estimated_affected': pop_est,
                    'buildings_within_m': round(crater_radius_m, 2),
                    'buildings_count': bld,
                },
            }

        # === ROTA 2 ===
        @self.router.post('/custom', status_code=HTTPStatus.OK)
        async def simulate_custom(request: Request, data: ImpactInput):
            # Física
            rho_t = 2500
            mass, energy_mt, crater_km = calcular_impacto(
                data.diameter_m, data.velocity_kms, data.density_kg_m3, rho_t
            )
            crater_radius_m = (crater_km * 1000) / 2

            # Contexto
            elevation_epqs(data.lat, data.lon)
            pop_block = population_at_point(data.lat, data.lon)
            bld = building_count_overpass(
                data.lat, data.lon, radius_m=crater_radius_m
            )

            # Estimar população afetada
            crater_radius_km = crater_km / 2
            pop_est = (
                int(pop_block * (math.pi * (crater_radius_km**2) / 0.01))
                if pop_block > 0
                else 0
            )

            return {
                'velocity_kms': round(data.velocity_kms, 2),
                'mass_kg': mass,
                'energy_megatons_tnt': round(energy_mt, 2),
                'crater_diameter_km': round(crater_km, 2),
                'context': {
                    'population_estimated_affected': pop_est,
                    'buildings_within_m': round(crater_radius_m, 2),
                    'buildings_count': bld,
                },
            }

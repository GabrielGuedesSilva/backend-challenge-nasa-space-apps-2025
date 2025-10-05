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
FCC_URL = 'https://geo.fcc.gov/api/census/block/find'
CENSUS_URL = 'https://api.census.gov/data/2020/dec/pl'


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


def calcular_profundidade_cratera(
    crater_diameter_km: float, elevation_m
) -> float:
    try:
        elevation_m = float(elevation_m)
    except (TypeError, ValueError):
        elevation_m = 0.0

    base_depth_km = (
        0.2 * crater_diameter_km
        if crater_diameter_km < 3
        else 0.1 * crater_diameter_km
    )
    correction_factor = max(0.5, 1 - (elevation_m / 10000))
    return base_depth_km * correction_factor


def calcular_efeitos_geologicos(
    energy_megatons_tnt: float, crater_diameter_km: float, ocean_impact=False
):
    E_J = energy_megatons_tnt * 4.184e15

    eta_values = [1e-6, 1e-5, 1e-4]
    magnitudes = []
    for eta in eta_values:
        E_seismic = eta * E_J
        mag = (math.log10(E_seismic) - 4.8) / 1.5
        magnitudes.append(round(mag, 2))

    tsunami_risk = 'none'
    if ocean_impact:
        if E_J > 1e18:
            tsunami_risk = 'regional'
        elif E_J > 1e17:
            tsunami_risk = 'local'

    mag_max = max(magnitudes)
    felt_radius_km = 0
    if mag_max >= 7:
        felt_radius_km = 1000
    elif mag_max >= 6:
        felt_radius_km = 500
    elif mag_max >= 5:
        felt_radius_km = 200
    elif mag_max >= 4:
        felt_radius_km = 50
    else:
        felt_radius_km = 10

    return {
        'energy_joules': E_J,
        'magnitude_estimate_range': magnitudes,
        'tsunami_risk': tsunami_risk,
        'felt_radius_km_est': felt_radius_km,
        'crater_radius_km': round(crater_diameter_km / 2, 2),
    }


def population_at_point(lat: float, lon: float) -> int:
    try:
        fr = requests.get(
            FCC_URL,
            params={
                'latitude': lat,
                'longitude': lon,
                'format': 'json',
                'showall': 'true',
            },
            headers=UA,
            timeout=10,
        )
        fjs = fr.json()
        fips_blk = fjs.get('Block', {}).get('FIPS')
        if not fips_blk or len(fips_blk) != 15:
            return 0

        state = fips_blk[0:2]
        county = fips_blk[2:5]
        tract = fips_blk[5:11]
        block = fips_blk[11:15]

        cr = requests.get(
            CENSUS_URL,
            params={
                'get': 'P1_001N',
                'for': f'block:{block}',
                'in': f'state:{state}+county:{county}+tract:{tract}',
            },
            headers=UA,
            timeout=10,
        )
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


class ImpactRouter:
    def __init__(self, container):
        self.router = APIRouter(prefix='/impact', tags=['impact'])

        @self.router.get('/population')
        async def get_population(
            lat: float | None = Query(None),
            lon: float | None = Query(None),
            state: str | None = Query(None),
        ):
            """
            Retorna população aproximada.
            - Se passar `lat` e `lon`, retorna população do bloco.
            - Se passar `state` (código FIPS do estado, ex: 47), retorna população do estado.
            """
            async with httpx.AsyncClient() as client:
                try:
                    if state:
                        # Consulta população do estado
                        census_resp = await client.get(
                            CENSUS_URL,
                            headers=UA,
                            params={
                                'get': 'P1_001N,NAME',
                                'for': f'state:{state}',
                            },
                            timeout=10,
                        )
                        census_resp.raise_for_status()
                        data = census_resp.json()
                        population = int(data[1][0])
                        state_name = data[1][1]
                        return {
                            'state': state_name,
                            'state_fips': state,
                            'population': population,
                        }

                    elif lat is not None and lon is not None:
                        # Consulta população do bloco (latitude/longitude)
                        fcc_resp = await client.get(
                            FCC_URL,
                            headers=UA,
                            params={
                                'latitude': lat,
                                'longitude': lon,
                                'format': 'json',
                                'showall': 'true',
                            },
                            timeout=10,
                        )
                        fcc_resp.raise_for_status()
                        fcc_data = fcc_resp.json()
                        fips = fcc_data['Block']['FIPS']

                        state_code = fips[:2]
                        county = fips[2:5]
                        tract = fips[5:11]
                        block = fips[11:]

                        census_resp = await client.get(
                            CENSUS_URL,
                            headers=UA,
                            params={
                                'get': 'P1_001N',
                                'for': f'block:{block}',
                                'in': f'state:{state_code}+county:{county}+tract:{tract}',
                            },
                            timeout=10,
                        )
                        census_resp.raise_for_status()
                        census_data = census_resp.json()
                        population = int(census_data[1][0])
                        return {
                            'lat': lat,
                            'lon': lon,
                            'population': population,
                        }

                    else:
                        raise HTTPException(
                            status_code=HTTPStatus.BAD_REQUEST,
                            detail='É necessário informar lat/lon ou state.',
                        )

                except httpx.HTTPStatusError as e:
                    return {
                        'error': f'HTTP error: {e.response.status_code}',
                        'details': str(e),
                    }
                except Exception as e:
                    return {
                        'error': 'Failed to fetch population',
                        'details': str(e),
                    }

        # Dentro da rota /simulate/{asteroid_id}
        @self.router.get('/simulate/{asteroid_id}', status_code=HTTPStatus.OK)
        async def simulate_impact(
            request: Request,
            asteroid_id: str,
            lat: float = Query(...),
            lon: float = Query(...),
        ):
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

            rho_i, rho_t = 3000, 2500
            mass, energy_mt, crater_km = calcular_impacto(
                diameter_m, velocity_kms, rho_i, rho_t
            )
            crater_radius_m = (crater_km * 1000) / 2

            elev_m = elevation_epqs(lat, lon)
            pop_block = population_at_point(lat, lon)
            bld = building_count_overpass(lat, lon, radius_m=crater_radius_m)

            crater_radius_km = crater_km / 2
            pop_est = (
                int(pop_block * (math.pi * (crater_radius_km**2) / 0.01))
                if pop_block > 0
                else 0
            )

            crater_depth_km = calcular_profundidade_cratera(crater_km, elev_m)

            return {
                'velocity_kms': round(velocity_kms, 2),
                'mass_kg': mass,
                'energy_megatons_tnt': round(energy_mt, 2),
                'crater_diameter_km': round(crater_km, 2),
                'crater_depth_km': crater_depth_km,
                'context': {
                    'elevation_m': elev_m,
                    'population_estimated_affected': pop_est,
                    'buildings_within_m': round(crater_radius_m, 2),
                    'buildings_count': bld,
                },
            }

        # Dentro da rota /custom
        @self.router.post('/custom', status_code=HTTPStatus.OK)
        async def simulate_custom(request: Request, data: ImpactInput):
            rho_t = 2500
            mass, energy_mt, crater_km = calcular_impacto(
                data.diameter_m, data.velocity_kms, data.density_kg_m3, rho_t
            )
            crater_radius_m = (crater_km * 1000) / 2

            elev_m = elevation_epqs(data.lat, data.lon)
            pop_block = population_at_point(data.lat, data.lon)
            bld = building_count_overpass(
                data.lat, data.lon, radius_m=crater_radius_m
            )

            crater_radius_km = crater_km / 2
            pop_est = (
                int(pop_block * (math.pi * (crater_radius_km**2) / 0.01))
                if pop_block > 0
                else 0
            )

            crater_depth_km = calcular_profundidade_cratera(crater_km, elev_m)

            return {
                'velocity_kms': round(data.velocity_kms, 2),
                'mass_kg': mass,
                'energy_megatons_tnt': round(energy_mt, 2),
                'crater_diameter_km': round(crater_km, 2),
                'crater_depth_km': crater_depth_km,
                'context': {
                    'elevation_m': elev_m,
                    'population_estimated_affected': pop_est,
                    'buildings_within_m': round(crater_radius_m, 2),
                    'buildings_count': bld,
                },
            }

        @self.router.post('/geological-effects', status_code=HTTPStatus.OK)
        async def geological_effects_endpoint(
            request: Request, data: ImpactInput
        ):
            rho_t = 2500
            mass, energy_mt, crater_km = calcular_impacto(
                data.diameter_m, data.velocity_kms, data.density_kg_m3, rho_t
            )
            efeitos = calcular_efeitos_geologicos(
                energy_mt, crater_km, ocean_impact=False
            )
            return efeitos

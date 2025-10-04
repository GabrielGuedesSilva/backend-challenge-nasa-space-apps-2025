import math
from http import HTTPStatus
import httpx
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel

# === Constantes ===
NASA_API_KEY = 'MPo2q666a93llKVNSWPQ0KcUafdvX38SrZ8dMi9T'
NASA_BASE_URL_NEO = 'https://api.nasa.gov/neo/rest/v1/neo'
EPQS_URL = 'https://epqs.nationalmap.gov/v1/json'
LAND_COVER_IDENTIFY = (
    'https://gis1.usgs.gov/arcgis/rest/services/gap/'
    'GAP_Land_Cover_NVC_Formation_Landuse/MapServer/identify'
)

# === Modelo de entrada da rota custom ===
class ImpactInput(BaseModel):
    diameter_m: float
    velocity_kms: float
    density_kg_m3: float = 3000
    lat: float
    lon: float

# === Função de cálculo físico ===
def calcular_impacto(diameter_m, velocity_kms, rho_i, rho_t):
    radius = diameter_m / 2
    volume = (4 / 3) * math.pi * (radius ** 3)
    mass = rho_i * volume
    v = velocity_kms * 1000
    energy_joules = 0.5 * mass * v**2
    energy_megatons = energy_joules / 4.184e15
    k = 1.8
    crater_diameter_m = (
        k * ((rho_i / rho_t) ** (1 / 3)) * (diameter_m ** 0.78) * (v ** 0.44)
    )
    return mass, energy_megatons, crater_diameter_m / 1000

# === Classe principal ===
class ImpactRouter:
    def __init__(self, container):
        self.router = APIRouter(prefix="/impact", tags=["impact"])

        # === ROTA 1: Usando ID da NASA ===
        @self.router.get("/simulate/{asteroid_id}", status_code=HTTPStatus.OK)
        async def simulate_impact(
            request: Request,
            asteroid_id: str,
            lat: float = Query(...),
            lon: float = Query(...),
        ):
            # 1. Dados do asteroide
            asteroid_url = f'{NASA_BASE_URL_NEO}/{asteroid_id}?api_key={NASA_API_KEY}'
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

            # 2. Elevação (EPQS)
            elevation_m = None
            async with httpx.AsyncClient(timeout=10.0) as client:
                elev_resp = await client.get(
                    EPQS_URL,
                    params={'x': lon, 'y': lat, 'units': 'Meters', 'output': 'json'},
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

            # 3. Land Cover (definir densidade alvo)
            rho_t = 2500
            async with httpx.AsyncClient(timeout=10.0) as client:
                land_resp = await client.get(
                    LAND_COVER_IDENTIFY,
                    params={
                        'geometry': f'{lon},{lat}',
                        'geometryType': 'esriGeometryPoint',
                        'sr': 4326,
                        'layers': 'all',
                        'tolerance': 1,
                        'mapExtent': f'{lon - 0.01},{lat - 0.01},{lon + 0.01},{lat + 0.01}',
                        'imageDisplay': '512,512,96',
                        'returnGeometry': 'false',
                        'f': 'json',
                    },
                )
            if land_resp.status_code == 200:
                try:
                    land_data = land_resp.json()
                    if 'results' in land_data and len(land_data['results']) > 0:
                        attrs = land_data['results'][0]['attributes']
                        land_class = (
                            attrs.get('Raster.nvc_class')
                            or attrs.get('Raster.nvc_form')
                            or ''
                        ).lower()
                        if 'water' in land_class:
                            rho_t = 1000
                        elif 'forest' in land_class or 'vegetation' in land_class:
                            rho_t = 1500
                        elif 'urban' in land_class or 'developed' in land_class:
                            rho_t = 2500
                except Exception:
                    pass

            # 4. Cálculo físico
            rho_i = 3000
            mass, energy_megatons, crater_diameter_km = calcular_impacto(
                diameter_m, velocity_kms, rho_i, rho_t
            )

            return {
                "velocity_kms": round(velocity_kms, 2),
                "mass_kg": mass,
                "energy_megatons_tnt": round(energy_megatons, 2),
                "crater_diameter_km": round(crater_diameter_km, 2),
            }

        # === ROTA 2: Dados customizados via body ===
        @self.router.post("/custom", status_code=HTTPStatus.OK)
        async def simulate_custom(request: Request, data: ImpactInput):
            # 1. Elevação (EPQS)
            elevation_m = None
            async with httpx.AsyncClient(timeout=10.0) as client:
                elev_resp = await client.get(
                    EPQS_URL,
                    params={'x': data.lon, 'y': data.lat, 'units': 'Meters', 'output': 'json'},
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

            # 2. Land Cover (define densidade alvo)
            rho_t = 2500
            async with httpx.AsyncClient(timeout=10.0) as client:
                land_resp = await client.get(
                    LAND_COVER_IDENTIFY,
                    params={
                        'geometry': f'{data.lon},{data.lat}',
                        'geometryType': 'esriGeometryPoint',
                        'sr': 4326,
                        'layers': 'all',
                        'tolerance': 1,
                        'mapExtent': f'{data.lon - 0.01},{data.lat - 0.01},{data.lon + 0.01},{data.lat + 0.01}',
                        'imageDisplay': '512,512,96',
                        'returnGeometry': 'false',
                        'f': 'json',
                    },
                )
            if land_resp.status_code == 200:
                try:
                    land_data = land_resp.json()
                    if 'results' in land_data and len(land_data['results']) > 0:
                        attrs = land_data['results'][0]['attributes']
                        land_class = (
                            attrs.get('Raster.nvc_class')
                            or attrs.get('Raster.nvc_form')
                            or ''
                        ).lower()
                        if 'water' in land_class:
                            rho_t = 1000
                        elif 'forest' in land_class or 'vegetation' in land_class:
                            rho_t = 1500
                        elif 'urban' in land_class or 'developed' in land_class:
                            rho_t = 2500
                except Exception:
                    pass

            # 3. Cálculo físico
            mass, energy_megatons, crater_diameter_km = calcular_impacto(
                data.diameter_m, data.velocity_kms, data.density_kg_m3, rho_t
            )

            return {
                "velocity_kms": round(data.velocity_kms, 2),
                "mass_kg": mass,
                "energy_megatons_tnt": round(energy_megatons, 2),
                "crater_diameter_km": round(crater_diameter_km, 2),
            }

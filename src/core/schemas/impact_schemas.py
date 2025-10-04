from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, Field


class RegionPoint(BaseModel):
    type: str = Field(..., description="Sempre 'Point' no MVP")
    coordinates: Tuple[float, float] = Field(..., description='[lon, lat]')

    @validator('type')
    def _must_be_point(cls, v):
        if v != 'Point':
            raise ValueError("region.type deve ser 'Point' no MVP")
        return v


class Overrides(BaseModel):
    velocity_kms: Optional[float] = Field(None, gt=0)
    diameter_m: Optional[float] = Field(None, gt=0)
    density_impactor: Optional[float] = Field(None, gt=0, description='kg/m³')
    angle_deg: Optional[float] = Field(45, ge=1, le=90)


class ImpactRequest(BaseModel):
    asteroid_id: str
    region: RegionPoint
    overrides: Optional[Overrides] = None


class ImpactResponse(BaseModel):
    asteroid: Dict[str, Any]
    site: Dict[str, Any]
    assumptions: Dict[str, Any]
    results: Dict[str, Any]
    sources: Dict[str, Any]

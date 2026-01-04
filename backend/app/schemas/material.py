"""material Pydantic schemas"""

from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, Field, ConfigDict


class ElementResponse(BaseModel):
    """element response schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    name: str
    atomic_number: int
    atomic_mass: float
    electronegativity: Optional[float] = None


class CompositionBase(BaseModel):
    """base composition schema"""

    element_symbol: str
    amount: float
    weight_fraction: Optional[float] = None
    atomic_fraction: Optional[float] = None


class CompositionResponse(BaseModel):
    """composition response schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    weight_fraction: Optional[float] = None
    atomic_fraction: Optional[float] = None
    element: ElementResponse


class MaterialBase(BaseModel):
    """base material schema"""

    material_id: str = Field(..., description="Unique material identifier (e.g., mp-1234)")
    formula: str = Field(..., description="Chemical formula")
    formula_pretty: str = Field(..., description="Pretty-printed formula")
    chemsys: str = Field(..., description="Chemical system (e.g., Fe-O)")
    nelements: int = Field(..., ge=1, description="Number of elements")


class MaterialCreate(MaterialBase):
    """schema for creating a material"""

    formula_anonymous: Optional[str] = None
    nsites: Optional[int] = None
    crystal_system: Optional[str] = None
    spacegroup_symbol: Optional[str] = None
    spacegroup_number: Optional[int] = None
    volume: Optional[float] = None
    density: Optional[float] = None
    source: str = "materials_project"
    source_id: Optional[str] = None


class MaterialUpdate(BaseModel):
    """schema for updating a material"""

    formula: Optional[str] = None
    formula_pretty: Optional[str] = None
    crystal_system: Optional[str] = None
    spacegroup_symbol: Optional[str] = None
    spacegroup_number: Optional[int] = None
    volume: Optional[float] = None
    density: Optional[float] = None


class MaterialResponse(MaterialBase):
    """material response schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    formula_anonymous: Optional[str] = None
    nsites: Optional[int] = None
    crystal_system: Optional[str] = None
    spacegroup_symbol: Optional[str] = None
    spacegroup_number: Optional[int] = None
    volume: Optional[float] = None
    density: Optional[float] = None
    density_atomic: Optional[float] = None
    source: str
    source_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MaterialDetailResponse(MaterialResponse):
    """detailed material response with related data"""

    compositions: List[CompositionResponse] = []
    # Properties and structure loaded separately for performance


class MaterialListResponse(BaseModel):
    items: List[MaterialResponse]
    total: int
    page: int
    page_size: int
    pages: int

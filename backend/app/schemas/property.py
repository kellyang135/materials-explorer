"""property and calculation Pydantic schemas"""

from datetime import datetime
from typing import Optional, Any, List

from pydantic import BaseModel, Field, ConfigDict


class PropertyBase(BaseModel):
    """base property schema"""

    name: str = Field(..., description="Property name")
    category: str = Field(..., description="Property category (electronic, magnetic, etc.)")
    value_numeric: Optional[float] = None
    value_string: Optional[str] = None
    value_json: Optional[Any] = None
    unit: Optional[str] = None
    uncertainty: Optional[float] = None


class PropertyCreate(PropertyBase):
    """schema for creating a property"""

    material_id: int
    source: str = "calculated"
    calculation_id: Optional[int] = None


class PropertyResponse(PropertyBase):
    """property response schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    created_at: datetime


class CalculationBase(BaseModel):
    """base calculation schema"""

    calc_type: str = Field(..., description="Calculation type (GGA, GGA+U, HSE, etc.)")
    functional: Optional[str] = None
    run_type: Optional[str] = None


class CalculationCreate(CalculationBase):
    """schema for creating a calculation"""

    material_id: int
    task_id: Optional[str] = None
    pseudopotential: Optional[str] = None
    is_hubbard: bool = False
    hubbard_u: Optional[Any] = None
    is_converged: bool = True
    energy_cutoff: Optional[float] = None
    kpoints: Optional[Any] = None
    energy: Optional[float] = None
    energy_per_atom: Optional[float] = None
    formation_energy_per_atom: Optional[float] = None
    energy_above_hull: Optional[float] = None
    is_stable: Optional[bool] = None
    band_gap: Optional[float] = None
    is_gap_direct: Optional[bool] = None
    cbm: Optional[float] = None
    vbm: Optional[float] = None
    efermi: Optional[float] = None
    total_magnetization: Optional[float] = None
    is_magnetic: Optional[bool] = None
    completed_at: Optional[datetime] = None


class CalculationResponse(BaseModel):
    """calculation response schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: Optional[str] = None
    calc_type: str
    functional: Optional[str] = None
    pseudopotential: Optional[str] = None
    run_type: Optional[str] = None
    is_hubbard: bool
    is_converged: bool
    energy_cutoff: Optional[float] = None
    energy: Optional[float] = None
    energy_per_atom: Optional[float] = None
    formation_energy_per_atom: Optional[float] = None
    energy_above_hull: Optional[float] = None
    is_stable: Optional[bool] = None
    band_gap: Optional[float] = None
    is_gap_direct: Optional[bool] = None
    cbm: Optional[float] = None
    vbm: Optional[float] = None
    efermi: Optional[float] = None
    total_magnetization: Optional[float] = None
    is_magnetic: Optional[bool] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class MaterialPropertiesResponse(BaseModel):
    """combined properties for a material"""

    material_id: str
    properties: List[PropertyResponse]
    calculations: List[CalculationResponse]

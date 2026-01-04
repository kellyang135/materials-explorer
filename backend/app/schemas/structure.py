"""structure Pydantic schemas"""

from typing import Optional, Any, List

from pydantic import BaseModel, Field, ConfigDict


class LatticeBase(BaseModel):
    """base lattice schema"""

    a: float = Field(..., description="Lattice parameter a (Angstrom)")
    b: float = Field(..., description="Lattice parameter b (Angstrom)")
    c: float = Field(..., description="Lattice parameter c (Angstrom)")
    alpha: float = Field(..., description="Angle alpha (degrees)")
    beta: float = Field(..., description="Angle beta (degrees)")
    gamma: float = Field(..., description="Angle gamma (degrees)")
    volume: float = Field(..., description="Unit cell volume (Angstrom^3)")
    matrix: List[List[float]] = Field(..., description="3x3 lattice matrix")


class LatticeResponse(LatticeBase):
    """lattice response schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int


class SiteBase(BaseModel):
    """base site schema"""

    species: str = Field(..., description="Element symbol")
    frac_coords: List[float] = Field(..., description="Fractional coordinates [x, y, z]")
    cart_coords: List[float] = Field(..., description="Cartesian coordinates [x, y, z]")
    occupancy: float = Field(default=1.0, description="Site occupancy")
    label: Optional[str] = None
    properties: Optional[Any] = None


class SiteResponse(SiteBase):
    """site response schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    site_index: int


class StructureBase(BaseModel):
    """base structure schema"""

    num_sites: int = Field(..., description="Number of atomic sites")
    is_ordered: bool = Field(default=True, description="Whether structure is ordered")
    spacegroup_number: Optional[int] = None
    spacegroup_symbol: Optional[str] = None
    point_group: Optional[str] = None
    crystal_system: Optional[str] = None


class StructureCreate(StructureBase):
    """schema for creating a structure"""

    material_id: int
    lattice: LatticeBase
    sites: List[SiteBase]
    cif_string: Optional[str] = None
    structure_json: Optional[Any] = None


class StructureResponse(StructureBase):
    """structure response schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    lattice: LatticeResponse
    sites: List[SiteResponse]
    cif_string: Optional[str] = None


class StructureSummary(BaseModel):
    """brief structure summary for list views"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    num_sites: int
    crystal_system: Optional[str] = None
    spacegroup_symbol: Optional[str] = None


class Structure3DData(BaseModel):
    """structure data formatted for 3D visualization"""

    lattice: LatticeBase
    sites: List[SiteBase]
    bonds: Optional[List[dict]] = None  

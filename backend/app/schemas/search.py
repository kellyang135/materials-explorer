"""search and prediction Pydantic schemas"""

from typing import Optional, List, Any

from pydantic import BaseModel, Field

from app.schemas.material import MaterialResponse
from app.schemas.structure import StructureResponse


class SearchFilters(BaseModel):
    """search filters for material queries"""

    elements: Optional[List[str]] = Field(
        None, description="List of elements to include"
    )
    exclude_elements: Optional[List[str]] = Field(
        None, description="List of elements to exclude"
    )
    chemsys: Optional[str] = Field(
        None, description="Chemical system (e.g., Fe-O)"
    )
    crystal_system: Optional[str] = Field(
        None, description="Crystal system (cubic, hexagonal, etc.)"
    )
    spacegroup_number: Optional[int] = Field(
        None, description="Space group number"
    )
    nelements_min: Optional[int] = Field(None, ge=1)
    nelements_max: Optional[int] = Field(None, le=20)
    band_gap_min: Optional[float] = Field(None, ge=0)
    band_gap_max: Optional[float] = Field(None)
    energy_above_hull_max: Optional[float] = Field(
        None, ge=0, description="Maximum energy above hull (eV/atom)"
    )
    is_stable: Optional[bool] = Field(None, description="Filter for stable materials")
    is_magnetic: Optional[bool] = Field(None)
    formation_energy_min: Optional[float] = Field(None)
    formation_energy_max: Optional[float] = Field(None)


class SearchQuery(BaseModel):
    """full search query with filters and pagination"""

    query: Optional[str] = Field(None, description="Text search query (formula, etc.)")
    filters: Optional[SearchFilters] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = Field(
        default="material_id",
        description="Field to sort by"
    )
    sort_desc: bool = Field(default=False)


class SearchResponse(BaseModel):
    """search results response"""

    items: List[MaterialResponse]
    total: int
    page: int
    page_size: int
    pages: int
    query: Optional[str] = None
    filters_applied: Optional[dict] = None


class CompareRequest(BaseModel):
    """request to compare multiple materials"""

    material_ids: List[str] = Field(
        ..., min_length=2, max_length=10,
        description="List of material IDs to compare"
    )
    include_structure: bool = Field(
        default=True, description="Include structure comparison"
    )


class MaterialComparison(BaseModel):
    """comparison data for a single material"""

    material: MaterialResponse
    structure: Optional[StructureResponse] = None
    band_gap: Optional[float] = None
    formation_energy: Optional[float] = None
    energy_above_hull: Optional[float] = None
    is_stable: Optional[bool] = None


class StructureSimilarity(BaseModel):
    """structure similarity between two materials"""

    material_id_1: str
    material_id_2: str
    similarity_score: float = Field(..., ge=0, le=1)
    method: str = Field(default="cosine", description="Similarity method used")


class CompareResponse(BaseModel):
    """response for material comparison"""

    materials: List[MaterialComparison]
    structure_similarities: Optional[List[StructureSimilarity]] = None


class PredictRequest(BaseModel):
    """request for ML prediction on a structure"""

    structure_json: Optional[Any] = Field(
        None, description="Structure in pymatgen JSON format"
    )
    cif_string: Optional[str] = Field(
        None, description="Structure in CIF format"
    )
    properties: List[str] = Field(
        default=["formation_energy", "band_gap"],
        description="Properties to predict"
    )


class PropertyPrediction(BaseModel):
    """predicted property value"""

    name: str
    value: float
    unit: Optional[str] = None
    uncertainty: Optional[float] = None
    model: str = Field(..., description="Model used for prediction")


class PredictResponse(BaseModel):
    """response for ML prediction"""

    predictions: List[PropertyPrediction]
    structure_formula: Optional[str] = None
    warnings: Optional[List[str]] = None


class PhaseDiagramRequest(BaseModel):
    """request for phase diagram data"""

    chemsys: str = Field(..., description="Chemical system (e.g., Li-Fe-O)")
    include_unstable: bool = Field(
        default=False, description="Include unstable phases"
    )


class PhaseDiagramEntry(BaseModel):
    """entry in a phase diagram"""

    material_id: str
    formula: str
    composition: dict
    formation_energy: float
    energy_above_hull: float
    is_stable: bool


class PhaseDiagramResponse(BaseModel):
    """phase diagram data response"""

    chemsys: str
    elements: List[str]
    entries: List[PhaseDiagramEntry]
    stable_entries: List[str]  # material_ids of stable phases

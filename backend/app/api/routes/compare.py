"""material comparison API routes"""

from itertools import combinations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import numpy as np

from app.db.session import get_db
from app.models.material import Material
from app.models.property import Calculation
from app.models.structure import Structure
from app.schemas.search import (
    CompareRequest,
    CompareResponse,
    MaterialComparison,
    StructureSimilarity,
)
from app.schemas.material import MaterialResponse
from app.schemas.structure import StructureResponse

router = APIRouter()


def calculate_structure_similarity(
    embedding1: list[float] | None,
    embedding2: list[float] | None,
) -> float | None:
    """
    calculate cosine similarity between two structure embeddings

    returns None if either embedding is missing
    """
    if embedding1 is None or embedding2 is None:
        return None

    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)

    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


@router.post("", response_model=CompareResponse)
async def compare_materials(
    request: CompareRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    compare multiple materials side by side

    returns comparison data
    - Basic material info
    - Key properties (band gap, formation energy, etc.)
    - Structure data (optional)
    - Structure similarity scores between pairs
    """
    # Fetch all requested materials
    query = (
        select(Material)
        .options(
            selectinload(Material.structure).selectinload(Structure.lattice),
            selectinload(Material.structure).selectinload(Structure.sites),
            selectinload(Material.calculations),
        )
        .where(Material.material_id.in_(request.material_ids))
    )
    result = await db.execute(query)
    materials = {m.material_id: m for m in result.scalars().all()}

    # Check all materials were found
    missing = set(request.material_ids) - set(materials.keys())
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Materials not found: {', '.join(missing)}"
        )

    # Build comparison data
    comparisons = []
    for mat_id in request.material_ids:
        material = materials[mat_id]

        # Get best calculation (prefer GGA+U or most recent)
        best_calc = None
        if material.calculations:
            # Sort by preference: GGA+U > GGA > others
            sorted_calcs = sorted(
                material.calculations,
                key=lambda c: (
                    0 if c.calc_type == "GGA+U" else (1 if c.calc_type == "GGA" else 2),
                    c.created_at,
                ),
            )
            best_calc = sorted_calcs[0]

        comparison = MaterialComparison(
            material=MaterialResponse.model_validate(material),
            structure=(
                StructureResponse.model_validate(material.structure)
                if request.include_structure and material.structure
                else None
            ),
            band_gap=best_calc.band_gap if best_calc else None,
            formation_energy=(
                best_calc.formation_energy_per_atom if best_calc else None
            ),
            energy_above_hull=best_calc.energy_above_hull if best_calc else None,
            is_stable=best_calc.is_stable if best_calc else None,
        )
        comparisons.append(comparison)

    # Calculate structure similarities between all pairs
    similarities = []
    if request.include_structure:
        for mat_id1, mat_id2 in combinations(request.material_ids, 2):
            mat1 = materials[mat_id1]
            mat2 = materials[mat_id2]

            similarity = calculate_structure_similarity(
                mat1.structure_embedding,
                mat2.structure_embedding,
            )

            if similarity is not None:
                similarities.append(
                    StructureSimilarity(
                        material_id_1=mat_id1,
                        material_id_2=mat_id2,
                        similarity_score=similarity,
                        method="cosine",
                    )
                )

    return CompareResponse(
        materials=comparisons,
        structure_similarities=similarities if similarities else None,
    )


@router.get("/similar/{material_id}")
async def find_similar_materials(
    material_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    find materials with similar crystal structures

    uses structure embeddings and cosine similarity to find
    the most structurally similar materials
    """
    # Get the target material
    query = select(Material).where(Material.material_id == material_id)
    result = await db.execute(query)
    target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(status_code=404, detail=f"Material {material_id} not found")

    if target.structure_embedding is None:
        raise HTTPException(
            status_code=400,
            detail=f"Material {material_id} has no structure embedding"
        )

    # Get all materials with embeddings
    # In production, use pgvector for efficient similarity search
    query = select(Material).where(
        Material.structure_embedding.isnot(None),
        Material.material_id != material_id,
    )
    result = await db.execute(query)
    candidates = result.scalars().all()

    # Calculate similarities
    similarities = []
    for candidate in candidates:
        sim = calculate_structure_similarity(
            target.structure_embedding,
            candidate.structure_embedding,
        )
        if sim is not None:
            similarities.append((candidate, sim))

    # Sort by similarity and take top N
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_similar = similarities[:limit]

    return {
        "material_id": material_id,
        "similar_materials": [
            {
                "material_id": mat.material_id,
                "formula": mat.formula_pretty,
                "similarity_score": score,
            }
            for mat, score in top_similar
        ],
    }

"""phase diagram API routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.material import Material
from app.models.property import Calculation
from app.schemas.search import (
    PhaseDiagramRequest,
    PhaseDiagramResponse,
    PhaseDiagramEntry,
)
from app.core.cache import cache

router = APIRouter()


def parse_chemsys(chemsys: str) -> list[str]:
    """parse chemical system string into sorted list of elements"""
    elements = [e.strip() for e in chemsys.split("-")]
    return sorted(elements)


def get_subsystems(elements: list[str]) -> list[str]:
    """
    get all subsystems of a chemical system.

    for Li-Fe-O, returns: Li, Fe, O, Li-Fe, Li-O, Fe-O, Li-Fe-O
    """
    from itertools import combinations

    subsystems = []
    for r in range(1, len(elements) + 1):
        for combo in combinations(elements, r):
            subsystems.append("-".join(sorted(combo)))
    return subsystems


@router.get("/{chemsys}", response_model=PhaseDiagramResponse)
async def get_phase_diagram(
    chemsys: str,
    include_unstable: bool = Query(False, description="Include unstable phases"),
    db: AsyncSession = Depends(get_db),
):
    """
    get phase diagram data for a chemical system

    the chemical system should be specified as element symbols
    separated by hyphens, like "Li-Fe-O" or "Fe-O".

    returns all phases in the system 
    - Formation energy
    - Energy above hull (stability measure)
    - Composition

    set include_unstable=True to include metastable phases.
    """
    # Validate and parse chemsys
    elements = parse_chemsys(chemsys)
    if len(elements) < 2:
        raise HTTPException(
            status_code=400,
            detail="Chemical system must contain at least 2 elements"
        )
    if len(elements) > 5:
        raise HTTPException(
            status_code=400,
            detail="Chemical system can contain at most 5 elements"
        )

    # Normalize chemsys
    normalized_chemsys = "-".join(elements)

    # Try cache
    cache_key = f"phase_diagram:{normalized_chemsys}:{include_unstable}"
    cached = await cache.get(cache_key)
    if cached:
        return PhaseDiagramResponse(**cached)

    # Get all subsystems
    subsystems = get_subsystems(elements)

    # Query materials in all subsystems with calculations
    query = (
        select(Material, Calculation)
        .join(Calculation, Material.id == Calculation.material_id)
        .where(
            and_(
                Material.chemsys.in_(subsystems),
                Calculation.formation_energy_per_atom.isnot(None),
            )
        )
    )

    result = await db.execute(query)
    rows = result.all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for chemical system {normalized_chemsys}"
        )

    # Process entries
    entries = []
    stable_entries = []

    for material, calc in rows:
        # Skip unstable if not requested
        if not include_unstable and calc.energy_above_hull and calc.energy_above_hull > 0.001:
            continue

        # Parse composition from formula (simplified)
        # In production, use pymatgen for proper parsing
        composition = {}
        for elem in elements:
            # This is simplified - should use proper formula parsing
            if elem in material.formula:
                composition[elem] = 1.0  # Placeholder

        entry = PhaseDiagramEntry(
            material_id=material.material_id,
            formula=material.formula_pretty,
            composition=composition,
            formation_energy=calc.formation_energy_per_atom,
            energy_above_hull=calc.energy_above_hull or 0.0,
            is_stable=(calc.energy_above_hull or 0.0) < 0.001,
        )
        entries.append(entry)

        if entry.is_stable:
            stable_entries.append(material.material_id)

    response = PhaseDiagramResponse(
        chemsys=normalized_chemsys,
        elements=elements,
        entries=entries,
        stable_entries=stable_entries,
    )

    # Cache result
    await cache.set(cache_key, response.model_dump(mode="json"), ttl=3600)

    return response


@router.get("/{chemsys}/hull")
async def get_convex_hull(
    chemsys: str,
    db: AsyncSession = Depends(get_db),
):
    """
    get convex hull vertices for a phase diagram
    returns the stable phases that form the convex hull,
    with their compositions in a format suitable for plotting
    """
    # Get phase diagram data
    phase_data = await get_phase_diagram(chemsys, include_unstable=False, db=db)

    # Extract stable entries for hull
    hull_points = []
    for entry in phase_data.entries:
        if entry.is_stable:
            hull_points.append({
                "material_id": entry.material_id,
                "formula": entry.formula,
                "composition": entry.composition,
                "formation_energy": entry.formation_energy,
            })

    return {
        "chemsys": phase_data.chemsys,
        "elements": phase_data.elements,
        "hull_vertices": hull_points,
        "num_stable": len(hull_points),
    }


@router.get("")
async def list_available_systems(
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """
    list available chemical systems in the database

    returns unique chemical systems that have phase diagram data
    """
    query = (
        select(Material.chemsys)
        .distinct()
        .order_by(Material.chemsys)
        .limit(limit)
    )

    result = await db.execute(query)
    systems = [row[0] for row in result.all()]

    return {
        "systems": systems,
        "total": len(systems),
    }

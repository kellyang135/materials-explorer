"""search API routes"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.material import Material, Composition, Element
from app.models.property import Calculation
from app.schemas.search import SearchQuery, SearchFilters, SearchResponse
from app.schemas.material import MaterialResponse

router = APIRouter()


def build_search_query(filters: SearchFilters | None, base_query):
    """build SQLAlchemy query from search filters"""
    if not filters:
        return base_query

    conditions = []

    # Element filters
    if filters.elements:
        # Materials must contain all specified elements
        for element in filters.elements:
            subquery = (
                select(Composition.material_id)
                .join(Element)
                .where(Element.symbol == element)
            )
            conditions.append(Material.id.in_(subquery))

    if filters.exclude_elements:
        # Materials must NOT contain any excluded elements
        for element in filters.exclude_elements:
            subquery = (
                select(Composition.material_id)
                .join(Element)
                .where(Element.symbol == element)
            )
            conditions.append(Material.id.notin_(subquery))

    # Chemical system
    if filters.chemsys:
        conditions.append(Material.chemsys == filters.chemsys)

    # Crystal system
    if filters.crystal_system:
        conditions.append(Material.crystal_system == filters.crystal_system)

    # Space group
    if filters.spacegroup_number:
        conditions.append(Material.spacegroup_number == filters.spacegroup_number)

    # Number of elements
    if filters.nelements_min:
        conditions.append(Material.nelements >= filters.nelements_min)
    if filters.nelements_max:
        conditions.append(Material.nelements <= filters.nelements_max)

    # Join with calculations for property filters
    needs_calc_join = any([
        filters.band_gap_min is not None,
        filters.band_gap_max is not None,
        filters.energy_above_hull_max is not None,
        filters.is_stable is not None,
        filters.is_magnetic is not None,
        filters.formation_energy_min is not None,
        filters.formation_energy_max is not None,
    ])

    if needs_calc_join:
        # Subquery for calculation-based filters
        calc_conditions = []

        if filters.band_gap_min is not None:
            calc_conditions.append(Calculation.band_gap >= filters.band_gap_min)
        if filters.band_gap_max is not None:
            calc_conditions.append(Calculation.band_gap <= filters.band_gap_max)
        if filters.energy_above_hull_max is not None:
            calc_conditions.append(
                Calculation.energy_above_hull <= filters.energy_above_hull_max
            )
        if filters.is_stable is not None:
            calc_conditions.append(Calculation.is_stable == filters.is_stable)
        if filters.is_magnetic is not None:
            calc_conditions.append(Calculation.is_magnetic == filters.is_magnetic)
        if filters.formation_energy_min is not None:
            calc_conditions.append(
                Calculation.formation_energy_per_atom >= filters.formation_energy_min
            )
        if filters.formation_energy_max is not None:
            calc_conditions.append(
                Calculation.formation_energy_per_atom <= filters.formation_energy_max
            )

        if calc_conditions:
            calc_subquery = (
                select(Calculation.material_id)
                .where(and_(*calc_conditions))
                .distinct()
            )
            conditions.append(Material.id.in_(calc_subquery))

    if conditions:
        base_query = base_query.where(and_(*conditions))

    return base_query


@router.get("", response_model=SearchResponse)
async def search_materials(
    query: str | None = Query(None, description="Search query (formula, etc.)"),
    elements: str | None = Query(None, description="Comma-separated elements to include"),
    exclude_elements: str | None = Query(None, description="Comma-separated elements to exclude"),
    chemsys: str | None = Query(None, description="Chemical system (e.g., Fe-O)"),
    crystal_system: str | None = Query(None),
    spacegroup_number: int | None = Query(None),
    nelements_min: int | None = Query(None, ge=1),
    nelements_max: int | None = Query(None, le=20),
    band_gap_min: float | None = Query(None, ge=0),
    band_gap_max: float | None = Query(None),
    energy_above_hull_max: float | None = Query(None, ge=0),
    is_stable: bool | None = Query(None),
    is_magnetic: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("material_id"),
    sort_desc: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """
    search materials with various filters
    - Elements (include/exclude)
    - Chemical system
    - Crystal system
    - Space group
    - Band gap range
    - Stability (energy above hull)
    - Magnetic properties
    """
    # Build filters from query params
    filters = SearchFilters(
        elements=elements.split(",") if elements else None,
        exclude_elements=exclude_elements.split(",") if exclude_elements else None,
        chemsys=chemsys,
        crystal_system=crystal_system,
        spacegroup_number=spacegroup_number,
        nelements_min=nelements_min,
        nelements_max=nelements_max,
        band_gap_min=band_gap_min,
        band_gap_max=band_gap_max,
        energy_above_hull_max=energy_above_hull_max,
        is_stable=is_stable,
        is_magnetic=is_magnetic,
    )

    # Base query
    base_query = select(Material)

    # Text search on formula
    if query:
        base_query = base_query.where(
            or_(
                Material.formula.ilike(f"%{query}%"),
                Material.formula_pretty.ilike(f"%{query}%"),
                Material.material_id.ilike(f"%{query}%"),
            )
        )

    # Apply filters
    filtered_query = build_search_query(filters, base_query)

    # Count total
    count_query = select(func.count()).select_from(filtered_query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Sorting
    sort_column = getattr(Material, sort_by, Material.material_id)
    if sort_desc:
        sort_column = sort_column.desc()
    filtered_query = filtered_query.order_by(sort_column)

    # Pagination
    offset = (page - 1) * page_size
    filtered_query = filtered_query.offset(offset).limit(page_size)

    # Execute
    result = await db.execute(filtered_query)
    materials = result.scalars().all()

    return SearchResponse(
        items=[MaterialResponse.model_validate(m) for m in materials],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
        query=query,
        filters_applied=filters.model_dump(exclude_none=True) if filters else None,
    )


@router.post("", response_model=SearchResponse)
async def search_materials_post(
    search: SearchQuery,
    db: AsyncSession = Depends(get_db),
):
    """
    search materials using POST with complex filters

    this endpoint accepts a JSON body for more complex search queries
    """
    base_query = select(Material)

    # Text search
    if search.query:
        base_query = base_query.where(
            or_(
                Material.formula.ilike(f"%{search.query}%"),
                Material.formula_pretty.ilike(f"%{search.query}%"),
                Material.material_id.ilike(f"%{search.query}%"),
            )
        )

    # Apply filters
    filtered_query = build_search_query(search.filters, base_query)

    # Count
    count_query = select(func.count()).select_from(filtered_query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Sort
    sort_column = getattr(Material, search.sort_by, Material.material_id)
    if search.sort_desc:
        sort_column = sort_column.desc()
    filtered_query = filtered_query.order_by(sort_column)

    # Paginate
    offset = (search.page - 1) * search.page_size
    filtered_query = filtered_query.offset(offset).limit(search.page_size)

    result = await db.execute(filtered_query)
    materials = result.scalars().all()

    return SearchResponse(
        items=[MaterialResponse.model_validate(m) for m in materials],
        total=total,
        page=search.page,
        page_size=search.page_size,
        pages=(total + search.page_size - 1) // search.page_size if total > 0 else 0,
        query=search.query,
        filters_applied=search.filters.model_dump(exclude_none=True) if search.filters else None,
    )

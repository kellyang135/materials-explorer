"""materials CRUD API routes"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.material import Material, Composition
from app.models.property import Property, Calculation
from app.models.structure import Structure
from app.schemas.material import (
    MaterialCreate,
    MaterialUpdate,
    MaterialResponse,
    MaterialListResponse,
    MaterialDetailResponse,
)
from app.schemas.property import PropertyResponse, CalculationResponse
from app.schemas.structure import StructureResponse
from app.core.cache import cache

router = APIRouter()


@router.get("", response_model=MaterialListResponse)
async def list_materials(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """list all materials with pagination"""
    # Get total count
    count_query = select(func.count(Material.id))
    total = (await db.execute(count_query)).scalar()

    # Get paginated results
    offset = (page - 1) * page_size
    query = (
        select(Material)
        .order_by(Material.material_id)
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    materials = result.scalars().all()

    return MaterialListResponse(
        items=[MaterialResponse.model_validate(m) for m in materials],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{material_id}", response_model=MaterialDetailResponse)
async def get_material(
    material_id: str,
    db: AsyncSession = Depends(get_db),
):
    """get a material by its ID (such as mp-1234)"""
    # Try cache first
    cache_key = f"material:{material_id}"
    cached = await cache.get(cache_key)
    if cached:
        return MaterialDetailResponse(**cached)

    # Query database with compositions
    query = (
        select(Material)
        .options(selectinload(Material.compositions).selectinload(Composition.element))
        .where(Material.material_id == material_id)
    )
    result = await db.execute(query)
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(status_code=404, detail=f"Material {material_id} not found")

    response = MaterialDetailResponse.model_validate(material)

    # Cache the result
    await cache.set(cache_key, response.model_dump(mode="json"))

    return response


@router.get("/{material_id}/properties", response_model=list[PropertyResponse])
async def get_material_properties(
    material_id: str,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """get all properties for a material"""
    # First get the material internal ID
    mat_query = select(Material.id).where(Material.material_id == material_id)
    mat_result = await db.execute(mat_query)
    mat_id = mat_result.scalar_one_or_none()

    if not mat_id:
        raise HTTPException(status_code=404, detail=f"Material {material_id} not found")

    # Query properties
    query = select(Property).where(Property.material_id == mat_id)
    if category:
        query = query.where(Property.category == category)

    result = await db.execute(query)
    properties = result.scalars().all()

    return [PropertyResponse.model_validate(p) for p in properties]


@router.get("/{material_id}/calculations", response_model=list[CalculationResponse])
async def get_material_calculations(
    material_id: str,
    calc_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """get all calculations for a material"""
    mat_query = select(Material.id).where(Material.material_id == material_id)
    mat_result = await db.execute(mat_query)
    mat_id = mat_result.scalar_one_or_none()

    if not mat_id:
        raise HTTPException(status_code=404, detail=f"Material {material_id} not found")

    query = select(Calculation).where(Calculation.material_id == mat_id)
    if calc_type:
        query = query.where(Calculation.calc_type == calc_type)

    result = await db.execute(query)
    calculations = result.scalars().all()

    return [CalculationResponse.model_validate(c) for c in calculations]


@router.get("/{material_id}/structure", response_model=StructureResponse)
async def get_material_structure(
    material_id: str,
    db: AsyncSession = Depends(get_db),
):
    """get the crystal structure for a material"""
    mat_query = select(Material.id).where(Material.material_id == material_id)
    mat_result = await db.execute(mat_query)
    mat_id = mat_result.scalar_one_or_none()

    if not mat_id:
        raise HTTPException(status_code=404, detail=f"Material {material_id} not found")

    query = (
        select(Structure)
        .options(
            selectinload(Structure.lattice),
            selectinload(Structure.sites),
        )
        .where(Structure.material_id == mat_id)
    )
    result = await db.execute(query)
    structure = result.scalar_one_or_none()

    if not structure:
        raise HTTPException(
            status_code=404,
            detail=f"Structure not found for material {material_id}"
        )

    # Convert JSON string coordinates to lists for response
    import json
    
    # Parse sites and convert coordinates
    sites_data = []
    for site in structure.sites:
        site_dict = {
            'id': site.id,
            'site_index': site.site_index,
            'species': site.species,
            'frac_coords': json.loads(site.frac_coords) if isinstance(site.frac_coords, str) else site.frac_coords,
            'cart_coords': json.loads(site.cart_coords) if isinstance(site.cart_coords, str) else site.cart_coords,
            'occupancy': site.occupancy,
            'label': site.label,
            'properties': site.properties
        }
        sites_data.append(site_dict)
    
    # Build response manually
    response_data = {
        'id': structure.id,
        'num_sites': structure.num_sites,
        'is_ordered': structure.is_ordered,
        'spacegroup_number': structure.spacegroup_number,
        'spacegroup_symbol': structure.spacegroup_symbol,
        'point_group': structure.point_group,
        'crystal_system': structure.crystal_system,
        'lattice': structure.lattice,
        'sites': sites_data,
        'cif_string': structure.cif_string
    }
    
    return StructureResponse(**response_data)


@router.post("", response_model=MaterialResponse, status_code=201)
async def create_material(
    material: MaterialCreate,
    db: AsyncSession = Depends(get_db),
):
    """create a new material"""
    # Check if material already exists
    existing = await db.execute(
        select(Material).where(Material.material_id == material.material_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Material {material.material_id} already exists"
        )

    db_material = Material(**material.model_dump())
    db.add(db_material)
    await db.commit()
    await db.refresh(db_material)

    return MaterialResponse.model_validate(db_material)


@router.patch("/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: str,
    material_update: MaterialUpdate,
    db: AsyncSession = Depends(get_db),
):
    """update a material"""
    query = select(Material).where(Material.material_id == material_id)
    result = await db.execute(query)
    db_material = result.scalar_one_or_none()

    if not db_material:
        raise HTTPException(status_code=404, detail=f"Material {material_id} not found")

    update_data = material_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_material, field, value)

    await db.commit()
    await db.refresh(db_material)

    # Invalidate cache
    await cache.delete(f"material:{material_id}")

    return MaterialResponse.model_validate(db_material)


@router.delete("/{material_id}", status_code=204)
async def delete_material(
    material_id: str,
    db: AsyncSession = Depends(get_db),
):
    """delete a material"""
    query = select(Material).where(Material.material_id == material_id)
    result = await db.execute(query)
    db_material = result.scalar_one_or_none()

    if not db_material:
        raise HTTPException(status_code=404, detail=f"Material {material_id} not found")

    await db.delete(db_material)
    await db.commit()

    # Invalidate cache
    await cache.delete(f"material:{material_id}")

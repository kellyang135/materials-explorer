#!/usr/bin/env python3
"""
data ingestion script to populate the database from Materials Project

usage:
    python -m scripts.ingest_data --chemsys Fe-O --limit 100
    python -m scripts.ingest_data --elements Fe,Co,Ni --stable-only
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, engine
from app.db.base import Base
from app.models.material import Material, Composition, Element
from app.models.property import Calculation
from app.models.structure import Structure, Lattice, Site
from scripts.mp_client import MaterialsProjectClient


# Periodic table data for seeding elements
ELEMENTS_DATA = [
    {"symbol": "H", "name": "Hydrogen", "atomic_number": 1, "atomic_mass": 1.008, "electronegativity": 2.20},
    {"symbol": "He", "name": "Helium", "atomic_number": 2, "atomic_mass": 4.003, "electronegativity": None},
    {"symbol": "Li", "name": "Lithium", "atomic_number": 3, "atomic_mass": 6.94, "electronegativity": 0.98},
    {"symbol": "Be", "name": "Beryllium", "atomic_number": 4, "atomic_mass": 9.012, "electronegativity": 1.57},
    {"symbol": "B", "name": "Boron", "atomic_number": 5, "atomic_mass": 10.81, "electronegativity": 2.04},
    {"symbol": "C", "name": "Carbon", "atomic_number": 6, "atomic_mass": 12.011, "electronegativity": 2.55},
    {"symbol": "N", "name": "Nitrogen", "atomic_number": 7, "atomic_mass": 14.007, "electronegativity": 3.04},
    {"symbol": "O", "name": "Oxygen", "atomic_number": 8, "atomic_mass": 15.999, "electronegativity": 3.44},
    {"symbol": "F", "name": "Fluorine", "atomic_number": 9, "atomic_mass": 18.998, "electronegativity": 3.98},
    {"symbol": "Ne", "name": "Neon", "atomic_number": 10, "atomic_mass": 20.180, "electronegativity": None},
    {"symbol": "Na", "name": "Sodium", "atomic_number": 11, "atomic_mass": 22.990, "electronegativity": 0.93},
    {"symbol": "Mg", "name": "Magnesium", "atomic_number": 12, "atomic_mass": 24.305, "electronegativity": 1.31},
    {"symbol": "Al", "name": "Aluminum", "atomic_number": 13, "atomic_mass": 26.982, "electronegativity": 1.61},
    {"symbol": "Si", "name": "Silicon", "atomic_number": 14, "atomic_mass": 28.086, "electronegativity": 1.90},
    {"symbol": "P", "name": "Phosphorus", "atomic_number": 15, "atomic_mass": 30.974, "electronegativity": 2.19},
    {"symbol": "S", "name": "Sulfur", "atomic_number": 16, "atomic_mass": 32.06, "electronegativity": 2.58},
    {"symbol": "Cl", "name": "Chlorine", "atomic_number": 17, "atomic_mass": 35.45, "electronegativity": 3.16},
    {"symbol": "Ar", "name": "Argon", "atomic_number": 18, "atomic_mass": 39.948, "electronegativity": None},
    {"symbol": "K", "name": "Potassium", "atomic_number": 19, "atomic_mass": 39.098, "electronegativity": 0.82},
    {"symbol": "Ca", "name": "Calcium", "atomic_number": 20, "atomic_mass": 40.078, "electronegativity": 1.00},
    {"symbol": "Fe", "name": "Iron", "atomic_number": 26, "atomic_mass": 55.845, "electronegativity": 1.83},
    {"symbol": "Co", "name": "Cobalt", "atomic_number": 27, "atomic_mass": 58.933, "electronegativity": 1.88},
    {"symbol": "Ni", "name": "Nickel", "atomic_number": 28, "atomic_mass": 58.693, "electronegativity": 1.91},
    {"symbol": "Cu", "name": "Copper", "atomic_number": 29, "atomic_mass": 63.546, "electronegativity": 1.90},
    {"symbol": "Zn", "name": "Zinc", "atomic_number": 30, "atomic_mass": 65.38, "electronegativity": 1.65},
]


async def seed_elements(db: AsyncSession) -> dict[str, int]:
    """seed the elements table and return symbol->id mapping"""
    element_map = {}

    for elem_data in ELEMENTS_DATA:
        # Check if element exists
        result = await db.execute(
            select(Element).where(Element.symbol == elem_data["symbol"])
        )
        element = result.scalar_one_or_none()

        if not element:
            element = Element(**elem_data)
            db.add(element)
            await db.flush()

        element_map[elem_data["symbol"]] = element.id

    await db.commit()
    return element_map


async def ingest_material(
    db: AsyncSession,
    mp_data: dict,
    element_map: dict[str, int],
) -> Material | None:
    """
    ingest a single material from Materials Project data

    returns the created Material or None if it already exists
    """
    material_id = mp_data.get("material_id")
    if not material_id:
        return None

    # Check if material exists
    result = await db.execute(
        select(Material).where(Material.material_id == material_id)
    )
    if result.scalar_one_or_none():
        print(f"  Skipping {material_id} (already exists)")
        return None

    # Create material
    material = Material(
        material_id=material_id,
        formula=mp_data.get("formula_pretty", ""),
        formula_pretty=mp_data.get("formula_pretty", ""),
        formula_anonymous=mp_data.get("formula_anonymous"),
        chemsys=mp_data.get("chemsys", ""),
        nelements=mp_data.get("nelements", 1),
        nsites=mp_data.get("nsites"),
        crystal_system=mp_data.get("symmetry", {}).get("crystal_system"),
        spacegroup_symbol=mp_data.get("symmetry", {}).get("symbol"),
        spacegroup_number=mp_data.get("symmetry", {}).get("number"),
        volume=mp_data.get("volume"),
        density=mp_data.get("density"),
        source="materials_project",
        source_id=material_id,
    )
    db.add(material)
    await db.flush()

    # Add composition
    composition_dict = mp_data.get("composition", {})
    if isinstance(composition_dict, dict):
        for symbol, amount in composition_dict.items():
            if symbol in element_map:
                comp = Composition(
                    material_id=material.id,
                    element_id=element_map[symbol],
                    amount=float(amount),
                )
                db.add(comp)

    # Add calculation data
    calc = Calculation(
        material_id=material.id,
        task_id=mp_data.get("task_id"),
        calc_type=mp_data.get("calc_type", "GGA"),
        run_type=mp_data.get("run_type"),
        is_hubbard=mp_data.get("is_hubbard", False),
        energy=mp_data.get("energy"),
        energy_per_atom=mp_data.get("energy_per_atom"),
        formation_energy_per_atom=mp_data.get("formation_energy_per_atom"),
        energy_above_hull=mp_data.get("energy_above_hull"),
        is_stable=mp_data.get("is_stable"),
        band_gap=mp_data.get("band_gap"),
        is_gap_direct=mp_data.get("is_gap_direct"),
        cbm=mp_data.get("cbm"),
        vbm=mp_data.get("vbm"),
        efermi=mp_data.get("efermi"),
        total_magnetization=mp_data.get("total_magnetization"),
        is_magnetic=mp_data.get("is_magnetic"),
    )
    db.add(calc)

    # Add structure if available
    structure_data = mp_data.get("structure")
    if structure_data and isinstance(structure_data, dict):
        lattice_data = structure_data.get("lattice", {})
        if lattice_data:
            lattice = Lattice(
                a=lattice_data.get("a", 0),
                b=lattice_data.get("b", 0),
                c=lattice_data.get("c", 0),
                alpha=lattice_data.get("alpha", 90),
                beta=lattice_data.get("beta", 90),
                gamma=lattice_data.get("gamma", 90),
                volume=lattice_data.get("volume", 0),
                matrix=lattice_data.get("matrix", [[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
            )
            db.add(lattice)
            await db.flush()

            structure = Structure(
                material_id=material.id,
                lattice_id=lattice.id,
                num_sites=len(structure_data.get("sites", [])),
                is_ordered=True,
                spacegroup_number=mp_data.get("symmetry", {}).get("number"),
                spacegroup_symbol=mp_data.get("symmetry", {}).get("symbol"),
                crystal_system=mp_data.get("symmetry", {}).get("crystal_system"),
                structure_json=structure_data,
            )
            db.add(structure)
            await db.flush()

            # Add sites
            for i, site_data in enumerate(structure_data.get("sites", [])):
                species = site_data.get("species", [{}])[0].get("element", "X")
                site = Site(
                    structure_id=structure.id,
                    species=species,
                    site_index=i,
                    frac_coords=site_data.get("abc", [0, 0, 0]),
                    cart_coords=site_data.get("xyz", [0, 0, 0]),
                    occupancy=site_data.get("species", [{}])[0].get("occu", 1.0),
                )
                db.add(site)

    await db.commit()
    print(f"  Ingested {material_id}: {material.formula_pretty}")
    return material


async def run_ingestion(
    chemsys: str | None = None,
    elements: list[str] | None = None,
    stable_only: bool = False,
    limit: int = 100,
):
    """run the data ingestion process"""
    print("Starting data ingestion...")

    # Initialize database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Seed elements
        print("Seeding elements...")
        element_map = await seed_elements(db)
        print(f"  {len(element_map)} elements ready")

        # Initialize MP client
        try:
            client = MaterialsProjectClient()
        except ValueError as e:
            print(f"Error: {e}")
            print("Please set the MP_API_KEY environment variable.")
            return

        # Fetch materials
        print(f"Fetching materials (limit={limit})...")
        materials = await client.search_materials(
            chemsys=chemsys,
            elements=elements,
            is_stable=stable_only if stable_only else None,
            limit=limit,
        )
        print(f"  Found {len(materials)} materials")

        # Ingest each material
        print("Ingesting materials...")
        ingested = 0
        for mp_data in materials:
            material = await ingest_material(db, mp_data, element_map)
            if material:
                ingested += 1

        print(f"\nIngestion complete: {ingested} new materials added")


def main():
    parser = argparse.ArgumentParser(
        description="Ingest materials data from Materials Project"
    )
    parser.add_argument(
        "--chemsys",
        type=str,
        help="Chemical system to fetch (e.g., Fe-O, Li-Fe-O)",
    )
    parser.add_argument(
        "--elements",
        type=str,
        help="Comma-separated list of elements to include",
    )
    parser.add_argument(
        "--stable-only",
        action="store_true",
        help="Only fetch thermodynamically stable materials",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of materials to fetch",
    )

    args = parser.parse_args()

    elements = args.elements.split(",") if args.elements else None

    asyncio.run(run_ingestion(
        chemsys=args.chemsys,
        elements=elements,
        stable_only=args.stable_only,
        limit=args.limit,
    ))


if __name__ == "__main__":
    main()

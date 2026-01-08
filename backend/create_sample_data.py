#!/usr/bin/env python3
"""
Create sample materials data for testing the 3D viewer
"""

import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal, engine
from app.db.base import Base
from app.models.material import Material, Element, Composition
from app.models.structure import Structure, Lattice, Site

# Sample structure data
SAMPLE_STRUCTURES = [
    {
        "material": {
            "material_id": "demo-si",
            "formula": "Si",
            "formula_pretty": "Si",
            "chemsys": "Si",
            "nelements": 1,
            "nsites": 2,
            "crystal_system": "cubic",
            "spacegroup_symbol": "Fd3m",
            "spacegroup_number": 227,
            "volume": 40.04,
            "density": 2.33,
            "source": "demo"
        },
        "structure": {
            "lattice": {
                "a": 5.431, "b": 5.431, "c": 5.431,
                "alpha": 90, "beta": 90, "gamma": 90,
                "volume": 160.19,
                "matrix": [
                    [5.431, 0.0, 0.0],
                    [0.0, 5.431, 0.0],
                    [0.0, 0.0, 5.431]
                ]
            },
            "sites": [
                {"species": "Si", "frac_coords": [0.0, 0.0, 0.0], "cart_coords": [0.0, 0.0, 0.0]},
                {"species": "Si", "frac_coords": [0.25, 0.25, 0.25], "cart_coords": [1.358, 1.358, 1.358]}
            ]
        },
        "elements": [{"symbol": "Si", "name": "Silicon", "atomic_number": 14, "atomic_mass": 28.085}]
    },
    {
        "material": {
            "material_id": "demo-nacl",
            "formula": "NaCl",
            "formula_pretty": "NaCl",
            "chemsys": "Na-Cl",
            "nelements": 2,
            "nsites": 2,
            "crystal_system": "cubic",
            "spacegroup_symbol": "Fm3m",
            "spacegroup_number": 225,
            "volume": 179.41,
            "density": 2.16,
            "source": "demo"
        },
        "structure": {
            "lattice": {
                "a": 5.64, "b": 5.64, "c": 5.64,
                "alpha": 90, "beta": 90, "gamma": 90,
                "volume": 179.41,
                "matrix": [
                    [5.64, 0.0, 0.0],
                    [0.0, 5.64, 0.0],
                    [0.0, 0.0, 5.64]
                ]
            },
            "sites": [
                {"species": "Na", "frac_coords": [0.0, 0.0, 0.0], "cart_coords": [0.0, 0.0, 0.0]},
                {"species": "Cl", "frac_coords": [0.5, 0.5, 0.5], "cart_coords": [2.82, 2.82, 2.82]}
            ]
        },
        "elements": [
            {"symbol": "Na", "name": "Sodium", "atomic_number": 11, "atomic_mass": 22.990},
            {"symbol": "Cl", "name": "Chlorine", "atomic_number": 17, "atomic_mass": 35.45}
        ]
    },
    {
        "material": {
            "material_id": "demo-feo",
            "formula": "FeO",
            "formula_pretty": "FeO",
            "chemsys": "Fe-O",
            "nelements": 2,
            "nsites": 2,
            "crystal_system": "cubic",
            "spacegroup_symbol": "Fm3m",
            "spacegroup_number": 225,
            "volume": 77.68,
            "density": 5.70,
            "source": "demo"
        },
        "structure": {
            "lattice": {
                "a": 4.31, "b": 4.31, "c": 4.31,
                "alpha": 90, "beta": 90, "gamma": 90,
                "volume": 80.15,
                "matrix": [
                    [4.31, 0.0, 0.0],
                    [0.0, 4.31, 0.0],
                    [0.0, 0.0, 4.31]
                ]
            },
            "sites": [
                {"species": "Fe", "frac_coords": [0.0, 0.0, 0.0], "cart_coords": [0.0, 0.0, 0.0]},
                {"species": "O", "frac_coords": [0.5, 0.5, 0.5], "cart_coords": [2.155, 2.155, 2.155]}
            ]
        },
        "elements": [
            {"symbol": "Fe", "name": "Iron", "atomic_number": 26, "atomic_mass": 55.845},
            {"symbol": "O", "name": "Oxygen", "atomic_number": 8, "atomic_mass": 15.999}
        ]
    }
]

async def create_sample_data():
    """Create sample materials data"""
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as db:
        
        # Create elements first
        elements_db = {}
        all_elements = []
        for sample in SAMPLE_STRUCTURES:
            all_elements.extend(sample["elements"])
        
        # Remove duplicates
        unique_elements = {elem["symbol"]: elem for elem in all_elements}.values()
        
        for elem_data in unique_elements:
            # Check if element already exists
            from sqlalchemy import select
            result = await db.execute(
                select(Element).where(Element.symbol == elem_data["symbol"])
            )
            element = result.scalar_one_or_none()
            
            if not element:
                element = Element(**elem_data)
                db.add(element)
                await db.flush()
                print(f"Created element: {elem_data['symbol']}")
            else:
                print(f"Element {elem_data['symbol']} already exists")
            
            elements_db[elem_data["symbol"]] = element.id
        
        # Create materials and structures
        for sample in SAMPLE_STRUCTURES:
            material_data = sample["material"]
            structure_data = sample["structure"]
            
            # Check if material already exists
            result = await db.execute(
                select(Material).where(Material.material_id == material_data["material_id"])
            )
            existing_material = result.scalar_one_or_none()
            
            if existing_material:
                print(f"Material {material_data['material_id']} already exists, skipping...")
                continue
            
            # Create material
            material = Material(**material_data)
            db.add(material)
            await db.flush()
            
            # Create lattice
            lattice_data = structure_data["lattice"]
            lattice = Lattice(**lattice_data)
            db.add(lattice)
            await db.flush()
            
            # Create structure
            structure = Structure(
                material_id=material.id,
                lattice_id=lattice.id,
                num_sites=len(structure_data["sites"]),
                is_ordered=True,
                spacegroup_number=material_data.get("spacegroup_number"),
                spacegroup_symbol=material_data.get("spacegroup_symbol"),
                crystal_system=material_data.get("crystal_system"),
                structure_json=structure_data
            )
            db.add(structure)
            await db.flush()
            
            # Create sites
            for i, site_data in enumerate(structure_data["sites"]):
                site = Site(
                    structure_id=structure.id,
                    species=site_data["species"],
                    site_index=i,
                    frac_coords=json.dumps(site_data["frac_coords"]),
                    cart_coords=json.dumps(site_data["cart_coords"]),
                    occupancy=1.0
                )
                db.add(site)
            
            # Create composition
            elements_in_material = {}
            for site_data in structure_data["sites"]:
                species = site_data["species"]
                elements_in_material[species] = elements_in_material.get(species, 0) + 1
            
            for species, count in elements_in_material.items():
                if species in elements_db:
                    comp = Composition(
                        material_id=material.id,
                        element_id=elements_db[species],
                        amount=float(count)
                    )
                    db.add(comp)
            
            print(f"Created material: {material.material_id} ({material.formula_pretty})")
        
        await db.commit()
        print("Sample data created successfully!")

async def main():
    await create_sample_data()

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Import materials data from mp_materials.json into the backend database
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to Python path
sys.path.append(str(Path(__file__).parent / "backend"))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal, engine
from app.db.base import Base
from app.models.material import Material, Element, Composition
from app.models.structure import Structure, Lattice, Site
from app.models.property import Calculation

async def create_database_tables():
    """Create database tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")

async def ensure_elements_exist(session, elements):
    """Ensure all required elements exist in the database."""
    
    elements_db = {}
    
    for element_symbol in elements:
        result = await session.execute(
            select(Element).where(Element.symbol == element_symbol)
        )
        element = result.scalar_one_or_none()
        
        if not element:
            try:
                from pymatgen.core import Element as PMGElement
                pmg_element = PMGElement(element_symbol)
                element = Element(
                    symbol=element_symbol,
                    name=pmg_element.name,
                    atomic_number=pmg_element.number,
                    atomic_mass=float(pmg_element.atomic_mass),
                    electronegativity=float(pmg_element.X) if pmg_element.X else None
                )
                session.add(element)
                await session.flush()
                print(f"  ➕ Created element: {element_symbol}")
            except Exception as e:
                print(f"  ⚠️ Error creating element {element_symbol}: {e}")
                continue
        
        elements_db[element_symbol] = element.id
    
    return elements_db

async def store_material(session, material_data, elements_db):
    """Store a single material in the database."""
    
    material_id = material_data.get('material_id')
    
    # Check if material already exists
    result = await session.execute(
        select(Material).where(Material.material_id == material_id)
    )
    if result.scalar_one_or_none():
        print(f"  ⏭️ {material_id} already exists, skipping...")
        return None
    
    # Calculate chemical system from structure
    structure_data = material_data.get('structure')
    elements = set()
    nsites = 0
    
    if structure_data and 'sites' in structure_data:
        nsites = len(structure_data['sites'])
        for site in structure_data['sites']:
            element_symbol = site.get('species', [{}])[0].get('element', 'X')
            elements.add(element_symbol)
    
    # Create chemsys (sorted elements separated by dashes)
    chemsys = "-".join(sorted(elements)) if elements else "Unknown"
    
    # Create material record
    material = Material(
        material_id=material_id,
        formula=material_data.get('formula'),
        formula_pretty=material_data.get('formula'),
        chemsys=chemsys,
        nelements=len(elements),
        nsites=nsites,
        crystal_system=material_data.get('crystal_system'),
        spacegroup_symbol=material_data.get('spacegroup_symbol'),
        spacegroup_number=material_data.get('spacegroup_number'),
        source=material_data.get('source', 'materials_project'),
        source_id=material_id
    )
    session.add(material)
    await session.flush()
    
    # Process structure
    structure_data = material_data.get('structure')
    if structure_data:
        # Create lattice
        lattice_data = structure_data.get('lattice', {})
        lattice = Lattice(
            a=float(lattice_data.get('a', 1.0)),
            b=float(lattice_data.get('b', 1.0)),
            c=float(lattice_data.get('c', 1.0)),
            alpha=float(lattice_data.get('alpha', 90.0)),
            beta=float(lattice_data.get('beta', 90.0)),
            gamma=float(lattice_data.get('gamma', 90.0)),
            volume=float(lattice_data.get('volume', 1.0)),
            matrix=lattice_data.get('matrix', [[1,0,0],[0,1,0],[0,0,1]])
        )
        session.add(lattice)
        await session.flush()
        
        # Create structure
        structure = Structure(
            material_id=material.id,
            lattice_id=lattice.id,
            num_sites=len(structure_data.get('sites', [])),
            is_ordered=True,
            spacegroup_number=material_data.get('spacegroup_number'),
            spacegroup_symbol=material_data.get('spacegroup_symbol'),
            crystal_system=material_data.get('crystal_system'),
            structure_json=structure_data
        )
        session.add(structure)
        await session.flush()
        
        # Create sites and track composition
        composition = {}
        for i, site_data in enumerate(structure_data.get('sites', [])):
            element_symbol = site_data.get('species', [{}])[0].get('element', 'X')
            
            # Track composition
            composition[element_symbol] = composition.get(element_symbol, 0) + 1
            
            # Create site
            site = Site(
                structure_id=structure.id,
                species=element_symbol,
                site_index=i,
                frac_coords=json.dumps(site_data.get('abc', [0,0,0])),
                cart_coords=json.dumps(site_data.get('xyz', [0,0,0])),
                occupancy=1.0
            )
            session.add(site)
        
        # Create composition records
        for element_symbol, count in composition.items():
            if element_symbol in elements_db:
                comp = Composition(
                    material_id=material.id,
                    element_id=elements_db[element_symbol],
                    amount=float(count)
                )
                session.add(comp)
    
    return material

async def import_materials():
    """Import materials from mp_materials.json."""
    
    # Load JSON data
    json_file = Path("mp_materials.json")
    if not json_file.exists():
        print(f"❌ {json_file} not found. Please run load_mp_materials.py first.")
        return False
    
    with open(json_file) as f:
        materials_data = json.load(f)
    
    print(f"📥 Found {len(materials_data)} materials to import")
    
    # Set up database
    await create_database_tables()
    
    async with AsyncSessionLocal() as session:
        # Collect all unique elements
        all_elements = set()
        for material_data in materials_data:
            structure_data = material_data.get('structure')
            if structure_data and 'sites' in structure_data:
                for site in structure_data['sites']:
                    element_symbol = site.get('species', [{}])[0].get('element', 'X')
                    all_elements.add(element_symbol)
        
        print(f"🧪 Ensuring {len(all_elements)} elements exist...")
        elements_db = await ensure_elements_exist(session, all_elements)
        
        # Import materials
        print(f"\n💎 Importing materials...")
        imported = 0
        
        for material_data in materials_data:
            try:
                material = await store_material(session, material_data, elements_db)
                if material:
                    imported += 1
                    print(f"  ✅ {material.material_id}: {material.formula_pretty}")
                
                # Commit after each material
                await session.commit()
                
            except Exception as e:
                print(f"  ❌ Error importing {material_data.get('material_id')}: {e}")
                await session.rollback()
                continue
    
    print(f"\n🎉 Successfully imported {imported} materials!")
    return imported > 0

async def main():
    """Main function."""
    print("📦 Materials Project Data Importer")
    print("==================================")
    
    success = await import_materials()
    
    if success:
        print("\n✨ Import complete!")
        print("🌐 Start the backend to see your new materials")
        print("   Backend: uvicorn app.main:app --reload")
        print("   Frontend: npm run dev")
    else:
        print("\n💥 Import failed")
        
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
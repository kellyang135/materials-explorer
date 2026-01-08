#!/usr/bin/env python3
"""
Load sample materials from Materials Project API for testing the 3D viewer.

This script fetches popular materials from Materials Project and stores them
in the local SQLite database with full structure information.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to Python path
sys.path.append(str(Path(__file__).parent / "backend"))

from app.db.session import AsyncSessionLocal, engine
from app.db.base import Base
from app.models.material import Material, Element, Composition
from app.models.structure import Structure, Lattice, Site
from backend.scripts.mp_client import MaterialsProjectClient

# List of interesting materials for testing
SAMPLE_MATERIALS = [
    {"material_id": "mp-149", "name": "Silicon", "formula": "Si"},
    {"material_id": "mp-13", "name": "Iron", "formula": "Fe"}, 
    {"material_id": "mp-22862", "name": "Sodium Chloride", "formula": "NaCl"},
    {"material_id": "mp-2534", "name": "Gallium Arsenide", "formula": "GaAs"},
    {"material_id": "mp-134", "name": "Aluminum", "formula": "Al"},
    {"material_id": "mp-1265", "name": "Quartz", "formula": "SiO2"},
    {"material_id": "mp-19017", "name": "Iron Oxide", "formula": "Fe2O3"},
    {"material_id": "mp-1143", "name": "Copper", "formula": "Cu"},
]

async def create_database_tables():
    """Create database tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")

async def store_material_data(session, material_data, structure_data):
    """Store a material and its structure in the database."""
    
    # First, handle elements
    elements_db = {}
    unique_elements = set()
    
    # Extract elements from structure sites
    if structure_data and 'sites' in structure_data:
        for site in structure_data['sites']:
            element_symbol = site.get('species', [{}])[0].get('element', 'X')
            unique_elements.add(element_symbol)
    
    # Create or get elements
    for element_symbol in unique_elements:
        from sqlalchemy import select
        result = await session.execute(
            select(Element).where(Element.symbol == element_symbol)
        )
        element = result.scalar_one_or_none()
        
        if not element:
            # Create basic element data
            from pymatgen.core import Element as PMGElement
            try:
                pmg_element = PMGElement(element_symbol)
                element = Element(
                    symbol=element_symbol,
                    name=pmg_element.name,
                    atomic_number=pmg_element.number,
                    atomic_mass=float(pmg_element.atomic_mass)
                )
                session.add(element)
                await session.flush()
                print(f"  ➕ Created element: {element_symbol}")
            except Exception as e:
                print(f"  ⚠️ Error creating element {element_symbol}: {e}")
                continue
        
        elements_db[element_symbol] = element.id
    
    # Create material
    material = Material(
        material_id=material_data.get('material_id'),
        formula=material_data.get('formula_pretty', material_data.get('formula')),
        formula_pretty=material_data.get('formula_pretty'),
        chemsys=material_data.get('chemsys'),
        nelements=material_data.get('nelements', len(unique_elements)),
        nsites=material_data.get('nsites'),
        crystal_system=material_data.get('crystal_system'),
        spacegroup_symbol=material_data.get('symmetry', {}).get('symbol'),
        spacegroup_number=material_data.get('symmetry', {}).get('number'),
        volume=material_data.get('volume'),
        density=material_data.get('density'),
        source="materials_project",
        source_id=material_data.get('material_id')
    )
    session.add(material)
    await session.flush()
    print(f"  💎 Created material: {material.material_id} ({material.formula_pretty})")
    
    # Create composition
    for element_symbol in unique_elements:
        if element_symbol in elements_db:
            # Count occurrences in sites
            count = sum(1 for site in structure_data.get('sites', []) 
                       if site.get('species', [{}])[0].get('element') == element_symbol)
            
            comp = Composition(
                material_id=material.id,
                element_id=elements_db[element_symbol],
                amount=float(count)
            )
            session.add(comp)
    
    # Create structure if available
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
            spacegroup_number=material_data.get('symmetry', {}).get('number'),
            spacegroup_symbol=material_data.get('symmetry', {}).get('symbol'),
            crystal_system=material_data.get('crystal_system'),
            structure_json=structure_data,
            cif_string=None
        )
        session.add(structure)
        await session.flush()
        
        # Create sites
        for i, site_data in enumerate(structure_data.get('sites', [])):
            element_symbol = site_data.get('species', [{}])[0].get('element', 'X')
            
            site = Site(
                structure_id=structure.id,
                species=element_symbol,
                site_index=i,
                frac_coords=json.dumps(site_data.get('abc', [0,0,0])),
                cart_coords=json.dumps(site_data.get('xyz', [0,0,0])),
                occupancy=1.0
            )
            session.add(site)
        
        print(f"  🏗️ Created structure with {len(structure_data.get('sites', []))} sites")

async def load_samples():
    """Load sample materials from Materials Project."""
    
    print("🔗 Connecting to Materials Project API...")
    
    try:
        mp_client = MaterialsProjectClient()
    except Exception as e:
        print(f"❌ Error connecting to Materials Project: {e}")
        print("💡 Make sure your API key is correct and you have internet access")
        return False
    
    print("🗄️ Setting up database...")
    await create_database_tables()
    
    async with AsyncSessionLocal() as session:
        loaded_count = 0
        
        for sample in SAMPLE_MATERIALS:
            material_id = sample["material_id"]
            name = sample["name"] 
            
            print(f"\n📥 Loading {name} ({material_id})...")
            
            try:
                # Check if already exists
                from sqlalchemy import select
                result = await session.execute(
                    select(Material).where(Material.material_id == material_id)
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    print(f"  ⏭️ {material_id} already exists, skipping...")
                    continue
                
                # Fetch material data
                material_data = await mp_client.get_material(material_id)
                if not material_data:
                    print(f"  ❌ No data found for {material_id}")
                    continue
                
                # Fetch structure data
                structure_data = await mp_client.get_structure(material_id)
                
                # Store in database
                await store_material_data(session, material_data, structure_data)
                loaded_count += 1
                
                # Commit after each material
                await session.commit()
                print(f"  ✅ Successfully loaded {name}")
                
            except Exception as e:
                print(f"  ❌ Error loading {material_id}: {e}")
                await session.rollback()
                continue
    
    print(f"\n🎉 Successfully loaded {loaded_count} materials!")
    return loaded_count > 0

async def main():
    """Main function."""
    print("🚀 Materials Project Data Loader")
    print("=================================")
    print("This script will load sample materials from Materials Project")
    print("for testing the 3D crystal structure viewer.\n")
    
    success = await load_samples()
    
    if success:
        print("\n✨ Sample data loaded successfully!")
        print("🌐 You can now start the backend and view materials in 3D")
        print("   Run: ./run_backend.sh")
    else:
        print("\n💥 Failed to load sample data")
        print("🔧 Please check your internet connection and API key")
        
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
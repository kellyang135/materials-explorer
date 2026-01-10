#!/usr/bin/env python3
"""
Enhanced Materials Project data loader for diverse materials database

This script fetches 100-200 diverse, stable materials from Materials Project
with varied crystal systems, chemical compositions, and structures for
comprehensive demos and testing.

Rate limit: 25 requests/second (Materials Project limit)
"""

import asyncio
import json
import time
import sys
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict

# Add backend to Python path
sys.path.append(str(Path(__file__).parent / "backend"))

from mp_api.client import MPRester
from pymatgen.core import Structure

# Configuration
API_KEY = "4qLIaDzBfyUgYLrnh6mu9tOsGbAshwYG"
TARGET_MATERIALS = 150  # Target number of materials to fetch
REQUEST_DELAY = 0.05  # 50ms delay = 20 req/sec (safely under 25/sec limit)

class DiverseMaterialsLoader:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.materials = []
        self.stats = defaultdict(int)
        
    def print_progress(self, message: str, step: int = None, total: int = None):
        """Print progress with optional step counter"""
        if step and total:
            progress = f"[{step}/{total}]"
            print(f"{progress} {message}")
        else:
            print(f"🔄 {message}")
    
    def get_diverse_search_strategies(self) -> List[Dict]:
        """Define search strategies for diverse material types"""
        return [
            # 1. Chemical systems with semiconductors 
            {
                "name": "Semiconductor Systems",
                "criteria": {
                    "chemsys": ["Si", "Ge", "Ga-As", "In-P", "Zn-O", "Cd-Te", "Ga-N", "Si-C"],
                    "limit": 20
                }
            },
            
            # 2. Binary compounds by chemical system
            {
                "name": "Binary Compounds",
                "criteria": {
                    "chemsys": ["Li-O", "Na-Cl", "Mg-O", "Ca-F", "K-Br", "Fe-O", "Cu-O", "Zn-S"],
                    "limit": 25
                }
            },
            
            # 3. Ternary oxides
            {
                "name": "Ternary Oxides", 
                "criteria": {
                    "chemsys": ["Al-Si-O", "Ti-Ba-O", "Mg-Al-O", "Ca-Ti-O", "Fe-Cr-O"],
                    "limit": 20
                }
            },
            
            # 4. Metal and alloy systems
            {
                "name": "Metals & Alloys",
                "criteria": {
                    "chemsys": ["Fe", "Al", "Cu", "Ni", "Ti", "Cr", "Mn", "Co", "Fe-Ni", "Al-Cu"],
                    "limit": 20
                }
            },
            
            # 5. Complex compounds (4+ elements)
            {
                "name": "Complex Compounds",
                "criteria": {
                    "chemsys": ["Ba-Ti-O", "La-Sr-Cu-O", "Y-Ba-Cu-O", "Pb-Zr-Ti-O"],
                    "limit": 15
                }
            },
            
            # 6. Carbon and layered materials
            {
                "name": "Layered Materials",
                "criteria": {
                    "elements": ["C"],  # Carbon compounds often layered
                    "limit": 15
                }
            },
            
            # 7. Alkali halides (ionic crystals)
            {
                "name": "Ionic Crystals",
                "criteria": {
                    "chemsys": ["Li-F", "Li-Cl", "Na-F", "Na-Cl", "K-F", "K-Cl", "K-Br", "K-I"],
                    "limit": 15
                }
            },
            
            # 8. Transition metal oxides
            {
                "name": "Transition Metal Oxides",
                "criteria": {
                    "chemsys": ["Sc-O", "Ti-O", "V-O", "Cr-O", "Mn-O", "Fe-O", "Co-O", "Ni-O", "Cu-O", "Zn-O"],
                    "limit": 20
                }
            }
        ]
    
    def filter_quality_materials(self, docs: List) -> List:
        """Filter for materials with complete data and good structures"""
        quality_materials = []
        
        for doc in docs:
            # Check required data
            if not hasattr(doc, 'structure') or doc.structure is None:
                continue
            
            # Check for reasonable structure size (for 3D visualization)
            try:
                structure = doc.structure
                if not hasattr(structure, 'num_sites') or structure.num_sites < 1 or structure.num_sites > 200:
                    continue
            except:
                continue
            
            # Must have material_id and formula
            if not hasattr(doc, 'material_id') or not hasattr(doc, 'formula_pretty'):
                continue
                
            quality_materials.append(doc)
        
        return quality_materials
    
    def ensure_crystal_system_diversity(self, materials: List) -> List:
        """Ensure we have representation from all crystal systems"""
        by_crystal_system = defaultdict(list)
        
        # Group by crystal system
        for material in materials:
            if hasattr(material, 'symmetry') and material.symmetry:
                system = str(material.symmetry.crystal_system).lower()
                by_crystal_system[system].append(material)
        
        # Ensure minimum representation from each system
        diverse_materials = []
        target_systems = ["cubic", "hexagonal", "tetragonal", "orthorhombic", "trigonal", "monoclinic", "triclinic"]
        
        for system in target_systems:
            if system in by_crystal_system:
                # Take up to 3 representatives from each system
                diverse_materials.extend(by_crystal_system[system][:3])
        
        # Add remaining materials to reach target count
        remaining = [m for m in materials if m not in diverse_materials]
        diverse_materials.extend(remaining[:TARGET_MATERIALS - len(diverse_materials)])
        
        return diverse_materials[:TARGET_MATERIALS]
    
    async def fetch_materials_batch(self, search_strategy: Dict) -> List:
        """Fetch materials for a specific search strategy"""
        strategy_name = search_strategy["name"]
        criteria = search_strategy["criteria"]
        limit = criteria.pop("limit", 20)
        
        self.print_progress(f"Fetching {strategy_name}...")
        
        with MPRester(self.api_key) as mpr:
            try:
                # Build search parameters using only supported fields
                search_params = {
                    "fields": [
                        "material_id", 
                        "formula_pretty", 
                        "symmetry",
                        "structure",
                        "volume",
                        "density",
                        "nelements",
                        "elements",
                        "chemsys"
                    ]
                }
                
                # Add only supported search criteria
                if "chemsys" in criteria:
                    # Search each chemical system individually due to API limitations
                    all_docs = []
                    chemsys_list = criteria["chemsys"][:3]  # Limit to 3 to avoid timeout
                    
                    for chemsys in chemsys_list:
                        try:
                            docs = mpr.materials.search(chemsys=chemsys, **search_params)
                            all_docs.extend(docs)
                            # Rate limiting between requests
                            await asyncio.sleep(REQUEST_DELAY)
                        except Exception as e:
                            self.print_progress(f"  ⚠️ Error with {chemsys}: {e}")
                            continue
                    
                    docs = all_docs
                
                elif "elements" in criteria:
                    # Search by elements
                    elements_list = criteria["elements"][:3]  # Limit to 3
                    docs = mpr.materials.search(elements=elements_list, **search_params)
                
                else:
                    # Fallback: search without specific criteria, then filter
                    docs = mpr.materials.search(**search_params)
                
                # Filter and limit results
                filtered_docs = self.filter_quality_materials(docs)
                limited_docs = filtered_docs[:limit]
                
                self.print_progress(f"✅ {strategy_name}: {len(limited_docs)} materials found")
                self.stats[strategy_name] = len(limited_docs)
                
                # Rate limiting
                await asyncio.sleep(REQUEST_DELAY)
                
                return limited_docs
                
            except Exception as e:
                self.print_progress(f"❌ Error fetching {strategy_name}: {e}")
                return []
    
    async def load_diverse_materials(self) -> List:
        """Main method to load diverse materials"""
        print("🚀 Enhanced Materials Project Data Loader")
        print("=" * 50)
        print(f"Target: {TARGET_MATERIALS} diverse, stable materials")
        print(f"Rate limit: {1/REQUEST_DELAY:.1f} req/sec (under MP's 25/sec limit)")
        print()
        
        strategies = self.get_diverse_search_strategies()
        all_materials = []
        
        # Execute search strategies
        for i, strategy in enumerate(strategies, 1):
            self.print_progress(f"Strategy {i}/{len(strategies)}: {strategy['name']}")
            materials = await self.fetch_materials_batch(strategy)
            all_materials.extend(materials)
            
            # Show running total
            unique_ids = set(m.material_id for m in all_materials)
            print(f"   Running total: {len(unique_ids)} unique materials")
            print()
        
        # Remove duplicates
        unique_materials = {}
        for material in all_materials:
            if material.material_id not in unique_materials:
                unique_materials[material.material_id] = material
        
        unique_list = list(unique_materials.values())
        print(f"📊 After deduplication: {len(unique_list)} unique materials")
        
        # Ensure crystal system diversity
        diverse_materials = self.ensure_crystal_system_diversity(unique_list)
        print(f"🎯 Final diverse set: {len(diverse_materials)} materials")
        
        return diverse_materials
    
    def analyze_diversity(self, materials: List) -> None:
        """Analyze and display diversity statistics"""
        print("\n📈 Diversity Analysis:")
        print("=" * 30)
        
        # Crystal systems
        crystal_systems = defaultdict(int)
        elements_count = defaultdict(int)
        nelements_count = defaultdict(int)
        
        for material in materials:
            # Crystal system
            if hasattr(material, 'symmetry') and material.symmetry:
                crystal_systems[str(material.symmetry.crystal_system)] += 1
            
            # Elements
            if hasattr(material, 'elements'):
                for element in material.elements:
                    elements_count[str(element)] += 1
            
            # Number of elements
            if hasattr(material, 'nelements'):
                nelements_count[material.nelements] += 1
        
        print("Crystal Systems:")
        for system, count in sorted(crystal_systems.items()):
            print(f"  {system}: {count} materials")
        
        print(f"\nMost common elements:")
        top_elements = sorted(elements_count.items(), key=lambda x: x[1], reverse=True)[:10]
        for element, count in top_elements:
            print(f"  {element}: {count} materials")
        
        print(f"\nComposition complexity:")
        for nelems, count in sorted(nelements_count.items()):
            print(f"  {nelems} elements: {count} materials")
        
        print(f"\nSearch strategy results:")
        for strategy, count in self.stats.items():
            print(f"  {strategy}: {count} materials")
    
    def save_materials_data(self, materials: List) -> str:
        """Save materials data for backend import"""
        materials_data = []
        
        print(f"\n💾 Converting {len(materials)} materials to database format...")
        
        for i, material in enumerate(materials, 1):
            try:
                # Convert to dict format backend expects
                material_dict = {
                    "material_id": material.material_id,
                    "formula": material.formula_pretty,
                    "crystal_system": str(material.symmetry.crystal_system) if material.symmetry else None,
                    "spacegroup_symbol": material.symmetry.symbol if material.symmetry else None, 
                    "spacegroup_number": material.symmetry.number if material.symmetry else None,
                    "structure": material.structure.as_dict() if material.structure else None,
                    "band_gap": material.band_gap if hasattr(material, 'band_gap') else None,
                    "energy_above_hull": material.energy_above_hull if hasattr(material, 'energy_above_hull') else None,
                    "formation_energy_per_atom": material.formation_energy_per_atom if hasattr(material, 'formation_energy_per_atom') else None,
                    "volume": material.volume if hasattr(material, 'volume') else None,
                    "density": material.density if hasattr(material, 'density') else None,
                    "nelements": material.nelements if hasattr(material, 'nelements') else None,
                    "chemsys": material.chemsys if hasattr(material, 'chemsys') else None,
                    "source": "materials_project"
                }
                
                materials_data.append(material_dict)
                
                if i % 25 == 0:
                    print(f"   Processed {i}/{len(materials)} materials...")
                    
            except Exception as e:
                print(f"   ⚠️ Error processing {material.material_id}: {e}")
                continue
        
        # Save to JSON file
        output_file = "diverse_materials.json"
        with open(output_file, "w") as f:
            json.dump(materials_data, f, indent=2)
        
        print(f"✅ Saved {len(materials_data)} materials to {output_file}")
        return output_file

async def main():
    """Main execution function"""
    loader = DiverseMaterialsLoader(API_KEY)
    
    try:
        # Load diverse materials
        materials = await loader.load_diverse_materials()
        
        if not materials:
            print("❌ No materials loaded successfully")
            return 1
        
        # Analyze diversity
        loader.analyze_diversity(materials)
        
        # Save for backend import
        output_file = loader.save_materials_data(materials)
        
        print(f"\n🎉 Success! Loaded {len(materials)} diverse materials")
        print(f"📁 Data saved to: {output_file}")
        print(f"⚡ Next steps:")
        print(f"   1. Import with: python import_mp_data.py")
        print(f"   2. Restart backend to see new materials")
        print(f"   3. Enjoy the diverse materials database!")
        
        return 0
        
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
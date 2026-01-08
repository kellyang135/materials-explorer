#!/usr/bin/env python3
"""
Simple script to load popular materials using the Materials Project Python API
"""

import requests
import json
import os
from pathlib import Path

# Materials Project API configuration
API_KEY = "4qLIaDzBfyUgYLrnh6mu9tOsGbAshwYG"
API_BASE = "https://api.materialsproject.org"

# Popular materials to load (more diverse than current set)
POPULAR_MATERIALS = [
    "mp-149",    # Si (diamond cubic)
    "mp-13",     # Fe (BCC) 
    "mp-1265",   # SiO2 (quartz)
    "mp-22862",  # NaCl (rock salt)
    "mp-2534",   # GaAs (zincblende) 
    "mp-134",    # Al (FCC)
    "mp-1143",   # Cu (FCC)
    "mp-19017",  # Fe2O3 (hematite)
    "mp-1185",   # CaF2 (fluorite)
    "mp-569",    # GaN (wurtzite)
    "mp-1018058", # CsPbI3 (perovskite) 
    "mp-72",     # Mg (HCP)
    "mp-66",     # CaCO3 (calcite)
    "mp-8062",   # TiO2 (rutile)
    "mp-1695",   # InAs (zincblende)
]

def fetch_material_data(material_id):
    """Fetch material data from Materials Project API"""
    
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"Fetching {material_id}...")
    
    # Get basic material data
    url = f"{API_BASE}/materials/{material_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch {material_id}: {response.status_code}")
        return None
        
    data = response.json()
    material_data = data.get('data', [])
    
    if not material_data:
        print(f"❌ No data for {material_id}")
        return None
        
    material = material_data[0]
    
    print(f"✅ {material_id}: {material.get('formula')} - {material.get('crystal_system')}")
    
    return {
        'material_id': material_id,
        'formula': material.get('formula'),
        'crystal_system': material.get('crystal_system'), 
        'spacegroup_symbol': material.get('spacegroup', {}).get('symbol'),
        'spacegroup_number': material.get('spacegroup', {}).get('number'),
        'structure': material.get('structure')
    }

def save_materials_json(materials):
    """Save materials to JSON file for backend to load"""
    
    output_file = Path(__file__).parent / "materials_data.json"
    
    with open(output_file, 'w') as f:
        json.dump(materials, f, indent=2)
    
    print(f"\n💾 Saved {len(materials)} materials to {output_file}")
    return output_file

def main():
    print("🚀 Loading materials from Materials Project API...")
    print(f"📡 Using API key: {API_KEY[:10]}...")
    
    materials = []
    
    for material_id in POPULAR_MATERIALS:
        material_data = fetch_material_data(material_id)
        if material_data:
            materials.append(material_data)
    
    if materials:
        output_file = save_materials_json(materials)
        print(f"\n🎉 Successfully loaded {len(materials)} materials!")
        print("\n📋 Materials loaded:")
        for m in materials:
            print(f"  {m['material_id']}: {m['formula']} ({m['crystal_system']})")
        
        print(f"\n💡 Next steps:")
        print(f"1. The material data is saved in: {output_file}")
        print(f"2. Import this data into your backend database")
        print(f"3. Refresh your frontend to see the new materials")
    else:
        print("❌ No materials were loaded successfully")

if __name__ == "__main__":
    main()
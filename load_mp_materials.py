#!/usr/bin/env python3
"""
Load materials from Materials Project using the official mp-api
"""

from mp_api.client import MPRester
import json

# Your Materials Project API key
API_KEY = "4qLIaDzBfyUgYLrnh6mu9tOsGbAshwYG"

def load_popular_materials():
    """Load popular materials using various search criteria"""
    
    with MPRester(API_KEY) as mpr:
        
        print("🚀 Connected to Materials Project API")
        
        # Search for different types of interesting materials
        materials = []
        
        # 1. Common semiconductors
        print("\n📱 Loading semiconductors...")
        semiconductor_docs = mpr.materials.search(
            elements=["Si"],
            fields=["material_id", "formula_pretty", "symmetry", "structure"]
        )
        for doc in semiconductor_docs[:5]:  # First 5
            print(f"  ✓ {doc.material_id}: {doc.formula_pretty}")
            materials.append(doc)
        
        # 2. Common metals 
        print("\n🔩 Loading metals...")
        metal_docs = mpr.materials.search(
            elements=["Fe"],
            fields=["material_id", "formula_pretty", "symmetry", "structure"]
        )
        for doc in metal_docs[:5]:  # First 5
            print(f"  ✓ {doc.material_id}: {doc.formula_pretty}")
            materials.append(doc)
        
        # 3. Important oxides
        print("\n🧪 Loading oxides...")
        oxide_docs = mpr.materials.search(
            chemsys=["Ti-O", "Fe-O", "Si-O"],
            fields=["material_id", "formula_pretty", "symmetry", "structure"]
        )
        for doc in oxide_docs[:5]:  # First 5
            print(f"  ✓ {doc.material_id}: {doc.formula_pretty}")
            materials.append(doc)
        
        # 4. Ionic compounds
        print("\n🧂 Loading ionic compounds...")
        ionic_docs = mpr.materials.search(
            chemsys=["Na-Cl", "Ca-F", "Mg-O"],
            fields=["material_id", "formula_pretty", "symmetry", "structure"]
        )
        for doc in ionic_docs[:5]:  # First 5
            print(f"  ✓ {doc.material_id}: {doc.formula_pretty}")
            materials.append(doc)
        
        return materials

def save_for_backend(materials):
    """Save materials in format for backend import"""
    
    materials_data = []
    
    for doc in materials:
        try:
            # Convert to dict format backend can understand
            material_data = {
                "material_id": doc.material_id,
                "formula": doc.formula_pretty,
                "crystal_system": str(doc.symmetry.crystal_system) if doc.symmetry else None,
                "spacegroup_symbol": doc.symmetry.symbol if doc.symmetry else None,
                "spacegroup_number": doc.symmetry.number if doc.symmetry else None,
                "structure": doc.structure.as_dict() if doc.structure else None,
                "source": "materials_project"
            }
            materials_data.append(material_data)
            
        except Exception as e:
            print(f"❌ Error processing {doc.material_id}: {e}")
            continue
    
    # Save to JSON file
    with open("mp_materials.json", "w") as f:
        json.dump(materials_data, f, indent=2)
    
    print(f"\n💾 Saved {len(materials_data)} materials to mp_materials.json")
    return materials_data

def main():
    """Main function"""
    
    print("🌟 Materials Project Data Loader")
    print("=" * 40)
    
    try:
        # Load materials from MP
        materials = load_popular_materials()
        
        print(f"\n📊 Total materials loaded: {len(materials)}")
        
        if materials:
            # Save for backend
            materials_data = save_for_backend(materials)
            
            print("\n📋 Summary by crystal system:")
            systems = {}
            for m in materials_data:
                system = m.get("crystal_system", "unknown")
                systems[system] = systems.get(system, 0) + 1
            
            for system, count in systems.items():
                print(f"  {system}: {count} materials")
            
            print(f"\n✅ Success! Loaded {len(materials_data)} materials from Materials Project")
            print("💡 Next: Import mp_materials.json into your backend database")
        else:
            print("❌ No materials loaded")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Check your API key and internet connection")

if __name__ == "__main__":
    main()
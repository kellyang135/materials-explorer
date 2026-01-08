"""ML service for material property predictions using rule-based heuristics"""

import json
import math
from typing import Any, Optional, Dict, List, Tuple
import numpy as np



class MLService:
    """
    Service for materials property predictions using rule-based heuristics.
    
    Implements chemically-informed predictions based on:
    - Electronegativity differences for band gap estimation
    - Atomic properties for formation energy
    - Bonding characteristics for mechanical properties
    """

    def __init__(self):
        self._models = {}
        self._loaded = False
        self._element_cache = {}

    def _lazy_load_models(self):
        """Initialize rule-based prediction models"""
        if self._loaded:
            return

        self._models = {
            "formation_energy": {
                "name": "composition_heuristic_v1",
                "type": "RuleBased",
                "version": "1.0.0",
                "description": "Atomic property weighted formation energy estimation"
            },
            "band_gap": {
                "name": "electronegativity_gap_v1", 
                "type": "RuleBased",
                "version": "1.0.0",
                "description": "Band gap from electronegativity differences"
            },
            "bulk_modulus": {
                "name": "atomic_radius_modulus_v1",
                "type": "RuleBased", 
                "version": "1.0.0",
                "description": "Bulk modulus from atomic radii and bonding"
            },
            "shear_modulus": {
                "name": "atomic_radius_modulus_v1",
                "type": "RuleBased",
                "version": "1.0.0", 
                "description": "Shear modulus from atomic radii and bonding"
            },
        }
        self._loaded = True

    def parse_structure(
        self,
        structure_json: Optional[dict] = None,
        cif_string: Optional[str] = None,
    ) -> Any:
        """
        parse structure from JSON or CIF format

        returns a pymatgen Structure object
        """
        try:
            from pymatgen.core import Structure
        except ImportError:
            raise ValueError(
                "pymatgen is required for structure parsing. "
                "install pip install pymatgen"
            )

        if structure_json:
            try:
                return Structure.from_dict(structure_json)
            except Exception as e:
                raise ValueError(f"Invalid structure JSON: {str(e)}")

        if cif_string:
            try:
                return Structure.from_str(cif_string, fmt="cif")
            except Exception as e:
                raise ValueError(f"Invalid CIF string: {str(e)}")

        raise ValueError("No structure data provided")

    async def predict_property(
        self,
        structure: Any,
        property_name: str,
    ) -> dict:
        """
        predict a property for a given structure

        args:
            structure: pymatgen Structure object
            property_name: Name of property to predict

        returns:
            Dict with prediction results
        """
        self._lazy_load_models()

        if property_name not in self._models:
            raise ValueError(
                f"Unknown property: {property_name}. "
                f"Available: {list(self._models.keys())}"
            )

        model_info = self._models[property_name]

        # run rule-based prediction
        prediction = self._predict_property_heuristic(structure, property_name)

        return {
            "name": property_name,
            "value": prediction["value"],
            "unit": prediction["unit"],
            "uncertainty": prediction.get("uncertainty"),
            "model": f"{model_info['type']}/{model_info['name']}",
        }

    def _get_element_properties(self, element_symbol: str) -> Dict[str, float]:
        """Get element properties using pymatgen. Cache results for performance."""
        if element_symbol in self._element_cache:
            return self._element_cache[element_symbol]
        
        try:
            from pymatgen.core import Element
            element = Element(element_symbol)
            
            properties = {
                'electronegativity': getattr(element, 'X', None) or 1.5,  # Pauling scale
                'atomic_radius': getattr(element, 'atomic_radius', None) or 1.0,  # Angstroms
                'mendeleev_no': getattr(element, 'mendeleev_no', None) or element.Z,
                'atomic_mass': element.atomic_mass,
                'row': element.row,
                'group': element.group,
                'ionization_energy': getattr(element, 'ionization_energies', [0])[0] if getattr(element, 'ionization_energies', None) else 5.0,
                'electron_affinity': getattr(element, 'electron_affinity', None) or 0.0,
                'metallic_radius': getattr(element, 'metallic_radius', None) or getattr(element, 'atomic_radius', None) or 1.0,
                'common_oxidation_states': list(getattr(element, 'common_oxidation_states', [0]))
            }
            
            self._element_cache[element_symbol] = properties
            return properties
            
        except ImportError:
            raise ValueError("pymatgen is required for element property calculations")
        except Exception as e:
            # Fallback values for unknown elements
            return {
                'electronegativity': 1.5,
                'atomic_radius': 1.0,
                'mendeleev_no': 50,
                'atomic_mass': 50.0,
                'row': 4,
                'group': 10,
                'ionization_energy': 5.0,
                'electron_affinity': 0.0,
                'metallic_radius': 1.0,
                'common_oxidation_states': [0]
            }

    def _predict_band_gap(self, structure: Any) -> Dict[str, float]:
        """
        Predict band gap from electronegativity differences.
        
        Based on empirical correlations:
        - Larger electronegativity differences → larger gaps (ionic character)
        - All metals → zero gap
        - Semiconductors/insulators have gaps proportional to electronegativity spread
        """
        composition = structure.composition
        elements = list(composition.keys())
        
        if len(elements) == 1:
            # Pure element - use periodic trends
            element_props = self._get_element_properties(str(elements[0]))
            
            # Metals typically have zero gap, non-metals have gaps
            if element_props['group'] in [1, 2] or (element_props['row'] >= 4 and element_props['group'] <= 12):
                # Alkali, alkaline earth, or transition metals
                gap = 0.0
                uncertainty = 0.1
            else:
                # Non-metals - estimate from position in periodic table
                gap = max(0, 8.0 - element_props['row'] + (element_props['group'] - 14) * 0.5)
                uncertainty = 0.3
        else:
            # Compound - calculate from electronegativity differences
            electronegativities = []
            fractions = []
            
            for element, fraction in composition.items():
                props = self._get_element_properties(str(element))
                electronegativities.append(props['electronegativity'])
                fractions.append(fraction)
            
            # Weighted average and spread
            avg_electronegativity = np.average(electronegativities, weights=fractions)
            electronegativity_range = max(electronegativities) - min(electronegativities)
            
            # Empirical correlation: larger differences → larger gaps
            if electronegativity_range > 2.0:
                # Highly ionic - large gap
                gap = 3.0 + electronegativity_range * 1.5
            elif electronegativity_range > 1.0:
                # Moderately ionic/covalent
                gap = 1.0 + electronegativity_range * 2.0
            else:
                # Metallic or small differences - small gap
                gap = max(0, electronegativity_range * 0.5)
            
            # Adjust for average electronegativity (more electronegative → larger gaps)
            gap *= (1.0 + (avg_electronegativity - 2.0) * 0.2)
            gap = max(0, gap)
            uncertainty = 0.2 + electronegativity_range * 0.1

        return {
            "value": round(gap, 2),
            "unit": "eV",
            "uncertainty": round(uncertainty, 2)
        }

    def _predict_formation_energy(self, structure: Any) -> Dict[str, float]:
        """
        Predict formation energy from atomic properties.
        
        Uses Miedema's model concepts:
        - Electronegativity differences drive compound formation
        - Size effects from atomic radius mismatches
        - Electronic effects from ionization energies
        """
        composition = structure.composition
        elements = list(composition.keys())
        
        if len(elements) == 1:
            # Pure element - formation energy is zero by definition
            return {
                "value": 0.0,
                "unit": "eV/atom", 
                "uncertainty": 0.01
            }
        
        # Calculate formation energy from mixing effects
        total_energy = 0.0
        total_atoms = sum(composition.values())
        
        # Pairwise interactions between elements
        for i, (elem1, frac1) in enumerate(composition.items()):
            props1 = self._get_element_properties(str(elem1))
            
            for elem2, frac2 in list(composition.items())[i+1:]:
                props2 = self._get_element_properties(str(elem2))
                
                # Electronegativity term (ionic character)
                electronegativity_diff = abs(props1['electronegativity'] - props2['electronegativity'])
                ionic_energy = -0.3 * electronegativity_diff**1.5
                
                # Size mismatch penalty
                radius_diff = abs(props1['atomic_radius'] - props2['atomic_radius'])
                size_penalty = 0.1 * (radius_diff / max(props1['atomic_radius'], props2['atomic_radius']))**2
                
                # Electronic contribution
                ionization_diff = abs(props1['ionization_energy'] - props2['ionization_energy'])
                electronic_term = -0.05 * ionization_diff / 10.0
                
                # Weight by composition fractions
                pair_contribution = (ionic_energy - size_penalty + electronic_term) * (frac1 * frac2 / total_atoms)
                total_energy += pair_contribution
        
        # Stability correction for common oxide formers
        oxide_formers = ['Al', 'Si', 'Ti', 'Zr', 'Hf', 'Fe', 'Cr', 'Mn']
        if any(str(elem) in oxide_formers for elem in elements) and any(str(elem) == 'O' for elem in elements):
            total_energy -= 0.5  # Oxides tend to be more stable
        
        # Uncertainty increases with number of elements and composition complexity
        uncertainty = 0.1 + 0.05 * len(elements)
        
        return {
            "value": round(total_energy, 3),
            "unit": "eV/atom",
            "uncertainty": round(uncertainty, 3)
        }

    def _predict_bulk_modulus(self, structure: Any) -> Dict[str, float]:
        """
        Predict bulk modulus from atomic properties and bonding.
        
        Based on:
        - Average atomic volume (smaller atoms → higher modulus)
        - Bonding strength (electronegativity, ionization energy)
        - Crystal structure effects (coordination)
        """
        composition = structure.composition
        volume_per_atom = structure.volume / len(structure)
        
        # Calculate average properties weighted by composition
        total_modulus = 0.0
        total_weight = 0.0
        
        for element, fraction in composition.items():
            props = self._get_element_properties(str(element))
            
            # Base modulus from atomic properties
            # Smaller, harder atoms have higher moduli
            atomic_contribution = 200.0 / (props['atomic_radius']**2)
            
            # Electronegativity contribution (stronger bonds → higher modulus)
            electronegativity_contribution = props['electronegativity'] * 30.0
            
            # Ionization energy contribution  
            ionization_contribution = props['ionization_energy'] * 5.0
            
            element_modulus = atomic_contribution + electronegativity_contribution + ionization_contribution
            
            total_modulus += element_modulus * fraction
            total_weight += fraction
        
        avg_modulus = total_modulus / total_weight if total_weight > 0 else 100.0
        
        # Volume correction (dense materials are typically harder)
        if volume_per_atom < 15.0:  # Very dense
            avg_modulus *= 1.5
        elif volume_per_atom > 30.0:  # Less dense
            avg_modulus *= 0.7
        
        # Ensure reasonable range
        avg_modulus = max(10.0, min(500.0, avg_modulus))
        
        uncertainty = 20.0 + avg_modulus * 0.15
        
        return {
            "value": round(avg_modulus, 1),
            "unit": "GPa", 
            "uncertainty": round(uncertainty, 1)
        }

    def _predict_shear_modulus(self, structure: Any) -> Dict[str, float]:
        """
        Predict shear modulus from bulk modulus.
        
        Uses approximate relation: G ≈ (3/8) * B for most materials
        with corrections for bonding type.
        """
        bulk_result = self._predict_bulk_modulus(structure)
        bulk_modulus = bulk_result["value"]
        
        composition = structure.composition
        
        # Estimate shear/bulk ratio from composition
        # Metals: G/B ≈ 0.4
        # Ionic compounds: G/B ≈ 0.3  
        # Covalent compounds: G/B ≈ 0.5
        
        metallic_fraction = 0.0
        ionic_fraction = 0.0
        
        for element in composition.keys():
            props = self._get_element_properties(str(element))
            
            # Metals have low electronegativity and are in certain groups
            if props['electronegativity'] < 2.0 and props['group'] <= 12:
                metallic_fraction += composition[element]
            elif props['electronegativity'] > 3.0:
                ionic_fraction += composition[element]
        
        # Estimate G/B ratio
        if metallic_fraction > 0.5:
            gb_ratio = 0.4  # Metallic
        elif ionic_fraction > 0.3:
            gb_ratio = 0.3  # Ionic
        else:
            gb_ratio = 0.45  # Mixed/covalent
        
        shear_modulus = bulk_modulus * gb_ratio
        uncertainty = bulk_result["uncertainty"] * 0.8  # Slightly less uncertain than bulk
        
        return {
            "value": round(shear_modulus, 1),
            "unit": "GPa",
            "uncertainty": round(uncertainty, 1)
        }

    def _predict_property_heuristic(self, structure: Any, property_name: str) -> Dict[str, Any]:
        """
        Main dispatch method for rule-based property predictions.
        """
        try:
            if property_name == "band_gap":
                return self._predict_band_gap(structure)
            elif property_name == "formation_energy":
                return self._predict_formation_energy(structure)
            elif property_name == "bulk_modulus":
                return self._predict_bulk_modulus(structure)
            elif property_name == "shear_modulus":
                return self._predict_shear_modulus(structure)
            else:
                raise ValueError(f"Unknown property: {property_name}")
                
        except Exception as e:
            # Fallback to reasonable defaults if calculations fail
            fallback_values = {
                "formation_energy": {"value": -0.5, "unit": "eV/atom", "uncertainty": 0.5},
                "band_gap": {"value": 1.0, "unit": "eV", "uncertainty": 0.5},
                "bulk_modulus": {"value": 100.0, "unit": "GPa", "uncertainty": 50.0},
                "shear_modulus": {"value": 40.0, "unit": "GPa", "uncertainty": 20.0},
            }
            result = fallback_values.get(property_name, {"value": 0, "unit": "unknown", "uncertainty": 1.0})
            result["warning"] = f"Calculation failed, using fallback: {str(e)}"
            return result

    def get_available_models(self) -> list[dict]:
        """Get list of available ML models."""
        self._lazy_load_models()
        return [
            {
                "property": prop,
                "model_name": info["name"],
                "model_type": info["type"],
                "version": info["version"],
            }
            for prop, info in self._models.items()
        ]

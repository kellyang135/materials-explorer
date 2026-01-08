/**
 * Atomic data for 3D visualization
 * Element colors based on CPK coloring convention
 * Atomic radii in Angstroms (covalent radii)
 */

export interface ElementData {
  color: string;
  radius: number;
  name: string;
}

export const ATOMIC_DATA: Record<string, ElementData> = {
  // Common elements
  H: { color: '#FFFFFF', radius: 0.31, name: 'Hydrogen' },
  He: { color: '#D9FFFF', radius: 0.28, name: 'Helium' },
  
  Li: { color: '#CC80FF', radius: 1.28, name: 'Lithium' },
  Be: { color: '#C2FF00', radius: 0.96, name: 'Beryllium' },
  B: { color: '#FFB5B5', radius: 0.84, name: 'Boron' },
  C: { color: '#909090', radius: 0.76, name: 'Carbon' },
  N: { color: '#3050F8', radius: 0.71, name: 'Nitrogen' },
  O: { color: '#FF0D0D', radius: 0.66, name: 'Oxygen' },
  F: { color: '#90E050', radius: 0.57, name: 'Fluorine' },
  Ne: { color: '#B3E3F5', radius: 0.58, name: 'Neon' },
  
  Na: { color: '#AB5CF2', radius: 1.66, name: 'Sodium' },
  Mg: { color: '#8AFF00', radius: 1.41, name: 'Magnesium' },
  Al: { color: '#BFA6A6', radius: 1.21, name: 'Aluminum' },
  Si: { color: '#F0C8A0', radius: 1.11, name: 'Silicon' },
  P: { color: '#FF8000', radius: 1.07, name: 'Phosphorus' },
  S: { color: '#FFFF30', radius: 1.05, name: 'Sulfur' },
  Cl: { color: '#1FF01F', radius: 1.02, name: 'Chlorine' },
  Ar: { color: '#80D1E3', radius: 1.06, name: 'Argon' },
  
  K: { color: '#8F40D4', radius: 2.03, name: 'Potassium' },
  Ca: { color: '#3DFF00', radius: 1.76, name: 'Calcium' },
  
  // Transition metals
  Sc: { color: '#E6E6E6', radius: 1.70, name: 'Scandium' },
  Ti: { color: '#BFC2C7', radius: 1.60, name: 'Titanium' },
  V: { color: '#A6A6AB', radius: 1.53, name: 'Vanadium' },
  Cr: { color: '#8A99C7', radius: 1.39, name: 'Chromium' },
  Mn: { color: '#9C7AC7', radius: 1.39, name: 'Manganese' },
  Fe: { color: '#4169E1', radius: 1.32, name: 'Iron' }, // Bright blue for maximum contrast with red O
  Co: { color: '#F090A0', radius: 1.26, name: 'Cobalt' },
  Ni: { color: '#50D050', radius: 1.24, name: 'Nickel' },
  Cu: { color: '#C88033', radius: 1.32, name: 'Copper' },
  Zn: { color: '#7D80B0', radius: 1.22, name: 'Zinc' },
  
  Ga: { color: '#C28F8F', radius: 1.22, name: 'Gallium' },
  Ge: { color: '#668F8F', radius: 1.20, name: 'Germanium' },
  As: { color: '#BD80E3', radius: 1.19, name: 'Arsenic' },
  Se: { color: '#FFA100', radius: 1.20, name: 'Selenium' },
  Br: { color: '#A62929', radius: 1.20, name: 'Bromine' },
  Kr: { color: '#5CB8D1', radius: 1.16, name: 'Krypton' },
  
  // More elements as needed
  Rb: { color: '#702EB0', radius: 2.20, name: 'Rubidium' },
  Sr: { color: '#00FF00', radius: 1.95, name: 'Strontium' },
  Y: { color: '#94FFFF', radius: 1.90, name: 'Yttrium' },
  Zr: { color: '#94E0E0', radius: 1.75, name: 'Zirconium' },
  Nb: { color: '#73C2C9', radius: 1.64, name: 'Niobium' },
  Mo: { color: '#54B5B5', radius: 1.54, name: 'Molybdenum' },
  
  // Rare earths (simplified)
  La: { color: '#70D4FF', radius: 2.07, name: 'Lanthanum' },
  Ce: { color: '#FFFFC7', radius: 2.04, name: 'Cerium' },
  Nd: { color: '#C7FFC7', radius: 2.01, name: 'Neodymium' },
  
  // Default fallback for unknown elements
  X: { color: '#FF1493', radius: 1.0, name: 'Unknown' },
};

/**
 * Get element data for a given element symbol
 * Falls back to default values for unknown elements
 */
export function getElementData(symbol: string): ElementData {
  const cleanSymbol = symbol.trim();
  return ATOMIC_DATA[cleanSymbol] || ATOMIC_DATA.X;
}

/**
 * Get scaled radius for visualization
 * Scales atomic radii for better visibility in 3D
 */
export function getVisualizationRadius(symbol: string, scale: number = 0.3): number {
  const data = getElementData(symbol);
  return data.radius * scale;
}

/**
 * Convert hex color to RGB array
 */
export function hexToRgb(hex: string): [number, number, number] {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return [1, 0, 1]; // Fallback to magenta
  
  return [
    parseInt(result[1], 16) / 255,
    parseInt(result[2], 16) / 255,
    parseInt(result[3], 16) / 255,
  ];
}
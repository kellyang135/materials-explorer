export interface Material {
  id: number;
  material_id: string;
  formula: string;
  formula_pretty: string;
  chemsys: string;
  nelements: number;
  nsites?: number;
  crystal_system?: string;
  spacegroup_symbol?: string;
  spacegroup_number?: number;
  volume?: number;
  density?: number;
  density_atomic?: number;
  source: string;
  source_id?: string;
  created_at: string;
  updated_at: string;
  compositions?: Composition[];
}

export interface Composition {
  id: number;
  amount: number;
  weight_fraction?: number;
  atomic_fraction?: number;
  element: Element;
}

export interface Element {
  id: number;
  symbol: string;
  name: string;
  atomic_number: number;
  atomic_mass: number;
  electronegativity?: number;
}

export interface MaterialsResponse {
  items: Material[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface SearchResponse extends MaterialsResponse {
  query?: string;
  filters_applied?: any;
}

export interface Calculation {
  id: number;
  calc_type: string;
  energy?: number;
  energy_per_atom?: number;
  formation_energy_per_atom?: number;
  energy_above_hull?: number;
  is_stable?: boolean;
  band_gap?: number;
  is_gap_direct?: boolean;
  cbm?: number;
  vbm?: number;
  efermi?: number;
  total_magnetization?: number;
  is_magnetic?: boolean;
  created_at: string;
}

export interface Structure {
  id: number;
  num_sites: number;
  is_ordered: boolean;
  spacegroup_number?: number;
  spacegroup_symbol?: string;
  crystal_system?: string;
  lattice: Lattice;
  sites: Site[];
  cif_string?: string;
}

export interface Lattice {
  id: number;
  a: number;
  b: number;
  c: number;
  alpha: number;
  beta: number;
  gamma: number;
  volume: number;
  matrix: number[][];
}

export interface Site {
  id: number;
  site_index: number;
  species: string;
  frac_coords: number[];
  cart_coords: number[];
  occupancy: number;
  label?: string;
}

export interface PredictResponse {
  predictions: PropertyPrediction[];
  structure_formula?: string;
  warnings?: string[];
}

export interface PropertyPrediction {
  name: string;
  value: number;
  unit?: string;
  uncertainty?: number;
  model: string;
}
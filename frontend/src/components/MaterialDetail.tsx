import React, { useState, useEffect } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  CircularProgress,
  Alert,
  Breadcrumbs,
  Link
} from '@mui/material';
import { Grid } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import MaterialsAPI from '../services/api';
import { Material, Calculation, Structure } from '../types/api';
import ImprovedCrystalStructure3D from './Structure3D/ImprovedCrystalStructure3D';

const MaterialDetail: React.FC = () => {
  const { materialId } = useParams<{ materialId: string }>();
  const [material, setMaterial] = useState<Material | null>(null);
  const [calculations, setCalculations] = useState<Calculation[]>([]);
  const [structure, setStructure] = useState<Structure | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (materialId) {
      loadMaterialData(materialId);
    }
  }, [materialId]);

  const loadMaterialData = async (id: string) => {
    setLoading(true);
    setError(null);
    
    try {
      // Load material details
      const materialData = await MaterialsAPI.getMaterial(id);
      setMaterial(materialData);

      // Load calculations
      try {
        const calculationsData = await MaterialsAPI.getMaterialCalculations(id);
        setCalculations(calculationsData);
      } catch (err) {
        console.log('No calculations available');
      }

      // Load structure
      try {
        const structureData = await MaterialsAPI.getMaterialStructure(id);
        setStructure(structureData);
      } catch (err) {
        console.log('No structure available');
      }

    } catch (err) {
      setError('Failed to load material data');
      console.error('Error loading material:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !material) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error || 'Material not found'}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link component={RouterLink} to="/" underline="hover">
          Materials
        </Link>
        <Typography color="text.primary">{material.material_id}</Typography>
      </Breadcrumbs>

      <Button
        component={RouterLink}
        to="/"
        startIcon={<ArrowBackIcon />}
        sx={{ mb: 3 }}
      >
        Back to Materials
      </Button>

      {/* Material Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Typography variant="h4" component="h1" gutterBottom>
              {material.formula_pretty}
            </Typography>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              {material.material_id}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 2 }}>
              <Chip label={`${material.nelements} elements`} color="primary" />
              <Chip label={material.chemsys} variant="outlined" />
              {material.crystal_system && (
                <Chip label={material.crystal_system} color="secondary" />
              )}
              {material.spacegroup_symbol && (
                <Chip label={`SG: ${material.spacegroup_symbol}`} />
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>

      <Grid container spacing={3}>
        {/* Basic Properties */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Basic Properties
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell><strong>Formula</strong></TableCell>
                      <TableCell>{material.formula}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell><strong>Chemical System</strong></TableCell>
                      <TableCell>{material.chemsys}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell><strong>Number of Elements</strong></TableCell>
                      <TableCell>{material.nelements}</TableCell>
                    </TableRow>
                    {material.nsites && (
                      <TableRow>
                        <TableCell><strong>Number of Sites</strong></TableCell>
                        <TableCell>{material.nsites}</TableCell>
                      </TableRow>
                    )}
                    {material.volume && (
                      <TableRow>
                        <TableCell><strong>Volume</strong></TableCell>
                        <TableCell>{material.volume.toFixed(2)} Ų</TableCell>
                      </TableRow>
                    )}
                    {material.density && (
                      <TableRow>
                        <TableCell><strong>Density</strong></TableCell>
                        <TableCell>{material.density.toFixed(3)} g/cm³</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Composition */}
        {material.compositions && material.compositions.length > 0 && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Composition
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Element</TableCell>
                        <TableCell>Amount</TableCell>
                        <TableCell>Atomic Number</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {material.compositions.map((comp) => (
                        <TableRow key={comp.id}>
                          <TableCell>
                            <strong>{comp.element.symbol}</strong> - {comp.element.name}
                          </TableCell>
                          <TableCell>{comp.amount}</TableCell>
                          <TableCell>{comp.element.atomic_number}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Calculations */}
        {calculations.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Electronic Properties
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Calculation Type</TableCell>
                        <TableCell>Formation Energy (eV/atom)</TableCell>
                        <TableCell>Band Gap (eV)</TableCell>
                        <TableCell>Energy Above Hull (eV/atom)</TableCell>
                        <TableCell>Is Stable</TableCell>
                        <TableCell>Is Magnetic</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {calculations.map((calc) => (
                        <TableRow key={calc.id}>
                          <TableCell>
                            <Chip label={calc.calc_type} size="small" />
                          </TableCell>
                          <TableCell>
                            {calc.formation_energy_per_atom?.toFixed(3) ?? 'N/A'}
                          </TableCell>
                          <TableCell>
                            {calc.band_gap?.toFixed(2) ?? 'N/A'}
                            {calc.band_gap !== undefined && calc.band_gap > 0 && (
                              <Chip
                                label={calc.is_gap_direct ? "Direct" : "Indirect"}
                                size="small"
                                sx={{ ml: 1 }}
                              />
                            )}
                          </TableCell>
                          <TableCell>
                            {calc.energy_above_hull?.toFixed(3) ?? 'N/A'}
                          </TableCell>
                          <TableCell>
                            {calc.is_stable !== undefined ? (
                              <Chip
                                label={calc.is_stable ? "Yes" : "No"}
                                color={calc.is_stable ? "success" : "warning"}
                                size="small"
                              />
                            ) : 'N/A'}
                          </TableCell>
                          <TableCell>
                            {calc.is_magnetic !== undefined ? (
                              calc.is_magnetic ? "Yes" : "No"
                            ) : 'N/A'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Structure Info */}
        {structure && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Crystal Structure
                </Typography>
                
                {/* 3D Visualization */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    3D Structure Visualization
                  </Typography>
                  <ImprovedCrystalStructure3D 
                    structure={structure}
                  />
                  <Typography variant="caption" sx={{ mt: 1, display: 'block', textAlign: 'center' }}>
                    Click and drag to rotate • Scroll to zoom • Right-click and drag to pan
                  </Typography>
                </Box>

                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Lattice Parameters
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableBody>
                          <TableRow>
                            <TableCell>a, b, c (Å)</TableCell>
                            <TableCell>
                              {structure.lattice.a.toFixed(3)}, {structure.lattice.b.toFixed(3)}, {structure.lattice.c.toFixed(3)}
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>α, β, γ (°)</TableCell>
                            <TableCell>
                              {structure.lattice.alpha.toFixed(1)}, {structure.lattice.beta.toFixed(1)}, {structure.lattice.gamma.toFixed(1)}
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Volume (Ų)</TableCell>
                            <TableCell>{structure.lattice.volume.toFixed(2)}</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Structure Info
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableBody>
                          <TableRow>
                            <TableCell>Number of Sites</TableCell>
                            <TableCell>{structure.num_sites}</TableCell>
                          </TableRow>
                          {structure.spacegroup_symbol && (
                            <TableRow>
                              <TableCell>Space Group</TableCell>
                              <TableCell>
                                {structure.spacegroup_symbol} (#{structure.spacegroup_number})
                              </TableCell>
                            </TableRow>
                          )}
                          {structure.crystal_system && (
                            <TableRow>
                              <TableCell>Crystal System</TableCell>
                              <TableCell>{structure.crystal_system}</TableCell>
                            </TableRow>
                          )}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                </Grid>
                
                {structure.sites.length > 0 && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Atomic Sites (first 10)
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Index</TableCell>
                            <TableCell>Species</TableCell>
                            <TableCell>Fractional Coords</TableCell>
                            <TableCell>Occupancy</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {structure.sites.slice(0, 10).map((site) => (
                            <TableRow key={site.id}>
                              <TableCell>{site.site_index}</TableCell>
                              <TableCell>
                                <Chip label={site.species} size="small" />
                              </TableCell>
                              <TableCell>
                                [{site.frac_coords.map(c => c.toFixed(3)).join(', ')}]
                              </TableCell>
                              <TableCell>{site.occupancy}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                    {structure.sites.length > 10 && (
                      <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                        Showing first 10 of {structure.sites.length} sites
                      </Typography>
                    )}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default MaterialDetail;
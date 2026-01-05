import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  TextField,
  Button,
  Pagination,
  Chip,
  InputAdornment,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import SearchIcon from '@mui/icons-material/Search';
import MaterialsAPI from '../services/api';
import { Material, SearchResponse } from '../types/api';

const MaterialsBrowser: React.FC = () => {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [elements, setElements] = useState('');
  const [crystalSystem, setCrystalSystem] = useState('');

  const pageSize = 20;

  useEffect(() => {
    loadMaterials();
  }, [page, searchQuery, elements, crystalSystem]);

  const loadMaterials = async () => {
    setLoading(true);
    try {
      let response: SearchResponse;
      
      if (searchQuery || elements || crystalSystem) {
        response = await MaterialsAPI.searchMaterials({
          query: searchQuery || undefined,
          elements: elements || undefined,
          crystal_system: crystalSystem || undefined,
          page,
          page_size: pageSize,
        });
      } else {
        response = await MaterialsAPI.getMaterials(page, pageSize);
      }

      setMaterials(response.items);
      setTotal(response.total);
      setTotalPages(response.pages);
    } catch (error) {
      console.error('Error loading materials:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1);
    loadMaterials();
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setElements('');
    setCrystalSystem('');
    setPage(1);
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Materials Database
      </Typography>
      
      {/* Search and Filters */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Search"
              placeholder="Formula, material ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              label="Elements"
              placeholder="Si,O"
              value={elements}
              onChange={(e) => setElements(e.target.value)}
              helperText="Comma-separated"
            />
          </Grid>
          
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Crystal System</InputLabel>
              <Select
                value={crystalSystem}
                label="Crystal System"
                onChange={(e) => setCrystalSystem(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="cubic">Cubic</MenuItem>
                <MenuItem value="tetragonal">Tetragonal</MenuItem>
                <MenuItem value="orthorhombic">Orthorhombic</MenuItem>
                <MenuItem value="hexagonal">Hexagonal</MenuItem>
                <MenuItem value="trigonal">Trigonal</MenuItem>
                <MenuItem value="monoclinic">Monoclinic</MenuItem>
                <MenuItem value="triclinic">Triclinic</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={2}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button 
                variant="contained" 
                onClick={handleSearch}
                fullWidth
              >
                Search
              </Button>
              <Button 
                variant="outlined" 
                onClick={handleClearFilters}
                fullWidth
              >
                Clear
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Results */}
      <Paper>
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            {total} materials found
          </Typography>
          
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Material ID</TableCell>
                      <TableCell>Formula</TableCell>
                      <TableCell>Chemical System</TableCell>
                      <TableCell>Crystal System</TableCell>
                      <TableCell>Elements</TableCell>
                      <TableCell>Density</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {materials.map((material) => (
                      <TableRow key={material.id} hover>
                        <TableCell>
                          <Button
                            component={RouterLink}
                            to={`/materials/${material.material_id}`}
                            variant="text"
                            color="primary"
                          >
                            {material.material_id}
                          </Button>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body1">
                            {material.formula_pretty}
                          </Typography>
                        </TableCell>
                        <TableCell>{material.chemsys}</TableCell>
                        <TableCell>
                          {material.crystal_system && (
                            <Chip 
                              label={material.crystal_system} 
                              size="small" 
                              variant="outlined"
                            />
                          )}
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={`${material.nelements} elements`} 
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {material.density 
                            ? `${material.density.toFixed(2)} g/cm³` 
                            : 'N/A'
                          }
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              
              {totalPages > 1 && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                  <Pagination
                    count={totalPages}
                    page={page}
                    onChange={(_, value) => setPage(value)}
                    color="primary"
                  />
                </Box>
              )}
            </>
          )}
        </Box>
      </Paper>
    </Box>
  );
};

export default MaterialsBrowser;
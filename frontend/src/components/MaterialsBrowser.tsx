import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Card,
  CardContent,
  CardActionArea,
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
  CircularProgress,
  Stack,
  Avatar,
  Divider,
  IconButton,
  Fade,
  Grow,
  Switch,
  FormControlLabel
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import SearchIcon from '@mui/icons-material/Search';
import ScienceIcon from '@mui/icons-material/Science';
import ViewInArIcon from '@mui/icons-material/ViewInAr';
import ClearIcon from '@mui/icons-material/Clear';
import FilterListIcon from '@mui/icons-material/FilterList';
import MaterialsAPI from '../services/api';
import { Material, SearchResponse } from '../types/api';
import { explorationTracker } from '../services/explorationTracker';
import ExplorationDebug from './ExplorationDebug';
import ExplorationBreadcrumb from './ExplorationBreadcrumb';

const MaterialsBrowser: React.FC = () => {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [elements, setElements] = useState('');
  const [crystalSystem, setCrystalSystem] = useState('');
  const [isGuidedMode, setIsGuidedMode] = useState(() => {
    // Initialize from localStorage to persist across navigation
    const saved = localStorage.getItem('materials_guided_mode');
    return saved === 'true';
  });

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
    // Track search behavior
    if (searchQuery) {
      explorationTracker.trackSearch(searchQuery);
    }
    if (elements) {
      explorationTracker.trackFilter('elements', elements);
    }
    if (crystalSystem) {
      explorationTracker.trackFilter('crystal_system', crystalSystem);
    }
    
    setPage(1);
    loadMaterials();
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setElements('');
    setCrystalSystem('');
    setPage(1);
  };

  // Get crystal system color for visual variety
  const getCrystalSystemColor = (system: string) => {
    const colors = {
      cubic: '#4A7C59',
      tetragonal: '#8B5A3C', 
      orthorhombic: '#5A8B73',
      hexagonal: '#2D5A3D',
      trigonal: '#6B7A4F',
      monoclinic: '#A67C5A',
      triclinic: '#7B6B4F',
    };
    return colors[system as keyof typeof colors] || '#5A6B5A';
  };

  return (
    <Fade in timeout={800}>
      <Box>
        {/* Zen-inspired page header */}
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <Typography 
            variant="h4" 
            component="h1" 
            gutterBottom
            sx={{
              background: 'linear-gradient(135deg, #0D4E41 0%, #4A7C59 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              color: 'transparent',
              fontWeight: 300,
              mb: 1,
            }}
          >
            Explore Materials
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
            Discover crystal structures and properties from our curated database
          </Typography>
        </Box>

        {/* Guided Discovery Mode Toggle */}
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
          <FormControlLabel
            control={
              <Switch
                checked={isGuidedMode}
                onChange={(e) => {
                  const newValue = e.target.checked;
                  setIsGuidedMode(newValue);
                  localStorage.setItem('materials_guided_mode', newValue.toString());
                }}
                color="primary"
              />
            }
            label={
              <Stack direction="row" alignItems="center" spacing={1}>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>
                  🧭 Guided Discovery Mode
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {isGuidedMode ? 'Track your exploration journey' : 'Enable smart exploration assistance'}
                </Typography>
              </Stack>
            }
            sx={{
              background: isGuidedMode ? 'linear-gradient(135deg, rgba(13, 78, 65, 0.1) 0%, rgba(74, 124, 89, 0.1) 100%)' : 'transparent',
              borderRadius: 2,
              px: 2,
              py: 1,
              border: isGuidedMode ? '1px solid' : '1px solid transparent',
              borderColor: isGuidedMode ? 'primary.light' : 'transparent',
              transition: 'all 0.3s ease'
            }}
          />
        </Box>

        {/* Exploration Breadcrumb Trail */}
        <ExplorationBreadcrumb isGuidedMode={isGuidedMode} />

        {/* Elegant Search Section */}
        <Card sx={{ 
          mb: 4, 
          background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(250,251,250,0.9) 100%)',
          backdropFilter: 'blur(20px)',
        }}>
          <CardContent sx={{ p: 4 }}>
            <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
              <Avatar sx={{ bgcolor: 'primary.main' }}>
                <FilterListIcon />
              </Avatar>
              <Typography variant="h6" color="primary.main">
                Search & Filter
              </Typography>
            </Stack>

            <Grid container spacing={3}>
              <Grid item xs={12} md={5}>
                <TextField
                  fullWidth
                  label="Search Materials"
                  placeholder="Formula, material ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon color="primary" />
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        boxShadow: '0 4px 12px rgba(13, 78, 65, 0.15)',
                      },
                    },
                  }}
                />
              </Grid>
              
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Elements"
                  placeholder="Si, O, Fe..."
                  value={elements}
                  onChange={(e) => setElements(e.target.value)}
                  helperText="Comma-separated"
                />
              </Grid>
              
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Crystal System</InputLabel>
                  <Select
                    value={crystalSystem}
                    label="Crystal System"
                    onChange={(e) => setCrystalSystem(e.target.value)}
                  >
                    <MenuItem value="">All Systems</MenuItem>
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
            </Grid>

            <Stack direction="row" spacing={2} sx={{ mt: 3, justifyContent: 'center' }}>
              <Button 
                variant="contained" 
                onClick={handleSearch}
                startIcon={<SearchIcon />}
                sx={{ minWidth: 120 }}
              >
                Search
              </Button>
              <Button 
                variant="outlined" 
                onClick={handleClearFilters}
                startIcon={<ClearIcon />}
                sx={{ minWidth: 120 }}
              >
                Clear Filters
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {/* Results Summary */}
        <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6" color="text.primary">
            {total} materials found
          </Typography>
          {totalPages > 1 && (
            <Pagination
              count={totalPages}
              page={page}
              onChange={(_, value) => setPage(value)}
              color="primary"
              size="large"
            />
          )}
        </Box>

        {/* Beautiful Material Cards */}
        {loading ? (
          <Box sx={{ 
            display: 'flex', 
            flexDirection: 'column',
            alignItems: 'center', 
            justifyContent: 'center',
            p: 8,
          }}>
            <CircularProgress size={60} sx={{ mb: 2 }} />
            <Typography variant="body1" color="text.secondary">
              Loading materials...
            </Typography>
          </Box>
        ) : (
          <Grid container spacing={3}>
            {materials.map((material, index) => (
              <Grow 
                key={material.id} 
                in 
                timeout={600 + index * 100}
                style={{ transformOrigin: '50% 0 0' }}
              >
                <Grid item xs={12} sm={6} lg={4} xl={3}>
                  <Card
                    component={RouterLink}
                    to={`/materials/${material.material_id}`}
                    onClick={() => {
                      // Track material view for guided discovery
                      explorationTracker.trackMaterialView(
                        material.material_id,
                        material.formula_pretty,
                        material.crystal_system
                      );
                    }}
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      cursor: 'pointer',
                      textDecoration: 'none',
                      position: 'relative',
                      '&:hover': {
                        transform: 'translateY(-8px)',
                        boxShadow: '0 12px 40px rgba(13, 78, 65, 0.2)',
                      },
                      '&:before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        height: '4px',
                        background: `linear-gradient(90deg, ${getCrystalSystemColor(material.crystal_system || 'cubic')} 0%, rgba(255,255,255,0) 100%)`,
                        borderRadius: '20px 20px 0 0',
                      }
                    }}
                  >
                    <CardContent sx={{ flexGrow: 1, p: 3 }}>
                      {/* Material Header */}
                      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
                        <Avatar 
                          sx={{ 
                            bgcolor: getCrystalSystemColor(material.crystal_system || 'cubic'),
                            width: 48,
                            height: 48,
                          }}
                        >
                          <ViewInArIcon />
                        </Avatar>
                        <Box>
                          <Typography variant="h6" color="primary.main" sx={{ fontWeight: 500 }}>
                            {material.material_id}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Materials Project ID
                          </Typography>
                        </Box>
                      </Stack>

                      {/* Chemical Formula */}
                      <Box sx={{ mb: 2 }}>
                        <Typography 
                          variant="h5" 
                          sx={{ 
                            fontWeight: 300, 
                            color: 'text.primary',
                            fontFamily: 'monospace',
                            letterSpacing: '0.5px',
                          }}
                        >
                          {material.formula_pretty}
                        </Typography>
                      </Box>

                      <Divider sx={{ my: 2 }} />

                      {/* Material Properties */}
                      <Stack spacing={2}>
                        {/* Chemical System */}
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                            Chemical System
                          </Typography>
                          <Typography variant="body1" sx={{ fontWeight: 500 }}>
                            {material.chemsys}
                          </Typography>
                        </Box>

                        {/* Crystal System & Elements */}
                        <Stack direction="row" spacing={2}>
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                              Crystal System
                            </Typography>
                            {material.crystal_system ? (
                              <Chip 
                                label={material.crystal_system}
                                size="small"
                                sx={{
                                  bgcolor: getCrystalSystemColor(material.crystal_system),
                                  color: 'white',
                                  fontWeight: 500,
                                  mt: 0.5,
                                }}
                              />
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                Unknown
                              </Typography>
                            )}
                          </Box>
                          
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                              Elements
                            </Typography>
                            <Chip 
                              label={`${material.nelements || 0} elements`}
                              size="small"
                              variant="outlined"
                              sx={{ mt: 0.5 }}
                            />
                          </Box>
                        </Stack>

                        {/* Density */}
                        {material.density && (
                          <Box>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                              Density
                            </Typography>
                            <Typography variant="body1" sx={{ fontWeight: 500 }}>
                              {material.density.toFixed(2)} g/cm³
                            </Typography>
                          </Box>
                        )}
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              </Grow>
            ))}
          </Grid>
        )}

        {/* Bottom Pagination */}
        {totalPages > 1 && !loading && (
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            mt: 6,
            p: 3,
          }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={(_, value) => setPage(value)}
              color="primary"
              size="large"
              showFirstButton
              showLastButton
            />
          </Box>
        )}

        {/* Debug Panel for Testing Exploration Tracking */}
        <ExplorationDebug />
      </Box>
    </Fade>
  );
};

export default MaterialsBrowser;
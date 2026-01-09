import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  Chip,
  FormControl,
  FormLabel,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Autocomplete,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Divider,
  Stack,
  Avatar,
  Fade,
  Grow,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
import ScienceIcon from '@mui/icons-material/Science';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import SearchIcon from '@mui/icons-material/Search';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import MaterialsAPI from '../services/api';
import { PredictResponse, PropertyPrediction, Material } from '../types/api';

const MLPredictor: React.FC = () => {
  // Input method state
  const [inputMethod, setInputMethod] = useState<'database' | 'formula' | 'advanced'>('database');
  const [activeStep, setActiveStep] = useState(0);
  
  // Material selection states
  const [selectedMaterial, setSelectedMaterial] = useState<Material | null>(null);
  const [materialOptions, setMaterialOptions] = useState<Material[]>([]);
  const [formula, setFormula] = useState('');
  const [structureJson, setStructureJson] = useState('');
  
  // Prediction states
  const [selectedProperties, setSelectedProperties] = useState<string[]>(['formation_energy', 'band_gap']);
  const [predictions, setPredictions] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const availableProperties = [
    { 
      name: 'formation_energy', 
      label: 'Formation Energy', 
      unit: 'eV/atom',
      description: 'Energy required to form the material from its elements',
      icon: '⚡'
    },
    { 
      name: 'band_gap', 
      label: 'Band Gap', 
      unit: 'eV',
      description: 'Energy gap between valence and conduction bands',
      icon: '🔋'
    },
    { 
      name: 'bulk_modulus', 
      label: 'Bulk Modulus', 
      unit: 'GPa',
      description: 'Resistance to uniform compression',
      icon: '💎'
    },
    { 
      name: 'shear_modulus', 
      label: 'Shear Modulus', 
      unit: 'GPa',
      description: 'Resistance to shape change',
      icon: '🔧'
    },
  ];

  const steps = [
    'Choose Material',
    'Select Properties', 
    'Run Prediction'
  ];

  useEffect(() => {
    loadMaterials();
  }, []);

  const loadMaterials = async () => {
    try {
      const response = await MaterialsAPI.getMaterials(1, 20);
      setMaterialOptions(response.items);
    } catch (err) {
      console.error('Error loading materials:', err);
    }
  };

  const handlePropertyChange = (property: string) => {
    setSelectedProperties(prev => 
      prev.includes(property) 
        ? prev.filter(p => p !== property)
        : [...prev, property]
    );
  };

  const handleNext = () => {
    setActiveStep(prev => prev + 1);
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const handleMaterialSelect = (material: Material | null) => {
    setSelectedMaterial(material);
    setError(null);
  };

  const findMaterialByFormula = async (formula: string) => {
    try {
      // Search for materials with matching formula
      const response = await MaterialsAPI.searchMaterials({
        query: formula,
        page: 1,
        page_size: 10
      });
      
      // Find exact match or closest match
      const exactMatch = response.items.find(m => 
        m.formula_pretty.toLowerCase().replace(/[₀-₉]/g, (match) => String.fromCharCode(match.charCodeAt(0) - 8272 + 48)) === formula.toLowerCase()
      );
      
      if (exactMatch) return exactMatch;
      
      // If no exact match, try first result
      if (response.items.length > 0) {
        return response.items[0];
      }
      
      return null;
    } catch (err) {
      console.error('Error searching for material:', err);
      return null;
    }
  };

  const handlePredict = async () => {
    if (!selectedMaterial && !formula && !structureJson) {
      setError('Please select a material or provide a chemical formula');
      return;
    }

    if (selectedProperties.length === 0) {
      setError('Please select at least one property to predict');
      return;
    }

    setLoading(true);
    setError(null);
    setPredictions(null);

    try {
      const requestData: any = {
        properties: selectedProperties
      };

      let materialForPrediction = selectedMaterial;

      // If we have a formula but no selected material, try to find it in database
      if (!selectedMaterial && formula.trim()) {
        materialForPrediction = await findMaterialByFormula(formula.trim());
        if (!materialForPrediction) {
          throw new Error(`Material "${formula}" not found in database. Please select from available materials or use advanced structure input.`);
        }
        // Update the selected material for display purposes
        setSelectedMaterial(materialForPrediction);
      }

      if (materialForPrediction) {
        // Use the material's structure
        const materialDetail = await MaterialsAPI.getMaterial(materialForPrediction.material_id);
        if (materialDetail.structure) {
          requestData.structure_json = materialDetail.structure.structure_json;
        } else {
          throw new Error('Selected material has no structure data');
        }
      } else if (structureJson.trim()) {
        try {
          requestData.structure_json = JSON.parse(structureJson);
        } catch (err) {
          throw new Error('Invalid structure format');
        }
      } else {
        throw new Error('No valid structure data found');
      }

      const result = await MaterialsAPI.predictProperties(requestData);
      setPredictions(result);
      setActiveStep(2); // Move to results step
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Prediction failed');
    } finally {
      setLoading(false);
    }
  };

  const resetPrediction = () => {
    setPredictions(null);
    setSelectedMaterial(null);
    setFormula('');
    setStructureJson('');
    setActiveStep(0);
    setError(null);
  };

  return (
    <Fade in timeout={800}>
      <Box>
        {/* Zen Header */}
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
            AI-Powered Material Predictions
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
            Discover material properties using advanced machine learning models trained on materials science data
          </Typography>
        </Box>

        <Grid container spacing={4}>
          {/* Guided Workflow */}
          <Grid item xs={12} lg={8}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(250,251,250,0.9) 100%)',
              backdropFilter: 'blur(20px)',
            }}>
              <CardContent sx={{ p: 4 }}>
                {/* Progress Stepper */}
                <Stepper activeStep={activeStep} orientation="horizontal" sx={{ mb: 4 }}>
                  {steps.map((label) => (
                    <Step key={label}>
                      <StepLabel>{label}</StepLabel>
                    </Step>
                  ))}
                </Stepper>

                {/* Step 1: Choose Material */}
                {activeStep === 0 && (
                  <Fade in>
                    <Box>
                      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
                        <Avatar sx={{ bgcolor: 'primary.main' }}>
                          <SearchIcon />
                        </Avatar>
                        <Typography variant="h6" color="primary.main">
                          Choose Your Material
                        </Typography>
                      </Stack>

                      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        Select a material from our database or enter a chemical formula (like "NaCl" or "Fe2O3")
                      </Typography>

                      {/* Input Method Toggle */}
                      <ToggleButtonGroup
                        value={inputMethod}
                        exclusive
                        onChange={(_, value) => value && setInputMethod(value)}
                        sx={{ mb: 3, display: 'flex', width: '100%' }}
                      >
                        <ToggleButton value="database" sx={{ flex: 1 }}>
                          <SearchIcon sx={{ mr: 1 }} />
                          From Database
                        </ToggleButton>
                        <ToggleButton value="formula" sx={{ flex: 1 }}>
                          <TextFieldsIcon sx={{ mr: 1 }} />
                          Chemical Formula
                        </ToggleButton>
                        <ToggleButton value="advanced" sx={{ flex: 1 }}>
                          <UploadFileIcon sx={{ mr: 1 }} />
                          Advanced
                        </ToggleButton>
                      </ToggleButtonGroup>

                      {/* Material Selection Interface */}
                      {inputMethod === 'database' && (
                        <Box>
                          <Typography variant="subtitle1" gutterBottom>
                            Select from Materials Database
                          </Typography>
                          <Autocomplete
                            options={materialOptions}
                            getOptionLabel={(option) => `${option.material_id} - ${option.formula_pretty}`}
                            value={selectedMaterial}
                            onChange={(_, newValue) => handleMaterialSelect(newValue)}
                            renderInput={(params) => (
                              <TextField
                                {...params}
                                label="Search Materials"
                                placeholder="Type to search by ID or formula..."
                                helperText={`${materialOptions.length} materials available`}
                              />
                            )}
                            renderOption={(props, option) => (
                              <Box component="li" {...props}>
                                <Box>
                                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                                    {option.material_id}
                                  </Typography>
                                  <Typography variant="body2" color="text.secondary">
                                    {option.formula_pretty} • {option.crystal_system}
                                  </Typography>
                                </Box>
                              </Box>
                            )}
                          />
                        </Box>
                      )}

                      {inputMethod === 'formula' && (
                        <Box>
                          <Typography variant="subtitle1" gutterBottom>
                            Enter Chemical Formula
                          </Typography>
                          <TextField
                            fullWidth
                            label="Chemical Formula"
                            placeholder="NaCl, Fe2O3, SiO2..."
                            value={formula}
                            onChange={(e) => setFormula(e.target.value)}
                            helperText="Enter a standard chemical formula (e.g., NaCl for sodium chloride)"
                          />
                        </Box>
                      )}

                      {inputMethod === 'advanced' && (
                        <Box>
                          <Typography variant="subtitle1" gutterBottom>
                            Advanced Structure Input
                          </Typography>
                          <Alert severity="info" sx={{ mb: 2 }}>
                            For advanced users: Provide crystal structure data in JSON format
                          </Alert>
                          <TextField
                            fullWidth
                            label="Structure Data"
                            multiline
                            rows={8}
                            value={structureJson}
                            onChange={(e) => setStructureJson(e.target.value)}
                            helperText="Crystal structure in Materials Project JSON format"
                          />
                        </Box>
                      )}

                      {/* Current Selection Display */}
                      {(selectedMaterial || formula.trim() || structureJson.trim()) && (
                        <Card sx={{ mt: 3, bgcolor: 'success.light', color: 'success.contrastText' }}>
                          <CardContent>
                            <Typography variant="subtitle2" gutterBottom>
                              ✓ Material Ready:
                            </Typography>
                            <Typography variant="h6">
                              {selectedMaterial ? 
                                `${selectedMaterial.material_id} (${selectedMaterial.formula_pretty})` :
                                formula.trim() ? 
                                  `${formula.trim()} (will search database)` :
                                  'Advanced Structure'
                              }
                            </Typography>
                            {formula.trim() && !selectedMaterial && (
                              <Typography variant="caption" sx={{ mt: 1, display: 'block', opacity: 0.8 }}>
                                We'll find this material in our database when you run the prediction
                              </Typography>
                            )}
                          </CardContent>
                        </Card>
                      )}

                      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end' }}>
                        <Button
                          variant="contained"
                          onClick={handleNext}
                          disabled={!selectedMaterial && !formula.trim() && !structureJson.trim()}
                          endIcon={<PlayArrowIcon />}
                        >
                          Choose Properties
                        </Button>
                      </Box>
                    </Box>
                  </Fade>
                )}

                {/* Step 2: Select Properties */}
                {activeStep === 1 && (
                  <Fade in>
                    <Box>
                      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
                        <Avatar sx={{ bgcolor: 'secondary.main' }}>
                          <ScienceIcon />
                        </Avatar>
                        <Typography variant="h6" color="secondary.main">
                          Select Properties to Predict
                        </Typography>
                      </Stack>

                      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        Choose which material properties you want our AI models to predict
                      </Typography>

                      <Grid container spacing={2}>
                        {availableProperties.map((property) => (
                          <Grid item xs={12} sm={6} key={property.name}>
                            <Grow in timeout={600}>
                              <Card
                                sx={{
                                  cursor: 'pointer',
                                  transition: 'all 0.3s ease',
                                  border: selectedProperties.includes(property.name) 
                                    ? '2px solid' 
                                    : '2px solid transparent',
                                  borderColor: selectedProperties.includes(property.name) 
                                    ? 'primary.main' 
                                    : 'transparent',
                                  '&:hover': {
                                    transform: 'translateY(-4px)',
                                    boxShadow: '0 8px 25px rgba(13, 78, 65, 0.15)',
                                  },
                                }}
                                onClick={() => handlePropertyChange(property.name)}
                              >
                                <CardContent>
                                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                    <Typography variant="h4" sx={{ mr: 1 }}>
                                      {property.icon}
                                    </Typography>
                                    <Typography variant="h6" sx={{ fontWeight: 500 }}>
                                      {property.label}
                                    </Typography>
                                    {selectedProperties.includes(property.name) && (
                                      <Chip 
                                        label="Selected" 
                                        size="small" 
                                        color="primary" 
                                        sx={{ ml: 'auto' }}
                                      />
                                    )}
                                  </Box>
                                  <Typography variant="body2" color="text.secondary" gutterBottom>
                                    {property.description}
                                  </Typography>
                                  <Chip 
                                    label={property.unit} 
                                    size="small" 
                                    variant="outlined"
                                  />
                                </CardContent>
                              </Card>
                            </Grow>
                          </Grid>
                        ))}
                      </Grid>

                      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'space-between' }}>
                        <Button onClick={handleBack}>
                          Back
                        </Button>
                        <Button
                          variant="contained"
                          onClick={handlePredict}
                          disabled={selectedProperties.length === 0 || loading}
                          startIcon={loading ? <CircularProgress size={20} /> : <AutoAwesomeIcon />}
                        >
                          {loading ? 'Running Prediction...' : 'Run Prediction'}
                        </Button>
                      </Box>
                    </Box>
                  </Fade>
                )}

                {/* Step 3: Results */}
                {activeStep === 2 && (
                  <Fade in>
                    <Box>
                      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
                        <Avatar sx={{ bgcolor: 'success.main' }}>
                          <AutoAwesomeIcon />
                        </Avatar>
                        <Typography variant="h6" color="success.main">
                          Prediction Results
                        </Typography>
                      </Stack>

                      {predictions && (
                        <Box>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                            AI predictions for {predictions.structure_formula || selectedMaterial?.formula_pretty || formula}
                          </Typography>

                          <Grid container spacing={3}>
                            {predictions.predictions.map((prediction, index) => (
                              <Grid item xs={12} md={6} key={index}>
                                <Grow in timeout={600 + index * 100}>
                                  <Card sx={{ 
                                    height: '100%',
                                    background: `linear-gradient(135deg, ${
                                      ['#E8F5E8', '#FFF3E0', '#E3F2FD', '#F3E5F5'][index % 4]
                                    } 0%, rgba(255,255,255,0.8) 100%)`,
                                  }}>
                                    <CardContent sx={{ textAlign: 'center', p: 3 }}>
                                      <Typography variant="h5" sx={{ mb: 1, textTransform: 'capitalize' }}>
                                        {prediction.name.replace('_', ' ')}
                                      </Typography>
                                      <Typography variant="h3" color="primary.main" gutterBottom>
                                        {typeof prediction.value === 'number' 
                                          ? prediction.value.toFixed(3) 
                                          : prediction.value}
                                      </Typography>
                                      <Chip 
                                        label={prediction.unit || 'dimensionless'} 
                                        color="primary" 
                                        variant="outlined"
                                        sx={{ mb: 2 }}
                                      />
                                      {prediction.uncertainty && (
                                        <Typography variant="body2" color="text.secondary">
                                          ± {prediction.uncertainty}
                                        </Typography>
                                      )}
                                    </CardContent>
                                  </Card>
                                </Grow>
                              </Grid>
                            ))}
                          </Grid>

                          <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
                            <Button
                              variant="outlined"
                              onClick={resetPrediction}
                              size="large"
                            >
                              Predict Another Material
                            </Button>
                          </Box>
                        </Box>
                      )}
                    </Box>
                  </Fade>
                )}

                {error && (
                  <Alert severity="error" sx={{ mt: 3 }}>
                    {error}
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Info Panel */}
          <Grid item xs={12} lg={4}>
            <Stack spacing={3}>
              {/* About AI Models */}
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="primary.main">
                    🤖 About Our AI Models
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Our machine learning models are trained on thousands of materials from computational databases and experimental data.
                  </Typography>
                  <Box component="ul" sx={{ pl: 2, color: 'text.secondary' }}>
                    <Typography component="li" variant="body2">
                      Formation energy models predict material stability
                    </Typography>
                    <Typography component="li" variant="body2">
                      Band gap models predict electronic properties  
                    </Typography>
                    <Typography component="li" variant="body2">
                      Mechanical property models predict strength
                    </Typography>
                  </Box>
                </CardContent>
              </Card>

              {/* Quick Examples */}
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="secondary.main">
                    💡 Quick Examples
                  </Typography>
                  <Stack spacing={1}>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => {
                        setFormula('NaCl');
                        setInputMethod('formula');
                        setActiveStep(0);
                      }}
                    >
                      Try NaCl (Salt)
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => {
                        setFormula('Fe2O3');
                        setInputMethod('formula');
                        setActiveStep(0);
                      }}
                    >
                      Try Fe₂O₃ (Rust)
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => {
                        setFormula('SiO2');
                        setInputMethod('formula');
                        setActiveStep(0);
                      }}
                    >
                      Try SiO₂ (Quartz)
                    </Button>
                  </Stack>
                </CardContent>
              </Card>
            </Stack>
          </Grid>
        </Grid>
      </Box>
    </Fade>
  );
};

export default MLPredictor;
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
  Chip,
  FormControl,
  FormLabel,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PredictionsIcon from '@mui/icons-material/Psychology';
import MaterialsAPI from '../services/api';
import { PredictResponse, PropertyPrediction } from '../types/api';

const MLPredictor: React.FC = () => {
  const [structureJson, setStructureJson] = useState('');
  const [cifString, setCifString] = useState('');
  const [selectedProperties, setSelectedProperties] = useState<string[]>(['formation_energy', 'band_gap']);
  const [predictions, setPredictions] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableModels, setAvailableModels] = useState<any>(null);

  const availableProperties = [
    { name: 'formation_energy', label: 'Formation Energy', unit: 'eV/atom' },
    { name: 'band_gap', label: 'Band Gap', unit: 'eV' },
    { name: 'bulk_modulus', label: 'Bulk Modulus', unit: 'GPa' },
    { name: 'shear_modulus', label: 'Shear Modulus', unit: 'GPa' },
  ];

  const exampleStructure = {
    "lattice": {
      "a": 5.431,
      "b": 5.431,
      "c": 5.431,
      "alpha": 90,
      "beta": 90,
      "gamma": 90
    },
    "sites": [
      {"species": [{"element": "Si", "occu": 1}], "abc": [0, 0, 0]},
      {"species": [{"element": "Si", "occu": 1}], "abc": [0.25, 0.25, 0.25]}
    ]
  };

  useEffect(() => {
    loadAvailableModels();
    setStructureJson(JSON.stringify(exampleStructure, null, 2));
  }, []);

  const loadAvailableModels = async () => {
    try {
      const models = await MaterialsAPI.getAvailableModels();
      setAvailableModels(models);
    } catch (err) {
      console.error('Error loading models:', err);
    }
  };

  const handlePropertyChange = (property: string) => {
    setSelectedProperties(prev => 
      prev.includes(property) 
        ? prev.filter(p => p !== property)
        : [...prev, property]
    );
  };

  const handlePredict = async () => {
    if (!structureJson && !cifString) {
      setError('Please provide either structure JSON or CIF string');
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

      if (structureJson.trim()) {
        try {
          requestData.structure_json = JSON.parse(structureJson);
        } catch (err) {
          throw new Error('Invalid JSON structure');
        }
      } else if (cifString.trim()) {
        requestData.cif_string = cifString;
      }

      const result = await MaterialsAPI.predictProperties(requestData);
      setPredictions(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Prediction failed');
    } finally {
      setLoading(false);
    }
  };

  const loadExample = () => {
    setStructureJson(JSON.stringify(exampleStructure, null, 2));
    setCifString('');
    setSelectedProperties(['formation_energy', 'band_gap']);
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        ML Property Prediction
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Use machine learning models to predict material properties from crystal structure.
      </Typography>

      <Grid container spacing={3}>
        {/* Input Section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Structure Input
            </Typography>
            
            <Button 
              variant="outlined" 
              onClick={loadExample}
              sx={{ mb: 2 }}
            >
              Load Silicon Example
            </Button>

            <Box sx={{ mb: 3 }}>
              <TextField
                fullWidth
                label="Structure JSON"
                multiline
                rows={12}
                value={structureJson}
                onChange={(e) => setStructureJson(e.target.value)}
                helperText="Pymatgen Structure JSON format"
                sx={{ mb: 2 }}
              />
              
              <Typography variant="body2" align="center" sx={{ my: 1 }}>
                OR
              </Typography>
              
              <TextField
                fullWidth
                label="CIF String"
                multiline
                rows={6}
                value={cifString}
                onChange={(e) => setCifString(e.target.value)}
                helperText="Crystallographic Information File format"
              />
            </Box>

            <FormControl component="fieldset" sx={{ mb: 3 }}>
              <FormLabel component="legend">Properties to Predict</FormLabel>
              <FormGroup>
                {availableProperties.map((property) => (
                  <FormControlLabel
                    key={property.name}
                    control={
                      <Checkbox
                        checked={selectedProperties.includes(property.name)}
                        onChange={() => handlePropertyChange(property.name)}
                      />
                    }
                    label={`${property.label} (${property.unit})`}
                  />
                ))}
              </FormGroup>
            </FormControl>

            <Button
              variant="contained"
              size="large"
              fullWidth
              onClick={handlePredict}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : <PredictionsIcon />}
            >
              {loading ? 'Predicting...' : 'Predict Properties'}
            </Button>

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </Paper>

          {/* Available Models */}
          {availableModels && (
            <Paper sx={{ p: 3, mt: 3 }}>
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">Available ML Models</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Property</TableCell>
                          <TableCell>Model Type</TableCell>
                          <TableCell>Version</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {availableModels.models?.map((model: any, index: number) => (
                          <TableRow key={index}>
                            <TableCell>{model.property}</TableCell>
                            <TableCell>
                              <Chip label={model.model_type} size="small" />
                            </TableCell>
                            <TableCell>{model.version}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>
            </Paper>
          )}
        </Grid>

        {/* Results Section */}
        <Grid item xs={12} md={6}>
          {predictions && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Prediction Results
              </Typography>
              
              {predictions.structure_formula && (
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Formula: {predictions.structure_formula}
                </Typography>
              )}

              <Grid container spacing={2}>
                {predictions.predictions.map((prediction: PropertyPrediction, index: number) => (
                  <Grid item xs={12} sm={6} key={index}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" component="div">
                          {prediction.name.replace('_', ' ').toUpperCase()}
                        </Typography>
                        <Typography variant="h4" color="primary" gutterBottom>
                          {prediction.value}
                          {prediction.unit && (
                            <Typography variant="caption" sx={{ ml: 1 }}>
                              {prediction.unit}
                            </Typography>
                          )}
                        </Typography>
                        {prediction.uncertainty && (
                          <Typography variant="body2" color="text.secondary">
                            Uncertainty: ±{prediction.uncertainty}
                          </Typography>
                        )}
                        <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                          Model: {prediction.model}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>

              {predictions.warnings && predictions.warnings.length > 0 && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Warnings:
                  </Typography>
                  <ul>
                    {predictions.warnings.map((warning, index) => (
                      <li key={index}>{warning}</li>
                    ))}
                  </ul>
                </Alert>
              )}
            </Paper>
          )}

          {!predictions && !loading && (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <PredictionsIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                Enter a crystal structure and select properties to predict
              </Typography>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default MLPredictor;
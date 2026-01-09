import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Container, Box } from '@mui/material';
import MaterialsBrowser from './components/MaterialsBrowser';
import MaterialDetail from './components/MaterialDetail';
import MLPredictor from './components/MLPredictor';
import Navigation from './components/Navigation';

// Bonsai-inspired theme with natural, zen colors
const theme = createTheme({
  palette: {
    primary: {
      main: '#0D4E41', // Deep forest green (like bonsai foliage)
      light: '#4A7C59',
      dark: '#0A3D32',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#8B5A3C', // Warm earth brown (like bonsai pot)
      light: '#A67C5A',
      dark: '#6B4423',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#FAFBFA', // Soft off-white (like zen garden sand)
      paper: '#FFFFFF',
    },
    success: {
      main: '#2D5A3D', // Deeper green for success states
    },
    info: {
      main: '#5A8B73', // Sage green for info states
    },
    text: {
      primary: '#2D3E2D', // Dark green-gray for text
      secondary: '#5A6B5A',
    },
  },
  typography: {
    // Medium's elegant font stack
    fontFamily: 'Charter, "Droid Serif", Georgia, Cambria, "Times New Roman", serif',
    h1: {
      fontFamily: '"Playfair Display", Charter, Georgia, serif',
      fontWeight: 400,
      letterSpacing: '-0.02em',
    },
    h2: {
      fontFamily: '"Playfair Display", Charter, Georgia, serif',
      fontWeight: 400,
      letterSpacing: '-0.01em',
    },
    h3: {
      fontFamily: '"Playfair Display", Charter, Georgia, serif',
      fontWeight: 400,
    },
    h4: {
      fontFamily: '"Playfair Display", Charter, Georgia, serif',
      fontWeight: 400,
      letterSpacing: '-0.01em',
      color: '#0D4E41',
    },
    h5: {
      fontFamily: '"Playfair Display", Charter, Georgia, serif',
      fontWeight: 400,
    },
    h6: {
      fontFamily: '"Source Sans Pro", "Helvetica Neue", Helvetica, Arial, sans-serif',
      fontWeight: 600,
      letterSpacing: '0.01em',
      textTransform: 'uppercase',
      fontSize: '0.75rem',
    },
    body1: {
      fontFamily: 'Charter, "Droid Serif", Georgia, Cambria, "Times New Roman", serif',
      fontSize: '1.1rem',
      lineHeight: 1.6,
      letterSpacing: '0.01em',
    },
    body2: {
      fontFamily: '"Source Sans Pro", "Helvetica Neue", Helvetica, Arial, sans-serif',
      fontSize: '0.95rem',
      lineHeight: 1.5,
    },
    button: {
      fontFamily: '"Source Sans Pro", "Helvetica Neue", Helvetica, Arial, sans-serif',
      fontWeight: 500,
      letterSpacing: '0.02em',
    },
  },
  shape: {
    borderRadius: 16, // More organic, rounded corners
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 4px 20px rgba(13, 78, 65, 0.08)', // Soft green shadow
          border: '1px solid rgba(13, 78, 65, 0.06)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: '12px',
          fontWeight: 500,
        },
        contained: {
          boxShadow: '0 3px 12px rgba(13, 78, 65, 0.2)',
          '&:hover': {
            boxShadow: '0 6px 20px rgba(13, 78, 65, 0.3)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: '12px',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '20px',
          border: '1px solid rgba(13, 78, 65, 0.08)',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        {/* Deep green bonsai border - outer container */}
        <Box
          sx={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #0D4E41 0%, #0A3D32 100%)',
            p: { xs: 1, md: 2 },
          }}
        >
          {/* Inner zen garden container */}
          <Box
            sx={{
              minHeight: 'calc(100vh - 16px)',
              backgroundColor: 'background.default',
              borderRadius: { xs: 2, md: 4 },
              boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
              overflow: 'hidden',
              border: '1px solid rgba(255,255,255,0.1)',
            }}
          >
            {/* Modern header with zen aesthetic */}
            <AppBar 
              position="sticky" 
              sx={{
                background: 'linear-gradient(90deg, rgba(13,78,65,0.95) 0%, rgba(74,124,89,0.95) 100%)',
                backdropFilter: 'blur(20px)',
                boxShadow: '0 2px 20px rgba(13,78,65,0.1)',
                borderRadius: 0,
              }}
            >
              <Toolbar sx={{ px: { xs: 2, md: 4 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
                  {/* Bonsai-inspired logo/icon */}
                  <Box
                    sx={{
                      width: 40,
                      height: 40,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #FFFFFF 0%, #F0F7F0 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mr: 2,
                      boxShadow: '0 4px 12px rgba(255,255,255,0.2)',
                    }}
                  >
                    <Typography variant="h6" sx={{ color: 'primary.main', fontWeight: 'bold' }}>
                      🌿
                    </Typography>
                  </Box>
                  <Typography 
                    variant="h6" 
                    component="div" 
                    sx={{ 
                      fontWeight: 300,
                      letterSpacing: '0.5px',
                      color: 'white',
                    }}
                  >
                    Materials Explorer
                  </Typography>
                </Box>
                <Navigation />
              </Toolbar>
            </AppBar>
            
            {/* Main content with zen spacing */}
            <Container 
              maxWidth="xl" 
              sx={{ 
                py: { xs: 3, md: 6 },
                px: { xs: 2, md: 4 },
              }}
            >
              <Routes>
                <Route path="/" element={<MaterialsBrowser />} />
                <Route path="/materials/:materialId" element={<MaterialDetail />} />
                <Route path="/predict" element={<MLPredictor />} />
              </Routes>
            </Container>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;

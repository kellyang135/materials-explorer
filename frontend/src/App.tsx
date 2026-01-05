import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Container } from '@mui/material';
import MaterialsBrowser from './components/MaterialsBrowser';
import MaterialDetail from './components/MaterialDetail';
import MLPredictor from './components/MLPredictor';
import Navigation from './components/Navigation';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <AppBar position="sticky">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Materials Explorer
            </Typography>
            <Navigation />
          </Toolbar>
        </AppBar>
        
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          <Routes>
            <Route path="/" element={<MaterialsBrowser />} />
            <Route path="/materials/:materialId" element={<MaterialDetail />} />
            <Route path="/predict" element={<MLPredictor />} />
          </Routes>
        </Container>
      </Router>
    </ThemeProvider>
  );
}

export default App;

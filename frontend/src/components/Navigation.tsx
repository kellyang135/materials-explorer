import React from 'react';
import { Button, Box } from '@mui/material';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import SearchIcon from '@mui/icons-material/Search';
import PredictionsIcon from '@mui/icons-material/Psychology';
import HomeIcon from '@mui/icons-material/Home';

const Navigation: React.FC = () => {
  const location = useLocation();

  return (
    <Box sx={{ display: 'flex', gap: 2 }}>
      <Button
        color="inherit"
        component={RouterLink}
        to="/"
        startIcon={<HomeIcon />}
        variant={location.pathname === '/' ? 'outlined' : 'text'}
      >
        Materials
      </Button>
      <Button
        color="inherit"
        component={RouterLink}
        to="/predict"
        startIcon={<PredictionsIcon />}
        variant={location.pathname === '/predict' ? 'outlined' : 'text'}
      >
        ML Predict
      </Button>
    </Box>
  );
};

export default Navigation;
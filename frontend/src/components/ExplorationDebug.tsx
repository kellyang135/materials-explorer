import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Stack,
  Divider,
  IconButton
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import BugReportIcon from '@mui/icons-material/BugReport';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import { explorationTracker } from '../services/explorationTracker';

const ExplorationDebug: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [sessionData, setSessionData] = useState<any>(null);

  const refreshData = () => {
    const summary = explorationTracker.getSessionSummary();
    const path = explorationTracker.getExplorationPath();
    const recent = explorationTracker.getRecentMaterials();
    const focus = explorationTracker.getCurrentFocusAreas();
    
    setSessionData({
      summary,
      path: path.slice(-10), // Last 10 events
      recentMaterials: recent,
      focusAreas: focus,
      explorationPattern: explorationTracker.detectExplorationPattern()
    });
  };

  useEffect(() => {
    if (isOpen) {
      refreshData();
      // Refresh data every 2 seconds when panel is open
      const interval = setInterval(refreshData, 2000);
      return () => clearInterval(interval);
    }
  }, [isOpen]);

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getEventIcon = (type: string) => {
    const icons = {
      material_view: '🔍',
      search: '🔎',
      filter: '🎛️',
      property_focus: '📊',
      comparison: '⚖️'
    };
    return icons[type as keyof typeof icons] || '❓';
  };

  const resetSession = () => {
    explorationTracker.resetSession();
    refreshData();
  };

  if (!isOpen) {
    return (
      <Box 
        sx={{ 
          position: 'fixed', 
          bottom: 20, 
          right: 20, 
          zIndex: 1000 
        }}
      >
        <IconButton
          onClick={() => setIsOpen(true)}
          sx={{
            bgcolor: 'primary.main',
            color: 'white',
            '&:hover': { bgcolor: 'primary.dark' }
          }}
          size="large"
        >
          <BugReportIcon />
        </IconButton>
      </Box>
    );
  }

  return (
    <Box 
      sx={{ 
        position: 'fixed', 
        bottom: 20, 
        right: 20, 
        width: 400,
        maxHeight: '80vh',
        zIndex: 1000,
        overflow: 'auto'
      }}
    >
      <Paper elevation={8} sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BugReportIcon /> Exploration Debug
          </Typography>
          <Box>
            <IconButton onClick={refreshData} size="small">
              <RefreshIcon />
            </IconButton>
            <IconButton onClick={resetSession} size="small" color="error">
              <DeleteIcon />
            </IconButton>
            <Button onClick={() => setIsOpen(false)} size="small">
              Close
            </Button>
          </Box>
        </Box>

        {sessionData && (
          <Stack spacing={2}>
            {/* Session Summary */}
            <Box>
              <Typography variant="subtitle1" gutterBottom>Session Summary</Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                <Chip label={`${sessionData.summary.eventCount} events`} size="small" />
                <Chip label={`${Math.round(sessionData.summary.duration / 1000)}s`} size="small" />
                <Chip label={sessionData.explorationPattern.replace(/_/g, ' ')} size="small" color="primary" />
              </Stack>
            </Box>

            <Divider />

            {/* Focus Areas */}
            {sessionData.focusAreas.length > 0 && (
              <Box>
                <Typography variant="subtitle1" gutterBottom>Focus Areas</Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {sessionData.focusAreas.map((area: string) => (
                    <Chip key={area} label={area.replace(/_/g, ' ')} size="small" color="secondary" />
                  ))}
                </Stack>
              </Box>
            )}

            {/* Recent Materials */}
            {sessionData.recentMaterials.length > 0 && (
              <Box>
                <Typography variant="subtitle1" gutterBottom>Recent Materials</Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {sessionData.recentMaterials.map((material: string) => (
                    <Chip key={material} label={material} size="small" variant="outlined" />
                  ))}
                </Stack>
              </Box>
            )}

            <Divider />

            {/* Recent Events */}
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">Recent Events ({sessionData.path.length})</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Stack spacing={1}>
                  {sessionData.path.slice(-5).reverse().map((event: any, index: number) => (
                    <Box key={index} sx={{ p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                      <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <span>{getEventIcon(event.type)}</span>
                        <strong>{event.type}</strong>
                        <span>{formatTimestamp(event.timestamp)}</span>
                      </Typography>
                      {event.data.materialFormula && (
                        <Typography variant="caption" color="text.secondary">
                          Material: {event.data.materialFormula}
                        </Typography>
                      )}
                      {event.data.searchQuery && (
                        <Typography variant="caption" color="text.secondary">
                          Search: "{event.data.searchQuery}"
                        </Typography>
                      )}
                      {event.data.filterType && (
                        <Typography variant="caption" color="text.secondary">
                          Filter: {event.data.filterType} = {event.data.filterValue}
                        </Typography>
                      )}
                    </Box>
                  ))}
                </Stack>
              </AccordionDetails>
            </Accordion>

            {/* Context Data */}
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">Raw Context</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body2" component="pre" sx={{ fontSize: '0.75rem', overflow: 'auto' }}>
                  {JSON.stringify(sessionData.summary.currentContext, null, 2)}
                </Typography>
              </AccordionDetails>
            </Accordion>
          </Stack>
        )}
      </Paper>
    </Box>
  );
};

export default ExplorationDebug;
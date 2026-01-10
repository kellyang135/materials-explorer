import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Stack,
  IconButton,
  Tooltip,
  Divider,
  Fade,
  Collapse
} from '@mui/material';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent
} from '@mui/lab';
import SearchIcon from '@mui/icons-material/Search';
import ScienceIcon from '@mui/icons-material/Science';
import TuneIcon from '@mui/icons-material/Tune';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import RouteIcon from '@mui/icons-material/Route';
import { explorationTracker, ExplorationEvent } from '../services/explorationTracker';

interface ExplorationBreadcrumbProps {
  isGuidedMode?: boolean;
}

const ExplorationBreadcrumb: React.FC<ExplorationBreadcrumbProps> = ({ isGuidedMode = false }) => {
  const [explorationPath, setExplorationPath] = useState<ExplorationEvent[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [focusAreas, setFocusAreas] = useState<string[]>([]);

  useEffect(() => {
    if (isGuidedMode) {
      const updatePath = () => {
        const path = explorationTracker.getExplorationPath();
        const recent = path.slice(-10); // Show last 10 events
        setExplorationPath(recent);
        
        const areas = explorationTracker.getCurrentFocusAreas();
        setFocusAreas(areas);
      };

      updatePath();
      
      // Update every 3 seconds when in guided mode
      const interval = setInterval(updatePath, 3000);
      return () => clearInterval(interval);
    }
  }, [isGuidedMode]);

  const getEventIcon = (type: string) => {
    const icons = {
      material_view: <ScienceIcon />,
      search: <SearchIcon />,
      filter: <TuneIcon />,
      property_focus: <ShowChartIcon />,
      comparison: <CompareArrowsIcon />
    };
    return icons[type as keyof typeof icons] || <ScienceIcon />;
  };

  const getEventColor = (type: string) => {
    const colors = {
      material_view: 'primary',
      search: 'secondary', 
      filter: 'info',
      property_focus: 'warning',
      comparison: 'success'
    } as const;
    return colors[type as keyof typeof colors] || 'default';
  };

  const formatEventDescription = (event: ExplorationEvent): string => {
    switch (event.type) {
      case 'material_view':
        return `Viewed ${event.data.materialFormula}`;
      case 'search':
        return `Searched "${event.data.searchQuery}"`;
      case 'filter':
        return `Filtered by ${event.data.filterType}: ${event.data.filterValue}`;
      case 'property_focus':
        return `Focused on ${event.data.property}`;
      case 'comparison':
        return `Compared ${event.data.comparedMaterials?.length} materials`;
      default:
        return 'Exploration event';
    }
  };

  const formatTime = (timestamp: number): string => {
    const now = Date.now();
    const diff = now - timestamp;
    
    if (diff < 60000) return 'just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    return `${Math.floor(diff / 3600000)}h ago`;
  };

  const getFocusAreaColor = (area: string): 'primary' | 'secondary' | 'success' | 'warning' | 'info' => {
    const colorMap = {
      'solid_electrolytes': 'primary' as const,
      'cathode_materials': 'secondary' as const,
      'high_conductivity': 'success' as const,
      'stability_focus': 'warning' as const,
      'cost_conscious': 'info' as const
    };
    return colorMap[area as keyof typeof colorMap] || 'primary';
  };

  // Don't render if not in guided mode or no exploration data
  if (!isGuidedMode || explorationPath.length === 0) {
    return null;
  }

  const recentEvents = explorationPath.slice(-5); // Show last 5 events in summary
  const hasMoreEvents = explorationPath.length > 5;

  return (
    <Fade in timeout={600}>
      <Paper 
        elevation={3}
        sx={{ 
          mb: 3,
          background: 'linear-gradient(135deg, rgba(13, 78, 65, 0.03) 0%, rgba(74, 124, 89, 0.03) 100%)',
          border: '1px solid',
          borderColor: 'primary.light',
          overflow: 'hidden'
        }}
      >
        {/* Header */}
        <Box sx={{ p: 2, pb: 1 }}>
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Stack direction="row" alignItems="center" spacing={1}>
              <RouteIcon color="primary" />
              <Typography variant="h6" color="primary.main" sx={{ fontWeight: 500 }}>
                Exploration Trail
              </Typography>
              <Chip 
                label={`${explorationPath.length} events`}
                size="small" 
                color="primary" 
                variant="outlined"
              />
            </Stack>
            
            {hasMoreEvents && (
              <IconButton 
                size="small" 
                onClick={() => setIsExpanded(!isExpanded)}
                sx={{ color: 'primary.main' }}
              >
                {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            )}
          </Stack>

          {/* Focus Areas */}
          {focusAreas.length > 0 && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                Detected interests:
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {focusAreas.map((area) => (
                  <Chip
                    key={area}
                    label={area.replace(/_/g, ' ')}
                    size="small"
                    color={getFocusAreaColor(area)}
                    sx={{ textTransform: 'capitalize' }}
                  />
                ))}
              </Stack>
            </Box>
          )}
        </Box>

        <Divider />

        {/* Timeline - Recent Events */}
        <Box sx={{ p: 2, pt: 1 }}>
          <Timeline sx={{ m: 0, p: 0 }}>
            {recentEvents.reverse().map((event, index) => (
              <TimelineItem key={`${event.timestamp}-${index}`} sx={{ minHeight: 'auto', '&:before': { display: 'none' } }}>
                <TimelineOppositeContent sx={{ flex: 0, px: 0, py: 0.5 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                    {formatTime(event.timestamp)}
                  </Typography>
                </TimelineOppositeContent>
                
                <TimelineSeparator>
                  <TimelineDot color={getEventColor(event.type)} sx={{ width: 32, height: 32 }}>
                    {getEventIcon(event.type)}
                  </TimelineDot>
                  {index < recentEvents.length - 1 && <TimelineConnector sx={{ height: 30 }} />}
                </TimelineSeparator>
                
                <TimelineContent sx={{ py: 0.5, px: 1 }}>
                  <Tooltip title={`${event.type} event`} placement="right">
                    <Typography variant="body2" sx={{ fontWeight: 400 }}>
                      {formatEventDescription(event)}
                    </Typography>
                  </Tooltip>
                  
                  {/* Additional context for material views */}
                  {event.type === 'material_view' && event.data.crystalSystem && (
                    <Chip
                      label={event.data.crystalSystem}
                      size="small"
                      variant="outlined"
                      sx={{ mt: 0.5, height: 20, fontSize: '0.65rem' }}
                    />
                  )}
                </TimelineContent>
              </TimelineItem>
            ))}
          </Timeline>

          {/* Expand/Collapse for more events */}
          <Collapse in={isExpanded && hasMoreEvents}>
            <Divider sx={{ my: 1 }} />
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              Earlier events:
            </Typography>
            <Timeline sx={{ m: 0, p: 0 }}>
              {explorationPath.slice(0, -5).reverse().map((event, index) => (
                <TimelineItem key={`expanded-${event.timestamp}-${index}`} sx={{ minHeight: 'auto', '&:before': { display: 'none' } }}>
                  <TimelineOppositeContent sx={{ flex: 0, px: 0, py: 0.5 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                      {formatTime(event.timestamp)}
                    </Typography>
                  </TimelineOppositeContent>
                  
                  <TimelineSeparator>
                    <TimelineDot color={getEventColor(event.type)} sx={{ width: 28, height: 28 }}>
                      {getEventIcon(event.type)}
                    </TimelineDot>
                    {index < explorationPath.slice(0, -5).length - 1 && <TimelineConnector sx={{ height: 25 }} />}
                  </TimelineSeparator>
                  
                  <TimelineContent sx={{ py: 0.5, px: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 400, opacity: 0.8 }}>
                      {formatEventDescription(event)}
                    </Typography>
                  </TimelineContent>
                </TimelineItem>
              ))}
            </Timeline>
          </Collapse>
        </Box>
      </Paper>
    </Fade>
  );
};

export default ExplorationBreadcrumb;
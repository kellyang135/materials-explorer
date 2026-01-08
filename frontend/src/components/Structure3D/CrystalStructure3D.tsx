import React, { useMemo, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera } from '@react-three/drei';
import { Box, CircularProgress, Typography, Paper, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import { ExpandMore } from '@mui/icons-material';
import { Structure } from '../../types/api';
import { getElementData, getVisualizationRadius } from './atomicData';
import * as THREE from 'three';

// Structure validation function
function validateStructure(structure: Structure): {
  isValid: boolean;
  issues: string[];
  stats: {
    siteCount: number;
    hasLattice: boolean;
    latticeVolume: number;
    hasCartCoords: boolean;
    avgCoordMagnitude: number;
  };
} {
  console.log('=== STRUCTURE VALIDATION ===');
  
  const issues: string[] = [];
  
  // Check basic structure
  if (!structure) {
    issues.push('Structure is null/undefined');
    return { isValid: false, issues, stats: {} as any };
  }
  
  // Check sites
  const siteCount = structure.sites?.length || 0;
  console.log(`Site count: ${siteCount}`);
  
  if (siteCount === 0) {
    issues.push('No sites in structure');
  }
  
  // Check lattice
  const hasLattice = !!(structure.lattice?.matrix);
  console.log(`Has lattice: ${hasLattice}`);
  
  if (!hasLattice) {
    issues.push('Missing lattice data');
  }
  
  let latticeVolume = 0;
  if (hasLattice) {
    const { a, b, c } = structure.lattice;
    latticeVolume = a * b * c;
    console.log(`Lattice parameters: a=${a}, b=${b}, c=${c}, volume=${latticeVolume}`);
    
    if (latticeVolume <= 0) {
      issues.push('Invalid lattice volume');
    }
  }
  
  // Check cartesian coordinates
  let hasCartCoords = true;
  let totalMagnitude = 0;
  let validCoords = 0;
  
  structure.sites?.forEach((site, i) => {
    if (!site.cart_coords || site.cart_coords.length !== 3) {
      hasCartCoords = false;
      issues.push(`Site ${i} missing cart_coords`);
    } else {
      const [x, y, z] = site.cart_coords;
      const magnitude = Math.sqrt(x*x + y*y + z*z);
      totalMagnitude += magnitude;
      validCoords++;
      
      if (i < 3) {
        console.log(`Site ${i} (${site.species}): cart=[${x.toFixed(3)}, ${y.toFixed(3)}, ${z.toFixed(3)}] mag=${magnitude.toFixed(3)}`);
      }
    }
  });
  
  const avgCoordMagnitude = validCoords > 0 ? totalMagnitude / validCoords : 0;
  console.log(`Average coordinate magnitude: ${avgCoordMagnitude.toFixed(3)}`);
  
  if (avgCoordMagnitude > 1000) {
    issues.push('Suspiciously large coordinate values');
  }
  
  const stats = {
    siteCount,
    hasLattice,
    latticeVolume,
    hasCartCoords,
    avgCoordMagnitude
  };
  
  console.log('Validation issues:', issues);
  console.log('Validation stats:', stats);
  
  return {
    isValid: issues.length === 0,
    issues,
    stats
  };
}

interface CrystalStructure3DProps {
  structure: Structure;
  height?: number;
  showUnitCell?: boolean;
  atomScale?: number;
}

interface AtomProps {
  position: [number, number, number];
  element: string;
  scale: number;
}

const Atom: React.FC<AtomProps> = ({ position, element, scale }) => {
  const elementData = getElementData(element);
  // Balance visibility and clarity
  const radius = getVisualizationRadius(element, scale * 0.8); // Visible but not overwhelming
  
  return (
    <mesh position={position}>
      <sphereGeometry args={[radius, 16, 12]} />
      <meshStandardMaterial 
        color={elementData.color}
        metalness={0.1}
        roughness={0.4}
      />
    </mesh>
  );
};

interface UnitCellProps {
  lattice: {
    matrix: number[][];
  };
}

const UnitCell: React.FC<UnitCellProps> = ({ lattice }) => {
  const lines = useMemo(() => {
    const matrix = lattice.matrix;
    const origin = [0, 0, 0];
    
    // Unit cell vertices
    const vertices = [
      [0, 0, 0],  // origin
      matrix[0],  // a
      matrix[1],  // b  
      matrix[2],  // c
      [matrix[0][0] + matrix[1][0], matrix[0][1] + matrix[1][1], matrix[0][2] + matrix[1][2]], // a+b
      [matrix[0][0] + matrix[2][0], matrix[0][1] + matrix[2][1], matrix[0][2] + matrix[2][2]], // a+c
      [matrix[1][0] + matrix[2][0], matrix[1][1] + matrix[2][1], matrix[1][2] + matrix[2][2]], // b+c
      [matrix[0][0] + matrix[1][0] + matrix[2][0], matrix[0][1] + matrix[1][1] + matrix[2][1], matrix[0][2] + matrix[1][2] + matrix[2][2]], // a+b+c
    ];
    
    // Unit cell edges
    const edges = [
      [0, 1], [0, 2], [0, 3], // from origin
      [1, 4], [1, 5], // from a
      [2, 4], [2, 6], // from b
      [3, 5], [3, 6], // from c
      [4, 7], [5, 7], [6, 7], // to opposite corner
    ];
    
    return edges.map(([start, end], index) => {
      const startPos = vertices[start] as [number, number, number];
      const endPos = vertices[end] as [number, number, number];
      
      return (
        <line key={index}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              args={[new Float32Array([...startPos, ...endPos]), 3]}
            />
          </bufferGeometry>
          <lineBasicMaterial color="#cccccc" linewidth={2} opacity={0.6} transparent={true} />
        </line>
      );
    });
  }, [lattice]);
  
  return <>{lines}</>;
};

// Highlighted center unit cell component
const CenterUnitCell: React.FC<UnitCellProps> = ({ lattice }) => {
  const lines = useMemo(() => {
    const matrix = lattice.matrix;
    const origin = [0, 0, 0];
    
    // Unit cell vertices
    const vertices = [
      [0, 0, 0],  // origin
      matrix[0],  // a
      matrix[1],  // b  
      matrix[2],  // c
      [matrix[0][0] + matrix[1][0], matrix[0][1] + matrix[1][1], matrix[0][2] + matrix[1][2]], // a+b
      [matrix[0][0] + matrix[2][0], matrix[0][1] + matrix[2][1], matrix[0][2] + matrix[2][2]], // a+c
      [matrix[1][0] + matrix[2][0], matrix[1][1] + matrix[2][1], matrix[1][2] + matrix[2][2]], // b+c
      [matrix[0][0] + matrix[1][0] + matrix[2][0], matrix[0][1] + matrix[1][1] + matrix[2][1], matrix[0][2] + matrix[1][2] + matrix[2][2]], // a+b+c
    ];
    
    // Unit cell edges
    const edges = [
      [0, 1], [0, 2], [0, 3], // from origin
      [1, 4], [1, 5], // from a
      [2, 4], [2, 6], // from b
      [3, 5], [3, 6], // from c
      [4, 7], [5, 7], [6, 7], // to opposite corner
    ];
    
    return edges.map(([start, end], index) => {
      const startPos = vertices[start] as [number, number, number];
      const endPos = vertices[end] as [number, number, number];
      
      return (
        <line key={index}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              args={[new Float32Array([...startPos, ...endPos]), 3]}
            />
          </bufferGeometry>
          <lineBasicMaterial color="#ffff00" linewidth={3} opacity={1.0} transparent={false} />
        </line>
      );
    });
  }, [lattice]);
  
  return <>{lines}</>;
};

const Scene: React.FC<{
  structure: Structure;
  showUnitCell: boolean;
  atomScale: number;
}> = ({ structure, showUnitCell, atomScale }) => {
  
  // DEBUG: Validate and log structure data
  const validation = validateStructure(structure);
  
  console.log('=== CRYSTAL STRUCTURE DEBUG ===');
  console.log('Raw structure data:', structure);
  console.log('Sites count:', structure.sites?.length || 0);
  console.log('Lattice data:', structure.lattice);
  console.log('Validation result:', validation);
  
  // Generate additional atoms for better visualization (replicate unit cell)
  const expandedSites = useMemo(() => {
    console.log('=== EXPANSION DEBUG ===');
    console.log('Original sites:', structure.sites);
    
    if (!structure.sites || structure.sites.length === 0) {
      console.log('No sites found, returning empty array');
      return [];
    }
    
    const expanded = [];
    const matrix = structure.lattice.matrix;
    
    console.log('Lattice matrix:', matrix);
    console.log('Sites before expansion:', structure.sites.length);
    
    // Always expand structures to show crystal pattern (regardless of atom count)
    if (true) { // Expand all structures
      console.log('Expanding crystal structure to show pattern (2x2x2 supercell)');
      
      // Generate atoms only within the 2x2x2 structure bounds
      // But ensure all corners and edges are properly covered
      for (let dx = 0; dx <= 2; dx++) {
        for (let dy = 0; dy <= 2; dy++) {
          for (let dz = 0; dz <= 2; dz++) {
            
            structure.sites.forEach((site) => {
              // Calculate position for this lattice point
              const newFracCoords = [
                site.frac_coords[0] + dx,
                site.frac_coords[1] + dy,
                site.frac_coords[2] + dz
              ];
              
              const newCartCoords = [
                site.cart_coords[0] + dx * structure.lattice.a,
                site.cart_coords[1] + dy * structure.lattice.b,
                site.cart_coords[2] + dz * structure.lattice.c
              ];
              
              // Include atoms within the 2x2x2 supercell boundaries  
              const maxX = 2 * structure.lattice.a + 0.1;
              const maxY = 2 * structure.lattice.b + 0.1; 
              const maxZ = 2 * structure.lattice.c + 0.1;
              const minBound = -0.1;
              
              const withinBounds = newCartCoords[0] >= minBound && newCartCoords[0] <= maxX &&
                                 newCartCoords[1] >= minBound && newCartCoords[1] <= maxY &&
                                 newCartCoords[2] >= minBound && newCartCoords[2] <= maxZ;
              
              if (withinBounds) {
                expanded.push({
                  ...site,
                  id: `${site.species}-${dx}${dy}${dz}`,
                  frac_coords: newFracCoords,
                  cart_coords: newCartCoords
                });
                
                console.log(`${site.species} [${dx},${dy},${dz}]: cart=[${newCartCoords.map(x => x.toFixed(1)).join(', ')}] - INCLUDED`);
              } else {
                console.log(`${site.species} [${dx},${dy},${dz}]: cart=[${newCartCoords.map(x => x.toFixed(1)).join(', ')}] - EXCLUDED (outside bounds)`);
              }
            });
          }
        }
      }
      
      console.log(`Generated ${expanded.length} total atoms`);
      
      // Verify all corners have atoms
      console.log('=== CORNER VERIFICATION ===');
      const cornerPositions = [
        [0,0,0], [1,0,0], [0,1,0], [0,0,1],
        [1,1,0], [1,0,1], [0,1,1], [1,1,1]
      ];
      
      cornerPositions.forEach(([cx, cy, cz]) => {
        const expectedCart = [cx * structure.lattice.a, cy * structure.lattice.b, cz * structure.lattice.c];
        const atomsAtCorner = expanded.filter(atom => {
          const dx = Math.abs(atom.cart_coords[0] - expectedCart[0]);
          const dy = Math.abs(atom.cart_coords[1] - expectedCart[1]); 
          const dz = Math.abs(atom.cart_coords[2] - expectedCart[2]);
          return dx < 0.1 && dy < 0.1 && dz < 0.1;
        });
        
        if (atomsAtCorner.length === 0) {
          console.log(`❌ NO ATOM at corner [${cx},${cy},${cz}] = [${expectedCart.map(x => x.toFixed(1)).join(',')}]`);
        } else {
          console.log(`✅ ${atomsAtCorner[0].species} at corner [${cx},${cy},${cz}]`);
        }
      });
      
    } else {
      console.log('Using original sites (no expansion needed)');
      // For larger structures, just use the original sites
      expanded.push(...structure.sites);
    }
    
    console.log('Total expanded atoms:', expanded.length);
    console.log('Expanded sites sample (first 3):', expanded.slice(0, 3));
    
    return expanded;
  }, [structure]);
  
  // Calculate scene center and bounds
  const { center, bounds } = useMemo(() => {
    console.log('=== BOUNDS CALCULATION DEBUG ===');
    
    if (!expandedSites || expandedSites.length === 0) {
      console.log('No expanded sites, using default bounds');
      return { center: [0, 0, 0], bounds: 10 };
    }
    
    let minX = Infinity, maxX = -Infinity;
    let minY = Infinity, maxY = -Infinity;
    let minZ = Infinity, maxZ = -Infinity;
    
    expandedSites.forEach((site, index) => {
      const [x, y, z] = site.cart_coords;
      minX = Math.min(minX, x);
      maxX = Math.max(maxX, x);
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
      minZ = Math.min(minZ, z);
      maxZ = Math.max(maxZ, z);
      
      // Log first few atom positions
      if (index < 4) {
        console.log(`Atom ${index + 1} bounds check: [${x.toFixed(2)}, ${y.toFixed(2)}, ${z.toFixed(2)}]`);
      }
    });
    
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    const centerZ = (minZ + maxZ) / 2;
    
    const rangeX = maxX - minX;
    const rangeY = maxY - minY;
    const rangeZ = maxZ - minZ;
    const maxRange = Math.max(rangeX, rangeY, rangeZ);
    
    console.log(`Bounds: min=[${minX.toFixed(2)}, ${minY.toFixed(2)}, ${minZ.toFixed(2)}] max=[${maxX.toFixed(2)}, ${maxY.toFixed(2)}, ${maxZ.toFixed(2)}]`);
    console.log(`Center: [${centerX.toFixed(2)}, ${centerY.toFixed(2)}, ${centerZ.toFixed(2)}]`);
    console.log(`Range: [${rangeX.toFixed(2)}, ${rangeY.toFixed(2)}, ${rangeZ.toFixed(2)}] → maxRange: ${maxRange.toFixed(2)}`);
    console.log(`Final bounds: ${Math.max(maxRange * 1.5, 10).toFixed(2)}`);
    
    return {
      center: [centerX, centerY, centerZ] as [number, number, number],
      bounds: Math.max(maxRange * 1.5, 10)
    };
  }, [expandedSites]);
  
  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.4} />
      <directionalLight 
        position={[10, 10, 5]} 
        intensity={0.8}
        castShadow
      />
      <directionalLight 
        position={[-10, -10, -5]} 
        intensity={0.3}
      />
      
      {/* Camera positioned to show the crystal structure clearly */}
      <PerspectiveCamera
        makeDefault
        position={[center[0] + 8, center[1] + 8, center[2] + 12]}
        fov={60}
        near={0.1}
        far={1000}
      />
      
      {/* Controls */}
      <OrbitControls
        target={new THREE.Vector3(...center)}
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        dampingFactor={0.05}
        enableDamping={true}
      />
      
      {/* Atoms */}
      {expandedSites?.map((site, index) => (
        <Atom
          key={`atom-${site.id || index}`}
          position={site.cart_coords as [number, number, number]}
          element={site.species}
          scale={atomScale}
        />
      ))}
      
      {/* Unit cell wireframes */}
      {showUnitCell && structure.lattice && (
        <>
          {/* Always show 2x2x2 unit cell grid for crystal visualization */}
          {structure.sites && structure.sites.length >= 0 ? (
            // Show 2x2x2 grid of unit cells to match atom generation
            Array.from({ length: 8 }, (_, i) => {
              const dx = i % 2;           // 0, 1
              const dy = Math.floor(i / 2) % 2;  // 0, 1  
              const dz = Math.floor(i / 4);      // 0, 1
              
              // Highlight the center cell (0,0,0)
              const isCenter = dx === 0 && dy === 0 && dz === 0;
              
              return (
                <group
                  key={`unit-cell-${dx}-${dy}-${dz}`}
                  position={[
                    dx * structure.lattice.a,
                    dy * structure.lattice.b,
                    dz * structure.lattice.c
                  ]}
                >
                  {isCenter ? (
                    // Highlighted center cell with brighter wireframe
                    <CenterUnitCell lattice={structure.lattice} />
                  ) : (
                    // Regular unit cell
                    <UnitCell lattice={structure.lattice} />
                  )}
                </group>
              );
            })
          ) : (
            // For larger structures, show single unit cell
            <UnitCell lattice={structure.lattice} />
          )}
        </>
      )}
    </>
  );
};

// Debug UI Component
const DebugInfo: React.FC<{
  structure: Structure;
  expandedSites: any[];
  center: [number, number, number];
  bounds: number;
  validation: ReturnType<typeof validateStructure>;
}> = ({ structure, expandedSites, center, bounds, validation }) => (
  <Accordion sx={{ mt: 1 }}>
    <AccordionSummary expandIcon={<ExpandMore />}>
      <Typography variant="h6">🔍 Structure Debug Info</Typography>
    </AccordionSummary>
    <AccordionDetails>
      <Box component="div" sx={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>
        
        {/* Validation Status */}
        <Typography variant="subtitle1" sx={{ color: validation.isValid ? 'success.main' : 'error.main', mb: 1 }}>
          {validation.isValid ? '✅ Structure Valid' : '❌ Structure Issues'}
        </Typography>
        
        {validation.issues.length > 0 && (
          <Box component="div" sx={{ mb: 2, p: 1, bgcolor: 'error.light', borderRadius: 1 }}>
            <Typography variant="subtitle2">Issues:</Typography>
            {validation.issues.map((issue, i) => (
              <Typography key={i} variant="body2">• {issue}</Typography>
            ))}
          </Box>
        )}

        {/* Stats */}
        <Box component="div" sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2, mb: 2 }}>
          <Box component="div">
            <Typography variant="subtitle2">Original Structure:</Typography>
            <Typography>Sites: {validation.stats.siteCount}</Typography>
            <Typography>Has Lattice: {validation.stats.hasLattice ? 'Yes' : 'No'}</Typography>
            <Typography>Volume: {validation.stats.latticeVolume?.toFixed(2)} Ų</Typography>
          </Box>
          
          <Box component="div">
            <Typography variant="subtitle2">After Expansion:</Typography>
            <Typography>Atoms Rendered: {expandedSites.length}</Typography>
            <Typography>Center: [{center.map(x => x.toFixed(1)).join(', ')}]</Typography>
            <Typography>Bounds: {bounds.toFixed(1)}</Typography>
          </Box>
        </Box>

        {/* Lattice Parameters */}
        {structure.lattice && (
          <Box component="div" sx={{ mb: 2 }}>
            <Typography variant="subtitle2">Lattice:</Typography>
            <Typography>a={structure.lattice.a?.toFixed(3)}, b={structure.lattice.b?.toFixed(3)}, c={structure.lattice.c?.toFixed(3)}</Typography>
            <Typography>α={structure.lattice.alpha?.toFixed(1)}°, β={structure.lattice.beta?.toFixed(1)}°, γ={structure.lattice.gamma?.toFixed(1)}°</Typography>
          </Box>
        )}

        {/* First Few Atoms */}
        <Box component="div">
          <Typography variant="subtitle2">First 4 Atom Positions:</Typography>
          {expandedSites.slice(0, 4).map((site, i) => (
            <Typography key={i}>
              {site.species}: [{site.cart_coords?.map((x: number) => x.toFixed(2)).join(', ')}]
            </Typography>
          ))}
          {expandedSites.length > 4 && (
            <Typography sx={{ color: 'text.secondary' }}>
              ... and {expandedSites.length - 4} more atoms
            </Typography>
          )}
        </Box>
      </Box>
    </AccordionDetails>
  </Accordion>
);

const CrystalStructure3D: React.FC<CrystalStructure3DProps> = ({
  structure,
  height = 400,
  showUnitCell = true,
  atomScale = 1.0, // Increased from 0.3 to 1.0
}) => {
  
  // Run validation and get debug info
  const validation = validateStructure(structure);
  
  // Get expanded sites and bounds for debug display
  const debugInfo = useMemo(() => {
    if (!structure.sites || structure.sites.length === 0) {
      return { expandedSites: [], center: [0, 0, 0] as [number, number, number], bounds: 10 };
    }
    
    const expanded = [];
    const matrix = structure.lattice?.matrix;
    
    if (matrix) {
      // Match the main expansion: 3x3x3 grid for complete coverage
      for (let dx = 0; dx <= 2; dx++) {
        for (let dy = 0; dy <= 2; dy++) {
          for (let dz = 0; dz <= 2; dz++) {
            
            structure.sites.forEach((site) => {
              const cartCoords = [
                site.cart_coords[0] + dx * structure.lattice.a,
                site.cart_coords[1] + dy * structure.lattice.b,
                site.cart_coords[2] + dz * structure.lattice.c
              ];
              
              // Apply same boundary check as main expansion
              const maxX = 2 * structure.lattice.a + 0.1;
              const maxY = 2 * structure.lattice.b + 0.1; 
              const maxZ = 2 * structure.lattice.c + 0.1;
              const minBound = -0.1;
              
              const withinBounds = cartCoords[0] >= minBound && cartCoords[0] <= maxX &&
                                 cartCoords[1] >= minBound && cartCoords[1] <= maxY &&
                                 cartCoords[2] >= minBound && cartCoords[2] <= maxZ;
              
              if (withinBounds) {
                expanded.push({
                  species: site.species,
                  cart_coords: cartCoords
                });
              }
            });
          }
        }
      }
    } else {
      expanded.push(...structure.sites);
    }
    
    // Calculate bounds
    let minX = Infinity, maxX = -Infinity;
    let minY = Infinity, maxY = -Infinity;
    let minZ = Infinity, maxZ = -Infinity;
    
    expanded.forEach(site => {
      const [x, y, z] = site.cart_coords;
      minX = Math.min(minX, x);
      maxX = Math.max(maxX, x);
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
      minZ = Math.min(minZ, z);
      maxZ = Math.max(maxZ, z);
    });
    
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    const centerZ = (minZ + maxZ) / 2;
    
    const rangeX = maxX - minX;
    const rangeY = maxY - minY;
    const rangeZ = maxZ - minZ;
    const maxRange = Math.max(rangeX, rangeY, rangeZ);
    
    return {
      expandedSites: expanded,
      center: [centerX, centerY, centerZ] as [number, number, number],
      bounds: Math.max(maxRange * 1.5, 10)
    };
  }, [structure]);
  
  if (!structure || !structure.sites || structure.sites.length === 0) {
    return (
      <Box
        component="div"
        sx={{
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: 'background.paper',
          border: 1,
          borderColor: 'divider',
          borderRadius: 1,
        }}
      >
        <Typography color="text.secondary">
          No structure data available
        </Typography>
      </Box>
    );
  }
  
  return (
    <Box
      component="div"
      sx={{
        height,
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
        overflow: 'hidden',
        bgcolor: 'background.paper',
      }}
    >
      <Canvas
        gl={{ antialias: true, alpha: false }}
        dpr={window.devicePixelRatio}
        style={{ background: '#f5f5f5' }}
      >
        <Suspense fallback={null}>
          <Scene 
            structure={structure}
            showUnitCell={showUnitCell}
            atomScale={atomScale}
          />
        </Suspense>
      </Canvas>
      
      {/* Simple loading indicator overlay */}
      <Suspense 
        fallback={
          <Box
            component="div"
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              bgcolor: 'rgba(255, 255, 255, 0.8)',
            }}
          >
            <CircularProgress />
          </Box>
        }
      />
      
      {/* Simple Debug Overlay */}
      <Box
        component="div"
        sx={{
          position: 'absolute',
          top: 8,
          left: 8,
          bgcolor: 'rgba(0,0,0,0.8)',
          color: 'white',
          p: 1,
          borderRadius: 1,
          fontFamily: 'monospace',
          fontSize: '0.75rem',
          maxWidth: 200,
          zIndex: 10
        }}
      >
        <div>🔍 DEBUG INFO</div>
        <div>Original: {structure.sites?.length || 0} atoms</div>
        <div>Rendered: {debugInfo.expandedSites.length} atoms</div>
        <div>Center: [{debugInfo.center.map(x => x.toFixed(1)).join(', ')}]</div>
        <div>Bounds: {debugInfo.bounds.toFixed(1)}</div>
        <div>Valid: {validation.isValid ? '✅' : '❌'}</div>
        {debugInfo.expandedSites.slice(0, 2).map((site, i) => (
          <div key={i}>{site.species}: [{site.cart_coords?.map((x: number) => x.toFixed(1)).join(', ')}]</div>
        ))}
      </Box>

      {/* Full Debug Information */}
      <DebugInfo 
        structure={structure}
        expandedSites={debugInfo.expandedSites}
        center={debugInfo.center}
        bounds={debugInfo.bounds}
        validation={validation}
      />
    </Box>
  );
};

export default CrystalStructure3D;
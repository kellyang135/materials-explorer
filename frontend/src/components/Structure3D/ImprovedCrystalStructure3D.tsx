import React, { useEffect, useRef, useMemo } from 'react';
import { Box, Typography, Paper } from '@mui/material';
import * as THREE from 'three';
import { Structure } from '../../types/api';
import { ATOMIC_DATA } from './atomicData';

interface ImprovedCrystalStructure3DProps {
  structure: Structure;
}

const ImprovedCrystalStructure3D: React.FC<ImprovedCrystalStructure3DProps> = ({ structure }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const animationIdRef = useRef<number | null>(null);

  // Process structure data with improved logic
  const processedStructure = useMemo(() => {
    console.log('Processing structure:', structure);
    
    if (!structure?.sites || !structure?.lattice) {
      console.warn('Invalid structure data');
      return { atoms: [], bonds: [], unitCell: null };
    }

    // Create unit cell vectors from lattice parameters
    const { a, b, c, alpha, beta, gamma } = structure.lattice;
    
    // Convert angles to radians
    const alphaRad = (alpha * Math.PI) / 180;
    const betaRad = (beta * Math.PI) / 180;
    const gammaRad = (gamma * Math.PI) / 180;

    // Calculate lattice vectors (standard crystallographic conversion)
    const cosAlpha = Math.cos(alphaRad);
    const cosBeta = Math.cos(betaRad);
    const cosGamma = Math.cos(gammaRad);
    const sinGamma = Math.sin(gammaRad);

    // Unit cell vectors
    const aVec = new THREE.Vector3(a, 0, 0);
    const bVec = new THREE.Vector3(b * cosGamma, b * sinGamma, 0);
    const cVec = new THREE.Vector3(
      c * cosBeta,
      c * (cosAlpha - cosBeta * cosGamma) / sinGamma,
      c * Math.sqrt(1 - cosBeta * cosBeta - ((cosAlpha - cosBeta * cosGamma) / sinGamma) ** 2)
    );

    console.log('Lattice vectors:', { aVec, bVec, cVec });

    // Generate atoms with proper expansion
    const atoms: Array<{
      position: THREE.Vector3;
      element: string;
      radius: number;
      color: string;
    }> = [];

    // Determine expansion factor based on structure size
    const avgLatticeParam = (a + b + c) / 3;
    const expansionSize = avgLatticeParam < 5 ? 2 : 1; // Expand small cells more

    for (let i = 0; i < expansionSize; i++) {
      for (let j = 0; j < expansionSize; j++) {
        for (let k = 0; k < expansionSize; k++) {
          structure.sites.forEach((site, siteIndex) => {
            // Get fractional coordinates
            const [fx, fy, fz] = site.frac_coords;
            
            // Add lattice translations
            const fracX = fx + i;
            const fracY = fy + j;
            const fracZ = fz + k;
            
            // Convert to cartesian using lattice vectors
            const position = new THREE.Vector3()
              .addScaledVector(aVec, fracX)
              .addScaledVector(bVec, fracY)
              .addScaledVector(cVec, fracZ);

            // Get element properties
            const element = site.species;
            const atomData = ATOMIC_DATA[element] || ATOMIC_DATA['C']; // Default to carbon if unknown
            
            atoms.push({
              position,
              element,
              radius: atomData.radius * 0.3, // Scale for better visualization
              color: atomData.color
            });
          });
        }
      }
    }

    // Generate bonds (simple distance-based bonding)
    const bonds: Array<{
      start: THREE.Vector3;
      end: THREE.Vector3;
      length: number;
    }> = [];

    const maxBondDistance = 3.0; // Reasonable bond cutoff
    
    for (let i = 0; i < atoms.length; i++) {
      for (let j = i + 1; j < atoms.length; j++) {
        const distance = atoms[i].position.distanceTo(atoms[j].position);
        
        if (distance < maxBondDistance && distance > 0.1) {
          // Check if it's a reasonable bond based on atomic radii
          const expectedBondLength = (atoms[i].radius + atoms[j].radius) / 0.3; // Unscale radii
          
          if (distance < expectedBondLength * 1.5) {
            bonds.push({
              start: atoms[i].position.clone(),
              end: atoms[j].position.clone(),
              length: distance
            });
          }
        }
      }
    }

    // Create unit cell outline
    const unitCell = {
      vertices: [
        new THREE.Vector3(0, 0, 0),
        aVec.clone(),
        aVec.clone().add(bVec),
        bVec.clone(),
        cVec.clone(),
        aVec.clone().add(cVec),
        aVec.clone().add(bVec).add(cVec),
        bVec.clone().add(cVec)
      ]
    };

    console.log(`Generated ${atoms.length} atoms and ${bonds.length} bonds`);
    
    return { atoms, bonds, unitCell };
  }, [structure]);

  // Initialize and update 3D scene
  useEffect(() => {
    if (!containerRef.current || !processedStructure.atoms.length) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Create scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8f9fa);
    sceneRef.current = scene;

    // Create camera
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    cameraRef.current = camera;

    // Create renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    rendererRef.current = renderer;

    container.appendChild(renderer.domElement);

    // Add lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 10, 10);
    directionalLight.castShadow = true;
    scene.add(directionalLight);

    // Add atoms
    const atomGroup = new THREE.Group();
    processedStructure.atoms.forEach((atom, index) => {
      const geometry = new THREE.SphereGeometry(atom.radius, 16, 12);
      const material = new THREE.MeshLambertMaterial({ 
        color: atom.color,
        transparent: true,
        opacity: 0.8
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.copy(atom.position);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      atomGroup.add(mesh);
    });
    scene.add(atomGroup);

    // Add bonds
    const bondGroup = new THREE.Group();
    processedStructure.bonds.forEach((bond) => {
      const direction = bond.end.clone().sub(bond.start);
      const length = direction.length();
      
      const geometry = new THREE.CylinderGeometry(0.1, 0.1, length);
      const material = new THREE.MeshLambertMaterial({ color: 0x666666 });
      const mesh = new THREE.Mesh(geometry, material);
      
      // Position and orient the cylinder
      mesh.position.copy(bond.start.clone().add(bond.end).multiplyScalar(0.5));
      mesh.lookAt(bond.end);
      mesh.rotateX(Math.PI / 2);
      
      bondGroup.add(mesh);
    });
    scene.add(bondGroup);

    // Add unit cell wireframe
    const wireframeGroup = new THREE.Group();
    if (processedStructure.unitCell) {
      const edges = [
        [0, 1], [1, 2], [2, 3], [3, 0], // bottom face
        [4, 5], [5, 6], [6, 7], [7, 4], // top face
        [0, 4], [1, 5], [2, 6], [3, 7]  // vertical edges
      ];

      edges.forEach(([i, j]) => {
        const geometry = new THREE.BufferGeometry().setFromPoints([
          processedStructure.unitCell!.vertices[i],
          processedStructure.unitCell!.vertices[j]
        ]);
        const material = new THREE.LineBasicMaterial({ 
          color: 0x0D4E41, 
          linewidth: 2,
          transparent: true,
          opacity: 0.6
        });
        const line = new THREE.Line(geometry, material);
        wireframeGroup.add(line);
      });
    }
    scene.add(wireframeGroup);

    // Position camera
    const boundingBox = new THREE.Box3();
    scene.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        boundingBox.expandByObject(object);
      }
    });

    const center = boundingBox.getCenter(new THREE.Vector3());
    const size = boundingBox.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    
    camera.position.set(center.x + maxDim, center.y + maxDim, center.z + maxDim);
    camera.lookAt(center);

    // Animation loop
    let animationTime = 0;
    const animate = () => {
      animationTime += 0.01;
      
      // Gentle rotation
      atomGroup.rotation.y = animationTime * 0.5;
      bondGroup.rotation.y = animationTime * 0.5;
      wireframeGroup.rotation.y = animationTime * 0.5;
      
      renderer.render(scene, camera);
      animationIdRef.current = requestAnimationFrame(animate);
    };
    animate();

    // Handle resize
    const handleResize = () => {
      if (!container) return;
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight;
      
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [processedStructure]);

  if (!structure?.sites?.length) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="text.secondary">
          No structure data available for 3D visualization
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      <Box
        ref={containerRef}
        sx={{
          width: '100%',
          height: 400,
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 1,
          position: 'relative',
          overflow: 'hidden'
        }}
      />
      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
        {structure.crystal_system} crystal system • {structure.sites.length} atoms in unit cell
      </Typography>
    </Box>
  );
};

export default ImprovedCrystalStructure3D;
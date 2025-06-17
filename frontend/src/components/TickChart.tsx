import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import type { Trade } from '../types';

interface TickChartProps {
  trades: Trade[];
  width?: number;
  height?: number;
}

interface TickPoint {
  price: number;
  time: number;
  volume: number;
}

export const TickChart: React.FC<TickChartProps> = ({
  trades,
  width = 800,
  height = 400
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene>();
  const rendererRef = useRef<THREE.WebGLRenderer>();
  const cameraRef = useRef<THREE.PerspectiveCamera>();
  const frameRef = useRef<number>();
  const [isInitialized, setIsInitialized] = useState(false);
  
  // Initialize Three.js scene
  useEffect(() => {
    if (!mountRef.current || isInitialized) return;
    
    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8fafc);
    sceneRef.current = scene;
    
    // Camera setup
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.set(0, 0, 10);
    cameraRef.current = camera;
    
    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    rendererRef.current = renderer;
    
    mountRef.current.appendChild(renderer.domElement);
    
    // Add grid
    const gridHelper = new THREE.GridHelper(20, 20, 0x888888, 0xcccccc);
    gridHelper.rotateX(Math.PI / 2);
    scene.add(gridHelper);
    
    // Add axes
    const axesHelper = new THREE.AxesHelper(5);
    scene.add(axesHelper);
    
    // Add lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 10, 5);
    scene.add(directionalLight);
    
    setIsInitialized(true);
    
    return () => {
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
      }
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [width, height, isInitialized]);
  
  // Update chart with new trade data
  useEffect(() => {
    if (!isInitialized || !sceneRef.current || !rendererRef.current || !cameraRef.current) return;
    
    const scene = sceneRef.current;
    const renderer = rendererRef.current;
    const camera = cameraRef.current;
    
    // Clear existing tick points
    const tickPoints = scene.children.filter(child => child.userData.type === 'tick');
    tickPoints.forEach(point => scene.remove(point));
    
    if (trades.length === 0) {
      renderer.render(scene, camera);
      return;
    }
    
    // Process trades into tick points
    const tickData: TickPoint[] = trades.slice(0, 500).map(trade => ({
      price: trade.price,
      time: trade.timestamp,
      volume: trade.quantity
    }));
    
    if (tickData.length === 0) return;
    
    // Calculate bounds
    const prices = tickData.map(d => d.price);
    const times = tickData.map(d => d.time);
    const volumes = tickData.map(d => d.volume);
    
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const minTime = Math.min(...times);
    const maxTime = Math.max(...times);
    const maxVolume = Math.max(...volumes);
    
    // Normalize coordinates
    const scaleX = 15; // Time axis scale
    const scaleY = 10; // Price axis scale
    const scaleZ = 5;  // Volume axis scale
    
    // Create geometry for all tick points
    const geometry = new THREE.BufferGeometry();
    const positions: number[] = [];
    const colors: number[] = [];
    const sizes: number[] = [];
    
    tickData.forEach((tick, index) => {
      // Normalize coordinates
      const x = ((tick.time - minTime) / (maxTime - minTime) - 0.5) * scaleX;
      const y = ((tick.price - minPrice) / (maxPrice - minPrice) - 0.5) * scaleY;
      const z = (tick.volume / maxVolume) * scaleZ;
      
      positions.push(x, y, z);
      
      // Color based on price movement (simplified)
      const color = new THREE.Color();
      if (index > 0) {
        const prevPrice = tickData[index - 1].price;
        if (tick.price > prevPrice) {
          color.setHex(0x22c55e); // Green for price increase
        } else if (tick.price < prevPrice) {
          color.setHex(0xef4444); // Red for price decrease
        } else {
          color.setHex(0x6b7280); // Gray for no change
        }
      } else {
        color.setHex(0x6b7280);
      }
      
      colors.push(color.r, color.g, color.b);
      
      // Size based on volume
      const size = Math.max(2, (tick.volume / maxVolume) * 8);
      sizes.push(size);
    });
    
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    geometry.setAttribute('size', new THREE.Float32BufferAttribute(sizes, 1));
    
    // Create material with vertex colors
    const material = new THREE.PointsMaterial({
      size: 0.1,
      vertexColors: true,
      transparent: true,
      opacity: 0.8,
      sizeAttenuation: true
    });
    
    // Create points mesh
    const points = new THREE.Points(geometry, material);
    points.userData.type = 'tick';
    scene.add(points);
    
    // Create connecting lines
    const lineGeometry = new THREE.BufferGeometry();
    const linePositions: number[] = [];
    
    for (let i = 0; i < tickData.length - 1; i++) {
      const tick1 = tickData[i];
      const tick2 = tickData[i + 1];
      
      const x1 = ((tick1.time - minTime) / (maxTime - minTime) - 0.5) * scaleX;
      const y1 = ((tick1.price - minPrice) / (maxPrice - minPrice) - 0.5) * scaleY;
      const z1 = (tick1.volume / maxVolume) * scaleZ;
      
      const x2 = ((tick2.time - minTime) / (maxTime - minTime) - 0.5) * scaleX;
      const y2 = ((tick2.price - minPrice) / (maxPrice - minPrice) - 0.5) * scaleY;
      const z2 = (tick2.volume / maxVolume) * scaleZ;
      
      linePositions.push(x1, y1, z1, x2, y2, z2);
    }
    
    lineGeometry.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));
    
    const lineMaterial = new THREE.LineBasicMaterial({
      color: 0x3b82f6,
      transparent: true,
      opacity: 0.6
    });
    
    const lines = new THREE.LineSegments(lineGeometry, lineMaterial);
    lines.userData.type = 'tick';
    scene.add(lines);
    
    // Animation loop
    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);
      
      // Rotate camera around the scene
      const time = Date.now() * 0.0005;
      camera.position.x = Math.cos(time) * 15;
      camera.position.z = Math.sin(time) * 15;
      camera.lookAt(0, 0, 0);
      
      renderer.render(scene, camera);
    };
    
    animate();
    
    return () => {
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
      }
    };
  }, [trades, isInitialized]);
  
  // Handle resize
  useEffect(() => {
    if (!rendererRef.current || !cameraRef.current) return;
    
    const renderer = rendererRef.current;
    const camera = cameraRef.current;
    
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  }, [width, height]);
  
  return (
    <div className="tick-chart">
      <h3 style={{ textAlign: 'center', margin: '0 0 10px 0' }}>
        3D Tick Chart - Real-time Trades
      </h3>
      <div
        ref={mountRef}
        style={{
          width: width,
          height: height,
          border: '1px solid #ccc',
          borderRadius: '4px',
          position: 'relative',
          overflow: 'hidden'
        }}
      />
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        gap: '20px',
        marginTop: '10px',
        fontSize: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{ width: '12px', height: '12px', backgroundColor: '#22c55e', marginRight: '5px' }}></div>
          Price Up
        </div>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{ width: '12px', height: '12px', backgroundColor: '#ef4444', marginRight: '5px' }}></div>
          Price Down
        </div>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{ width: '12px', height: '12px', backgroundColor: '#3b82f6', marginRight: '5px' }}></div>
          Connections
        </div>
      </div>
      <div style={{ textAlign: 'center', marginTop: '5px', fontSize: '11px', color: '#666' }}>
        X: Time | Y: Price | Z: Volume | Auto-rotating view
      </div>
    </div>
  );
};
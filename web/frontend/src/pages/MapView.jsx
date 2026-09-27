import React, { useEffect, useRef } from 'react';
import { useSocket } from '../context/SocketContext';
import './MapView.css';

function MapView() {
  const canvasRef = useRef(null);
  const { visualizationData, emit } = useSocket();

  useEffect(() => {
    // Request visualization data on mount
    emit('request_visualization_data');
    
    // Set up periodic updates
    const interval = setInterval(() => {
      emit('request_visualization_data');
    }, 2000);

    return () => clearInterval(interval);
  }, [emit]);

  useEffect(() => {
    if (canvasRef.current && visualizationData) {
      drawVisualization(canvasRef.current, visualizationData);
    }
  }, [visualizationData]);

  const drawVisualization = (canvas, data) => {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.fillStyle = '#f5f5f5';
    ctx.fillRect(0, 0, width, height);

    // Get bounds for scaling
    const allPoints = [
      ...(data.fire || []),
      ...(data.boundary || []),
      ...(data.mesh || []),
      ...(data.drones || [])
    ];

    if (allPoints.length === 0) {
      ctx.fillStyle = '#999';
      ctx.font = '16px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('No data to display', width / 2, height / 2);
      return;
    }

    // Find bounds
    let minLat = allPoints[0][0] || 0;
    let maxLat = minLat;
    let minLon = allPoints[0][1] || 0;
    let maxLon = minLon;

    allPoints.forEach(point => {
      const lat = point[0] || 0;
      const lon = point[1] || 0;
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
      minLon = Math.min(minLon, lon);
      maxLon = Math.max(maxLon, lon);
    });

    const padding = 40;
    const scale = (point) => {
      const x = ((point[1] - minLon) / (maxLon - minLon)) * (width - 2 * padding) + padding;
      const y = height - padding - ((point[0] - minLat) / (maxLat - minLat)) * (height - 2 * padding);
      return [x, y];
    };

    // Draw fire observations
    if (data.fire && data.fire.length > 0) {
      ctx.fillStyle = '#ef4444';
      ctx.globalAlpha = 0.7;
      data.fire.forEach(point => {
        const [x, y] = scale(point);
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.globalAlpha = 1;
    }

    // Draw fire boundary
    if (data.boundary && data.boundary.length > 0) {
      ctx.strokeStyle = '#ff6b6b';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      const [startX, startY] = scale(data.boundary[0]);
      ctx.moveTo(startX, startY);
      for (let i = 1; i < data.boundary.length; i++) {
        const [x, y] = scale(data.boundary[i]);
        ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Draw mesh nodes
    if (data.mesh && data.mesh.length > 0) {
      ctx.fillStyle = '#3b82f6';
      ctx.globalAlpha = 0.5;
      data.mesh.forEach(point => {
        const [x, y] = scale(point);
        ctx.fillRect(x - 2, y - 2, 4, 4);
      });
      ctx.globalAlpha = 1;
    }

    // Draw drone paths
    if (data.paths && data.paths.length > 0) {
      const colors = ['#22c55e', '#3b82f6', '#a855f7', '#f59e0b', '#06b6d4', '#ec4899'];
      data.paths.forEach((pathData, idx) => {
        ctx.strokeStyle = colors[idx % colors.length];
        ctx.lineWidth = 1.5;
        ctx.globalAlpha = 0.6;
        ctx.beginPath();
        const path = pathData.path || [];
        if (path.length > 0) {
          const [startX, startY] = scale(path[0]);
          ctx.moveTo(startX, startY);
          for (let i = 1; i < path.length; i++) {
            const [x, y] = scale(path[i]);
            ctx.lineTo(x, y);
          }
          ctx.stroke();
        }
        ctx.globalAlpha = 1;
      });
    }

    // Draw drones
    if (data.drones && data.drones.length > 0) {
      data.drones.forEach((drone, idx) => {
        const [x, y] = scale(drone.position || [0, 0]);
        
        // Draw drone circle
        ctx.fillStyle = drone.status === 'active' ? '#22c55e' : '#999';
        ctx.beginPath();
        ctx.arc(x, y, 6, 0, Math.PI * 2);
        ctx.fill();

        // Draw drone label
        ctx.fillStyle = '#333';
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(`D${idx + 1}`, x, y + 15);

        // Draw battery indicator
        const battery = drone.battery || 100;
        ctx.fillStyle = battery > 50 ? '#4ade80' : battery > 20 ? '#fbbf24' : '#ef4444';
        ctx.fillRect(x - 4, y - 10, 8, 2);
      });
    }

    // Draw risk zones
    if (data.risk_zones && Object.keys(data.risk_zones).length > 0) {
      // This would be more complex to draw; typically done with heat map
      // Placeholder for risk zone visualization
    }

    // Draw legend
    drawLegend(ctx, width, height);
  };

  const drawLegend = (ctx, width, height) => {
    const items = [
      { label: 'Fire Observations', color: '#ef4444', style: 'circle' },
      { label: 'Fire Boundary', color: '#ff6b6b', style: 'line' },
      { label: 'Mesh Nodes', color: '#3b82f6', style: 'square' },
      { label: 'Drones', color: '#22c55e', style: 'circle' }
    ];

    ctx.font = '12px Arial';
    ctx.textAlign = 'left';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.fillRect(width - 160, height - 120, 150, 110);

    ctx.strokeStyle = '#999';
    ctx.lineWidth = 1;
    ctx.strokeRect(width - 160, height - 120, 150, 110);

    items.forEach((item, idx) => {
      const y = height - 105 + idx * 25;
      
      ctx.fillStyle = item.color;
      if (item.style === 'circle') {
        ctx.beginPath();
        ctx.arc(width - 145, y + 5, 3, 0, Math.PI * 2);
        ctx.fill();
      } else if (item.style === 'line') {
        ctx.beginPath();
        ctx.moveTo(width - 150, y + 5);
        ctx.lineTo(width - 140, y + 5);
        ctx.stroke();
      } else if (item.style === 'square') {
        ctx.fillRect(width - 148, y + 2, 6, 6);
      }

      ctx.fillStyle = '#333';
      ctx.fillText(item.label, width - 130, y + 8);
    });
  };

  return (
    <div className="map-view">
      <div className="map-header">
        <h1>Real-time Map Visualization</h1>
        <p>Fire boundary, drone positions, paths, and risk zones</p>
      </div>

      <div className="map-container">
        <canvas
          ref={canvasRef}
          width={window.innerWidth - 60}
          height={window.innerHeight - 200}
          className="map-canvas"
        />
      </div>

      <div className="map-controls">
        <div className="control-info">
          <p>🔥 Red dots = Fire observations</p>
          <p>🟦 Blue squares = Mesh nodes</p>
          <p>🚁 Green circles = Drones</p>
          <p>📍 Colored lines = Drone paths</p>
        </div>
      </div>
    </div>
  );
}

export default MapView;

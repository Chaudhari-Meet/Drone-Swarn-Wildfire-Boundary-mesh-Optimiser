/**
 * Maps Page - Fire detection and drone tracking map
 */

import React, { useEffect } from 'react';
import { useStore } from '../store';
import './Maps.css';

const Maps: React.FC = () => {
  const { fireObservations, fireBoundary, drones, loadFireData, loadDrones } = useStore();

  useEffect(() => {
    loadFireData();
    loadDrones();
    const interval = setInterval(() => {
      loadFireData();
      loadDrones();
    }, 10000);
    return () => clearInterval(interval);
  }, [loadFireData, loadDrones]);

  // Calculate bounds for map center
  const getCenter = () => {
    if (fireObservations.length === 0) return { lat: 35.0, lon: -120.0 };
    const lats = fireObservations.map((o) => o.latitude);
    const lons = fireObservations.map((o) => o.longitude);
    return {
      lat: (Math.min(...lats) + Math.max(...lats)) / 2,
      lon: (Math.min(...lons) + Math.max(...lons)) / 2,
    };
  };

  const center = getCenter();

  return (
    <div className="maps-page">
      <h1>Fire & Drone Tracking Map</h1>

      <div className="map-container">
        {/* Simple map placeholder - would use Leaflet/Mapbox in production */}
        <svg className="map-svg" viewBox="34 -121 2 2" width="100%" height="600">
          {/* Map background */}
          <rect x="34" y="-121" width="2" height="2" fill="#e8f4f8" />

          {/* Fire observations */}
          {fireObservations.map((obs, i) => (
            <circle
              key={`obs-${i}`}
              cx={obs.longitude}
              cy={obs.latitude}
              r="0.01"
              fill="red"
              opacity={obs.confidence}
              title={`Fire ${i + 1} (${obs.confidence.toFixed(2)})`}
            />
          ))}

          {/* Fire boundary */}
          {fireBoundary.length > 1 && (
            <polyline
              points={fireBoundary.map((p) => `${p[1]},${p[0]}`).join(' ')}
              fill="none"
              stroke="orange"
              strokeWidth="0.005"
              opacity="0.7"
            />
          )}

          {/* Drones */}
          {drones.map((drone) =>
            drone.position ? (
              <g key={`drone-${drone.drone_id}`}>
                <circle
                  cx={drone.position[1]}
                  cy={drone.position[0]}
                  r="0.015"
                  fill={drone.armed ? 'green' : 'gray'}
                  opacity="0.8"
                />
                <text
                  x={drone.position[1]}
                  y={drone.position[0] + 0.03}
                  fontSize="0.02"
                  textAnchor="middle"
                  fill="black"
                >
                  D{drone.drone_id}
                </text>
              </g>
            ) : null
          )}
        </svg>

        {/* Legend */}
        <div className="map-legend">
          <h4>Legend</h4>
          <div className="legend-item">
            <div className="legend-symbol" style={{ backgroundColor: 'red' }}></div>
            <span>Fire Observations</span>
          </div>
          <div className="legend-item">
            <div className="legend-symbol" style={{ borderColor: 'orange' }}></div>
            <span>Fire Boundary</span>
          </div>
          <div className="legend-item">
            <div className="legend-symbol" style={{ backgroundColor: 'green' }}></div>
            <span>Armed Drones</span>
          </div>
          <div className="legend-item">
            <div className="legend-symbol" style={{ backgroundColor: 'gray' }}></div>
            <span>Disarmed Drones</span>
          </div>
        </div>
      </div>

      {/* Data summary */}
      <div className="map-summary">
        <div className="summary-item">
          <strong>Observations:</strong> {fireObservations.length}
        </div>
        <div className="summary-item">
          <strong>Boundary Points:</strong> {fireBoundary.length}
        </div>
        <div className="summary-item">
          <strong>Drones:</strong> {drones.filter((d) => d.position).length}/{drones.length}
        </div>
        <div className="summary-item">
          <strong>Center:</strong> ({center.lat.toFixed(3)}, {center.lon.toFixed(3)})
        </div>
      </div>
    </div>
  );
};

export default Maps;

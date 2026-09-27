import React from 'react';
import './DataPanel.css';

function DataPanel({ systemStatus }) {
  const formatNumber = (num) => {
    if (!num) return '0';
    return num.toLocaleString();
  };

  const formatArea = (area) => {
    if (!area) return '0 m²';
    if (area > 10000) {
      return `${(area / 10000).toFixed(2)} hectares`;
    }
    return `${area.toFixed(2)} m²`;
  };

  return (
    <div className="data-section">
      <h2>System Data</h2>
      
      <div className="data-panels">
        {/* Fire Information */}
        <div className="data-card">
          <div className="card-header">
            <h3>Fire Information</h3>
            <span className="card-icon">🔥</span>
          </div>
          <div className="card-content">
            <div className="data-row">
              <span className="label">Observations:</span>
              <span className="value">{formatNumber(systemStatus?.fire_observations?.length)}</span>
            </div>
            <div className="data-row">
              <span className="label">Area:</span>
              <span className="value">{formatArea(systemStatus?.fire_area)}</span>
            </div>
            <div className="data-row">
              <span className="label">Boundary Points:</span>
              <span className="value">{formatNumber(systemStatus?.boundary_points)}</span>
            </div>
            <div className="data-row">
              <span className="label">Confidence:</span>
              <span className="value">{systemStatus?.boundary_confidence ? `${(systemStatus.boundary_confidence * 100).toFixed(1)}%` : 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* Mesh Information */}
        <div className="data-card">
          <div className="card-header">
            <h3>Mesh Coverage</h3>
            <span className="card-icon">🔲</span>
          </div>
          <div className="card-content">
            <div className="data-row">
              <span className="label">Total Nodes:</span>
              <span className="value">{formatNumber(systemStatus?.mesh_nodes)}</span>
            </div>
            <div className="data-row">
              <span className="label">Grid Spacing:</span>
              <span className="value">{systemStatus?.mesh_spacing ? `${systemStatus.mesh_spacing}m` : 'N/A'}</span>
            </div>
            <div className="data-row">
              <span className="label">Coverage:</span>
              <span className="value">{systemStatus?.coverage_percentage ? `${systemStatus.coverage_percentage.toFixed(1)}%` : 'N/A'}</span>
            </div>
            <div className="data-row">
              <span className="label">Altitude:</span>
              <span className="value">{systemStatus?.mesh_altitude ? `${systemStatus.mesh_altitude}m` : 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* Drone Fleet */}
        <div className="data-card">
          <div className="card-header">
            <h3>Drone Fleet</h3>
            <span className="card-icon">🚁</span>
          </div>
          <div className="card-content">
            <div className="data-row">
              <span className="label">Total Drones:</span>
              <span className="value">{formatNumber(systemStatus?.num_drones)}</span>
            </div>
            <div className="data-row">
              <span className="label">Avg Battery:</span>
              <span className="value">{systemStatus?.average_battery ? `${systemStatus.average_battery.toFixed(0)}%` : 'N/A'}</span>
            </div>
            <div className="data-row">
              <span className="label">Total Path Distance:</span>
              <span className="value">{systemStatus?.total_path_distance ? `${systemStatus.total_path_distance.toFixed(0)}m` : 'N/A'}</span>
            </div>
            <div className="data-row">
              <span className="label">Optimization Gain:</span>
              <span className="value">{systemStatus?.optimization_improvement ? `${systemStatus.optimization_improvement.toFixed(1)}%` : 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* Risk Assessment */}
        <div className="data-card">
          <div className="card-header">
            <h3>Risk Assessment</h3>
            <span className="card-icon">⚠️</span>
          </div>
          <div className="card-content">
            <div className="data-row">
              <span className="label risk-green">✓ Green Zone:</span>
              <span className="value">{formatNumber(systemStatus?.risk_zones?.GREEN)}</span>
            </div>
            <div className="data-row">
              <span className="label risk-yellow">⚠ Yellow Zone:</span>
              <span className="value">{formatNumber(systemStatus?.risk_zones?.YELLOW)}</span>
            </div>
            <div className="data-row">
              <span className="label risk-red">✕ Red Zone:</span>
              <span className="value">{formatNumber(systemStatus?.risk_zones?.RED)}</span>
            </div>
            <div className="data-row">
              <span className="label risk-critical">🛑 Critical Zone:</span>
              <span className="value">{formatNumber(systemStatus?.risk_zones?.CRITICAL)}</span>
            </div>
          </div>
        </div>

        {/* Detections */}
        <div className="data-card">
          <div className="card-header">
            <h3>Object Detection</h3>
            <span className="card-icon">🔍</span>
          </div>
          <div className="card-content">
            <div className="data-row">
              <span className="label">Total Detections:</span>
              <span className="value">{formatNumber(systemStatus?.num_detections)}</span>
            </div>
            <div className="data-row">
              <span className="label">Animals Detected:</span>
              <span className="value">{formatNumber(systemStatus?.animals_detected)}</span>
            </div>
            <div className="data-row">
              <span className="label">Persons Detected:</span>
              <span className="value">{formatNumber(systemStatus?.persons_detected)}</span>
            </div>
            <div className="data-row">
              <span className="label">High Confidence:</span>
              <span className="value">{formatNumber(systemStatus?.high_confidence_detections)}</span>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="data-card">
          <div className="card-header">
            <h3>Performance</h3>
            <span className="card-icon">📊</span>
          </div>
          <div className="card-content">
            <div className="data-row">
              <span className="label">Execution Time:</span>
              <span className="value">{systemStatus?.execution_time ? `${systemStatus.execution_time.toFixed(2)}s` : 'N/A'}</span>
            </div>
            <div className="data-row">
              <span className="label">Path Quality:</span>
              <span className="value">{systemStatus?.path_quality ? `${systemStatus.path_quality.toFixed(1)}%` : 'N/A'}</span>
            </div>
            <div className="data-row">
              <span className="label">Last Update:</span>
              <span className="value">{systemStatus?.last_update ? new Date(systemStatus.last_update).toLocaleTimeString() : 'N/A'}</span>
            </div>
            <div className="data-row">
              <span className="label">Mission Status:</span>
              <span className={`value ${systemStatus?.mission_status?.toLowerCase()}`}>
                {systemStatus?.mission_status || 'Idle'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DataPanel;

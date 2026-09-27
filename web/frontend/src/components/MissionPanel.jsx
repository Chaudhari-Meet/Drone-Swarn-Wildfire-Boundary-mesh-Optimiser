import React from 'react';
import './MissionPanel.css';

function MissionPanel({
  numDrones,
  meshSpacing,
  onNumDronesChange,
  onMeshSpacingChange,
  onLoadFireData,
  onGenerateMesh,
  onAllocateDrones,
  onOptimizePaths,
  onAnalyzeRisk,
  onRunDetection,
  onRunMission,
  onRequestVisualization,
  loading,
  missionRunning
}) {
  return (
    <div className="mission-section">
      <h2>Mission Control</h2>
      
      <div className="mission-control">
        {/* Configuration Panel */}
        <div className="config-panel">
          <h3>Configuration</h3>
          
          <div className="config-item">
            <label htmlFor="num-drones">Number of Drones:</label>
            <div className="input-group">
              <input
                id="num-drones"
                type="number"
                min="1"
                max="100"
                value={numDrones}
                onChange={(e) => onNumDronesChange(parseInt(e.target.value))}
                disabled={missionRunning}
              />
              <span className="input-hint">(1-100)</span>
            </div>
          </div>

          <div className="config-item">
            <label htmlFor="mesh-spacing">Mesh Spacing (meters):</label>
            <div className="input-group">
              <input
                id="mesh-spacing"
                type="number"
                min="1"
                max="50"
                step="0.5"
                value={meshSpacing}
                onChange={(e) => onMeshSpacingChange(parseFloat(e.target.value))}
                disabled={missionRunning}
              />
              <span className="input-hint">(1-50m)</span>
            </div>
          </div>
        </div>

        {/* Step-by-Step Mission Panel */}
        <div className="mission-steps">
          <h3>Mission Steps</h3>
          <div className="steps-container">
            <button
              className="step-button"
              onClick={onLoadFireData}
              disabled={loading || missionRunning}
              title="Load fire data from simulation"
            >
              <span className="step-number">1</span>
              <span className="step-label">Load Fire Data</span>
              <span className="step-icon">📊</span>
            </button>

            <button
              className="step-button"
              onClick={onGenerateMesh}
              disabled={loading || missionRunning}
              title="Generate mesh coverage grid"
            >
              <span className="step-number">2</span>
              <span className="step-label">Generate Mesh</span>
              <span className="step-icon">🔲</span>
            </button>

            <button
              className="step-button"
              onClick={onAllocateDrones}
              disabled={loading || missionRunning}
              title="Allocate drones to mesh nodes"
            >
              <span className="step-number">3</span>
              <span className="step-label">Allocate Drones</span>
              <span className="step-icon">🚁</span>
            </button>

            <button
              className="step-button"
              onClick={onOptimizePaths}
              disabled={loading || missionRunning}
              title="Optimize drone paths"
            >
              <span className="step-number">4</span>
              <span className="step-label">Optimize Paths</span>
              <span className="step-icon">📍</span>
            </button>

            <button
              className="step-button"
              onClick={onAnalyzeRisk}
              disabled={loading || missionRunning}
              title="Analyze risk zones"
            >
              <span className="step-number">5</span>
              <span className="step-label">Analyze Risk</span>
              <span className="step-icon">⚠️</span>
            </button>

            <button
              className="step-button"
              onClick={onRunDetection}
              disabled={loading || missionRunning}
              title="Run object detection"
            >
              <span className="step-number">6</span>
              <span className="step-label">Run Detection</span>
              <span className="step-icon">🔍</span>
            </button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="quick-actions">
          <button
            className="action-button primary"
            onClick={onRunMission}
            disabled={missionRunning || loading}
            title="Run complete mission with all steps"
          >
            {missionRunning ? '⏳ Mission Running...' : '▶️ Run Full Mission'}
          </button>

          <button
            className="action-button secondary"
            onClick={onRequestVisualization}
            disabled={missionRunning}
            title="Request live visualization data"
          >
            📺 Refresh Visualization
          </button>
        </div>
      </div>
    </div>
  );
}

export default MissionPanel;

/**
 * Settings Page - System configuration
 */

import React, { useState } from 'react';
import { useStore } from '../store';
import './Settings.css';

const Settings: React.FC = () => {
  const { mode, initializeSystem } = useStore();
  const [settings, setSettings] = useState({
    mode: mode,
    numDrones: 5,
  });

  const handleSave = async () => {
    await initializeSystem(settings.mode, settings.numDrones);
  };

  return (
    <div className="settings-page">
      <h1>System Settings</h1>

      <div className="settings-form">
        <div className="form-section">
          <h3>Operational Mode</h3>

          <div className="form-group">
            <label>Mode:</label>
            <select value={settings.mode} onChange={(e) => setSettings({ ...settings, mode: e.target.value })}>
              <option value="simulation">Simulation</option>
              <option value="real_drone">Real Drone</option>
              <option value="satellite">Satellite Data</option>
              <option value="historical">Historical Data</option>
            </select>
            <p className="form-help">
              {settings.mode === 'simulation' && 'Simulated fire data for testing'}
              {settings.mode === 'real_drone' && 'Real drone telemetry and thermal imaging'}
              {settings.mode === 'satellite' && 'NASA FIRMS and satellite data integration'}
              {settings.mode === 'historical' && 'Historical fire data analysis'}
            </p>
          </div>
        </div>

        <div className="form-section">
          <h3>Fleet Configuration</h3>

          <div className="form-group">
            <label>Number of Drones:</label>
            <input
              type="number"
              min="1"
              max="20"
              value={settings.numDrones}
              onChange={(e) => setSettings({ ...settings, numDrones: Number(e.target.value) })}
            />
          </div>
        </div>

        <div className="form-section">
          <h3>Data Export</h3>

          <div className="export-buttons">
            <a href="/api/export/csv" className="btn-secondary">
              Export as CSV
            </a>
            <a href="/api/export/json" className="btn-secondary">
              Export as JSON
            </a>
            <a href="/api/export/geojson" className="btn-secondary">
              Export as GeoJSON
            </a>
          </div>
        </div>

        <div className="form-actions">
          <button onClick={handleSave} className="btn-primary">
            Apply Settings
          </button>
        </div>
      </div>

      <div className="settings-info">
        <h3>System Information</h3>
        <p><strong>API Version:</strong> 1.0.0</p>
        <p><strong>Frontend Version:</strong> 1.0.0</p>
        <p><strong>Last Updated:</strong> {new Date().toLocaleString()}</p>
      </div>
    </div>
  );
};

export default Settings;

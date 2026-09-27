import React, { useState, useEffect } from 'react';
import { useSystem } from '../context/SystemContext';
import './Settings.css';

function Settings() {
  const { getConfig } = useSystem();
  const [config, setConfig] = useState(null);
  const [settings, setSettings] = useState({
    numDrones: 10,
    meshSpacing: 5,
    altitude: 50,
    useTwoOpt: true,
    riskWeights: {
      distance: 0.25,
      fire: 0.25,
      smoke: 0.15,
      heat: 0.15,
      wind: 0.1,
      terrain: 0.05,
      battery: 0.03,
      obstacle: 0.02
    },
    features: {
      satellite_data: true,
      real_drones: false,
      cloud_integration: false,
      ml_detection: true
    }
  });

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const data = await getConfig();
      setConfig(data);
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  };

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleRiskWeightChange = (weight, value) => {
    setSettings(prev => ({
      ...prev,
      riskWeights: {
        ...prev.riskWeights,
        [weight]: parseFloat(value)
      }
    }));
  };

  const handleFeatureToggle = (feature) => {
    setSettings(prev => ({
      ...prev,
      features: {
        ...prev.features,
        [feature]: !prev.features[feature]
      }
    }));
  };

  const handleSaveSettings = () => {
    localStorage.setItem('systemSettings', JSON.stringify(settings));
    alert('Settings saved successfully!');
  };

  const handleResetSettings = () => {
    if (window.confirm('Reset all settings to defaults?')) {
      localStorage.removeItem('systemSettings');
      window.location.reload();
    }
  };

  const getTotalRiskWeight = () => {
    return Object.values(settings.riskWeights).reduce((a, b) => a + b, 0).toFixed(2);
  };

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h1>System Settings</h1>
        <p>Configure system parameters and preferences</p>
      </div>

      <div className="settings-grid">
        {/* General Settings */}
        <div className="settings-card">
          <div className="card-header">
            <h3>General Settings</h3>
            <span className="card-icon">⚙️</span>
          </div>
          <div className="card-content">
            <div className="setting-item">
              <label htmlFor="num-drones">Default Number of Drones:</label>
              <div className="input-wrapper">
                <input
                  id="num-drones"
                  type="number"
                  min="1"
                  max="100"
                  value={settings.numDrones}
                  onChange={(e) => handleSettingChange('numDrones', parseInt(e.target.value))}
                />
                <span className="unit">drones</span>
              </div>
            </div>

            <div className="setting-item">
              <label htmlFor="mesh-spacing">Mesh Spacing:</label>
              <div className="input-wrapper">
                <input
                  id="mesh-spacing"
                  type="number"
                  min="1"
                  max="50"
                  step="0.5"
                  value={settings.meshSpacing}
                  onChange={(e) => handleSettingChange('meshSpacing', parseFloat(e.target.value))}
                />
                <span className="unit">meters</span>
              </div>
            </div>

            <div className="setting-item">
              <label htmlFor="altitude">Drone Altitude:</label>
              <div className="input-wrapper">
                <input
                  id="altitude"
                  type="number"
                  min="10"
                  max="500"
                  value={settings.altitude}
                  onChange={(e) => handleSettingChange('altitude', parseInt(e.target.value))}
                />
                <span className="unit">meters</span>
              </div>
            </div>

            <div className="setting-item checkbox">
              <label htmlFor="two-opt">
                <input
                  id="two-opt"
                  type="checkbox"
                  checked={settings.useTwoOpt}
                  onChange={(e) => handleSettingChange('useTwoOpt', e.target.checked)}
                />
                <span>Use 2-opt Path Optimization</span>
              </label>
              <p className="help-text">Enable advanced path optimization algorithm</p>
            </div>
          </div>
        </div>

        {/* Risk Weighting */}
        <div className="settings-card">
          <div className="card-header">
            <h3>Risk Analysis Weights</h3>
            <span className="card-icon">⚠️</span>
          </div>
          <div className="card-content">
            <p className="weight-total">Total Weight: <strong>{getTotalRiskWeight()}</strong> (should be 1.0)</p>
            
            <div className="weights-container">
              {Object.entries(settings.riskWeights).map(([weight, value]) => (
                <div key={weight} className="weight-item">
                  <label htmlFor={`weight-${weight}`}>
                    {weight.charAt(0).toUpperCase() + weight.slice(1)}:
                  </label>
                  <div className="weight-input">
                    <input
                      id={`weight-${weight}`}
                      type="number"
                      min="0"
                      max="1"
                      step="0.01"
                      value={value}
                      onChange={(e) => handleRiskWeightChange(weight, e.target.value)}
                    />
                    <span className="weight-percent">{(value * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="weight-help">
              <p>Adjust weights to prioritize different risk factors. Total should equal 1.0.</p>
            </div>
          </div>
        </div>

        {/* Feature Flags */}
        <div className="settings-card">
          <div className="card-header">
            <h3>Features</h3>
            <span className="card-icon">✨</span>
          </div>
          <div className="card-content">
            {Object.entries(settings.features).map(([feature, enabled]) => (
              <div key={feature} className="feature-item" onClick={() => handleFeatureToggle(feature)}>
                <div className="feature-toggle">
                  <input
                    type="checkbox"
                    checked={enabled}
                    onChange={() => {}}
                    className="toggle-checkbox"
                  />
                  <span className={`toggle-label ${enabled ? 'enabled' : 'disabled'}`}></span>
                </div>
                <div className="feature-info">
                  <span className="feature-name">
                    {feature.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                  </span>
                  <span className="feature-status">
                    {enabled ? '✓ Enabled' : '✗ Disabled'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* System Info */}
        <div className="settings-card">
          <div className="card-header">
            <h3>System Information</h3>
            <span className="card-icon">ℹ️</span>
          </div>
          <div className="card-content info-content">
            <div className="info-item">
              <span className="info-label">Version:</span>
              <span className="info-value">{config?.version || '1.0.0'}</span>
            </div>

            <div className="info-item">
              <span className="info-label">Mode:</span>
              <span className="info-value">{config?.mode || 'simulation'}</span>
            </div>

            <div className="info-item">
              <span className="info-label">API Status:</span>
              <span className="info-value">✓ Connected</span>
            </div>

            <div className="info-item">
              <span className="info-label">Storage:</span>
              <span className="info-value">Local Browser</span>
            </div>

            <div className="info-item">
              <span className="info-label">Last Updated:</span>
              <span className="info-value">{new Date().toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Safety & Privacy */}
        <div className="settings-card full-width">
          <div className="card-header">
            <h3>Safety & Privacy</h3>
            <span className="card-icon">🔒</span>
          </div>
          <div className="card-content">
            <div className="safety-notice">
              <h4>Data Privacy</h4>
              <p>
                All data is stored locally in your browser. No personal or mission data is sent to external servers.
                This system uses simulation data only and does not connect to real satellites or drone systems.
              </p>
            </div>

            <div className="safety-notice">
              <h4>Safety Disclaimer</h4>
              <p>
                <strong>⚠️ IMPORTANT:</strong> This is an academic simulation system. All recommendations are for 
                demonstration purposes only and must not be used for actual emergency response without:
              </p>
              <ul>
                <li>Integration with real satellite data verification</li>
                <li>Real drone hardware and flight testing</li>
                <li>Professional emergency response coordination</li>
                <li>Qualified human operator oversight at all times</li>
              </ul>
            </div>

            <div className="safety-notice">
              <h4>Firefighter Route Warning</h4>
              <p>
                All firefighter routes are recommendations only and must not be used for actual firefighting 
                operations. Trained firefighters must make all route decisions based on real-time field conditions 
                and professional judgment.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="settings-actions">
        <button className="btn btn-primary" onClick={handleSaveSettings}>
          💾 Save Settings
        </button>
        <button className="btn btn-danger" onClick={handleResetSettings}>
          🔄 Reset to Defaults
        </button>
      </div>

      <div className="settings-footer">
        <p>
          <strong>Help & Support:</strong> For issues or questions, refer to the system documentation 
          or contact your system administrator.
        </p>
      </div>
    </div>
  );
}

export default Settings;

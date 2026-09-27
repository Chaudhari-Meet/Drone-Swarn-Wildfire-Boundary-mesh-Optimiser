import React, { useState, useEffect } from 'react';
import { useSystem } from '../context/SystemContext';
import './Missions.css';

function Missions() {
  const { 
    runMission, 
    exportReport, 
    getCurrentReport,
    loading 
  } = useSystem();

  const [missions, setMissions] = useState([]);
  const [selectedMission, setSelectedMission] = useState(null);
  const [newMission, setNewMission] = useState({ numDrones: 10, meshSpacing: 5, name: '' });

  useEffect(() => {
    // Load missions from localStorage
    const savedMissions = localStorage.getItem('missions');
    if (savedMissions) {
      setMissions(JSON.parse(savedMissions));
    }
  }, []);

  const handleStartMission = async () => {
    if (!newMission.name) {
      alert('Please enter a mission name');
      return;
    }

    try {
      const result = await runMission(newMission.numDrones, newMission.meshSpacing);
      
      const mission = {
        id: Date.now(),
        name: newMission.name,
        numDrones: newMission.numDrones,
        meshSpacing: newMission.meshSpacing,
        status: 'completed',
        timestamp: new Date().toLocaleString(),
        result: result.status
      };

      const updatedMissions = [...missions, mission];
      setMissions(updatedMissions);
      localStorage.setItem('missions', JSON.stringify(updatedMissions));

      // Export report
      await exportReport(`mission_${mission.id}.json`);

      // Reset form
      setNewMission({ numDrones: 10, meshSpacing: 5, name: '' });
      
      alert('Mission completed and report exported!');
    } catch (error) {
      alert(`Mission failed: ${error.message}`);
    }
  };

  const handleExportMission = async (mission) => {
    try {
      await exportReport(`mission_${mission.id}.json`);
      alert('Report exported successfully!');
    } catch (error) {
      alert(`Export failed: ${error.message}`);
    }
  };

  const handleDeleteMission = (id) => {
    const updatedMissions = missions.filter(m => m.id !== id);
    setMissions(updatedMissions);
    localStorage.setItem('missions', JSON.stringify(updatedMissions));
    setSelectedMission(null);
  };

  return (
    <div className="missions-page">
      <div className="missions-header">
        <h1>Mission Management</h1>
        <p>Create, track, and export wildfire response missions</p>
      </div>

      <div className="missions-content">
        {/* Create New Mission */}
        <div className="create-mission-panel">
          <h2>Create New Mission</h2>
          
          <div className="form-group">
            <label htmlFor="mission-name">Mission Name:</label>
            <input
              id="mission-name"
              type="text"
              placeholder="Enter mission name (e.g., 'California Fire 2024')"
              value={newMission.name}
              onChange={(e) => setNewMission({ ...newMission, name: e.target.value })}
              disabled={loading}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="mission-drones">Number of Drones:</label>
              <input
                id="mission-drones"
                type="number"
                min="1"
                max="100"
                value={newMission.numDrones}
                onChange={(e) => setNewMission({ ...newMission, numDrones: parseInt(e.target.value) })}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="mission-spacing">Mesh Spacing (m):</label>
              <input
                id="mission-spacing"
                type="number"
                min="1"
                max="50"
                step="0.5"
                value={newMission.meshSpacing}
                onChange={(e) => setNewMission({ ...newMission, meshSpacing: parseFloat(e.target.value) })}
                disabled={loading}
              />
            </div>
          </div>

          <button
            className="btn btn-primary"
            onClick={handleStartMission}
            disabled={loading}
          >
            {loading ? '⏳ Starting Mission...' : '▶️ Start Mission'}
          </button>
        </div>

        {/* Missions List */}
        <div className="missions-list-panel">
          <h2>Mission History ({missions.length})</h2>
          
          {missions.length === 0 ? (
            <div className="empty-state">
              <p>📭 No missions yet. Create one to get started!</p>
            </div>
          ) : (
            <div className="missions-table">
              <div className="table-header">
                <div className="col-name">Name</div>
                <div className="col-drones">Drones</div>
                <div className="col-spacing">Spacing</div>
                <div className="col-status">Status</div>
                <div className="col-timestamp">Date/Time</div>
                <div className="col-actions">Actions</div>
              </div>

              {missions.map((mission) => (
                <div 
                  key={mission.id}
                  className={`table-row ${selectedMission?.id === mission.id ? 'selected' : ''}`}
                  onClick={() => setSelectedMission(mission)}
                >
                  <div className="col-name">{mission.name}</div>
                  <div className="col-drones">{mission.numDrones}</div>
                  <div className="col-spacing">{mission.meshSpacing}m</div>
                  <div className="col-status">
                    <span className={`status-badge status-${mission.status.toLowerCase()}`}>
                      {mission.status}
                    </span>
                  </div>
                  <div className="col-timestamp">{mission.timestamp}</div>
                  <div className="col-actions">
                    <button
                      className="btn btn-small btn-export"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleExportMission(mission);
                      }}
                      title="Export mission report"
                    >
                      📥 Export
                    </button>
                    <button
                      className="btn btn-small btn-delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteMission(mission.id);
                      }}
                      title="Delete mission"
                    >
                      🗑️ Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Mission Details */}
        {selectedMission && (
          <div className="mission-details-panel">
            <h2>Mission Details</h2>
            
            <div className="details-grid">
              <div className="detail-item">
                <span className="label">Mission Name:</span>
                <span className="value">{selectedMission.name}</span>
              </div>

              <div className="detail-item">
                <span className="label">Number of Drones:</span>
                <span className="value">{selectedMission.numDrones}</span>
              </div>

              <div className="detail-item">
                <span className="label">Mesh Spacing:</span>
                <span className="value">{selectedMission.meshSpacing}m</span>
              </div>

              <div className="detail-item">
                <span className="label">Status:</span>
                <span className={`value status-${selectedMission.status.toLowerCase()}`}>
                  {selectedMission.status}
                </span>
              </div>

              <div className="detail-item">
                <span className="label">Timestamp:</span>
                <span className="value">{selectedMission.timestamp}</span>
              </div>

              <div className="detail-item">
                <span className="label">Fire Observations:</span>
                <span className="value">{selectedMission.result?.fire_observations?.length || 0}</span>
              </div>

              <div className="detail-item">
                <span className="label">Mesh Nodes:</span>
                <span className="value">{selectedMission.result?.mesh_nodes || 0}</span>
              </div>

              <div className="detail-item">
                <span className="label">Optimization Gain:</span>
                <span className="value">{selectedMission.result?.optimization_improvement?.toFixed(1) || 0}%</span>
              </div>
            </div>

            <div className="detail-actions">
              <button
                className="btn btn-primary"
                onClick={() => handleExportMission(selectedMission)}
              >
                📥 Export Full Report
              </button>
              <button
                className="btn btn-danger"
                onClick={() => handleDeleteMission(selectedMission.id)}
              >
                🗑️ Delete Mission
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="missions-footer">
        <p>
          <strong>Note:</strong> All mission data is stored locally in your browser. 
          Use the export feature to backup important missions.
        </p>
      </div>
    </div>
  );
}

export default Missions;

/**
 * Missions Page - Mission planning and execution
 */

import React, { useEffect, useState } from 'react';
import { useStore } from '../store';
import './Missions.css';

const Missions: React.FC = () => {
  const { missions, drones, loadMissions, createMission, startMission, stopMission, loading } = useStore();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    droneId: 1,
    waypointCount: 5,
  });

  useEffect(() => {
    loadMissions();
    const interval = setInterval(loadMissions, 5000);
    return () => clearInterval(interval);
  }, [loadMissions]);

  const handleCreateMission = async () => {
    const waypoints = Array.from({ length: formData.waypointCount }, (_, i) => ({
      latitude: 35.0 + i * 0.001,
      longitude: -120.0 + i * 0.001,
      altitude: 50 + i * 10,
      sequence: i,
    }));

    await createMission(formData.droneId, waypoints);
    setShowCreateForm(false);
  };

  return (
    <div className="missions-page">
      <h1>Mission Planning & Execution</h1>

      <div className="missions-toolbar">
        <button onClick={() => setShowCreateForm(true)} className="btn-primary">
          + Create Mission
        </button>
      </div>

      {showCreateForm && (
        <div className="create-mission-form">
          <h3>Create New Mission</h3>
          <div className="form-group">
            <label>Select Drone:</label>
            <select
              value={formData.droneId}
              onChange={(e) => setFormData({ ...formData, droneId: Number(e.target.value) })}
            >
              {drones.map((drone) => (
                <option key={drone.drone_id} value={drone.drone_id}>
                  Drone {drone.drone_id}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Number of Waypoints:</label>
            <input
              type="number"
              min="1"
              max="100"
              value={formData.waypointCount}
              onChange={(e) => setFormData({ ...formData, waypointCount: Number(e.target.value) })}
            />
          </div>

          <div className="form-actions">
            <button onClick={handleCreateMission} className="btn-primary" disabled={loading}>
              Create
            </button>
            <button onClick={() => setShowCreateForm(false)} className="btn-secondary">
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="missions-list">
        {missions.length === 0 ? (
          <p className="no-missions">No missions yet. Create one to get started.</p>
        ) : (
          missions.map((mission) => (
            <div key={mission.mission_id} className="mission-card">
              <div className="mission-header">
                <h3>{mission.mission_id}</h3>
                <div className={`mission-status ${mission.is_active ? 'active' : 'inactive'}`}>
                  {mission.is_active ? '▶ Active' : '⏹ Inactive'}
                </div>
              </div>

              <div className="mission-details">
                <p><strong>Drone:</strong> {mission.drone_id}</p>
                <p><strong>Waypoints:</strong> {mission.waypoints.length}</p>
                <p><strong>Progress:</strong> {mission.current_waypoint}/{mission.waypoints.length} ({mission.progress.toFixed(0)}%)</p>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${mission.progress}%` }}></div>
                </div>
              </div>

              <div className="mission-actions">
                {!mission.is_active ? (
                  <button onClick={() => startMission(mission.mission_id)} className="btn-success" disabled={loading}>
                    Start
                  </button>
                ) : (
                  <button onClick={() => stopMission(mission.mission_id)} className="btn-danger" disabled={loading}>
                    Stop
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Missions;

/**
 * Drones Page - Drone management and control
 */

import React, { useEffect } from 'react';
import { useStore } from '../store';
import './Drones.css';

const Drones: React.FC = () => {
  const { drones, loadDrones, sendDroneCommand, loading } = useStore();

  useEffect(() => {
    loadDrones();
    const interval = setInterval(loadDrones, 5000);
    return () => clearInterval(interval);
  }, [loadDrones]);

  const handleCommand = (droneId: number, command: string) => {
    sendDroneCommand(droneId, command);
  };

  return (
    <div className="drones-page">
      <h1>Drone Fleet Management</h1>

      <div className="drones-grid">
        {drones.map((drone) => (
          <div key={drone.drone_id} className="drone-card">
            <div className="drone-header">
              <h3>Drone {drone.drone_id}</h3>
              <div className={`drone-status ${drone.armed ? 'armed' : 'disarmed'}`}>
                {drone.armed ? 'Armed' : 'Disarmed'}
              </div>
            </div>

            <div className="drone-info">
              <p><strong>Mode:</strong> {drone.mode}</p>
              <p><strong>Position:</strong> {drone.position ? `${drone.position[0].toFixed(4)}, ${drone.position[1].toFixed(4)}` : 'N/A'}</p>
              <p><strong>Altitude:</strong> {drone.position ? `${drone.position[2].toFixed(1)}m` : 'N/A'}</p>
              <p><strong>Battery:</strong> {drone.battery_level.toFixed(1)}%</p>
              <p><strong>Signal:</strong> {drone.signal_strength.toFixed(0)}%</p>
            </div>

            <div className="drone-controls">
              <button onClick={() => handleCommand(drone.drone_id, 'arm')} disabled={drone.armed || loading}>
                Arm
              </button>
              <button onClick={() => handleCommand(drone.drone_id, 'disarm')} disabled={!drone.armed || loading}>
                Disarm
              </button>
              <button onClick={() => handleCommand(drone.drone_id, 'takeoff')} disabled={!drone.armed || loading}>
                Takeoff
              </button>
              <button onClick={() => handleCommand(drone.drone_id, 'land')} disabled={drone.mode !== 'AUTO' || loading}>
                Land
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Drones;

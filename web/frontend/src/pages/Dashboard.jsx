import React, { useState, useEffect } from 'react';
import { useSystem } from '../context/SystemContext';
import { useSocket } from '../context/SocketContext';
import StatusCard from '../components/StatusCard';
import MissionPanel from '../components/MissionPanel';
import DataPanel from '../components/DataPanel';
import './Dashboard.css';

function Dashboard() {
  const { 
    getSystemStatus, 
    loadFireData, 
    generateMesh, 
    allocateDrones,
    optimizePaths,
    analyzeRisk,
    runDetection,
    generateRoutes,
    runMission,
    loading,
    error 
  } = useSystem();
  
  const { systemStatus, emit } = useSocket();
  const [missionRunning, setMissionRunning] = useState(false);
  const [missionProgress, setMissionProgress] = useState(0);
  const [numDrones, setNumDrones] = useState(10);
  const [meshSpacing, setMeshSpacing] = useState(5);

  useEffect(() => {
    // Load initial status on mount
    loadInitialStatus();
  }, []);

  const loadInitialStatus = async () => {
    await getSystemStatus();
  };

  const handleLoadFireData = async () => {
    try {
      setMissionProgress(10);
      await loadFireData('simulation', {
        center_lat: 35.0,
        center_lon: -120.0,
        num_observations: 50,
        boundary_radius: 2.0
      });
      setMissionProgress(20);
    } catch (err) {
      console.error('Failed to load fire data:', err);
    }
  };

  const handleGenerateMesh = async () => {
    try {
      setMissionProgress(30);
      await generateMesh(meshSpacing, 50);
      setMissionProgress(40);
    } catch (err) {
      console.error('Failed to generate mesh:', err);
    }
  };

  const handleAllocateDrones = async () => {
    try {
      setMissionProgress(50);
      await allocateDrones(numDrones);
      setMissionProgress(60);
    } catch (err) {
      console.error('Failed to allocate drones:', err);
    }
  };

  const handleOptimizePaths = async () => {
    try {
      setMissionProgress(70);
      await optimizePaths(true);
      setMissionProgress(80);
    } catch (err) {
      console.error('Failed to optimize paths:', err);
    }
  };

  const handleAnalyzeRisk = async () => {
    try {
      setMissionProgress(85);
      await analyzeRisk();
      setMissionProgress(90);
    } catch (err) {
      console.error('Failed to analyze risk:', err);
    }
  };

  const handleRunDetection = async () => {
    try {
      await runDetection();
      setMissionProgress(95);
    } catch (err) {
      console.error('Failed to run detection:', err);
    }
  };

  const handleRunMission = async () => {
    try {
      setMissionRunning(true);
      setMissionProgress(0);
      
      // Run complete mission
      await runMission(numDrones, meshSpacing);
      
      setMissionProgress(100);
      setTimeout(() => {
        setMissionRunning(false);
        setMissionProgress(0);
      }, 2000);
    } catch (err) {
      console.error('Failed to run mission:', err);
      setMissionRunning(false);
    }
  };

  const handleRequestVisualization = () => {
    emit('request_visualization_data');
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Wildfire Response System Dashboard</h1>
        <p>Real-time drone coordination and wildfire boundary monitoring</p>
      </div>

      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {missionRunning && (
        <div className="mission-progress-bar">
          <div className="progress">
            <div 
              className="progress-fill" 
              style={{ width: `${missionProgress}%` }}
            ></div>
          </div>
          <span className="progress-text">Mission Progress: {missionProgress}%</span>
        </div>
      )}

      <div className="dashboard-grid">
        {/* Status Cards */}
        <div className="status-section">
          <h2>System Status</h2>
          <div className="status-cards">
            <StatusCard 
              title="System Health" 
              value={systemStatus ? 'Active' : 'Initializing'} 
              color="green"
              icon="✓"
            />
            <StatusCard 
              title="Fire Observations" 
              value={systemStatus?.fire_observations?.length || 0} 
              color="orange"
              icon="🔥"
            />
            <StatusCard 
              title="Active Drones" 
              value={systemStatus?.num_drones || 0} 
              color="blue"
              icon="🚁"
            />
            <StatusCard 
              title="Mesh Nodes" 
              value={systemStatus?.mesh_nodes || 0} 
              color="purple"
              icon="📍"
            />
          </div>
        </div>

        {/* Mission Control Panel */}
        <MissionPanel
          numDrones={numDrones}
          meshSpacing={meshSpacing}
          onNumDronesChange={setNumDrones}
          onMeshSpacingChange={setMeshSpacing}
          onLoadFireData={handleLoadFireData}
          onGenerateMesh={handleGenerateMesh}
          onAllocateDrones={handleAllocateDrones}
          onOptimizePaths={handleOptimizePaths}
          onAnalyzeRisk={handleAnalyzeRisk}
          onRunDetection={handleRunDetection}
          onRunMission={handleRunMission}
          onRequestVisualization={handleRequestVisualization}
          loading={loading}
          missionRunning={missionRunning}
        />

        {/* Data Summary */}
        <DataPanel systemStatus={systemStatus} />
      </div>

      <div className="dashboard-footer">
        <p>
          <strong>Safety Notice:</strong> All drone paths and firefighter routes are recommendations only. 
          Qualified personnel must review and approve all recommendations before deployment.
        </p>
      </div>
    </div>
  );
}

export default Dashboard;

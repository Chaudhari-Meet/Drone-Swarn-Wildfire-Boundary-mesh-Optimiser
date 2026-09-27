/**
 * Main Application Component
 * Routes and layout for the Wildfire Drone System
 */

import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useStore } from './store';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Drones from './pages/Drones';
import Missions from './pages/Missions';
import Maps from './pages/Maps';
import Settings from './pages/Settings';
import './App.css';

const App: React.FC = () => {
  const { initializeSystem } = useStore();

  useEffect(() => {
    // Initialize system on app load
    initializeSystem('simulation', 5);
  }, [initializeSystem]);

  return (
    <Router>
      <div className="app">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/drones" element={<Drones />} />
            <Route path="/missions" element={<Missions />} />
            <Route path="/map" element={<Maps />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default App;

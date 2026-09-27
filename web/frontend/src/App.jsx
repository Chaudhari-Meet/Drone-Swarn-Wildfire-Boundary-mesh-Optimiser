import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import Navigation from './components/Navigation';
import Dashboard from './pages/Dashboard';
import MapView from './pages/MapView';
import Missions from './pages/Missions';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import Login from './pages/Login';
import { SocketProvider } from './context/SocketContext';
import { SystemProvider } from './context/SystemContext';

function App() {
  const [systemReady, setSystemReady] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [authToken, setAuthToken] = useState(null);

  useEffect(() => {
    // Check if already logged in
    const token = localStorage.getItem('authToken');
    if (token) {
      setAuthToken(token);
      setAuthenticated(true);
    }

    // Check backend health
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      const response = await fetch('/api/health');
      if (response.ok) {
        setSystemReady(true);
      }
    } catch (error) {
      console.error('Backend not ready:', error);
      setSystemReady(false);
    }
  };

  const handleLoginSuccess = (token) => {
    setAuthToken(token);
    setAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    setAuthToken(null);
    setAuthenticated(false);
  };

  return (
    <Router>
      <div className="app">
        {!systemReady && (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Connecting to Wildfire System...</p>
          </div>
        )}

        {systemReady && !authenticated && (
          <Login onLoginSuccess={handleLoginSuccess} />
        )}

        {systemReady && authenticated && (
          <SystemProvider token={authToken}>
            <SocketProvider token={authToken}>
              <>
                <Navigation onLogout={handleLogout} />
                <main className="main-content">
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/map" element={<MapView />} />
                    <Route path="/missions" element={<Missions />} />
                    <Route path="/analytics" element={<Analytics />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="*" element={<Navigate to="/" />} />
                  </Routes>
                </main>
              </>
            </SocketProvider>
          </SystemProvider>
        )}
      </div>
    </Router>
  );
}

export default App;

import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useSocket } from '../context/SocketContext';
import './Navigation.css';

function Navigation({ onLogout }) {
  const location = useLocation();
  const { connected } = useSocket();
  const [user, setUser] = useState(null);
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, []);

  const isActive = (path) => location.pathname === path;

  const handleLogout = () => {
    setShowUserMenu(false);
    onLogout();
  };

  const getRoleColor = (role) => {
    switch(role) {
      case 'admin': return '#dc2626';
      case 'operator': return '#2563eb';
      case 'viewer': return '#059669';
      default: return '#666';
    }
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          <span className="logo-icon">🚁</span>
          Wildfire Drone System
        </Link>

        <ul className="nav-menu">
          <li className="nav-item">
            <Link
              to="/"
              className={`nav-link ${isActive('/') ? 'active' : ''}`}
            >
              Dashboard
            </Link>
          </li>
          <li className="nav-item">
            <Link
              to="/map"
              className={`nav-link ${isActive('/map') ? 'active' : ''}`}
            >
              Map View
            </Link>
          </li>
          <li className="nav-item">
            <Link
              to="/missions"
              className={`nav-link ${isActive('/missions') ? 'active' : ''}`}
            >
              Missions
            </Link>
          </li>
          <li className="nav-item">
            <Link
              to="/analytics"
              className={`nav-link ${isActive('/analytics') ? 'active' : ''}`}
            >
              Analytics
            </Link>
          </li>
          <li className="nav-item">
            <Link
              to="/settings"
              className={`nav-link ${isActive('/settings') ? 'active' : ''}`}
            >
              Settings
            </Link>
          </li>
        </ul>

        <div className="navbar-right">
          <div className="navbar-status">
            <div className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}></div>
            <span className="status-text">
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          {user && (
            <div className="user-menu-container">
              <button 
                className="user-button"
                onClick={() => setShowUserMenu(!showUserMenu)}
              >
                <span className="user-icon">👤</span>
                <span className="user-name">{user.username}</span>
                <span className="user-role" style={{ backgroundColor: getRoleColor(user.role) }}>
                  {user.role.toUpperCase()}
                </span>
              </button>

              {showUserMenu && (
                <div className="user-menu">
                  <div className="menu-header">
                    <strong>{user.username}</strong>
                    <p>{user.email}</p>
                  </div>
                  <div className="menu-divider"></div>
                  <Link to="/settings" className="menu-item" onClick={() => setShowUserMenu(false)}>
                    ⚙️ Settings
                  </Link>
                  <button className="menu-item logout" onClick={handleLogout}>
                    🚪 Logout
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navigation;

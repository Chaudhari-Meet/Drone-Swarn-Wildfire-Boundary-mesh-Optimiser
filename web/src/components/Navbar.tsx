/**
 * Navigation Bar Component
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useStore } from '../store';
import './Navbar.css';

const Navbar: React.FC = () => {
  const location = useLocation();
  const { toggleSidebar, sidebarOpen } = useStore();

  const isActive = (path: string) => location.pathname === path ? 'active' : '';

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <button className="hamburger" onClick={toggleSidebar}>
          ☰
        </button>
        <h1>🚁 Wildfire Drone System</h1>
      </div>

      <ul className="navbar-menu">
        <li>
          <Link to="/" className={`nav-link ${isActive('/')}`}>
            Dashboard
          </Link>
        </li>
        <li>
          <Link to="/drones" className={`nav-link ${isActive('/drones')}`}>
            Drones
          </Link>
        </li>
        <li>
          <Link to="/missions" className={`nav-link ${isActive('/missions')}`}>
            Missions
          </Link>
        </li>
        <li>
          <Link to="/map" className={`nav-link ${isActive('/map')}`}>
            Map
          </Link>
        </li>
        <li>
          <Link to="/settings" className={`nav-link ${isActive('/settings')}`}>
            Settings
          </Link>
        </li>
      </ul>

      <div className="navbar-status">
        <span className="status-indicator">● Online</span>
      </div>
    </nav>
  );
};

export default Navbar;

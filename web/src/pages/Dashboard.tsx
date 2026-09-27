/**
 * Dashboard Page - Real-time system overview
 */

import React, { useEffect, useState } from 'react';
import { useStore } from '../store';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const { dashboardData, loadDashboard, loading } = useStore();
  const [batteryTrend, setBatteryTrend] = useState<any[]>([]);

  useEffect(() => {
    // Load dashboard data
    loadDashboard();

    // Refresh every 5 seconds
    const interval = setInterval(loadDashboard, 5000);
    return () => clearInterval(interval);
  }, [loadDashboard]);

  // Simulate battery trend data
  useEffect(() => {
    if (dashboardData) {
      setBatteryTrend((prev) => [
        ...prev.slice(-19),
        {
          time: new Date().toLocaleTimeString(),
          battery: dashboardData.fleet.avg_battery,
        },
      ]);
    }
  }, [dashboardData]);

  if (loading) {
    return <div className="dashboard loading">Loading...</div>;
  }

  if (!dashboardData) {
    return <div className="dashboard">No data available</div>;
  }

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c'];

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>

      {/* Key Metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <h3>Fire Observations</h3>
          <p className="metric-value">{dashboardData.fire.observations}</p>
          <p className="metric-unit">observations</p>
        </div>

        <div className="metric-card">
          <h3>Fire Area</h3>
          <p className="metric-value">{dashboardData.fire.area_hectares.toFixed(0)}</p>
          <p className="metric-unit">hectares</p>
        </div>

        <div className="metric-card">
          <h3>Active Drones</h3>
          <p className="metric-value">{dashboardData.fleet.armed_drones}/{dashboardData.fleet.total_drones}</p>
          <p className="metric-unit">armed</p>
        </div>

        <div className="metric-card">
          <h3>Average Battery</h3>
          <p className="metric-value">{dashboardData.fleet.avg_battery.toFixed(1)}%</p>
          <p className="metric-unit">charge</p>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        {/* Battery Trend */}
        <div className="chart-container">
          <h3>Battery Trend</h3>
          {batteryTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={batteryTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="battery"
                  stroke="#8884d8"
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p>No data yet</p>
          )}
        </div>

        {/* Fleet Status */}
        <div className="chart-container">
          <h3>Fleet Status</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={[
                  { name: 'Armed', value: dashboardData.fleet.armed_drones },
                  { name: 'Disarmed', value: dashboardData.fleet.total_drones - dashboardData.fleet.armed_drones },
                ]}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {['#82ca9d', '#ffc658'].map((color, index) => (
                  <Cell key={`cell-${index}`} fill={color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Fire Zone Coverage */}
        <div className="chart-container">
          <h3>Fire Coverage</h3>
          <div className="stat-bars">
            <div className="stat-bar">
              <label>Boundary Points</label>
              <div className="bar-fill" style={{ width: `${Math.min(dashboardData.fire.boundary_points * 5, 100)}%` }}>
                {dashboardData.fire.boundary_points}
              </div>
            </div>
            <div className="stat-bar">
              <label>Total Area (hectares)</label>
              <div className="bar-fill" style={{ width: `${Math.min(dashboardData.fire.area_hectares / 1000 * 100, 100)}%` }}>
                {dashboardData.fire.area_hectares.toFixed(0)}
              </div>
            </div>
          </div>
        </div>

        {/* System Status */}
        <div className="chart-container">
          <h3>System Status</h3>
          <div className="status-list">
            <div className="status-item">
              <span className="status-label">Mode:</span>
              <span className="status-value">{dashboardData.system.mode}</span>
            </div>
            <div className="status-item">
              <span className="status-label">Drones:</span>
              <span className="status-value">{dashboardData.fleet.total_drones}</span>
            </div>
            <div className="status-item">
              <span className="status-label">Mesh Nodes:</span>
              <span className="status-value">{dashboardData.system.mesh_nodes || 0}</span>
            </div>
            <div className="status-item">
              <span className="status-label">Last Update:</span>
              <span className="status-value">{new Date().toLocaleTimeString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts */}
      <div className="alerts-section">
        <h3>System Alerts</h3>
        <div className="alerts-list">
          {dashboardData.fleet.avg_battery < 30 && (
            <div className="alert alert-warning">
              ⚠ Low battery warning: {dashboardData.fleet.avg_battery.toFixed(1)}%
            </div>
          )}
          {dashboardData.fire.observations > 50 && (
            <div className="alert alert-critical">
              🔥 High number of fire observations: {dashboardData.fire.observations}
            </div>
          )}
          <div className="alert alert-info">
            ℹ System running in {dashboardData.system.mode} mode
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

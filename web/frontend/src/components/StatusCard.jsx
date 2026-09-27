import React from 'react';
import './StatusCard.css';

function StatusCard({ title, value, color, icon, details }) {
  return (
    <div className={`status-card status-${color}`}>
      <div className="status-icon">{icon}</div>
      <div className="status-content">
        <div className="status-title">{title}</div>
        <div className="status-value">{value}</div>
        {details && <div className="status-details">{details}</div>}
      </div>
    </div>
  );
}

export default StatusCard;

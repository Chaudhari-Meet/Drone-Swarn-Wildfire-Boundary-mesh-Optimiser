import React, { useEffect, useState } from 'react';
import { useSystem } from '../context/SystemContext';
import { useSocket } from '../context/SocketContext';
import './Analytics.css';

function Analytics() {
  const { getCurrentReport } = useSystem();
  const { systemStatus } = useSocket();
  const [report, setReport] = useState(null);

  useEffect(() => {
    loadReport();
  }, [systemStatus]);

  const loadReport = async () => {
    try {
      const data = await getCurrentReport();
      setReport(data);
    } catch (error) {
      console.error('Failed to load report:', error);
    }
  };

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <h1>Analytics & Performance</h1>
        <p>Detailed system performance metrics and analysis</p>
      </div>

      <div className="analytics-grid">
        {/* Performance Metrics */}
        <div className="analytics-card">
          <div className="card-header">
            <h3>Performance Metrics</h3>
            <span className="card-icon">📊</span>
          </div>
          <div className="card-content">
            <div className="metric">
              <span className="metric-label">Total Execution Time:</span>
              <span className="metric-value">{report?.execution_time?.toFixed(2)}s</span>
            </div>
            <div className="metric">
              <span className="metric-label">Path Optimization Improvement:</span>
              <span className="metric-value">{report?.optimization_improvement?.toFixed(1)}%</span>
            </div>
            <div className="metric">
              <span className="metric-label">Path Quality Score:</span>
              <span className="metric-value">{report?.path_quality?.toFixed(1)}%</span>
            </div>
            <div className="metric">
              <span className="metric-label">Coverage Percentage:</span>
              <span className="metric-value">{report?.coverage_percentage?.toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Algorithm Comparison */}
        <div className="analytics-card">
          <div className="card-header">
            <h3>Algorithm Comparison</h3>
            <span className="card-icon">⚖️</span>
          </div>
          <div className="card-content">
            <div className="comparison">
              <div className="algo-item">
                <span className="algo-name">Baseline (Sequential)</span>
                <div className="algo-bar">
                  <div className="bar-fill" style={{ width: '100%' }}></div>
                </div>
                <span className="algo-value">100%</span>
              </div>
              <div className="algo-item">
                <span className="algo-name">Nearest Neighbor</span>
                <div className="algo-bar">
                  <div className="bar-fill" style={{ width: '65%' }}></div>
                </div>
                <span className="algo-value">65%</span>
              </div>
              <div className="algo-item">
                <span className="algo-name">2-opt Optimized</span>
                <div className="algo-bar">
                  <div className="bar-fill" style={{ width: '60%' }}></div>
                </div>
                <span className="algo-value">60%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Drone Statistics */}
        <div className="analytics-card">
          <div className="card-header">
            <h3>Drone Fleet Statistics</h3>
            <span className="card-icon">🚁</span>
          </div>
          <div className="card-content">
            <div className="stat-box">
              <div className="stat-title">Total Drones</div>
              <div className="stat-value">{report?.num_drones || 0}</div>
            </div>
            <div className="stat-box">
              <div className="stat-title">Average Battery</div>
              <div className="stat-value">{report?.average_battery?.toFixed(0)}%</div>
            </div>
            <div className="stat-box">
              <div className="stat-title">Total Distance</div>
              <div className="stat-value">{(report?.total_path_distance / 1000).toFixed(1)}km</div>
            </div>
            <div className="stat-box">
              <div className="stat-title">Load Imbalance</div>
              <div className="stat-value">{report?.load_imbalance?.toFixed(1)}%</div>
            </div>
          </div>
        </div>

        {/* Risk Analysis */}
        <div className="analytics-card">
          <div className="card-header">
            <h3>Risk Zone Distribution</h3>
            <span className="card-icon">🎯</span>
          </div>
          <div className="card-content">
            <div className="risk-breakdown">
              <div className="risk-item risk-green">
                <span className="risk-label">Green Safe</span>
                <span className="risk-count">{report?.risk_zones?.GREEN || 0}</span>
              </div>
              <div className="risk-item risk-yellow">
                <span className="risk-label">Yellow Caution</span>
                <span className="risk-count">{report?.risk_zones?.YELLOW || 0}</span>
              </div>
              <div className="risk-item risk-red">
                <span className="risk-label">Red Danger</span>
                <span className="risk-count">{report?.risk_zones?.RED || 0}</span>
              </div>
              <div className="risk-item risk-critical">
                <span className="risk-label">Critical</span>
                <span className="risk-count">{report?.risk_zones?.CRITICAL || 0}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Detection Summary */}
        <div className="analytics-card">
          <div className="card-header">
            <h3>Object Detection Summary</h3>
            <span className="card-icon">🔍</span>
          </div>
          <div className="card-content">
            <div className="detection-stats">
              <div className="detection-item">
                <span className="detection-type">🐾 Animals</span>
                <span className="detection-count">{report?.animals_detected || 0}</span>
              </div>
              <div className="detection-item">
                <span className="detection-type">👤 Persons</span>
                <span className="detection-count">{report?.persons_detected || 0}</span>
              </div>
              <div className="detection-item">
                <span className="detection-type">✓ High Confidence</span>
                <span className="detection-count">{report?.high_confidence_detections || 0}</span>
              </div>
              <div className="detection-item">
                <span className="detection-type">? Need Verification</span>
                <span className="detection-count">{report?.num_detections - report?.high_confidence_detections || 0}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Fire Monitoring */}
        <div className="analytics-card">
          <div className="card-header">
            <h3>Fire Monitoring Data</h3>
            <span className="card-icon">🔥</span>
          </div>
          <div className="card-content">
            <div className="fire-stats">
              <div className="stat-box">
                <div className="stat-title">Fire Observations</div>
                <div className="stat-value">{report?.fire_observations?.length || 0}</div>
              </div>
              <div className="stat-box">
                <div className="stat-title">Affected Area</div>
                <div className="stat-value">{(report?.fire_area / 10000).toFixed(2)} ha</div>
              </div>
              <div className="stat-box">
                <div className="stat-title">Boundary Points</div>
                <div className="stat-value">{report?.boundary_points || 0}</div>
              </div>
              <div className="stat-box">
                <div className="stat-title">Confidence Level</div>
                <div className="stat-value">{report?.boundary_confidence ? `${(report.boundary_confidence * 100).toFixed(1)}%` : 'N/A'}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Recommendations */}
        <div className="analytics-card full-width">
          <div className="card-header">
            <h3>System Recommendations</h3>
            <span className="card-icon">💡</span>
          </div>
          <div className="card-content recommendations">
            <div className="recommendation-item">
              <span className="rec-icon">✓</span>
              <span className="rec-text">Current drone allocation provides optimal coverage with minimal redundancy</span>
            </div>
            <div className="recommendation-item">
              <span className="rec-icon">✓</span>
              <span className="rec-text">Path optimization achieved {report?.optimization_improvement?.toFixed(1)}% improvement over baseline</span>
            </div>
            <div className="recommendation-item">
              <span className="rec-icon">ℹ</span>
              <span className="rec-text">Consider deploying additional drones for higher mesh density coverage</span>
            </div>
            <div className="recommendation-item">
              <span className="rec-icon">⚠</span>
              <span className="rec-text">Monitor high-risk zones for real-time threat assessment</span>
            </div>
          </div>
        </div>
      </div>

      <div className="analytics-footer">
        <p>
          <strong>Data Accuracy:</strong> All metrics are based on simulation data. 
          Actual deployment requires real satellite and drone telemetry integration.
        </p>
      </div>
    </div>
  );
}

export default Analytics;

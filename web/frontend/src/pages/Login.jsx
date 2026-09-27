import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Login.css';

function Login({ onLoginSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [demoMode, setDemoMode] = useState(false);

  useEffect(() => {
    // Check if already logged in
    const token = localStorage.getItem('authToken');
    if (token) {
      onLoginSuccess(token);
    }
  }, [onLoginSuccess]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/auth/login', {
        username,
        password
      });

      if (response.data.success) {
        const token = response.data.token;
        localStorage.setItem('authToken', token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        onLoginSuccess(token);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Please try again.');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async (role) => {
    const demoUsers = {
      admin: { username: 'admin', password: 'admin123' },
      operator: { username: 'operator', password: 'operator123' },
      viewer: { username: 'viewer', password: 'viewer123' }
    };

    const user = demoUsers[role];
    setUsername(user.username);
    setPassword(user.password);

    // Perform login immediately with the credentials
    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/auth/login', {
        username: user.username,
        password: user.password
      });

      if (response.data.success) {
        const token = response.data.token;
        localStorage.setItem('authToken', token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        onLoginSuccess(token);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Please try again.');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        {/* Left Side - Branding */}
        <div className="login-branding">
          <div className="branding-content">
            <div className="logo">🚁</div>
            <h1>Wildfire Drone System</h1>
            <p>Advanced Drone Swarm Coordination & Response</p>

            <div className="features-list">
              <div className="feature">
                <span className="feature-icon">🔥</span>
                <span>Fire Boundary Detection</span>
              </div>
              <div className="feature">
                <span className="feature-icon">🔲</span>
                <span>Mesh Coverage Planning</span>
              </div>
              <div className="feature">
                <span className="feature-icon">🚁</span>
                <span>Drone Path Optimization</span>
              </div>
              <div className="feature">
                <span className="feature-icon">⚠️</span>
                <span>Risk Analysis</span>
              </div>
              <div className="feature">
                <span className="feature-icon">🔍</span>
                <span>Object Detection</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Login Form */}
        <div className="login-form-container">
          <div className="login-form">
            <h2>Sign In</h2>
            <p className="login-subtitle">Access your Wildfire System dashboard</p>

            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleLogin} autoComplete="off">
              <div className="form-group">
                <label htmlFor="username">Username</label>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your username"
                  disabled={loading}
                  autoFocus
                  autoComplete="off"
                />
              </div>

              <div className="form-group">
                <label htmlFor="password">Password</label>
                <div className="password-input-group">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    disabled={loading}
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    className="toggle-password"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={loading}
                    title={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? '🙈' : '👁️'}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="login-button"
                disabled={loading || !username || !password}
              >
                {loading ? '⏳ Signing In...' : '✓ Sign In'}
              </button>
            </form>

            {/* Demo Credentials */}
            <div className="demo-section">
              <p className="demo-title">Demo Credentials</p>
              
              <div className="demo-buttons">
                <button
                  className="demo-button admin"
                  onClick={() => handleDemoLogin('admin')}
                  disabled={loading}
                  title="Full system access"
                >
                  👑 Admin
                </button>
                <button
                  className="demo-button operator"
                  onClick={() => handleDemoLogin('operator')}
                  disabled={loading}
                  title="Can run missions"
                >
                  🎮 Operator
                </button>
                <button
                  className="demo-button viewer"
                  onClick={() => handleDemoLogin('viewer')}
                  disabled={loading}
                  title="Read-only access"
                >
                  👁️ Viewer
                </button>
              </div>

              <p className="demo-notice">
                Click any role above to auto-fill demo credentials
              </p>
            </div>

            {/* Info Section */}
            <div className="login-info">
              <h4>ℹ️ System Information</h4>
              <p>
                <strong>Status:</strong> Production Ready
              </p>
              <p>
                <strong>Mode:</strong> Simulation (Demo Data)
              </p>
              <p>
                <strong>Version:</strong> 1.0.0
              </p>
            </div>

            {/* Safety Notice */}
            <div className="safety-notice">
              <p>
                <strong>⚠️ Academic System Notice:</strong> This is an academic 
                simulation system. All data is simulated and for demonstration only.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;

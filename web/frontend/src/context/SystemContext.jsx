import React, { createContext, useContext, useState, useCallback } from 'react';
import axios from 'axios';

const SystemContext = createContext();

const API_BASE_URL = '/api';

export const SystemProvider = ({ children }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [config, setConfig] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);

  // Fetch system configuration
  const getConfig = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/config`);
      setConfig(response.data);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.message);
      console.error('Error fetching config:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Get system status
  const getSystemStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/system/status`);
      setSystemStatus(response.data);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.message);
      console.error('Error fetching status:', err);
    }
  }, []);

  // Load fire data
  const loadFireData = useCallback(async (source, params) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/data/load`, {
        source,
        params
      });
      setSystemStatus(response.data.status);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.error || err.message);
      console.error('Error loading fire data:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get current fire data
  const getCurrentData = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/data/current`);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.message);
      console.error('Error fetching current data:', err);
    }
  }, []);

  // Generate mesh
  const generateMesh = useCallback(async (spacing, altitude) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/mesh/generate`, {
        spacing,
        altitude
      });
      setSystemStatus(response.data.status);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.error || err.message);
      console.error('Error generating mesh:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get current mesh
  const getCurrentMesh = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/mesh/current`);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.message);
      console.error('Error fetching mesh:', err);
    }
  }, []);

  // Allocate drones
  const allocateDrones = useCallback(async (numDrones) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/drones/allocate`, {
        num_drones: numDrones
      });
      setSystemStatus(response.data.status);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.error || err.message);
      console.error('Error allocating drones:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // List drones
  const listDrones = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/drones/list`);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.message);
      console.error('Error listing drones:', err);
    }
  }, []);

  // Optimize paths
  const optimizePaths = useCallback(async (useTwoOpt) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/paths/optimize`, {
        use_two_opt: useTwoOpt
      });
      setSystemStatus(response.data.status);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.error || err.message);
      console.error('Error optimizing paths:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get current paths
  const getCurrentPaths = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/paths/current`);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.message);
      console.error('Error fetching paths:', err);
    }
  }, []);

  // Analyze risk
  const analyzeRisk = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/risk/analyze`);
      setSystemStatus(response.data.status);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.error || err.message);
      console.error('Error analyzing risk:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get risk zones
  const getRiskZones = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/risk/zones`);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.message);
      console.error('Error fetching risk zones:', err);
    }
  }, []);

  // Run detection
  const runDetection = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/detection/run`);
      setSystemStatus(response.data.status);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.error || err.message);
      console.error('Error running detection:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get detection results
  const getDetectionResults = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/detection/results`);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.message);
      console.error('Error fetching detections:', err);
    }
  }, []);

  // Generate firefighter routes
  const generateRoutes = useCallback(async (startPoint, endPoint) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/routes/generate`, {
        start_point: startPoint,
        end_point: endPoint
      });
      setSystemStatus(response.data.status);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.error || err.message);
      console.error('Error generating routes:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get routes
  const getRoutes = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/routes/list`);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.message);
      console.error('Error fetching routes:', err);
    }
  }, []);

  // Run full mission
  const runMission = useCallback(async (numDrones, meshSpacing) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/mission/run`, {
        num_drones: numDrones,
        mesh_spacing: meshSpacing
      });
      setSystemStatus(response.data.status);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.error || err.message);
      console.error('Error running mission:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Export report
  const exportReport = useCallback(async (filename) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/report/export`, {
        filename
      });
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.error || err.message);
      console.error('Error exporting report:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get current report
  const getCurrentReport = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/report/current`);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.message);
      console.error('Error fetching report:', err);
    }
  }, []);

  const value = {
    loading,
    error,
    config,
    systemStatus,
    getConfig,
    getSystemStatus,
    loadFireData,
    getCurrentData,
    generateMesh,
    getCurrentMesh,
    allocateDrones,
    listDrones,
    optimizePaths,
    getCurrentPaths,
    analyzeRisk,
    getRiskZones,
    runDetection,
    getDetectionResults,
    generateRoutes,
    getRoutes,
    runMission,
    exportReport,
    getCurrentReport
  };

  return (
    <SystemContext.Provider value={value}>
      {children}
    </SystemContext.Provider>
  );
};

export const useSystem = () => {
  const context = useContext(SystemContext);
  if (!context) {
    throw new Error('useSystem must be used within SystemProvider');
  }
  return context;
};

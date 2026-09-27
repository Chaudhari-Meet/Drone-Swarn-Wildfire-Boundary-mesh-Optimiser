import React, { createContext, useContext, useEffect, useState } from 'react';
import io from 'socket.io-client';

const SocketContext = createContext();

export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);
  const [visualizationData, setVisualizationData] = useState(null);

  useEffect(() => {
    const newSocket = io(window.location.origin, {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5
    });

    newSocket.on('connect', () => {
      console.log('Connected to WebSocket');
      setConnected(true);
    });

    newSocket.on('disconnect', () => {
      console.log('Disconnected from WebSocket');
      setConnected(false);
    });

    newSocket.on('status_update', (data) => {
      setSystemStatus(data);
    });

    newSocket.on('visualization_data', (data) => {
      setVisualizationData(data);
    });

    newSocket.on('data_loaded', (data) => {
      console.log('Fire data loaded', data);
      setSystemStatus(data.status);
    });

    newSocket.on('mesh_generated', (data) => {
      console.log('Mesh generated', data);
      setSystemStatus(data.status);
    });

    newSocket.on('drones_allocated', (data) => {
      console.log('Drones allocated', data);
      setSystemStatus(data.status);
    });

    newSocket.on('paths_optimized', (data) => {
      console.log('Paths optimized', data);
      setSystemStatus(data.status);
    });

    newSocket.on('risk_analyzed', (data) => {
      console.log('Risk analyzed', data);
      setSystemStatus(data.status);
    });

    newSocket.on('detection_complete', (data) => {
      console.log('Detection complete', data);
      setSystemStatus(data.status);
    });

    newSocket.on('routes_generated', (data) => {
      console.log('Routes generated', data);
      setSystemStatus(data.status);
    });

    newSocket.on('mission_complete', (data) => {
      console.log('Mission complete', data);
      setSystemStatus(data.status);
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, []);

  const emit = (event, data) => {
    if (socket) {
      socket.emit(event, data);
    }
  };

  return (
    <SocketContext.Provider value={{ socket, connected, systemStatus, visualizationData, emit }}>
      {children}
    </SocketContext.Provider>
  );
};

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within SocketProvider');
  }
  return context;
};

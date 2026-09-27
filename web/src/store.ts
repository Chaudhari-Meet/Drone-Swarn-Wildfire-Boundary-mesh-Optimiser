/**
 * Zustand Store - State Management
 * Centralized state for drones, missions, fire data, and UI
 */

import create from 'zustand';
import api from './api';

// Types
export interface DroneStatus {
  drone_id: number;
  armed: boolean;
  mode: string;
  position: [number, number, number] | null;
  battery_level: number;
  signal_strength: number;
  last_update: string;
}

export interface MissionWaypoint {
  latitude: number;
  longitude: number;
  altitude: number;
  sequence: number;
}

export interface Mission {
  mission_id: string;
  drone_id: number;
  waypoints: MissionWaypoint[];
  current_waypoint: number;
  is_active: boolean;
  progress: number;
}

export interface FireObservation {
  id: number;
  latitude: number;
  longitude: number;
  confidence: number;
  temperature?: number;
  source: string;
}

export interface DashboardData {
  fire: {
    observations: number;
    area_hectares: number;
    boundary_points: number;
  };
  fleet: {
    total_drones: number;
    armed_drones: number;
    flying_drones: number;
    avg_battery: number;
  };
  system: any;
}

interface Store {
  // System state
  initialized: boolean;
  mode: string;
  loading: boolean;
  error: string | null;

  // Drones
  drones: DroneStatus[];
  selectedDrone: DroneStatus | null;

  // Missions
  missions: Mission[];
  selectedMission: Mission | null;

  // Fire data
  fireObservations: FireObservation[];
  fireBoundary: [number, number][];

  // Dashboard
  dashboardData: DashboardData | null;

  // UI
  activeTab: string;
  sidebarOpen: boolean;

  // Actions
  initializeSystem: (mode: string, numDrones: number) => Promise<void>;
  loadDashboard: () => Promise<void>;
  loadDrones: () => Promise<void>;
  loadMissions: () => Promise<void>;
  loadFireData: () => Promise<void>;
  sendDroneCommand: (droneId: number, command: string, parameters?: any) => Promise<void>;
  createMission: (droneId: number, waypoints: MissionWaypoint[]) => Promise<void>;
  startMission: (missionId: string) => Promise<void>;
  stopMission: (missionId: string) => Promise<void>;
  selectDrone: (drone: DroneStatus) => void;
  selectMission: (mission: Mission) => void;
  setActiveTab: (tab: string) => void;
  toggleSidebar: () => void;
  setError: (error: string | null) => void;
}

export const useStore = create<Store>((set, get) => ({
  // Initial state
  initialized: false,
  mode: 'simulation',
  loading: false,
  error: null,
  drones: [],
  selectedDrone: null,
  missions: [],
  selectedMission: null,
  fireObservations: [],
  fireBoundary: [],
  dashboardData: null,
  activeTab: 'dashboard',
  sidebarOpen: true,

  // Actions
  initializeSystem: async (mode: string, numDrones: number) => {
    set({ loading: true, error: null });
    try {
      const response = await api.post('/system/initialize', {
        mode,
        num_drones: numDrones,
      });
      set({
        initialized: true,
        mode,
        loading: false,
      });
      // Load initial data
      await get().loadDashboard();
      await get().loadDrones();
    } catch (error: any) {
      set({
        error: error.message,
        loading: false,
      });
    }
  },

  loadDashboard: async () => {
    try {
      const response = await api.get('/dashboard');
      set({ dashboardData: response.data.data });
    } catch (error: any) {
      set({ error: error.message });
    }
  },

  loadDrones: async () => {
    try {
      const response = await api.get('/drones');
      set({ drones: response.data.data.drones || [] });
    } catch (error: any) {
      set({ error: error.message });
    }
  },

  loadMissions: async () => {
    try {
      const response = await api.get('/missions');
      set({ missions: response.data.data.missions || [] });
    } catch (error: any) {
      set({ error: error.message });
    }
  },

  loadFireData: async () => {
    try {
      const response = await api.get('/fire/data');
      const data = response.data.data;
      set({
        fireObservations: data.observations || [],
        fireBoundary: data.boundary?.points || [],
      });
    } catch (error: any) {
      set({ error: error.message });
    }
  },

  sendDroneCommand: async (droneId: number, command: string, parameters: any = {}) => {
    set({ loading: true });
    try {
      await api.post(`/drones/${droneId}/command`, {
        command,
        parameters,
      });
      // Reload drone status
      await get().loadDrones();
      set({ loading: false });
    } catch (error: any) {
      set({
        error: error.message,
        loading: false,
      });
    }
  },

  createMission: async (droneId: number, waypoints: MissionWaypoint[]) => {
    set({ loading: true });
    try {
      await api.post('/missions/create', {
        drone_id: droneId,
        mission_id: `MISSION_${Date.now()}`,
        waypoints,
      });
      await get().loadMissions();
      set({ loading: false });
    } catch (error: any) {
      set({
        error: error.message,
        loading: false,
      });
    }
  },

  startMission: async (missionId: string) => {
    set({ loading: true });
    try {
      await api.post(`/missions/${missionId}/start`);
      await get().loadMissions();
      set({ loading: false });
    } catch (error: any) {
      set({
        error: error.message,
        loading: false,
      });
    }
  },

  stopMission: async (missionId: string) => {
    set({ loading: true });
    try {
      await api.post(`/missions/${missionId}/stop`);
      await get().loadMissions();
      set({ loading: false });
    } catch (error: any) {
      set({
        error: error.message,
        loading: false,
      });
    }
  },

  selectDrone: (drone: DroneStatus) => {
    set({ selectedDrone: drone });
  },

  selectMission: (mission: Mission) => {
    set({ selectedMission: mission });
  },

  setActiveTab: (tab: string) => {
    set({ activeTab: tab });
  },

  toggleSidebar: () => {
    set((state) => ({ sidebarOpen: !state.sidebarOpen }));
  },

  setError: (error: string | null) => {
    set({ error });
  },
}));

"""
Real-time Telemetry System - Aggregate and process telemetry from drone fleet.

Features:
- Telemetry message aggregation
- Flight status tracking
- Mission progress monitoring
- Battery and fuel management
- GPS tracking and waypoint navigation
- Real-time dashboards
"""

import time
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import logging

from Drone.MAVLinkProtocol import TelemetryPacket, GPSData, BatteryData, DroneMode

logger = logging.getLogger(__name__)


@dataclass
class FlightMetrics:
    """Flight performance metrics."""
    total_distance: float = 0.0  # meters
    total_time: float = 0.0  # seconds
    average_speed: float = 0.0  # m/s
    max_altitude: float = 0.0  # meters
    min_altitude: float = float('inf')  # meters
    battery_drain_rate: float = 0.0  # %/second
    coverage_area: float = 0.0  # square meters
    hotspots_detected: int = 0


@dataclass
class DroneFlightStatus:
    """Current flight status of a drone."""
    drone_id: int
    mode: DroneMode = DroneMode.STABILIZE
    armed: bool = False
    position: Optional[Tuple[float, float, float]] = None  # (lat, lon, alt)
    velocity: Optional[Tuple[float, float, float]] = None  # (vx, vy, vz) m/s
    heading: float = 0.0  # degrees
    attitude: Optional[Dict] = None  # roll, pitch, yaw in radians
    battery_level: float = 100.0  # 0-100%
    battery_voltage: float = 0.0  # volts
    temperature: float = 25.0  # Celsius
    signal_strength: float = 100.0  # 0-100%
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class MissionWaypoint:
    """Mission waypoint."""
    sequence: int
    latitude: float
    longitude: float
    altitude: float  # meters above ground level
    acceptance_radius: float = 5.0  # meters
    hold_time: float = 0.0  # seconds
    reached: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MissionPlan:
    """Flight mission plan."""
    mission_id: str
    drone_id: int
    waypoints: List[MissionWaypoint] = field(default_factory=list)
    current_waypoint: int = 0
    is_active: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class TelemetryBuffer:
    """Ring buffer for telemetry history."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.buffer: deque = deque(maxlen=max_size)
        self.lock = threading.Lock()

    def add(self, packet: TelemetryPacket):
        """Add telemetry packet to buffer."""
        with self.lock:
            self.buffer.append(packet)

    def get_latest(self, count: int = 1) -> List[TelemetryPacket]:
        """Get latest N packets."""
        with self.lock:
            if count >= len(self.buffer):
                return list(self.buffer)
            return list(self.buffer)[-count:]

    def get_range(self, start_time: datetime, end_time: datetime) -> List[TelemetryPacket]:
        """Get packets within time range."""
        with self.lock:
            result = []
            for packet in self.buffer:
                if start_time <= packet.timestamp <= end_time:
                    result.append(packet)
            return result


class DroneFleetTelemetry:
    """Manage telemetry for entire drone fleet."""

    def __init__(self, num_drones: int = 5):
        self.num_drones = num_drones
        self.drones: Dict[int, DroneFlightStatus] = {}
        self.telemetry_buffers: Dict[int, TelemetryBuffer] = {}
        self.mission_plans: Dict[int, MissionPlan] = {}
        self.flight_metrics: Dict[int, FlightMetrics] = {}

        # Initialize for each drone
        for i in range(1, num_drones + 1):
            self.drones[i] = DroneFlightStatus(drone_id=i)
            self.telemetry_buffers[i] = TelemetryBuffer()
            self.flight_metrics[i] = FlightMetrics()

        self.lock = threading.Lock()
        self.is_recording = False

    def update_telemetry(self, drone_id: int, packet: TelemetryPacket):
        """Update telemetry for a drone."""
        with self.lock:
            if drone_id not in self.drones:
                logger.warning(f"Unknown drone {drone_id}")
                return

            # Update flight status
            status = self.drones[drone_id]
            status.mode = packet.mode
            status.armed = packet.armed
            status.last_update = datetime.now()

            # Update GPS position
            if packet.gps:
                status.position = (packet.gps.latitude, packet.gps.longitude, packet.gps.altitude_msl)

            # Update attitude
            if packet.attitude:
                status.attitude = {
                    'roll': packet.attitude.roll,
                    'pitch': packet.attitude.pitch,
                    'yaw': packet.attitude.yaw,
                }
                status.heading = np.degrees(packet.attitude.yaw)

            # Update battery
            if packet.battery:
                status.battery_level = packet.battery.charge_remaining
                status.battery_voltage = packet.battery.voltage

            # Add to buffer
            self.telemetry_buffers[drone_id].add(packet)

            # Update metrics
            if self.is_recording:
                self._update_metrics(drone_id, packet)

    def _update_metrics(self, drone_id: int, packet: TelemetryPacket):
        """Update flight metrics."""
        metrics = self.flight_metrics[drone_id]

        # Update altitude range
        if packet.gps:
            metrics.max_altitude = max(metrics.max_altitude, packet.gps.altitude_msl)
            metrics.min_altitude = min(metrics.min_altitude, packet.gps.altitude_msl)

        # Update battery drain rate
        if packet.battery:
            current_time = time.time()
            if not hasattr(self, '_last_battery_update'):
                self._last_battery_update = {}
            if not hasattr(self, '_last_battery_level'):
                self._last_battery_level = {}

            if drone_id in self._last_battery_update:
                time_delta = current_time - self._last_battery_update[drone_id]
                if time_delta > 0:
                    battery_delta = self._last_battery_level[drone_id] - packet.battery.charge_remaining
                    metrics.battery_drain_rate = battery_delta / time_delta

            self._last_battery_update[drone_id] = current_time
            self._last_battery_level[drone_id] = packet.battery.charge_remaining

    def get_drone_status(self, drone_id: int) -> Optional[DroneFlightStatus]:
        """Get current status of a drone."""
        with self.lock:
            return self.drones.get(drone_id)

    def get_fleet_status(self) -> Dict[int, DroneFlightStatus]:
        """Get status of all drones."""
        with self.lock:
            return {drone_id: status for drone_id, status in self.drones.items()}

    def get_telemetry_history(self, drone_id: int, seconds: float = 60) -> List[TelemetryPacket]:
        """Get telemetry history for a drone."""
        now = datetime.now()
        start_time = now - timedelta(seconds=seconds)
        return self.telemetry_buffers[drone_id].get_range(start_time, now)

    def create_mission(self, drone_id: int, mission_id: str, waypoints: List[MissionWaypoint]) -> MissionPlan:
        """Create a mission for a drone."""
        mission = MissionPlan(
            mission_id=mission_id,
            drone_id=drone_id,
            waypoints=waypoints,
        )
        self.mission_plans[drone_id] = mission
        logger.info(f"Mission created for drone {drone_id}: {len(waypoints)} waypoints")
        return mission

    def start_mission(self, drone_id: int):
        """Start mission for a drone."""
        with self.lock:
            if drone_id in self.mission_plans:
                mission = self.mission_plans[drone_id]
                mission.is_active = True
                mission.start_time = datetime.now()
                logger.info(f"Mission started for drone {drone_id}")

    def update_mission_progress(self, drone_id: int, current_waypoint: int):
        """Update mission progress."""
        with self.lock:
            if drone_id in self.mission_plans:
                mission = self.mission_plans[drone_id]
                mission.current_waypoint = current_waypoint

                if current_waypoint < len(mission.waypoints):
                    mission.waypoints[current_waypoint].reached = True
                    logger.info(f"Drone {drone_id} reached waypoint {current_waypoint}")

    def end_mission(self, drone_id: int):
        """End mission for a drone."""
        with self.lock:
            if drone_id in self.mission_plans:
                mission = self.mission_plans[drone_id]
                mission.is_active = False
                mission.end_time = datetime.now()
                logger.info(f"Mission ended for drone {drone_id}")

    def get_mission(self, drone_id: int) -> Optional[MissionPlan]:
        """Get current mission for a drone."""
        return self.mission_plans.get(drone_id)

    def start_recording(self):
        """Start recording telemetry metrics."""
        self.is_recording = True
        logger.info("Telemetry recording started")

    def stop_recording(self):
        """Stop recording telemetry metrics."""
        self.is_recording = False
        logger.info("Telemetry recording stopped")

    def get_flight_report(self, drone_id: int) -> Dict:
        """Generate flight report for a drone."""
        with self.lock:
            status = self.drones.get(drone_id)
            metrics = self.flight_metrics.get(drone_id)
            mission = self.mission_plans.get(drone_id)

            if not status:
                return {}

            return {
                'drone_id': drone_id,
                'status': {
                    'mode': status.mode.name if status.mode else None,
                    'armed': status.armed,
                    'position': status.position,
                    'battery_level': status.battery_level,
                    'signal_strength': status.signal_strength,
                },
                'metrics': {
                    'total_distance': metrics.total_distance if metrics else 0,
                    'total_time': metrics.total_time if metrics else 0,
                    'average_speed': metrics.average_speed if metrics else 0,
                    'max_altitude': metrics.max_altitude if metrics else 0,
                    'battery_drain_rate': metrics.battery_drain_rate if metrics else 0,
                },
                'mission': {
                    'id': mission.mission_id if mission else None,
                    'active': mission.is_active if mission else False,
                    'current_waypoint': mission.current_waypoint if mission else 0,
                    'total_waypoints': len(mission.waypoints) if mission else 0,
                    'progress': (mission.current_waypoint / len(mission.waypoints) * 100) if mission and mission.waypoints else 0,
                } if mission else None,
            }

    def get_fleet_report(self) -> Dict:
        """Generate report for entire fleet."""
        reports = {}
        for drone_id in self.drones.keys():
            reports[drone_id] = self.get_flight_report(drone_id)

        return {
            'timestamp': datetime.now().isoformat(),
            'drone_count': len(self.drones),
            'drones': reports,
            'summary': {
                'armed_count': sum(1 for s in self.drones.values() if s.armed),
                'flying_count': sum(1 for s in self.drones.values() if s.mode == DroneMode.AUTO),
                'avg_battery': sum(s.battery_level for s in self.drones.values()) / len(self.drones) if self.drones else 0,
            },
        }


# Import numpy for calculations
import numpy as np


def create_sample_mission(start_lat: float, start_lon: float, num_waypoints: int = 5,
                         spacing_m: float = 100) -> List[MissionWaypoint]:
    """Create a sample grid mission."""
    waypoints = []

    for i in range(num_waypoints):
        # Create grid pattern
        row = i // 3
        col = i % 3

        # Convert meters to degrees (approximate)
        lat_offset = (row * spacing_m) / 111000
        lon_offset = (col * spacing_m) / (111000 * np.cos(np.radians(start_lat)))

        wp = MissionWaypoint(
            sequence=i,
            latitude=start_lat + lat_offset,
            longitude=start_lon + lon_offset,
            altitude=50.0,  # meters above ground
            acceptance_radius=5.0,
        )
        waypoints.append(wp)

    return waypoints

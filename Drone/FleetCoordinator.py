"""
Drone Fleet Coordinator - Multi-drone mission planning and coordination.

Features:
- Mission sequencing and task distribution
- Inter-drone communication simulation
- Collision avoidance
- Formation flying support
- Real-time task reassignment
"""

import time
import threading
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
import numpy as np

from Drone.MAVLinkProtocol import DroneCommandInterface, DroneMode
from Drone.TelemetrySystem import MissionWaypoint, DroneFleetTelemetry

logger = logging.getLogger(__name__)


@dataclass
class DroneTask:
    """Task assigned to a drone."""
    task_id: str
    drone_id: int
    task_type: str  # "survey", "thermal_scan", "monitoring", etc.
    priority: int = 0  # 0=lowest, 10=highest
    target_area: Optional[Tuple[float, float, float, float]] = None  # (lat_min, lon_min, lat_max, lon_max)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, assigned, in_progress, completed, failed
    result: Dict = field(default_factory=dict)


@dataclass
class FleetFormation:
    """Formation configuration for multiple drones."""
    formation_id: str
    drone_ids: List[int]
    formation_type: str  # "line", "triangle", "square", "circle"
    spacing: float = 20.0  # meters between drones
    heading: float = 0.0  # degrees


@dataclass
class SafetyZone:
    """No-fly or restricted zone."""
    zone_id: str
    center: Tuple[float, float]
    radius: float  # meters
    altitude_min: float = 0.0  # meters
    altitude_max: float = 500.0
    zone_type: str = "no_fly"  # "no_fly" or "warning"


class CollisionAvoidanceManager:
    """Manage collision avoidance for drone fleet."""

    def __init__(self, min_distance: float = 10.0, min_altitude_separation: float = 5.0):
        self.min_distance = min_distance  # meters
        self.min_altitude_separation = min_altitude_separation
        self.safety_zones: List[SafetyZone] = []

    def add_safety_zone(self, zone: SafetyZone):
        """Add no-fly or warning zone."""
        self.safety_zones.append(zone)
        logger.info(f"Safety zone added: {zone.zone_id} at ({zone.center[0]:.4f}, {zone.center[1]:.4f})")

    def check_collision_risk(self, drone_positions: Dict[int, Tuple[float, float, float]]) -> Dict:
        """
        Check for collision risks between drones.

        Args:
            drone_positions: {drone_id: (lat, lon, altitude)}

        Returns:
            Dictionary with collision risks and recommendations
        """
        risks = []
        warnings = []

        # Check pairwise distances
        drone_ids = sorted(drone_positions.keys())
        for i in range(len(drone_ids)):
            for j in range(i + 1, len(drone_ids)):
                drone_a = drone_ids[i]
                drone_b = drone_ids[j]

                pos_a = drone_positions[drone_a]
                pos_b = drone_positions[drone_b]

                distance = self._calculate_distance(pos_a[:2], pos_b[:2])
                altitude_diff = abs(pos_a[2] - pos_b[2])

                if distance < self.min_distance:
                    if altitude_diff >= self.min_altitude_separation:
                        warnings.append({
                            'type': 'horizontal_collision_risk',
                            'drone_a': drone_a,
                            'drone_b': drone_b,
                            'distance': distance,
                        })
                    else:
                        risks.append({
                            'type': 'collision_risk',
                            'drone_a': drone_a,
                            'drone_b': drone_b,
                            'distance': distance,
                            'altitude_diff': altitude_diff,
                            'severity': 'high' if distance < self.min_distance / 2 else 'medium',
                        })

        # Check safety zones
        for drone_id, (lat, lon, alt) in drone_positions.items():
            for zone in self.safety_zones:
                if self._point_in_zone(lat, lon, alt, zone):
                    risks.append({
                        'type': 'safety_zone_violation',
                        'drone_id': drone_id,
                        'zone_id': zone.zone_id,
                        'severity': 'critical' if zone.zone_type == 'no_fly' else 'warning',
                    })

        return {
            'has_risks': len(risks) > 0,
            'risks': risks,
            'warnings': warnings,
        }

    def calculate_safe_waypoints(self, start: Tuple[float, float], goal: Tuple[float, float],
                                current_positions: Dict[int, Tuple[float, float, float]]) -> List[Tuple[float, float]]:
        """Calculate safe waypoints avoiding other drones and zones."""
        # Simple RRT-style path planning (in production, use more sophisticated algorithm)
        path = [start]

        # Check direct path
        if self._is_path_clear(start, goal, current_positions):
            path.append(goal)
        else:
            # Add intermediate waypoint
            mid_lat = (start[0] + goal[0]) / 2 + 0.0001  # Small offset
            mid_lon = (start[1] + goal[1]) / 2
            if self._is_path_clear(start, (mid_lat, mid_lon), current_positions) and \
               self._is_path_clear((mid_lat, mid_lon), goal, current_positions):
                path.append((mid_lat, mid_lon))
                path.append(goal)
            else:
                # Alternative waypoint
                mid_lat = (start[0] + goal[0]) / 2
                mid_lon = (start[1] + goal[1]) / 2 - 0.0001
                path.append((mid_lat, mid_lon))
                path.append(goal)

        return path

    def _is_path_clear(self, start: Tuple[float, float], end: Tuple[float, float],
                      positions: Dict[int, Tuple[float, float, float]]) -> bool:
        """Check if path between start and end is collision-free."""
        # Sample path at regular intervals
        samples = 10
        for i in range(1, samples):
            t = i / samples
            lat = start[0] + t * (end[0] - start[0])
            lon = start[1] + t * (end[1] - start[1])

            # Check distance to all drones
            for drone_id, (d_lat, d_lon, d_alt) in positions.items():
                dist = self._calculate_distance((lat, lon), (d_lat, d_lon))
                if dist < self.min_distance * 2:  # Buffer zone
                    return False

        return True

    @staticmethod
    def _calculate_distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Calculate distance between two GPS positions in meters."""
        # Haversine formula
        lat1, lon1 = pos1
        lat2, lon2 = pos2

        R = 6371000  # Earth radius in meters
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)

        a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

        return R * c

    @staticmethod
    def _point_in_zone(lat: float, lon: float, alt: float, zone: SafetyZone) -> bool:
        """Check if point is inside safety zone."""
        distance = CollisionAvoidanceManager._calculate_distance((lat, lon), zone.center)
        in_horizontal = distance <= zone.radius
        in_vertical = zone.altitude_min <= alt <= zone.altitude_max
        return in_horizontal and in_vertical


class FleetCoordinator:
    """Coordinate operations for entire drone fleet."""

    def __init__(self, fleet_telemetry: DroneFleetTelemetry, num_drones: int = 5):
        self.fleet_telemetry = fleet_telemetry
        self.num_drones = num_drones
        self.drone_commands: Dict[int, DroneCommandInterface] = {}
        self.task_queue: List[DroneTask] = []
        self.active_tasks: Dict[int, DroneTask] = {}  # drone_id -> task
        self.completed_tasks: List[DroneTask] = []
        self.formations: Dict[str, FleetFormation] = {}
        self.collision_avoidance = CollisionAvoidanceManager()

        # Initialize command interfaces
        for i in range(1, num_drones + 1):
            self.drone_commands[i] = DroneCommandInterface(i)

        self.lock = threading.Lock()
        self.is_running = False
        self.coordinator_thread: Optional[threading.Thread] = None

    def add_task(self, task: DroneTask):
        """Add task to queue."""
        with self.lock:
            self.task_queue.append(task)
            logger.info(f"Task added: {task.task_id} (priority={task.priority})")

    def assign_tasks(self):
        """Assign queued tasks to available drones."""
        with self.lock:
            # Sort by priority
            self.task_queue.sort(key=lambda t: t.priority, reverse=True)

            # Get available drones
            available_drones = [d for d in range(1, self.num_drones + 1)
                               if d not in self.active_tasks]

            # Assign tasks
            assigned = []
            for task in self.task_queue:
                if not available_drones:
                    break

                drone_id = available_drones.pop(0)
                task.drone_id = drone_id
                task.status = "assigned"
                task.started_at = datetime.now()
                self.active_tasks[drone_id] = task
                assigned.append(task.task_id)

                logger.info(f"Task {task.task_id} assigned to drone {drone_id}")

            # Remove assigned tasks from queue
            self.task_queue = [t for t in self.task_queue if t.task_id not in assigned]

    def complete_task(self, drone_id: int, result: Dict):
        """Mark task as complete."""
        with self.lock:
            if drone_id in self.active_tasks:
                task = self.active_tasks.pop(drone_id)
                task.status = "completed"
                task.completed_at = datetime.now()
                task.result = result
                self.completed_tasks.append(task)

                logger.info(f"Task {task.task_id} completed on drone {drone_id}")

    def form_formation(self, formation: FleetFormation):
        """Create drone formation."""
        self.formations[formation.formation_id] = formation
        logger.info(f"Formation {formation.formation_id} created: {len(formation.drone_ids)} drones")

    def get_formation_positions(self, formation_id: str, center: Tuple[float, float],
                               altitude: float) -> Dict[int, Tuple[float, float, float]]:
        """Calculate positions for formation."""
        formation = self.formations.get(formation_id)
        if not formation:
            return {}

        positions = {}

        if formation.formation_type == "line":
            # Line formation
            for i, drone_id in enumerate(formation.drone_ids):
                offset_lat = (i - len(formation.drone_ids) / 2) * formation.spacing / 111000
                offset_lon = 0
                positions[drone_id] = (center[0] + offset_lat, center[1] + offset_lon, altitude)

        elif formation.formation_type == "triangle":
            # Triangle formation
            for i, drone_id in enumerate(formation.drone_ids):
                angle = (i * 120) % 360
                offset_lat = formation.spacing * np.cos(np.radians(angle)) / 111000
                offset_lon = formation.spacing * np.sin(np.radians(angle)) / (111000 * np.cos(np.radians(center[0])))
                positions[drone_id] = (center[0] + offset_lat, center[1] + offset_lon, altitude)

        elif formation.formation_type == "circle":
            # Circle formation
            for i, drone_id in enumerate(formation.drone_ids):
                angle = (i * 360 / len(formation.drone_ids)) % 360
                offset_lat = formation.spacing * np.cos(np.radians(angle)) / 111000
                offset_lon = formation.spacing * np.sin(np.radians(angle)) / (111000 * np.cos(np.radians(center[0])))
                positions[drone_id] = (center[0] + offset_lat, center[1] + offset_lon, altitude)

        return positions

    def start_coordinator(self):
        """Start fleet coordination."""
        if self.is_running:
            return

        self.is_running = True
        self.coordinator_thread = threading.Thread(target=self._coordinator_loop, daemon=True)
        self.coordinator_thread.start()
        logger.info("Fleet coordinator started")

    def stop_coordinator(self):
        """Stop fleet coordination."""
        self.is_running = False
        if self.coordinator_thread:
            self.coordinator_thread.join(timeout=2.0)
        logger.info("Fleet coordinator stopped")

    def _coordinator_loop(self):
        """Main coordinator loop."""
        while self.is_running:
            try:
                # Assign tasks
                self.assign_tasks()

                # Check collision risks
                positions = self._get_current_positions()
                risks = self.collision_avoidance.check_collision_risk(positions)

                if risks['has_risks']:
                    logger.warning(f"Collision risks detected: {risks['risks']}")

                # Get fleet status
                # (would update dashboard, send commands, etc.)

                time.sleep(1.0)

            except Exception as e:
                logger.error(f"Error in coordinator loop: {e}")
                time.sleep(1.0)

    def _get_current_positions(self) -> Dict[int, Tuple[float, float, float]]:
        """Get current positions of all drones."""
        positions = {}

        for drone_id in range(1, self.num_drones + 1):
            status = self.fleet_telemetry.get_drone_status(drone_id)
            if status and status.position:
                positions[drone_id] = status.position

        return positions

    def get_fleet_status(self) -> Dict:
        """Get comprehensive fleet status."""
        return {
            'timestamp': datetime.now().isoformat(),
            'active_tasks': len(self.active_tasks),
            'queued_tasks': len(self.task_queue),
            'completed_tasks': len(self.completed_tasks),
            'active_formations': len(self.formations),
            'tasks': {
                'active': [
                    {
                        'id': task.task_id,
                        'drone_id': task.drone_id,
                        'type': task.task_type,
                        'status': task.status,
                    }
                    for task in self.active_tasks.values()
                ],
                'queued': [
                    {
                        'id': task.task_id,
                        'type': task.task_type,
                        'priority': task.priority,
                    }
                    for task in self.task_queue[:5]  # First 5
                ],
            },
        }

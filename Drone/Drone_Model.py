"""
Drone data model and telemetry representation.
Supports both real and virtual drones with various capabilities.
"""

from typing import Dict, List, Tuple, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DroneStatus(Enum):
    """Drone operational status."""
    IDLE = "idle"
    ARMED = "armed"
    FLYING = "flying"
    RETURNING = "returning"
    LANDED = "landed"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class DroneType(Enum):
    """Drone hardware types."""
    QUADCOPTER = "quadcopter"
    HEXACOPTER = "hexacopter"
    FIXED_WING = "fixed_wing"
    VIRTUAL = "virtual"
    SIMULATED = "simulated"


@dataclass
class DroneCapabilities:
    """Drone sensor and operational capabilities."""
    thermal_camera: bool = False
    rgb_camera: bool = False
    lidar: bool = False
    thermal_resolution: Optional[Tuple[int, int]] = None  # (width, height)
    rgb_resolution: Optional[Tuple[int, int]] = None
    lidar_range_m: Optional[float] = None
    max_altitude_m: float = 500
    max_speed_ms: float = 20
    max_flight_time_s: float = 1800  # 30 minutes
    payload_kg: float = 2.0
    wind_resistance_ms: float = 10
    gps_precision_m: float = 2.0
    can_rtk: bool = False
    can_follow_me: bool = False
    can_autonomous_flight: bool = True


@dataclass
class DroneTelemetry:
    """Real-time drone telemetry data."""
    timestamp: datetime
    latitude: float
    longitude: float
    altitude_m: float
    battery_percent: float
    speed_ms: float
    heading_degrees: float
    gps_satcount: int
    gps_hdop: float
    temperature_c: float
    status: DroneStatus
    
    # Optional sensor data
    thermal_image: Optional[bytes] = None
    rgb_image: Optional[bytes] = None
    
    # Navigation data
    target_latitude: Optional[float] = None
    target_longitude: Optional[float] = None
    distance_to_target_m: Optional[float] = None
    
    # Warnings
    low_battery: bool = False
    critical_battery: bool = False
    gps_warning: bool = False
    sensor_error: bool = False
    
    def to_dict(self):
        """Convert telemetry to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude_m": self.altitude_m,
            "battery_percent": self.battery_percent,
            "speed_ms": self.speed_ms,
            "heading_degrees": self.heading_degrees,
            "status": self.status.value
        }


class Drone:
    """
    Represents a drone (real or virtual) in the system.
    """
    
    def __init__(self,
                 drone_id: int,
                 name: str,
                 drone_type: DroneType = DroneType.VIRTUAL,
                 capabilities: Optional[DroneCapabilities] = None,
                 launch_lat: float = 0,
                 launch_lon: float = 0):
        """
        Initialize drone.
        
        Args:
            drone_id: Unique drone identifier
            name: Human-readable drone name
            drone_type: Type of drone (quadcopter, virtual, etc.)
            capabilities: Drone capabilities
            launch_lat: Launch location latitude
            launch_lon: Launch location longitude
        """
        self.drone_id = drone_id
        self.name = name
        self.drone_type = drone_type
        self.capabilities = capabilities or DroneCapabilities()
        
        # Location
        self.launch_latitude = launch_lat
        self.launch_longitude = launch_lon
        self.current_latitude = launch_lat
        self.current_longitude = launch_lon
        self.current_altitude = 0
        
        # State
        self.status = DroneStatus.IDLE
        self.battery_percent = 100
        self.current_speed = 0
        self.heading = 0
        
        # Mission
        self.assigned_nodes: List[Tuple[float, float]] = []
        self.planned_path: List[Tuple[float, float]] = []
        self.waypoints: List[Tuple[float, float]] = []
        self.current_waypoint_index = 0
        
        # Statistics
        self.flight_distance = 0
        self.flight_time_s = 0
        self.mission_start_time: Optional[datetime] = None
        self.mission_end_time: Optional[datetime] = None
        self.nodes_visited: Set[Tuple[float, float]] = set()
        
        # Telemetry history
        self.telemetry_history: List[DroneTelemetry] = []
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}_{drone_id}")
    
    def is_real(self) -> bool:
        """Check if this is a real or simulated drone."""
        return self.drone_type not in [DroneType.VIRTUAL, DroneType.SIMULATED]
    
    def set_assigned_nodes(self, nodes: List[Tuple[float, float]]):
        """Set the mesh nodes assigned to this drone."""
        self.assigned_nodes = nodes
        self.logger.info(f"Drone {self.drone_id}: {len(nodes)} nodes assigned")
    
    def set_planned_path(self, path: List[Tuple[float, float]]):
        """Set the planned flight path."""
        self.planned_path = path
        self.waypoints = path.copy()
        self.current_waypoint_index = 0
        self.logger.info(f"Drone {self.drone_id}: Path planned with {len(path)} waypoints")
    
    def arm(self) -> bool:
        """Arm the drone for flight."""
        if self.status == DroneStatus.IDLE and self.battery_percent > 20:
            self.status = DroneStatus.ARMED
            self.mission_start_time = datetime.now()
            self.logger.info(f"Drone {self.drone_id} armed")
            return True
        return False
    
    def disarm(self):
        """Disarm the drone."""
        self.status = DroneStatus.LANDED
        if self.mission_start_time:
            self.mission_end_time = datetime.now()
            self.flight_time_s = (self.mission_end_time - self.mission_start_time).total_seconds()
        self.logger.info(f"Drone {self.drone_id} disarmed")
    
    def start_mission(self) -> bool:
        """Start executing the mission."""
        if self.status == DroneStatus.ARMED and self.planned_path:
            self.status = DroneStatus.FLYING
            self.logger.info(f"Drone {self.drone_id} mission started")
            return True
        return False
    
    def update_position(self,
                       latitude: float,
                       longitude: float,
                       altitude_m: float,
                       battery_percent: float,
                       speed_ms: float,
                       heading_degrees: float):
        """Update drone position and telemetry."""
        
        # Calculate distance traveled
        from GIS.CoordinateSystem import CoordinateSystem
        if self.current_latitude != 0 or self.current_longitude != 0:
            segment_distance = CoordinateSystem.haversine_distance(
                (self.current_latitude, self.current_longitude),
                (latitude, longitude)
            )
            self.flight_distance += segment_distance
        
        # Update state
        self.current_latitude = latitude
        self.current_longitude = longitude
        self.current_altitude = altitude_m
        self.battery_percent = battery_percent
        self.current_speed = speed_ms
        self.heading = heading_degrees
        
        # Store telemetry
        telemetry = DroneTelemetry(
            timestamp=datetime.now(),
            latitude=latitude,
            longitude=longitude,
            altitude_m=altitude_m,
            battery_percent=battery_percent,
            speed_ms=speed_ms,
            heading_degrees=heading_degrees,
            gps_satcount=10,
            gps_hdop=1.0,
            temperature_c=25,
            status=self.status,
            low_battery=battery_percent < 20,
            critical_battery=battery_percent < 5
        )
        self.telemetry_history.append(telemetry)
    
    def visit_node(self, node: Tuple[float, float]):
        """Mark a node as visited."""
        if node in self.assigned_nodes:
            self.nodes_visited.add(node)
    
    def get_coverage_percentage(self) -> float:
        """Get percentage of assigned nodes visited."""
        if not self.assigned_nodes:
            return 0.0
        
        return (len(self.nodes_visited) / len(self.assigned_nodes)) * 100
    
    def get_status_report(self) -> Dict:
        """Get current status report."""
        return {
            "drone_id": self.drone_id,
            "name": self.name,
            "type": self.drone_type.value,
            "status": self.status.value,
            "battery_percent": self.battery_percent,
            "latitude": self.current_latitude,
            "longitude": self.current_longitude,
            "altitude_m": self.current_altitude,
            "assigned_nodes": len(self.assigned_nodes),
            "visited_nodes": len(self.nodes_visited),
            "coverage_percent": self.get_coverage_percentage(),
            "flight_distance_m": self.flight_distance,
            "flight_time_s": self.flight_time_s
        }
    
    def __repr__(self):
        return (f"Drone(id={self.drone_id}, name='{self.name}', "
                f"type={self.drone_type.value}, status={self.status.value})")

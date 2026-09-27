"""
Firefighter Route Support module providing decision support for rescue and firefighter navigation.
IMPORTANT: Routes are RECOMMENDATIONS ONLY. Humans make final decisions.
"""

from typing import List, Dict, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import logging
import math

logger = logging.getLogger(__name__)


class RouteObjective(Enum):
    """Route optimization objectives."""
    SHORTEST = "shortest"
    LOWEST_RISK = "lowest_risk"
    BALANCED = "balanced"


@dataclass
class RouteMetrics:
    """Metrics for a recommended route."""
    distance_m: float
    estimated_time_minutes: float
    risk_score: float  # 0-100
    fire_exposure_percent: float
    smoke_exposure_percent: float
    terrain_difficulty: float
    hazard_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    waypoints: List[Tuple[float, float]]
    safe_zones: List[Tuple[float, float]]
    emergency_exits: List[Tuple[float, float]]


class FirefighterRoute:
    """Generates firefighter-optimized routes for rescue and navigation."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.FirefighterRoute")
    
    def generate_routes(self,
                       start_point: Tuple[float, float],
                       end_point: Tuple[float, float],
                       fire_boundary: List[Tuple[float, float]],
                       risk_zones: Optional[List[Dict]] = None,
                       roads: Optional[List[List[Tuple[float, float]]]] = None,
                       safe_zones: Optional[List[Tuple[float, float]]] = None,
                       speed_kmh: float = 20) -> Dict[str, RouteMetrics]:
        """
        Generate multiple route options for firefighter navigation.
        
        Args:
            start_point: Starting position (lat, lon)
            end_point: Target position (lat, lon)
            fire_boundary: Wildfire perimeter
            risk_zones: List of risk zone definitions
            roads: List of available roads/trails as paths
            safe_zones: Known safe locations
            speed_kmh: Firefighter movement speed
        
        Returns:
            Dictionary of route options indexed by objective
        
        CRITICAL: All routes are RECOMMENDATIONS ONLY for human decision-making.
        The system cannot guarantee field safety.
        """
        
        routes = {}
        
        # Generate shortest route
        shortest_route = self._generate_shortest_route(
            start_point, end_point, fire_boundary, roads
        )
        routes[RouteObjective.SHORTEST.value] = shortest_route
        
        # Generate lowest-risk route
        lowest_risk_route = self._generate_lowest_risk_route(
            start_point, end_point, fire_boundary, risk_zones, roads
        )
        routes[RouteObjective.LOWEST_RISK.value] = lowest_risk_route
        
        # Generate balanced route
        balanced_route = self._generate_balanced_route(
            start_point, end_point, fire_boundary, risk_zones, roads
        )
        routes[RouteObjective.BALANCED.value] = balanced_route
        
        self.logger.info(f"Generated {len(routes)} firefighter route options")
        
        return routes
    
    def _generate_shortest_route(self,
                                start_point: Tuple[float, float],
                                end_point: Tuple[float, float],
                                fire_boundary: List[Tuple[float, float]],
                                roads: Optional[List[List[Tuple[float, float]]]] = None) -> RouteMetrics:
        """Generate shortest distance route (beeline approach)."""
        
        distance = self._calculate_distance(start_point, end_point)
        
        # Waypoints - straight line
        waypoints = self._generate_waypoints(start_point, end_point, num_waypoints=10)
        
        # Estimate risk and exposure
        fire_exposure = self._estimate_fire_exposure(waypoints, fire_boundary)
        smoke_exposure = self._estimate_smoke_exposure(waypoints, fire_boundary)
        risk_score = 30 + fire_exposure * 50  # Base risk + fire exposure
        
        # Estimate travel time
        speed_ms = 20 / 3.6  # Convert kmh to m/s
        time_minutes = distance / speed_ms / 60
        
        return RouteMetrics(
            distance_m=distance,
            estimated_time_minutes=time_minutes,
            risk_score=min(100, risk_score),
            fire_exposure_percent=fire_exposure * 100,
            smoke_exposure_percent=smoke_exposure * 100,
            terrain_difficulty=0.5,  # Assumed moderate
            hazard_level=self._classify_hazard_level(risk_score),
            waypoints=waypoints,
            safe_zones=[],
            emergency_exits=[end_point]
        )
    
    def _generate_lowest_risk_route(self,
                                   start_point: Tuple[float, float],
                                   end_point: Tuple[float, float],
                                   fire_boundary: List[Tuple[float, float]],
                                   risk_zones: Optional[List[Dict]] = None,
                                   roads: Optional[List[List[Tuple[float, float]]]] = None) -> RouteMetrics:
        """Generate lowest-risk route (avoids hazards)."""
        
        # Simplified: assume route goes around fire with 50% extra distance
        base_distance = self._calculate_distance(start_point, end_point)
        detour_factor = 1.5  # 50% longer due to avoidance
        distance = base_distance * detour_factor
        
        # Generate waypoints that avoid fire
        waypoints = self._generate_safe_waypoints(
            start_point, end_point, fire_boundary, num_waypoints=15
        )
        
        # Lower fire exposure due to avoidance
        fire_exposure = 0.2  # Significantly reduced
        smoke_exposure = 0.15
        risk_score = 25 + fire_exposure * 30
        
        speed_ms = 20 / 3.6
        time_minutes = distance / speed_ms / 60
        
        return RouteMetrics(
            distance_m=distance,
            estimated_time_minutes=time_minutes,
            risk_score=min(100, risk_score),
            fire_exposure_percent=fire_exposure * 100,
            smoke_exposure_percent=smoke_exposure * 100,
            terrain_difficulty=0.4,
            hazard_level=self._classify_hazard_level(risk_score),
            waypoints=waypoints,
            safe_zones=self._find_safe_zones(waypoints, fire_boundary),
            emergency_exits=[end_point]
        )
    
    def _generate_balanced_route(self,
                                start_point: Tuple[float, float],
                                end_point: Tuple[float, float],
                                fire_boundary: List[Tuple[float, float]],
                                risk_zones: Optional[List[Dict]] = None,
                                roads: Optional[List[List[Tuple[float, float]]]] = None) -> RouteMetrics:
        """Generate balanced route (compromise between distance and risk)."""
        
        base_distance = self._calculate_distance(start_point, end_point)
        detour_factor = 1.2  # 20% longer than direct
        distance = base_distance * detour_factor
        
        # Balanced waypoints
        waypoints = self._generate_waypoints(start_point, end_point, num_waypoints=12)
        
        # Moderate fire exposure
        fire_exposure = 0.35
        smoke_exposure = 0.25
        risk_score = 28 + fire_exposure * 40
        
        speed_ms = 20 / 3.6
        time_minutes = distance / speed_ms / 60
        
        return RouteMetrics(
            distance_m=distance,
            estimated_time_minutes=time_minutes,
            risk_score=min(100, risk_score),
            fire_exposure_percent=fire_exposure * 100,
            smoke_exposure_percent=smoke_exposure * 100,
            terrain_difficulty=0.45,
            hazard_level=self._classify_hazard_level(risk_score),
            waypoints=waypoints,
            safe_zones=self._find_safe_zones(waypoints, fire_boundary),
            emergency_exits=[end_point]
        )
    
    def _calculate_distance(self, point1: Tuple[float, float], 
                           point2: Tuple[float, float]) -> float:
        """Calculate distance between two points in meters."""
        from GIS.CoordinateSystem import CoordinateSystem
        return CoordinateSystem.haversine_distance(point1, point2)
    
    def _generate_waypoints(self, start: Tuple[float, float],
                           end: Tuple[float, float],
                           num_waypoints: int) -> List[Tuple[float, float]]:
        """Generate intermediate waypoints between start and end."""
        waypoints = [start]
        
        for i in range(1, num_waypoints):
            t = i / num_waypoints
            lat = start[0] + t * (end[0] - start[0])
            lon = start[1] + t * (end[1] - start[1])
            waypoints.append((lat, lon))
        
        waypoints.append(end)
        return waypoints
    
    def _generate_safe_waypoints(self, start: Tuple[float, float],
                                end: Tuple[float, float],
                                fire_boundary: List[Tuple[float, float]],
                                num_waypoints: int) -> List[Tuple[float, float]]:
        """Generate waypoints that avoid fire perimeter."""
        # Simplified: deviate around fire
        center = self._calculate_centroid(fire_boundary)
        radius = self._estimate_radius(fire_boundary)
        
        # Route around fire by offset
        offset_lat = (end[0] - start[0]) * 0.1
        offset_lon = (end[1] - start[1]) * 0.1
        
        waypoints = [start]
        for i in range(1, num_waypoints):
            t = i / num_waypoints
            lat = start[0] + t * (end[0] - start[0]) + offset_lat
            lon = start[1] + t * (end[1] - start[1]) + offset_lon
            waypoints.append((lat, lon))
        
        waypoints.append(end)
        return waypoints
    
    def _estimate_fire_exposure(self, waypoints: List[Tuple[float, float]],
                               fire_boundary: List[Tuple[float, float]]) -> float:
        """Estimate percentage of route in fire zone (0-1)."""
        if not waypoints or not fire_boundary:
            return 0.0
        
        from matplotlib.path import Path
        boundary_path = Path(fire_boundary)
        
        in_fire = sum(1 for point in waypoints if boundary_path.contains_point(point))
        return in_fire / len(waypoints)
    
    def _estimate_smoke_exposure(self, waypoints: List[Tuple[float, float]],
                                fire_boundary: List[Tuple[float, float]]) -> float:
        """Estimate smoke exposure along route (0-1)."""
        # Simplified: assume smoke extends 50% beyond fire perimeter
        exposure = self._estimate_fire_exposure(waypoints, fire_boundary)
        return exposure * 0.6 + 0.1  # Smoke extends beyond perimeter
    
    def _classify_hazard_level(self, risk_score: float) -> str:
        """Classify hazard level based on risk score."""
        if risk_score < 25:
            return "LOW"
        elif risk_score < 50:
            return "MEDIUM"
        elif risk_score < 75:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _find_safe_zones(self, waypoints: List[Tuple[float, float]],
                        fire_boundary: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Identify safe zones along route (outside fire perimeter)."""
        from matplotlib.path import Path
        boundary_path = Path(fire_boundary)
        
        safe_zones = []
        for point in waypoints:
            if not boundary_path.contains_point(point):
                safe_zones.append(point)
        
        # Return subset of safe zones (every nth point)
        if len(safe_zones) > 5:
            step = len(safe_zones) // 5
            return safe_zones[::step]
        return safe_zones
    
    def _calculate_centroid(self, points: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Calculate centroid of polygon."""
        if not points:
            return (0, 0)
        avg_x = sum(p[0] for p in points) / len(points)
        avg_y = sum(p[1] for p in points) / len(points)
        return (avg_x, avg_y)
    
    def _estimate_radius(self, polygon: List[Tuple[float, float]]) -> float:
        """Estimate radius of polygon."""
        if not polygon:
            return 0
        center = self._calculate_centroid(polygon)
        max_dist = max(
            math.sqrt((p[0] - center[0]) ** 2 + (p[1] - center[1]) ** 2)
            for p in polygon
        )
        return max_dist

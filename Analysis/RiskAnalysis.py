"""
Risk Analysis module for wildfire monitoring and drone path safety assessment.
Calculates multi-factor risk scores for regions and paths.
"""

from typing import Dict, List, Tuple, Optional, Callable
from enum import Enum
import logging
import math

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk classification levels."""
    GREEN = "safe"
    YELLOW = "caution"
    RED = "restricted"
    CRITICAL = "critical"


class RiskZone:
    """Represents a risk zone in the wildfire area."""
    
    def __init__(self,
                 zone_id: str,
                 center: Tuple[float, float],
                 radius_m: float,
                 risk_level: RiskLevel,
                 cause: str,
                 intensity: float = 1.0):
        """
        Initialize risk zone.
        
        Args:
            zone_id: Unique identifier
            center: Center coordinates (lat, lon) or (x, y)
            radius_m: Zone radius in meters
            risk_level: Risk classification
            cause: Description of risk cause
            intensity: Risk intensity factor (0-1)
        """
        self.zone_id = zone_id
        self.center = center
        self.radius_m = radius_m
        self.risk_level = risk_level
        self.cause = cause
        self.intensity = intensity
    
    def contains_point(self, point: Tuple[float, float]) -> bool:
        """Check if point is within this risk zone."""
        x1, y1 = self.center
        x2, y2 = point
        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return distance <= self.radius_m
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "zone_id": self.zone_id,
            "center": self.center,
            "radius_m": self.radius_m,
            "risk_level": self.risk_level.value,
            "cause": self.cause,
            "intensity": self.intensity
        }


def calculate_risk_score(fire_distance_m: float,
                        fire_intensity: float = 1.0,
                        smoke_level: float = 0,
                        heat_intensity: float = 0,
                        wind_speed_ms: float = 0,
                        terrain_difficulty: float = 0,
                        battery_percent: float = 100) -> float:
    """
    Calculate comprehensive risk score (0-100).
    
    Args:
        fire_distance_m: Distance from fire perimeter in meters
        fire_intensity: Fire intensity factor (0-1)
        smoke_level: Smoke visibility reduction (0-1)
        heat_intensity: Heat radiation intensity (0-1)
        wind_speed_ms: Wind speed in m/s
        terrain_difficulty: Terrain difficulty factor (0-1)
        battery_percent: Current battery percentage
    
    Returns:
        Risk score (0-100)
    """
    score = 0
    
    # Fire distance risk (closer = higher risk)
    if fire_distance_m < 100:
        fire_risk = 40 * fire_intensity * (1 - fire_distance_m / 100)
    elif fire_distance_m < 500:
        fire_risk = 25 * fire_intensity * (1 - (fire_distance_m - 100) / 400)
    else:
        fire_risk = 5 * fire_intensity
    
    score += fire_risk
    
    # Smoke risk
    score += 20 * smoke_level
    
    # Heat risk
    score += 15 * heat_intensity
    
    # Wind risk
    wind_risk = min(100, wind_speed_ms * 2)
    score += (wind_risk / 100) * 10
    
    # Terrain risk
    score += 5 * terrain_difficulty
    
    # Battery risk
    if battery_percent < 20:
        score += 5
    if battery_percent < 5:
        score += 10
    
    return min(100, max(0, score))


def classify_risk_zone(risk_score: float) -> RiskLevel:
    """Classify risk level based on score."""
    if risk_score < 30:
        return RiskLevel.GREEN
    elif risk_score < 60:
        return RiskLevel.YELLOW
    elif risk_score < 85:
        return RiskLevel.RED
    else:
        return RiskLevel.CRITICAL


def generate_risk_zones(fire_boundary: List[Tuple[float, float]],
                       fire_observations: Optional[List[Tuple[float, float]]] = None,
                       buffer_distance_m: float = 100) -> List[RiskZone]:
    """
    Generate risk zones from fire boundary and observations.
    
    Args:
        fire_boundary: Perimeter of fire zone
        fire_observations: Detected fire hotspots
        buffer_distance_m: Buffer distance around fire
    
    Returns:
        List of risk zones
    """
    zones = []
    
    # Main fire zone (RED)
    center = _calculate_centroid(fire_boundary)
    radius = _estimate_boundary_radius(fire_boundary)
    
    main_zone = RiskZone(
        zone_id="fire_main",
        center=center,
        radius_m=radius + buffer_distance_m,
        risk_level=RiskLevel.RED,
        cause="Active wildfire zone",
        intensity=1.0
    )
    zones.append(main_zone)
    
    # Hotspot zones
    if fire_observations:
        for i, hotspot in enumerate(fire_observations[:10]):  # Limit to 10
            hotspot_zone = RiskZone(
                zone_id=f"hotspot_{i}",
                center=hotspot,
                radius_m=50,
                risk_level=RiskLevel.RED,
                cause="Thermal hotspot detected",
                intensity=0.8
            )
            zones.append(hotspot_zone)
    
    # Smoke zone (YELLOW) - assume extends beyond main zone
    smoke_zone = RiskZone(
        zone_id="smoke_zone",
        center=center,
        radius_m=radius + buffer_distance_m * 1.5,
        risk_level=RiskLevel.YELLOW,
        cause="Smoke and reduced visibility",
        intensity=0.6
    )
    zones.append(smoke_zone)
    
    logger.info(f"Generated {len(zones)} risk zones")
    return zones


def calculate_path_risk(path: List[Tuple[float, float]],
                       risk_zones: List[RiskZone],
                       risk_weights: Optional[Dict[str, float]] = None) -> Dict:
    """
    Analyze risk along a path.
    
    Args:
        path: Waypoints path
        risk_zones: List of risk zones
        risk_weights: Custom risk weights
    
    Returns:
        Risk analysis dictionary
    """
    if not risk_weights:
        risk_weights = {
            "distance": 0.25,
            "fire": 0.25,
            "smoke": 0.15,
            "heat": 0.15,
            "wind": 0.10,
            "terrain": 0.05,
            "obstacle": 0.03,
            "battery": 0.02
        }
    
    total_risk = 0
    risky_segments = []
    
    for i in range(len(path) - 1):
        segment_start = path[i]
        segment_end = path[i + 1]
        segment_midpoint = (
            (segment_start[0] + segment_end[0]) / 2,
            (segment_start[1] + segment_end[1]) / 2
        )
        
        # Check segment risk
        segment_risk = 0
        for zone in risk_zones:
            if zone.contains_point(segment_midpoint):
                segment_risk = max(segment_risk, 
                                  classify_risk_zone_score(zone.risk_level) * zone.intensity)
        
        total_risk += segment_risk
        
        if segment_risk > 50:
            risky_segments.append({
                "segment": i,
                "risk_score": segment_risk,
                "location": segment_midpoint
            })
    
    average_risk = total_risk / max(len(path) - 1, 1)
    
    return {
        "total_path_risk": total_risk,
        "average_segment_risk": average_risk,
        "risky_segments": risky_segments,
        "risk_level": classify_risk_zone(average_risk).value,
        "path_feasibility": "HIGH RISK" if average_risk > 75 else "MEDIUM RISK" if average_risk > 50 else "ACCEPTABLE"
    }


def classify_risk_zone_score(risk_level: RiskLevel) -> float:
    """Convert risk level to numeric score."""
    scores = {
        RiskLevel.GREEN: 20,
        RiskLevel.YELLOW: 50,
        RiskLevel.RED: 80,
        RiskLevel.CRITICAL: 95
    }
    return scores.get(risk_level, 50)


def _calculate_centroid(points: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Calculate centroid of points."""
    if not points:
        return (0, 0)
    avg_x = sum(p[0] for p in points) / len(points)
    avg_y = sum(p[1] for p in points) / len(points)
    return (avg_x, avg_y)


def _estimate_boundary_radius(boundary: List[Tuple[float, float]]) -> float:
    """Estimate radius of boundary polygon."""
    if not boundary:
        return 0
    
    center = _calculate_centroid(boundary)
    max_distance = max(
        math.sqrt((p[0] - center[0]) ** 2 + (p[1] - center[1]) ** 2)
        for p in boundary
    )
    return max_distance

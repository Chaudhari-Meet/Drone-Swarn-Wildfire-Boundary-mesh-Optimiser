"""
GIS Coordinate transformation and geographic utilities.
Handles conversion between different coordinate systems and projections.
"""

import math
from typing import Tuple, List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Earth constants
EARTH_RADIUS_M = 6371000  # meters
EARTH_RADIUS_KM = 6371  # kilometers
EARTH_RADIUS_MILES = 3959  # miles


class CoordinateSystem:
    """
    Utility class for geographic coordinate operations.
    Supports both Cartesian (XY) and geographic (lat/lon) coordinates.
    """
    
    @staticmethod
    def is_geographic(boundary_points: List[Tuple[float, float]]) -> bool:
        """
        Detect if coordinates are geographic (lat/lon) or Cartesian (xy).
        
        Heuristic: if all points have absolute values < 180, assume geographic.
        """
        for x, y in boundary_points:
            if abs(x) > 180 or abs(y) > 180:
                return False
        return True
    
    @staticmethod
    def haversine_distance(point1: Tuple[float, float], 
                          point2: Tuple[float, float]) -> float:
        """
        Calculate geodesic distance between two points using Haversine formula.
        
        Args:
            point1: (latitude, longitude) in degrees
            point2: (latitude, longitude) in degrees
        
        Returns:
            Distance in meters
        """
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        distance = EARTH_RADIUS_M * c
        return distance
    
    @staticmethod
    def cartesian_distance(point1: Tuple[float, float],
                          point2: Tuple[float, float]) -> float:
        """
        Calculate Euclidean distance between two points.
        
        Args:
            point1: (x, y) coordinates
            point2: (x, y) coordinates
        
        Returns:
            Distance in units
        """
        x1, y1 = point1
        x2, y2 = point2
        
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
    @staticmethod
    def calculate_distance(point1: Tuple[float, float],
                          point2: Tuple[float, float],
                          is_geographic: bool = True) -> float:
        """
        Calculate distance between two points (geographic or Cartesian).
        
        Args:
            point1: First point
            point2: Second point
            is_geographic: True for lat/lon, False for xy
        
        Returns:
            Distance (in meters for geographic, units for Cartesian)
        """
        if is_geographic:
            return CoordinateSystem.haversine_distance(point1, point2)
        else:
            return CoordinateSystem.cartesian_distance(point1, point2)
    
    @staticmethod
    def geographic_to_projected(lat: float, lon: float, 
                               center_lat: float = 0, 
                               center_lon: float = 0) -> Tuple[float, float]:
        """
        Convert geographic coordinates to Web Mercator projection.
        
        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            center_lat: Reference latitude for local projection
            center_lon: Reference longitude for local projection
        
        Returns:
            (x, y) in projected coordinates
        """
        # Simple equirectangular projection centered at reference point
        x = (lon - center_lon) * 111000 * math.cos(math.radians(center_lat))
        y = (lat - center_lat) * 111000
        
        return x, y
    
    @staticmethod
    def projected_to_geographic(x: float, y: float,
                               center_lat: float = 0,
                               center_lon: float = 0) -> Tuple[float, float]:
        """
        Convert projected coordinates back to geographic.
        
        Args:
            x: Projected X coordinate
            y: Projected Y coordinate
            center_lat: Reference latitude for local projection
            center_lon: Reference longitude for local projection
        
        Returns:
            (latitude, longitude) in degrees
        """
        lat = y / 111000 + center_lat
        lon = x / (111000 * math.cos(math.radians(center_lat))) + center_lon
        
        return lat, lon
    
    @staticmethod
    def calculate_area_cartesian(boundary_points: List[Tuple[float, float]]) -> float:
        """
        Calculate polygon area using Shoelace formula (Cartesian coordinates).
        
        Args:
            boundary_points: List of (x, y) tuples
        
        Returns:
            Area in square units
        """
        n = len(boundary_points)
        if n < 3:
            return 0.0
        
        area = 0.0
        for i in range(n):
            x1, y1 = boundary_points[i]
            x2, y2 = boundary_points[(i + 1) % n]
            area += (x1 * y2) - (x2 * y1)
        
        return abs(area) / 2.0
    
    @staticmethod
    def calculate_area_geographic(boundary_points: List[Tuple[float, float]]) -> float:
        """
        Calculate polygon area from geographic coordinates using spherical excess.
        
        Args:
            boundary_points: List of (lat, lon) tuples in degrees
        
        Returns:
            Area in square meters
        """
        if len(boundary_points) < 3:
            return 0.0
        
        # Convert to radians
        points_rad = [(math.radians(lat), math.radians(lon)) 
                     for lat, lon in boundary_points]
        
        # Calculate spherical excess using l'Huilier's formula
        area = 0.0
        n = len(points_rad)
        
        for i in range(n):
            lat1, lon1 = points_rad[i]
            lat2, lon2 = points_rad[(i + 1) % n]
            
            # Calculate angle
            dlon = lon2 - lon1
            y = math.atan2(
                math.sin(dlon) * math.cos(lat2),
                math.cos(lat1) * math.sin(lat2) - 
                math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
            )
            x = math.atan2(
                math.sin(lat1) * math.sin(dlon),
                math.cos(lat2) + math.cos(lat1) * math.cos(dlon) * math.sin(lat2)
            )
            area += 2 * math.atan2(math.tan(x / 2) * (math.tan(lat1 / 2) + math.tan(lat2 / 2)), 1)
        
        area = abs(area * EARTH_RADIUS_M * EARTH_RADIUS_M / 2.0)
        return area
    
    @staticmethod
    def calculate_area(boundary_points: List[Tuple[float, float]], 
                      is_geographic: bool = True) -> float:
        """
        Calculate polygon area (automatic method selection).
        
        Args:
            boundary_points: List of coordinate tuples
            is_geographic: True for lat/lon, False for xy
        
        Returns:
            Area in square units
        """
        if is_geographic:
            return CoordinateSystem.calculate_area_geographic(boundary_points)
        else:
            return CoordinateSystem.calculate_area_cartesian(boundary_points)
    
    @staticmethod
    def degrees_to_meters(area_degrees_sq: float, 
                         center_lat: float = 0) -> float:
        """
        Convert area in square degrees to square meters.
        
        Args:
            area_degrees_sq: Area in square degrees
            center_lat: Reference latitude for adjustment
        
        Returns:
            Area in square meters
        """
        # 1 degree ≈ 111 km at equator
        lat_m_per_degree = 111000
        lon_m_per_degree = 111000 * math.cos(math.radians(center_lat))
        
        m_per_degree_avg = (lat_m_per_degree + lon_m_per_degree) / 2
        
        return area_degrees_sq * (m_per_degree_avg ** 2)
    
    @staticmethod
    def square_meters_to_hectares(area_m2: float) -> float:
        """Convert square meters to hectares."""
        return area_m2 / 10000
    
    @staticmethod
    def square_meters_to_acres(area_m2: float) -> float:
        """Convert square meters to acres."""
        return area_m2 / 4046.86
    
    @staticmethod
    def square_meters_to_square_km(area_m2: float) -> float:
        """Convert square meters to square kilometers."""
        return area_m2 / 1000000
    
    @staticmethod
    def format_area(area_m2: float) -> Dict[str, float]:
        """
        Return area in multiple units.
        
        Args:
            area_m2: Area in square meters
        
        Returns:
            Dictionary with area in different units
        """
        return {
            "m2": area_m2,
            "km2": CoordinateSystem.square_meters_to_square_km(area_m2),
            "hectares": CoordinateSystem.square_meters_to_hectares(area_m2),
            "acres": CoordinateSystem.square_meters_to_acres(area_m2)
        }
    
    @staticmethod
    def validate_geographic_boundary(boundary_points: List[Tuple[float, float]]) -> Tuple[bool, str]:
        """
        Validate geographic boundary coordinates.
        
        Returns:
            (is_valid, error_message)
        """
        if len(boundary_points) < 3:
            return False, "Boundary must have at least 3 points"
        
        for i, (lat, lon) in enumerate(boundary_points):
            if not (-90 <= lat <= 90):
                return False, f"Point {i}: Latitude {lat} out of range [-90, 90]"
            if not (-180 <= lon <= 180):
                return False, f"Point {i}: Longitude {lon} out of range [-180, 180]"
        
        # Check for duplicate points
        if len(set(boundary_points)) < len(boundary_points):
            return False, "Boundary contains duplicate points"
        
        return True, "Valid"
    
    @staticmethod
    def get_boundary_centroid(boundary_points: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Calculate the centroid of a boundary polygon."""
        if not boundary_points:
            return 0, 0
        
        avg_x = sum(p[0] for p in boundary_points) / len(boundary_points)
        avg_y = sum(p[1] for p in boundary_points) / len(boundary_points)
        
        return avg_x, avg_y
    
    @staticmethod
    def get_boundary_bounds(boundary_points: List[Tuple[float, float]]) -> Dict[str, float]:
        """Get min/max bounds of a boundary."""
        if not boundary_points:
            return {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0}
        
        xs = [p[0] for p in boundary_points]
        ys = [p[1] for p in boundary_points]
        
        return {
            "min_x": min(xs),
            "max_x": max(xs),
            "min_y": min(ys),
            "max_y": max(ys)
        }

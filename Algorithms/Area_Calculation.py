"""
Enhanced Area Calculation with support for both Cartesian and Geographic coordinates.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from GIS.CoordinateSystem import CoordinateSystem
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def calculate_area(boundary: List[Tuple[float, float]], 
                  is_geographic: bool = False) -> float:
    """
    Calculate polygon area using Shoelace Algorithm (Cartesian) or Spherical Excess (Geographic).
    
    Args:
        boundary: List of (x, y) or (lat, lon) tuples
        is_geographic: True if coordinates are geographic (lat/lon), False if Cartesian (x/y)
    
    Returns:
        Area in square units
    
    Complexity:
        Time: O(n) where n = number of boundary points
        Space: O(1) additional space
    """
    if not boundary or len(boundary) < 3:
        logger.warning("Boundary must have at least 3 points")
        return 0.0
    
    # Auto-detect coordinate type if not specified
    if not is_geographic:
        is_geographic = CoordinateSystem.is_geographic(boundary)
    
    try:
        area = CoordinateSystem.calculate_area(boundary, is_geographic)
        logger.info(f"Calculated area: {area:.2f} square units (geographic={is_geographic})")
        return area
    except Exception as e:
        logger.error(f"Error calculating area: {str(e)}")
        return 0.0


def calculate_area_units(area_m2: float) -> Dict[str, float]:
    """
    Convert area from square meters to multiple units.
    
    Args:
        area_m2: Area in square meters
    
    Returns:
        Dictionary with area in different units
    """
    return CoordinateSystem.format_area(area_m2)


def validate_boundary(boundary: List[Tuple[float, float]]) -> Tuple[bool, str]:
    """
    Validate boundary polygon.
    
    Args:
        boundary: List of coordinate tuples
    
    Returns:
        (is_valid, message)
    """
    if not boundary:
        return False, "Boundary is empty"
    
    if len(boundary) < 3:
        return False, "Boundary must have at least 3 points"
    
    # Check for duplicate points
    if len(set(boundary)) < len(boundary):
        return False, "Boundary contains duplicate points"
    
    # Check coordinates validity (simplified)
    for i, (x, y) in enumerate(boundary):
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            return False, f"Point {i}: Invalid coordinate type"
    
    return True, "Valid boundary"
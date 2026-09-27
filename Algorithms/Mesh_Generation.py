"""
Enhanced Mesh Generation with configurable parameters and obstacle awareness.
Generates a coverage mesh inside wildfire boundary for drone mission planning.
"""

import numpy as np
from matplotlib.path import Path
from typing import List, Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def generate_mesh(boundary: List[Tuple[float, float]], 
                 spacing: float = 5,
                 restricted_zones: Optional[List[List[Tuple[float, float]]]] = None,
                 altitude: float = 50,
                 camera_coverage_radius: float = 30) -> List[Tuple[float, float]]:
    """
    Generate a coverage mesh inside wildfire boundary.
    
    Args:
        boundary: List of (x, y) boundary points
        spacing: Grid spacing between mesh points
        restricted_zones: List of polygons representing restricted areas
        altitude: Drone altitude in meters
        camera_coverage_radius: Coverage radius of drone camera
    
    Returns:
        List of mesh node coordinates (x, y)
    
    Complexity:
        Time: O(n*m) where n, m are grid dimensions
        Space: O(n*m) for mesh points
    
    Algorithm:
        1. Create bounding box from boundary
        2. Generate grid with specified spacing
        3. Test each grid point for inclusion in boundary (point-in-polygon)
        4. Exclude points in restricted zones
        5. Return valid mesh points
    """
    if not boundary or len(boundary) < 3:
        logger.warning("Boundary must have at least 3 points")
        return []
    
    try:
        # Create polygon from boundary
        polygon = Path(boundary)
        
        # Get boundary bounding box
        xs = [p[0] for p in boundary]
        ys = [p[1] for p in boundary]
        
        min_x = min(xs)
        max_x = max(xs)
        min_y = min(ys)
        max_y = max(ys)
        
        logger.info(f"Bounding box: X[{min_x:.2f}, {max_x:.2f}], Y[{min_y:.2f}, {max_y:.2f}]")
        
        # Generate mesh points
        mesh_points = []
        
        x = min_x
        while x <= max_x:
            y = min_y
            while y <= max_y:
                point = (x, y)
                
                # Check if point is inside boundary
                if polygon.contains_point(point):
                    
                    # Check if point is in restricted zone
                    in_restricted = False
                    if restricted_zones:
                        for restricted_polygon in restricted_zones:
                            restricted_path = Path(restricted_polygon)
                            if restricted_path.contains_point(point):
                                in_restricted = True
                                break
                    
                    if not in_restricted:
                        mesh_points.append(point)
                
                y += spacing
            
            x += spacing
        
        logger.info(f"Generated {len(mesh_points)} mesh nodes with spacing={spacing}")
        return mesh_points
    
    except Exception as e:
        logger.error(f"Error generating mesh: {str(e)}")
        return []


def optimize_mesh_density(mesh_points: List[Tuple[float, float]],
                         target_density: int) -> List[Tuple[float, float]]:
    """
    Reduce mesh density by removing points while maintaining coverage.
    
    Args:
        mesh_points: Original mesh points
        target_density: Desired number of mesh points
    
    Returns:
        Reduced mesh with approximately target_density points
    """
    if len(mesh_points) <= target_density:
        return mesh_points
    
    # Simple decimation by regular spacing
    step = len(mesh_points) // target_density
    return mesh_points[::step][:target_density]


def get_mesh_statistics(mesh_points: List[Tuple[float, float]]) -> Dict[str, float]:
    """
    Calculate statistics about mesh coverage.
    
    Args:
        mesh_points: List of mesh node coordinates
    
    Returns:
        Dictionary with coverage statistics
    """
    if not mesh_points:
        return {
            "total_nodes": 0,
            "coverage_area": 0,
            "average_spacing": 0,
            "grid_density": 0
        }
    
    points_array = np.array(mesh_points)
    
    # Estimate coverage area (bounding box)
    xs = points_array[:, 0]
    ys = points_array[:, 1]
    coverage_area = (xs.max() - xs.min()) * (ys.max() - ys.min())
    
    # Estimate average spacing between nearby points
    if len(mesh_points) > 1:
        distances = []
        for i in range(min(100, len(mesh_points))):
            point = mesh_points[i]
            # Find 4 nearest neighbors
            dists = [np.sqrt((p[0] - point[0])**2 + (p[1] - point[1])**2) 
                    for p in mesh_points if p != point]
            if dists:
                distances.append(sorted(dists)[0])
        average_spacing = np.mean(distances) if distances else 0
    else:
        average_spacing = 0
    
    return {
        "total_nodes": len(mesh_points),
        "coverage_area": coverage_area,
        "average_spacing": average_spacing,
        "grid_density": len(mesh_points) / max(coverage_area, 1)
    }
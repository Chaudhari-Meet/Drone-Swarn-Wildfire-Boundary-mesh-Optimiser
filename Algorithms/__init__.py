"""Wildfire response algorithms module."""

from .Area_Calculation import calculate_area, calculate_area_units, validate_boundary
from .Mesh_Generation import generate_mesh, optimize_mesh_density, get_mesh_statistics
from .Drone_Allocation import allocate_drones, allocate_drones_by_capability, get_allocation_statistics
from .Path_Planning import (
    calculate_distance, nearest_neighbor_path, two_opt_optimization,
    calculate_path_distance, calculate_sequential_distance,
    risk_aware_path, get_path_statistics
)
from .Performance_Analysis import (
    calculate_sequential_distance, calculate_total_distance,
    calculate_average_distance, calculate_longest_path,
    calculate_shortest_path, calculate_improvement_percentage,
    get_performance_report, calculate_coverage_percentage,
    calculate_load_balance_ratio
)

__all__ = [
    # Area
    "calculate_area",
    "calculate_area_units",
    "validate_boundary",
    
    # Mesh
    "generate_mesh",
    "optimize_mesh_density",
    "get_mesh_statistics",
    
    # Drones
    "allocate_drones",
    "allocate_drones_by_capability",
    "get_allocation_statistics",
    
    # Paths
    "calculate_distance",
    "nearest_neighbor_path",
    "two_opt_optimization",
    "calculate_path_distance",
    "calculate_sequential_distance",
    "risk_aware_path",
    "get_path_statistics",
    
    # Performance
    "calculate_total_distance",
    "calculate_average_distance",
    "calculate_longest_path",
    "calculate_shortest_path",
    "calculate_improvement_percentage",
    "get_performance_report",
    "calculate_coverage_percentage",
    "calculate_load_balance_ratio"
]

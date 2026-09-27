"""
Enhanced Performance Analysis with detailed metrics and comparisons.
"""

from typing import Dict, List, Tuple, Optional
import logging
import time

logger = logging.getLogger(__name__)


def calculate_sequential_distance(nodes: List[Tuple[float, float]]) -> float:
    """
    Calculate distance if nodes are visited in sequence (baseline).
    
    Args:
        nodes: List of nodes
    
    Returns:
        Total sequential distance
    
    Complexity: O(n)
    """
    if len(nodes) < 2:
        return 0.0
    
    total_distance = 0.0
    
    for i in range(len(nodes) - 1):
        x1, y1 = nodes[i]
        x2, y2 = nodes[i + 1]
        
        distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        total_distance += distance
    
    return total_distance


def calculate_total_distance(drone_distances: Dict[int, float]) -> float:
    """
    Calculate total distance across all drones.
    
    Args:
        drone_distances: Dict mapping drone_id to distance
    
    Returns:
        Sum of all drone distances
    
    Complexity: O(n) where n = number of drones
    """
    if not drone_distances:
        return 0.0
    
    return round(sum(drone_distances.values()), 2)


def calculate_average_distance(drone_distances: Dict[int, float]) -> float:
    """
    Calculate average distance per drone.
    
    Args:
        drone_distances: Dict mapping drone_id to distance
    
    Returns:
        Average distance per drone
    
    Complexity: O(n)
    """
    if not drone_distances or len(drone_distances) == 0:
        return 0.0
    
    average = sum(drone_distances.values()) / len(drone_distances)
    return round(average, 2)


def calculate_longest_path(drone_distances: Dict[int, float]) -> float:
    """
    Calculate distance of longest path.
    
    Args:
        drone_distances: Dict mapping drone_id to distance
    
    Returns:
        Maximum distance among all drones
    
    Complexity: O(n)
    """
    if not drone_distances or len(drone_distances) == 0:
        return 0.0
    
    return round(max(drone_distances.values()), 2)


def calculate_shortest_path(drone_distances: Dict[int, float]) -> float:
    """
    Calculate distance of shortest path.
    
    Args:
        drone_distances: Dict mapping drone_id to distance
    
    Returns:
        Minimum distance among all drones
    
    Complexity: O(n)
    """
    if not drone_distances or len(drone_distances) == 0:
        return 0.0
    
    return round(min(drone_distances.values()), 2)


def calculate_improvement_percentage(sequential_distance: float,
                                    optimized_distance: float) -> float:
    """
    Calculate distance improvement percentage.
    
    Args:
        sequential_distance: Baseline distance
        optimized_distance: Optimized distance
    
    Returns:
        Improvement percentage
    
    Formula:
        Improvement % = ((Sequential - Optimized) / Sequential) × 100
    """
    if sequential_distance == 0:
        return 0.0
    
    improvement = ((sequential_distance - optimized_distance) / sequential_distance) * 100
    return round(improvement, 2)


def get_performance_report(sequential_dist: float,
                          nearest_neighbor_dist: float,
                          two_opt_dist: Optional[float] = None,
                          execution_time: Optional[float] = None,
                          num_nodes: int = 0,
                          num_drones: int = 0) -> Dict:
    """
    Generate comprehensive performance report.
    
    Args:
        sequential_dist: Sequential baseline distance
        nearest_neighbor_dist: Nearest Neighbor algorithm distance
        two_opt_dist: 2-opt optimized distance (optional)
        execution_time: Total execution time in seconds
        num_nodes: Number of mesh nodes
        num_drones: Number of drones
    
    Returns:
        Comprehensive performance report dictionary
    """
    report = {
        "baseline": {
            "algorithm": "Sequential",
            "distance": round(sequential_dist, 2),
            "description": "Visiting nodes in given order"
        },
        "nearest_neighbor": {
            "algorithm": "Nearest Neighbor",
            "distance": round(nearest_neighbor_dist, 2),
            "improvement_from_baseline": calculate_improvement_percentage(
                sequential_dist, nearest_neighbor_dist
            ),
            "description": "Greedy heuristic - O(n²) time complexity"
        },
        "summary": {
            "total_nodes": num_nodes,
            "total_drones": num_drones,
            "execution_time_seconds": round(execution_time, 3) if execution_time else None,
            "average_nodes_per_drone": round(num_nodes / max(num_drones, 1), 1) if num_drones > 0 else 0
        }
    }
    
    # Add 2-opt if provided
    if two_opt_dist is not None:
        report["two_opt"] = {
            "algorithm": "2-opt Optimization",
            "distance": round(two_opt_dist, 2),
            "improvement_from_baseline": calculate_improvement_percentage(
                sequential_dist, two_opt_dist
            ),
            "improvement_from_nearest_neighbor": calculate_improvement_percentage(
                nearest_neighbor_dist, two_opt_dist
            ),
            "description": "Local search optimization"
        }
        
        # Update summary with best algorithm
        best_dist = min(nearest_neighbor_dist, two_opt_dist)
        report["best_algorithm"] = "2-opt" if two_opt_dist == best_dist else "Nearest Neighbor"
        report["best_distance"] = round(best_dist, 2)
    else:
        report["best_algorithm"] = "Nearest Neighbor"
        report["best_distance"] = round(nearest_neighbor_dist, 2)
    
    return report


def calculate_coverage_percentage(assigned_nodes: int,
                                 total_nodes: int) -> float:
    """
    Calculate coverage percentage.
    
    Args:
        assigned_nodes: Number of assigned nodes
        total_nodes: Total nodes to cover
    
    Returns:
        Coverage percentage
    """
    if total_nodes == 0:
        return 0.0
    
    coverage = (assigned_nodes / total_nodes) * 100
    return round(coverage, 2)


def calculate_load_balance_ratio(drone_distances: Dict[int, float]) -> float:
    """
    Calculate load balance ratio (0-1, higher is more balanced).
    
    Args:
        drone_distances: Dict of drone distances
    
    Returns:
        Load balance ratio
    """
    if not drone_distances or len(drone_distances) < 2:
        return 1.0
    
    avg_distance = sum(drone_distances.values()) / len(drone_distances)
    max_distance = max(drone_distances.values())
    
    if max_distance == 0:
        return 1.0
    
    ratio = avg_distance / max_distance
    return round(ratio, 3)

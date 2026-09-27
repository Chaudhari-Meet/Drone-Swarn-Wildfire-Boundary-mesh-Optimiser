"""
Enhanced Path Planning with Nearest Neighbor, 2-opt optimization, and risk-aware routing.
"""

import math
from typing import List, Tuple, Dict, Optional, Callable
import logging

logger = logging.getLogger(__name__)


def calculate_distance(point1: Tuple[float, float], 
                      point2: Tuple[float, float]) -> float:
    """
    Calculate Euclidean distance between two points.
    
    Args:
        point1: First point (x, y)
        point2: Second point (x, y)
    
    Returns:
        Distance in units
    
    Complexity: O(1)
    """
    x1, y1 = point1
    x2, y2 = point2
    
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def nearest_neighbor_path(nodes: List[Tuple[float, float]],
                         start_node: Optional[Tuple[float, float]] = None) -> List[Tuple[float, float]]:
    """
    Generate path using Nearest Neighbor heuristic.
    
    Args:
        nodes: List of nodes to visit
        start_node: Starting node (default: first node)
    
    Returns:
        Ordered list of nodes representing the path
    
    Complexity:
        Time: O(n²) where n = number of nodes
        Space: O(n)
    
    Note:
        This is a greedy heuristic, NOT optimal. Finds approximate solution quickly.
    """
    if not nodes:
        return []
    
    if len(nodes) == 1:
        return nodes
    
    try:
        unvisited = nodes.copy()
        
        # Start from specified node or first node
        if start_node and start_node in nodes:
            current = start_node
            unvisited.remove(current)
        else:
            current = unvisited.pop(0)
        
        path = [current]
        
        # Greedily add nearest unvisited node
        while unvisited:
            nearest_node = min(
                unvisited,
                key=lambda node: calculate_distance(current, node)
            )
            
            path.append(nearest_node)
            unvisited.remove(nearest_node)
            current = nearest_node
        
        logger.debug(f"Nearest Neighbor path generated: {len(path)} nodes")
        return path
    
    except Exception as e:
        logger.error(f"Error in nearest neighbor: {str(e)}")
        return nodes


def two_opt_optimization(path: List[Tuple[float, float]],
                        max_iterations: int = 1000,
                        improvement_threshold: float = 0.01) -> List[Tuple[float, float]]:
    """
    Optimize path using 2-opt local search algorithm.
    
    Args:
        path: Initial path
        max_iterations: Maximum number of iterations
        improvement_threshold: Stop if improvement < threshold
    
    Returns:
        Optimized path
    
    Complexity:
        Time: O(n²) per iteration, up to n² iterations worst case, typically much less
        Space: O(n)
    
    Algorithm:
        1. For each pair of edges in the path
        2. Try reversing the segment between them
        3. If total distance decreases, keep the reversal
        4. Repeat until no improvement or max iterations reached
    """
    if len(path) <= 2:
        return path
    
    try:
        improved_path = path.copy()
        best_distance = calculate_path_distance(improved_path)
        improvement_count = 0
        
        for iteration in range(max_iterations):
            improved = False
            
            for i in range(1, len(improved_path) - 2):
                for j in range(i + 1, len(improved_path)):
                    if j - i == 1:
                        continue
                    
                    # Create new path with reversed segment
                    new_path = improved_path[:i] + improved_path[i:j][::-1] + improved_path[j:]
                    new_distance = calculate_path_distance(new_path)
                    
                    # Check if improvement is significant
                    improvement = (best_distance - new_distance) / best_distance
                    
                    if improvement > improvement_threshold:
                        improved_path = new_path
                        best_distance = new_distance
                        improved = True
                        improvement_count += 1
                        break
                
                if improved:
                    break
            
            if not improved:
                break
        
        logger.info(f"2-opt: {improvement_count} improvements, distance reduced to {best_distance:.2f}")
        return improved_path
    
    except Exception as e:
        logger.error(f"Error in 2-opt optimization: {str(e)}")
        return path


def calculate_path_distance(path: List[Tuple[float, float]]) -> float:
    """
    Calculate total distance of a path.
    
    Args:
        path: Ordered list of points
    
    Returns:
        Total distance
    
    Complexity: O(n)
    """
    if len(path) < 2:
        return 0.0
    
    total_distance = 0.0
    
    for i in range(len(path) - 1):
        total_distance += calculate_distance(path[i], path[i + 1])
    
    return total_distance


def calculate_sequential_distance(nodes: List[Tuple[float, float]]) -> float:
    """
    Calculate distance if nodes are visited in sequence (no optimization).
    
    Args:
        nodes: List of nodes in sequence
    
    Returns:
        Distance for sequential traversal
    
    Complexity: O(n)
    """
    return calculate_path_distance(nodes)


def risk_aware_path(nodes: List[Tuple[float, float]],
                   risk_map: Callable[[Tuple[float, float]], float],
                   distance_weight: float = 0.5,
                   risk_weight: float = 0.5) -> List[Tuple[float, float]]:
    """
    Generate path considering both distance and risk.
    
    Args:
        nodes: List of nodes to visit
        risk_map: Function that returns risk score (0-1) for a point
        distance_weight: Weight for distance in cost calculation
        risk_weight: Weight for risk in cost calculation
    
    Returns:
        Path optimized for distance and risk
    """
    if not nodes:
        return []
    
    if len(nodes) == 1:
        return nodes
    
    try:
        unvisited = nodes.copy()
        current = unvisited.pop(0)
        path = [current]
        
        while unvisited:
            best_node = None
            best_cost = float('inf')
            
            for candidate in unvisited:
                distance = calculate_distance(current, candidate)
                risk = risk_map(candidate)
                
                # Combined cost
                cost = (distance_weight * distance + 
                       risk_weight * risk)
                
                if cost < best_cost:
                    best_cost = cost
                    best_node = candidate
            
            if best_node:
                path.append(best_node)
                unvisited.remove(best_node)
                current = best_node
        
        logger.debug(f"Risk-aware path generated: {len(path)} nodes")
        return path
    
    except Exception as e:
        logger.error(f"Error in risk-aware path: {str(e)}")
        return nodes


def get_path_statistics(path: List[Tuple[float, float]]) -> Dict:
    """Calculate statistics about a path."""
    if len(path) < 2:
        return {"total_distance": 0, "num_nodes": len(path), "avg_segment_length": 0}
    
    distances = [calculate_distance(path[i], path[i+1]) for i in range(len(path)-1)]
    
    return {
        "total_distance": sum(distances),
        "num_nodes": len(path),
        "avg_segment_length": sum(distances) / len(distances) if distances else 0,
        "max_segment": max(distances) if distances else 0,
        "min_segment": min(distances) if distances else 0
    }
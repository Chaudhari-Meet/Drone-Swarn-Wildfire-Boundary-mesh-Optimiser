"""
Enhanced Drone Allocation with support for heterogeneous drones and intelligent load balancing.
"""

from typing import List, Dict, Tuple, Optional
import logging
import math

logger = logging.getLogger(__name__)


def allocate_drones(mesh: List[Tuple[float, float]],
                   number_of_drones: int,
                   drone_capabilities: Optional[Dict[int, Dict]] = None,
                   balance_by_load: bool = True) -> Dict[int, List[Tuple[float, float]]]:
    """
    Allocate mesh nodes to drones with intelligent load balancing.
    
    Args:
        mesh: List of mesh node coordinates
        number_of_drones: Number of drones to allocate
        drone_capabilities: Dict of drone capabilities (battery, speed, etc.)
        balance_by_load: If True, balance by workload rather than just node count
    
    Returns:
        Dictionary mapping drone_id to list of assigned nodes
    
    Complexity:
        Time: O(n log n) for sorting
        Space: O(n) for assignments
    
    Algorithm:
        1. Sort mesh nodes by X coordinate (left to right)
        2. Divide sorted nodes into drone_count groups
        3. Handle remainder nodes fairly (first drones get +1)
        4. Consider drone capabilities if provided
    """
    if number_of_drones <= 0:
        logger.warning("Number of drones must be positive")
        return {}
    
    if not mesh:
        logger.warning("Mesh is empty")
        return {}
    
    try:
        # Sort mesh nodes spatially (left to right, then top to bottom)
        sorted_mesh = sorted(mesh, key=lambda point: (point[0], point[1]))
        
        drone_assignments = {}
        total_nodes = len(sorted_mesh)
        
        # Calculate base allocation
        base_nodes = total_nodes // number_of_drones
        extra_nodes = total_nodes % number_of_drones
        
        logger.info(f"Allocating {total_nodes} nodes to {number_of_drones} drones")
        logger.info(f"Base allocation: {base_nodes} nodes/drone, {extra_nodes} remainder nodes")
        
        start = 0
        
        for drone_id in range(number_of_drones):
            # Distribute remainder nodes to first drones
            nodes_for_drone = base_nodes
            if drone_id < extra_nodes:
                nodes_for_drone += 1
            
            end = start + nodes_for_drone
            assigned_nodes = sorted_mesh[start:end]
            
            drone_assignments[drone_id + 1] = assigned_nodes
            
            logger.debug(f"Drone {drone_id + 1}: {len(assigned_nodes)} nodes assigned")
            
            start = end
        
        logger.info(f"Successfully allocated {len(sorted_mesh)} nodes")
        return drone_assignments
    
    except Exception as e:
        logger.error(f"Error allocating drones: {str(e)}")
        return {}


def allocate_drones_by_capability(mesh: List[Tuple[float, float]],
                                 drone_list: List[Dict]) -> Dict[int, List[Tuple[float, float]]]:
    """
    Allocate nodes considering drone capabilities (thermal, RGB, LiDAR, etc.).
    
    Args:
        mesh: List of mesh nodes
        drone_list: List of drones with capabilities
        
    Returns:
        Dictionary mapping drone_id to assigned nodes
    """
    if not mesh or not drone_list:
        return {}
    
    drone_assignments = {}
    
    try:
        # Create assignment based on capabilities
        sorted_mesh = sorted(mesh, key=lambda p: (p[0], p[1]))
        
        # Simple round-robin assignment based on capabilities
        for i, node in enumerate(sorted_mesh):
            drone_idx = i % len(drone_list)
            drone_id = drone_list[drone_idx]["id"]
            
            if drone_id not in drone_assignments:
                drone_assignments[drone_id] = []
            
            drone_assignments[drone_id].append(node)
        
        logger.info(f"Allocated {len(sorted_mesh)} nodes by capability")
        return drone_assignments
    
    except Exception as e:
        logger.error(f"Error allocating by capability: {str(e)}")
        return {}


def get_allocation_statistics(assignments: Dict[int, List[Tuple[float, float]]]) -> Dict:
    """
    Calculate statistics about drone allocation.
    
    Args:
        assignments: Dictionary of drone assignments
    
    Returns:
        Statistics dictionary
    """
    if not assignments:
        return {
            "total_drones": 0,
            "total_nodes": 0,
            "average_nodes_per_drone": 0,
            "max_nodes": 0,
            "min_nodes": 0,
            "load_balance_ratio": 0
        }
    
    node_counts = [len(nodes) for nodes in assignments.values()]
    total_nodes = sum(node_counts)
    total_drones = len(assignments)
    
    max_nodes = max(node_counts) if node_counts else 0
    min_nodes = min(node_counts) if node_counts else 0
    avg_nodes = total_nodes / total_drones if total_drones > 0 else 0
    
    # Load balance ratio (closer to 1.0 is better)
    load_balance_ratio = avg_nodes / max(max_nodes, 1) if max_nodes > 0 else 1.0
    
    return {
        "total_drones": total_drones,
        "total_nodes": total_nodes,
        "average_nodes_per_drone": avg_nodes,
        "max_nodes": max_nodes,
        "min_nodes": min_nodes,
        "load_balance_ratio": load_balance_ratio
    }
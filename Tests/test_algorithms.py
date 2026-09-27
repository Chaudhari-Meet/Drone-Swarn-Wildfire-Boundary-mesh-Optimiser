"""
Comprehensive test suite for wildfire response algorithms.
Tests core functionality with edge cases.
"""

import pytest
import math
from pathlib import Path

# Import algorithms
from Algorithms import (
    calculate_area, validate_boundary, generate_mesh,
    allocate_drones, nearest_neighbor_path, calculate_path_distance,
    two_opt_optimization, calculate_sequential_distance
)


class TestAreaCalculation:
    """Test area calculation algorithms."""
    
    def test_triangle_area(self):
        """Test area calculation for triangle."""
        # Triangle: (0,0), (4,0), (0,3)
        triangle = [(0, 0), (4, 0), (0, 3)]
        area = calculate_area(triangle, is_geographic=False)
        
        # Expected: 1/2 * 4 * 3 = 6
        assert abs(area - 6.0) < 0.01
    
    def test_square_area(self):
        """Test area calculation for square."""
        square = [(0, 0), (5, 0), (5, 5), (0, 5)]
        area = calculate_area(square, is_geographic=False)
        
        # Expected: 5 * 5 = 25
        assert abs(area - 25.0) < 0.01
    
    def test_complex_polygon_area(self):
        """Test area for complex polygon."""
        polygon = [(0, 0), (10, 0), (10, 10), (5, 15), (0, 10)]
        area = calculate_area(polygon, is_geographic=False)
        
        # Should be positive
        assert area > 0
    
    def test_empty_boundary(self):
        """Test with empty boundary."""
        assert calculate_area([]) == 0.0
    
    def test_insufficient_points(self):
        """Test with insufficient points."""
        assert calculate_area([(0, 0), (1, 1)]) == 0.0
    
    def test_degenerate_polygon(self):
        """Test with degenerate polygon (all collinear)."""
        line = [(0, 0), (5, 0), (10, 0)]
        area = calculate_area(line, is_geographic=False)
        
        # Area should be ~0
        assert abs(area) < 0.01


class TestBoundaryValidation:
    """Test boundary validation."""
    
    def test_valid_triangle(self):
        """Test valid triangle boundary."""
        boundary = [(0, 0), (5, 0), (5, 5)]
        is_valid, msg = validate_boundary(boundary)
        
        assert is_valid
    
    def test_insufficient_points(self):
        """Test boundary with insufficient points."""
        boundary = [(0, 0), (1, 1)]
        is_valid, msg = validate_boundary(boundary)
        
        assert not is_valid
    
    def test_duplicate_points(self):
        """Test boundary with duplicate points."""
        boundary = [(0, 0), (5, 0), (5, 5), (0, 0)]
        is_valid, msg = validate_boundary(boundary)
        
        # Should detect duplicates
        assert not is_valid or "duplicate" in msg.lower()


class TestMeshGeneration:
    """Test mesh generation."""
    
    def test_basic_mesh(self):
        """Test basic mesh generation."""
        boundary = [(0, 0), (20, 0), (20, 20), (0, 20)]
        mesh = generate_mesh(boundary, spacing=5)
        
        # Should generate grid points
        assert len(mesh) > 0
        
        # All points should be inside boundary
        for node in mesh:
            assert 0 <= node[0] <= 20
            assert 0 <= node[1] <= 20
    
    def test_fine_mesh(self):
        """Test fine mesh with small spacing."""
        boundary = [(0, 0), (10, 0), (10, 10), (0, 10)]
        
        coarse = generate_mesh(boundary, spacing=5)
        fine = generate_mesh(boundary, spacing=2)
        
        # Fine mesh should have more points
        assert len(fine) > len(coarse)
    
    def test_small_boundary(self):
        """Test mesh for very small boundary."""
        boundary = [(0, 0), (1, 0), (1, 1), (0, 1)]
        mesh = generate_mesh(boundary, spacing=0.5)
        
        # Should generate some points
        assert len(mesh) > 0
    
    def test_empty_boundary(self):
        """Test mesh with empty boundary."""
        mesh = generate_mesh([], spacing=5)
        
        assert len(mesh) == 0


class TestDroneAllocation:
    """Test drone allocation."""
    
    def test_basic_allocation(self):
        """Test basic drone allocation."""
        mesh = [(i, j) for i in range(0, 20, 5) for j in range(0, 20, 5)]
        assignments = allocate_drones(mesh, 4)
        
        # Should have 4 drones
        assert len(assignments) == 4
        
        # All nodes should be assigned
        total_assigned = sum(len(nodes) for nodes in assignments.values())
        assert total_assigned == len(mesh)
    
    def test_uneven_allocation(self):
        """Test allocation with uneven node distribution."""
        mesh = [(i, 0) for i in range(10)]
        assignments = allocate_drones(mesh, 3)
        
        # Should distribute as evenly as possible
        node_counts = [len(nodes) for nodes in assignments.values()]
        assert max(node_counts) - min(node_counts) <= 1
    
    def test_single_drone(self):
        """Test allocation to single drone."""
        mesh = [(i, 0) for i in range(10)]
        assignments = allocate_drones(mesh, 1)
        
        assert len(assignments) == 1
        assert len(assignments[1]) == len(mesh)
    
    def test_more_drones_than_nodes(self):
        """Test with more drones than nodes."""
        mesh = [(0, 0), (1, 1), (2, 2)]
        assignments = allocate_drones(mesh, 5)
        
        # Should still allocate
        total = sum(len(nodes) for nodes in assignments.values())
        assert total == len(mesh)


class TestPathPlanning:
    """Test path planning algorithms."""
    
    def test_nearest_neighbor_simple(self):
        """Test nearest neighbor on simple path."""
        nodes = [(0, 0), (1, 0), (2, 0), (3, 0)]
        path = nearest_neighbor_path(nodes)
        
        # Should visit all nodes
        assert len(path) == len(nodes)
        assert set(path) == set(nodes)
    
    def test_nearest_neighbor_2d(self):
        """Test nearest neighbor on 2D points."""
        nodes = [(0, 0), (1, 1), (2, 0), (1, 2)]
        path = nearest_neighbor_path(nodes)
        
        # Should be valid path
        assert len(path) == 4
        assert len(set(path)) == 4  # No duplicates
    
    def test_empty_nodes(self):
        """Test with empty nodes."""
        path = nearest_neighbor_path([])
        assert len(path) == 0
    
    def test_single_node(self):
        """Test with single node."""
        path = nearest_neighbor_path([(0, 0)])
        assert path == [(0, 0)]
    
    def test_path_distance(self):
        """Test path distance calculation."""
        path = [(0, 0), (3, 0), (3, 4)]
        distance = calculate_path_distance(path)
        
        # Expected: 3 + 4 = 7
        assert abs(distance - 7.0) < 0.01
    
    def test_two_opt_optimization(self):
        """Test 2-opt optimization."""
        # Simple path with obvious improvement
        path = [(0, 0), (2, 0), (2, 2), (0, 2)]
        
        optimized = two_opt_optimization(path, max_iterations=100)
        
        # Optimized should be same or better distance
        original_dist = calculate_path_distance(path)
        optimized_dist = calculate_path_distance(optimized)
        
        assert optimized_dist <= original_dist + 0.01


class TestPerformanceAnalysis:
    """Test performance analysis."""
    
    def test_sequential_distance(self):
        """Test sequential distance calculation."""
        nodes = [(0, 0), (1, 0), (1, 1), (0, 1)]
        seq_dist = calculate_sequential_distance(nodes)
        
        # Expected: 1 + 1 + sqrt(2) + 1 ≈ 3.414
        assert 3.0 < seq_dist < 3.5
    
    def test_empty_sequential(self):
        """Test sequential distance with empty nodes."""
        assert calculate_sequential_distance([]) == 0.0
    
    def test_single_node_sequential(self):
        """Test sequential distance with single node."""
        assert calculate_sequential_distance([(0, 0)]) == 0.0


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_very_large_mesh(self):
        """Test with very large mesh."""
        boundary = [(0, 0), (100, 0), (100, 100), (0, 100)]
        mesh = generate_mesh(boundary, spacing=1)
        
        # Should handle large mesh
        assert len(mesh) > 1000
    
    def test_very_small_spacing(self):
        """Test mesh with very small spacing."""
        boundary = [(0, 0), (1, 0), (1, 1), (0, 1)]
        mesh = generate_mesh(boundary, spacing=0.1)
        
        # Should generate many points
        assert len(mesh) > 50
    
    def test_concave_polygon(self):
        """Test with concave polygon."""
        # L-shaped polygon
        concave = [(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2)]
        mesh = generate_mesh(concave, spacing=0.5)
        
        # Should generate mesh respecting concavity
        assert len(mesh) > 0
    
    def test_path_with_clusters(self):
        """Test nearest neighbor with clustered points."""
        # Three clusters
        cluster1 = [(i, 0) for i in range(3)]
        cluster2 = [(i, 10) for i in range(3)]
        cluster3 = [(i, 20) for i in range(3)]
        
        nodes = cluster1 + cluster2 + cluster3
        path = nearest_neighbor_path(nodes)
        
        # Should find reasonable path
        assert len(path) == 9


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_optimization_workflow(self):
        """Test complete mesh -> allocation -> optimization workflow."""
        # Create boundary
        boundary = [(0, 0), (50, 0), (50, 50), (0, 50)]
        
        # Generate mesh
        mesh = generate_mesh(boundary, spacing=10)
        assert len(mesh) > 0
        
        # Allocate drones
        assignments = allocate_drones(mesh, 5)
        assert len(assignments) == 5
        
        # Plan paths for each drone
        for drone_id, nodes in assignments.items():
            path = nearest_neighbor_path(nodes)
            distance = calculate_path_distance(path)
            
            assert len(path) == len(nodes)
            assert distance >= 0
    
    def test_performance_comparison(self):
        """Test performance comparison workflow."""
        nodes = [(i % 10, i // 10) for i in range(20)]
        
        # Sequential
        seq_dist = calculate_sequential_distance(nodes)
        
        # Optimized
        nn_path = nearest_neighbor_path(nodes)
        opt_dist = calculate_path_distance(nn_path)
        
        # Both should be valid
        assert seq_dist > 0
        assert opt_dist > 0
        
        # Calculate improvement
        if seq_dist > 0:
            improvement = (seq_dist - opt_dist) / seq_dist * 100
            assert -5 < improvement < 100  # Some reasonable bounds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

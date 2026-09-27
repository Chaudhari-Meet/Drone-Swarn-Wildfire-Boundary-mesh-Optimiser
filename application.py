"""
Main Application Class - Drone Swarm Wildfire Response System
Orchestrates all modules and data flow for wildfire monitoring and drone swarm optimization.
"""

import logging
import time
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path

from config import get_logger, PROJECT_ROOT, DATA_DIR, RESULTS_DIR, DEFAULT_MODE
from config import RISK_WEIGHTS, FEATURES

from Data.DataSource import DataSource, FireBoundary, FireObservation
from Data.SimulationDataSource import SimulationDataSource

from GIS.CoordinateSystem import CoordinateSystem

from Algorithms import (
    calculate_area, validate_boundary, generate_mesh,
    allocate_drones, nearest_neighbor_path, two_opt_optimization,
    calculate_path_distance, calculate_sequential_distance,
    get_performance_report, calculate_total_distance
)

from Drone import Drone, DroneType, DroneCapabilities, DroneStatus

from Analysis import calculate_risk_score, generate_risk_zones, calculate_path_risk

from Detection import AnimalDetector, PersonDetector

from Rescue import FirefighterRoute, RouteObjective


class WildfireResponseSystem:
    """
    Main application class for Drone Swarm Wildfire Response System.
    
    Responsibilities:
    - Manage data sources (satellite, real drones, historical, images, simulation)
    - Orchestrate fire boundary generation
    - Manage mesh generation and drone allocation
    - Execute path planning and optimization
    - Coordinate risk analysis
    - Execute detection and sensor fusion
    - Generate firefighter route recommendations
    - Provide comprehensive dashboard and reporting
    """
    
    def __init__(self, mode: str = DEFAULT_MODE):
        """
        Initialize the wildfire response system.
        
        Args:
            mode: Operating mode (simulation, satellite, real_drone, historical, image_upload)
        """
        self.logger = get_logger(self.__class__.__name__)
        self.mode = mode
        
        # Data sources
        self.active_data_source: Optional[DataSource] = None
        self.data_sources: Dict[str, DataSource] = {}
        
        # Fire data
        self.fire_observations: List[FireObservation] = []
        self.fire_boundary: Optional[FireBoundary] = None
        self.fire_area_m2: float = 0
        self.fire_area_units = {}
        
        # Mesh and allocation
        self.mesh_nodes: List[Tuple[float, float]] = []
        self.mesh_statistics: Dict = {}
        self.drone_assignments: Dict = {}
        self.allocation_statistics: Dict = {}
        
        # Drones
        self.drones: Dict[int, Drone] = {}
        self.drone_paths: Dict[int, List[Tuple[float, float]]] = {}
        self.drone_distances: Dict[int, float] = {}
        
        # Performance
        self.sequential_distance = 0
        self.nearest_neighbor_distance = 0
        self.two_opt_distance = 0
        self.performance_report: Dict = {}
        self.optimization_runtime = 0
        
        # Risk and safety
        self.risk_zones = []
        self.path_risk_analysis: Dict = {}
        
        # Detection
        self.detections = []
        self.animal_detector = AnimalDetector()
        self.person_detector = PersonDetector()
        
        # Firefighter routing
        self.firefighter_routes = {}
        
        # State tracking
        self.mission_start_time = None
        self.last_update_time = None
        self.system_status = "INITIALIZED"
        
        # Initialize data sources
        self._initialize_data_sources()
        
        self.logger.info(f"System initialized in {mode} mode")
    
    def _initialize_data_sources(self):
        """Initialize available data sources."""
        # Simulation source (always available)
        simulation_source = SimulationDataSource("demo_wildfire")
        self.data_sources["simulation"] = simulation_source
        
        # Set default to simulation for demo
        if self.mode == "simulation":
            self.active_data_source = simulation_source
            self.logger.info("Active data source: SIMULATION")
        
        self.logger.info(f"Initialized {len(self.data_sources)} data sources")
    
    def set_data_source(self, source_name: str, initialize_params: Dict = None) -> bool:
        """
        Set the active data source.
        
        Args:
            source_name: Name of data source to activate
            initialize_params: Configuration parameters
        
        Returns:
            Success status
        """
        if source_name not in self.data_sources:
            self.logger.error(f"Unknown data source: {source_name}")
            return False
        
        source = self.data_sources[source_name]
        
        if not source.is_available():
            self.logger.error(f"Data source not available: {source_name}")
            return False
        
        if initialize_params:
            if not source.initialize(**initialize_params):
                self.logger.error(f"Failed to initialize {source_name}")
                return False
        
        self.active_data_source = source
        self.logger.info(f"Active data source changed to: {source.name}")
        
        return True
    
    def load_fire_data(self) -> bool:
        """
        Load fire data from active source.
        
        Returns:
            Success status
        """
        if not self.active_data_source:
            self.logger.error("No active data source selected")
            return False
        
        try:
            self.logger.info(f"Loading fire data from {self.active_data_source.name}")
            
            # Get observations
            self.fire_observations = self.active_data_source.get_fire_observations()
            self.logger.info(f"Loaded {len(self.fire_observations)} fire observations")
            
            # Get boundary
            self.fire_boundary = self.active_data_source.get_fire_boundary()
            if self.fire_boundary:
                self.logger.info(f"Fire boundary generated: {len(self.fire_boundary.boundary_points)} points")
                
                # Validate boundary
                is_valid, message = validate_boundary(self.fire_boundary.boundary_points)
                if not is_valid:
                    self.logger.warning(f"Boundary validation: {message}")
                    return False
            else:
                self.logger.warning("No fire boundary available")
                return False
            
            self.system_status = "FIRE_DATA_LOADED"
            self.last_update_time = datetime.now()
            return True
        
        except Exception as e:
            self.logger.error(f"Error loading fire data: {str(e)}")
            return False
    
    def process_fire_data(self) -> bool:
        """
        Process loaded fire data (area calculation, validation).
        
        Returns:
            Success status
        """
        if not self.fire_boundary:
            self.logger.error("No fire boundary to process")
            return False
        
        try:
            # Calculate area
            area_cartesian = calculate_area(
                self.fire_boundary.boundary_points,
                is_geographic=False
            )
            
            self.fire_area_m2 = area_cartesian  # Simplified
            self.fire_area_units = {
                "m2": self.fire_area_m2,
                "km2": self.fire_area_m2 / 1000000,
                "hectares": self.fire_area_m2 / 10000,
                "acres": self.fire_area_m2 / 4046.86
            }
            
            self.logger.info(f"Fire area calculated: {self.fire_area_units['hectares']:.2f} hectares")
            
            self.system_status = "FIRE_DATA_PROCESSED"
            return True
        
        except Exception as e:
            self.logger.error(f"Error processing fire data: {str(e)}")
            return False
    
    def generate_mesh_coverage(self, spacing: float = 5, altitude: float = 50) -> bool:
        """
        Generate coverage mesh for drone path planning.
        
        Args:
            spacing: Grid spacing in units
            altitude: Drone operating altitude
        
        Returns:
            Success status
        """
        if not self.fire_boundary:
            self.logger.error("No fire boundary for mesh generation")
            return False
        
        try:
            self.mesh_nodes = generate_mesh(
                self.fire_boundary.boundary_points,
                spacing=spacing
            )
            
            if not self.mesh_nodes:
                self.logger.warning("No mesh nodes generated")
                return False
            
            self.logger.info(f"Generated {len(self.mesh_nodes)} mesh nodes")
            
            self.system_status = "MESH_GENERATED"
            return True
        
        except Exception as e:
            self.logger.error(f"Error generating mesh: {str(e)}")
            return False
    
    def allocate_drones(self, num_drones: int) -> bool:
        """
        Allocate mesh nodes to drones.
        
        Args:
            num_drones: Number of drones
        
        Returns:
            Success status
        """
        if not self.mesh_nodes:
            self.logger.error("No mesh nodes to allocate")
            return False
        
        try:
            self.drone_assignments = allocate_drones(
                self.mesh_nodes,
                num_drones
            )
            
            if not self.drone_assignments:
                self.logger.warning("No drone allocations generated")
                return False
            
            self.logger.info(f"Allocated {len(self.drone_assignments)} drones")
            
            # Create drone objects
            self._create_drones(num_drones)
            
            # Assign nodes to drones
            for drone_id, nodes in self.drone_assignments.items():
                if drone_id in self.drones:
                    self.drones[drone_id].set_assigned_nodes(nodes)
            
            self.system_status = "DRONES_ALLOCATED"
            return True
        
        except Exception as e:
            self.logger.error(f"Error allocating drones: {str(e)}")
            return False
    
    def _create_drones(self, num_drones: int):
        """Create virtual drone objects."""
        self.drones = {}
        
        capabilities = DroneCapabilities(
            thermal_camera=True,
            rgb_camera=True,
            lidar=True,
            max_altitude_m=500,
            max_speed_ms=20,
            max_flight_time_s=1800
        )
        
        for i in range(num_drones):
            drone = Drone(
                drone_id=i + 1,
                name=f"Virtual Drone {i + 1}",
                drone_type=DroneType.VIRTUAL,
                capabilities=capabilities
            )
            self.drones[i + 1] = drone
        
        self.logger.info(f"Created {num_drones} virtual drones")
    
    def optimize_drone_paths(self, use_two_opt: bool = True) -> bool:
        """
        Optimize drone paths using nearest neighbor and optionally 2-opt.
        
        Args:
            use_two_opt: Whether to apply 2-opt optimization
        
        Returns:
            Success status
        """
        if not self.drone_assignments or not self.drones:
            self.logger.error("No drone assignments for path optimization")
            return False
        
        try:
            start_time = time.time()
            
            self.drone_paths = {}
            self.drone_distances = {}
            sequential_distances = {}
            
            # Plan paths for each drone
            for drone_id, nodes in self.drone_assignments.items():
                # Sequential path (baseline)
                seq_distance = calculate_sequential_distance(nodes)
                sequential_distances[drone_id] = seq_distance
                
                # Nearest Neighbor
                nn_path = nearest_neighbor_path(nodes)
                nn_distance = calculate_path_distance(nn_path)
                
                # 2-opt optimization
                if use_two_opt and len(nn_path) > 3:
                    opt_path = two_opt_optimization(nn_path)
                    opt_distance = calculate_path_distance(opt_path)
                    self.two_opt_distance += opt_distance
                else:
                    opt_path = nn_path
                    opt_distance = nn_distance
                
                self.drone_paths[drone_id] = opt_path
                self.drone_distances[drone_id] = opt_distance
                self.nearest_neighbor_distance += nn_distance
                self.sequential_distance += seq_distance
                
                # Set path in drone
                if drone_id in self.drones:
                    self.drones[drone_id].set_planned_path(opt_path)
                
                self.logger.debug(
                    f"Drone {drone_id}: Sequential={seq_distance:.2f}, "
                    f"NN={nn_distance:.2f}, Opt={opt_distance:.2f}"
                )
            
            self.optimization_runtime = time.time() - start_time
            
            # Generate performance report
            self.performance_report = get_performance_report(
                self.sequential_distance,
                self.nearest_neighbor_distance,
                self.two_opt_distance if use_two_opt else None,
                self.optimization_runtime,
                len(self.mesh_nodes),
                len(self.drones)
            )
            
            self.logger.info(
                f"Path optimization complete. "
                f"Sequential: {self.sequential_distance:.2f}, "
                f"NN: {self.nearest_neighbor_distance:.2f}, "
                f"Improvement: {calculate_total_distance(self.drone_distances):.2f}"
            )
            
            self.system_status = "PATHS_OPTIMIZED"
            return True
        
        except Exception as e:
            self.logger.error(f"Error optimizing paths: {str(e)}")
            return False
    
    def analyze_risk(self) -> bool:
        """
        Analyze risk in fire area and along drone paths.
        
        Returns:
            Success status
        """
        if not self.fire_boundary:
            self.logger.error("No fire boundary for risk analysis")
            return False
        
        try:
            # Generate risk zones
            fire_observations = [
                (obs.latitude, obs.longitude)
                for obs in self.fire_observations[:20]
            ]
            
            self.risk_zones = generate_risk_zones(
                self.fire_boundary.boundary_points,
                fire_observations
            )
            
            # Analyze path risk for each drone
            self.path_risk_analysis = {}
            for drone_id, path in self.drone_paths.items():
                risk_analysis = calculate_path_risk(path, self.risk_zones, RISK_WEIGHTS)
                self.path_risk_analysis[drone_id] = risk_analysis
                
                self.logger.debug(
                    f"Drone {drone_id} path risk: {risk_analysis['average_segment_risk']:.2f}"
                )
            
            self.logger.info(f"Risk analysis complete for {len(self.risk_zones)} zones")
            self.system_status = "RISK_ANALYZED"
            return True
        
        except Exception as e:
            self.logger.error(f"Error analyzing risk: {str(e)}")
            return False
    
    def detect_objects(self) -> bool:
        """
        Detect animals and persons using thermal and RGB fusion.
        
        Returns:
            Success status
        """
        try:
            # Simulate detections from random mesh nodes
            import random
            
            for _ in range(min(3, len(self.mesh_nodes))):
                if random.random() > 0.7:
                    node = random.choice(self.mesh_nodes)
                    drone_id = random.choice(list(self.drones.keys()))
                    
                    # Animal detection
                    if random.random() > 0.5:
                        thermal = self.animal_detector.detect_from_thermal(
                            node[0], node[1], 50, drone_id, 0.8
                        )
                        rgb = self.animal_detector.detect_from_rgb(
                            node[0], node[1], 50, drone_id, 0.75
                        )
                        if thermal and rgb:
                            fused = self.animal_detector.sensor_fusion(thermal, rgb)
                            if fused:
                                self.detections.append(fused)
                    
                    # Person detection
                    else:
                        thermal = self.person_detector.detect_from_thermal(
                            node[0], node[1], 50, drone_id, 0.85
                        )
                        rgb = self.person_detector.detect_from_rgb(
                            node[0], node[1], 50, drone_id, 0.80
                        )
                        if thermal and rgb:
                            fused = self.person_detector.sensor_fusion(thermal, rgb)
                            if fused:
                                self.detections.append(fused)
            
            self.logger.info(f"Object detection: {len(self.detections)} detections found")
            self.system_status = "DETECTION_COMPLETE"
            return True
        
        except Exception as e:
            self.logger.error(f"Error in object detection: {str(e)}")
            return False
    
    def generate_firefighter_routes(self, start_point: Tuple[float, float],
                                   end_point: Tuple[float, float]) -> bool:
        """
        Generate firefighter route recommendations.
        
        Args:
            start_point: Firefighter start position
            end_point: Target position
        
        Returns:
            Success status
        """
        if not self.fire_boundary:
            self.logger.error("No fire boundary for firefighter routing")
            return False
        
        try:
            router = FirefighterRoute()
            
            self.firefighter_routes = router.generate_routes(
                start_point,
                end_point,
                self.fire_boundary.boundary_points,
                self.risk_zones
            )
            
            self.logger.info(f"Generated {len(self.firefighter_routes)} firefighter route options")
            self.logger.warning("REMINDER: All routes are RECOMMENDATIONS ONLY. "
                              "Humans make final navigation decisions.")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error generating firefighter routes: {str(e)}")
            return False
    
    def run_full_mission(self, num_drones: int = 10, mesh_spacing: float = 5) -> bool:
        """
        Run complete mission pipeline.
        
        Args:
            num_drones: Number of drones to use
            mesh_spacing: Mesh grid spacing
        
        Returns:
            Success status
        """
        self.logger.info("="*60)
        self.logger.info("STARTING FULL WILDFIRE RESPONSE MISSION")
        self.logger.info("="*60)
        
        self.mission_start_time = datetime.now()
        
        # Step 1: Load fire data
        self.logger.info("\n[1/7] Loading fire data...")
        if not self.load_fire_data():
            return False
        
        # Step 2: Process fire data
        self.logger.info("\n[2/7] Processing fire data...")
        if not self.process_fire_data():
            return False
        
        # Step 3: Generate mesh
        self.logger.info(f"\n[3/7] Generating mesh coverage (spacing={mesh_spacing})...")
        if not self.generate_mesh_coverage(spacing=mesh_spacing):
            return False
        
        # Step 4: Allocate drones
        self.logger.info(f"\n[4/7] Allocating {num_drones} drones...")
        if not self.allocate_drones(num_drones):
            return False
        
        # Step 5: Optimize paths
        self.logger.info("\n[5/7] Optimizing drone paths (NN + 2-opt)...")
        if not self.optimize_drone_paths(use_two_opt=True):
            return False
        
        # Step 6: Analyze risk
        self.logger.info("\n[6/7] Analyzing risk zones...")
        if not self.analyze_risk():
            return False
        
        # Step 7: Detect objects
        self.logger.info("\n[7/7] Detecting animals and persons...")
        if not self.detect_objects():
            return False
        
        self.system_status = "MISSION_COMPLETE"
        self.logger.info("\n" + "="*60)
        self.logger.info("MISSION COMPLETE")
        self.logger.info("="*60)
        
        return True
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status."""
        return {
            "mode": self.mode,
            "status": self.system_status,
            "data_source": self.active_data_source.name if self.active_data_source else None,
            "fire_observations": len(self.fire_observations),
            "fire_area_hectares": self.fire_area_units.get("hectares", 0),
            "mesh_nodes": len(self.mesh_nodes),
            "drones": len(self.drones),
            "drone_assignments": len(self.drone_assignments),
            "optimized_distance": calculate_total_distance(self.drone_distances),
            "improvement_percent": (
                (self.sequential_distance - calculate_total_distance(self.drone_distances)) /
                max(self.sequential_distance, 1) * 100
            ),
            "detections": len(self.detections),
            "risk_zones": len(self.risk_zones),
            "last_update": self.last_update_time.isoformat() if self.last_update_time else None
        }
    
    def export_report(self, filename: str = "wildfire_mission_report.json") -> bool:
        """Export mission report to JSON."""
        try:
            report = {
                "mission_timestamp": self.mission_start_time.isoformat() if self.mission_start_time else None,
                "system_status": self.get_system_status(),
                "fire_data": {
                    "observations": len(self.fire_observations),
                    "boundary_points": len(self.fire_boundary.boundary_points) if self.fire_boundary else 0,
                    "area_hectares": self.fire_area_units.get("hectares", 0)
                },
                "mesh": {
                    "total_nodes": len(self.mesh_nodes),
                    "grid_spacing": 5  # Default
                },
                "drones": {
                    "total_drones": len(self.drones),
                    "assignments": len(self.drone_assignments),
                    "total_path_distance_m": calculate_total_distance(self.drone_distances)
                },
                "performance": self.performance_report,
                "detections": len(self.detections),
                "risk_zones": len(self.risk_zones)
            }
            
            filepath = RESULTS_DIR / filename
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Report exported to {filepath}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting report: {str(e)}")
            return False

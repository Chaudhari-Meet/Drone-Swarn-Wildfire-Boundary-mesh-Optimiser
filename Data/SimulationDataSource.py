"""
Simulation/Virtual Data Source for testing and demonstration.
Generates realistic but synthetic wildfire data.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timedelta
from .DataSource import DataSource, FireObservation, FireBoundary
import logging

logger = logging.getLogger(__name__)


class SimulationDataSource(DataSource):
    """
    Virtual data source that simulates wildfire observations.
    Generates synthetic but realistic data for testing and demonstration.
    
    Available Scenarios:
    - small_fire: 20 observations, 1.0 degree radius
    - medium_fire: 50 observations, 2.0 degree radius
    - large_fire: 100 observations, 4.0 degree radius
    - extreme_fire: 200 observations, 8.0 degree radius
    - wildland_urban_interface: Mix of urban and wildland features
    - coastal_fire: Fire near coastline with geographic constraints
    - mountain_fire: High-altitude fire with terrain complexity
    """
    
    def __init__(self, scenario_name: str = "medium_fire"):
        super().__init__(
            name=f"Simulated Fire - {scenario_name}",
            source_type="simulation"
        )
        self.scenario_name = scenario_name
        self.center_lat = 35.0
        self.center_lon = -120.0
        self.num_observations = 50
        self.boundary_radius = 2.0  # degrees
        self.available = True
        
        # Simulation realism parameters
        self.time_progression = True  # Hotspots evolve over time
        self.wind_direction = 270  # Degrees (0-360, 270 = westerly)
        self.spread_direction = None  # Will be set based on wind
        self.fire_intensity_variation = True  # Temperature varies by location
        self.background_noise = 0.1  # False positive rate for observations
    
    def is_available(self) -> bool:
        """Simulation is always available."""
        return self.available
    
    def initialize(self, **kwargs) -> bool:
        """Initialize simulation with optional parameters."""
        try:
            if "center_lat" in kwargs:
                self.center_lat = kwargs["center_lat"]
            if "center_lon" in kwargs:
                self.center_lon = kwargs["center_lon"]
            if "num_observations" in kwargs:
                self.num_observations = kwargs["num_observations"]
            if "boundary_radius" in kwargs:
                self.boundary_radius = kwargs["boundary_radius"]
            
            logger.info(f"Initialized {self.name}")
            return True
        except Exception as e:
            logger.error(f"Error initializing simulation: {str(e)}")
            return False
    
    def _generate_clustered_points(self, 
                                   center: Tuple[float, float],
                                   num_points: int,
                                   radius: float) -> List[Tuple[float, float]]:
        """
        Generate clustered points around a center for realistic fire hotspots.
        
        Features:
        - Main cluster at fire center
        - Secondary clusters along wind spread direction
        - More intense observations in downwind direction
        - Realistic fire progression patterns
        """
        points = []
        
        # Wind direction in radians (convert from degrees)
        import math
        wind_rad = math.radians(self.spread_direction or self.wind_direction)
        
        # Main cluster (strongest fire)
        main_cluster_size = int(num_points * 0.6)
        for _ in range(main_cluster_size):
            angle = np.random.uniform(0, 2 * np.pi)
            r = np.random.uniform(0, radius * 0.4)
            lat = center[0] + r * np.cos(angle)
            lon = center[1] + r * np.sin(angle)
            points.append((lat, lon))
        
        # Secondary clusters downwind (fire spread direction)
        num_secondary_clusters = 3
        secondary_cluster_size = (num_points - main_cluster_size) // num_secondary_clusters
        
        for cluster_idx in range(num_secondary_clusters):
            # Position along wind direction
            secondary_distance = radius * 0.6 * (cluster_idx + 1) / num_secondary_clusters
            secondary_center_lat = center[0] + secondary_distance * np.sin(wind_rad)
            secondary_center_lon = center[1] + secondary_distance * np.cos(wind_rad)
            
            # Points in each secondary cluster
            for _ in range(secondary_cluster_size):
                angle = np.random.uniform(0, 2 * np.pi)
                r = np.random.uniform(0, radius * 0.2)
                lat = secondary_center_lat + r * np.cos(angle)
                lon = secondary_center_lon + r * np.sin(angle)
                points.append((lat, lon))
        
        # Add background noise (false positives)
        if self.background_noise > 0:
            noise_points = int(num_points * self.background_noise)
            for _ in range(noise_points):
                angle = np.random.uniform(0, 2 * np.pi)
                r = np.random.uniform(radius * 0.5, radius * 1.2)
                lat = center[0] + r * np.cos(angle)
                lon = center[1] + r * np.sin(angle)
                points.append((lat, lon))
        
        return points[:num_points]
    
    def get_fire_observations(self,
                             location: Optional[Tuple[float, float]] = None,
                             radius_km: float = 100,
                             time_range_hours: int = 24) -> List[FireObservation]:
        """
        Generate simulated fire observations with realistic properties.
        
        Features:
        - Hotspots cluster around fire center
        - Wind-driven spread pattern
        - Varying fire intensity (temperature)
        - Temporal progression (older observations fade)
        - Fire Radiative Power (FRP) correlation with temperature
        """
        observations = []
        
        if location is None:
            location = (self.center_lat, self.center_lon)
        
        # Convert radius_km to approximate degrees (1 degree ≈ 111 km)
        radius_degrees = radius_km / 111.0
        
        # Generate hotspot locations with wind bias
        points = self._generate_clustered_points(
            location,
            self.num_observations,
            min(radius_degrees, self.boundary_radius)
        )
        
        # Generate observations with varying timestamps and fire properties
        now = datetime.now()
        for i, (lat, lon) in enumerate(points):
            # Stagger observations over time range (older fires have older observations)
            time_offset = timedelta(
                hours=np.random.uniform(-time_range_hours, 0)
            )
            timestamp = now + time_offset
            
            # Confidence decreases with time (older observations are less certain)
            time_decay = 1.0 - (abs(time_offset.total_seconds()) / (time_range_hours * 3600))
            confidence = np.clip(0.7 + 0.3 * time_decay, 0.5, 1.0)
            
            # Fire intensity varies by location
            if self.fire_intensity_variation:
                # Strongest at center, weaker at edges
                import math
                dist_from_center = math.sqrt((lat - location[0])**2 + (lon - location[1])**2)
                intensity_factor = max(0.3, 1.0 - (dist_from_center / self.boundary_radius) * 0.7)
                temperature = np.random.uniform(200, 800) * intensity_factor
            else:
                temperature = np.random.uniform(200, 800)
            
            # Fire Radiative Power (FRP) correlates with temperature
            # FRP (MW) ≈ (Temperature - ambient) * area_factor
            frp = max(10, (temperature - 50) / 10.0 + np.random.uniform(-50, 50))
            
            observation = FireObservation(
                latitude=lat,
                longitude=lon,
                timestamp=timestamp,
                confidence=confidence,
                temperature=temperature,
                fire_radiative_power=frp,
                source="simulated",
                metadata={
                    "platform": "SIMULATED",
                    "detection_type": "thermal",
                    "scenario": self.scenario_name,
                    "wind_direction": self.wind_direction,
                    "intensity_factor": intensity_factor if self.fire_intensity_variation else 1.0
                }
            )
            observations.append(observation)
        
        self.observations = observations
        self.last_update = now
        logger.info(f"Generated {len(observations)} simulated fire observations")
        logger.info(f"  Scenario: {self.scenario_name} | Wind: {self.wind_direction}° | Temperature range: {min(obs.temperature or 0 for obs in observations):.0f}-{max(obs.temperature or 0 for obs in observations):.0f}K")
        
        return observations
    
    def get_fire_boundary(self, location: Optional[Tuple[float, float]] = None) -> Optional[FireBoundary]:
        """Generate a simulated fire boundary using convex hull of observations."""
        if location is None:
            location = (self.center_lat, self.center_lon)
        
        if not self.observations:
            self.get_fire_observations(location)
        
        # Generate boundary points using alpha shape or convex hull concept
        # For simplicity, we create an elliptical boundary
        points = []
        num_boundary_points = 20
        
        # Extract observation points
        obs_points = np.array([(obs.latitude, obs.longitude) for obs in self.observations])
        
        if len(obs_points) < 3:
            logger.warning("Not enough observations to generate boundary")
            return None
        
        # Simple approach: create convex polygon around observations
        center = obs_points.mean(axis=0)
        distances = np.linalg.norm(obs_points - center, axis=1)
        max_distance = distances.max() * 1.2  # Add 20% buffer
        
        # Create boundary points in circle around center
        for i in range(num_boundary_points):
            angle = 2 * np.pi * i / num_boundary_points
            lat = center[0] + max_distance * np.sin(angle)
            lon = center[1] + max_distance * np.cos(angle)
            
            # Add some irregularity to boundary
            perturbation = np.random.uniform(-0.1, 0.1)
            lat += perturbation
            lon += perturbation
            
            points.append((lat, lon))
        
        boundary = FireBoundary(
            boundary_points=points,
            timestamp=self.last_update or datetime.now(),
            confidence=0.85,
            source="simulated",
            method="convex_hull",
            is_geographic=True,
            metadata={
                "scenario": self.scenario_name,
                "num_observations": len(self.observations),
                "generation_method": "clustering_analysis"
            }
        )
        
        self.boundary = boundary
        logger.info(f"Generated simulated fire boundary with {len(points)} points")
        
        return boundary
    
    def set_scenario(self, scenario_name: str, **kwargs):
        """
        Change the simulation scenario with realistic parameters.
        
        Scenarios:
        - small_fire: Limited spread, few observations
        - medium_fire: Moderate spread, default scenario
        - large_fire: Wide spread, significant observations
        - extreme_fire: Massive fire, many observations
        - wildland_urban_interface: Urban structures + wildland
        - coastal_fire: Fire near water boundary
        - mountain_fire: High terrain variation
        """
        self.scenario_name = scenario_name
        self.name = f"Simulated Fire - {scenario_name}"
        
        # Base scenario parameters
        scenarios = {
            "small_fire": {
                "num_observations": 20,
                "boundary_radius": 1.0,
                "center_lat": 35.0,
                "center_lon": -120.0,
                "wind_direction": 270,
                "fire_intensity_variation": True
            },
            "medium_fire": {
                "num_observations": 50,
                "boundary_radius": 2.0,
                "center_lat": 35.0,
                "center_lon": -120.0,
                "wind_direction": 270,
                "fire_intensity_variation": True
            },
            "large_fire": {
                "num_observations": 100,
                "boundary_radius": 4.0,
                "center_lat": 35.0,
                "center_lon": -120.0,
                "wind_direction": 270,
                "fire_intensity_variation": True
            },
            "extreme_fire": {
                "num_observations": 200,
                "boundary_radius": 8.0,
                "center_lat": 35.0,
                "center_lon": -120.0,
                "wind_direction": 270,
                "fire_intensity_variation": True
            },
            "wildland_urban_interface": {
                "num_observations": 80,
                "boundary_radius": 3.0,
                "center_lat": 34.5,
                "center_lon": -118.5,
                "wind_direction": 315,
                "fire_intensity_variation": True
            },
            "coastal_fire": {
                "num_observations": 60,
                "boundary_radius": 2.5,
                "center_lat": 33.5,
                "center_lon": -117.2,
                "wind_direction": 45,
                "fire_intensity_variation": True
            },
            "mountain_fire": {
                "num_observations": 90,
                "boundary_radius": 3.5,
                "center_lat": 37.0,
                "center_lon": -121.0,
                "wind_direction": 180,
                "fire_intensity_variation": True
            }
        }
        
        if scenario_name in scenarios:
            for key, value in scenarios[scenario_name].items():
                setattr(self, key, value)
        
        # Override with any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Calculate spread direction based on wind
        self.spread_direction = (self.wind_direction + 180) % 360
        
        logger.info(f"Scenario changed to: {scenario_name} (wind: {self.wind_direction}°, spread: {self.spread_direction}°)")
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of simulation."""
        status = super().get_status()
        status.update({
            "scenario": self.scenario_name,
            "center": (self.center_lat, self.center_lon),
            "num_observations": self.num_observations,
            "boundary_radius": self.boundary_radius
        })
        return status
    
    def get_data_source_info(self) -> Dict[str, Any]:
        """Get detailed information about this data source."""
        return {
            "source_type": self.source_type,
            "name": self.name,
            "description": "Virtual drone simulation for testing and demonstration without physical hardware",
            "data_origin": "Synthetic/Simulated",
            "is_real_data": False,
            "geographic_coords": True,
            "temporal_coverage": "Current simulation time step",
            "requires_authentication": False,
            "update_frequency": "On-demand (manual refresh)",
            "confidence_level": 0.85  # Simulation data is reliable but not real
        }
    
    def validate_data(self) -> Tuple[bool, str]:
        """Validate that simulated data is complete and coherent."""
        try:
            # Check observations
            if not self.observations:
                return False, "No fire observations generated"
            
            if len(self.observations) < 3:
                return False, f"Too few observations ({len(self.observations)}), need at least 3"
            
            # Check observation validity
            for obs in self.observations:
                if not (-90 <= obs.latitude <= 90):
                    return False, f"Invalid latitude: {obs.latitude}"
                if not (-180 <= obs.longitude <= 180):
                    return False, f"Invalid longitude: {obs.longitude}"
                if not (0 <= obs.confidence <= 1):
                    return False, f"Invalid confidence: {obs.confidence}"
            
            # Check boundary
            if not self.boundary:
                return False, "No fire boundary generated"
            
            if len(self.boundary.boundary_points) < 3:
                return False, f"Boundary has too few points: {len(self.boundary.boundary_points)}"
            
            # Check for duplicate boundary points
            points_set = set(self.boundary.boundary_points)
            if len(points_set) < len(self.boundary.boundary_points):
                return False, "Boundary has duplicate points"
            
            # Check confidence
            if not (0 <= self.boundary.confidence <= 1):
                return False, f"Boundary confidence invalid: {self.boundary.confidence}"
            
            return True, "Data validation passed - simulation is coherent"
            
        except Exception as e:
            return False, f"Data validation error: {str(e)}"

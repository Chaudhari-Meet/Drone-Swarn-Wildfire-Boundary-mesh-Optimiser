"""
Abstract base class for all data sources.
Defines the common interface that all data sources must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class FireObservation:
    """Represents a single fire observation (hotspot, detection, etc.)"""
    latitude: float
    longitude: float
    timestamp: datetime
    confidence: float  # 0-1
    temperature: Optional[float] = None
    fire_radiative_power: Optional[float] = None
    source: str = "unknown"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "temperature": self.temperature,
            "fire_radiative_power": self.fire_radiative_power,
            "source": self.source,
            "metadata": self.metadata
        }


@dataclass
class FireBoundary:
    """Represents a wildfire boundary"""
    boundary_points: List[Tuple[float, float]]  # List of (lat, lon) or (x, y)
    timestamp: datetime
    confidence: float  # 0-1
    source: str = "unknown"
    method: str = "unknown"  # e.g., "convex_hull", "dbscan", "manual", etc.
    is_geographic: bool = True  # True if lat/lon, False if Cartesian
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        
        if len(self.boundary_points) < 3:
            raise ValueError("Boundary must have at least 3 points")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "boundary_points": self.boundary_points,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "source": self.source,
            "method": self.method,
            "is_geographic": self.is_geographic,
            "metadata": self.metadata
        }


class DataSource(ABC):
    """
    Abstract base class for all wildfire data sources.
    
    Supports 5 input modes:
    1. Real Drone Mode - Live MAVLink telemetry from physical drones
    2. Satellite Fire Data Mode - NASA FIRMS / Copernicus hotspot data
    3. Historical Wildfire Mode - GeoJSON/KML/CSV historical incidents
    4. Satellite Image Upload Mode - JPG/PNG/GeoTIFF fire imagery
    5. Virtual/Simulated Drone Mode - Synthetic demonstration data
    
    Subclasses must implement:
    - is_available()
    - initialize(**kwargs)
    - get_fire_observations()
    - get_fire_boundary()
    - get_data_source_info() - NEW
    - validate_data() - NEW
    """
    
    def __init__(self, name: str, source_type: str):
        """
        Initialize data source.
        
        Args:
            name: Human-readable name for this source
            source_type: One of: 'real_drone', 'satellite', 'historical', 'image_upload', 'simulation'
        """
        if source_type not in ['real_drone', 'satellite', 'historical', 'image_upload', 'simulation']:
            raise ValueError(f"Invalid source_type: {source_type}. Must be one of: real_drone, satellite, historical, image_upload, simulation")
        
        self.name = name
        self.source_type = source_type
        self.last_update = None
        self.observations = []
        self.boundary = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Data quality and confidence tracking
        self.data_confidence = 0.0  # 0-1 scale indicating data reliability
        self.data_timestamp = None
        self.data_status = "UNINITIALIZED"  # UNINITIALIZED, LOADING, READY, ERROR
        self.error_message = None
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this data source is available and ready to use.
        
        Returns:
            True if data source can be used, False otherwise
        """
        pass
    
    @abstractmethod
    def initialize(self, **kwargs) -> bool:
        """
        Initialize the data source with configuration.
        
        Args:
            **kwargs: Configuration parameters specific to this source
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_fire_observations(self, 
                             location: Optional[Tuple[float, float]] = None,
                             radius_km: float = 100,
                             time_range_hours: int = 24) -> List[FireObservation]:
        """
        Retrieve fire observations from this source.
        
        Args:
            location: (latitude, longitude) or (x, y) center point
            radius_km: Search radius in kilometers
            time_range_hours: How many hours back to search
        
        Returns:
            List of FireObservation objects
        """
        pass
    
    @abstractmethod
    def get_fire_boundary(self, location: Optional[Tuple[float, float]] = None) -> Optional[FireBoundary]:
        """
        Get or generate fire boundary from available data.
        
        Args:
            location: Optional center point for boundary generation
        
        Returns:
            FireBoundary object or None if no data available
        """
        pass
    
    @abstractmethod
    def get_data_source_info(self) -> Dict[str, Any]:
        """
        Get detailed information about this data source.
        
        MUST BE IMPLEMENTED BY ALL SUBCLASSES.
        
        Returns:
            Dictionary with keys:
            - 'source_type': str (real_drone, satellite, historical, image_upload, simulation)
            - 'name': str (human-readable name)
            - 'description': str (what this source does)
            - 'data_origin': str (where data comes from: e.g., "NASA FIRMS", "User Upload", "Simulated")
            - 'is_real_data': bool (True if real observations, False if simulated/synthetic)
            - 'geographic_coords': bool (True if data is lat/lon, False if Cartesian)
            - 'temporal_coverage': str (e.g., "Last 24 hours", "Single snapshot", "Historical")
            - 'requires_authentication': bool (True if needs API key/credentials)
            - 'update_frequency': str (e.g., "Real-time", "Hourly", "Manual upload")
            - 'confidence_level': float (0-1 scale of data reliability)
        """
        pass
    
    @abstractmethod
    def validate_data(self) -> Tuple[bool, str]:
        """
        Validate that loaded data is complete and coherent.
        
        MUST BE IMPLEMENTED BY ALL SUBCLASSES.
        
        Returns:
            Tuple of (is_valid: bool, message: str)
            - is_valid: True if all data checks passed
            - message: Human-readable validation result
            
        Should check:
        - At least some fire observations exist
        - Boundary is valid (3+ points, no duplicates, closed polygon)
        - Coordinates are within valid ranges
        - Timestamps are reasonable
        - Confidence scores are in valid range (0-1)
        """
        pass
    
    def refresh(self, **kwargs) -> bool:
        """
        Refresh data from the source.
        
        Args:
            **kwargs: Refresh parameters specific to this source
        
        Returns:
            True if refresh successful, False otherwise
        """
        self.logger.info(f"Refreshing data from {self.name}")
        self.data_status = "LOADING"
        
        try:
            # Get fresh observations
            self.observations = self.get_fire_observations(**kwargs)
            
            # Get boundary
            self.boundary = self.get_fire_boundary()
            
            # Validate data
            is_valid, validation_message = self.validate_data()
            if not is_valid:
                self.logger.warning(f"Data validation issue: {validation_message}")
                self.error_message = validation_message
                self.data_status = "WARNING"
                return False
            
            # Update timestamps
            self.last_update = datetime.now()
            self.data_timestamp = self.last_update
            self.data_status = "READY"
            self.error_message = None
            
            self.logger.info(f"Successfully refreshed {len(self.observations)} observations from {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error refreshing data from {self.name}: {str(e)}")
            self.data_status = "ERROR"
            self.error_message = str(e)
            return False
    
    def get_observations_summary(self) -> Dict[str, Any]:
        """Get summary statistics about current observations."""
        if not self.observations:
            return {
                "total_count": 0,
                "average_confidence": 0.0,
                "min_confidence": None,
                "max_confidence": None,
                "latest_timestamp": None,
                "earliest_timestamp": None
            }
        
        confidences = [obs.confidence for obs in self.observations]
        timestamps = [obs.timestamp for obs in self.observations]
        
        return {
            "total_count": len(self.observations),
            "average_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "latest_timestamp": max(timestamps).isoformat() if timestamps else None,
            "earliest_timestamp": min(timestamps).isoformat() if timestamps else None
        }
    
    def get_boundary_info(self) -> Dict[str, Any]:
        """Get information about the current boundary."""
        if not self.boundary:
            return {
                "exists": False,
                "points": 0,
                "confidence": None,
                "source": None,
                "method": None
            }
        
        return {
            "exists": True,
            "points": len(self.boundary.boundary_points),
            "confidence": self.boundary.confidence,
            "source": self.boundary.source,
            "method": self.boundary.method,
            "is_geographic": self.boundary.is_geographic,
            "timestamp": self.boundary.timestamp.isoformat() if self.boundary.timestamp else None
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information about this data source."""
        source_info = self.get_data_source_info()
        obs_summary = self.get_observations_summary()
        boundary_info = self.get_boundary_info()
        
        return {
            "name": self.name,
            "source_type": self.source_type,
            "data_origin": source_info.get("data_origin", "unknown"),
            "is_real_data": source_info.get("is_real_data", False),
            "available": self.is_available(),
            "status": self.data_status,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "error_message": self.error_message,
            "data_confidence": self.data_confidence,
            "observations": obs_summary,
            "boundary": boundary_info
        }
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', type='{self.source_type}')"

"""
Object Detection module for animals and persons using thermal and RGB fusion.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DetectionType(Enum):
    """Type of detected object."""
    ANIMAL = "animal"
    PERSON = "person"
    VEHICLE = "vehicle"
    EQUIPMENT = "equipment"
    UNKNOWN = "unknown"


class DetectionCategory(Enum):
    """Category of detected object."""
    # Animals
    DOG = "dog"
    COW = "cow"
    DEER = "deer"
    LIVESTOCK = "livestock"
    WILDLIFE = "wildlife"
    
    # People
    CIVILIAN = "civilian"
    FIREFIGHTER = "firefighter"
    RESCUE_PERSONNEL = "rescue_personnel"
    
    # Other
    VEHICLE = "vehicle"
    STRUCTURE = "structure"
    UNKNOWN = "unknown"


@dataclass
class Detection:
    """Represents a single detection result."""
    detection_id: str
    detection_type: DetectionType
    category: Optional[DetectionCategory]
    latitude: float
    longitude: float
    altitude_m: float
    confidence: float  # 0-1
    timestamp: datetime
    
    # Evidence
    thermal_confidence: float = 0.0
    rgb_confidence: float = 0.0
    lidar_evidence: bool = False
    
    # Metadata
    drone_id: Optional[int] = None
    source: str = "simulated"  # simulated, real_thermal, real_rgb
    verified: bool = False
    verified_by: Optional[str] = None
    
    # Additional info
    size_estimate: Optional[str] = None  # small, medium, large
    movement: Optional[str] = None  # stationary, moving
    urgency: Optional[str] = None  # low, medium, high
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "detection_id": self.detection_id,
            "type": self.detection_type.value,
            "category": self.category.value if self.category else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "verified": self.verified,
            "source": self.source
        }


class AnimalDetector:
    """Detects animals in thermal and RGB imagery."""
    
    def __init__(self):
        self.detection_history = []
        self.logger = logging.getLogger(f"{__name__}.AnimalDetector")
    
    def detect_from_thermal(self,
                           latitude: float,
                           longitude: float,
                           altitude_m: float,
                           drone_id: int,
                           thermal_confidence: float = 0.75) -> Optional[Detection]:
        """
        Detect possible animal from thermal image.
        
        Args:
            latitude: Detection latitude
            longitude: Detection longitude
            altitude_m: Drone altitude
            drone_id: Drone ID making detection
            thermal_confidence: Thermal detection confidence
        
        Returns:
            Detection object or None
        """
        if thermal_confidence < 0.6:
            return None
        
        # Simple heuristic for animal classification
        # In production, this would use trained ML model
        
        detection = Detection(
            detection_id=f"animal_{int(datetime.now().timestamp() * 1000)}",
            detection_type=DetectionType.ANIMAL,
            category=DetectionCategory.WILDLIFE,
            latitude=latitude,
            longitude=longitude,
            altitude_m=altitude_m,
            confidence=thermal_confidence * 0.9,  # Reduce for thermal only
            timestamp=datetime.now(),
            thermal_confidence=thermal_confidence,
            drone_id=drone_id,
            source="real_thermal",
            urgency="medium" if thermal_confidence > 0.8 else "low",
            size_estimate="medium"
        )
        
        self.detection_history.append(detection)
        self.logger.info(f"Animal detection (thermal): {detection.detection_id}")
        
        return detection
    
    def detect_from_rgb(self,
                       latitude: float,
                       longitude: float,
                       altitude_m: float,
                       drone_id: int,
                       rgb_confidence: float = 0.75) -> Optional[Detection]:
        """Detect animal from RGB image."""
        if rgb_confidence < 0.7:
            return None
        
        detection = Detection(
            detection_id=f"animal_{int(datetime.now().timestamp() * 1000)}",
            detection_type=DetectionType.ANIMAL,
            category=DetectionCategory.WILDLIFE,
            latitude=latitude,
            longitude=longitude,
            altitude_m=altitude_m,
            confidence=rgb_confidence * 0.85,
            timestamp=datetime.now(),
            rgb_confidence=rgb_confidence,
            drone_id=drone_id,
            source="real_rgb",
            urgency="medium",
            size_estimate="medium"
        )
        
        self.detection_history.append(detection)
        self.logger.info(f"Animal detection (RGB): {detection.detection_id}")
        
        return detection
    
    def sensor_fusion(self,
                     thermal_detection: Optional[Detection],
                     rgb_detection: Optional[Detection]) -> Optional[Detection]:
        """Fuse thermal and RGB detections for higher confidence."""
        if thermal_detection is None and rgb_detection is None:
            return None
        
        # If both detections exist and are close in location
        if thermal_detection and rgb_detection:
            # Check proximity
            dist = ((thermal_detection.latitude - rgb_detection.latitude) ** 2 +
                   (thermal_detection.longitude - rgb_detection.longitude) ** 2) ** 0.5
            
            if dist < 0.001:  # Roughly 100m at equator
                # Fuse detections
                fused_confidence = (thermal_detection.confidence + rgb_detection.confidence) / 2 * 1.15
                
                fused = Detection(
                    detection_id=f"fused_animal_{int(datetime.now().timestamp() * 1000)}",
                    detection_type=DetectionType.ANIMAL,
                    category=DetectionCategory.WILDLIFE,
                    latitude=(thermal_detection.latitude + rgb_detection.latitude) / 2,
                    longitude=(thermal_detection.longitude + rgb_detection.longitude) / 2,
                    altitude_m=(thermal_detection.altitude_m + rgb_detection.altitude_m) / 2,
                    confidence=min(1.0, fused_confidence),
                    timestamp=datetime.now(),
                    thermal_confidence=thermal_detection.confidence,
                    rgb_confidence=rgb_detection.confidence,
                    source="thermal_rgb_fusion",
                    verified=fused_confidence > 0.9
                )
                
                self.logger.info(f"Fused animal detection: confidence={fused.confidence:.2f}")
                return fused
        
        # Return better single detection
        if thermal_detection and rgb_detection:
            return thermal_detection if thermal_detection.confidence > rgb_detection.confidence else rgb_detection
        
        return thermal_detection or rgb_detection


class PersonDetector:
    """Detects persons (civilians, firefighters, rescue personnel)."""
    
    def __init__(self):
        self.detection_history = []
        self.logger = logging.getLogger(f"{__name__}.PersonDetector")
    
    def detect_from_thermal(self,
                           latitude: float,
                           longitude: float,
                           altitude_m: float,
                           drone_id: int,
                           thermal_confidence: float = 0.85) -> Optional[Detection]:
        """Detect possible person from thermal image."""
        if thermal_confidence < 0.75:
            return None
        
        # Determine if civilian or firefighter (heuristic)
        # Could be enhanced with thermal signature analysis
        is_firefighter = thermal_confidence > 0.9
        
        detection = Detection(
            detection_id=f"person_{int(datetime.now().timestamp() * 1000)}",
            detection_type=DetectionType.PERSON,
            category=DetectionCategory.FIREFIGHTER if is_firefighter else DetectionCategory.CIVILIAN,
            latitude=latitude,
            longitude=longitude,
            altitude_m=altitude_m,
            confidence=thermal_confidence * 0.95,
            timestamp=datetime.now(),
            thermal_confidence=thermal_confidence,
            drone_id=drone_id,
            source="real_thermal",
            urgency="high",
            size_estimate="small",
            movement="stationary"
        )
        
        self.detection_history.append(detection)
        self.logger.warning(f"PERSON DETECTED: {detection.detection_id} - Category: {detection.category.value}")
        
        return detection
    
    def detect_from_rgb(self,
                       latitude: float,
                       longitude: float,
                       altitude_m: float,
                       drone_id: int,
                       rgb_confidence: float = 0.85) -> Optional[Detection]:
        """Detect possible person from RGB image."""
        if rgb_confidence < 0.8:
            return None
        
        detection = Detection(
            detection_id=f"person_{int(datetime.now().timestamp() * 1000)}",
            detection_type=DetectionType.PERSON,
            category=DetectionCategory.CIVILIAN,
            latitude=latitude,
            longitude=longitude,
            altitude_m=altitude_m,
            confidence=rgb_confidence * 0.9,
            timestamp=datetime.now(),
            rgb_confidence=rgb_confidence,
            drone_id=drone_id,
            source="real_rgb",
            urgency="high",
            size_estimate="small"
        )
        
        self.detection_history.append(detection)
        self.logger.warning(f"PERSON DETECTED: {detection.detection_id}")
        
        return detection
    
    def sensor_fusion(self,
                     thermal_detection: Optional[Detection],
                     rgb_detection: Optional[Detection]) -> Optional[Detection]:
        """Fuse thermal and RGB person detections."""
        if thermal_detection is None and rgb_detection is None:
            return None
        
        if thermal_detection and rgb_detection:
            dist = ((thermal_detection.latitude - rgb_detection.latitude) ** 2 +
                   (thermal_detection.longitude - rgb_detection.longitude) ** 2) ** 0.5
            
            if dist < 0.001:
                fused_confidence = min(1.0, (thermal_detection.confidence + rgb_detection.confidence) / 2 * 1.2)
                
                fused = Detection(
                    detection_id=f"fused_person_{int(datetime.now().timestamp() * 1000)}",
                    detection_type=DetectionType.PERSON,
                    category=thermal_detection.category,
                    latitude=(thermal_detection.latitude + rgb_detection.latitude) / 2,
                    longitude=(thermal_detection.longitude + rgb_detection.longitude) / 2,
                    altitude_m=(thermal_detection.altitude_m + rgb_detection.altitude_m) / 2,
                    confidence=fused_confidence,
                    timestamp=datetime.now(),
                    thermal_confidence=thermal_detection.confidence,
                    rgb_confidence=rgb_detection.confidence,
                    source="thermal_rgb_fusion",
                    urgency="high",
                    verified=fused_confidence > 0.92
                )
                
                self.logger.warning(f"FUSED PERSON DETECTION: confidence={fused.confidence:.2f}")
                return fused
        
        return thermal_detection or rgb_detection

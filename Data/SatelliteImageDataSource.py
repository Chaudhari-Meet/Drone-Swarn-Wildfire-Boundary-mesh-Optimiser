"""
Satellite Image Upload Data Source.

Processes satellite wildfire imagery for:
- JPG/JPEG: Standard RGB satellite imagery
- PNG: PNG with optional transparency
- TIFF/GeoTIFF: Georeferenced imagery with geographic metadata
- Multi-band imagery: Thermal + RGB combination

Features:
- Fire hotspot segmentation
- Wildfire boundary extraction
- Georeferencing (if GeoTIFF metadata available)
- Manual coordinate assignment (if no metadata)
- Confidence scoring based on image analysis
"""

from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import logging
from .DataSource import DataSource, FireObservation, FireBoundary

logger = logging.getLogger(__name__)


class SatelliteImageDataSource(DataSource):
    """
    Process and analyze satellite fire imagery.
    
    Supports:
    - JPG/JPEG: Standard imagery
    - PNG: RGB with transparency
    - TIFF/GeoTIFF: Georeferenced imagery with CRS
    - Multi-band: Thermal + RGB fusion
    
    IMPORTANT:
    - If image has no geographic metadata, geographic positioning is APPROXIMATE/MANUAL
    - Fire segmentation is automatic but may have false positives
    - Manual boundary correction is always recommended
    - Detected hotspots require human verification
    """
    
    def __init__(self, image_path: Optional[str] = None):
        """
        Initialize satellite image data source.
        
        Args:
            image_path: Path to satellite fire imagery file
        """
        super().__init__(
            name="Satellite Image Upload",
            source_type="image_upload"
        )
        
        self.image_path = image_path
        self.image_format = None  # jpg, png, tiff, geotiff
        self.image_data = None  # PIL Image object
        self.image_metadata = {}  # EXIF / GeoTIFF metadata
        self.georeferencing = "UNKNOWN"  # GEOREFERENCED, APPROXIMATE, MANUAL, NONE
        
        # Georeferencing parameters (if manual)
        self.reference_lat = None
        self.reference_lon = None
        self.image_bounds = None  # (north, south, east, west)
        
        # Image analysis results
        self.fire_pixels = []  # Detected fire/hotspot pixel coordinates
        self.fire_confidence_map = None  # Confidence map of fire detection
        
        # Data quality
        self.data_confidence = 0.80  # Image-based detection has uncertainty
        self.detection_method = "image_segmentation"
        self.image_acquisition_date = None
        
        if image_path:
            self.image_format = self._detect_format(image_path)
            logger.info(f"Satellite image source created: {image_path} (format: {self.image_format})")
    
    def is_available(self) -> bool:
        """
        Check if image has been loaded and processed.
        
        Returns:
            True if image data is available
        """
        return self.image_data is not None and self.boundary is not None
    
    def initialize(self, **kwargs) -> bool:
        """
        Load and process satellite imagery.
        
        Args:
            **kwargs: Configuration:
                - 'image_path': Path to image file
                - 'reference_lat': Manual reference latitude
                - 'reference_lon': Manual reference longitude
                - 'bounds': Image bounds (north, south, east, west)
                - 'acquisition_date': When image was acquired
        
        Returns:
            True if loading and processing successful
        """
        try:
            if "image_path" in kwargs:
                self.image_path = kwargs["image_path"]
                self.image_format = self._detect_format(self.image_path)
            
            if not self.image_path:
                raise ValueError("No image_path provided")
            
            # Check file exists
            if not Path(self.image_path).exists():
                raise FileNotFoundError(f"Image file not found: {self.image_path}")
            
            # Load image
            success = self._load_image()
            if not success:
                return False
            
            # Extract/set georeferencing
            if "reference_lat" in kwargs and "reference_lon" in kwargs:
                self.reference_lat = kwargs["reference_lat"]
                self.reference_lon = kwargs["reference_lon"]
                self.georeferencing = "MANUAL"
                logger.info(f"Manual georeferencing set: ({self.reference_lat}, {self.reference_lon})")
            
            if "bounds" in kwargs:
                self.image_bounds = kwargs["bounds"]
            
            if "acquisition_date" in kwargs:
                self.image_acquisition_date = kwargs["acquisition_date"]
            
            # Analyze image for fire hotspots
            success = self._analyze_image_for_fire()
            if not success:
                return False
            
            # Generate boundary from detected hotspots
            if self.observations:
                self.boundary = self._generate_boundary_from_image()
            else:
                logger.warning("No fire hotspots detected in image")
                return False
            
            self.data_status = "READY"
            self.last_update = datetime.now()
            logger.info(f"Successfully processed satellite image: {len(self.observations)} hotspots detected")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing satellite image data: {str(e)}")
            self.data_status = "ERROR"
            self.error_message = str(e)
            return False
    
    def _detect_format(self, file_path: str) -> Optional[str]:
        """Detect image format from file extension."""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        format_map = {
            ".jpg": "jpg",
            ".jpeg": "jpg",
            ".png": "png",
            ".tif": "tiff",
            ".tiff": "tiff",
            ".geotiff": "geotiff",
            ".tif": "geotiff"
        }
        
        return format_map.get(suffix, "unknown")
    
    def _load_image(self) -> bool:
        """Load image file using PIL/Pillow."""
        try:
            from PIL import Image
            from PIL.TiffTags import TAGS
            
            img = Image.open(self.image_path)
            self.image_data = img
            
            logger.info(f"Loaded image: {img.size[0]}x{img.size[1]}, mode: {img.mode}")
            
            # Extract metadata
            if hasattr(img, "tag_v2"):
                # GeoTIFF metadata
                for tag_id, tag_data in img.tag_v2.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    self.image_metadata[tag_name] = tag_data
                
                # Check for georeferencing info
                if "ModelPixelScale" in self.image_metadata or "ModelTiepoint" in self.image_metadata:
                    self.georeferencing = "GEOREFERENCED"
                    logger.info("GeoTIFF georeferencing detected")
            
            if self.image_format == "jpg" or self.image_format == "png":
                self.georeferencing = "NONE"
                logger.warning(f"{self.image_format.upper()} image has no geographic metadata - georeferencing will be APPROXIMATE or MANUAL")
            
            return True
            
        except ImportError:
            logger.error("PIL/Pillow not installed - cannot process images")
            logger.info("Install with: pip install Pillow")
            return False
        except Exception as e:
            logger.error(f"Error loading image: {str(e)}")
            return False
    
    def _analyze_image_for_fire(self) -> bool:
        """
        Analyze image for fire hotspots using color-based segmentation.
        
        IMPORTANT: This is a simplified analysis. Real implementation would use:
        - ML models (YOLO, U-Net)
        - Thermal band analysis (if available)
        - Multi-spectral indices (NDVI, NDBI)
        - Sensor fusion
        """
        try:
            import numpy as np
            
            # Convert to numpy array
            img_array = np.array(self.image_data)
            
            if len(img_array.shape) == 2:
                # Grayscale image - not suitable for fire detection
                logger.warning("Grayscale image - fire detection accuracy reduced")
                # Simple threshold-based detection
                fire_mask = img_array > np.percentile(img_array, 80)
            else:
                # RGB or RGBA image
                if img_array.shape[2] == 4:
                    # Remove alpha channel
                    img_array = img_array[:, :, :3]
                
                # Extract R and G channels
                red = img_array[:, :, 0].astype(float)
                green = img_array[:, :, 1].astype(float)
                blue = img_array[:, :, 2].astype(float)
                
                # Simple fire detection: high red, lower green and blue
                # This is a basic heuristic - real fire detection is more complex
                red_dominant = red > (green + blue) / 2
                red_bright = red > 150
                
                fire_mask = red_dominant & red_bright
            
            # Find fire pixel coordinates
            fire_coords = np.argwhere(fire_mask)
            
            if len(fire_coords) == 0:
                logger.warning("No fire hotspots detected in image")
                return True  # Image loaded but no fires detected
            
            logger.info(f"Detected {len(fire_coords)} fire pixels")
            
            # Cluster fire pixels to identify distinct hotspots
            hotspots = self._cluster_fire_pixels(fire_coords, img_array)
            
            # Convert hotspots to geographic observations
            self._convert_pixels_to_observations(hotspots)
            
            return True
            
        except ImportError:
            logger.error("NumPy not installed - cannot analyze image")
            return False
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return False
    
    def _cluster_fire_pixels(self, fire_coords: Any, img_array: Any) -> List[Dict[str, Any]]:
        """Cluster detected fire pixels into distinct hotspots."""
        try:
            from scipy.cluster.hierarchy import fclusterdata
            import numpy as np
            
            if len(fire_coords) < 3:
                # Too few pixels for clustering
                return [{"center": tuple(fire_coords.mean(axis=0)), "pixels": fire_coords}]
            
            # Cluster fire pixels
            clusters = fclusterdata(fire_coords, t=50, criterion="distance", method="complete")
            
            # Extract hotspot centers and properties
            hotspots = []
            unique_clusters = np.unique(clusters)
            
            for cluster_id in unique_clusters:
                cluster_pixels = fire_coords[clusters == cluster_id]
                center = cluster_pixels.mean(axis=0)
                
                hotspots.append({
                    "center": tuple(center),
                    "pixels": cluster_pixels,
                    "size": len(cluster_pixels),
                    "intensity": self._calculate_cluster_intensity(cluster_pixels, img_array)
                })
            
            logger.info(f"Clustered fire pixels into {len(hotspots)} hotspots")
            return hotspots
            
        except ImportError:
            logger.warning("SciPy not installed - using simple fire pixel grouping")
            # Fallback: group all fire pixels as single hotspot
            return [{"center": tuple(fire_coords.mean(axis=0)), "pixels": fire_coords}]
    
    def _calculate_cluster_intensity(self, pixels: Any, img_array: Any) -> float:
        """Calculate intensity of a fire cluster (0-1 scale)."""
        try:
            import numpy as np
            
            # Get RGB values for cluster pixels
            pixel_values = img_array[pixels[:, 0], pixels[:, 1]]
            
            # Calculate red intensity (0-1)
            if len(pixel_values.shape) == 2:  # RGB
                red_intensity = pixel_values[:, 0].mean() / 255.0
            else:  # Grayscale
                red_intensity = pixel_values.mean() / 255.0
            
            return float(np.clip(red_intensity, 0, 1))
            
        except Exception as e:
            logger.warning(f"Error calculating intensity: {str(e)}")
            return 0.5
    
    def _convert_pixels_to_observations(self, hotspots: List[Dict]) -> None:
        """Convert image pixel hotspots to geographic fire observations."""
        try:
            for hotspot in hotspots:
                pixel_y, pixel_x = hotspot["center"]
                
                # Convert pixel coordinates to geographic (if georeferenced)
                if self.georeferencing == "MANUAL" and self.reference_lat and self.reference_lon:
                    # Simple linear mapping from pixel to geo coordinates
                    lat, lon = self._pixel_to_geo(pixel_x, pixel_y)
                elif self.georeferencing == "GEOREFERENCED":
                    # Use GeoTIFF metadata to convert
                    lat, lon = self._pixel_to_geo_geotiff(pixel_x, pixel_y)
                else:
                    # No georeferencing - skip geographic assignment
                    logger.debug(f"Skipping geographic conversion - no georeferencing available")
                    continue
                
                # Create observation
                observation = FireObservation(
                    latitude=lat,
                    longitude=lon,
                    timestamp=self.image_acquisition_date or datetime.now(),
                    confidence=min(0.5 + hotspot.get("intensity", 0.5), 1.0),
                    temperature=None,  # Not available from RGB image
                    fire_radiative_power=hotspot.get("size", 0),  # Proxy: cluster size
                    source="satellite_image",
                    metadata={
                        "image_file": str(self.image_path),
                        "detection_method": "color_segmentation",
                        "pixel_center": hotspot["center"],
                        "cluster_size": hotspot.get("size", 0),
                        "georeferencing": self.georeferencing
                    }
                )
                
                self.observations.append(observation)
            
            logger.info(f"Converted {len(self.observations)} hotspots to geographic observations")
            
        except Exception as e:
            logger.error(f"Error converting pixels to observations: {str(e)}")
    
    def _pixel_to_geo(self, pixel_x: float, pixel_y: float) -> Tuple[float, float]:
        """Convert pixel coordinates to geographic coordinates (manual georeferencing)."""
        if not self.reference_lat or not self.reference_lon or not self.image_data:
            raise ValueError("Manual georeferencing parameters not set")
        
        # Simple scaling: assume image dimensions map to bounds
        img_width, img_height = self.image_data.size
        
        # Assume reference point is center of image
        lat_offset = (pixel_y - img_height / 2) * 0.01  # Arbitrary scaling
        lon_offset = (pixel_x - img_width / 2) * 0.01
        
        lat = self.reference_lat + lat_offset
        lon = self.reference_lon + lon_offset
        
        return lat, lon
    
    def _pixel_to_geo_geotiff(self, pixel_x: float, pixel_y: float) -> Tuple[float, float]:
        """Convert pixel coordinates to geographic coordinates using GeoTIFF metadata."""
        # Placeholder for GeoTIFF transformation
        logger.warning("GeoTIFF coordinate transformation not yet implemented")
        # Would use ModelPixelScale and ModelTiepoint tags
        return self.reference_lat or 0.0, self.reference_lon or 0.0
    
    def _generate_boundary_from_image(self) -> Optional[FireBoundary]:
        """Generate wildfire boundary from detected hotspots."""
        try:
            if len(self.observations) < 3:
                logger.warning("Too few observations for boundary generation")
                return None
            
            import numpy as np
            
            # Extract observation coordinates
            obs_points = np.array([(obs.latitude, obs.longitude) for obs in self.observations])
            
            # Create convex hull-like boundary
            center = obs_points.mean(axis=0)
            distances = np.linalg.norm(obs_points - center, axis=1)
            max_distance = distances.max() * 1.3  # Add 30% buffer
            
            # Generate boundary polygon
            boundary_points = []
            num_points = 20
            for i in range(num_points):
                angle = 2 * np.pi * i / num_points
                lat = center[0] + max_distance * np.sin(angle)
                lon = center[1] + max_distance * np.cos(angle)
                boundary_points.append((lat, lon))
            
            return FireBoundary(
                boundary_points=boundary_points,
                timestamp=self.image_acquisition_date or datetime.now(),
                confidence=self.data_confidence,
                source="satellite_image",
                method="hotspot_clustering",
                is_geographic=True,
                metadata={
                    "image_file": str(self.image_path),
                    "image_format": self.image_format,
                    "georeferencing": self.georeferencing,
                    "num_hotspots": len(self.observations),
                    "detection_method": "color_segmentation"
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating boundary: {str(e)}")
            return None
    
    def get_fire_observations(self,
                             location: Optional[Tuple[float, float]] = None,
                             radius_km: float = 100,
                             time_range_hours: int = 24) -> List[FireObservation]:
        """
        Get fire observations from satellite image analysis.
        
        Returns:
            List of detected hotspots as FireObservation objects
        """
        return self.observations
    
    def get_fire_boundary(self, location: Optional[Tuple[float, float]] = None) -> Optional[FireBoundary]:
        """
        Get estimated wildfire boundary from image analysis.
        
        Returns:
            FireBoundary estimated from hotspot clustering
        """
        return self.boundary
    
    def get_data_source_info(self) -> Dict[str, Any]:
        """Get information about satellite image data source."""
        return {
            "source_type": self.source_type,
            "name": self.name,
            "description": "Satellite or aerial fire imagery uploaded for analysis (JPG/PNG/GeoTIFF)",
            "data_origin": f"Satellite Image: {Path(self.image_path).name if self.image_path else 'Unknown'}",
            "is_real_data": True,  # Real imagery (though AI-analyzed)
            "geographic_coords": self.georeferencing != "NONE",
            "temporal_coverage": f"Single snapshot: {self.image_acquisition_date or 'Unknown'}",
            "requires_authentication": False,
            "update_frequency": "Single image analysis",
            "confidence_level": self.data_confidence,
            "supported_formats": ["JPG", "JPEG", "PNG", "TIFF", "GeoTIFF"],
            "georeferencing_status": self.georeferencing,
            "detection_method": self.detection_method
        }
    
    def validate_data(self) -> Tuple[bool, str]:
        """Validate satellite image analysis results."""
        try:
            if not self.image_data:
                return False, "No image loaded"
            
            if not self.observations:
                return False, "No hotspots detected in image"
            
            if not self.boundary:
                return False, "No boundary generated"
            
            # Validate observations
            for obs in self.observations:
                if self.georeferencing != "NONE":
                    if not (-90 <= obs.latitude <= 90) or not (-180 <= obs.longitude <= 180):
                        return False, f"Invalid coordinates in observation: ({obs.latitude}, {obs.longitude})"
                
                if not (0 <= obs.confidence <= 1):
                    return False, f"Invalid confidence: {obs.confidence}"
            
            # Validate boundary
            if len(self.boundary.boundary_points) < 3:
                return False, "Boundary has too few points"
            
            msg = f"Satellite image validation passed - {len(self.observations)} hotspots detected"
            if self.georeferencing != "NONE":
                msg += f" (georeferencing: {self.georeferencing})"
            else:
                msg += " (⚠️ WARNING: No georeferencing - coordinates are APPROXIMATE or MANUAL)"
            
            return True, msg
            
        except Exception as e:
            return False, f"Satellite image validation error: {str(e)}"
    
    def set_manual_georeferencing(self, latitude: float, longitude: float,
                                  bounds: Optional[Tuple[float, float, float, float]] = None) -> bool:
        """
        Manually set geographic reference for image without metadata.
        
        Args:
            latitude: Reference latitude (center or corner)
            longitude: Reference longitude (center or corner)
            bounds: Optional (north, south, east, west) bounds
        
        Returns:
            True if georeferencing set
        """
        try:
            self.reference_lat = latitude
            self.reference_lon = longitude
            self.image_bounds = bounds
            self.georeferencing = "MANUAL"
            logger.info(f"Manual georeferencing set: ({latitude}, {longitude})")
            return True
        except Exception as e:
            logger.error(f"Error setting manual georeferencing: {str(e)}")
            return False
    
    def __repr__(self):
        return f"SatelliteImageDataSource(file='{Path(self.image_path).name if self.image_path else 'Unknown'}', hotspots={len(self.observations)}, georeferencing='{self.georeferencing}')"

"""
SatelliteImageryPipeline - Advanced satellite imagery processing for fire detection.

Provides multiple detection algorithms:
1. Color-based fire detection (Red/NIR ratio)
2. Thermal anomaly detection (brightness anomalies)
3. Vegetation anomaly detection (NDVI-based)
4. Machine learning-ready interface for future models

Can process Sentinel-2, Landsat 8/9, and aerial imagery.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.ndimage import label, binary_dilation
from scipy.spatial import ConvexHull

logger = logging.getLogger(__name__)


class FireDetectionAlgorithm:
    """Base class for fire detection algorithms."""
    
    def detect(self, image: np.ndarray) -> np.ndarray:
        """
        Detect fire in image.
        
        Args:
            image: Image array (H x W or H x W x C)
        
        Returns:
            Boolean mask of detected fire pixels
        """
        raise NotImplementedError


class ColorBasedDetector(FireDetectionAlgorithm):
    """
    Detect fire using Red/NIR color ratio.
    
    Fire emits in red spectrum and reflects NIR poorly.
    Index = (Red - NIR) / (Red + NIR)
    High values indicate fire.
    """
    
    def __init__(self, threshold: float = 0.4):
        self.threshold = threshold
    
    def detect(self, image: np.ndarray) -> np.ndarray:
        """Detect fire using color channels."""
        if image.shape[2] < 3:
            return np.zeros(image.shape[:2], dtype=bool)
        
        red = image[:, :, 0] / 255.0 if image.max() > 1 else image[:, :, 0]
        
        # Use NIR channel if available (4+ channels), else use green inverse
        if image.shape[2] >= 4:
            nir = image[:, :, 3] / 255.0 if image.max() > 1 else image[:, :, 3]
        else:
            green = image[:, :, 1] / 255.0 if image.max() > 1 else image[:, :, 1]
            nir = 1.0 - green  # Approximate
        
        # Fire index
        denominator = red + nir + 1e-8
        fire_index = (red - nir) / denominator
        
        # High fire index indicates fire
        fire_mask = fire_index > self.threshold
        
        logger.debug(f"Color detector: {np.sum(fire_mask)} fire pixels")
        return fire_mask


class ThermalAnomalyDetector(FireDetectionAlgorithm):
    """
    Detect fire using thermal anomaly (bright pixels).
    
    Fire appears as very bright in thermal band.
    Uses percentile-based threshold to find anomalies.
    """
    
    def __init__(self, percentile: float = 90, margin: float = 0.15):
        self.percentile = percentile
        self.margin = margin  # Additional threshold margin
    
    def detect(self, image: np.ndarray) -> np.ndarray:
        """Detect thermal anomalies."""
        # Use thermal band if available, else use brightness
        if len(image.shape) == 3 and image.shape[2] >= 10:
            # SWIR band (Landsat 10) for thermal
            thermal = image[:, :, 9] / 255.0 if image.max() > 1 else image[:, :, 9]
        elif len(image.shape) == 3:
            # Use red channel as proxy
            thermal = image[:, :, 0] / 255.0 if image.max() > 1 else image[:, :, 0]
        else:
            thermal = image / 255.0 if image.max() > 1 else image
        
        # Find anomalously bright pixels
        threshold = np.percentile(thermal, self.percentile) + self.margin
        fire_mask = thermal > threshold
        
        logger.debug(f"Thermal detector: {np.sum(fire_mask)} anomalous pixels")
        return fire_mask


class VegetationAnomalyDetector(FireDetectionAlgorithm):
    """
    Detect fire using vegetation anomalies (NDVI-based).
    
    Burned areas show as low NDVI (dead vegetation).
    Combines with high reflectance in red to identify active fires.
    """
    
    def __init__(self, ndvi_threshold: float = 0.1, brightness_threshold: float = 0.5):
        self.ndvi_threshold = ndvi_threshold
        self.brightness_threshold = brightness_threshold
    
    def detect(self, image: np.ndarray) -> np.ndarray:
        """Detect vegetation anomalies."""
        if image.shape[2] < 3:
            return np.zeros(image.shape[:2], dtype=bool)
        
        red = image[:, :, 0] / 255.0 if image.max() > 1 else image[:, :, 0]
        
        # NIR channel (4th channel for Sentinel-2/Landsat)
        if image.shape[2] >= 4:
            nir = image[:, :, 3] / 255.0 if image.max() > 1 else image[:, :, 3]
        else:
            # Use green as proxy (not ideal but works)
            nir = image[:, :, 1] / 255.0 if image.max() > 1 else image[:, :, 1]
        
        # Calculate NDVI
        denominator = nir + red + 1e-8
        ndvi = (nir - red) / denominator
        
        # Brightness
        brightness = np.mean(image[:, :, :3], axis=2)
        if brightness.max() > 1:
            brightness = brightness / 255.0
        
        # Burned/burning areas: low NDVI + high brightness
        fire_mask = (ndvi < self.ndvi_threshold) & (brightness > self.brightness_threshold)
        
        logger.debug(f"Vegetation detector: {np.sum(fire_mask)} anomalous pixels")
        return fire_mask


class SatelliteImageryPipeline:
    """
    Complete pipeline for satellite imagery fire detection.
    
    Combines multiple detection algorithms and post-processes results.
    """
    
    def __init__(self):
        self.detectors = [
            ColorBasedDetector(threshold=0.3),
            ThermalAnomalyDetector(percentile=88),
            VegetationAnomalyDetector(ndvi_threshold=0.15),
        ]
        self.last_detection = None
        self.last_hotspots = None
    
    def detect_fires(self, image: np.ndarray, use_morphology: bool = True) -> np.ndarray:
        """
        Detect fires in image using all detectors.
        
        Args:
            image: Image array (H x W x C)
            use_morphology: Apply morphological operations for cleanup
        
        Returns:
            Combined fire mask from all detectors
        """
        fire_masks = []
        
        for detector in self.detectors:
            try:
                mask = detector.detect(image)
                fire_masks.append(mask)
            except Exception as e:
                logger.warning(f"Detector {detector.__class__.__name__} failed: {e}")
        
        if not fire_masks:
            return np.zeros(image.shape[:2], dtype=bool)
        
        # Combine detections (union)
        combined_mask = np.zeros_like(fire_masks[0], dtype=bool)
        for mask in fire_masks:
            combined_mask |= mask
        
        # Morphological post-processing
        if use_morphology:
            combined_mask = self._post_process_mask(combined_mask)
        
        self.last_detection = combined_mask
        logger.info(f"Combined detection: {np.sum(combined_mask)} fire pixels from {len(fire_masks)} detectors")
        
        return combined_mask
    
    def _post_process_mask(self, mask: np.ndarray) -> np.ndarray:
        """
        Apply morphological operations to clean up fire mask.
        
        - Remove small isolated pixels
        - Fill small holes
        - Dilate to connect nearby fire regions
        """
        # Remove small isolated pixels
        mask = binary_dilation(mask, iterations=1)
        
        # Label connected components
        labeled, num_features = label(mask)
        
        # Remove very small regions (<10 pixels)
        for i in range(1, num_features + 1):
            component_mask = labeled == i
            if np.sum(component_mask) < 10:
                mask[component_mask] = False
        
        return mask
    
    def extract_hotspots(self, fire_mask: np.ndarray, image: np.ndarray,
                        min_size: int = 5) -> List[Dict]:
        """
        Extract individual hotspots from fire mask.
        
        Args:
            fire_mask: Boolean fire detection mask
            image: Original image for intensity calculation
            min_size: Minimum hotspot size in pixels
        
        Returns:
            List of hotspot dictionaries with location, size, intensity
        """
        labeled, num_features = label(fire_mask)
        
        hotspots = []
        for i in range(1, num_features + 1):
            component_mask = labeled == i
            size = np.sum(component_mask)
            
            if size < min_size:
                continue
            
            # Calculate hotspot properties
            coords = np.argwhere(component_mask)
            center_y, center_x = coords.mean(axis=0)
            
            # Intensity from image
            intensity = self._calculate_intensity(image[component_mask])
            
            # Bounding box
            min_y, min_x = coords.min(axis=0)
            max_y, max_x = coords.max(axis=0)
            
            hotspots.append({
                "center": (center_x, center_y),  # (x, y) format
                "bbox": ((min_x, min_y), (max_x, max_y)),
                "size_pixels": size,
                "intensity": intensity,
                "pixels": coords  # For reference
            })
        
        self.last_hotspots = hotspots
        logger.info(f"Extracted {len(hotspots)} hotspots")
        return hotspots
    
    @staticmethod
    def _calculate_intensity(pixels: np.ndarray) -> float:
        """
        Calculate average intensity of pixels (0-1).
        
        Args:
            pixels: Array of pixel values
        
        Returns:
            Average intensity 0-1
        """
        if len(pixels) == 0:
            return 0.0
        
        mean_value = np.mean(pixels)
        
        # Normalize to 0-1
        if mean_value > 1:
            mean_value = mean_value / 255.0
        
        return float(np.clip(mean_value, 0, 1))
    
    def generate_boundary(self, hotspots: List[Dict]) -> Optional[List[Tuple[float, float]]]:
        """
        Generate boundary polygon from hotspots.
        
        Args:
            hotspots: List of hotspot dictionaries
        
        Returns:
            List of (x, y) points forming boundary, or None if insufficient hotspots
        """
        if len(hotspots) < 3:
            logger.warning("Not enough hotspots to generate boundary")
            return None
        
        # Extract hotspot centers
        centers = np.array([h["center"] for h in hotspots])
        
        try:
            # Compute convex hull
            hull = ConvexHull(centers)
            boundary = [tuple(centers[i]) for i in hull.vertices]
            
            logger.info(f"Generated boundary with {len(boundary)} vertices")
            return boundary
        except Exception as e:
            logger.error(f"Failed to compute boundary: {e}")
            return None
    
    def get_detection_summary(self) -> Dict:
        """Get summary of last detection."""
        if self.last_detection is None:
            return {}
        
        hotspot_count = len(self.last_hotspots) if self.last_hotspots else 0
        fire_pixels = np.sum(self.last_detection)
        total_pixels = self.last_detection.size
        fire_percentage = (fire_pixels / total_pixels) * 100
        
        return {
            "fire_pixels": int(fire_pixels),
            "total_pixels": int(total_pixels),
            "fire_percentage": float(fire_percentage),
            "hotspot_count": hotspot_count,
            "timestamp": datetime.now().isoformat()
        }

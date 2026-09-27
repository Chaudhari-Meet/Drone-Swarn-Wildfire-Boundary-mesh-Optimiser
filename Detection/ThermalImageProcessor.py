"""
Thermal Image Processor - Process thermal images from drone cameras.

Features:
- Radiometric calibration and temperature conversion
- Fire hotspot detection from thermal data
- Integration with satellite imagery pipeline
- Temperature anomaly extraction
- Thermal boundary generation
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ThermalHotspot:
    """Thermal hotspot detection result."""
    center: Tuple[float, float]  # (row, col) pixel coordinates
    temperature: float  # Celsius
    intensity: float  # 0-1 normalized intensity
    area_pixels: int
    confidence: float  # 0-1


@dataclass
class ThermalCalibration:
    """Thermal camera calibration parameters."""
    # Black-body radiation constants
    R1: float = 68.4  # Calibration constant 1
    R2: float = 0.01  # Calibration constant 2
    B: float = 1428.0  # Planck's constant B
    F: float = 1.0  # Effective focal length
    O: float = 0.0  # Atmospheric offset
    
    # Temperature range (Celsius)
    min_temp: float = -40.0
    max_temp: float = 150.0
    
    # Camera parameters
    emissivity: float = 0.95  # Assumed emissivity
    ambient_temp: float = 25.0  # Ambient reference temperature


class ThermalImageProcessor:
    """Process thermal images for fire detection."""

    def __init__(self, calibration: Optional[ThermalCalibration] = None):
        self.calibration = calibration or ThermalCalibration()
        self.detection_threshold = 60.0  # Celsius - temperature threshold for fire
        self.hotspot_min_size = 3  # Minimum hotspot area in pixels

    def process_thermal_frame(self, thermal_data: np.ndarray) -> Dict:
        """
        Process a thermal image frame.

        Args:
            thermal_data: Thermal image (can be raw sensor values or pre-processed)

        Returns:
            Dictionary with detection results
        """
        if thermal_data.size == 0:
            return {
                'success': False,
                'error': 'Empty thermal data',
                'hotspots': [],
                'temperature_map': None,
            }

        try:
            # Convert raw values to temperature if needed
            temp_map = self._convert_to_temperature(thermal_data)

            # Detect hotspots
            hotspots = self._detect_hotspots(temp_map)

            # Filter by confidence
            filtered_hotspots = [h for h in hotspots if h.confidence > 0.5]

            return {
                'success': True,
                'temperature_map': temp_map,
                'hotspots': filtered_hotspots,
                'hotspot_count': len(filtered_hotspots),
                'max_temperature': np.max(temp_map) if temp_map.size > 0 else None,
                'mean_temperature': np.mean(temp_map) if temp_map.size > 0 else None,
                'processing_time': 0.0,
            }
        except Exception as e:
            logger.error(f"Error processing thermal frame: {e}")
            return {
                'success': False,
                'error': str(e),
                'hotspots': [],
            }

    def _convert_to_temperature(self, raw_thermal: np.ndarray) -> np.ndarray:
        """
        Convert raw thermal sensor values to temperature in Celsius.

        Uses radiometric calibration formula.
        """
        # Normalize raw values to 0-1 range (assuming 16-bit sensor: 0-65535)
        if raw_thermal.max() > 256:
            normalized = raw_thermal / 65535.0
        else:
            normalized = raw_thermal / 255.0

        # Apply inverse planck equation for temperature conversion
        # T = B / ln(R1 / (R2 * (normalized / emissivity)) + 1)

        # Avoid division by zero
        normalized = np.clip(normalized, 0.001, 0.999)

        # Temperature in Kelvin
        numerator = self.calibration.R1
        denominator = self.calibration.R2 * (normalized / self.calibration.emissivity)
        denominator = np.clip(denominator, 0.001, 1e6)  # Avoid log errors

        with np.errstate(divide='ignore', invalid='ignore'):
            temp_k = self.calibration.B / np.log(numerator / denominator + 1)

        # Convert to Celsius
        temp_c = temp_k - 273.15

        # Clamp to calibration range
        temp_c = np.clip(temp_c, self.calibration.min_temp, self.calibration.max_temp)

        return temp_c

    def _detect_hotspots(self, temp_map: np.ndarray) -> List[ThermalHotspot]:
        """Detect thermal hotspots in temperature map."""
        hotspots = []

        # Create binary mask of hot regions
        hot_mask = temp_map > self.detection_threshold

        if not hot_mask.any():
            return hotspots

        # Find connected components (hotspots)
        labeled = self._label_connected_components(hot_mask)

        # Extract features from each hotspot
        unique_labels = np.unique(labeled)
        for label in unique_labels:
            if label == 0:  # Skip background
                continue

            hotspot_mask = labeled == label
            hotspot_temps = temp_map[hotspot_mask]

            # Filter by size
            area = np.sum(hotspot_mask)
            if area < self.hotspot_min_size:
                continue

            # Calculate center of mass
            rows, cols = np.where(hotspot_mask)
            center = (np.mean(rows), np.mean(cols))

            # Calculate features
            max_temp = np.max(hotspot_temps)
            mean_temp = np.mean(hotspot_temps)
            normalized_temp = (max_temp - self.detection_threshold) / (self.calibration.max_temp - self.detection_threshold)
            intensity = np.clip(normalized_temp, 0, 1)

            # Confidence based on temperature and area
            confidence = min(0.5 + 0.5 * intensity, 1.0)

            hotspot = ThermalHotspot(
                center=center,
                temperature=max_temp,
                intensity=intensity,
                area_pixels=area,
                confidence=confidence,
            )
            hotspots.append(hotspot)

        return hotspots

    @staticmethod
    def _label_connected_components(binary_mask: np.ndarray) -> np.ndarray:
        """Simple connected component labeling."""
        labeled = np.zeros_like(binary_mask, dtype=np.int32)
        current_label = 0

        for i in range(binary_mask.shape[0]):
            for j in range(binary_mask.shape[1]):
                if binary_mask[i, j] and labeled[i, j] == 0:
                    current_label += 1
                    ThermalImageProcessor._flood_fill(binary_mask, labeled, i, j, current_label)

        return labeled

    @staticmethod
    def _flood_fill(mask: np.ndarray, labeled: np.ndarray, i: int, j: int, label: int):
        """Flood fill algorithm for connected component labeling."""
        stack = [(i, j)]

        while stack:
            ci, cj = stack.pop()

            if ci < 0 or ci >= mask.shape[0] or cj < 0 or cj >= mask.shape[1]:
                continue
            if not mask[ci, cj] or labeled[ci, cj] != 0:
                continue

            labeled[ci, cj] = label

            # Add neighbors
            stack.extend([(ci + 1, cj), (ci - 1, cj), (ci, cj + 1), (ci, cj - 1)])

    def extract_fire_observations(self, hotspots: List[ThermalHotspot],
                                 image_metadata: Dict) -> List[Dict]:
        """
        Convert thermal hotspots to fire observations.

        Args:
            hotspots: Detected thermal hotspots
            image_metadata: Metadata about the thermal image (GPS, altitude, etc.)

        Returns:
            List of fire observations
        """
        observations = []

        for hotspot in hotspots:
            # Convert pixel coordinates to geographic coordinates
            # This requires camera calibration and image metadata
            lat, lon = self._pixel_to_geo(
                hotspot.center,
                image_metadata.get('drone_lat'),
                image_metadata.get('drone_lon'),
                image_metadata.get('altitude_agl', 50),
                image_metadata.get('camera_fov', 60),
            )

            observation = {
                'latitude': lat,
                'longitude': lon,
                'temperature': hotspot.temperature,
                'intensity': hotspot.intensity,
                'area_pixels': hotspot.area_pixels,
                'confidence': hotspot.confidence,
                'source_type': 'thermal_drone',
                'timestamp': datetime.now(),
            }
            observations.append(observation)

        return observations

    @staticmethod
    def _pixel_to_geo(pixel_coord: Tuple[float, float], drone_lat: float, drone_lon: float,
                     altitude_agl: float, camera_fov: float) -> Tuple[float, float]:
        """
        Convert pixel coordinates to geographic coordinates.

        Simple approximation - in production would use proper camera matrix.
        """
        if drone_lat is None or drone_lon is None:
            return 0, 0

        row, col = pixel_coord

        # Simplified conversion (would need proper camera calibration)
        # Assuming 640x480 image, 60 degree FOV
        image_width, image_height = 640, 480
        horizontal_fov = camera_fov  # degrees
        vertical_fov = camera_fov * image_height / image_width

        # Convert FOV to radians
        h_fov_rad = np.radians(horizontal_fov)
        v_fov_rad = np.radians(vertical_fov)

        # Calculate ground distance
        # Assuming level flight and nadir view
        pixel_from_center_x = col - image_width / 2
        pixel_from_center_y = row - image_height / 2

        # Tangent of angle from center
        tan_h = np.tan(h_fov_rad / 2) * (pixel_from_center_x / (image_width / 2))
        tan_v = np.tan(v_fov_rad / 2) * (pixel_from_center_y / (image_height / 2))

        # Ground distance
        ground_dist_x = altitude_agl * tan_h
        ground_dist_y = altitude_agl * tan_v

        # Convert to geographic offset (approximate)
        # 1 degree latitude ≈ 111 km
        lat_offset = ground_dist_y / 111000
        lon_offset = ground_dist_x / (111000 * np.cos(np.radians(drone_lat)))

        return drone_lat + lat_offset, drone_lon + lon_offset

    def generate_thermal_boundary(self, hotspots: List[ThermalHotspot]) -> Optional[List[Tuple[float, float]]]:
        """
        Generate boundary from thermal hotspots using convex hull.

        Args:
            hotspots: List of detected thermal hotspots

        Returns:
            List of boundary points (lat, lon) or None if no hotspots
        """
        if not hotspots:
            return None

        # Get all hotspot centers in pixel space
        centers = np.array([h.center for h in hotspots])

        if len(centers) < 3:
            return [(centers[i, 0], centers[i, 1]) for i in range(len(centers))]

        # Compute convex hull
        hull_indices = self._convex_hull(centers)

        # Convert indices to points
        boundary = [(centers[i, 0], centers[i, 1]) for i in hull_indices]

        return boundary

    @staticmethod
    def _convex_hull(points: np.ndarray) -> List[int]:
        """Simple convex hull algorithm (Graham scan)."""
        if len(points) <= 2:
            return list(range(len(points)))

        # Find point with lowest y (or leftmost if tie)
        start_idx = np.argmin(points[:, 0] + points[:, 1] * 1e-6)
        start = points[start_idx]

        # Sort points by polar angle with respect to start point
        def polar_angle(p):
            dx = p[0] - start[0]
            dy = p[1] - start[1]
            return np.arctan2(dy, dx)

        indices = list(range(len(points)))
        indices.remove(start_idx)
        indices.sort(key=lambda i: polar_angle(points[i]))
        indices.insert(0, start_idx)

        # Build hull
        hull = [indices[0], indices[1]]

        for i in range(2, len(indices)):
            while len(hull) > 1:
                o = points[hull[-2]]
                a = points[hull[-1]]
                b = points[indices[i]]

                cross = (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
                if cross > 0:
                    break
                hull.pop()

            hull.append(indices[i])

        return hull


def create_synthetic_thermal_image(width: int = 320, height: int = 240,
                                  has_hotspots: bool = True) -> np.ndarray:
    """Create synthetic thermal image for testing."""
    # Background temperature (20-30 C)
    bg_temp = np.random.uniform(20, 30, (height, width))

    # Add some variation
    for _ in range(5):
        cy, cx = np.random.randint(0, height), np.random.randint(0, width)
        r = np.random.randint(5, 20)
        y, x = np.ogrid[-r:r + 1, -r:r + 1]
        mask = x * x + y * y <= r * r
        cy_slice = slice(max(0, cy - r), min(height, cy + r + 1))
        cx_slice = slice(max(0, cx - r), min(width, cx + r + 1))
        if mask.shape[0] <= (cy_slice.stop - cy_slice.start) and \
           mask.shape[1] <= (cx_slice.stop - cx_slice.start):
            continue
        temp_adjustment = np.random.uniform(-3, 3)
        bg_temp[cy_slice, cx_slice] += temp_adjustment

    # Add fire hotspots
    if has_hotspots:
        for _ in range(3):
            cy, cx = np.random.randint(50, height - 50), np.random.randint(50, width - 50)
            r = np.random.randint(5, 15)
            y, x = np.ogrid[-r:r + 1, -r:r + 1]
            mask = x * x + y * y <= r * r
            cy_slice = slice(max(0, cy - r), min(height, cy + r + 1))
            cx_slice = slice(max(0, cx - r), min(width, cx + r + 1))

            if mask.shape[0] > (cy_slice.stop - cy_slice.start) or \
               mask.shape[1] > (cx_slice.stop - cx_slice.start):
                continue

            # High temperature hotspot (80-100 C)
            hotspot_temp = np.random.uniform(80, 100)
            bg_temp[cy_slice, cx_slice] = hotspot_temp

    # Convert to 16-bit raw sensor values (0-65535)
    # Normalize 0-150 C range to sensor range
    normalized = np.clip((bg_temp - 0) / 150.0, 0, 1)
    raw_thermal = (normalized * 65535).astype(np.uint16)

    return raw_thermal

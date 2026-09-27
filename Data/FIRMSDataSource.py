"""
FIRMSDataSource - Real satellite fire hotspot data from NASA FIRMS.

Fetches near real-time fire detection data from multiple satellite platforms:
- MODIS (1 km resolution, 3 hour latency)
- VIIRS (375m resolution, 3 hour latency)
- Landsat (30m resolution, US/Canada only, 1 hour latency)

NASA FIRMS API: https://firms.modaps.eosdis.nasa.gov/api/
"""

import logging
import os
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from io import StringIO
from pathlib import Path

import requests
from scipy.spatial import ConvexHull
import numpy as np

from Data.DataSource import DataSource, FireObservation, FireBoundary

logger = logging.getLogger(__name__)


class FIRMSDataSource(DataSource):
    """
    Real satellite fire hotspot data from NASA FIRMS.
    
    Supports:
    - MODIS (Terra/Aqua) NRT and Standard Processing
    - VIIRS (Suomi-NPP, NOAA-20, NOAA-21) NRT and Standard Processing
    - Landsat NRT (US/Canada only)
    
    Provides near real-time fire detection with confidence scoring,
    fire radiative power (FRP), brightness temperature measurements.
    """
    
    def __init__(self, map_key: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize FIRMS data source.
        
        Args:
            map_key: NASA FIRMS MAP_KEY (free from https://firms.modaps.eosdis.nasa.gov/api/)
            cache_dir: Directory to cache API responses (reduces rate limiting)
        """
        super().__init__(
            name="NASA FIRMS - Real Satellite Data",
            source_type="satellite"
        )
        
        self.map_key = map_key or os.environ.get('FIRMS_MAP_KEY', 'DEMO_KEY')
        self.api_base = "https://firms.modaps.eosdis.nasa.gov/api/area"
        self.cache_dir = cache_dir or Path(__file__).parent.parent / "Temp" / "firms_cache"
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        
        self.supported_sources = {
            "MODIS_NRT": {
                "platform": "MODIS",
                "satellites": ["Terra (T)", "Aqua (A)"],
                "latency": "3 hours",
                "resolution": "1 km",
                "confidence_type": "numeric (0-100%)"
            },
            "VIIRS_SNPP_NRT": {
                "platform": "VIIRS",
                "satellites": ["Suomi-NPP"],
                "latency": "3 hours",
                "resolution": "375 m",
                "confidence_type": "categorical (Low/Nominal/High)"
            },
            "VIIRS_NOAA20_NRT": {
                "platform": "VIIRS",
                "satellites": ["NOAA-20"],
                "latency": "3 hours",
                "resolution": "375 m",
                "confidence_type": "categorical (Low/Nominal/High)"
            },
            "VIIRS_NOAA21_NRT": {
                "platform": "VIIRS",
                "satellites": ["NOAA-21"],
                "latency": "3 hours",
                "resolution": "375 m",
                "confidence_type": "categorical (Low/Nominal/High)"
            },
            "LANDSAT_NRT": {
                "platform": "Landsat",
                "satellites": ["Landsat 8/9"],
                "latency": "1 hour",
                "resolution": "30 m",
                "coverage": "US/Canada only",
                "confidence_type": "numeric (0-100%)"
            }
        }
        
        self.bbox = None
        self.day_range = 3
        self.observations = []
        self.error_message = None
        self.data_status = "UNINITIALIZED"
        self.last_api_call = None
        self.observations_by_source = {}
        
        logger.info(f"FIRMS DataSource initialized with MAP_KEY: {self.map_key[:10]}...")
    
    def initialize(self, bbox: Optional[Tuple[float, float, float, float]] = None, 
                   days_back: int = 3) -> bool:
        """
        Initialize by fetching fire data for region.
        
        Args:
            bbox: Bounding box (west, south, east, north) or None for world
            days_back: Number of days to query (1-5)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.bbox = bbox or (-180, -90, 180, 90)  # World
            self.day_range = min(max(1, days_back), 5)  # Clamp to 1-5
            
            logger.info(f"FIRMS: Fetching fire data for bbox {self.bbox}, {self.day_range} days back")
            
            # Fetch from multiple sources
            all_observations = []
            for source in ["MODIS_NRT", "VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT"]:
                try:
                    obs = self._fetch_from_api(source, self.bbox, self.day_range)
                    all_observations.extend(obs)
                    self.observations_by_source[source] = obs
                    logger.info(f"FIRMS: {source} returned {len(obs)} observations")
                except Exception as e:
                    logger.warning(f"FIRMS: {source} fetch failed: {e}")
            
            if not all_observations:
                self.data_status = "WARNING"
                self.error_message = "No fire data returned from FIRMS API"
                logger.warning(self.error_message)
                self.observations = []
                return False
            
            # Deduplicate observations from different satellites
            self.observations = self._deduplicate_observations(all_observations)
            
            # Generate boundary
            if self.observations:
                boundary_points = [(obs.latitude, obs.longitude) for obs in self.observations]
                self.boundary = self._generate_boundary(boundary_points)
            
            self.data_status = "READY"
            self.last_api_call = datetime.now()
            self.available = True
            
            logger.info(f"FIRMS: Initialized with {len(self.observations)} unique fire observations")
            return True
            
        except Exception as e:
            self.data_status = "ERROR"
            self.error_message = f"FIRMS initialization failed: {str(e)}"
            logger.error(self.error_message, exc_info=True)
            return False
    
    def _fetch_from_api(self, source: str, bbox: Tuple[float, float, float, float], 
                        day_range: int, date: Optional[str] = None) -> List[FireObservation]:
        """
        Fetch fire data from FIRMS API.
        
        Args:
            source: Data source (MODIS_NRT, VIIRS_SNPP_NRT, etc.)
            bbox: Bounding box (west, south, east, north)
            day_range: Days to query (1-5)
            date: Optional date (YYYY-MM-DD), defaults to today
        
        Returns:
            List of FireObservation objects
        """
        # Check cache first
        cache_key = f"{source}_{bbox}_{day_range}_{date or 'today'}"
        cache_file = Path(self.cache_dir) / f"{cache_key}.csv"
        
        if cache_file.exists():
            logger.info(f"FIRMS: Using cached data for {source}")
            with open(cache_file, 'r') as f:
                csv_data = f.read()
        else:
            # Build API URL
            west, south, east, north = bbox
            coords = f"{west},{south},{east},{north}"
            
            if date:
                url = f"{self.api_base}/csv/{self.map_key}/{source}/{coords}/{day_range}/{date}"
            else:
                url = f"{self.api_base}/csv/{self.map_key}/{source}/{coords}/{day_range}"
            
            logger.debug(f"FIRMS API URL: {url}")
            
            # Fetch from API with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    csv_data = response.text
                    
                    # Cache the response
                    with open(cache_file, 'w') as f:
                        f.write(csv_data)
                    
                    break
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"FIRMS API call {attempt + 1} failed, retrying: {e}")
                    else:
                        raise
        
        # Parse CSV response
        observations = self._parse_csv_response(csv_data, source)
        
        return observations
    
    def _parse_csv_response(self, csv_data: str, source_type: str) -> List[FireObservation]:
        """
        Parse NASA FIRMS CSV response into FireObservation objects.
        
        Handles both MODIS and VIIRS field formats.
        
        Args:
            csv_data: CSV response text
            source_type: Data source (MODIS_NRT, VIIRS_SNPP_NRT, etc.)
        
        Returns:
            List of FireObservation objects
        """
        observations = []
        
        try:
            reader = csv.DictReader(StringIO(csv_data))
            
            for row in reader:
                try:
                    # Extract common fields
                    latitude = float(row['latitude'])
                    longitude = float(row['longitude'])
                    
                    # Parse timestamp
                    acq_date = row['acq_date']  # YYYY-MM-DD
                    acq_time = row['acq_time']  # HHMM
                    timestamp = datetime.strptime(f"{acq_date} {acq_time}", "%Y-%m-%d %H%M")
                    
                    # Handle confidence (differs between MODIS and VIIRS)
                    if 'confidence' in row:
                        conf_str = row['confidence'].strip()
                        # VIIRS uses text: Low, Nominal, High
                        if conf_str in ['Low', 'Nominal', 'High']:
                            confidence_map = {'Low': 0.5, 'Nominal': 0.75, 'High': 0.95}
                            confidence = confidence_map.get(conf_str, 0.75)
                        else:
                            # MODIS uses numeric: 0-100
                            confidence = float(conf_str) / 100.0
                    else:
                        confidence = 0.75
                    
                    # Extract brightness temperature
                    temperature = None
                    if 'brightness' in row:  # MODIS
                        temperature = float(row['brightness'])
                    elif 'bright_ti4' in row:  # VIIRS
                        temperature = float(row['bright_ti4'])
                    
                    # Extract Fire Radiative Power (FRP)
                    frp = None
                    if 'frp' in row:
                        frp_str = row['frp'].strip()
                        if frp_str:
                            frp = float(frp_str)
                    
                    # Extract satellite info
                    satellite = row.get('satellite', 'Unknown')
                    daynight = row.get('daynight', 'Unknown')
                    
                    # Filter by confidence threshold
                    if confidence < 0.5:  # Skip low-confidence detections (<50%)
                        logger.debug(f"Skipping low-confidence detection at ({latitude}, {longitude})")
                        continue
                    
                    # Create observation
                    observation = FireObservation(
                        latitude=latitude,
                        longitude=longitude,
                        timestamp=timestamp,
                        confidence=confidence,
                        temperature=temperature,
                        fire_radiative_power=frp,
                        source=source_type,
                        metadata={
                            "satellite": satellite,
                            "daynight": daynight,
                            "source_type": source_type,
                            "platform": source_type.split('_')[0],
                            "processing": "NRT" if "NRT" in source_type else "SP"
                        }
                    )
                    
                    observations.append(observation)
                    
                except (ValueError, KeyError) as e:
                    logger.warning(f"Failed to parse FIRMS row: {e}")
                    continue
            
            logger.info(f"Parsed {len(observations)} observations from {source_type}")
            return observations
            
        except Exception as e:
            logger.error(f"Error parsing FIRMS CSV response: {e}")
            return []
    
    def _deduplicate_observations(self, observations: List[FireObservation], 
                                 max_distance_km: float = 0.5) -> List[FireObservation]:
        """
        Remove duplicate detections from different satellites.
        
        If two observations from different sources are within max_distance_km
        and within same time window, keep the one with highest confidence.
        
        Args:
            observations: List of observations (possibly from multiple satellites)
            max_distance_km: Maximum distance to consider as duplicate
        
        Returns:
            Deduplicated observations
        """
        if not observations:
            return []
        
        # Sort by confidence (descending)
        sorted_obs = sorted(observations, key=lambda o: o.confidence, reverse=True)
        
        deduplicated = []
        used_indices = set()
        
        for i, obs1 in enumerate(sorted_obs):
            if i in used_indices:
                continue
            
            deduplicated.append(obs1)
            used_indices.add(i)
            
            # Find and mark nearby observations as duplicates
            for j in range(i + 1, len(sorted_obs)):
                if j in used_indices:
                    continue
                
                obs2 = sorted_obs[j]
                
                # Calculate distance
                distance = self._haversine_distance(
                    obs1.latitude, obs1.longitude,
                    obs2.latitude, obs2.longitude
                )
                
                # Check if time difference is within 2 hours
                time_diff = abs((obs1.timestamp - obs2.timestamp).total_seconds() / 3600)
                
                if distance < max_distance_km and time_diff < 2:
                    used_indices.add(j)
                    logger.debug(f"Deduplicated observation at ({obs2.latitude:.2f}, {obs2.longitude:.2f})")
        
        logger.info(f"Deduplicated {len(observations)} → {len(deduplicated)} observations")
        return deduplicated
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km."""
        from math import radians, cos, sin, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of Earth in km
        
        return c * r
    
    def _generate_boundary(self, points: List[Tuple[float, float]]) -> FireBoundary:
        """
        Generate fire boundary from observations using convex hull.
        
        Args:
            points: List of (latitude, longitude) tuples
        
        Returns:
            FireBoundary object
        """
        if len(points) < 3:
            logger.warning("Not enough points to generate boundary")
            points = points if points else [(0, 0)] * 3
        
        try:
            # Use convex hull for boundary
            points_array = np.array(points)
            hull = ConvexHull(points_array)
            boundary_points = [tuple(points_array[i]) for i in hull.vertices]
        except Exception as e:
            logger.warning(f"Failed to compute convex hull: {e}, using all points")
            boundary_points = points
        
        return FireBoundary(
            boundary_points=boundary_points,
            timestamp=datetime.now(),
            confidence=0.75,  # Average FIRMS confidence
            source="FIRMS",
            method="convex_hull"
        )
    
    def get_fire_observations(self, location: Optional[Tuple[float, float]] = None,
                             radius_km: float = 100,
                             time_range_hours: int = 24) -> List[FireObservation]:
        """
        Get fire observations from FIRMS.
        
        Note: location and radius parameters ignored for FIRMS
        (queries are bounded by initialization bbox)
        
        Returns:
            List of FireObservation objects
        """
        if not self.observations:
            logger.warning("No fire observations available")
        
        return self.observations
    
    def get_fire_boundary(self) -> Optional[FireBoundary]:
        """Get fire boundary from observations."""
        return self.boundary
    
    def is_available(self) -> bool:
        """Check if FIRMS data source is available."""
        return self.available
    
    def get_observations_summary(self) -> Dict:
        """Get summary statistics of observations."""
        if not self.observations:
            return {
                "total": 0,
                "avg_confidence": 0,
                "avg_temperature": 0,
                "avg_frp": 0,
                "sources": {}
            }
        
        temps = [o.temperature for o in self.observations if o.temperature]
        frps = [o.fire_radiative_power for o in self.observations if o.fire_radiative_power]
        
        return {
            "total": len(self.observations),
            "avg_confidence": np.mean([o.confidence for o in self.observations]),
            "avg_temperature": np.mean(temps) if temps else 0,
            "max_frp": np.max(frps) if frps else 0,
            "avg_frp": np.mean(frps) if frps else 0,
            "sources": {
                source: len(obs)
                for source, obs in self.observations_by_source.items()
            }
        }
    
    def get_boundary_info(self) -> Dict:
        """Get information about fire boundary."""
        if not self.boundary:
            return {"exists": False}
        
        points = self.boundary.boundary_points
        lats = [p[0] for p in points]
        lons = [p[1] for p in points]
        
        return {
            "exists": True,
            "points": len(points),
            "center_lat": np.mean(lats),
            "center_lon": np.mean(lons),
            "min_lat": np.min(lats),
            "max_lat": np.max(lats),
            "min_lon": np.min(lons),
            "max_lon": np.max(lons)
        }
    
    def get_status(self) -> Dict:
        """Get comprehensive status information."""
        return {
            "name": self.name,
            "source_type": self.source_type,
            "data_origin": "NASA FIRMS - Real Satellite Fire Detection",
            "is_real_data": True,
            "available": self.available,
            "status": self.data_status,
            "last_update": self.last_api_call.isoformat() if self.last_api_call else None,
            "error_message": self.error_message,
            "observations": self.get_observations_summary(),
            "boundary": self.get_boundary_info(),
            "supported_sources": list(self.supported_sources.keys()),
            "map_key_configured": self.map_key != 'DEMO_KEY'
        }
    
    def validate_data(self) -> Tuple[bool, str]:
        """
        Validate data coherence and quality.
        
        Returns:
            Tuple of (is_valid, message)
        """
        if self.data_status == "UNINITIALIZED":
            return False, "Data source not initialized"
        
        if not self.observations:
            return False, "No fire observations available"
        
        # Check boundary
        if not self.boundary:
            return False, "Fire boundary not generated"
        
        if len(self.boundary.boundary_points) < 3:
            return False, "Insufficient boundary points"
        
        # Check observations
        invalid_coords = 0
        for obs in self.observations:
            if not (-90 <= obs.latitude <= 90) or not (-180 <= obs.longitude <= 180):
                invalid_coords += 1
        
        if invalid_coords > 0:
            return False, f"Invalid coordinates in {invalid_coords} observations"
        
        # Check confidence
        avg_confidence = np.mean([o.confidence for o in self.observations])
        if avg_confidence < 0.4:
            return False, f"Average confidence too low: {avg_confidence:.1%}"
        
        return True, f"FIRMS data validation passed - {len(self.observations)} observations, {len(self.boundary.boundary_points)} boundary points"
    
    def get_data_source_info(self) -> Dict:
        """Return FIRMS data source metadata."""
        return {
            "source_type": self.source_type,
            "data_origin": "NASA FIRMS - Real Satellite Fire Detection",
            "description": "Near real-time fire hotspot data from MODIS, VIIRS, Landsat satellites",
            "is_real_data": True,
            "confidence_level": 0.75,  # Typical for MODIS/VIIRS
            "latency_hours": 3,  # Global NRT latency
            "spatial_resolution_m": 375,  # VIIRS typical resolution
            "supported_formats": ["CSV", "KML", "Shapefile"],
            "supported_sources": self.supported_sources,
            "update_frequency": "Every 3 hours globally, <60 seconds in US/Canada",
            "coverage": "Global",
            "requires": ["map_key (free from FIRMS website)"],
            "website": "https://firms.modaps.eosdis.nasa.gov/",
            "api_url": "https://firms.modaps.eosdis.nasa.gov/api/area/csv/",
            "implementation_status": "FULL - Ready for production"
        }

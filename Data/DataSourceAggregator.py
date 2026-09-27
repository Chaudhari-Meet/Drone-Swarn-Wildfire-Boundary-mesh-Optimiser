"""
DataSourceAggregator - Combine observations from multiple data sources.

Handles:
- Multi-source data fusion (FIRMS + satellite imagery + drone data)
- Observation deduplication and merging
- Confidence scoring and conflict resolution
- Quality assessment and weighting
- Boundary fusion from multiple sources
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import numpy as np

from Data.DataSource import DataSource, FireObservation, FireBoundary

logger = logging.getLogger(__name__)


@dataclass
class AggregatedObservation:
    """Fire observation aggregated from multiple sources."""
    latitude: float
    longitude: float
    timestamp: datetime
    
    # Aggregated properties
    avg_confidence: float  # 0-1
    avg_temperature: Optional[float]  # Kelvin (may be None)
    avg_frp: Optional[float]  # Fire Radiative Power in MW (may be None)
    
    # Source tracking
    contributing_sources: List[str]  # List of source names
    observation_count: int  # How many observations merged
    weight: float  # 0-1, higher = more confident
    
    # Quality metrics
    spatial_std_dev_m: float  # Geographic spread of observations (meters)
    temporal_std_dev_s: float  # Time spread of observations (seconds)
    confidence_consistency: float  # 0-1, how consistent were source confidences


class ConflictResolver:
    """Resolve conflicts between observations from different sources."""
    
    # Confidence weights for different source types
    SOURCE_WEIGHTS = {
        "satellite_firms": 0.85,  # NASA FIRMS is authoritative for hotspots
        "satellite": 0.75,  # Satellite imagery (user-provided)
        "real_drone": 0.90,  # Real drone data (highest quality when available)
        "historical": 0.60,  # Historical data (lower priority, past events)
        "image_upload": 0.70,  # User-uploaded images
        "simulation": 0.40,  # Simulation (lowest priority)
    }
    
    def __init__(self, max_merge_distance_km: float = 0.5,
                 max_merge_time_hours: float = 2.0):
        """
        Initialize conflict resolver.
        
        Args:
            max_merge_distance_km: Distance threshold for merging observations
            max_merge_time_hours: Time threshold for merging observations
        """
        self.max_merge_distance_km = max_merge_distance_km
        self.max_merge_time_hours = max_merge_time_hours
    
    def resolve_conflicts(self, observations: List[FireObservation]) -> List[AggregatedObservation]:
        """
        Resolve conflicts and merge observations from multiple sources.
        
        Args:
            observations: List of observations from various sources
        
        Returns:
            List of merged aggregated observations
        """
        if not observations:
            return []
        
        # Sort by timestamp
        sorted_obs = sorted(observations, key=lambda o: o.timestamp)
        
        merged = []
        used_indices = set()
        
        for i, obs1 in enumerate(sorted_obs):
            if i in used_indices:
                continue
            
            # Find all observations that should be merged with this one
            group = [obs1]
            used_indices.add(i)
            
            for j in range(i + 1, len(sorted_obs)):
                if j in used_indices:
                    continue
                
                obs2 = sorted_obs[j]
                
                # Check if should merge
                if self._should_merge(obs1, obs2):
                    group.append(obs2)
                    used_indices.add(j)
            
            # Merge group into single aggregated observation
            if group:
                agg_obs = self._merge_observations(group)
                merged.append(agg_obs)
        
        logger.info(f"Resolved {len(observations)} observations → {len(merged)} aggregated observations")
        return merged
    
    def _should_merge(self, obs1: FireObservation, obs2: FireObservation) -> bool:
        """Check if two observations should be merged."""
        # Distance check
        distance_km = self._haversine_distance(
            obs1.latitude, obs1.longitude,
            obs2.latitude, obs2.longitude
        )
        
        if distance_km > self.max_merge_distance_km:
            return False
        
        # Time check
        time_diff_hours = abs((obs1.timestamp - obs2.timestamp).total_seconds() / 3600)
        
        if time_diff_hours > self.max_merge_time_hours:
            return False
        
        return True
    
    def _merge_observations(self, observations: List[FireObservation]) -> AggregatedObservation:
        """Merge multiple observations into one aggregated observation."""
        # Calculate weighted average position
        weights = [self.SOURCE_WEIGHTS.get(o.source, 0.5) for o in observations]
        total_weight = sum(weights)
        
        weighted_lat = sum(o.latitude * w for o, w in zip(observations, weights)) / total_weight
        weighted_lon = sum(o.longitude * w for o, w in zip(observations, weights)) / total_weight
        
        # Average confidence
        avg_confidence = np.mean([o.confidence for o in observations])
        
        # Average temperature (handle None values)
        temps = [o.temperature for o in observations if o.temperature is not None]
        avg_temperature = np.mean(temps) if temps else None
        
        # Average FRP
        frps = [o.fire_radiative_power for o in observations if o.fire_radiative_power is not None]
        avg_frp = np.mean(frps) if frps else None
        
        # Timestamp (use median)
        sorted_timestamps = sorted([o.timestamp for o in observations])
        timestamp = sorted_timestamps[len(sorted_timestamps) // 2]
        
        # Calculate spatial/temporal spread
        spatial_std = self._calculate_spatial_spread(observations)
        temporal_std = self._calculate_temporal_spread(observations)
        
        # Confidence consistency (std dev of confidences, inverted)
        confidence_std = np.std([o.confidence for o in observations])
        confidence_consistency = 1.0 - min(confidence_std, 1.0)
        
        # Overall weight (higher when consistent across sources)
        combined_weight = np.mean(weights) * confidence_consistency
        
        return AggregatedObservation(
            latitude=weighted_lat,
            longitude=weighted_lon,
            timestamp=timestamp,
            avg_confidence=avg_confidence,
            avg_temperature=avg_temperature,
            avg_frp=avg_frp,
            contributing_sources=[o.source for o in observations],
            observation_count=len(observations),
            weight=combined_weight,
            spatial_std_dev_m=spatial_std,
            temporal_std_dev_s=temporal_std,
            confidence_consistency=confidence_consistency
        )
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km."""
        from math import radians, cos, sin, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth radius in km
        
        return c * r
    
    @staticmethod
    def _calculate_spatial_spread(observations: List[FireObservation]) -> float:
        """Calculate spatial spread of observations in meters."""
        if len(observations) < 2:
            return 0.0
        
        coords = np.array([[o.latitude, o.longitude] for o in observations])
        center = coords.mean(axis=0)
        distances = np.linalg.norm(coords - center, axis=1)
        
        # Convert degrees to meters (approximate)
        distances_m = distances * 111000
        
        return float(np.std(distances_m))
    
    @staticmethod
    def _calculate_temporal_spread(observations: List[FireObservation]) -> float:
        """Calculate temporal spread of observations in seconds."""
        if len(observations) < 2:
            return 0.0
        
        timestamps = [o.timestamp for o in observations]
        times_s = [(t - timestamps[0]).total_seconds() for t in timestamps]
        
        return float(np.std(times_s))


class DataSourceAggregator:
    """
    Aggregate fire observations from multiple data sources.
    
    Combines observations with conflict resolution and confidence scoring.
    """
    
    def __init__(self, max_merge_distance_km: float = 0.5,
                 max_merge_time_hours: float = 2.0):
        """
        Initialize aggregator.
        
        Args:
            max_merge_distance_km: Distance threshold for merging observations
            max_merge_time_hours: Time threshold for merging observations
        """
        self.resolver = ConflictResolver(max_merge_distance_km, max_merge_time_hours)
        self.aggregated_observations = []
        self.source_stats = {}
    
    def aggregate_sources(self, data_sources: Dict[str, DataSource],
                         min_confidence: float = 0.4) -> List[AggregatedObservation]:
        """
        Aggregate observations from multiple data sources.
        
        Args:
            data_sources: Dictionary of {name: DataSource} to aggregate
            min_confidence: Minimum confidence threshold for observations
        
        Returns:
            List of aggregated observations
        """
        all_observations = []
        
        # Collect observations from all sources
        for source_name, source in data_sources.items():
            try:
                if not source.is_available():
                    logger.debug(f"Source {source_name} not available")
                    continue
                
                observations = source.get_fire_observations()
                
                if not observations:
                    logger.debug(f"Source {source_name} returned no observations")
                    continue
                
                # Filter by confidence
                filtered_obs = [o for o in observations if o.confidence >= min_confidence]
                
                # Add source name to metadata
                for obs in filtered_obs:
                    if obs.metadata is None:
                        obs.metadata = {}
                    obs.source = source_name
                
                all_observations.extend(filtered_obs)
                
                # Track source stats
                self.source_stats[source_name] = {
                    "total": len(observations),
                    "passed_filter": len(filtered_obs),
                    "confidence_avg": np.mean([o.confidence for o in filtered_obs]) if filtered_obs else 0
                }
                
                logger.info(f"Source {source_name}: {len(filtered_obs)}/{len(observations)} observations")
                
            except Exception as e:
                logger.error(f"Error aggregating from {source_name}: {e}")
                continue
        
        if not all_observations:
            logger.warning("No observations from any source")
            return []
        
        # Resolve conflicts and merge
        aggregated = self.resolver.resolve_conflicts(all_observations)
        
        # Sort by weight (highest confidence first)
        aggregated.sort(key=lambda o: o.weight, reverse=True)
        
        self.aggregated_observations = aggregated
        
        logger.info(f"Aggregated {len(all_observations)} observations from {len(data_sources)} sources → {len(aggregated)} final observations")
        
        return aggregated
    
    def aggregate_boundaries(self, data_sources: Dict[str, DataSource]) -> Optional[FireBoundary]:
        """
        Aggregate fire boundaries from multiple sources.
        
        Combines boundaries using union approach (maximum extent).
        
        Args:
            data_sources: Dictionary of {name: DataSource}
        
        Returns:
            Merged boundary or None
        """
        all_boundary_points = []
        
        for source_name, source in data_sources.items():
            try:
                if not source.is_available():
                    continue
                
                boundary = source.get_fire_boundary()
                
                if boundary and boundary.boundary_points:
                    all_boundary_points.extend(boundary.boundary_points)
                    logger.debug(f"Source {source_name}: {len(boundary.boundary_points)} boundary points")
                
            except Exception as e:
                logger.warning(f"Failed to get boundary from {source_name}: {e}")
                continue
        
        if not all_boundary_points or len(all_boundary_points) < 3:
            logger.warning("Not enough boundary points from sources")
            return None
        
        # Generate convex hull from all boundary points
        try:
            from scipy.spatial import ConvexHull
            
            points_array = np.array(all_boundary_points)
            hull = ConvexHull(points_array)
            merged_boundary_points = [tuple(points_array[i]) for i in hull.vertices]
            
            merged_boundary = FireBoundary(
                boundary_points=merged_boundary_points,
                timestamp=datetime.now(),
                confidence=0.7,  # Average confidence
                source="aggregated",
                method="convex_hull_union"
            )
            
            logger.info(f"Aggregated boundary: {len(all_boundary_points)} points → {len(merged_boundary_points)} vertices")
            return merged_boundary
            
        except Exception as e:
            logger.error(f"Failed to compute merged boundary: {e}")
            return None
    
    def get_aggregation_summary(self) -> Dict:
        """Get summary of aggregation results."""
        return {
            "total_aggregated": len(self.aggregated_observations),
            "source_stats": self.source_stats,
            "avg_weight": np.mean([o.weight for o in self.aggregated_observations]) if self.aggregated_observations else 0,
            "avg_confidence": np.mean([o.avg_confidence for o in self.aggregated_observations]) if self.aggregated_observations else 0,
            "observations": [
                {
                    "lat": o.latitude,
                    "lon": o.longitude,
                    "confidence": o.avg_confidence,
                    "sources": o.contributing_sources,
                    "weight": o.weight
                }
                for o in self.aggregated_observations[:10]  # Top 10
            ]
        }
    
    def filter_by_weight(self, observations: List[AggregatedObservation],
                        min_weight: float = 0.5) -> List[AggregatedObservation]:
        """
        Filter aggregated observations by confidence weight.
        
        Args:
            observations: List of aggregated observations
            min_weight: Minimum weight threshold
        
        Returns:
            Filtered observations
        """
        filtered = [o for o in observations if o.weight >= min_weight]
        logger.info(f"Weight filter: {len(observations)} → {len(filtered)} observations (threshold: {min_weight})")
        return filtered
    
    def deduplicate_final(self, observations: List[AggregatedObservation],
                         distance_km: float = 0.2) -> List[AggregatedObservation]:
        """
        Final deduplication pass on aggregated observations.
        
        Removes very close observations that may have slipped through.
        
        Args:
            observations: Aggregated observations
            distance_km: Distance threshold for deduplication
        
        Returns:
            Deduplicated observations
        """
        if len(observations) < 2:
            return observations
        
        # Sort by weight
        sorted_obs = sorted(observations, key=lambda o: o.weight, reverse=True)
        
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
                distance = self.resolver._haversine_distance(
                    obs1.latitude, obs1.longitude,
                    obs2.latitude, obs2.longitude
                )
                
                if distance < distance_km:
                    used_indices.add(j)
        
        logger.info(f"Final deduplication: {len(observations)} → {len(deduplicated)}")
        return deduplicated

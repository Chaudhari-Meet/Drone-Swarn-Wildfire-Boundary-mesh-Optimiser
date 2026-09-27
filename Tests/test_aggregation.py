"""
Test DataSourceAggregator with mock data sources.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from Data.DataSource import FireObservation
from Data.DataSourceAggregator import DataSourceAggregator, ConflictResolver, AggregatedObservation
from Data.SimulationDataSource import SimulationDataSource
from Data.FIRMSDataSource import FIRMSDataSource


def test_conflict_resolver_should_merge():
    """Test conflict resolver merging logic."""
    print("\n[TEST] Conflict Resolver - Should Merge")
    print("=" * 60)
    
    resolver = ConflictResolver(max_merge_distance_km=1.0, max_merge_time_hours=2.0)
    
    # Create two nearby observations
    obs1 = FireObservation(
        latitude=35.0,
        longitude=-120.0,
        timestamp=datetime(2026, 9, 25, 10, 0),
        confidence=0.8,
        temperature=320,
        fire_radiative_power=200,
        source="satellite_firms"
    )
    
    obs2 = FireObservation(
        latitude=35.001,  # ~111 meters away
        longitude=-120.001,
        timestamp=datetime(2026, 9, 25, 10, 30),  # 30 minutes later
        confidence=0.75,
        temperature=315,
        fire_radiative_power=180,
        source="real_drone"
    )
    
    # Should merge
    should_merge = resolver._should_merge(obs1, obs2)
    assert should_merge == True, "Should merge nearby observations within time window"
    
    print(f"\n  Obs1: (35.000, -120.000) @ 10:00, confidence=0.80")
    print(f"  Obs2: (35.001, -120.001) @ 10:30, confidence=0.75")
    print(f"  Distance: ~111m, Time difference: 30 min")
    print(f"  Should merge: {should_merge} [OK]")
    
    return True


def test_conflict_resolver_should_not_merge():
    """Test conflict resolver not merging when appropriate."""
    print("\n[TEST] Conflict Resolver - Should NOT Merge")
    print("=" * 60)
    
    resolver = ConflictResolver(max_merge_distance_km=1.0, max_merge_time_hours=2.0)
    
    # Create distant observations
    obs1 = FireObservation(
        latitude=35.0,
        longitude=-120.0,
        timestamp=datetime(2026, 9, 25, 10, 0),
        confidence=0.8,
        temperature=320,
        fire_radiative_power=200,
        source="satellite_firms"
    )
    
    obs2 = FireObservation(
        latitude=35.05,  # ~5.5 km away
        longitude=-120.05,
        timestamp=datetime(2026, 9, 25, 10, 0),
        confidence=0.75,
        temperature=315,
        fire_radiative_power=180,
        source="real_drone"
    )
    
    # Should NOT merge (too far)
    should_merge = resolver._should_merge(obs1, obs2)
    assert should_merge == False, "Should not merge distant observations"
    
    print(f"\n  Obs1: (35.000, -120.000)")
    print(f"  Obs2: (35.050, -120.050)")
    print(f"  Distance: ~7.8 km (exceeds 1.0 km threshold)")
    print(f"  Should merge: {should_merge} [OK]")
    
    return True


def test_merge_observations():
    """Test merging multiple observations."""
    print("\n[TEST] Merge Multiple Observations")
    print("=" * 60)
    
    resolver = ConflictResolver()
    
    # Create group of observations to merge
    observations = [
        FireObservation(
            latitude=35.0,
            longitude=-120.0,
            timestamp=datetime(2026, 9, 25, 10, 0),
            confidence=0.90,
            temperature=330,
            fire_radiative_power=250,
            source="satellite_firms"
        ),
        FireObservation(
            latitude=35.0005,
            longitude=-120.0005,
            timestamp=datetime(2026, 9, 25, 10, 15),
            confidence=0.75,
            temperature=310,
            fire_radiative_power=200,
            source="real_drone"
        ),
        FireObservation(
            latitude=35.0010,
            longitude=-120.0010,
            timestamp=datetime(2026, 9, 25, 10, 30),
            confidence=0.80,
            temperature=320,
            fire_radiative_power=220,
            source="image_upload"
        ),
    ]
    
    # Merge
    merged = resolver._merge_observations(observations)
    
    assert isinstance(merged, AggregatedObservation)
    assert merged.observation_count == 3
    assert len(merged.contributing_sources) == 3
    assert 34.999 < merged.latitude < 35.002
    assert -120.002 < merged.longitude < -120.000
    
    print(f"\n  Merged {len(observations)} observations:")
    print(f"    Sources: {', '.join(merged.contributing_sources)}")
    print(f"    Position: ({merged.latitude:.4f}, {merged.longitude:.4f})")
    print(f"    Avg confidence: {merged.avg_confidence:.2f}")
    print(f"    Avg temperature: {merged.avg_temperature:.0f} K")
    print(f"    Avg FRP: {merged.avg_frp:.0f} MW")
    print(f"    Weight: {merged.weight:.2f}")
    print(f"\n[OK] Observations merged correctly")
    
    return True


def test_aggregator_integration():
    """Test aggregator with real data sources."""
    print("\n[TEST] Aggregator Integration")
    print("=" * 60)
    
    aggregator = DataSourceAggregator(max_merge_distance_km=2.0, max_merge_time_hours=3.0)
    
    # Create data sources
    data_sources = {
        "simulation_small": SimulationDataSource("small_fire"),
        "simulation_medium": SimulationDataSource("medium_fire"),
    }
    
    # Initialize sources
    for name, source in data_sources.items():
        source.initialize()
    
    # Aggregate
    aggregated = aggregator.aggregate_sources(data_sources, min_confidence=0.5)
    
    print(f"\n  Created {len(data_sources)} data sources")
    print(f"  Aggregated into {len(aggregated)} observations")
    
    # Check source stats
    summary = aggregator.get_aggregation_summary()
    print(f"\n  Source statistics:")
    for source_name, stats in summary['source_stats'].items():
        print(f"    {source_name}: {stats['passed_filter']}/{stats['total']} observations")
    
    assert len(aggregated) > 0, "Should have aggregated observations"
    assert summary['avg_confidence'] > 0, "Should have average confidence"
    
    print(f"\n  Average aggregated confidence: {summary['avg_confidence']:.2f}")
    print(f"  Average weight: {summary['avg_weight']:.2f}")
    
    print(f"\n[OK] Aggregator integration working")
    
    return True


def test_weight_filtering():
    """Test filtering by weight."""
    print("\n[TEST] Weight-Based Filtering")
    print("=" * 60)
    
    # Create mock aggregated observations
    observations = [
        AggregatedObservation(
            latitude=35.0, longitude=-120.0, timestamp=datetime.now(),
            avg_confidence=0.9, avg_temperature=320, avg_frp=250,
            contributing_sources=["satellite_firms", "real_drone"],
            observation_count=2, weight=0.95,
            spatial_std_dev_m=50, temporal_std_dev_s=300, confidence_consistency=0.98
        ),
        AggregatedObservation(
            latitude=35.1, longitude=-120.1, timestamp=datetime.now(),
            avg_confidence=0.7, avg_temperature=310, avg_frp=180,
            contributing_sources=["image_upload"],
            observation_count=1, weight=0.65,
            spatial_std_dev_m=0, temporal_std_dev_s=0, confidence_consistency=1.0
        ),
        AggregatedObservation(
            latitude=35.2, longitude=-120.2, timestamp=datetime.now(),
            avg_confidence=0.5, avg_temperature=300, avg_frp=100,
            contributing_sources=["simulation"],
            observation_count=1, weight=0.35,
            spatial_std_dev_m=0, temporal_std_dev_s=0, confidence_consistency=1.0
        ),
    ]
    
    aggregator = DataSourceAggregator()
    aggregator.aggregated_observations = observations
    
    # Filter by weight
    filtered = aggregator.filter_by_weight(observations, min_weight=0.6)
    
    print(f"\n  Original: {len(observations)} observations")
    print(f"  After filtering (min_weight=0.6): {len(filtered)} observations")
    
    assert len(filtered) == 2, "Should have 2 observations with weight >= 0.6"
    assert all(o.weight >= 0.6 for o in filtered), "All should meet threshold"
    
    print(f"\n  Filtered observations:")
    for obs in filtered:
        print(f"    Weight: {obs.weight:.2f}, Sources: {', '.join(obs.contributing_sources)}")
    
    print(f"\n[OK] Weight filtering working")
    
    return True


def test_final_deduplication():
    """Test final deduplication pass."""
    print("\n[TEST] Final Deduplication")
    print("=" * 60)
    
    # Create mock observations with near-duplicates
    observations = [
        AggregatedObservation(
            latitude=35.0, longitude=-120.0, timestamp=datetime.now(),
            avg_confidence=0.9, avg_temperature=320, avg_frp=250,
            contributing_sources=["satellite_firms"],
            observation_count=2, weight=0.95,
            spatial_std_dev_m=50, temporal_std_dev_s=300, confidence_consistency=0.98
        ),
        AggregatedObservation(
            latitude=35.00001, longitude=-120.00001, timestamp=datetime.now(),  # ~1m away
            avg_confidence=0.7, avg_temperature=310, avg_frp=180,
            contributing_sources=["image_upload"],
            observation_count=1, weight=0.65,
            spatial_std_dev_m=0, temporal_std_dev_s=0, confidence_consistency=1.0
        ),
        AggregatedObservation(
            latitude=35.1, longitude=-120.1, timestamp=datetime.now(),
            avg_confidence=0.8, avg_temperature=315, avg_frp=220,
            contributing_sources=["real_drone"],
            observation_count=1, weight=0.85,
            spatial_std_dev_m=0, temporal_std_dev_s=0, confidence_consistency=1.0
        ),
    ]
    
    aggregator = DataSourceAggregator()
    deduplicated = aggregator.deduplicate_final(observations, distance_km=0.1)
    
    print(f"\n  Original: {len(observations)} observations")
    print(f"  After final deduplication: {len(deduplicated)} observations")
    
    # First two are very close, should be deduplicated
    assert len(deduplicated) == 2, "Should have 2 observations after deduplication"
    
    print(f"\n  Kept observations (highest weight first):")
    for obs in deduplicated:
        print(f"    ({obs.latitude:.5f}, {obs.longitude:.5f}) weight={obs.weight:.2f}")
    
    print(f"\n[OK] Final deduplication working")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Data Source Aggregation Testing")
    print("=" * 60)
    
    all_passed = True
    tests = [
        test_conflict_resolver_should_merge,
        test_conflict_resolver_should_not_merge,
        test_merge_observations,
        test_aggregator_integration,
        test_weight_filtering,
        test_final_deduplication,
    ]
    
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"\n[FAIL] {test.__name__}: {e}")
            all_passed = False
        except Exception as e:
            print(f"\n[FAIL] {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] All aggregation tests passed!")
    else:
        print("[FAIL] Some tests failed")
    print("=" * 60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

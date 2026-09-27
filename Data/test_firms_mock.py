"""
Test FIRMSDataSource with mock API responses.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from Data.FIRMSDataSource import FIRMSDataSource


def test_firms_mock_modis():
    """Test FIRMS parsing of mock MODIS data."""
    print("\n[TEST] FIRMS Mock MODIS Data Parsing")
    print("=" * 60)
    
    # Mock MODIS CSV response
    mock_modis = """latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,confidence,version,bright_t31,frp,type,daynight
35.2451,-120.1234,321.45,1.0,1.0,2026-09-25,1430,T,85,6.1NRT,298.32,250.5,0,D
35.2480,-120.1200,319.20,1.0,1.0,2026-09-25,1430,T,72,6.1NRT,296.15,180.3,0,D
35.2500,-120.1300,318.50,1.0,1.0,2026-09-25,1430,T,45,6.1NRT,295.80,120.0,0,D"""
    
    # Create FIRMS source
    firms = FIRMSDataSource(map_key="DEMO_KEY")
    
    # Parse mock data
    observations = firms._parse_csv_response(mock_modis, "MODIS_NRT")
    
    print(f"[OK] Parsed {len(observations)} MODIS observations")
    
    for i, obs in enumerate(observations):
        print(f"\n  Observation {i+1}:")
        print(f"    Position: ({obs.latitude:.4f}, {obs.longitude:.4f})")
        print(f"    Timestamp: {obs.timestamp}")
        print(f"    Confidence: {obs.confidence:.1%}")
        print(f"    Temperature: {obs.temperature:.1f} K")
        print(f"    FRP: {obs.fire_radiative_power:.1f} MW")
        print(f"    Satellite: {obs.metadata.get('satellite')}")
    
    # Check filtering: should skip low confidence (45%)
    assert len(observations) == 2, f"Expected 2 observations (>40% confidence), got {len(observations)}"
    print(f"\n[OK] Low confidence observation filtered out")
    
    return True


def test_firms_mock_viirs():
    """Test FIRMS parsing of mock VIIRS data."""
    print("\n[TEST] FIRMS Mock VIIRS Data Parsing")
    print("=" * 60)
    
    # Mock VIIRS CSV response
    mock_viirs = """latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti5,frp,daynight
35.2451,-120.1234,321.45,0.375,0.375,2026-09-25,1430,N20,High,1.0NRT,298.32,250.5,D
35.2480,-120.1200,319.20,0.375,0.375,2026-09-25,1430,N20,Nominal,1.0NRT,296.15,180.3,D
35.2500,-120.1300,318.50,0.375,0.375,2026-09-25,1430,N20,Low,1.0NRT,295.80,120.0,D"""
    
    # Create FIRMS source
    firms = FIRMSDataSource(map_key="DEMO_KEY")
    
    # Parse mock data
    observations = firms._parse_csv_response(mock_viirs, "VIIRS_NOAA20_NRT")
    
    print(f"[OK] Parsed {len(observations)} VIIRS observations")
    
    for i, obs in enumerate(observations):
        print(f"\n  Observation {i+1}:")
        print(f"    Position: ({obs.latitude:.4f}, {obs.longitude:.4f})")
        print(f"    Confidence: {obs.confidence:.1%}")
        print(f"    Satellite: {obs.metadata.get('satellite')}")
    
    # Check confidence mapping: High=0.95, Nominal=0.75, Low=0.5
    assert observations[0].confidence == 0.95, "High confidence should map to 0.95"
    assert observations[1].confidence == 0.75, "Nominal confidence should map to 0.75"
    assert observations[2].confidence == 0.5, "Low confidence should map to 0.5"
    
    # All three should be included (threshold is <0.5, so 0.5 and above are included)
    assert len(observations) == 3, f"Expected 3 observations (>=50% threshold), got {len(observations)}"
    print(f"\n[OK] Confidence text to numeric mapping correct")
    print(f"[OK] All confidence levels >= 50% included")
    
    return True


def test_firms_deduplication():
    """Test FIRMS deduplication of nearby observations."""
    print("\n[TEST] FIRMS Observation Deduplication")
    print("=" * 60)
    
    from Data.DataSource import FireObservation
    
    # Create mock observations from different satellites at same location
    obs1 = FireObservation(
        latitude=35.2451,
        longitude=-120.1234,
        timestamp=datetime(2026, 9, 25, 14, 30),
        confidence=0.85,
        temperature=321.45,
        fire_radiative_power=250.5,
        source="MODIS_NRT"
    )
    
    obs2 = FireObservation(
        latitude=35.2453,  # 0.0002 degrees ≈ 22 meters away
        longitude=-120.1236,
        timestamp=datetime(2026, 9, 25, 14, 31),  # 1 minute later
        confidence=0.75,
        temperature=319.20,
        fire_radiative_power=240.0,
        source="VIIRS_NOAA20_NRT"
    )
    
    obs3 = FireObservation(
        latitude=35.3000,  # Far away
        longitude=-120.2000,
        timestamp=datetime(2026, 9, 25, 14, 30),
        confidence=0.70,
        temperature=315.0,
        fire_radiative_power=150.0,
        source="MODIS_NRT"
    )
    
    firms = FIRMSDataSource(map_key="DEMO_KEY")
    deduplicated = firms._deduplicate_observations([obs1, obs2, obs3])
    
    print(f"[OK] Deduplication: {3} → {len(deduplicated)} observations")
    
    assert len(deduplicated) == 2, f"Expected 2 observations after deduplication, got {len(deduplicated)}"
    assert deduplicated[0].confidence == 0.85, "Should keep highest confidence observation"
    print(f"[OK] Kept highest confidence (0.85) duplicate")
    print(f"[OK] Kept distant observation (separate fire)")
    
    return True


def test_firms_boundary_generation():
    """Test FIRMS boundary generation."""
    print("\n[TEST] FIRMS Boundary Generation")
    print("=" * 60)
    
    from Data.DataSource import FireObservation
    
    # Create observations forming a triangle
    points = [
        (35.0, -120.0),
        (35.5, -119.5),
        (34.5, -119.5),
        (35.2, -119.8),  # Interior point
    ]
    
    firms = FIRMSDataSource(map_key="DEMO_KEY")
    boundary = firms._generate_boundary(points)
    
    print(f"[OK] Generated boundary with {len(boundary.boundary_points)} points")
    
    # Convex hull should have 3 points (triangle vertices)
    assert len(boundary.boundary_points) == 3, f"Expected 3 boundary points, got {len(boundary.boundary_points)}"
    print(f"[OK] Convex hull correctly computed (3 vertices)")
    
    for i, (lat, lon) in enumerate(boundary.boundary_points):
        print(f"  Vertex {i+1}: ({lat:.1f}, {lon:.1f})")
    
    return True


def test_firms_haversine_distance():
    """Test Haversine distance calculation."""
    print("\n[TEST] FIRMS Haversine Distance")
    print("=" * 60)
    
    firms = FIRMSDataSource(map_key="DEMO_KEY")
    
    # Test 1: Same location
    dist = firms._haversine_distance(35.0, -120.0, 35.0, -120.0)
    assert abs(dist) < 0.001, f"Same location should be ~0 km, got {dist}"
    print(f"[OK] Same location: {dist:.3f} km")
    
    # Test 2: Known distance
    # San Francisco (37.77, -122.42) to Los Angeles (34.05, -118.24) ≈ 559 km
    dist = firms._haversine_distance(37.77, -122.42, 34.05, -118.24)
    assert 550 < dist < 570, f"SF to LA should be ~559 km, got {dist:.1f}"
    print(f"[OK] SF to LA: {dist:.1f} km (expected ~559)")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("FIRMS DataSource Mock Testing")
    print("=" * 60)
    
    all_passed = True
    tests = [
        test_firms_mock_modis,
        test_firms_mock_viirs,
        test_firms_deduplication,
        test_firms_boundary_generation,
        test_firms_haversine_distance,
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
        print("[SUCCESS] All FIRMS mock tests passed!")
    else:
        print("[FAIL] Some tests failed")
    print("=" * 60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

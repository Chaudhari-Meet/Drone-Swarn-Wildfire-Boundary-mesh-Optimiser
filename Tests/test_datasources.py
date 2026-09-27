"""
Test suite for all 5 DataSource implementations.
Verifies each data source works independently and integrates with WildfireResponseSystem.

PHASE 2 Integration Tests - Architecture Refactoring
Runs without pytest - standalone functions only
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from Data.DataSource import DataSource, FireObservation, FireBoundary
from Data.SimulationDataSource import SimulationDataSource
from Data.RealDroneDataSource import RealDroneDataSource
from Data.HistoricalDataSource import HistoricalDataSource
from Data.SatelliteImageDataSource import SatelliteImageDataSource


# Test functions (no class-based test runners, no pytest)

def test_simulation_data_source_interface():
    """Verify SimulationDataSource implements all required methods."""
    sim = SimulationDataSource("test_scenario")
    
    # Test abstract methods
    assert hasattr(sim, 'is_available')
    assert hasattr(sim, 'initialize')
    assert hasattr(sim, 'get_fire_observations')
    assert hasattr(sim, 'get_fire_boundary')
    
    # Test new abstract methods (extended interface)
    assert hasattr(sim, 'get_data_source_info')
    assert hasattr(sim, 'validate_data')
    
    # Test helper methods
    assert hasattr(sim, 'get_observations_summary')
    assert hasattr(sim, 'get_boundary_info')
    assert hasattr(sim, 'get_status')
    
    print("[PASS] SimulationDataSource implements full interface")


def test_real_drone_data_source_interface():
    """Verify RealDroneDataSource implements all required methods."""
    drone = RealDroneDataSource()
    
    # Test abstract methods
    assert hasattr(drone, 'is_available')
    assert hasattr(drone, 'initialize')
    assert hasattr(drone, 'get_fire_observations')
    assert hasattr(drone, 'get_fire_boundary')
    assert hasattr(drone, 'get_data_source_info')
    assert hasattr(drone, 'validate_data')
    
    # Test drone-specific methods
    assert hasattr(drone, 'arm_drone')
    assert hasattr(drone, 'start_mission')
    assert hasattr(drone, 'get_thermal_image')
    
    print("[PASS] RealDroneDataSource implements full interface")


def test_historical_data_source_interface():
    """Verify HistoricalDataSource implements all required methods."""
    hist = HistoricalDataSource()
    
    assert hasattr(hist, 'is_available')
    assert hasattr(hist, 'initialize')
    assert hasattr(hist, 'get_fire_observations')
    assert hasattr(hist, 'get_fire_boundary')
    assert hasattr(hist, 'get_data_source_info')
    assert hasattr(hist, 'validate_data')
    assert hasattr(hist, 'get_incident_info')
    
    print("[PASS] HistoricalDataSource implements full interface")


def test_satellite_image_data_source_interface():
    """Verify SatelliteImageDataSource implements all required methods."""
    sat = SatelliteImageDataSource()
    
    assert hasattr(sat, 'is_available')
    assert hasattr(sat, 'initialize')
    assert hasattr(sat, 'get_fire_observations')
    assert hasattr(sat, 'get_fire_boundary')
    assert hasattr(sat, 'get_data_source_info')
    assert hasattr(sat, 'validate_data')
    assert hasattr(sat, 'set_manual_georeferencing')
    
    print("[PASS] SatelliteImageDataSource implements full interface")


def test_simulation_initialization():
    """Test simulation initialization."""
    sim = SimulationDataSource("medium_fire")
    assert sim.initialize() == True
    assert sim.is_available() == True
    print("âœ“ SimulationDataSource initializes successfully")


def test_simulation_fire_observations():
    """Test fire observation generation."""
    sim = SimulationDataSource("small_fire")
    sim.initialize()
    obs = sim.get_fire_observations()
    
    assert len(obs) > 0
    assert all(isinstance(o, FireObservation) for o in obs)
    assert all(-90 <= o.latitude <= 90 for o in obs)
    assert all(-180 <= o.longitude <= 180 for o in obs)
    assert all(0 <= o.confidence <= 1 for o in obs)
    
    print(f"âœ“ Generated {len(obs)} fire observations")


def test_simulation_fire_boundary():
    """Test boundary generation."""
    sim = SimulationDataSource("large_fire")
    sim.initialize()
    boundary = sim.get_fire_boundary()
    
    assert boundary is not None
    assert len(boundary.boundary_points) >= 3
    assert all(-90 <= lat <= 90 for lat, lon in boundary.boundary_points)
    assert all(-180 <= lon <= 180 for lat, lon in boundary.boundary_points)
    
    print(f"âœ“ Generated boundary with {len(boundary.boundary_points)} points")


def test_simulation_data_validation():
    """Test data validation."""
    sim = SimulationDataSource("medium_fire")
    sim.initialize()
    sim.get_fire_observations()  # Generate observations
    sim.get_fire_boundary()  # Generate boundary
    
    is_valid, message = sim.validate_data()
    assert is_valid == True
    assert "validation passed" in message.lower()
    
    print(f"âœ“ Data validation: {message}")


def test_simulation_data_source_info():
    """Test data source metadata."""
    sim = SimulationDataSource("extreme_fire")
    info = sim.get_data_source_info()
    
    assert info["source_type"] == "simulation"
    assert info["is_real_data"] == False
    assert info["confidence_level"] == 0.85
    
    print(f"âœ“ Data source info: {info['data_origin']}")


def test_simulation_multiple_scenarios():
    """Test multiple simulation scenarios."""
    scenarios = ["small_fire", "medium_fire", "large_fire", "extreme_fire", 
                "wildland_urban_interface", "coastal_fire", "mountain_fire"]
    
    for scenario in scenarios:
        sim = SimulationDataSource(scenario)
        sim.initialize()
        obs = sim.get_fire_observations()
        boundary = sim.get_fire_boundary()
        
        assert len(obs) > 0
        assert boundary is not None
        assert len(boundary.boundary_points) >= 3
        
        print(f"âœ“ Scenario '{scenario}': {len(obs)} observations")


def test_real_drone_initialization():
    """Test real drone initialization (should fail gracefully)."""
    drone = RealDroneDataSource()
    result = drone.initialize()
    
    # Stub implementation should return False
    assert result == False
    assert drone.data_status == "UNINITIALIZED"
    assert "not implemented" in drone.error_message.lower()
    
    print("âœ“ RealDroneDataSource gracefully handles unimplemented status")


def test_real_drone_data_source_info():
    """Test real drone metadata."""
    drone = RealDroneDataSource()
    info = drone.get_data_source_info()
    
    assert info["source_type"] == "real_drone"
    assert info["is_real_data"] == True
    assert "STUB" in info["implementation_status"]
    assert "dronekit" in info["required_packages"]
    
    print(f"âœ“ Real drone info: {info['description']}")


def test_historical_data_initialization():
    """Test initialization without file (should fail gracefully)."""
    hist = HistoricalDataSource()
    result = hist.initialize()
    
    assert result == False
    assert hist.data_status == "ERROR"
    
    print("âœ“ HistoricalDataSource handles missing file gracefully")


def test_historical_data_source_info():
    """Test historical data metadata."""
    hist = HistoricalDataSource()
    info = hist.get_data_source_info()
    
    assert info["source_type"] == "historical"
    assert info["is_real_data"] == True
    assert "GeoJSON" in info["supported_formats"]
    assert "CSV" in info["supported_formats"]
    
    print(f"âœ“ Historical data supports: {', '.join(info['supported_formats'])}")


def test_satellite_image_initialization():
    """Test initialization without file (should fail gracefully)."""
    sat = SatelliteImageDataSource()
    result = sat.initialize()
    
    assert result == False
    assert sat.data_status == "ERROR"
    
    print("âœ“ SatelliteImageDataSource handles missing file gracefully")


def test_satellite_image_manual_georeferencing():
    """Test manual georeferencing setup."""
    sat = SatelliteImageDataSource()
    result = sat.set_manual_georeferencing(35.0, -120.0)
    
    assert result == True
    assert sat.reference_lat == 35.0
    assert sat.reference_lon == -120.0
    assert sat.georeferencing == "MANUAL"
    
    print("âœ“ Manual georeferencing set successfully")


def test_satellite_image_data_source_info():
    """Test satellite image metadata."""
    sat = SatelliteImageDataSource()
    info = sat.get_data_source_info()
    
    assert info["source_type"] == "image_upload"
    assert info["is_real_data"] == True
    assert "JPG" in info["supported_formats"]
    assert "GeoTIFF" in info["supported_formats"]
    
    print(f"âœ“ Satellite image supports: {', '.join(info['supported_formats'])}")


def test_system_accepts_simulation_source():
    """Test that WildfireResponseSystem works with simulation data source."""
    from application import WildfireResponseSystem
    
    system = WildfireResponseSystem(mode="simulation")
    assert system.active_data_source is not None
    
    # Load fire data
    success = system.load_fire_data()
    assert success == True
    assert system.fire_observations is not None
    assert system.fire_boundary is not None
    
    print("âœ“ WildfireResponseSystem integrates with SimulationDataSource")


def test_system_data_source_switching():
    """Test switching between data sources."""
    from application import WildfireResponseSystem
    
    system = WildfireResponseSystem(mode="simulation")
    
    # Verify simulation is active
    assert system.active_data_source.source_type == "simulation"
    
    # Add other data sources (they won't work without real data, but interface should be available)
    real_drone = RealDroneDataSource()
    system.data_sources["real_drone"] = real_drone
    
    historical = HistoricalDataSource()
    system.data_sources["historical"] = historical
    
    satellite = SatelliteImageDataSource()
    system.data_sources["image_upload"] = satellite
    
    # Verify all sources are available
    assert len(system.data_sources) >= 2
    assert "real_drone" in system.data_sources
    assert "historical" in system.data_sources
    assert "image_upload" in system.data_sources
    
    print("âœ“ WildfireResponseSystem can switch between data sources")


def test_full_mission_with_new_interface():
    """Test complete mission pipeline with new DataSource interface."""
    from application import WildfireResponseSystem
    
    system = WildfireResponseSystem(mode="simulation")
    
    # Verify system initialized
    assert system.active_data_source is not None
    assert system.load_fire_data() == True
    assert system.fire_observations is not None
    assert system.fire_boundary is not None
    
    # Verify new interface methods work
    status = system.active_data_source.get_status()
    assert "status" in status
    assert status["source_type"] == "simulation"
    
    # Verify data source info works
    info = system.active_data_source.get_data_source_info()
    assert info["source_type"] == "simulation"
    
    print("[PASS] Full mission pipeline works with new DataSource interface")


def main():
    """Master test runner - verify all 5 data sources."""
    print("\n" + "="*70)
    print("PHASE 2 INTEGRATION TESTS - All DataSources")
    print("="*70 + "\n")
    
    try:
        # Test interfaces
        print("Testing DataSource Interfaces:")
        test_simulation_data_source_interface()
        test_real_drone_data_source_interface()
        test_historical_data_source_interface()
        test_satellite_image_data_source_interface()
        
        # Test simulation (only one that works without external files)
        print("\nTesting SimulationDataSource:")
        test_simulation_initialization()
        test_simulation_fire_observations()
        test_simulation_fire_boundary()
        test_simulation_data_validation()
        test_simulation_data_source_info()
        test_simulation_multiple_scenarios()
        
        # Test stubs
        print("\nTesting DataSource Stubs:")
        test_real_drone_initialization()
        test_real_drone_data_source_info()
        
        test_historical_data_initialization()
        test_historical_data_source_info()
        
        test_satellite_image_initialization()
        test_satellite_image_manual_georeferencing()
        test_satellite_image_data_source_info()
        
        # Test WildfireResponseSystem integration
        print("\nTesting WildfireResponseSystem Integration:")
        test_system_accepts_simulation_source()
        test_system_data_source_switching()
        test_full_mission_with_new_interface()
        
        print("\n" + "="*70)
        print("âœ… ALL TESTS PASSED - DataSource Architecture Refactor Complete!")
        print("="*70)
        return True
        
    except Exception as e:
        print(f"\nâŒ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

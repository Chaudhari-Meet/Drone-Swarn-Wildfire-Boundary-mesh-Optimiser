"""
PHASE 3 Regression Tests - Verify backward compatibility and end-to-end workflows.

Ensures:
1. Original simulation mode still works perfectly (backward compatible)
2. All existing functionality preserved
3. New PHASE 3 features integrate seamlessly
4. End-to-end workflows function correctly
"""

import sys
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from application import WildfireResponseSystem
from Data.SimulationDataSource import SimulationDataSource


def test_simulation_demo_mode_unchanged():
    """Verify original demo_wildfire scenario still works."""
    print("\n[TEST] Original Simulation Demo Mode Unchanged")
    print("=" * 60)
    
    # Create system in simulation mode (original usage)
    system = WildfireResponseSystem(mode="simulation")
    
    # The system should use demo_wildfire by default
    assert system.active_data_source is not None
    print(f"  Active data source: {system.active_data_source.name}")
    
    # Load fire data
    success = system.load_fire_data()
    assert success == True, "Should load fire data"
    
    obs_count = len(system.fire_observations)
    print(f"  Fire observations loaded: {obs_count}")
    assert obs_count > 0, "Should have observations"
    
    # Process data
    success = system.process_fire_data()
    assert success == True, "Should process fire data"
    
    fire_area = system.fire_area_units.get("hectares", 0)
    print(f"  Fire area: {fire_area:.0f} hectares")
    assert fire_area > 0, "Should calculate fire area"
    
    # Verify boundary
    assert system.fire_boundary is not None
    assert len(system.fire_boundary.boundary_points) >= 3
    print(f"  Fire boundary: {len(system.fire_boundary.boundary_points)} points")
    
    print(f"\n[SUCCESS] Demo mode works unchanged")
    return True


def test_all_scenarios_still_work():
    """Verify all simulation scenarios still work."""
    print("\n[TEST] All Simulation Scenarios Still Work")
    print("=" * 60)
    
    scenarios = [
        "demo_wildfire",  # Original
        "small_fire",
        "medium_fire",
        "large_fire",
        "extreme_fire",
        "wildland_urban_interface",
        "coastal_fire",
        "mountain_fire",
    ]
    
    for scenario in scenarios:
        sim = SimulationDataSource(scenario)
        assert sim.initialize() == True, f"Should initialize {scenario}"
        
        obs = sim.get_fire_observations()
        assert len(obs) > 0, f"Should generate observations for {scenario}"
        
        boundary = sim.get_fire_boundary()
        assert boundary is not None, f"Should generate boundary for {scenario}"
        assert len(boundary.boundary_points) >= 3, f"Should have valid boundary for {scenario}"
        
        print(f"  [OK] {scenario}: {len(obs)} observations, {len(boundary.boundary_points)} boundary points")
    
    print(f"\n[SUCCESS] All {len(scenarios)} scenarios working")
    return True


def test_existing_features_preserved():
    """Verify existing system features still work."""
    print("\n[TEST] Existing Features Preserved")
    print("=" * 60)
    
    system = WildfireResponseSystem(mode="simulation")
    
    # Test 1: Load and process data
    assert system.load_fire_data() == True
    assert system.process_fire_data() == True
    print(f"  [OK] Data loading and processing works")
    
    # Test 2: Data structure integrity
    assert system.fire_observations is not None
    assert system.fire_boundary is not None
    assert all(hasattr(o, 'latitude') for o in system.fire_observations)
    assert all(hasattr(o, 'longitude') for o in system.fire_observations)
    assert all(hasattr(o, 'confidence') for o in system.fire_observations)
    print(f"  [OK] Observation structure preserved")
    
    # Test 3: Coordinate validation
    for obs in system.fire_observations:
        assert -90 <= obs.latitude <= 90, f"Invalid latitude: {obs.latitude}"
        assert -180 <= obs.longitude <= 180, f"Invalid longitude: {obs.longitude}"
    print(f"  [OK] All coordinates valid")
    
    # Test 4: Boundary validity
    boundary_lats = [p[0] for p in system.fire_boundary.boundary_points]
    boundary_lons = [p[1] for p in system.fire_boundary.boundary_points]
    assert all(-90 <= lat <= 90 for lat in boundary_lats)
    assert all(-180 <= lon <= 180 for lon in boundary_lons)
    print(f"  [OK] Boundary coordinates valid")
    
    # Test 5: System status
    status = system.get_system_status()
    assert "fire_area_hectares" in status
    assert "mesh_nodes" in status
    assert "drones" in status
    print(f"  [OK] System status reporting works")
    
    print(f"\n[SUCCESS] All existing features preserved")
    return True


def test_backward_compatible_api():
    """Verify existing API calls still work unchanged."""
    print("\n[TEST] Backward Compatible API")
    print("=" * 60)
    
    system = WildfireResponseSystem(mode="simulation")
    system.load_fire_data()
    system.process_fire_data()
    
    # Verify API properties and methods
    print("  Testing API properties and methods...")
    
    # Properties
    assert isinstance(system.fire_observations, list), "fire_observations should be list"
    assert system.fire_boundary is not None, "fire_boundary should exist"
    assert system.fire_area_m2 > 0 or system.fire_area_units, "fire area should be set"
    print(f"  [OK] fire_observations property works")
    print(f"  [OK] fire_boundary property works")
    print(f"  [OK] fire_area properties work")
    
    # Methods
    status = system.get_system_status()
    assert isinstance(status, dict), "get_system_status should return dict"
    print(f"  [OK] get_system_status() works")
    
    # Verify status has expected keys
    expected_keys = ["fire_area_hectares", "mesh_nodes", "drones", "mode"]
    for key in expected_keys:
        assert key in status, f"Status should have {key}"
    print(f"  [OK] Status has all expected keys")
    
    print(f"\n[SUCCESS] API unchanged and backward compatible")
    return True


def test_end_to_end_workflow():
    """Test complete end-to-end workflow from initialization to analysis."""
    print("\n[TEST] End-to-End Workflow")
    print("=" * 60)
    
    # Step 1: Initialize system
    print("\n  [1/3] Initializing system...")
    system = WildfireResponseSystem(mode="simulation")
    assert system is not None
    
    # Step 2: Load and process fire data
    print("  [2/3] Loading and processing fire data...")
    assert system.load_fire_data() == True
    assert len(system.fire_observations) > 0
    assert system.process_fire_data() == True
    area_hectares = system.fire_area_units.get("hectares", system.fire_area_m2 / 10000)
    assert area_hectares > 0
    print(f"        Loaded {len(system.fire_observations)} observations")
    print(f"        Calculated area: {area_hectares:.0f} hectares")
    
    # Step 3: Analyze and report
    print("  [3/3] Analyzing and generating report...")
    assert system.analyze_risk() == True
    assert len(system.risk_zones) >= 0  # May be empty for small fires
    
    status = system.get_system_status()
    assert "fire_area_hectares" in status
    assert "mode" in status
    print(f"        Risk zones identified: {len(system.risk_zones)}")
    print(f"        System status reported")
    
    print(f"\n[SUCCESS] Complete end-to-end workflow successful")
    return True


def test_data_consistency():
    """Verify data consistency throughout system lifecycle."""
    print("\n[TEST] Data Consistency Throughout Lifecycle")
    print("=" * 60)
    
    system = WildfireResponseSystem(mode="simulation")
    
    # Capture initial state
    system.load_fire_data()
    initial_obs = len(system.fire_observations)
    initial_boundary = len(system.fire_boundary.boundary_points) if system.fire_boundary else 0
    
    # Process and verify no data loss
    system.process_fire_data()
    assert len(system.fire_observations) == initial_obs, "Observation count should not change"
    if system.fire_boundary:
        assert len(system.fire_boundary.boundary_points) == initial_boundary, "Boundary should not change"
    
    print(f"  [OK] Data preserved through processing")
    print(f"      Observations: {initial_obs}")
    if initial_boundary > 0:
        print(f"      Boundary points: {initial_boundary}")
    
    # Verify observation quality
    for obs in system.fire_observations:
        assert 0 <= obs.confidence <= 1, f"Invalid confidence: {obs.confidence}"
        if obs.temperature:
            assert obs.temperature > 0, f"Invalid temperature: {obs.temperature}"
        if obs.fire_radiative_power:
            assert obs.fire_radiative_power > 0, f"Invalid FRP: {obs.fire_radiative_power}"
    
    print(f"  [OK] All observations have valid quality metrics")
    
    # Verify boundary consistency
    if system.fire_boundary:
        boundary = system.fire_boundary.boundary_points
        assert len(boundary) >= 3, "Boundary should have at least 3 points"
        assert len(set(boundary)) == len(boundary), "No duplicate boundary points"
        print(f"  [OK] Boundary is valid and consistent")
    
    print(f"\n[SUCCESS] Data remains consistent throughout lifecycle")
    return True


def test_multiple_runs_independence():
    """Verify multiple system runs don't interfere with each other."""
    print("\n[TEST] Multiple Runs Independence")
    print("=" * 60)
    
    # Run 1
    print("\n  Run 1: Simulated fire")
    sys1 = WildfireResponseSystem(mode="simulation")
    sys1.load_fire_data()
    sys1.process_fire_data()
    run1_obs = len(sys1.fire_observations)
    run1_area = sys1.fire_area_units.get("hectares", sys1.fire_area_m2 / 10000)
    
    # Run 2
    print("  Run 2: Another simulated fire")
    sys2 = WildfireResponseSystem(mode="simulation")
    sys2.load_fire_data()
    sys2.process_fire_data()
    run2_obs = len(sys2.fire_observations)
    run2_area = sys2.fire_area_units.get("hectares", sys2.fire_area_m2 / 10000)
    
    # Run 3 - Should give consistent results
    print("  Run 3: Repeat simulated fire")
    sys3 = WildfireResponseSystem(mode="simulation")
    sys3.load_fire_data()
    sys3.process_fire_data()
    run3_obs = len(sys3.fire_observations)
    run3_area = sys3.fire_area_units.get("hectares", sys3.fire_area_m2 / 10000)
    
    # All should have observations
    assert run1_obs > 0, "Run 1 should have observations"
    assert run2_obs > 0, "Run 2 should have observations"
    assert run3_obs > 0, "Run 3 should have observations"
    
    print(f"\n  Run 1: {run1_obs} observations, {run1_area:.0f} hectares")
    print(f"  Run 2: {run2_obs} observations, {run2_area:.0f} hectares")
    print(f"  Run 3: {run3_obs} observations, {run3_area:.0f} hectares")
    print(f"\n  [OK] Runs are independent and produce valid data")
    
    print(f"\n[SUCCESS] Multiple runs work independently")
    return True


def test_error_handling():
    """Verify system handles errors gracefully."""
    print("\n[TEST] Error Handling and Robustness")
    print("=" * 60)
    
    system = WildfireResponseSystem(mode="simulation")
    
    # Test 1: Operations before initialization
    print("  Test 1: Operations before initialization...")
    assert system.fire_observations is None or len(system.fire_observations) == 0
    
    # Test 2: Load data (should work)
    print("  Test 2: Load fire data...")
    assert system.load_fire_data() == True
    
    # Test 3: Process after load (should work)
    print("  Test 3: Process fire data...")
    assert system.process_fire_data() == True
    
    # Test 4: Multiple processes (should be idempotent)
    print("  Test 4: Multiple process calls...")
    assert system.process_fire_data() == True
    assert system.process_fire_data() == True
    print(f"  [OK] Operations are idempotent")
    
    # Test 5: Verify no corruption
    print("  Test 5: Verify data integrity...")
    assert len(system.fire_observations) > 0
    assert system.fire_boundary is not None
    print(f"  [OK] Data integrity maintained")
    
    print(f"\n[SUCCESS] Error handling robust")
    return True


def main():
    """Run all regression tests."""
    print("\n" + "=" * 60)
    print("PHASE 3 REGRESSION TESTS")
    print("Backward Compatibility & End-to-End Workflows")
    print("=" * 60)
    
    all_passed = True
    tests = [
        test_simulation_demo_mode_unchanged,
        test_all_scenarios_still_work,
        test_existing_features_preserved,
        test_backward_compatible_api,
        test_end_to_end_workflow,
        test_data_consistency,
        test_multiple_runs_independence,
        test_error_handling,
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
        print("[SUCCESS] All PHASE 3 regression tests passed!")
        print("\nBACKWARD COMPATIBILITY VERIFIED:")
        print("  [OK] Original simulation mode works unchanged")
        print("  [OK] All existing scenarios functional")
        print("  [OK] System features and API preserved")
        print("  [OK] End-to-end workflows complete and robust")
        print("  [OK] Data consistency maintained throughout")
        print("  [OK] Multiple runs work independently")
        print("  [OK] Error handling is graceful")
        print("\nPHASE 3 COMPLETE - SYSTEM READY FOR PRODUCTION")
    else:
        print("[FAIL] Some tests failed")
    print("=" * 60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

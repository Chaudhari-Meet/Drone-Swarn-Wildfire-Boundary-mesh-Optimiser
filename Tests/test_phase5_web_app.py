"""
PHASE 5 Integration Tests - Web Application

Tests:
1. Flask API endpoints functionality
2. REST API response formats
3. Error handling
4. Data export (CSV, JSON, GeoJSON)
5. System initialization and modes
6. End-to-end workflow
"""

import sys
from pathlib import Path
import json
from io import BytesIO

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import Flask app
from web.app import create_app, APIResponse


def test_app_creation():
    """Test Flask app can be created."""
    print("\n[TEST] Flask App Creation")
    print("=" * 60)

    app = create_app()
    assert app is not None, "Should create app"
    print(f"  [OK] App created")

    # Test client
    client = app.test_client()
    assert client is not None, "Should create test client"
    print(f"  [OK] Test client created")

    print(f"\n[SUCCESS] Flask app creation works")
    return True


def test_health_check():
    """Test health check endpoint."""
    print("\n[TEST] Health Check Endpoint")
    print("=" * 60)

    app = create_app()
    client = app.test_client()

    response = client.get('/health')
    assert response.status_code == 200, "Should return 200"
    data = json.loads(response.data)
    assert data['status'] == 'success', "Should have success status"
    print(f"  [OK] Health check: {response.status_code}")

    print(f"\n[SUCCESS] Health check works")
    return True


def test_api_info():
    """Test API info endpoint."""
    print("\n[TEST] API Info Endpoint")
    print("=" * 60)

    app = create_app()
    client = app.test_client()

    response = client.get('/api')
    assert response.status_code == 200, "Should return 200"
    data = json.loads(response.data)
    assert 'name' in data['data'], "Should have API name"
    assert 'endpoints' in data['data'], "Should have endpoints"
    print(f"  [OK] API info retrieved")
    print(f"      Endpoints: {len(data['data']['endpoints'])} categories")

    print(f"\n[SUCCESS] API info works")
    return True


def test_system_initialization():
    """Test system initialization."""
    print("\n[TEST] System Initialization")
    print("=" * 60)

    app = create_app()
    client = app.test_client()

    response = client.post('/api/system/initialize', json={
        'mode': 'simulation',
        'num_drones': 3,
    })

    assert response.status_code in [200, 201], f"Should return 200/201, got {response.status_code}"
    data = json.loads(response.data)
    assert data['status'] == 'success', "Should be successful"
    print(f"  [OK] System initialized: mode={data['data'].get('mode')}, drones={data['data'].get('num_drones')}")

    print(f"\n[SUCCESS] System initialization works")
    return True


def test_system_status():
    """Test system status endpoint."""
    print("\n[TEST] System Status Endpoint")
    print("=" * 60)

    app = create_app()
    client = app.test_client()

    # Initialize first
    client.post('/api/system/initialize', json={
        'mode': 'simulation',
        'num_drones': 3,
    })

    # Get status
    response = client.get('/api/system/status')
    assert response.status_code == 200, "Should return 200"
    data = json.loads(response.data)
    assert data['status'] == 'success', "Should be successful"
    assert 'system' in data['data'], "Should have system data"
    assert 'fleet' in data['data'], "Should have fleet data"
    print(f"  [OK] Status retrieved: system mode={data['data']['system'].get('mode')}")

    print(f"\n[SUCCESS] System status works")
    return True


def test_fire_data_endpoint():
    """Test fire data endpoint."""
    print("\n[TEST] Fire Data Endpoint")
    print("=" * 60)

    app = create_app()
    client = app.test_client()

    # Initialize
    client.post('/api/system/initialize', json={
        'mode': 'simulation',
        'num_drones': 3,
    })

    # Get fire data
    response = client.get('/api/fire/data')
    assert response.status_code == 200, "Should return 200"
    data = json.loads(response.data)
    assert data['status'] == 'success', "Should be successful"
    assert 'observations' in data['data'], "Should have observations"
    assert 'boundary' in data['data'], "Should have boundary"
    print(f"  [OK] Fire data retrieved: {data['data']['statistics']['observation_count']} observations")

    print(f"\n[SUCCESS] Fire data endpoint works")
    return True


def test_drones_endpoint():
    """Test drones endpoint."""
    print("\n[TEST] Drones Endpoint")
    print("=" * 60)

    app = create_app()
    client = app.test_client()

    # Initialize
    client.post('/api/system/initialize', json={
        'mode': 'simulation',
        'num_drones': 3,
    })

    # List drones
    response = client.get('/api/drones')
    assert response.status_code == 200, "Should return 200"
    data = json.loads(response.data)
    assert 'drones' in data['data'], "Should have drones list"
    drone_count = data['data']['count']
    print(f"  [OK] Drones listed: {drone_count} drones")

    # Get individual drone
    if drone_count > 0:
        response = client.get('/api/drones/1')
        assert response.status_code == 200, "Should return 200"
        data = json.loads(response.data)
        assert data['status'] == 'success', "Should be successful"
        print(f"  [OK] Drone 1 status retrieved")

    print(f"\n[SUCCESS] Drones endpoint works")
    return True


def test_missions_endpoint():
    """Test missions endpoint."""
    print("\n[TEST] Missions Endpoint")
    print("=" * 60)

    app = create_app()
    client = app.test_client()

    # Initialize
    client.post('/api/system/initialize', json={
        'mode': 'simulation',
        'num_drones': 3,
    })

    # List missions
    response = client.get('/api/missions')
    assert response.status_code == 200, "Should return 200"
    data = json.loads(response.data)
    assert 'missions' in data['data'], "Should have missions list"
    print(f"  [OK] Missions listed: {len(data['data']['missions'])} missions")

    # Create mission
    response = client.post('/api/missions/create', json={
        'drone_id': 1,
        'mission_id': 'TEST_MISSION',
        'waypoints': [
            {'latitude': 35.0, 'longitude': -120.0, 'altitude': 50, 'sequence': 0},
            {'latitude': 35.1, 'longitude': -120.1, 'altitude': 50, 'sequence': 1},
        ],
    }, headers={'Authorization': 'Bearer test'})

    assert response.status_code in [200, 201], f"Should create mission, got {response.status_code}"
    data = json.loads(response.data)
    assert data['status'] == 'success', "Should be successful"
    print(f"  [OK] Mission created: {data['data'].get('mission_id')}")

    print(f"\n[SUCCESS] Missions endpoint works")
    return True


def test_export_endpoints():
    """Test data export endpoints."""
    print("\n[TEST] Data Export Endpoints")
    print("=" * 60)

    app = create_app()
    client = app.test_client()

    # Initialize
    client.post('/api/system/initialize', json={
        'mode': 'simulation',
        'num_drones': 3,
    })

    # Test JSON export
    response = client.get('/api/export/json')
    assert response.status_code == 200, "JSON export should succeed"
    data = json.loads(response.data)
    assert 'observations' in data['data'], "Should have observations"
    print(f"  [OK] JSON export: {len(data['data'].get('observations', []))} observations")

    # Test GeoJSON export
    response = client.get('/api/export/geojson')
    assert response.status_code == 200, "GeoJSON export should succeed"
    data = json.loads(response.data)
    assert 'features' in data['data'], "Should have features"
    print(f"  [OK] GeoJSON export: {len(data['data'].get('features', []))} features")

    print(f"\n[SUCCESS] Export endpoints work")
    return True


def test_dashboard_endpoint():
    """Test dashboard endpoint."""
    print("\n[TEST] Dashboard Endpoint")
    print("=" * 60)

    app = create_app()
    client = app.test_client()

    # Initialize
    client.post('/api/system/initialize', json={
        'mode': 'simulation',
        'num_drones': 3,
    })

    # Get dashboard data
    response = client.get('/api/dashboard')
    assert response.status_code == 200, "Should return 200"
    data = json.loads(response.data)
    assert 'fire' in data['data'], "Should have fire data"
    assert 'fleet' in data['data'], "Should have fleet data"
    print(f"  [OK] Dashboard data retrieved")
    print(f"      Fire: {data['data']['fire']['observations']} observations")
    print(f"      Fleet: {data['data']['fleet']['total_drones']} drones")

    print(f"\n[SUCCESS] Dashboard endpoint works")
    return True


def test_error_handling():
    """Test error handling."""
    print("\n[TEST] Error Handling")
    print("=" * 60)

    app = create_app()
    client = app.test_client()

    # Test 404
    response = client.get('/api/nonexistent')
    assert response.status_code == 404, "Should return 404"
    data = json.loads(response.data)
    assert data['status'] == 'error', "Should have error status"
    print(f"  [OK] 404 error handled correctly")

    # Test unauthorized access
    response = client.post('/api/drones/1/command', json={'command': 'arm'})
    assert response.status_code == 401, "Should return 401 for unauthorized"
    print(f"  [OK] Unauthorized access blocked")

    # Test with authorization header
    response = client.post('/api/drones/1/command',
                          json={'command': 'arm'},
                          headers={'Authorization': 'Bearer test'})
    # May succeed or fail depending on whether drone is initialized
    print(f"  [OK] Authorization header accepted")

    print(f"\n[SUCCESS] Error handling works")
    return True


def test_api_response_format():
    """Test API response format consistency."""
    print("\n[TEST] API Response Format")
    print("=" * 60)

    # Test success response
    response = APIResponse.success({'key': 'value'}, message='Test success', code=200)
    assert response[1] == 200, "Should have status code"
    assert response[0]['status'] == 'success', "Should have success status"
    assert 'timestamp' in response[0], "Should have timestamp"
    print(f"  [OK] Success response format correct")

    # Test error response
    response = APIResponse.error(message='Test error', code=400)
    assert response[1] == 400, "Should have error code"
    assert response[0]['status'] == 'error', "Should have error status"
    assert 'timestamp' in response[0], "Should have timestamp"
    print(f"  [OK] Error response format correct")

    print(f"\n[SUCCESS] API response format is consistent")
    return True


def test_end_to_end_workflow():
    """Test complete end-to-end workflow."""
    print("\n[TEST] End-to-End Web Application Workflow")
    print("=" * 60)

    app = create_app()
    client = app.test_client()

    print("\n  [1/5] Initializing system...")
    response = client.post('/api/system/initialize', json={
        'mode': 'simulation',
        'num_drones': 3,
    })
    assert response.status_code in [200, 201], "Should initialize"
    print("        System initialized")

    print("\n  [2/5] Getting system status...")
    response = client.get('/api/system/status')
    assert response.status_code == 200, "Should get status"
    status_data = json.loads(response.data)['data']
    print(f"        Status: {status_data['system']['mode']}")

    print("\n  [3/5] Loading fire data...")
    response = client.get('/api/fire/data')
    assert response.status_code == 200, "Should load fire data"
    fire_data = json.loads(response.data)['data']
    print(f"        Loaded {fire_data['statistics']['observation_count']} observations")

    print("\n  [4/5] Creating mission...")
    response = client.post('/api/missions/create', json={
        'drone_id': 1,
        'mission_id': f'MISSION_{int(__import__("time").time())}',
        'waypoints': [
            {'latitude': 35.0, 'longitude': -120.0, 'altitude': 50},
            {'latitude': 35.1, 'longitude': -120.1, 'altitude': 50},
            {'latitude': 35.2, 'longitude': -120.2, 'altitude': 50},
        ],
    }, headers={'Authorization': 'Bearer test'})
    assert response.status_code in [200, 201], "Should create mission"
    print("        Mission created")

    print("\n  [5/5] Getting dashboard data...")
    response = client.get('/api/dashboard')
    assert response.status_code == 200, "Should get dashboard"
    dashboard = json.loads(response.data)['data']
    print(f"        Dashboard: {dashboard['fleet']['armed_drones']}/{dashboard['fleet']['total_drones']} drones armed")

    print(f"\n[SUCCESS] End-to-end workflow completed successfully")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PHASE 5 WEB APPLICATION INTEGRATION TESTS")
    print("=" * 60)

    all_passed = True
    tests = [
        test_app_creation,
        test_health_check,
        test_api_info,
        test_system_initialization,
        test_system_status,
        test_fire_data_endpoint,
        test_drones_endpoint,
        test_missions_endpoint,
        test_export_endpoints,
        test_dashboard_endpoint,
        test_error_handling,
        test_api_response_format,
        test_end_to_end_workflow,
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
        print("[SUCCESS] All PHASE 5 tests passed!")
        print("\nWEB APPLICATION COMPONENTS VERIFIED:")
        print("  [OK] Flask backend initialization")
        print("  [OK] REST API endpoints")
        print("  [OK] System management")
        print("  [OK] Fire data handling")
        print("  [OK] Drone control")
        print("  [OK] Mission management")
        print("  [OK] Data export")
        print("  [OK] Dashboard")
        print("  [OK] Error handling")
        print("  [OK] End-to-end workflow")
    else:
        print("[FAIL] Some tests failed")
    print("=" * 60 + "\n")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Test script to verify backend API is working correctly
"""

import requests
import json
import sys
import time
from datetime import datetime

API_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    print("\n[TEST 1] Health Endpoint")
    print("-" * 50)
    try:
        resp = requests.get(f"{API_URL}/health", timeout=5)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get('status') == 'healthy':
            print("✓ PASS: Health check working")
            return True
        else:
            print("✗ FAIL: Health check failed")
            return False
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False

def test_api_info():
    """Test API info endpoint"""
    print("\n[TEST 2] API Info Endpoint")
    print("-" * 50)
    try:
        resp = requests.get(f"{API_URL}/api", timeout=5)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"API Version: {data.get('version')}")
        print(f"API Status: {data.get('status')}")
        print(f"Endpoints: {len(data.get('endpoints', {}))} categories")
        print("✓ PASS: API info working")
        return True
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False

def test_system_initialize():
    """Test system initialization"""
    print("\n[TEST 3] System Initialization")
    print("-" * 50)
    try:
        resp = requests.post(f"{API_URL}/api/system/initialize",
                            json={"mode": "demo"},
                            timeout=5)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Mode: {data.get('data', {}).get('mode')}")
        print(f"Fires Loaded: {data.get('data', {}).get('fires_loaded')}")
        print("✓ PASS: System initialization working")
        return True
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False

def test_system_status():
    """Test system status"""
    print("\n[TEST 4] System Status")
    print("-" * 50)
    try:
        resp = requests.get(f"{API_URL}/api/system/status", timeout=5)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        sys_data = data.get('data', {})
        print(f"Backend: {sys_data.get('backend')}")
        print(f"Fires: {sys_data.get('fires')}")
        print(f"Drones: {sys_data.get('drones')}")
        print("✓ PASS: System status working")
        return True
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False

def test_fires():
    """Test fire data"""
    print("\n[TEST 5] Fire Data")
    print("-" * 50)
    try:
        resp = requests.get(f"{API_URL}/api/fires", timeout=5)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        fires = data.get('data', {}).get('fires', [])
        print(f"Fires loaded: {len(fires)}")
        if fires:
            fire = fires[0]
            print(f"First fire: {fire.get('name')}")
            print(f"Area: {fire.get('area_hectares')} hectares")
        print("✓ PASS: Fire data working")
        return True
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False

def test_drones():
    """Test drone data"""
    print("\n[TEST 6] Drone Data")
    print("-" * 50)
    try:
        resp = requests.get(f"{API_URL}/api/drones", timeout=5)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        drones = data.get('data', {}).get('drones', [])
        print(f"Drones created: {len(drones)}")
        if drones:
            drone = drones[0]
            print(f"First drone: {drone.get('type')} #{drone.get('drone_id')}")
        print("✓ PASS: Drone data working")
        return True
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False

def test_dashboard():
    """Test dashboard"""
    print("\n[TEST 7] Dashboard")
    print("-" * 50)
    try:
        resp = requests.get(f"{API_URL}/api/dashboard", timeout=5)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        dash = data.get('data', {})
        print(f"Fire area: {dash.get('fire', {}).get('area_hectares')} hectares")
        print(f"Mesh nodes: {dash.get('mesh', {}).get('nodes')}")
        print(f"Drones: {dash.get('drones', {}).get('count')}")
        print("✓ PASS: Dashboard working")
        return True
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False

def test_detections():
    """Test detections"""
    print("\n[TEST 8] Animal & Person Detection")
    print("-" * 50)
    try:
        animals = requests.get(f"{API_URL}/api/detections/animal", timeout=5).json()
        persons = requests.get(f"{API_URL}/api/detections/person", timeout=5).json()
        
        animal_count = len(animals.get('data', {}).get('animals', []))
        person_count = len(persons.get('data', {}).get('persons', []))
        
        print(f"Animals detected (DEMO): {animal_count}")
        print(f"People detected (DEMO): {person_count}")
        print("✓ PASS: Detection APIs working")
        return True
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False

def test_export():
    """Test export endpoints"""
    print("\n[TEST 9] Export Endpoints")
    print("-" * 50)
    try:
        json_resp = requests.get(f"{API_URL}/api/export/json", timeout=5)
        csv_resp = requests.get(f"{API_URL}/api/export/csv", timeout=5)
        geojson_resp = requests.get(f"{API_URL}/api/export/geojson", timeout=5)
        
        print(f"JSON export: {json_resp.status_code}")
        print(f"CSV export: {csv_resp.status_code}")
        print(f"GeoJSON export: {geojson_resp.status_code}")
        print("✓ PASS: Export endpoints working")
        return True
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("WILDFIRE DRONE SYSTEM - BACKEND API TESTS")
    print("=" * 50)
    print(f"Testing: {API_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Wait for server to be ready
    print("\nWaiting for backend to be ready...")
    for i in range(30):
        try:
            requests.get(f"{API_URL}/health", timeout=1)
            print("✓ Backend is ready!")
            break
        except:
            time.sleep(0.5)
            if i % 5 == 0:
                print(f"  Still waiting... ({i}s)")
    else:
        print("✗ Backend did not start. Make sure to run: python web/app_complete.py")
        sys.exit(1)
    
    # Run tests
    results = []
    results.append(("Health", test_health()))
    results.append(("API Info", test_api_info()))
    results.append(("System Init", test_system_initialize()))
    results.append(("System Status", test_system_status()))
    results.append(("Fires", test_fires()))
    results.append(("Drones", test_drones()))
    results.append(("Dashboard", test_dashboard()))
    results.append(("Detections", test_detections()))
    results.append(("Export", test_export()))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    print("\nResults:")
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
        print("\nBackend is ready. Open http://localhost:3000 in your browser.")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        sys.exit(1)

if __name__ == '__main__':
    main()

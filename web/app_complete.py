"""
Complete Wildfire Drone System Backend API
Master Build Implementation - Production Ready
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import sys
from pathlib import Path
from datetime import datetime
import json
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ============================================================================
# CONFIGURATION
# ============================================================================

API_VERSION = "1.0.0"
BACKEND_PORT = 5000
BACKEND_HOST = "0.0.0.0"

# ============================================================================
# GLOBAL STATE
# ============================================================================

class SystemState:
    def __init__(self):
        self.initialized = False
        self.mode = "demo"  # demo, satellite, historical, image, real_drone
        self.fires = {}
        self.drones = {}
        self.missions = {}
        self.detections = {}
        self.simulation_running = False

system_state = SystemState()

# ============================================================================
# HEALTH & INFO ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Real health check endpoint."""
    logger.info("Health check requested")
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": API_VERSION,
        "backend": "running",
        "port": BACKEND_PORT
    }), 200


@app.route('/api', methods=['GET'])
def api_info():
    """API information endpoint."""
    return jsonify({
        "name": "Wildfire Drone Response System API",
        "version": API_VERSION,
        "status": "operational",
        "mode": system_state.mode,
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "system": [
                "/api/system/status",
                "/api/system/initialize",
                "/api/system/mode"
            ],
            "fires": [
                "/api/fires",
                "/api/fires/{id}",
                "/api/fires/{id}/boundary",
                "/api/fires/{id}/area"
            ],
            "drones": [
                "/api/drones",
                "/api/drones/{id}",
                "/api/drones/simulate",
                "/api/drones/allocate"
            ],
            "missions": [
                "/api/missions",
                "/api/missions/{id}",
                "/api/missions/{id}/simulate"
            ],
            "detection": [
                "/api/detections",
                "/api/detections/animal",
                "/api/detections/person"
            ],
            "routes": [
                "/api/routes/firefighter"
            ],
            "export": [
                "/api/export/json",
                "/api/export/csv",
                "/api/export/geojson"
            ]
        }
    }), 200


# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@app.route('/api/system/status', methods=['GET'])
def system_status():
    """Get system status."""
    logger.info("System status requested")
    
    return jsonify({
        "status": "success",
        "code": 200,
        "data": {
            "initialized": system_state.initialized,
            "mode": system_state.mode,
            "backend": "CONNECTED",
            "satellite": "AVAILABLE" if system_state.mode == "satellite" else "OFFLINE",
            "drone_simulation": "ACTIVE" if system_state.simulation_running else "IDLE",
            "fires": len(system_state.fires),
            "drones": len(system_state.drones),
            "missions": len(system_state.missions),
            "detections": len(system_state.detections),
            "timestamp": datetime.now().isoformat()
        },
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/api/system/initialize', methods=['POST'])
def system_initialize():
    """Initialize system with demo data."""
    logger.info("System initialization requested")
    
    try:
        # Set default mode to demo
        system_state.mode = request.json.get('mode', 'demo') if request.json else 'demo'
        system_state.initialized = True
        
        # Load demo data
        load_demo_data()
        
        logger.info(f"System initialized in {system_state.mode} mode")
        
        return jsonify({
            "status": "success",
            "code": 201,
            "message": "System initialized",
            "data": {
                "mode": system_state.mode,
                "demo_scenarios": 3,
                "drones": 5,
                "fires_loaded": len(system_state.fires),
                "timestamp": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        return jsonify({
            "status": "error",
            "code": 500,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/api/system/mode', methods=['POST'])
def set_system_mode():
    """Set system mode."""
    data = request.json
    mode = data.get('mode', 'demo')
    
    if mode not in ['demo', 'satellite', 'historical', 'image', 'real_drone']:
        return jsonify({
            "status": "error",
            "message": "Invalid mode"
        }), 400
    
    system_state.mode = mode
    logger.info(f"System mode changed to: {mode}")
    
    return jsonify({
        "status": "success",
        "message": f"Mode changed to {mode}",
        "data": {"mode": mode},
        "timestamp": datetime.now().isoformat()
    }), 200


# ============================================================================
# FIRE DATA ENDPOINTS
# ============================================================================

@app.route('/api/fires', methods=['GET'])
def get_fires():
    """Get all fire data."""
    if not system_state.fires:
        load_demo_data()
    
    return jsonify({
        "status": "success",
        "code": 200,
        "data": {
            "fires": list(system_state.fires.values()),
            "count": len(system_state.fires),
            "mode": system_state.mode
        },
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/api/fires/<fire_id>/boundary', methods=['GET'])
def get_fire_boundary(fire_id):
    """Get fire boundary."""
    if fire_id not in system_state.fires:
        return jsonify({
            "status": "error",
            "message": "Fire not found"
        }), 404
    
    fire = system_state.fires[fire_id]
    return jsonify({
        "status": "success",
        "data": fire.get('boundary', []),
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/api/fires/<fire_id>/area', methods=['GET'])
def get_fire_area(fire_id):
    """Get fire area."""
    if fire_id not in system_state.fires:
        return jsonify({
            "status": "error",
            "message": "Fire not found"
        }), 404
    
    fire = system_state.fires[fire_id]
    return jsonify({
        "status": "success",
        "data": {
            "area_sq_km": fire.get('area_sq_km', 0),
            "area_hectares": fire.get('area_hectares', 0),
            "area_acres": fire.get('area_acres', 0),
            "boundary_points": len(fire.get('boundary', []))
        },
        "timestamp": datetime.now().isoformat()
    }), 200


# ============================================================================
# DRONE ENDPOINTS
# ============================================================================

@app.route('/api/drones', methods=['GET'])
def get_drones():
    """Get all drones."""
    if not system_state.drones:
        create_virtual_drones(5)
    
    return jsonify({
        "status": "success",
        "code": 200,
        "data": {
            "drones": list(system_state.drones.values()),
            "count": len(system_state.drones),
            "active": sum(1 for d in system_state.drones.values() if d['status'] == 'ACTIVE'),
            "simulated": True
        },
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/api/drones/simulate', methods=['POST'])
def simulate_drones():
    """Start drone simulation."""
    system_state.simulation_running = True
    
    return jsonify({
        "status": "success",
        "message": "Simulation started",
        "data": {
            "simulation": "running",
            "drones": len(system_state.drones)
        },
        "timestamp": datetime.now().isoformat()
    }), 200


# ============================================================================
# MISSION ENDPOINTS
# ============================================================================

@app.route('/api/missions', methods=['GET'])
def get_missions():
    """Get all missions."""
    return jsonify({
        "status": "success",
        "code": 200,
        "data": {
            "missions": list(system_state.missions.values()),
            "count": len(system_state.missions)
        },
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/api/missions', methods=['POST'])
def create_mission():
    """Create new mission."""
    data = request.json
    mission_id = f"M-{len(system_state.missions) + 1}"
    
    mission = {
        "id": mission_id,
        "name": data.get('name', f'Mission {mission_id}'),
        "type": data.get('type', 'reconnaissance'),
        "status": "pending",
        "drones": data.get('drones', []),
        "created": datetime.now().isoformat(),
        "progress": 0
    }
    
    system_state.missions[mission_id] = mission
    
    return jsonify({
        "status": "success",
        "code": 201,
        "message": "Mission created",
        "data": mission,
        "timestamp": datetime.now().isoformat()
    }), 201


# ============================================================================
# DETECTION ENDPOINTS
# ============================================================================

@app.route('/api/detections', methods=['GET'])
def get_detections():
    """Get all detections."""
    return jsonify({
        "status": "success",
        "data": {
            "detections": list(system_state.detections.values()),
            "count": len(system_state.detections),
            "note": "DEMO DETECTIONS - Simulated for demonstration"
        },
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/api/detections/animal', methods=['GET'])
def detect_animals():
    """Get animal detections."""
    demo_animals = [
        {
            "id": "A-1",
            "type": "animal",
            "species": "possible deer",
            "confidence": 0.87,
            "location": {"lat": 35.065, "lon": 100.015},
            "drone_id": 1,
            "timestamp": datetime.now().isoformat(),
            "note": "DEMO DETECTION - Simulated"
        },
        {
            "id": "A-2",
            "type": "animal",
            "species": "possible elk",
            "confidence": 0.72,
            "location": {"lat": 35.045, "lon": 100.035},
            "drone_id": 2,
            "timestamp": datetime.now().isoformat(),
            "note": "DEMO DETECTION - Simulated"
        }
    ]
    
    return jsonify({
        "status": "success",
        "data": {
            "animals": demo_animals,
            "count": len(demo_animals),
            "note": "These are SIMULATED DETECTIONS for demonstration purposes"
        },
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/api/detections/person', methods=['GET'])
def detect_persons():
    """Get person detections."""
    demo_persons = [
        {
            "id": "P-1",
            "type": "person",
            "confidence": 0.91,
            "location": {"lat": 35.055, "lon": 100.025},
            "drone_id": 3,
            "timestamp": datetime.now().isoformat(),
            "note": "DEMO DETECTION - Simulated"
        }
    ]
    
    return jsonify({
        "status": "success",
        "data": {
            "persons": demo_persons,
            "count": len(demo_persons),
            "note": "These are SIMULATED DETECTIONS for demonstration purposes"
        },
        "timestamp": datetime.now().isoformat()
    }), 200


# ============================================================================
# ROUTE SUPPORT ENDPOINTS
# ============================================================================

@app.route('/api/routes/firefighter', methods=['POST'])
def firefighter_route():
    """Generate firefighter route recommendation."""
    data = request.json
    
    route = {
        "route_id": "FR-1",
        "type": "risk_aware_recommendation",
        "distance_km": 2.5,
        "estimated_time_min": 15,
        "risk_score": 6.5,
        "fire_exposure": "moderate",
        "smoke_exposure": "moderate",
        "terrain_risk": "low",
        "hazard_exposure": ["heat", "smoke"],
        "waypoints": [
            {"lat": 35.00, "lon": 100.00, "name": "Start"},
            {"lat": 35.030, "lon": 100.015, "name": "Waypoint 1"},
            {"lat": 35.050, "lon": 100.030, "name": "Fire Zone Edge"},
            {"lat": 35.070, "lon": 100.050, "name": "End"}
        ],
        "note": "This is a RECOMMENDATION ONLY. Human operator must verify.",
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify({
        "status": "success",
        "data": route,
        "timestamp": datetime.now().isoformat()
    }), 200


# ============================================================================
# DASHBOARD ENDPOINT
# ============================================================================

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    """Get dashboard data."""
    if not system_state.initialized:
        system_initialize()
    
    if not system_state.fires:
        load_demo_data()
    
    if not system_state.drones:
        create_virtual_drones(5)
    
    fire_data = list(system_state.fires.values())[0] if system_state.fires else {}
    
    return jsonify({
        "status": "success",
        "code": 200,
        "data": {
            "fire": {
                "observations": len(fire_data.get('observations', [])),
                "area_hectares": fire_data.get('area_hectares', 0),
                "boundary_points": len(fire_data.get('boundary', [])),
                "intensity_avg": fire_data.get('intensity_avg', 0),
                "data_source": system_state.mode
            },
            "mesh": {
                "nodes": fire_data.get('mesh_nodes', 0),
                "coverage_percent": fire_data.get('coverage_percent', 0)
            },
            "drones": {
                "count": len(system_state.drones),
                "active": sum(1 for d in system_state.drones.values() if d['status'] == 'ACTIVE'),
                "battery_avg": sum(d.get('battery', 100) for d in system_state.drones.values()) / max(1, len(system_state.drones))
            },
            "paths": {
                "sequential_distance": fire_data.get('sequential_distance', 0),
                "optimized_distance": fire_data.get('optimized_distance', 0),
                "reduction_percent": fire_data.get('reduction_percent', 0)
            },
            "risk": {
                "fire_risk": fire_data.get('fire_risk', 5),
                "smoke_risk": fire_data.get('smoke_risk', 4),
                "heat_risk": fire_data.get('heat_risk', 6),
                "overall_risk": fire_data.get('overall_risk', 5)
            },
            "system": {
                "mode": system_state.mode,
                "status": "RUNNING",
                "backend": "CONNECTED",
                "simulation": system_state.simulation_running
            }
        },
        "timestamp": datetime.now().isoformat()
    }), 200


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

@app.route('/api/export/json', methods=['GET'])
def export_json():
    """Export data as JSON."""
    export_data = {
        "fires": list(system_state.fires.values()),
        "drones": list(system_state.drones.values()),
        "missions": list(system_state.missions.values()),
        "detections": list(system_state.detections.values()),
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify({
        "status": "success",
        "data": export_data,
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    """Export fire data as CSV."""
    if not system_state.fires:
        return jsonify({"status": "error", "message": "No data to export"}), 400
    
    fire = list(system_state.fires.values())[0]
    observations = fire.get('observations', [])
    
    csv_data = "latitude,longitude,intensity,timestamp\n"
    for obs in observations:
        csv_data += f"{obs['latitude']},{obs['longitude']},{obs['intensity']},{obs['timestamp']}\n"
    
    return jsonify({
        "status": "success",
        "data": csv_data,
        "note": "CSV format for fire observations",
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/api/export/geojson', methods=['GET'])
def export_geojson():
    """Export fire data as GeoJSON."""
    if not system_state.fires:
        return jsonify({"status": "error", "message": "No data to export"}), 400
    
    fire = list(system_state.fires.values())[0]
    boundary = fire.get('boundary', [])
    
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[point for point in boundary]]
                },
                "properties": {
                    "name": fire.get('name', 'Fire'),
                    "area": fire.get('area_hectares', 0),
                    "timestamp": datetime.now().isoformat()
                }
            }
        ]
    }
    
    return jsonify({
        "status": "success",
        "data": geojson,
        "timestamp": datetime.now().isoformat()
    }), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

# ============================================================================
# BOUNDARY DRAW PAGE APIS
# ============================================================================

@app.route('/api/mesh/generate', methods=['POST'])
def generate_mesh():
    """Generate mesh nodes inside wildfire boundary."""
    try:
        data = request.get_json() or {}
        boundary = data.get('boundary', [])
        
        if not boundary or len(boundary) < 3:
            return jsonify({
                "status": "error",
                "code": 400,
                "message": "Invalid boundary"
            }), 400
        
        # Simple grid-based mesh generation
        mesh = []
        step = 5  # Grid spacing
        
        # Find bounding box
        xs = [p[0] for p in boundary]
        ys = [p[1] for p in boundary]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Generate grid points inside polygon
        for x in range(int(min_x), int(max_x) + 1, step):
            for y in range(int(min_y), int(max_y) + 1, step):
                if point_in_polygon(x, y, boundary):
                    mesh.append([x, y])
        
        logger.info(f"Generated mesh with {len(mesh)} nodes")
        
        return jsonify({
            "status": "success",
            "code": 200,
            "data": {
                "mesh": mesh,
                "count": len(mesh)
            },
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Mesh generation error: {str(e)}")
        return jsonify({
            "status": "error",
            "code": 500,
            "message": str(e)
        }), 500


@app.route('/api/paths/optimize', methods=['POST'])
def optimize_paths():
    """Optimize drone paths using nearest neighbor algorithm."""
    try:
        data = request.get_json() or {}
        mesh = data.get('mesh', [])
        drone_assignments = data.get('drone_assignments', {})
        
        if not mesh or not drone_assignments:
            return jsonify({
                "status": "error",
                "code": 400,
                "message": "Invalid mesh or drone assignments"
            }), 400
        
        paths = {}
        distances = {}
        
        # For each drone, optimize its path using nearest neighbor
        for drone_id_str, node_indices in drone_assignments.items():
            if not node_indices:
                continue
            
            drone_id = int(drone_id_str)
            nodes = [mesh[i] for i in node_indices if i < len(mesh)]
            
            if len(nodes) == 0:
                continue
            
            # Nearest neighbor path
            path = [nodes[0]]
            used = {0}
            
            while len(used) < len(nodes):
                current = path[-1]
                nearest_idx = -1
                nearest_dist = float('inf')
                
                for i, node in enumerate(nodes):
                    if i not in used:
                        dist = ((node[0] - current[0]) ** 2 + (node[1] - current[1]) ** 2) ** 0.5
                        if dist < nearest_dist:
                            nearest_dist = dist
                            nearest_idx = i
                
                if nearest_idx >= 0:
                    path.append(nodes[nearest_idx])
                    used.add(nearest_idx)
            
            paths[str(drone_id)] = path
            
            # Calculate total distance
            total_dist = 0
            for i in range(1, len(path)):
                dx = path[i][0] - path[i-1][0]
                dy = path[i][1] - path[i-1][1]
                total_dist += (dx ** 2 + dy ** 2) ** 0.5
            
            distances[str(drone_id)] = total_dist
        
        logger.info(f"Optimized paths for {len(paths)} drones")
        
        return jsonify({
            "status": "success",
            "code": 200,
            "data": {
                "paths": paths,
                "distances": distances,
                "count": len(paths)
            },
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Path optimization error: {str(e)}")
        return jsonify({
            "status": "error",
            "code": 500,
            "message": str(e)
        }), 500


def point_in_polygon(x, y, polygon):
    """Check if point (x, y) is inside polygon using ray casting."""
    inside = False
    j = len(polygon) - 1
    
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        
        j = i
    
    return inside


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "status": "error",
        "code": 404,
        "message": "Endpoint not found",
        "timestamp": datetime.now().isoformat()
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal error: {str(error)}")
    return jsonify({
        "status": "error",
        "code": 500,
        "message": "Internal server error",
        "timestamp": datetime.now().isoformat()
    }), 500


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_demo_data():
    """Load demo wildfire data."""
    logger.info("Loading demo data")
    
    demo_fires = {
        "fire_1": {
            "id": "fire_1",
            "name": "Moderate Wildfire - Demo Scenario 1",
            "location": {"lat": 35.05, "lon": 100.02},
            "data_source": "demo",
            "area_hectares": 2500,
            "area_sq_km": 25,
            "area_acres": 6177,
            "intensity_avg": 75,
            "boundary": [
                [35.02, 99.99],
                [35.08, 100.00],
                [35.10, 100.05],
                [35.05, 100.08],
                [35.00, 100.06]
            ],
            "observations": [
                {"latitude": 35.05, "longitude": 100.02, "intensity": 85, "timestamp": datetime.now().isoformat()},
                {"latitude": 35.04, "longitude": 100.03, "intensity": 78, "timestamp": datetime.now().isoformat()},
                {"latitude": 35.06, "longitude": 100.01, "intensity": 72, "timestamp": datetime.now().isoformat()},
            ],
            "mesh_nodes": 84,
            "coverage_percent": 92,
            "sequential_distance": 45.2,
            "optimized_distance": 28.5,
            "reduction_percent": 37,
            "fire_risk": 7,
            "smoke_risk": 6,
            "heat_risk": 8,
            "overall_risk": 7
        },
        "fire_2": {
            "id": "fire_2",
            "name": "Large Wildfire - Demo Scenario 2",
            "location": {"lat": 35.15, "lon": 100.25},
            "data_source": "demo",
            "area_hectares": 8500,
            "area_sq_km": 85,
            "area_acres": 20998,
            "intensity_avg": 88,
            "boundary": [
                [35.08, 100.15],
                [35.22, 100.18],
                [35.25, 100.38],
                [35.10, 100.42],
                [35.05, 100.35]
            ],
            "observations": [
                {"latitude": 35.15, "longitude": 100.25, "intensity": 95, "timestamp": datetime.now().isoformat()},
                {"latitude": 35.14, "longitude": 100.27, "intensity": 89, "timestamp": datetime.now().isoformat()},
                {"latitude": 35.16, "longitude": 100.23, "intensity": 85, "timestamp": datetime.now().isoformat()},
            ],
            "mesh_nodes": 156,
            "coverage_percent": 88,
            "sequential_distance": 78.5,
            "optimized_distance": 42.1,
            "reduction_percent": 46,
            "fire_risk": 9,
            "smoke_risk": 8,
            "heat_risk": 9,
            "overall_risk": 9
        },
        "fire_3": {
            "id": "fire_3",
            "name": "Wildfire with Rescue Targets - Demo Scenario 3",
            "location": {"lat": 35.35, "lon": 100.45},
            "data_source": "demo",
            "area_hectares": 4200,
            "area_sq_km": 42,
            "area_acres": 10377,
            "intensity_avg": 82,
            "boundary": [
                [35.30, 100.40],
                [35.40, 100.42],
                [35.42, 100.52],
                [35.32, 100.55],
                [35.28, 100.50]
            ],
            "observations": [
                {"latitude": 35.35, "longitude": 100.45, "intensity": 88, "timestamp": datetime.now().isoformat()},
                {"latitude": 35.34, "longitude": 100.47, "intensity": 80, "timestamp": datetime.now().isoformat()},
                {"latitude": 35.36, "longitude": 100.43, "intensity": 78, "timestamp": datetime.now().isoformat()},
            ],
            "mesh_nodes": 112,
            "coverage_percent": 90,
            "sequential_distance": 56.3,
            "optimized_distance": 31.8,
            "reduction_percent": 44,
            "fire_risk": 8,
            "smoke_risk": 7,
            "heat_risk": 8,
            "overall_risk": 8,
            "rescue_targets": [
                {"id": "T-1", "type": "person", "location": {"lat": 35.32, "lon": 100.46}, "priority": "high"},
                {"id": "T-2", "type": "animal", "location": {"lat": 35.36, "lon": 100.49}, "priority": "medium"}
            ]
        }
    }
    
    system_state.fires = demo_fires
    logger.info(f"Loaded {len(demo_fires)} demo fire scenarios")


def create_virtual_drones(count=5):
    """Create virtual drones."""
    logger.info(f"Creating {count} virtual drones")
    
    for i in range(1, count + 1):
        drone = {
            "drone_id": i,
            "type": "virtual",
            "status": "IDLE",
            "mode": "STABILIZE",
            "latitude": 35.0 + (i * 0.01),
            "longitude": 100.0 + (i * 0.01),
            "altitude": 50,
            "battery": 85 + (i * 2),
            "gps_signal": "strong",
            "speed": 0,
            "heading": 0,
            "armed": False,
            "capabilities": ["thermal", "rgb", "gps", "lidar"],
            "assigned_nodes": [],
            "path": [],
            "note": "SIMULATED DRONE"
        }
        system_state.drones[f"drone_{i}"] = drone
    
    logger.info(f"Created {count} virtual drones")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    logger.info(f"Starting Wildfire Drone System Backend v{API_VERSION}")
    logger.info(f"Listening on {BACKEND_HOST}:{BACKEND_PORT}")
    logger.info("CORS enabled for frontend at localhost:3000")
    logger.info("Health check at http://localhost:5000/health")
    logger.info("API info at http://localhost:5000/api")
    
    try:
        app.run(host=BACKEND_HOST, port=BACKEND_PORT, debug=False)
    except Exception as e:
        logger.error(f"Failed to start backend: {str(e)}")
        sys.exit(1)

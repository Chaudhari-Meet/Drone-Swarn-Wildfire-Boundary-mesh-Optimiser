"""
Flask Backend Server for Wildfire Drone Swarm System
Provides RESTful API and WebSocket support for the web frontend
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import sys
from pathlib import Path

# Add parent project to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_logger, DEFAULT_MODE, FEATURES
from application import WildfireResponseSystem

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Setup logging
logger = get_logger("flask_backend")

# Global system instance
wildfire_system = None
active_sessions = {}
active_missions = {}


# ==================== INITIALIZATION ====================

def initialize_system():
    """Initialize the wildfire system"""
    global wildfire_system
    try:
        wildfire_system = WildfireResponseSystem(mode=DEFAULT_MODE)
        logger.info("System initialized successfully")
        return True
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        return False


# ==================== SERVE STATIC FILES ====================

@app.route('/')
def serve_index():
    """Serve the React frontend"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')


# ==================== HEALTH & STATUS ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'system_initialized': wildfire_system is not None
    })


# ==================== AUTHENTICATION ====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authentication endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        # Demo credentials
        demo_users = {
            'admin': {'password': 'admin123', 'role': 'Admin'},
            'operator': {'password': 'operator123', 'role': 'Operator'},
            'viewer': {'password': 'viewer123', 'role': 'Viewer'}
        }

        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username and password are required'
            }), 400

        if username not in demo_users:
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401

        user_data = demo_users[username]
        if user_data['password'] != password:
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401

        # Generate a simple token (in production, use JWT)
        token = f"token_{username}_{datetime.now().timestamp()}"
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'username': username,
                'role': user_data['role'],
                'email': f'{username}@wildfire.system'
            }
        }), 200

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': 'Login failed'
        }), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get system configuration"""
    return jsonify({
        'mode': DEFAULT_MODE,
        'features': FEATURES,
        'version': '1.0.0'
    })


@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Get current system status"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        status = wildfire_system.get_system_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== DATA MANAGEMENT ENDPOINTS ====================

@app.route('/api/data/load', methods=['POST'])
def load_fire_data():
    """Load fire data from specified source"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        data = request.get_json()
        source = data.get('source', 'simulation')
        params = data.get('params', {})
        
        # Set data source
        if not wildfire_system.set_data_source(source, params):
            return jsonify({'error': 'Failed to set data source'}), 400
        
        # Load fire data
        if not wildfire_system.load_fire_data():
            return jsonify({'error': 'Failed to load fire data'}), 400
        
        # Process fire data
        if not wildfire_system.process_fire_data():
            return jsonify({'error': 'Failed to process fire data'}), 400
        
        status = wildfire_system.get_system_status()
        
        # Broadcast to all connected clients
        socketio.emit('data_loaded', {'status': status}, broadcast=True)
        
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"Error loading fire data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/current', methods=['GET'])
def get_current_data():
    """Get current fire data"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        return jsonify({
            'fire_observations': wildfire_system.fire_observations if hasattr(wildfire_system, 'fire_observations') else [],
            'boundary': wildfire_system.fire_boundary if hasattr(wildfire_system, 'fire_boundary') else [],
            'area': wildfire_system.fire_area if hasattr(wildfire_system, 'fire_area') else 0,
        })
    except Exception as e:
        logger.error(f"Error getting current data: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== MESH GENERATION ENDPOINTS ====================

@app.route('/api/mesh/generate', methods=['POST'])
def generate_mesh():
    """Generate mesh coverage grid"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        data = request.get_json()
        spacing = data.get('spacing', 5)
        altitude = data.get('altitude', 50)
        
        if not wildfire_system.generate_mesh_coverage(spacing=spacing, altitude=altitude):
            return jsonify({'error': 'Failed to generate mesh'}), 400
        
        status = wildfire_system.get_system_status()
        socketio.emit('mesh_generated', {'status': status}, broadcast=True)
        
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"Error generating mesh: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/mesh/current', methods=['GET'])
def get_current_mesh():
    """Get current mesh data"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        mesh_nodes = wildfire_system.mesh_nodes if hasattr(wildfire_system, 'mesh_nodes') else []
        mesh_stats = wildfire_system.mesh_stats if hasattr(wildfire_system, 'mesh_stats') else {}
        
        return jsonify({
            'mesh_nodes': mesh_nodes,
            'mesh_stats': mesh_stats,
            'count': len(mesh_nodes)
        })
    except Exception as e:
        logger.error(f"Error getting mesh data: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== DRONE MANAGEMENT ENDPOINTS ====================

@app.route('/api/drones/allocate', methods=['POST'])
def allocate_drones():
    """Allocate drones for mesh coverage"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        data = request.get_json()
        num_drones = data.get('num_drones', 10)
        
        if not wildfire_system.allocate_drones(num_drones=num_drones):
            return jsonify({'error': 'Failed to allocate drones'}), 400
        
        status = wildfire_system.get_system_status()
        socketio.emit('drones_allocated', {'status': status}, broadcast=True)
        
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"Error allocating drones: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/drones/list', methods=['GET'])
def list_drones():
    """Get list of allocated drones"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        drones = wildfire_system.drones if hasattr(wildfire_system, 'drones') else []
        
        drone_list = []
        for drone in drones:
            drone_list.append({
                'id': drone.drone_id if hasattr(drone, 'drone_id') else 'unknown',
                'position': [getattr(drone, 'latitude', 0), getattr(drone, 'longitude', 0)],
                'battery': getattr(drone, 'battery_level', 100),
                'status': getattr(drone, 'status', 'idle'),
                'assigned_nodes': len(getattr(drone, 'assigned_nodes', []))
            })
        
        return jsonify({'drones': drone_list, 'count': len(drone_list)})
    except Exception as e:
        logger.error(f"Error listing drones: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== PATH PLANNING ENDPOINTS ====================

@app.route('/api/paths/optimize', methods=['POST'])
def optimize_paths():
    """Optimize drone paths"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        data = request.get_json()
        use_two_opt = data.get('use_two_opt', True)
        
        if not wildfire_system.optimize_drone_paths(use_two_opt=use_two_opt):
            return jsonify({'error': 'Failed to optimize paths'}), 400
        
        status = wildfire_system.get_system_status()
        socketio.emit('paths_optimized', {'status': status}, broadcast=True)
        
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"Error optimizing paths: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/paths/current', methods=['GET'])
def get_current_paths():
    """Get current drone paths"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        paths = []
        if hasattr(wildfire_system, 'drones'):
            for drone in wildfire_system.drones:
                path = getattr(drone, 'path', [])
                if path:
                    paths.append({
                        'drone_id': getattr(drone, 'drone_id', 'unknown'),
                        'path': path,
                        'distance': getattr(drone, 'path_distance', 0)
                    })
        
        return jsonify({'paths': paths, 'count': len(paths)})
    except Exception as e:
        logger.error(f"Error getting paths: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== RISK ANALYSIS ENDPOINTS ====================

@app.route('/api/risk/analyze', methods=['POST'])
def analyze_risk():
    """Analyze risk zones and hazards"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        if not wildfire_system.analyze_risk():
            return jsonify({'error': 'Failed to analyze risk'}), 400
        
        status = wildfire_system.get_system_status()
        socketio.emit('risk_analyzed', {'status': status}, broadcast=True)
        
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"Error analyzing risk: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/risk/zones', methods=['GET'])
def get_risk_zones():
    """Get current risk zones"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        risk_zones = getattr(wildfire_system, 'risk_zones', {})
        return jsonify(risk_zones)
    except Exception as e:
        logger.error(f"Error getting risk zones: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== DETECTION ENDPOINTS ====================

@app.route('/api/detection/run', methods=['POST'])
def run_detection():
    """Run object detection (animals/persons)"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        if not wildfire_system.detect_objects():
            return jsonify({'error': 'Failed to run detection'}), 400
        
        status = wildfire_system.get_system_status()
        socketio.emit('detection_complete', {'status': status}, broadcast=True)
        
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"Error running detection: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/detection/results', methods=['GET'])
def get_detection_results():
    """Get detection results"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        detections = getattr(wildfire_system, 'detections', [])
        return jsonify({
            'detections': detections,
            'count': len(detections),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting detection results: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== FIREFIGHTER ROUTES ENDPOINTS ====================

@app.route('/api/routes/generate', methods=['POST'])
def generate_routes():
    """Generate firefighter routes"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        data = request.get_json()
        start_point = tuple(data.get('start_point', [35.0, -120.0]))
        end_point = tuple(data.get('end_point', [35.5, -119.5]))
        
        if not wildfire_system.generate_firefighter_routes(start_point=start_point, end_point=end_point):
            return jsonify({'error': 'Failed to generate routes'}), 400
        
        status = wildfire_system.get_system_status()
        socketio.emit('routes_generated', {'status': status}, broadcast=True)
        
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"Error generating routes: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/routes/list', methods=['GET'])
def get_routes():
    """Get generated firefighter routes"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        routes = getattr(wildfire_system, 'firefighter_routes', [])
        return jsonify({'routes': routes, 'count': len(routes)})
    except Exception as e:
        logger.error(f"Error getting routes: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== MISSION EXECUTION ENDPOINTS ====================

@app.route('/api/mission/run', methods=['POST'])
def run_mission():
    """Execute complete mission"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        data = request.get_json()
        num_drones = data.get('num_drones', 10)
        mesh_spacing = data.get('mesh_spacing', 5)
        
        logger.info(f"Starting full mission: {num_drones} drones, {mesh_spacing}m spacing")
        
        if wildfire_system.run_full_mission(num_drones=num_drones, mesh_spacing=mesh_spacing):
            status = wildfire_system.get_system_status()
            socketio.emit('mission_complete', {'status': status}, broadcast=True)
            
            return jsonify({
                'success': True,
                'status': status,
                'message': 'Mission completed successfully'
            })
        else:
            return jsonify({'error': 'Mission execution failed'}), 400
            
    except Exception as e:
        logger.error(f"Error running mission: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== REPORTING ENDPOINTS ====================

@app.route('/api/report/export', methods=['POST'])
def export_report():
    """Export mission report"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        data = request.get_json()
        filename = data.get('filename', f'wildfire_mission_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        # Export report
        if wildfire_system.export_report(filename):
            return jsonify({
                'success': True,
                'filename': filename,
                'message': 'Report exported successfully'
            })
        else:
            return jsonify({'error': 'Failed to export report'}), 400
            
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/report/current', methods=['GET'])
def get_current_report():
    """Get current mission data as report"""
    if not wildfire_system:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        status = wildfire_system.get_system_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting current report: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== WEBSOCKET EVENTS ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f'Client connected: {request.sid}')
    emit('connection_response', {'data': 'Connected to Wildfire System'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f'Client disconnected: {request.sid}')


@socketio.on('request_status')
def handle_status_request():
    """Handle real-time status request"""
    if wildfire_system:
        status = wildfire_system.get_system_status()
        emit('status_update', status)


@socketio.on('request_visualization_data')
def handle_viz_data_request():
    """Handle visualization data request"""
    if wildfire_system:
        try:
            data = {
                'fire': getattr(wildfire_system, 'fire_observations', []),
                'boundary': getattr(wildfire_system, 'fire_boundary', []),
                'mesh': getattr(wildfire_system, 'mesh_nodes', []),
                'drones': [],
                'paths': [],
                'risk_zones': getattr(wildfire_system, 'risk_zones', {}),
                'detections': getattr(wildfire_system, 'detections', [])
            }
            
            # Add drone data
            if hasattr(wildfire_system, 'drones'):
                for drone in wildfire_system.drones:
                    data['drones'].append({
                        'id': getattr(drone, 'drone_id', 'unknown'),
                        'position': [getattr(drone, 'latitude', 0), getattr(drone, 'longitude', 0)],
                        'battery': getattr(drone, 'battery_level', 100),
                        'status': getattr(drone, 'status', 'idle')
                    })
                    
                    path = getattr(drone, 'path', [])
                    if path:
                        data['paths'].append({
                            'drone_id': getattr(drone, 'drone_id', 'unknown'),
                            'path': path,
                            'distance': getattr(drone, 'path_distance', 0)
                        })
            
            emit('visualization_data', data)
        except Exception as e:
            logger.error(f"Error preparing visualization data: {e}")
            emit('error', {'message': str(e)})


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


# ==================== MAIN ====================

def main():
    """Main application entry point"""
    logger.info("="*70)
    logger.info("WILDFIRE DRONE SYSTEM - WEB BACKEND")
    logger.info("="*70)
    
    # Initialize system
    if not initialize_system():
        logger.error("Failed to initialize system")
        return
    
    # Run Flask app with SocketIO
    logger.info("Starting Flask server with SocketIO support...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
    main()

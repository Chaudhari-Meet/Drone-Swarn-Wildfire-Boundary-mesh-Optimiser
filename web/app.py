"""
Flask Web Application Backend - REST API for Wildfire Drone System

Endpoints:
- /api/system/* - System status and configuration
- /api/drones/* - Drone management and control
- /api/missions/* - Mission planning and execution
- /api/fire/* - Fire data and boundaries
- /api/dashboard/* - Real-time dashboard data
- /api/export/* - Data export and reporting
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_restful import Api, Resource
from functools import wraps
import threading
import json
import logging
from datetime import datetime, timedelta
from io import BytesIO
import csv
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from application import WildfireResponseSystem
from Drone.MAVLinkProtocol import DroneMode
from Drone.TelemetrySystem import DroneFleetTelemetry, MissionWaypoint
from Drone.FleetCoordinator import FleetCoordinator, DroneTask, FleetFormation
from Data.DataSourceAggregator import DataSourceAggregator

# Initialize Flask app
app = Flask(__name__)
CORS(app)
api = Api(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global system state
system: Optional[WildfireResponseSystem] = None
fleet_telemetry: Optional[DroneFleetTelemetry] = None
coordinator: Optional[FleetCoordinator] = None
aggregator: Optional[DataSourceAggregator] = None


class APIResponse:
    """Standard API response wrapper."""

    @staticmethod
    def success(data=None, message="Success", code=200):
        """Return successful response."""
        return {
            'status': 'success',
            'code': code,
            'message': message,
            'data': data or {},
            'timestamp': datetime.now().isoformat(),
        }, code

    @staticmethod
    def error(message="Error", code=400, details=None):
        """Return error response."""
        return {
            'status': 'error',
            'code': code,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat(),
        }, code


def require_auth(f):
    """Authentication decorator (simplified for demo)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return APIResponse.error("Missing authorization", 401)
        return f(*args, **kwargs)
    return decorated


# ============================================================================
# System Management Endpoints
# ============================================================================

class SystemStatus(Resource):
    """Get system status."""

    def get(self):
        """Get overall system status."""
        try:
            if not system:
                return APIResponse.error("System not initialized", 503)

            status = system.get_system_status()
            fleet_status = fleet_telemetry.get_fleet_status() if fleet_telemetry else {}

            return APIResponse.success({
                'system': status,
                'fleet': {drone_id: {
                    'armed': s.armed,
                    'mode': s.mode.name if s.mode else None,
                    'position': s.position,
                    'battery': s.battery_level,
                    'last_update': s.last_update.isoformat() if s.last_update else None,
                } for drone_id, s in fleet_status.items()},
                'timestamp': datetime.now().isoformat(),
            })
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return APIResponse.error(str(e), 500)


class SystemInitialize(Resource):
    """Initialize system."""

    def post(self):
        """Initialize the system."""
        try:
            global system, fleet_telemetry, coordinator, aggregator

            data = request.get_json() or {}
            mode = data.get('mode', 'simulation')
            num_drones = data.get('num_drones', 5)

            # Initialize components
            system = WildfireResponseSystem(mode=mode)
            fleet_telemetry = DroneFleetTelemetry(num_drones=num_drones)
            coordinator = FleetCoordinator(fleet_telemetry, num_drones=num_drones)
            aggregator = DataSourceAggregator()

            logger.info(f"System initialized: mode={mode}, drones={num_drones}")

            return APIResponse.success({
                'message': 'System initialized',
                'mode': mode,
                'num_drones': num_drones,
            }, code=201)
        except Exception as e:
            logger.error(f"Error initializing system: {e}")
            return APIResponse.error(str(e), 500)


# ============================================================================
# Fire Data Endpoints
# ============================================================================

class FireData(Resource):
    """Get fire observation data."""

    def get(self):
        """Get current fire data."""
        try:
            if not system:
                return APIResponse.error("System not initialized", 503)

            system.load_fire_data()
            system.process_fire_data()

            observations = system.fire_observations or []
            boundary = system.fire_boundary

            return APIResponse.success({
                'observations': [
                    {
                        'id': i,
                        'latitude': obs.latitude,
                        'longitude': obs.longitude,
                        'confidence': obs.confidence,
                        'temperature': obs.temperature if hasattr(obs, 'temperature') else None,
                        'source': obs.source_type if hasattr(obs, 'source_type') else 'unknown',
                    }
                    for i, obs in enumerate(observations[:100])  # Limit to 100
                ],
                'boundary': {
                    'points': boundary.boundary_points if boundary else [],
                    'method': boundary.method if boundary else None,
                } if boundary else None,
                'statistics': {
                    'observation_count': len(observations),
                    'area_hectares': system.fire_area_units.get('hectares', 0),
                },
            })
        except Exception as e:
            logger.error(f"Error getting fire data: {e}")
            return APIResponse.error(str(e), 500)


class RiskAnalysis(Resource):
    """Get risk analysis."""

    def get(self):
        """Get risk zones and analysis."""
        try:
            if not system:
                return APIResponse.error("System not initialized", 503)

            system.analyze_risk()

            return APIResponse.success({
                'risk_zones': len(system.risk_zones),
                'zones': [
                    {
                        'center': zone.get('center'),
                        'radius': zone.get('radius'),
                        'risk_level': zone.get('risk_level'),
                    }
                    for zone in system.risk_zones[:20]
                ] if system.risk_zones else [],
                'timestamp': datetime.now().isoformat(),
            })
        except Exception as e:
            logger.error(f"Error getting risk analysis: {e}")
            return APIResponse.error(str(e), 500)


# ============================================================================
# Drone Management Endpoints
# ============================================================================

class DroneList(Resource):
    """List all drones."""

    def get(self):
        """Get list of all drones."""
        try:
            if not fleet_telemetry:
                return APIResponse.error("Fleet not initialized", 503)

            statuses = fleet_telemetry.get_fleet_status()

            return APIResponse.success({
                'drones': [
                    {
                        'drone_id': drone_id,
                        'armed': status.armed,
                        'mode': status.mode.name if status.mode else None,
                        'position': status.position,
                        'battery_level': status.battery_level,
                        'signal_strength': status.signal_strength,
                        'last_update': status.last_update.isoformat() if status.last_update else None,
                    }
                    for drone_id, status in statuses.items()
                ],
                'count': len(statuses),
            })
        except Exception as e:
            logger.error(f"Error listing drones: {e}")
            return APIResponse.error(str(e), 500)


class DroneStatus(Resource):
    """Get individual drone status."""

    def get(self, drone_id):
        """Get status of specific drone."""
        try:
            if not fleet_telemetry:
                return APIResponse.error("Fleet not initialized", 503)

            status = fleet_telemetry.get_drone_status(drone_id)
            if not status:
                return APIResponse.error(f"Drone {drone_id} not found", 404)

            report = fleet_telemetry.get_flight_report(drone_id)

            return APIResponse.success(report)
        except Exception as e:
            logger.error(f"Error getting drone status: {e}")
            return APIResponse.error(str(e), 500)


class DroneCommand(Resource):
    """Send command to drone."""

    @require_auth
    def post(self, drone_id):
        """Send command to drone."""
        try:
            if not coordinator:
                return APIResponse.error("Coordinator not initialized", 503)

            data = request.get_json() or {}
            command = data.get('command')
            parameters = data.get('parameters', {})

            # Process commands
            if command == 'arm':
                logger.info(f"ARM command sent to drone {drone_id}")
            elif command == 'disarm':
                logger.info(f"DISARM command sent to drone {drone_id}")
            elif command == 'takeoff':
                altitude = parameters.get('altitude', 50)
                logger.info(f"TAKEOFF command sent to drone {drone_id} (altitude={altitude}m)")
            elif command == 'land':
                logger.info(f"LAND command sent to drone {drone_id}")
            elif command == 'goto':
                lat = parameters.get('latitude')
                lon = parameters.get('longitude')
                alt = parameters.get('altitude', 50)
                logger.info(f"GOTO command sent to drone {drone_id}: ({lat}, {lon}, {alt}m)")
            else:
                return APIResponse.error(f"Unknown command: {command}", 400)

            return APIResponse.success({
                'message': f"Command '{command}' sent to drone {drone_id}",
                'command': command,
                'drone_id': drone_id,
            })
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return APIResponse.error(str(e), 500)


# ============================================================================
# Mission Management Endpoints
# ============================================================================

class MissionList(Resource):
    """List missions."""

    def get(self):
        """Get list of missions."""
        try:
            if not fleet_telemetry:
                return APIResponse.error("Fleet not initialized", 503)

            missions = []
            for drone_id in range(1, 6):  # Get up to 5 missions
                mission = fleet_telemetry.get_mission(drone_id)
                if mission:
                    missions.append({
                        'mission_id': mission.mission_id,
                        'drone_id': mission.drone_id,
                        'waypoints': len(mission.waypoints),
                        'current_waypoint': mission.current_waypoint,
                        'is_active': mission.is_active,
                        'progress': (mission.current_waypoint / len(mission.waypoints) * 100) if mission.waypoints else 0,
                    })

            return APIResponse.success({'missions': missions})
        except Exception as e:
            logger.error(f"Error listing missions: {e}")
            return APIResponse.error(str(e), 500)


class MissionCreate(Resource):
    """Create new mission."""

    @require_auth
    def post(self):
        """Create a new mission."""
        try:
            if not fleet_telemetry:
                return APIResponse.error("Fleet not initialized", 503)

            data = request.get_json() or {}
            drone_id = data.get('drone_id')
            mission_id = data.get('mission_id', f"MISSION_{datetime.now().timestamp()}")
            waypoints_data = data.get('waypoints', [])

            if not drone_id:
                return APIResponse.error("drone_id required", 400)
            if not waypoints_data:
                return APIResponse.error("At least one waypoint required", 400)

            # Create waypoints
            waypoints = []
            for i, wp in enumerate(waypoints_data):
                waypoint = MissionWaypoint(
                    sequence=i,
                    latitude=wp.get('latitude'),
                    longitude=wp.get('longitude'),
                    altitude=wp.get('altitude', 50),
                    acceptance_radius=wp.get('acceptance_radius', 5),
                )
                waypoints.append(waypoint)

            # Create mission
            mission = fleet_telemetry.create_mission(drone_id, mission_id, waypoints)

            logger.info(f"Mission {mission_id} created for drone {drone_id} with {len(waypoints)} waypoints")

            return APIResponse.success({
                'mission_id': mission_id,
                'drone_id': drone_id,
                'waypoints': len(waypoints),
            }, code=201)
        except Exception as e:
            logger.error(f"Error creating mission: {e}")
            return APIResponse.error(str(e), 500)


class MissionControl(Resource):
    """Control mission execution."""

    @require_auth
    def post(self, mission_id, action):
        """Execute mission action."""
        try:
            if not fleet_telemetry:
                return APIResponse.error("Fleet not initialized", 503)

            # Find drone with this mission
            drone_id = None
            for did in range(1, 6):
                mission = fleet_telemetry.get_mission(did)
                if mission and mission.mission_id == mission_id:
                    drone_id = did
                    break

            if not drone_id:
                return APIResponse.error(f"Mission {mission_id} not found", 404)

            if action == 'start':
                fleet_telemetry.start_mission(drone_id)
                logger.info(f"Mission {mission_id} started")
            elif action == 'stop':
                fleet_telemetry.end_mission(drone_id)
                logger.info(f"Mission {mission_id} stopped")
            elif action == 'pause':
                logger.info(f"Mission {mission_id} paused")
            else:
                return APIResponse.error(f"Unknown action: {action}", 400)

            return APIResponse.success({
                'message': f"Mission {action} successful",
                'mission_id': mission_id,
                'action': action,
            })
        except Exception as e:
            logger.error(f"Error controlling mission: {e}")
            return APIResponse.error(str(e), 500)


# ============================================================================
# Dashboard Endpoints
# ============================================================================

class DashboardData(Resource):
    """Get real-time dashboard data."""

    def get(self):
        """Get all dashboard data."""
        try:
            if not system or not fleet_telemetry:
                return APIResponse.error("System not initialized", 503)

            # Get fire data
            system.load_fire_data()
            system.process_fire_data()

            # Get fleet status
            fleet_status = fleet_telemetry.get_fleet_report()

            return APIResponse.success({
                'fire': {
                    'observations': len(system.fire_observations or []),
                    'area_hectares': system.fire_area_units.get('hectares', 0),
                    'boundary_points': len(system.fire_boundary.boundary_points) if system.fire_boundary else 0,
                },
                'fleet': {
                    'total_drones': fleet_status['drone_count'],
                    'armed_drones': fleet_status['summary']['armed_count'],
                    'flying_drones': fleet_status['summary']['flying_count'],
                    'avg_battery': round(fleet_status['summary']['avg_battery'], 1),
                },
                'system': system.get_system_status(),
                'timestamp': datetime.now().isoformat(),
            })
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return APIResponse.error(str(e), 500)


# ============================================================================
# Export Endpoints
# ============================================================================

class ExportData(Resource):
    """Export data in various formats."""

    def get(self, format_type):
        """Export data."""
        try:
            if not system:
                return APIResponse.error("System not initialized", 503)

            system.load_fire_data()
            system.process_fire_data()

            if format_type == 'csv':
                # Create CSV
                output = BytesIO()
                writer = csv.writer(output.TextIOWrapper(output, encoding='utf-8'))
                
                # Write header
                writer.writerow(['latitude', 'longitude', 'confidence', 'source', 'timestamp'])
                
                # Write observations
                for obs in system.fire_observations or []:
                    writer.writerow([
                        obs.latitude,
                        obs.longitude,
                        obs.confidence,
                        obs.source_type if hasattr(obs, 'source_type') else 'unknown',
                        datetime.now().isoformat(),
                    ])

                output.seek(0)
                return send_file(
                    BytesIO(output.getvalue()),
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=f'fire_observations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                )

            elif format_type == 'json':
                data = {
                    'observations': [
                        {
                            'latitude': obs.latitude,
                            'longitude': obs.longitude,
                            'confidence': obs.confidence,
                        }
                        for obs in system.fire_observations or []
                    ],
                    'boundary': system.fire_boundary.boundary_points if system.fire_boundary else [],
                    'area_hectares': system.fire_area_units.get('hectares', 0),
                    'timestamp': datetime.now().isoformat(),
                }
                return APIResponse.success(data)

            elif format_type == 'geojson':
                features = []
                for obs in system.fire_observations or []:
                    features.append({
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': [obs.longitude, obs.latitude],
                        },
                        'properties': {
                            'confidence': obs.confidence,
                            'type': 'fire_observation',
                        },
                    })

                geojson = {
                    'type': 'FeatureCollection',
                    'features': features,
                }
                return APIResponse.success(geojson)

            else:
                return APIResponse.error(f"Unknown format: {format_type}", 400)

        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return APIResponse.error(str(e), 500)


# ============================================================================
# Register Resources
# ============================================================================

# System
api.add_resource(SystemStatus, '/api/system/status')
api.add_resource(SystemInitialize, '/api/system/initialize')

# Fire Data
api.add_resource(FireData, '/api/fire/data')
api.add_resource(RiskAnalysis, '/api/fire/risk')

# Drones
api.add_resource(DroneList, '/api/drones')
api.add_resource(DroneStatus, '/api/drones/<int:drone_id>')
api.add_resource(DroneCommand, '/api/drones/<int:drone_id>/command')

# Missions
api.add_resource(MissionList, '/api/missions')
api.add_resource(MissionCreate, '/api/missions/create')
api.add_resource(MissionControl, '/api/missions/<mission_id>/<action>')

# Dashboard
api.add_resource(DashboardData, '/api/dashboard')

# Export
api.add_resource(ExportData, '/api/export/<format_type>')


# ============================================================================
# Health Check
# ============================================================================

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return APIResponse.success({'status': 'healthy'})[0]


@app.route('/api')
def api_info():
    """API information."""
    return APIResponse.success({
        'name': 'Wildfire Drone System API',
        'version': '1.0.0',
        'endpoints': {
            'system': ['/api/system/status', '/api/system/initialize'],
            'fire': ['/api/fire/data', '/api/fire/risk'],
            'drones': ['/api/drones', '/api/drones/<id>', '/api/drones/<id>/command'],
            'missions': ['/api/missions', '/api/missions/create', '/api/missions/<id>/<action>'],
            'dashboard': ['/api/dashboard'],
            'export': ['/api/export/<format>'],
        },
    })[0]


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return APIResponse.error("Endpoint not found", 404)


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return APIResponse.error("Internal server error", 500)


# ============================================================================
# Application Factory
# ============================================================================

def create_app(config=None):
    """Create and configure app."""
    if config:
        app.config.update(config)
    
    logger.info("Flask app created and configured")
    return app


if __name__ == '__main__':
    # Development server
    logger.info("Starting Flask development server on http://0.0.0.0:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

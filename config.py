"""
Global configuration for Drone Swarm Wildfire Response System
"""
import os
import logging
from pathlib import Path

# ========================================================
# PATHS
# ========================================================

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "Data"
RESULTS_DIR = PROJECT_ROOT / "Results"
LOGS_DIR = PROJECT_ROOT / "Logs"
TEMP_DIR = PROJECT_ROOT / "Temp"

# Create directories if they don't exist
for directory in [DATA_DIR, RESULTS_DIR, LOGS_DIR, TEMP_DIR]:
    directory.mkdir(exist_ok=True)

# ========================================================
# LOGGING
# ========================================================

LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = LOGS_DIR / 'wildfire_system.log'

# ========================================================
# GIS CONFIGURATION
# ========================================================

DEFAULT_CRS = "EPSG:4326"  # WGS84 (latitude/longitude)
WORKING_CRS = "EPSG:3857"  # Web Mercator (for local calculations)
EARTH_RADIUS_M = 6371000  # meters

# ========================================================
# MESH CONFIGURATION
# ========================================================

DEFAULT_MESH_SPACING = 5  # meters or units
DEFAULT_DRONE_ALTITUDE = 50  # meters
DEFAULT_CAMERA_FOV = 60  # degrees
DEFAULT_COVERAGE_RADIUS = 30  # meters

# ========================================================
# DRONE CONFIGURATION
# ========================================================

DEFAULT_NUM_DRONES = 10
DEFAULT_DRONE_BATTERY = 100  # percentage
DEFAULT_DRONE_SPEED = 15  # m/s
DEFAULT_DRONE_MAX_FLIGHT_TIME = 1800  # seconds

DRONE_BATTERY_WARNING_THRESHOLD = 20  # percentage
DRONE_BATTERY_CRITICAL_THRESHOLD = 5  # percentage

# ========================================================
# RISK CONFIGURATION
# ========================================================

RISK_WEIGHTS = {
    "distance": 0.25,
    "fire": 0.25,
    "smoke": 0.15,
    "heat": 0.15,
    "wind": 0.10,
    "terrain": 0.05,
    "obstacle": 0.03,
    "battery": 0.02
}

# Risk zone thresholds (0-100 scale)
RISK_GREEN_THRESHOLD = 30      # Safe zone
RISK_YELLOW_THRESHOLD = 60     # Caution zone
RISK_RED_THRESHOLD = 100       # Restricted zone

# ========================================================
# SATELLITE DATA CONFIGURATION
# ========================================================

SATELLITE_DATA_SOURCES = {
    "nasa_firms": {
        "name": "NASA FIRMS",
        "url": "https://firms.modaps.eosdis.nasa.gov",
        "platforms": ["MODIS", "VIIRS"]
    },
    "copernicus": {
        "name": "Copernicus Sentinel",
        "url": "https://scihub.copernicus.eu",
        "platforms": ["Sentinel-1", "Sentinel-2"]
    }
}

# ========================================================
# DETECTION CONFIGURATION
# ========================================================

THERMAL_DETECTION = {
    "confidence_threshold": 0.7,
    "min_temperature": 50,  # Celsius
    "max_temperature": 300  # Celsius
}

ANIMAL_DETECTION = {
    "confidence_threshold": 0.8,
    "categories": ["dog", "cow", "deer", "livestock", "wildlife", "other_animal"]
}

PERSON_DETECTION = {
    "confidence_threshold": 0.85,
    "categories": ["civilian", "firefighter", "rescue_personnel", "unknown_person"]
}

# ========================================================
# FIREFIGHTER ROUTE CONFIGURATION
# ========================================================

FIREFIGHTER_ROUTE = {
    "objectives": ["shortest", "lowest_risk", "balanced"],
    "default_objective": "balanced",
    "safe_distance_from_fire": 50  # meters
}

# ========================================================
# VISUALIZATION CONFIGURATION
# ========================================================

UI_FIGURE_SIZE = (14, 10)
UI_DPI = 100
UI_GRID_ENABLED = True

BOUNDARY_COLOR = "red"
BOUNDARY_WIDTH = 2
WILDFIRE_REGION_COLOR = "orange"
WILDFIRE_REGION_ALPHA = 0.35

MESH_NODE_COLOR = "green"
MESH_NODE_SIZE = 30

DRONE_COLOR = "blue"
DRONE_PATH_COLOR = "cyan"
DRONE_PATH_WIDTH = 1.5

# ========================================================
# SIMULATION CONFIGURATION
# ========================================================

SIMULATION_TIME_STEP = 1  # seconds
SIMULATION_DEFAULT_SPEED = 1.0  # real-time multiplier
SIMULATION_MAX_SPEED = 10.0

# ========================================================
# DATA FORMAT CONFIGURATION
# ========================================================

SUPPORTED_FORMATS = {
    "boundary": ["json", "geojson", "kml"],
    "image": ["jpg", "jpeg", "png", "tiff", "tif"],
    "dataset": ["csv", "json", "geojson"]
}

# ========================================================
# API CONFIGURATION (for future cloud integration)
# ========================================================

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
API_KEY = os.getenv("API_KEY", "")
API_SECRET = os.getenv("API_SECRET", "")

# ========================================================
# DATABASE CONFIGURATION
# ========================================================

DATABASE_TYPE = "sqlite"  # sqlite, postgresql, mysql
DATABASE_PATH = DATA_DIR / "wildfire_system.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# ========================================================
# APPLICATION MODES
# ========================================================

MODES = {
    "real_drone": "Real Drone Mode (requires hardware)",
    "satellite": "Satellite Fire Data Mode (PRIMARY DEMO)",
    "historical": "Historical Wildfire Mode",
    "image_upload": "Satellite Image Upload Mode",
    "simulation": "Virtual Drone Simulation Mode"
}

DEFAULT_MODE = "simulation"  # Start in simulation mode for demo

# ========================================================
# PERFORMANCE CONFIGURATION
# ========================================================

ENABLE_PROFILING = False
CACHE_ENABLED = True
CACHE_TTL = 3600  # seconds

# ========================================================
# SAFETY CONFIGURATION
# ========================================================

HUMAN_IN_THE_LOOP_REQUIRED = {
    "confirm_boundary": True,
    "confirm_animal_detection": True,
    "confirm_person_detection": True,
    "confirm_drone_route": True,
    "confirm_firefighter_route": True,
    "confirm_emergency_action": True
}

# ========================================================
# DATA VALIDATION
# ========================================================

POLYGON_MIN_POINTS = 3
POLYGON_MAX_POINTS = 10000
COORDINATE_BOUNDS = {
    "lat_min": -90,
    "lat_max": 90,
    "lon_min": -180,
    "lon_max": 180
}

# ========================================================
# FEATURE FLAGS
# ========================================================

FEATURES = {
    "gis_enabled": True,
    "satellite_data_enabled": True,
    "historical_data_enabled": True,
    "image_upload_enabled": True,
    "virtual_drone_enabled": True,
    "risk_analysis_enabled": True,
    "detection_enabled": True,
    "firefighter_routing_enabled": True,
    "cloud_integration_enabled": True,
    "live_map_enabled": True,
    "dashboard_enabled": True,
    "reporting_enabled": True
}


def get_logger(name):
    """Get or create a logger with the configured settings."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(LOG_LEVEL)
        
        # File handler
        fh = logging.FileHandler(LOG_FILE)
        fh.setLevel(LOG_LEVEL)
        fh.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(fh)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(LOG_LEVEL)
        ch.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(ch)
    
    return logger

"""
Backend configuration for Wildfire Web System
"""

import os
from datetime import timedelta

# Flask Configuration
DEBUG = os.getenv('DEBUG', True)
TESTING = os.getenv('TESTING', False)
FLASK_ENV = os.getenv('FLASK_ENV', 'development')

# Server Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# CORS Configuration
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8080').split(',')

# Session Configuration
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', False)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///wildfire_system.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# SocketIO Configuration
SOCKETIO_MESSAGE_QUEUE = os.getenv('SOCKETIO_MESSAGE_QUEUE', None)
SOCKETIO_CORS_ALLOWED_ORIGINS = CORS_ORIGINS

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/wildfire_web.log')

# Wildfire System Configuration
WILDFIRE_DEFAULT_MODE = os.getenv('WILDFIRE_DEFAULT_MODE', 'simulation')
WILDFIRE_DEFAULT_NUM_DRONES = int(os.getenv('WILDFIRE_DEFAULT_NUM_DRONES', 10))
WILDFIRE_DEFAULT_MESH_SPACING = float(os.getenv('WILDFIRE_DEFAULT_MESH_SPACING', 5))

# File Upload Configuration
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload size
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = {'json', 'geojson', 'csv', 'tif', 'tiff', 'png', 'jpg', 'jpeg'}

# Cache Configuration
CACHE_TYPE = 'simple'
CACHE_DEFAULT_TIMEOUT = 300

# API Configuration
API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '100/hour')
API_TIMEOUT = int(os.getenv('API_TIMEOUT', 300))

# Features
FEATURES_ENABLED = {
    'satellite_data': os.getenv('FEATURE_SATELLITE', True),
    'real_drones': os.getenv('FEATURE_REAL_DRONES', False),
    'cloud_integration': os.getenv('FEATURE_CLOUD', False),
    'ml_detection': os.getenv('FEATURE_ML_DETECTION', True),
    'websocket': True,
    'reporting': True
}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

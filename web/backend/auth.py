"""
Authentication and authorization module for Wildfire Web System
Implements JWT-based authentication and role-based access control
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from flask_socketio import disconnect

# User roles
ROLE_ADMIN = "admin"
ROLE_OPERATOR = "operator"
ROLE_VIEWER = "viewer"

# Default credentials (CHANGE IN PRODUCTION!)
DEFAULT_USERS = {
    "admin": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": ROLE_ADMIN,
        "email": "admin@wildfire.local"
    },
    "operator": {
        "password_hash": hashlib.sha256("operator123".encode()).hexdigest(),
        "role": ROLE_OPERATOR,
        "email": "operator@wildfire.local"
    },
    "viewer": {
        "password_hash": hashlib.sha256("viewer123".encode()).hexdigest(),
        "role": ROLE_VIEWER,
        "email": "viewer@wildfire.local"
    }
}


class AuthManager:
    """Manages authentication and authorization"""

    def __init__(self, secret_key=None, token_expiry=24):
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
        self.token_expiry = token_expiry  # hours
        self.users = DEFAULT_USERS.copy()
        self.blacklist = set()  # Token blacklist for logout

    def hash_password(self, password):
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, username, password):
        """Verify username and password"""
        if username not in self.users:
            return False
        
        user = self.users[username]
        password_hash = self.hash_password(password)
        return user["password_hash"] == password_hash

    def generate_token(self, username, duration_hours=None):
        """Generate JWT token for user"""
        if not self.verify_password(username, self.users[username]["password_hash"]):
            # Skip password check if already verified
            pass

        user = self.users[username]
        duration = duration_hours or self.token_expiry

        payload = {
            'username': username,
            'role': user['role'],
            'email': user['email'],
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=duration),
            'jti': secrets.token_urlsafe(16)  # Unique token ID
        }

        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token

    def verify_token(self, token):
        """Verify JWT token and return payload"""
        try:
            if token in self.blacklist:
                return None

            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def revoke_token(self, token):
        """Add token to blacklist (logout)"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            # Store token ID (jti) instead of full token
            self.blacklist.add(payload.get('jti'))
            return True
        except:
            return False

    def create_user(self, username, password, role=ROLE_VIEWER, email=None):
        """Create new user (admin only)"""
        if username in self.users:
            return False, "User already exists"

        if role not in [ROLE_ADMIN, ROLE_OPERATOR, ROLE_VIEWER]:
            return False, "Invalid role"

        self.users[username] = {
            "password_hash": self.hash_password(password),
            "role": role,
            "email": email or f"{username}@wildfire.local"
        }
        return True, "User created successfully"

    def delete_user(self, username):
        """Delete user"""
        if username not in self.users:
            return False, "User not found"

        if username in ["admin", "operator", "viewer"]:
            return False, "Cannot delete default users"

        del self.users[username]
        return True, "User deleted"

    def change_password(self, username, old_password, new_password):
        """Change user password"""
        if not self.verify_password(username, old_password):
            return False, "Incorrect current password"

        self.users[username]["password_hash"] = self.hash_password(new_password)
        return True, "Password changed successfully"


# Global auth manager instance
auth_manager = AuthManager()


def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Invalid authorization header'}), 401

        if not token:
            return jsonify({'error': 'Missing authorization token'}), 401

        payload = auth_manager.verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Store user info in request context
        request.user = payload
        return f(*args, **kwargs)

    return decorated


def role_required(*allowed_roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'user'):
                return jsonify({'error': 'Authentication required'}), 401

            user_role = request.user.get('role')
            if user_role not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403

            return f(*args, **kwargs)

        return decorated
    return decorator


def socketio_token_required(f):
    """Decorator for SocketIO events requiring authentication"""
    @wraps(f)
    def decorated(data):
        token = None

        if 'token' in data:
            token = data['token']
        elif hasattr(request, 'args') and 'token' in request.args:
            token = request.args['token']

        if not token:
            disconnect()
            return False

        payload = auth_manager.verify_token(token)
        if not payload:
            disconnect()
            return False

        return f(data, payload)

    return decorated


# ==================== HELPER FUNCTIONS ====================

def get_current_user():
    """Get current authenticated user from request context"""
    return getattr(request, 'user', None)


def is_admin():
    """Check if current user is admin"""
    user = get_current_user()
    return user and user.get('role') == ROLE_ADMIN


def is_operator():
    """Check if current user is operator or admin"""
    user = get_current_user()
    return user and user.get('role') in [ROLE_OPERATOR, ROLE_ADMIN]


def generate_api_key():
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

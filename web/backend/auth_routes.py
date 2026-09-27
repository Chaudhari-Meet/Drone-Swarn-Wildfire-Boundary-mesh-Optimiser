"""
Authentication routes for Wildfire Web System
Handles login, logout, user management, and token operations
"""

from flask import Blueprint, request, jsonify, current_app
from flask_socketio import socketio
from auth import (
    auth_manager, token_required, role_required,
    ROLE_ADMIN, ROLE_OPERATOR, ROLE_VIEWER,
    get_current_user, is_admin
)
import logging

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


# ==================== AUTHENTICATION ENDPOINTS ====================

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint - returns JWT token"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Missing username or password'}), 400

        username = data.get('username')
        password = data.get('password')

        if not auth_manager.verify_password(username, password):
            logger.warning(f"Failed login attempt for user: {username}")
            return jsonify({'error': 'Invalid credentials'}), 401

        token = auth_manager.generate_token(username)
        
        logger.info(f"User logged in: {username}")
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'username': username,
                'role': auth_manager.users[username]['role'],
                'email': auth_manager.users[username]['email']
            }
        }), 200

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """Logout endpoint - revokes JWT token"""
    try:
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            token = auth_header.split(" ")[1]

        if token:
            auth_manager.revoke_token(token)

        username = request.user.get('username')
        logger.info(f"User logged out: {username}")

        return jsonify({'success': True, 'message': 'Logged out successfully'}), 200

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user_info():
    """Get current authenticated user information"""
    try:
        user = request.user
        return jsonify({
            'username': user.get('username'),
            'role': user.get('role'),
            'email': user.get('email'),
            'exp': user.get('exp')
        }), 200

    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@token_required
def refresh_token():
    """Refresh JWT token"""
    try:
        username = request.user.get('username')
        new_token = auth_manager.generate_token(username)

        return jsonify({
            'success': True,
            'token': new_token,
            'message': 'Token refreshed successfully'
        }), 200

    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== PASSWORD MANAGEMENT ====================

@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        
        if not data or not data.get('old_password') or not data.get('new_password'):
            return jsonify({'error': 'Missing required fields'}), 400

        username = request.user.get('username')
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        # Validate new password strength
        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        success, message = auth_manager.change_password(username, old_password, new_password)
        
        if not success:
            logger.warning(f"Failed password change for user: {username}")
            return jsonify({'error': message}), 401

        logger.info(f"Password changed for user: {username}")

        return jsonify({'success': True, 'message': message}), 200

    except Exception as e:
        logger.error(f"Password change error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== USER MANAGEMENT (ADMIN ONLY) ====================

@auth_bp.route('/users', methods=['GET'])
@token_required
@role_required(ROLE_ADMIN)
def list_users():
    """List all users (admin only)"""
    try:
        users = []
        for username, user_data in auth_manager.users.items():
            users.append({
                'username': username,
                'role': user_data['role'],
                'email': user_data['email']
            })

        return jsonify({'users': users, 'count': len(users)}), 200

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/users', methods=['POST'])
@token_required
@role_required(ROLE_ADMIN)
def create_user():
    """Create new user (admin only)"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Missing required fields'}), 400

        username = data.get('username')
        password = data.get('password')
        role = data.get('role', ROLE_VIEWER)
        email = data.get('email')

        # Validate password strength
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        # Validate role
        if role not in [ROLE_ADMIN, ROLE_OPERATOR, ROLE_VIEWER]:
            return jsonify({'error': 'Invalid role'}), 400

        success, message = auth_manager.create_user(username, password, role, email)
        
        if not success:
            logger.warning(f"Failed to create user: {username}")
            return jsonify({'error': message}), 400

        logger.info(f"User created by admin: {username} with role {role}")

        return jsonify({
            'success': True,
            'message': message,
            'user': {
                'username': username,
                'role': role,
                'email': email or f"{username}@wildfire.local"
            }
        }), 201

    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/users/<username>', methods=['DELETE'])
@token_required
@role_required(ROLE_ADMIN)
def delete_user(username):
    """Delete user (admin only)"""
    try:
        success, message = auth_manager.delete_user(username)
        
        if not success:
            return jsonify({'error': message}), 400

        logger.info(f"User deleted by admin: {username}")

        return jsonify({'success': True, 'message': message}), 200

    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/users/<username>/role', methods=['PUT'])
@token_required
@role_required(ROLE_ADMIN)
def update_user_role(username):
    """Update user role (admin only)"""
    try:
        if username not in auth_manager.users:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        new_role = data.get('role')

        if new_role not in [ROLE_ADMIN, ROLE_OPERATOR, ROLE_VIEWER]:
            return jsonify({'error': 'Invalid role'}), 400

        if username in ["admin", "operator", "viewer"]:
            return jsonify({'error': 'Cannot modify default users'}), 400

        auth_manager.users[username]['role'] = new_role
        logger.info(f"User role updated by admin: {username} -> {new_role}")

        return jsonify({
            'success': True,
            'message': 'User role updated',
            'user': {
                'username': username,
                'role': new_role,
                'email': auth_manager.users[username]['email']
            }
        }), 200

    except Exception as e:
        logger.error(f"Error updating user role: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== PERMISSION MANAGEMENT ====================

@auth_bp.route('/permissions', methods=['GET'])
@token_required
def get_permissions():
    """Get permissions for current user"""
    try:
        user_role = request.user.get('role')
        
        permissions = {
            ROLE_ADMIN: ['read_all', 'write_all', 'manage_users', 'manage_system'],
            ROLE_OPERATOR: ['read_all', 'write_all', 'run_missions'],
            ROLE_VIEWER: ['read_all']
        }

        return jsonify({
            'role': user_role,
            'permissions': permissions.get(user_role, [])
        }), 200

    except Exception as e:
        logger.error(f"Error getting permissions: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== SECURITY ENDPOINTS ====================

@auth_bp.route('/validate-token', methods=['GET'])
@token_required
def validate_token():
    """Validate if current token is still valid"""
    return jsonify({
        'valid': True,
        'user': request.user.get('username'),
        'role': request.user.get('role')
    }), 200


@auth_bp.route('/security-info', methods=['GET'])
def get_security_info():
    """Get security information (public endpoint)"""
    return jsonify({
        'jwt_enabled': True,
        'required_headers': ['Authorization: Bearer <token>'],
        'token_expiry_hours': auth_manager.token_expiry,
        'password_requirements': {
            'min_length': 6,
            'special_chars_recommended': True
        }
    }), 200


def register_auth_routes(app):
    """Register authentication routes with Flask app"""
    app.register_blueprint(auth_bp)
    logger.info("Authentication routes registered")

"""
Authentication Routes
Handles user authentication, registration, and token management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required, create_access_token, create_refresh_token,
    get_jwt_identity, get_jwt
)
from werkzeug.security import generate_password_hash
from models.user import User
from database import db
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

# Store blacklisted tokens (in production, use Redis or database)
blacklisted_tokens = set()

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Authenticate user
        user = User.authenticate(username, password)
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 403
        
        # Generate tokens
        tokens = user.generate_tokens()
        
        return jsonify({
            'message': 'Login successful',
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
@jwt_required()
def register():
    """User registration endpoint (admin only)"""
    try:
        # Check if current user is admin
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create user from data
        user = User.from_dict(data)
        
        # Validate user data
        errors = user.validate()
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        # Save user to database
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.get_by_id(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 404
        
        new_access_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            'access_token': new_access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout endpoint"""
    try:
        jti = get_jwt()['jti']
        blacklisted_tokens.add(jti)
        
        return jsonify({'message': 'Successfully logged out'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        current_user_id = get_jwt_identity()
        user = User.get_by_id(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    """Update current user information"""
    try:
        current_user_id = get_jwt_identity()
        user = User.get_by_id(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        allowed_fields = ['first_name', 'last_name', 'phone', 'email']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # Update password if provided
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        user.updated_at = datetime.utcnow()
        
        # Validate updated user
        errors = user.validate()
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        user = User.get_by_id(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Update password
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        users = User.get_all_active()
        
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get specific user (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        user = User.get_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update specific user (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        user = User.get_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        allowed_fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'is_admin', 'is_active']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # Update password if provided
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete specific user (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        if current_user_id == user_id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        user = User.get_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Soft delete by deactivating
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# JWT token blacklist checker
@auth_bp.before_app_request
def check_if_token_revoked():
    """Check if token is blacklisted"""
    try:
        if request.endpoint and 'auth' in request.endpoint:
            jwt_payload = get_jwt()
            if jwt_payload and jwt_payload.get('jti') in blacklisted_tokens:
                return jsonify({'error': 'Token has been revoked'}), 401
    except:
        pass  # Not all requests will have JWT tokens
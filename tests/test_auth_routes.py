"""
Authentication Routes Tests
Tests for all authentication-related API endpoints
"""

import pytest
import json
from models import User

class TestAuthRoutes:
    """Test cases for authentication routes"""
    
    def test_login_success(self, client, sample_user):
        """Test successful login"""
        response = client.post('/api/auth/login', json={
            'username': sample_user.username,
            'password': 'testpass123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'user' in data
        assert data['user']['username'] == sample_user.username
        assert data['message'] == 'Login successful'
    
    def test_login_invalid_credentials(self, client, sample_user):
        """Test login with invalid credentials"""
        response = client.post('/api/auth/login', json={
            'username': sample_user.username,
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Invalid credentials'
    
    def test_login_missing_data(self, client):
        """Test login with missing data"""
        response = client.post('/api/auth/login', json={
            'username': 'testuser'
            # Missing password
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Username and password are required' in data['error']
    
    def test_login_inactive_user(self, client, db_session):
        """Test login with inactive user"""
        user = User(
            username='inactiveuser',
            email='inactive@test.com',
            password='testpass123',
            is_active=False
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post('/api/auth/login', json={
            'username': 'inactiveuser',
            'password': 'testpass123'
        })
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Account is deactivated'
    
    def test_register_success(self, client, admin_headers, sample_user_data):
        """Test successful user registration by admin"""
        response = client.post('/api/auth/register', 
                              json=sample_user_data,
                              headers=admin_headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'User registered successfully'
        assert 'user' in data
        assert data['user']['username'] == sample_user_data['username']
    
    def test_register_non_admin(self, client, auth_headers, sample_user_data):
        """Test registration attempt by non-admin user"""
        response = client.post('/api/auth/register', 
                              json=sample_user_data,
                              headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Admin access required'
    
    def test_register_no_auth(self, client, sample_user_data):
        """Test registration without authentication"""
        response = client.post('/api/auth/register', json=sample_user_data)
        
        assert response.status_code == 401
    
    def test_register_invalid_data(self, client, admin_headers):
        """Test registration with invalid data"""
        invalid_data = {
            'username': '',  # Empty username
            'email': 'invalid-email',  # Invalid email
            'password': 'test123'
        }
        
        response = client.post('/api/auth/register', 
                              json=invalid_data,
                              headers=admin_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Validation failed'
        assert 'details' in data
    
    def test_refresh_token_success(self, client, sample_user):
        """Test successful token refresh"""
        # First login to get refresh token
        login_response = client.post('/api/auth/login', json={
            'username': sample_user.username,
            'password': 'testpass123'
        })
        
        refresh_token = login_response.get_json()['refresh_token']
        
        # Use refresh token to get new access token
        response = client.post('/api/auth/refresh', 
                              headers={'Authorization': f'Bearer {refresh_token}'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'user' in data
    
    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token"""
        response = client.post('/api/auth/refresh', 
                              headers={'Authorization': 'Bearer invalid_token'})
        
        assert response.status_code == 401  # Invalid token
    
    def test_logout_success(self, client, auth_headers):
        """Test successful logout"""
        response = client.post('/api/auth/logout', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Successfully logged out'
    
    def test_logout_no_auth(self, client):
        """Test logout without authentication"""
        response = client.post('/api/auth/logout')
        
        assert response.status_code == 401
    
    def test_get_current_user_success(self, client, auth_headers, sample_user):
        """Test getting current user info"""
        response = client.get('/api/auth/me', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'user' in data
        assert data['user']['username'] == sample_user.username
    
    def test_get_current_user_no_auth(self, client):
        """Test getting current user without authentication"""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
    
    def test_update_current_user_success(self, client, auth_headers):
        """Test updating current user info"""
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '9876543210'
        }
        
        response = client.put('/api/auth/me', 
                             json=update_data,
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'User updated successfully'
        assert data['user']['first_name'] == 'Updated'
        assert data['user']['last_name'] == 'Name'
    
    def test_update_current_user_with_password(self, client, auth_headers):
        """Test updating current user with password change"""
        update_data = {
            'first_name': 'Updated',
            'password': 'newpassword123'
        }
        
        response = client.put('/api/auth/me', 
                             json=update_data,
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'User updated successfully'
    
    def test_change_password_success(self, client, auth_headers):
        """Test successful password change"""
        change_data = {
            'current_password': 'testpass123',
            'new_password': 'newpassword123'
        }
        
        response = client.post('/api/auth/change-password', 
                              json=change_data,
                              headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Password changed successfully'
    
    def test_change_password_wrong_current(self, client, auth_headers):
        """Test password change with wrong current password"""
        change_data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123'
        }
        
        response = client.post('/api/auth/change-password', 
                              json=change_data,
                              headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Current password is incorrect'
    
    def test_change_password_missing_data(self, client, auth_headers):
        """Test password change with missing data"""
        change_data = {
            'current_password': 'testpass123'
            # Missing new_password
        }
        
        response = client.post('/api/auth/change-password', 
                              json=change_data,
                              headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Current password and new password are required' in data['error']
    
    def test_get_users_admin_success(self, client, admin_headers):
        """Test getting all users as admin"""
        response = client.get('/api/auth/users', headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'users' in data
        assert isinstance(data['users'], list)
    
    def test_get_users_non_admin(self, client, auth_headers):
        """Test getting users as non-admin"""
        response = client.get('/api/auth/users', headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Admin access required'
    
    def test_get_specific_user_admin(self, client, admin_headers, sample_user):
        """Test getting specific user as admin"""
        response = client.get(f'/api/auth/users/{sample_user.id}', 
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'user' in data
        assert data['user']['id'] == sample_user.id
    
    def test_get_specific_user_not_found(self, client, admin_headers):
        """Test getting non-existent user"""
        response = client.get('/api/auth/users/99999', headers=admin_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'User not found'
    
    def test_update_user_admin_success(self, client, admin_headers, sample_user):
        """Test updating user as admin"""
        update_data = {
            'first_name': 'AdminUpdated',
            'is_admin': True
        }
        
        response = client.put(f'/api/auth/users/{sample_user.id}', 
                             json=update_data,
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'User updated successfully'
        assert data['user']['first_name'] == 'AdminUpdated'
        assert data['user']['is_admin'] is True
    
    def test_update_user_non_admin(self, client, auth_headers, sample_user):
        """Test updating user as non-admin"""
        update_data = {
            'first_name': 'Updated'
        }
        
        response = client.put(f'/api/auth/users/{sample_user.id}', 
                             json=update_data,
                             headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Admin access required'
    
    def test_delete_user_admin_success(self, client, admin_headers, sample_user):
        """Test deleting user as admin (soft delete)"""
        response = client.delete(f'/api/auth/users/{sample_user.id}', 
                                headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'User deleted successfully'
    
    def test_delete_self_not_allowed(self, client, admin_headers, sample_admin):
        """Test admin cannot delete themselves"""
        response = client.delete(f'/api/auth/users/{sample_admin.id}', 
                                headers=admin_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Cannot delete your own account'
    
    def test_delete_user_non_admin(self, client, auth_headers, sample_user):
        """Test deleting user as non-admin"""
        response = client.delete(f'/api/auth/users/{sample_user.id}', 
                                headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Admin access required'
    
    def test_no_data_provided(self, client):
        """Test endpoints with no JSON data"""
        response = client.post('/api/auth/login')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'No data provided'
    
    def test_invalid_json(self, client):
        """Test endpoints with invalid JSON"""
        response = client.post('/api/auth/login', 
                              data='invalid json',
                              content_type='application/json')
        
        assert response.status_code == 400
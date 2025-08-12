"""
Customer Routes Tests
Tests for all customer-related API endpoints
"""

import pytest
import json
from models import Customer

class TestCustomerRoutes:
    """Test cases for customer routes"""
    
    def test_get_customers_success(self, client, auth_headers, sample_customer):
        """Test getting all customers"""
        response = client.get('/api/customers', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'customers' in data
        assert 'pagination' in data
        assert isinstance(data['customers'], list)
        assert len(data['customers']) >= 1
        assert data['customers'][0]['name'] == sample_customer.name
    
    def test_get_customers_pagination(self, client, auth_headers, sample_customer):
        """Test getting customers with pagination"""
        response = client.get('/api/customers?page=1&per_page=5', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'pagination' in data
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 5
        assert data['pagination']['total'] >= 0
    
    def test_get_customers_no_auth(self, client):
        """Test getting customers without authentication"""
        response = client.get('/api/customers')
        
        assert response.status_code == 401
    
    def test_get_specific_customer_success(self, client, auth_headers, sample_customer):
        """Test getting specific customer"""
        response = client.get(f'/api/customers/{sample_customer.id}', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'customer' in data
        assert data['customer']['id'] == sample_customer.id
        assert data['customer']['name'] == sample_customer.name
    
    def test_get_specific_customer_not_found(self, client, auth_headers):
        """Test getting non-existent customer"""
        response = client.get('/api/customers/99999', headers=auth_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'Customer not found'
    
    def test_create_customer_success(self, client, auth_headers, sample_customer_data):
        """Test creating customer"""
        response = client.post('/api/customers', 
                              json=sample_customer_data,
                              headers=auth_headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'Customer created successfully'
        assert 'customer' in data
        assert data['customer']['name'] == sample_customer_data['name']
    
    def test_create_customer_no_auth(self, client, sample_customer_data):
        """Test creating customer without authentication"""
        response = client.post('/api/customers', json=sample_customer_data)
        
        assert response.status_code == 401
    
    def test_create_customer_invalid_data(self, client, auth_headers):
        """Test creating customer with invalid data"""
        invalid_data = {
            'name': '',  # Empty name
            'email': 'invalid-email',  # Invalid email
            'phone': 'invalid-phone'  # Invalid phone
        }
        
        response = client.post('/api/customers', 
                              json=invalid_data,
                              headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Validation failed'
        assert 'details' in data
    
    def test_create_customer_no_data(self, client, auth_headers):
        """Test creating customer with no data"""
        response = client.post('/api/customers', headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'No data provided'
    
    def test_update_customer_success(self, client, auth_headers, sample_customer):
        """Test updating customer"""
        update_data = {
            'name': 'Updated Customer Name',
            'city': 'Updated City',
            'phone': '9999999999'
        }
        
        response = client.put(f'/api/customers/{sample_customer.id}', 
                             json=update_data,
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Customer updated successfully'
        assert data['customer']['name'] == 'Updated Customer Name'
        assert data['customer']['city'] == 'Updated City'
    
    def test_update_customer_not_found(self, client, auth_headers):
        """Test updating non-existent customer"""
        update_data = {
            'name': 'Updated Customer Name'
        }
        
        response = client.put('/api/customers/99999', 
                             json=update_data,
                             headers=auth_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'Customer not found'
    
    def test_update_customer_invalid_data(self, client, auth_headers, sample_customer):
        """Test updating customer with invalid data"""
        invalid_data = {
            'name': '',  # Empty name
            'email': 'invalid-email'
        }
        
        response = client.put(f'/api/customers/{sample_customer.id}', 
                             json=invalid_data,
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Validation failed'
    
    def test_delete_customer_success(self, client, admin_headers, sample_customer):
        """Test deleting customer as admin"""
        response = client.delete(f'/api/customers/{sample_customer.id}', 
                                headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Customer deleted successfully'
    
    def test_delete_customer_non_admin(self, client, auth_headers, sample_customer):
        """Test deleting customer as non-admin"""
        response = client.delete(f'/api/customers/{sample_customer.id}', 
                                headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Admin access required'
    
    def test_delete_customer_not_found(self, client, admin_headers):
        """Test deleting non-existent customer"""
        response = client.delete('/api/customers/99999', headers=admin_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'Customer not found'
    
    def test_delete_customer_with_invoices(self, client, admin_headers, sample_customer, sample_invoice):
        """Test deleting customer that has invoices"""
        # Ensure customer has invoices
        assert sample_invoice.customer_id == sample_customer.id
        
        response = client.delete(f'/api/customers/{sample_customer.id}', 
                                headers=admin_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Cannot delete customer with associated invoices' in data['error']
        assert 'invoice_count' in data
    
    def test_get_customer_invoices_success(self, client, auth_headers, sample_customer, sample_invoice):
        """Test getting customer invoices"""
        response = client.get(f'/api/customers/{sample_customer.id}/invoices', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'customer' in data
        assert 'invoices' in data
        assert 'pagination' in data
        assert data['customer']['id'] == sample_customer.id
        assert len(data['invoices']) >= 1
    
    def test_get_customer_invoices_with_filters(self, client, auth_headers, sample_customer, sample_invoice):
        """Test getting customer invoices with status filter"""
        response = client.get(f'/api/customers/{sample_customer.id}/invoices?status=DRAFT', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'invoices' in data
        # All returned invoices should have DRAFT status
        for invoice in data['invoices']:
            assert invoice['status'] == 'DRAFT'
    
    def test_get_customer_invoices_pagination(self, client, auth_headers, sample_customer):
        """Test getting customer invoices with pagination"""
        response = client.get(f'/api/customers/{sample_customer.id}/invoices?page=1&per_page=5', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'pagination' in data
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 5
    
    def test_search_customers_success(self, client, auth_headers, sample_customer):
        """Test searching customers"""
        response = client.get(f'/api/customers/search?q={sample_customer.name}', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'customers' in data
        assert 'query' in data
        assert data['query'] == sample_customer.name
        assert len(data['customers']) >= 1
    
    def test_search_customers_by_contact_person(self, client, auth_headers, sample_customer):
        """Test searching customers by contact person"""
        if sample_customer.contact_person:
            response = client.get(f'/api/customers/search?q={sample_customer.contact_person}', 
                                 headers=auth_headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'customers' in data
            assert len(data['customers']) >= 1
    
    def test_search_customers_no_query(self, client, auth_headers):
        """Test searching customers with no query"""
        response = client.get('/api/customers/search', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'customers' in data
        assert data['customers'] == []
    
    def test_search_customers_no_results(self, client, auth_headers):
        """Test searching customers with no results"""
        response = client.get('/api/customers/search?q=nonexistent', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'customers' in data
        assert len(data['customers']) == 0
    
    def test_validate_customer_success(self, client, auth_headers, sample_customer):
        """Test validating customer data"""
        response = client.post(f'/api/customers/{sample_customer.id}/validate', 
                              headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'valid' in data
        assert 'errors' in data
        assert data['valid'] is True
        assert len(data['errors']) == 0
    
    def test_validate_customer_with_errors(self, client, auth_headers, db_session):
        """Test validating customer with validation errors"""
        # Create invalid customer
        invalid_customer = Customer(
            name='',  # Empty name
            email='invalid-email',  # Invalid email
            phone='invalid-phone'  # Invalid phone
        )
        db_session.add(invalid_customer)
        db_session.commit()
        
        response = client.post(f'/api/customers/{invalid_customer.id}/validate', 
                              headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'valid' in data
        assert 'errors' in data
        assert data['valid'] is False
        assert len(data['errors']) > 0
    
    def test_get_customer_stats_success(self, client, auth_headers, sample_customer):
        """Test getting customer statistics"""
        response = client.get('/api/customers/stats', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_customers' in data
        assert 'customers_with_invoices' in data
        assert 'customers_by_state' in data
        assert 'top_customers' in data
        assert isinstance(data['customers_by_state'], list)
        assert isinstance(data['top_customers'], list)
        assert data['total_customers'] >= 1
    
    def test_export_customers_success(self, client, auth_headers, sample_customer):
        """Test exporting customers to CSV"""
        response = client.get('/api/customers/export', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'csv_data' in data
        assert 'filename' in data
        assert isinstance(data['csv_data'], list)
        assert len(data['csv_data']) >= 2  # Headers + at least one customer
        
        # Check CSV headers
        expected_headers = ['ID', 'Name', 'Address', 'City', 'State', 'Pincode',
                           'GSTIN', 'Contact Person', 'Phone', 'Email', 'Created At']
        assert data['csv_data'][0] == expected_headers
    
    def test_export_customers_no_auth(self, client):
        """Test exporting customers without authentication"""
        response = client.get('/api/customers/export')
        
        assert response.status_code == 401
    
    def test_customer_routes_error_handling(self, client, auth_headers):
        """Test error handling in customer routes"""
        # Test with invalid customer ID format
        response = client.get('/api/customers/invalid_id', headers=auth_headers)
        assert response.status_code == 404
        
        # First create a customer to test update
        customer_data = {'name': 'Test Customer for Error Handling'}
        create_response = client.post('/api/customers', json=customer_data, headers=auth_headers)
        assert create_response.status_code == 201
        customer_id = create_response.get_json()['customer']['id']
        
        # Test update with no data
        response = client.put(f'/api/customers/{customer_id}', headers=auth_headers)
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'No data provided'
    
    def test_customer_full_crud_flow(self, client, auth_headers, sample_customer_data):
        """Test complete CRUD flow for customer"""
        # Create
        response = client.post('/api/customers', 
                              json=sample_customer_data,
                              headers=auth_headers)
        assert response.status_code == 201
        customer_id = response.get_json()['customer']['id']
        
        # Read
        response = client.get(f'/api/customers/{customer_id}', 
                             headers=auth_headers)
        assert response.status_code == 200
        
        # Update
        update_data = {'name': 'Updated Customer Name'}
        response = client.put(f'/api/customers/{customer_id}', 
                             json=update_data,
                             headers=auth_headers)
        assert response.status_code == 200
        
        # Search
        response = client.get('/api/customers/search?q=Updated', 
                             headers=auth_headers)
        assert response.status_code == 200
        assert len(response.get_json()['customers']) >= 1
        
        # Validate
        response = client.post(f'/api/customers/{customer_id}/validate', 
                              headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json()['valid'] is True
    
    def test_customer_advanced_search(self, client, auth_headers, db_session):
        """Test advanced customer search functionality"""
        # Create customers in different states
        customers = [
            Customer(name='Customer A', city='City A', state='State A'),
            Customer(name='Customer B', city='City B', state='State B'),
            Customer(name='Customer C', city='City A', state='State A')
        ]
        
        for customer in customers:
            db_session.add(customer)
        db_session.commit()
        
        # Search by state
        response = client.get('/api/customers/search?q=State A', 
                             headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['customers']) == 2
        
        # Search by city
        response = client.get('/api/customers/search?q=City A', 
                             headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['customers']) == 2
    
    def test_customer_stats_detailed(self, client, auth_headers, db_session, sample_customer):
        """Test detailed customer statistics"""
        response = client.get('/api/customers/stats', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify structure
        assert 'total_customers' in data
        assert 'customers_with_invoices' in data
        assert 'customers_by_state' in data
        assert 'top_customers' in data
        
        # Verify data types
        assert isinstance(data['total_customers'], int)
        assert isinstance(data['customers_with_invoices'], int)
        assert isinstance(data['customers_by_state'], list)
        assert isinstance(data['top_customers'], list)
        
        # Check that total is reasonable
        assert data['total_customers'] >= 1
        assert data['customers_with_invoices'] >= 0
        assert data['customers_with_invoices'] <= data['total_customers']
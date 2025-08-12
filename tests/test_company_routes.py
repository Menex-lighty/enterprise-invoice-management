"""
Company Routes Tests
Tests for all company-related API endpoints
"""

import pytest
import json
from models import Company

class TestCompanyRoutes:
    """Test cases for company routes"""
    
    def test_get_companies_success(self, client, auth_headers, sample_company):
        """Test getting all companies"""
        response = client.get('/api/companies', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'companies' in data
        assert isinstance(data['companies'], list)
        assert len(data['companies']) >= 1
        assert data['companies'][0]['name'] == sample_company.name
    
    def test_get_companies_no_auth(self, client):
        """Test getting companies without authentication"""
        response = client.get('/api/companies')
        
        assert response.status_code == 401
    
    def test_get_specific_company_success(self, client, auth_headers, sample_company):
        """Test getting specific company"""
        response = client.get(f'/api/companies/{sample_company.id}', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'company' in data
        assert data['company']['id'] == sample_company.id
        assert data['company']['name'] == sample_company.name
    
    def test_get_specific_company_not_found(self, client, auth_headers):
        """Test getting non-existent company"""
        response = client.get('/api/companies/99999', headers=auth_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'Company not found'
    
    def test_create_company_success(self, client, admin_headers, sample_company_data):
        """Test creating company as admin"""
        response = client.post('/api/companies', 
                              json=sample_company_data,
                              headers=admin_headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'Company created successfully'
        assert 'company' in data
        assert data['company']['name'] == sample_company_data['name']
    
    def test_create_company_non_admin(self, client, auth_headers, sample_company_data):
        """Test creating company as non-admin"""
        response = client.post('/api/companies', 
                              json=sample_company_data,
                              headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Admin access required'
    
    def test_create_company_invalid_data(self, client, admin_headers):
        """Test creating company with invalid data"""
        invalid_data = {
            'name': '',  # Empty name
            'email': 'invalid-email',  # Invalid email
            'gstin': '123'  # Invalid GSTIN length
        }
        
        response = client.post('/api/companies', 
                              json=invalid_data,
                              headers=admin_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Validation failed'
        assert 'details' in data
    
    def test_create_company_no_data(self, client, admin_headers):
        """Test creating company with no data"""
        response = client.post('/api/companies', headers=admin_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'No data provided'
    
    def test_update_company_success(self, client, admin_headers, sample_company):
        """Test updating company as admin"""
        update_data = {
            'name': 'Updated Company Name',
            'city': 'Updated City',
            'contact_phone': '9999999999'
        }
        
        response = client.put(f'/api/companies/{sample_company.id}', 
                             json=update_data,
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Company updated successfully'
        assert data['company']['name'] == 'Updated Company Name'
        assert data['company']['city'] == 'Updated City'
    
    def test_update_company_non_admin(self, client, auth_headers, sample_company):
        """Test updating company as non-admin"""
        update_data = {
            'name': 'Updated Company Name'
        }
        
        response = client.put(f'/api/companies/{sample_company.id}', 
                             json=update_data,
                             headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Admin access required'
    
    def test_update_company_not_found(self, client, admin_headers):
        """Test updating non-existent company"""
        update_data = {
            'name': 'Updated Company Name'
        }
        
        response = client.put('/api/companies/99999', 
                             json=update_data,
                             headers=admin_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'Company not found'
    
    def test_update_company_invalid_data(self, client, admin_headers, sample_company):
        """Test updating company with invalid data"""
        invalid_data = {
            'name': '',  # Empty name
            'email': 'invalid-email'
        }
        
        response = client.put(f'/api/companies/{sample_company.id}', 
                             json=invalid_data,
                             headers=admin_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Validation failed'
    
    def test_delete_company_success(self, client, admin_headers, sample_company):
        """Test deleting company as admin"""
        response = client.delete(f'/api/companies/{sample_company.id}', 
                                headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Company deleted successfully'
    
    def test_delete_company_non_admin(self, client, auth_headers, sample_company):
        """Test deleting company as non-admin"""
        response = client.delete(f'/api/companies/{sample_company.id}', 
                                headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Admin access required'
    
    def test_delete_company_not_found(self, client, admin_headers):
        """Test deleting non-existent company"""
        response = client.delete('/api/companies/99999', headers=admin_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'Company not found'
    
    def test_delete_company_with_invoices(self, client, admin_headers, sample_company, sample_invoice):
        """Test deleting company that has invoices"""
        # Ensure company has invoices
        assert sample_invoice.company_id == sample_company.id
        
        response = client.delete(f'/api/companies/{sample_company.id}', 
                                headers=admin_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Cannot delete company with associated invoices' in data['error']
        assert 'invoice_count' in data
    
    def test_get_company_invoices_success(self, client, auth_headers, sample_company, sample_invoice):
        """Test getting company invoices"""
        response = client.get(f'/api/companies/{sample_company.id}/invoices', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'company' in data
        assert 'invoices' in data
        assert 'pagination' in data
        assert data['company']['id'] == sample_company.id
        assert len(data['invoices']) >= 1
    
    def test_get_company_invoices_with_filters(self, client, auth_headers, sample_company, sample_invoice):
        """Test getting company invoices with status filter"""
        response = client.get(f'/api/companies/{sample_company.id}/invoices?status=DRAFT', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'invoices' in data
        # All returned invoices should have DRAFT status
        for invoice in data['invoices']:
            assert invoice['status'] == 'DRAFT'
    
    def test_get_company_invoices_pagination(self, client, auth_headers, sample_company):
        """Test getting company invoices with pagination"""
        response = client.get(f'/api/companies/{sample_company.id}/invoices?page=1&per_page=5', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'pagination' in data
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 5
    
    def test_search_companies_success(self, client, auth_headers, sample_company):
        """Test searching companies"""
        response = client.get(f'/api/companies/search?q={sample_company.name}', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'companies' in data
        assert 'query' in data
        assert data['query'] == sample_company.name
        assert len(data['companies']) >= 1
    
    def test_search_companies_no_query(self, client, auth_headers):
        """Test searching companies with no query"""
        response = client.get('/api/companies/search', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'companies' in data
        assert data['companies'] == []
    
    def test_search_companies_no_results(self, client, auth_headers):
        """Test searching companies with no results"""
        response = client.get('/api/companies/search?q=nonexistent', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'companies' in data
        assert len(data['companies']) == 0
    
    def test_validate_company_success(self, client, auth_headers, sample_company):
        """Test validating company data"""
        response = client.post(f'/api/companies/{sample_company.id}/validate', 
                              headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'valid' in data
        assert 'errors' in data
        assert data['valid'] is True
        assert len(data['errors']) == 0
    
    def test_validate_company_with_errors(self, client, auth_headers, db_session):
        """Test validating company with validation errors"""
        # Create invalid company
        invalid_company = Company(
            name='',  # Empty name
            email='invalid-email',  # Invalid email
            gstin='123'  # Invalid GSTIN
        )
        db_session.add(invalid_company)
        db_session.commit()
        
        response = client.post(f'/api/companies/{invalid_company.id}/validate', 
                              headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'valid' in data
        assert 'errors' in data
        assert data['valid'] is False
        assert len(data['errors']) > 0
    
    def test_get_company_stats_success(self, client, auth_headers, sample_company):
        """Test getting company statistics"""
        response = client.get('/api/companies/stats', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_companies' in data
        assert 'companies_with_invoices' in data
        assert 'companies_by_state' in data
        assert isinstance(data['companies_by_state'], list)
        assert data['total_companies'] >= 1
    
    def test_get_company_stats_no_auth(self, client):
        """Test getting company statistics without authentication"""
        response = client.get('/api/companies/stats')
        
        assert response.status_code == 401
    
    def test_company_routes_error_handling(self, client, auth_headers):
        """Test error handling in company routes"""
        # Test with invalid company ID format
        response = client.get('/api/companies/invalid_id', headers=auth_headers)
        assert response.status_code == 404
        
        # Test update with no data
        response = client.put('/api/companies/1', headers=auth_headers)
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'No data provided'
    
    def test_company_full_crud_flow(self, client, admin_headers, sample_company_data):
        """Test complete CRUD flow for company"""
        # Create
        response = client.post('/api/companies', 
                              json=sample_company_data,
                              headers=admin_headers)
        assert response.status_code == 201
        company_id = response.get_json()['company']['id']
        
        # Read
        response = client.get(f'/api/companies/{company_id}', 
                             headers=admin_headers)
        assert response.status_code == 200
        
        # Update
        update_data = {'name': 'Updated Company Name'}
        response = client.put(f'/api/companies/{company_id}', 
                             json=update_data,
                             headers=admin_headers)
        assert response.status_code == 200
        
        # Delete
        response = client.delete(f'/api/companies/{company_id}', 
                                headers=admin_headers)
        assert response.status_code == 200
        
        # Verify deletion
        response = client.get(f'/api/companies/{company_id}', 
                             headers=admin_headers)
        assert response.status_code == 404
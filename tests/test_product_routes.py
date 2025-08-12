"""
Product Routes Tests
Tests for all product-related API endpoints
"""

import pytest
import json
from models import Product

class TestProductRoutes:
    """Test cases for product routes"""
    
    def test_get_products_success(self, client, auth_headers, sample_product):
        """Test getting all products"""
        response = client.get('/api/products', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'products' in data
        assert 'pagination' in data
        assert isinstance(data['products'], list)
        assert len(data['products']) >= 1
        assert data['products'][0]['name'] == sample_product.name
    
    def test_get_products_pagination(self, client, auth_headers, sample_product):
        """Test getting products with pagination"""
        response = client.get('/api/products?page=1&per_page=10', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'pagination' in data
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 10
        assert data['pagination']['total'] >= 0
    
    def test_get_products_with_category_filter(self, client, auth_headers, sample_product):
        """Test getting products with category filter"""
        response = client.get(f'/api/products?category={sample_product.category}', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'products' in data
        # All returned products should have the specified category
        for product in data['products']:
            assert product['category'] == sample_product.category
    
    def test_get_products_no_auth(self, client):
        """Test getting products without authentication"""
        response = client.get('/api/products')
        
        assert response.status_code == 401
    
    def test_get_specific_product_success(self, client, auth_headers, sample_product):
        """Test getting specific product"""
        response = client.get(f'/api/products/{sample_product.id}', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'product' in data
        assert data['product']['id'] == sample_product.id
        assert data['product']['name'] == sample_product.name
    
    def test_get_specific_product_not_found(self, client, auth_headers):
        """Test getting non-existent product"""
        response = client.get('/api/products/99999', headers=auth_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'Product not found'
    
    def test_create_product_success(self, client, auth_headers, sample_product_data):
        """Test creating product"""
        response = client.post('/api/products', 
                              json=sample_product_data,
                              headers=auth_headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'Product created successfully'
        assert 'product' in data
        assert data['product']['name'] == sample_product_data['name']
    
    def test_create_product_no_auth(self, client, sample_product_data):
        """Test creating product without authentication"""
        response = client.post('/api/products', json=sample_product_data)
        
        assert response.status_code == 401
    
    def test_create_product_invalid_data(self, client, auth_headers):
        """Test creating product with invalid data"""
        invalid_data = {
            'name': '',  # Empty name
            'rate': -10.0,  # Negative rate
            'unit': ''  # Empty unit
        }
        
        response = client.post('/api/products', 
                              json=invalid_data,
                              headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Validation failed'
        assert 'details' in data
    
    def test_create_product_no_data(self, client, auth_headers):
        """Test creating product with no data"""
        response = client.post('/api/products', headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'No data provided'
    
    def test_update_product_success(self, client, auth_headers, sample_product):
        """Test updating product"""
        update_data = {
            'name': 'Updated Product Name',
            'rate': 200.00,
            'description': 'Updated description'
        }
        
        response = client.put(f'/api/products/{sample_product.id}', 
                             json=update_data,
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Product updated successfully'
        assert data['product']['name'] == 'Updated Product Name'
        assert data['product']['rate'] == 200.00
    
    def test_update_product_not_found(self, client, auth_headers):
        """Test updating non-existent product"""
        update_data = {
            'name': 'Updated Product Name'
        }
        
        response = client.put('/api/products/99999', 
                             json=update_data,
                             headers=auth_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'Product not found'
    
    def test_update_product_invalid_data(self, client, auth_headers, sample_product):
        """Test updating product with invalid data"""
        invalid_data = {
            'name': '',  # Empty name
            'rate': -10.0  # Negative rate
        }
        
        response = client.put(f'/api/products/{sample_product.id}', 
                             json=invalid_data,
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Validation failed'
    
    def test_delete_product_success(self, client, admin_headers, sample_product):
        """Test deleting product as admin"""
        response = client.delete(f'/api/products/{sample_product.id}', 
                                headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Product deleted successfully'
    
    def test_delete_product_non_admin(self, client, auth_headers, sample_product):
        """Test deleting product as non-admin"""
        response = client.delete(f'/api/products/{sample_product.id}', 
                                headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Admin access required'
    
    def test_delete_product_not_found(self, client, admin_headers):
        """Test deleting non-existent product"""
        response = client.delete('/api/products/99999', headers=admin_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'Product not found'
    
    def test_delete_product_with_invoice_items(self, client, admin_headers, sample_product, sample_invoice_item):
        """Test deleting product that has invoice items"""
        # Ensure product has invoice items
        assert sample_invoice_item.product_id == sample_product.id
        
        response = client.delete(f'/api/products/{sample_product.id}', 
                                headers=admin_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Cannot delete product with associated invoice items' in data['error']
        assert 'invoice_item_count' in data
    
    def test_get_categories_success(self, client, auth_headers, sample_product):
        """Test getting all product categories"""
        response = client.get('/api/products/categories', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'categories' in data
        assert isinstance(data['categories'], list)
        assert sample_product.category in data['categories']
    
    def test_get_categories_no_auth(self, client):
        """Test getting categories without authentication"""
        response = client.get('/api/products/categories')
        
        assert response.status_code == 401
    
    def test_get_products_by_category_success(self, client, auth_headers, sample_product):
        """Test getting products by category"""
        response = client.get(f'/api/products/categories/{sample_product.category}', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'category' in data
        assert 'products' in data
        assert data['category'] == sample_product.category
        assert len(data['products']) >= 1
        assert data['products'][0]['category'] == sample_product.category
    
    def test_get_products_by_nonexistent_category(self, client, auth_headers):
        """Test getting products by non-existent category"""
        response = client.get('/api/products/categories/NonExistentCategory', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'products' in data
        assert len(data['products']) == 0
    
    def test_search_products_success(self, client, auth_headers, sample_product):
        """Test searching products"""
        response = client.get(f'/api/products/search?q={sample_product.name}', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'products' in data
        assert 'query' in data
        assert data['query'] == sample_product.name
        assert len(data['products']) >= 1
    
    def test_search_products_by_description(self, client, auth_headers, sample_product):
        """Test searching products by description"""
        if sample_product.description:
            response = client.get(f'/api/products/search?q={sample_product.description}', 
                                 headers=auth_headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'products' in data
            assert len(data['products']) >= 1
    
    def test_search_products_by_category(self, client, auth_headers, sample_product):
        """Test searching products by category"""
        response = client.get(f'/api/products/search?q={sample_product.category}', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'products' in data
        assert len(data['products']) >= 1
    
    def test_search_products_no_query(self, client, auth_headers):
        """Test searching products with no query"""
        response = client.get('/api/products/search', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'products' in data
        assert data['products'] == []
    
    def test_search_products_no_results(self, client, auth_headers):
        """Test searching products with no results"""
        response = client.get('/api/products/search?q=nonexistent', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'products' in data
        assert len(data['products']) == 0
    
    def test_validate_product_success(self, client, auth_headers, sample_product):
        """Test validating product data"""
        response = client.post(f'/api/products/{sample_product.id}/validate', 
                              headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'valid' in data
        assert 'errors' in data
        assert data['valid'] is True
        assert len(data['errors']) == 0
    
    def test_validate_product_with_errors(self, client, auth_headers, db_session):
        """Test validating product with validation errors"""
        # Create invalid product
        invalid_product = Product(
            name='',  # Empty name
            rate=-10.0,  # Negative rate
            unit=''  # Empty unit
        )
        db_session.add(invalid_product)
        db_session.commit()
        
        response = client.post(f'/api/products/{invalid_product.id}/validate', 
                              headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'valid' in data
        assert 'errors' in data
        assert data['valid'] is False
        assert len(data['errors']) > 0
    
    def test_get_product_stats_success(self, client, auth_headers, sample_product):
        """Test getting product statistics"""
        response = client.get('/api/products/stats', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_products' in data
        assert 'products_by_category' in data
        assert 'avg_rate_by_category' in data
        assert 'highest_rate_product' in data
        assert 'lowest_rate_product' in data
        assert isinstance(data['products_by_category'], list)
        assert isinstance(data['avg_rate_by_category'], list)
        assert data['total_products'] >= 1
    
    def test_bulk_update_products_success(self, client, admin_headers, sample_product):
        """Test bulk updating products as admin"""
        bulk_data = {
            'products': [
                {
                    'id': sample_product.id,
                    'name': 'Bulk Updated Product',
                    'rate': 250.00
                }
            ]
        }
        
        response = client.post('/api/products/bulk-update', 
                              json=bulk_data,
                              headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'updated_count' in data
        assert data['updated_count'] == 1
        assert 'Successfully updated' in data['message']
    
    def test_bulk_update_products_non_admin(self, client, auth_headers, sample_product):
        """Test bulk updating products as non-admin"""
        bulk_data = {
            'products': [
                {
                    'id': sample_product.id,
                    'name': 'Bulk Updated Product'
                }
            ]
        }
        
        response = client.post('/api/products/bulk-update', 
                              json=bulk_data,
                              headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Admin access required'
    
    def test_bulk_update_products_invalid_data(self, client, admin_headers):
        """Test bulk updating products with invalid data"""
        bulk_data = {
            'products': [
                {
                    'id': 99999,  # Non-existent product
                    'name': 'Updated Product'
                }
            ]
        }
        
        response = client.post('/api/products/bulk-update', 
                              json=bulk_data,
                              headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['updated_count'] == 0
        assert 'errors' in data
        assert len(data['errors']) > 0
    
    def test_export_products_success(self, client, auth_headers, sample_product):
        """Test exporting products to CSV"""
        response = client.get('/api/products/export', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'csv_data' in data
        assert 'filename' in data
        assert isinstance(data['csv_data'], list)
        assert len(data['csv_data']) >= 2  # Headers + at least one product
        
        # Check CSV headers
        expected_headers = ['ID', 'Category', 'Name', 'Description', 'Unit', 'Rate', 'HSN Code', 'Created At']
        assert data['csv_data'][0] == expected_headers
    
    def test_export_products_no_auth(self, client):
        """Test exporting products without authentication"""
        response = client.get('/api/products/export')
        
        assert response.status_code == 401
    
    def test_import_products_success(self, client, admin_headers):
        """Test importing products from CSV data"""
        csv_data = [
            ['ID', 'Category', 'Name', 'Description', 'Unit', 'Rate', 'HSN Code'],
            ['', 'Import Category', 'Import Product 1', 'Import Description 1', 'KG', '150.00', '1234'],
            ['', 'Import Category', 'Import Product 2', 'Import Description 2', 'PCS', '200.00', '5678']
        ]
        
        import_data = {
            'csv_data': csv_data
        }
        
        response = client.post('/api/products/import', 
                              json=import_data,
                              headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'imported_count' in data
        assert data['imported_count'] == 2
        assert 'Successfully imported' in data['message']
    
    def test_import_products_non_admin(self, client, auth_headers):
        """Test importing products as non-admin"""
        csv_data = [
            ['ID', 'Category', 'Name', 'Description', 'Unit', 'Rate', 'HSN Code'],
            ['', 'Import Category', 'Import Product', 'Import Description', 'KG', '150.00', '1234']
        ]
        
        import_data = {
            'csv_data': csv_data
        }
        
        response = client.post('/api/products/import', 
                              json=import_data,
                              headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Admin access required'
    
    def test_import_products_invalid_data(self, client, admin_headers):
        """Test importing products with invalid CSV data"""
        csv_data = [
            ['ID', 'Category', 'Name', 'Description', 'Unit', 'Rate', 'HSN Code'],
            ['', 'Import Category', '', 'Import Description', 'KG', '150.00', '1234']  # Empty name
        ]
        
        import_data = {
            'csv_data': csv_data
        }
        
        response = client.post('/api/products/import', 
                              json=import_data,
                              headers=admin_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['imported_count'] == 0
        assert 'errors' in data
        assert len(data['errors']) > 0
    
    def test_import_products_no_data(self, client, admin_headers):
        """Test importing products with no data"""
        response = client.post('/api/products/import', 
                              headers=admin_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'No CSV data provided'
    
    def test_product_full_crud_flow(self, client, auth_headers, sample_product_data):
        """Test complete CRUD flow for product"""
        # Create
        response = client.post('/api/products', 
                              json=sample_product_data,
                              headers=auth_headers)
        assert response.status_code == 201
        product_id = response.get_json()['product']['id']
        
        # Read
        response = client.get(f'/api/products/{product_id}', 
                             headers=auth_headers)
        assert response.status_code == 200
        
        # Update
        update_data = {'name': 'Updated Product Name', 'rate': 250.00}
        response = client.put(f'/api/products/{product_id}', 
                             json=update_data,
                             headers=auth_headers)
        assert response.status_code == 200
        
        # Search
        response = client.get('/api/products/search?q=Updated', 
                             headers=auth_headers)
        assert response.status_code == 200
        assert len(response.get_json()['products']) >= 1
        
        # Validate
        response = client.post(f'/api/products/{product_id}/validate', 
                              headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json()['valid'] is True
        
        # Get by category
        response = client.get(f'/api/products/categories/{sample_product_data["category"]}', 
                             headers=auth_headers)
        assert response.status_code == 200
        assert len(response.get_json()['products']) >= 1
    
    def test_product_advanced_features(self, client, auth_headers, db_session):
        """Test advanced product features"""
        # Create products in different categories
        products = [
            Product(name='Product A', category='Category A', rate=100.00),
            Product(name='Product B', category='Category B', rate=200.00),
            Product(name='Product C', category='Category A', rate=150.00)
        ]
        
        for product in products:
            db_session.add(product)
        db_session.commit()
        
        # Test category filtering
        response = client.get('/api/products?category=Category A', 
                             headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['products']) == 2
        
        # Test statistics
        response = client.get('/api/products/stats', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['total_products'] >= 3
        
        # Check category breakdown
        category_breakdown = data['products_by_category']
        category_a_count = next((item['count'] for item in category_breakdown if item['category'] == 'Category A'), 0)
        assert category_a_count == 2
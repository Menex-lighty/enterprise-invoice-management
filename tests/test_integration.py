"""
Integration Tests
Tests for complete workflows and integrations between different components
"""

import pytest
import json
from datetime import date, datetime
from models import User, Company, Customer, Product, Invoice, InvoiceItem
from conftest import create_test_invoice_with_items

class TestIntegrationWorkflows:
    """Integration test cases for complete workflows"""
    
    def test_complete_invoice_lifecycle(self, client, admin_headers, db_session):
        """Test complete invoice lifecycle from creation to completion"""
        # 1. Create a company
        company_data = {
            'name': 'Integration Test Company',
            'address': '123 Integration Street',
            'city': 'Test City',
            'state': 'Test State',
            'pincode': '123456',
            'gstin': '12INTEG3456F1Z5',
            'contact_phone': '9876543210',
            'email': 'integration@test.com'
        }
        
        response = client.post('/api/companies', json=company_data, headers=admin_headers)
        assert response.status_code == 201
        company_id = response.get_json()['company']['id']
        
        # 2. Create a customer
        customer_data = {
            'name': 'Integration Test Customer',
            'address': '456 Customer Street',
            'city': 'Customer City',
            'state': 'Customer State',
            'pincode': '654321',
            'gstin': '12CUSTM7890K1L2',
            'contact_person': 'John Customer',
            'phone': '9876543210',
            'email': 'customer@test.com'
        }
        
        response = client.post('/api/customers', json=customer_data, headers=admin_headers)
        assert response.status_code == 201
        customer_id = response.get_json()['customer']['id']
        
        # 3. Create products
        products_data = [
            {
                'category': 'Integration Category',
                'name': 'Integration Product 1',
                'description': 'First integration product',
                'unit': 'KG',
                'rate': 100.00,
                'hsn_code': '1234'
            },
            {
                'category': 'Integration Category',
                'name': 'Integration Product 2',
                'description': 'Second integration product',
                'unit': 'PCS',
                'rate': 200.00,
                'hsn_code': '5678'
            }
        ]
        
        product_ids = []
        for product_data in products_data:
            response = client.post('/api/products', json=product_data, headers=admin_headers)
            assert response.status_code == 201
            product_ids.append(response.get_json()['product']['id'])
        
        # 4. Create invoice
        invoice_data = {
            'invoice_date': date.today().isoformat(),
            'company_id': company_id,
            'customer_id': customer_id,
            'po_number': 'PO-INTEGRATION-123',
            'payment_mode': 'RTGS/NEFT',
            'transport': 'Road',
            'dispatch_from': 'Integration Warehouse'
        }
        
        response = client.post('/api/invoices', json=invoice_data, headers=admin_headers)
        assert response.status_code == 201
        invoice_id = response.get_json()['invoice']['id']
        
        # 5. Add items to invoice
        items_data = [
            {
                'product_id': product_ids[0],
                'description': 'Integration Product 1',
                'quantity': 10.0,
                'unit': 'KG',
                'rate': 100.00,
                'discount_percent': 5.0
            },
            {
                'product_id': product_ids[1],
                'description': 'Integration Product 2',
                'quantity': 5.0,
                'unit': 'PCS',
                'rate': 200.00,
                'discount_percent': 10.0
            }
        ]
        
        item_ids = []
        for item_data in items_data:
            response = client.post(f'/api/invoices/{invoice_id}/items', 
                                 json=item_data, headers=admin_headers)
            assert response.status_code == 201
            item_ids.append(response.get_json()['item']['id'])
        
        # 6. Calculate totals
        response = client.post(f'/api/invoices/{invoice_id}/calculate', headers=admin_headers)
        assert response.status_code == 200
        
        # 7. Update invoice status through workflow
        statuses = ['SENT', 'PAID']
        for status in statuses:
            response = client.put(f'/api/invoices/{invoice_id}/status', 
                                json={'status': status}, headers=admin_headers)
            assert response.status_code == 200
            assert response.get_json()['invoice']['status'] == status
        
        # 8. Verify final invoice state
        response = client.get(f'/api/invoices/{invoice_id}', headers=admin_headers)
        assert response.status_code == 200
        final_invoice = response.get_json()['invoice']
        
        assert final_invoice['status'] == 'PAID'
        assert len(final_invoice['items']) == 2
        assert final_invoice['subtotal'] is not None
        assert final_invoice['gst_amount'] is not None
        assert final_invoice['total_amount'] is not None
        
        # Verify calculations
        # Item 1: 10 * 100 * 0.95 = 950
        # Item 2: 5 * 200 * 0.90 = 900
        # Subtotal: 950 + 900 = 1850
        # GST: 1850 * 0.18 = 333
        # Total: 1850 + 333 = 2183
        
        expected_subtotal = 1850.0
        expected_gst = 333.0
        expected_total = 2183.0
        
        assert abs(final_invoice['subtotal'] - expected_subtotal) < 0.01
        assert abs(final_invoice['gst_amount'] - expected_gst) < 0.01
        assert abs(final_invoice['total_amount'] - expected_total) < 0.01
    
    def test_user_permissions_integration(self, client, db_session):
        """Test user permissions across different operations"""
        # Create admin user
        admin_user = User(
            username='admin_integration',
            email='admin@integration.com',
            password='adminpass123',
            is_admin=True
        )
        db_session.add(admin_user)
        
        # Create regular user
        regular_user = User(
            username='user_integration',
            email='user@integration.com',
            password='userpass123',
            is_admin=False
        )
        db_session.add(regular_user)
        db_session.commit()
        
        # Login as admin
        admin_response = client.post('/api/auth/login', json={
            'username': 'admin_integration',
            'password': 'adminpass123'
        })
        assert admin_response.status_code == 200
        admin_token = admin_response.get_json()['access_token']
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
        # Login as regular user
        user_response = client.post('/api/auth/login', json={
            'username': 'user_integration',
            'password': 'userpass123'
        })
        assert user_response.status_code == 200
        user_token = user_response.get_json()['access_token']
        user_headers = {'Authorization': f'Bearer {user_token}'}
        
        # Test admin can create company
        company_data = {'name': 'Permission Test Company'}
        response = client.post('/api/companies', json=company_data, headers=admin_headers)
        assert response.status_code == 201
        company_id = response.get_json()['company']['id']
        
        # Test regular user cannot create company
        response = client.post('/api/companies', json=company_data, headers=user_headers)
        assert response.status_code == 403
        
        # Test both can create customers
        customer_data = {'name': 'Permission Test Customer'}
        response = client.post('/api/customers', json=customer_data, headers=admin_headers)
        assert response.status_code == 201
        
        response = client.post('/api/customers', json=customer_data, headers=user_headers)
        assert response.status_code == 201
        
        # Test both can create products
        product_data = {'name': 'Permission Test Product'}
        response = client.post('/api/products', json=product_data, headers=admin_headers)
        assert response.status_code == 201
        
        response = client.post('/api/products', json=product_data, headers=user_headers)
        assert response.status_code == 201
        
        # Test both can create invoices
        invoice_data = {
            'invoice_date': date.today().isoformat(),
            'company_id': company_id,
            'customer_id': 1
        }
        response = client.post('/api/invoices', json=invoice_data, headers=admin_headers)
        assert response.status_code == 201
        admin_invoice_id = response.get_json()['invoice']['id']
        
        response = client.post('/api/invoices', json=invoice_data, headers=user_headers)
        assert response.status_code == 201
        user_invoice_id = response.get_json()['invoice']['id']
        
        # Test admin can delete, regular user cannot delete paid invoices
        # First, change invoice status to PAID
        response = client.put(f'/api/invoices/{admin_invoice_id}/status', 
                            json={'status': 'PAID'}, headers=admin_headers)
        assert response.status_code == 200
        
        response = client.put(f'/api/invoices/{user_invoice_id}/status', 
                            json={'status': 'PAID'}, headers=user_headers)
        assert response.status_code == 200
        
        # Regular user cannot delete paid invoice
        response = client.delete(f'/api/invoices/{user_invoice_id}', headers=user_headers)
        assert response.status_code == 403
        
        # Admin can delete paid invoice
        response = client.delete(f'/api/invoices/{admin_invoice_id}', headers=admin_headers)
        assert response.status_code == 200
    
    def test_invoice_duplication_integration(self, client, admin_headers, sample_company, sample_customer, sample_product):
        """Test invoice duplication with complex scenarios"""
        # Create original invoice with multiple items
        original_invoice_data = {
            'invoice_date': date.today().isoformat(),
            'company_id': sample_company.id,
            'customer_id': sample_customer.id,
            'po_number': 'PO-ORIGINAL-123',
            'payment_mode': 'RTGS/NEFT',
            'transport': 'Road',
            'items': [
                {
                    'product_id': sample_product.id,
                    'description': 'Original Item 1',
                    'quantity': 5.0,
                    'unit': 'KG',
                    'rate': 100.00,
                    'discount_percent': 10.0
                },
                {
                    'product_id': sample_product.id,
                    'description': 'Original Item 2',
                    'quantity': 3.0,
                    'unit': 'PCS',
                    'rate': 200.00,
                    'discount_percent': 5.0
                }
            ]
        }
        
        # Create original invoice
        response = client.post('/api/invoices', json=original_invoice_data, headers=admin_headers)
        assert response.status_code == 201
        original_invoice_id = response.get_json()['invoice']['id']
        original_invoice_number = response.get_json()['invoice']['invoice_number']
        
        # Update original invoice status
        response = client.put(f'/api/invoices/{original_invoice_id}/status', 
                            json={'status': 'SENT'}, headers=admin_headers)
        assert response.status_code == 200
        
        # Duplicate the invoice
        response = client.post(f'/api/invoices/duplicate/{original_invoice_id}', headers=admin_headers)
        assert response.status_code == 201
        duplicate_invoice = response.get_json()['invoice']
        
        # Verify duplicate properties
        assert duplicate_invoice['id'] != original_invoice_id
        assert duplicate_invoice['invoice_number'] != original_invoice_number
        assert duplicate_invoice['status'] == 'DRAFT'
        assert duplicate_invoice['customer_id'] == sample_customer.id
        assert duplicate_invoice['company_id'] == sample_company.id
        assert duplicate_invoice['po_number'] == 'PO-ORIGINAL-123'
        assert len(duplicate_invoice['items']) == 2
        
        # Verify item details are duplicated
        for item in duplicate_invoice['items']:
            assert item['invoice_id'] == duplicate_invoice['id']
            assert item['product_id'] == sample_product.id
            assert item['quantity'] in [5.0, 3.0]
            assert item['rate'] in [100.00, 200.00]
        
        # Modify duplicate invoice
        update_data = {
            'po_number': 'PO-DUPLICATE-456',
            'items': [
                {
                    'product_id': sample_product.id,
                    'description': 'Modified Item 1',
                    'quantity': 10.0,
                    'unit': 'KG',
                    'rate': 150.00,
                    'discount_percent': 15.0
                }
            ]
        }
        
        response = client.put(f'/api/invoices/{duplicate_invoice["id"]}', 
                            json=update_data, headers=admin_headers)
        assert response.status_code == 200
        modified_duplicate = response.get_json()['invoice']
        
        assert modified_duplicate['po_number'] == 'PO-DUPLICATE-456'
        assert len(modified_duplicate['items']) == 1
        assert modified_duplicate['items'][0]['description'] == 'Modified Item 1'
        
        # Verify original invoice is unchanged
        response = client.get(f'/api/invoices/{original_invoice_id}', headers=admin_headers)
        assert response.status_code == 200
        original_invoice = response.get_json()['invoice']
        
        assert original_invoice['po_number'] == 'PO-ORIGINAL-123'
        assert original_invoice['status'] == 'SENT'
        assert len(original_invoice['items']) == 2
    
    def test_search_and_filter_integration(self, client, admin_headers, db_session):
        """Test search and filter functionality across entities"""
        # Create test data with specific patterns
        test_data = {
            'companies': [
                {'name': 'Alpha Company', 'city': 'Mumbai', 'state': 'Maharashtra'},
                {'name': 'Beta Company', 'city': 'Delhi', 'state': 'Delhi'},
                {'name': 'Gamma Company', 'city': 'Bangalore', 'state': 'Karnataka'}
            ],
            'customers': [
                {'name': 'Alpha Customer', 'city': 'Mumbai', 'state': 'Maharashtra'},
                {'name': 'Beta Customer', 'city': 'Delhi', 'state': 'Delhi'},
                {'name': 'Gamma Customer', 'city': 'Bangalore', 'state': 'Karnataka'}
            ],
            'products': [
                {'name': 'Alpha Product', 'category': 'Electronics', 'rate': 100.00},
                {'name': 'Beta Product', 'category': 'Machinery', 'rate': 200.00},
                {'name': 'Gamma Product', 'category': 'Electronics', 'rate': 150.00}
            ]
        }
        
        # Create companies
        for company_data in test_data['companies']:
            response = client.post('/api/companies', json=company_data, headers=admin_headers)
            assert response.status_code == 201
        
        # Create customers
        for customer_data in test_data['customers']:
            response = client.post('/api/customers', json=customer_data, headers=admin_headers)
            assert response.status_code == 201
        
        # Create products
        for product_data in test_data['products']:
            response = client.post('/api/products', json=product_data, headers=admin_headers)
            assert response.status_code == 201
        
        # Test company search
        response = client.get('/api/companies/search?q=Alpha', headers=admin_headers)
        assert response.status_code == 200
        results = response.get_json()['companies']
        assert len(results) == 1
        assert results[0]['name'] == 'Alpha Company'
        
        # Test customer search by state
        response = client.get('/api/customers/search?q=Maharashtra', headers=admin_headers)
        assert response.status_code == 200
        results = response.get_json()['customers']
        assert len(results) == 1
        assert results[0]['state'] == 'Maharashtra'
        
        # Test product search by category
        response = client.get('/api/products/search?q=Electronics', headers=admin_headers)
        assert response.status_code == 200
        results = response.get_json()['products']
        assert len(results) == 2
        for product in results:
            assert product['category'] == 'Electronics'
        
        # Test product filter by category
        response = client.get('/api/products?category=Machinery', headers=admin_headers)
        assert response.status_code == 200
        results = response.get_json()['products']
        assert len(results) == 1
        assert results[0]['category'] == 'Machinery'
        
        # Test cross-entity search consistency
        search_term = 'Beta'
        
        # Search companies
        response = client.get(f'/api/companies/search?q={search_term}', headers=admin_headers)
        company_results = response.get_json()['companies']
        
        # Search customers
        response = client.get(f'/api/customers/search?q={search_term}', headers=admin_headers)
        customer_results = response.get_json()['customers']
        
        # Search products
        response = client.get(f'/api/products/search?q={search_term}', headers=admin_headers)
        product_results = response.get_json()['products']
        
        # Each should return exactly one result with 'Beta' in the name
        assert len(company_results) == 1
        assert len(customer_results) == 1
        assert len(product_results) == 1
        assert 'Beta' in company_results[0]['name']
        assert 'Beta' in customer_results[0]['name']
        assert 'Beta' in product_results[0]['name']
    
    def test_statistics_integration(self, client, admin_headers, db_session):
        """Test statistics across different entities"""
        # Create test data for statistics
        company = Company(name='Stats Company', state='Test State')
        db_session.add(company)
        
        customers = [
            Customer(name='Stats Customer 1', state='Test State'),
            Customer(name='Stats Customer 2', state='Test State'),
            Customer(name='Stats Customer 3', state='Other State')
        ]
        for customer in customers:
            db_session.add(customer)
        
        products = [
            Product(name='Stats Product 1', category='Category A', rate=100.00),
            Product(name='Stats Product 2', category='Category A', rate=200.00),
            Product(name='Stats Product 3', category='Category B', rate=150.00)
        ]
        for product in products:
            db_session.add(product)
        
        db_session.commit()
        
        # Create invoices with different statuses - Fix: Don't pass subtotal/gst_amount/total_amount to constructor
        for i, customer in enumerate(customers):
            invoice = Invoice(
                invoice_number=f'INV-STATS-{customer.id}',
                invoice_date=date.today(),
                company_id=company.id,
                customer_id=customer.id,
                status=['DRAFT', 'SENT', 'PAID'][i]
            )
            db_session.add(invoice)
            db_session.flush()
            
            # Add an item to calculate totals properly
            item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=products[0].id,
                description=f'Stats Item {i+1}',
                quantity=1.0,
                unit='KG',
                rate=1000.0,
                discount_percent=0
            )
            item.calculate_amount()
            db_session.add(item)
            
            # Let the invoice calculate its own totals
            invoice.calculate_totals()
        
        db_session.commit()
        
        # Test company statistics
        response = client.get('/api/companies/stats', headers=admin_headers)
        assert response.status_code == 200
        stats = response.get_json()
        assert stats['total_companies'] >= 1
        assert any(state['state'] == 'Test State' for state in stats['companies_by_state'])
        
        # Test customer statistics
        response = client.get('/api/customers/stats', headers=admin_headers)
        assert response.status_code == 200
        stats = response.get_json()
        assert stats['total_customers'] >= 3
        assert stats['customers_with_invoices'] >= 3
        assert any(state['state'] == 'Test State' for state in stats['customers_by_state'])
        assert len(stats['top_customers']) >= 3
        
        # Test product statistics
        response = client.get('/api/products/stats', headers=admin_headers)
        assert response.status_code == 200
        stats = response.get_json()
        assert stats['total_products'] >= 3
        assert any(cat['category'] == 'Category A' for cat in stats['products_by_category'])
        assert any(cat['category'] == 'Category B' for cat in stats['products_by_category'])
        
        # Test invoice statistics
        response = client.get('/api/invoices/stats', headers=admin_headers)
        assert response.status_code == 200
        stats = response.get_json()
        assert stats['total_invoices'] >= 3
        assert stats['status_breakdown']['draft'] >= 1
        assert stats['status_breakdown']['sent'] >= 1
        assert stats['status_breakdown']['paid'] >= 1
        assert stats['amounts']['total'] >= 3540.0  # 3 * 1180
        assert stats['amounts']['paid'] >= 1180.0
        assert stats['amounts']['pending'] >= 1180.0
    
    def test_error_handling_integration(self, client, admin_headers):
        """Test error handling across different operations"""
        # Test cascading errors
        
        # 1. Try to create invoice with non-existent customer
        invoice_data = {
            'invoice_date': date.today().isoformat(),
            'customer_id': 99999  # Non-existent
        }
        
        response = client.post('/api/invoices', json=invoice_data, headers=admin_headers)
        # Should succeed as foreign key constraint is not enforced in creation
        # But the invoice will have invalid references
        
        # 2. Try to add item with non-existent product
        if response.status_code == 201:
            invoice_id = response.get_json()['invoice']['id']
            item_data = {
                'product_id': 99999,  # Non-existent
                'description': 'Test item',
                'quantity': 1.0,
                'unit': 'KG',
                'rate': 100.00
            }
            
            response = client.post(f'/api/invoices/{invoice_id}/items', 
                                 json=item_data, headers=admin_headers)
            # Should succeed as foreign key constraint is not enforced in creation
        
        # 3. Test validation error cascading
        invalid_data = {
            'name': '',  # Invalid
            'email': 'invalid-email',  # Invalid
            'rate': -100.0  # Invalid for products
        }
        
        # Try to create company with invalid data
        response = client.post('/api/companies', json=invalid_data, headers=admin_headers)
        assert response.status_code == 400
        assert 'Validation failed' in response.get_json()['error']
        
        # Try to create customer with invalid data
        response = client.post('/api/customers', json=invalid_data, headers=admin_headers)
        assert response.status_code == 400
        assert 'Validation failed' in response.get_json()['error']
        
        # Try to create product with invalid data
        response = client.post('/api/products', json=invalid_data, headers=admin_headers)
        assert response.status_code == 400
        assert 'Validation failed' in response.get_json()['error']
        
        # 4. Test authentication error cascading
        no_auth_headers = {}
        
        # All protected endpoints should return 401
        endpoints = [
            '/api/companies',
            '/api/customers',
            '/api/products',
            '/api/invoices',
            '/api/companies/stats',
            '/api/customers/stats',
            '/api/products/stats',
            '/api/invoices/stats'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=no_auth_headers)
            assert response.status_code == 401
    
    def test_bulk_operations_integration(self, client, admin_headers):
        """Test bulk operations across different entities"""
        # Create multiple products for bulk operations
        products_data = [
            {'name': f'Bulk Product {i}', 'category': 'Bulk Category', 'rate': 100.0 + i}
            for i in range(5)
        ]
        
        product_ids = []
        for product_data in products_data:
            response = client.post('/api/products', json=product_data, headers=admin_headers)
            assert response.status_code == 201
            product_ids.append(response.get_json()['product']['id'])
        
        # Test bulk update
        bulk_update_data = {
            'products': [
                {'id': product_ids[0], 'rate': 150.0, 'category': 'Updated Category'},
                {'id': product_ids[1], 'rate': 160.0, 'category': 'Updated Category'},
                {'id': product_ids[2], 'rate': 170.0, 'category': 'Updated Category'}
            ]
        }
        
        response = client.post('/api/products/bulk-update', 
                              json=bulk_update_data, headers=admin_headers)
        assert response.status_code == 200
        result = response.get_json()
        assert result['updated_count'] == 3
        assert len(result['errors']) == 0
        
        # Verify updates
        for product_id in product_ids[:3]:
            response = client.get(f'/api/products/{product_id}', headers=admin_headers)
            assert response.status_code == 200
            product = response.get_json()['product']
            assert product['category'] == 'Updated Category'
            assert product['rate'] in [150.0, 160.0, 170.0]
        
        # Test bulk import
        csv_data = [
            ['ID', 'Category', 'Name', 'Description', 'Unit', 'Rate', 'HSN Code'],
            ['', 'Import Category', 'Import Product 1', 'Description 1', 'KG', '200.00', '1111'],
            ['', 'Import Category', 'Import Product 2', 'Description 2', 'PCS', '300.00', '2222'],
            ['', 'Import Category', 'Import Product 3', 'Description 3', 'LTR', '400.00', '3333']
        ]
        
        import_data = {'csv_data': csv_data}
        response = client.post('/api/products/import', 
                              json=import_data, headers=admin_headers)
        assert response.status_code == 200
        result = response.get_json()
        assert result['imported_count'] == 3
        assert len(result['errors']) == 0
        
        # Test export
        response = client.get('/api/products/export', headers=admin_headers)
        assert response.status_code == 200
        result = response.get_json()
        assert 'csv_data' in result
        assert len(result['csv_data']) > 1  # Headers + data
        
        # Verify imported products exist
        response = client.get('/api/products/search?q=Import Category', headers=admin_headers)
        assert response.status_code == 200
        search_results = response.get_json()['products']
        assert len(search_results) == 3
    
    def test_data_consistency_integration(self, client, admin_headers, db_session):
        """Test data consistency across operations"""
        # Create related entities
        company = Company(name='Consistency Company')
        customer = Customer(name='Consistency Customer')
        product = Product(name='Consistency Product', rate=100.0)
        
        db_session.add_all([company, customer, product])
        db_session.commit()
        
        # Create invoice with items
        invoice = Invoice(
            invoice_number='INV-CONSISTENCY-001',
            invoice_date=date.today(),
            company_id=company.id,
            customer_id=customer.id
        )
        db_session.add(invoice)
        db_session.flush()
        
        # Add items
        items = [
            InvoiceItem(
                invoice_id=invoice.id,
                product_id=product.id,
                description='Consistency Item 1',
                quantity=5.0,
                unit='KG',
                rate=100.0,
                discount_percent=10.0
            ),
            InvoiceItem(
                invoice_id=invoice.id,
                product_id=product.id,
                description='Consistency Item 2',
                quantity=3.0,
                unit='PCS',
                rate=150.0,
                discount_percent=5.0
            )
        ]
        
        for item in items:
            item.calculate_amount()
            db_session.add(item)
        
        invoice.calculate_totals()
        db_session.commit()
        
        # Test consistency through API
        response = client.get(f'/api/invoices/{invoice.id}', headers=admin_headers)
        assert response.status_code == 200
        api_invoice = response.get_json()['invoice']
        
        # Verify totals consistency
        api_subtotal = api_invoice['subtotal']
        api_gst = api_invoice['gst_amount']
        api_total = api_invoice['total_amount']
        
        # Manual calculation
        # Item 1: 5 * 100 * 0.9 = 450
        # Item 2: 3 * 150 * 0.95 = 427.5
        # Subtotal: 450 + 427.5 = 877.5
        # GST: 877.5 * 0.18 = 157.95
        # Total: 877.5 + 157.95 = 1035.45
        
        expected_subtotal = 877.5
        expected_gst = 157.95
        expected_total = 1035.45
        
        assert abs(api_subtotal - expected_subtotal) < 0.01
        assert abs(api_gst - expected_gst) < 0.01
        assert abs(api_total - expected_total) < 0.01
        
        # Test recalculation consistency
        response = client.post(f'/api/invoices/{invoice.id}/calculate', headers=admin_headers)
        assert response.status_code == 200
        recalc_invoice = response.get_json()['invoice']
        
        # Should match previous calculations
        assert abs(recalc_invoice['subtotal'] - api_subtotal) < 0.01
        assert abs(recalc_invoice['gst_amount'] - api_gst) < 0.01
        assert abs(recalc_invoice['total_amount'] - api_total) < 0.01
        
        # Test update consistency
        update_data = {
            'items': [
                {
                    'product_id': product.id,
                    'description': 'Updated Item',
                    'quantity': 10.0,
                    'unit': 'KG',
                    'rate': 200.0,
                    'discount_percent': 0.0
                }
            ]
        }
        
        response = client.put(f'/api/invoices/{invoice.id}', 
                            json=update_data, headers=admin_headers)
        assert response.status_code == 200
        updated_invoice = response.get_json()['invoice']
        
        # Verify new calculations
        # Item: 10 * 200 * 1.0 = 2000
        # GST: 2000 * 0.18 = 360
        # Total: 2000 + 360 = 2360
        
        assert abs(updated_invoice['subtotal'] - 2000.0) < 0.01
        assert abs(updated_invoice['gst_amount'] - 360.0) < 0.01
        assert abs(updated_invoice['total_amount'] - 2360.0) < 0.01
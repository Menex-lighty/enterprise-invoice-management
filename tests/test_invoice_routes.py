"""
Invoice Routes Tests
Tests for all invoice-related API endpoints
"""

import pytest
import json
from datetime import date, datetime
from models import Invoice, InvoiceItem

class TestInvoiceRoutes:
    """Test cases for invoice routes"""
    
    def test_get_invoices_success(self, client, auth_headers, sample_invoice):
        """Test getting all invoices"""
        response = client.get('/api/invoices', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'invoices' in data
        assert 'pagination' in data
        assert isinstance(data['invoices'], list)
        assert len(data['invoices']) >= 1
        assert data['invoices'][0]['invoice_number'] == sample_invoice.invoice_number
    
    def test_get_invoices_pagination(self, client, auth_headers, sample_invoice):
        """Test getting invoices with pagination"""
        response = client.get('/api/invoices?page=1&per_page=5', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'pagination' in data
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 5
        assert data['pagination']['total'] >= 0
    
    def test_get_invoices_with_filters(self, client, auth_headers, sample_invoice):
        """Test getting invoices with filters"""
        # Test status filter
        response = client.get('/api/invoices?status=DRAFT', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        for invoice in data['invoices']:
            assert invoice['status'] == 'DRAFT'
        
        # Test customer filter
        response = client.get(f'/api/invoices?customer_id={sample_invoice.customer_id}', 
                             headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        for invoice in data['invoices']:
            assert invoice['customer_id'] == sample_invoice.customer_id
        
        # Test date range filter
        today = date.today().isoformat()
        response = client.get(f'/api/invoices?date_from={today}&date_to={today}', 
                             headers=auth_headers)
        assert response.status_code == 200
    
    def test_get_invoices_no_auth(self, client):
        """Test getting invoices without authentication"""
        response = client.get('/api/invoices')
        
        assert response.status_code == 401
    
    def test_get_specific_invoice_success(self, client, auth_headers, sample_invoice):
        """Test getting specific invoice"""
        response = client.get(f'/api/invoices/{sample_invoice.id}', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'invoice' in data
        assert data['invoice']['id'] == sample_invoice.id
        assert data['invoice']['invoice_number'] == sample_invoice.invoice_number
    
    def test_get_specific_invoice_not_found(self, client, auth_headers):
        """Test getting non-existent invoice"""
        response = client.get('/api/invoices/99999', headers=auth_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'Invoice not found'
    
    def test_create_invoice_success(self, client, auth_headers, sample_company, sample_customer):
        """Test creating invoice"""
        invoice_data = {
            'invoice_number': 'INV-TEST-CREATE',
            'invoice_date': date.today().isoformat(),
            'company_id': sample_company.id,
            'customer_id': sample_customer.id,
            'po_number': 'PO-TEST-123',
            'payment_mode': 'RTGS/NEFT'
        }
        
        response = client.post('/api/invoices', 
                              json=invoice_data,
                              headers=auth_headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'Invoice created successfully'
        assert 'invoice' in data
        assert data['invoice']['invoice_number'] == invoice_data['invoice_number']
    
    def test_create_invoice_with_items(self, client, auth_headers, sample_company, sample_customer, sample_product):
        """Test creating invoice with items"""
        invoice_data = {
            'invoice_number': 'INV-TEST-ITEMS',
            'invoice_date': date.today().isoformat(),
            'company_id': sample_company.id,
            'customer_id': sample_customer.id,
            'items': [
                {
                    'product_id': sample_product.id,
                    'description': 'Test item 1',
                    'quantity': 5.0,
                    'unit': 'KG',
                    'rate': 100.00,
                    'discount_percent': 10.0
                },
                {
                    'product_id': sample_product.id,
                    'description': 'Test item 2',
                    'quantity': 3.0,
                    'unit': 'KG',
                    'rate': 150.00,
                    'discount_percent': 5.0
                }
            ]
        }
        
        response = client.post('/api/invoices', 
                              json=invoice_data,
                              headers=auth_headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'Invoice created successfully'
        assert 'invoice' in data
        assert len(data['invoice']['items']) == 2
        assert data['invoice']['subtotal'] is not None
        assert data['invoice']['total_amount'] is not None
    
    def test_create_invoice_auto_number(self, client, auth_headers, sample_customer):
        """Test creating invoice with auto-generated number"""
        invoice_data = {
            'invoice_date': date.today().isoformat(),
            'customer_id': sample_customer.id
        }
        
        response = client.post('/api/invoices', 
                              json=invoice_data,
                              headers=auth_headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'invoice' in data
        assert data['invoice']['invoice_number'] is not None
        assert 'INV-' in data['invoice']['invoice_number']
    
    def test_create_invoice_invalid_data(self, client, auth_headers):
        """Test creating invoice with invalid data"""
        invalid_data = {
            'invoice_number': '',  # Empty number
            'invoice_date': date.today().isoformat()
            # Missing customer_id
        }
        
        response = client.post('/api/invoices', 
                              json=invalid_data,
                              headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Validation failed'
        assert 'details' in data
    
    def test_update_invoice_success(self, client, auth_headers, sample_invoice):
        """Test updating invoice"""
        update_data = {
            'po_number': 'PO-UPDATED-123',
            'transport': 'Updated Transport',
            'payment_mode': 'NEFT'
        }
        
        response = client.put(f'/api/invoices/{sample_invoice.id}', 
                             json=update_data,
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Invoice updated successfully'
        assert data['invoice']['po_number'] == 'PO-UPDATED-123'
        assert data['invoice']['transport'] == 'Updated Transport'
    
    def test_update_invoice_with_items(self, client, auth_headers, sample_invoice, sample_product):
        """Test updating invoice with items"""
        update_data = {
            'po_number': 'PO-UPDATED-ITEMS',
            'items': [
                {
                    'product_id': sample_product.id,
                    'description': 'Updated item',
                    'quantity': 10.0,
                    'unit': 'KG',
                    'rate': 200.00,
                    'discount_percent': 15.0
                }
            ]
        }
        
        response = client.put(f'/api/invoices/{sample_invoice.id}', 
                             json=update_data,
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Invoice updated successfully'
        assert len(data['invoice']['items']) == 1
        assert data['invoice']['items'][0]['description'] == 'Updated item'
    
    def test_update_invoice_not_found(self, client, auth_headers):
        """Test updating non-existent invoice"""
        update_data = {
            'po_number': 'PO-UPDATED-123'
        }
        
        response = client.put('/api/invoices/99999', 
                             json=update_data,
                             headers=auth_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'Invoice not found'
    
    def test_update_invoice_permission_denied(self, client, auth_headers, db_session, sample_invoice):
        """Test updating invoice with wrong permissions"""
        # Change invoice status to PAID (only admin can edit)
        sample_invoice.status = 'PAID'
        db_session.commit()
        
        update_data = {
            'po_number': 'PO-UPDATED-123'
        }
        
        response = client.put(f'/api/invoices/{sample_invoice.id}', 
                             json=update_data,
                             headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Permission denied'
    
    def test_delete_invoice_success(self, client, auth_headers, sample_invoice):
        """Test deleting invoice"""
        response = client.delete(f'/api/invoices/{sample_invoice.id}', 
                                headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Invoice deleted successfully'
    
    def test_delete_invoice_permission_denied(self, client, auth_headers, db_session, sample_invoice):
        """Test deleting invoice with wrong permissions"""
        # Change invoice status to PAID (only admin can delete)
        sample_invoice.status = 'PAID'
        db_session.commit()
        
        response = client.delete(f'/api/invoices/{sample_invoice.id}', 
                                headers=auth_headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Permission denied'
    
    def test_get_invoice_items_success(self, client, auth_headers, sample_invoice, sample_invoice_item):
        """Test getting invoice items"""
        response = client.get(f'/api/invoices/{sample_invoice.id}/items', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data
        assert isinstance(data['items'], list)
        assert len(data['items']) >= 1
        assert data['items'][0]['invoice_id'] == sample_invoice.id
    
    def test_add_invoice_item_success(self, client, auth_headers, sample_invoice, sample_product):
        """Test adding item to invoice"""
        item_data = {
            'product_id': sample_product.id,
            'description': 'New test item',
            'quantity': 8.0,
            'unit': 'KG',
            'rate': 120.00,
            'discount_percent': 5.0
        }
        
        response = client.post(f'/api/invoices/{sample_invoice.id}/items', 
                              json=item_data,
                              headers=auth_headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'Item added successfully'
        assert 'item' in data
        assert 'invoice' in data
        assert data['item']['description'] == 'New test item'
    
    def test_add_invoice_item_invalid_data(self, client, auth_headers, sample_invoice):
        """Test adding invalid item to invoice"""
        invalid_item_data = {
            'description': '',  # Empty description
            'quantity': -5.0,  # Negative quantity
            'unit': 'KG',
            'rate': 120.00
        }
        
        response = client.post(f'/api/invoices/{sample_invoice.id}/items', 
                              json=invalid_item_data,
                              headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Validation failed'
    
    def test_update_invoice_item_success(self, client, auth_headers, sample_invoice, sample_invoice_item):
        """Test updating invoice item"""
        update_data = {
            'description': 'Updated item description',
            'quantity': 15.0,
            'rate': 180.00
        }
        
        response = client.put(f'/api/invoices/{sample_invoice.id}/items/{sample_invoice_item.id}', 
                             json=update_data,
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Item updated successfully'
        assert data['item']['description'] == 'Updated item description'
        assert data['item']['quantity'] == 15.0
    
    def test_update_invoice_item_not_found(self, client, auth_headers, sample_invoice):
        """Test updating non-existent invoice item"""
        update_data = {
            'description': 'Updated item description'
        }
        
        response = client.put(f'/api/invoices/{sample_invoice.id}/items/99999', 
                             json=update_data,
                             headers=auth_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'Item not found'
    
    def test_delete_invoice_item_success(self, client, auth_headers, sample_invoice, sample_invoice_item):
        """Test deleting invoice item"""
        response = client.delete(f'/api/invoices/{sample_invoice.id}/items/{sample_invoice_item.id}', 
                                headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Item deleted successfully'
        assert 'invoice' in data
    
    def test_calculate_invoice_totals(self, client, auth_headers, sample_invoice):
        """Test recalculating invoice totals"""
        response = client.post(f'/api/invoices/{sample_invoice.id}/calculate', 
                              headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Invoice totals calculated successfully'
        assert 'invoice' in data
        assert data['invoice']['subtotal'] is not None
        assert data['invoice']['gst_amount'] is not None
        assert data['invoice']['total_amount'] is not None
    
    def test_update_invoice_status_success(self, client, auth_headers, sample_invoice):
        """Test updating invoice status"""
        status_data = {
            'status': 'SENT'
        }
        
        response = client.put(f'/api/invoices/{sample_invoice.id}/status', 
                             json=status_data,
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Invoice status updated successfully'
        assert data['invoice']['status'] == 'SENT'
    
    def test_update_invoice_status_invalid(self, client, auth_headers, sample_invoice):
        """Test updating invoice with invalid status"""
        status_data = {
            'status': 'INVALID_STATUS'
        }
        
        response = client.put(f'/api/invoices/{sample_invoice.id}/status', 
                             json=status_data,
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Invalid status'
    
    def test_get_next_invoice_number(self, client, auth_headers):
        """Test getting next invoice number"""
        response = client.get('/api/invoices/next-number', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'next_invoice_number' in data
        assert 'INV-' in data['next_invoice_number']
    
    def test_get_invoice_stats_success(self, client, auth_headers, sample_invoice):
        """Test getting invoice statistics"""
        response = client.get('/api/invoices/stats', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_invoices' in data
        assert 'status_breakdown' in data
        assert 'amounts' in data
        assert 'monthly_stats' in data
        assert isinstance(data['status_breakdown'], dict)
        assert isinstance(data['amounts'], dict)
        assert isinstance(data['monthly_stats'], list)
        assert data['total_invoices'] >= 1
    
    def test_search_invoices_success(self, client, auth_headers, sample_invoice):
        """Test searching invoices"""
        response = client.get(f'/api/invoices/search?q={sample_invoice.invoice_number}', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'invoices' in data
        assert 'query' in data
        assert data['query'] == sample_invoice.invoice_number
        assert len(data['invoices']) >= 1
    
    def test_search_invoices_by_po_number(self, client, auth_headers, sample_invoice):
        """Test searching invoices by PO number"""
        if sample_invoice.po_number:
            response = client.get(f'/api/invoices/search?q={sample_invoice.po_number}', 
                                 headers=auth_headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'invoices' in data
            assert len(data['invoices']) >= 1
    
    def test_search_invoices_no_query(self, client, auth_headers):
        """Test searching invoices with no query"""
        response = client.get('/api/invoices/search', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'invoices' in data
        assert data['invoices'] == []
    
    def test_duplicate_invoice_success(self, client, auth_headers, sample_invoice, sample_invoice_item):
        """Test duplicating an invoice"""
        response = client.post(f'/api/invoices/duplicate/{sample_invoice.id}', 
                              headers=auth_headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'Invoice duplicated successfully'
        assert 'invoice' in data
        assert data['invoice']['invoice_number'] != sample_invoice.invoice_number
        assert data['invoice']['status'] == 'DRAFT'
        assert data['invoice']['customer_id'] == sample_invoice.customer_id
    
    def test_duplicate_invoice_not_found(self, client, auth_headers):
        """Test duplicating non-existent invoice"""
        response = client.post('/api/invoices/duplicate/99999', 
                              headers=auth_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'Invoice not found'
    
    def test_invoice_complete_workflow(self, client, auth_headers, sample_company, sample_customer, sample_product):
        """Test complete invoice workflow"""
        # 1. Create invoice
        invoice_data = {
            'invoice_date': date.today().isoformat(),
            'company_id': sample_company.id,
            'customer_id': sample_customer.id,
            'po_number': 'PO-WORKFLOW-123'
        }
        
        response = client.post('/api/invoices', 
                              json=invoice_data,
                              headers=auth_headers)
        assert response.status_code == 201
        invoice_id = response.get_json()['invoice']['id']
        
        # 2. Add items
        item_data = {
            'product_id': sample_product.id,
            'description': 'Workflow item',
            'quantity': 5.0,
            'unit': 'KG',
            'rate': 100.00,
            'discount_percent': 10.0
        }
        
        response = client.post(f'/api/invoices/{invoice_id}/items', 
                              json=item_data,
                              headers=auth_headers)
        assert response.status_code == 201
        item_id = response.get_json()['item']['id']
        
        # 3. Calculate totals
        response = client.post(f'/api/invoices/{invoice_id}/calculate', 
                              headers=auth_headers)
        assert response.status_code == 200
        
        # 4. Update status
        status_data = {'status': 'SENT'}
        response = client.put(f'/api/invoices/{invoice_id}/status', 
                             json=status_data,
                             headers=auth_headers)
        assert response.status_code == 200
        
        # 5. Verify final state
        response = client.get(f'/api/invoices/{invoice_id}', 
                             headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['invoice']['status'] == 'SENT'
        assert len(data['invoice']['items']) == 1
        assert data['invoice']['total_amount'] is not None
    
    def test_invoice_permissions_admin_vs_user(self, client, auth_headers, admin_headers, db_session, sample_invoice):
        """Test invoice permissions for admin vs regular user"""
        # Change invoice status to PAID
        sample_invoice.status = 'PAID'
        db_session.commit()
        
        # Regular user should not be able to edit PAID invoice
        update_data = {'po_number': 'PO-PERMISSION-TEST'}
        response = client.put(f'/api/invoices/{sample_invoice.id}', 
                             json=update_data,
                             headers=auth_headers)
        assert response.status_code == 403
        
        # Admin should be able to edit PAID invoice
        response = client.put(f'/api/invoices/{sample_invoice.id}', 
                             json=update_data,
                             headers=admin_headers)
        assert response.status_code == 200
        
        # Regular user should not be able to delete PAID invoice
        response = client.delete(f'/api/invoices/{sample_invoice.id}', 
                                headers=auth_headers)
        assert response.status_code == 403
        
        # Admin should be able to delete PAID invoice
        response = client.delete(f'/api/invoices/{sample_invoice.id}', 
                                headers=admin_headers)
        assert response.status_code == 200
    
    def test_invoice_error_handling(self, client, auth_headers, sample_customer):
        """Test invoice error handling"""
        # Test with invalid invoice ID format
        response = client.get('/api/invoices/invalid_id', headers=auth_headers)
        assert response.status_code == 404
        
        # First create an invoice to test update
        invoice_data = {
            'invoice_date': date.today().isoformat(),
            'customer_id': sample_customer.id
        }
        create_response = client.post('/api/invoices', json=invoice_data, headers=auth_headers)
        assert create_response.status_code == 201
        invoice_id = create_response.get_json()['invoice']['id']
        
        # Test update with no data
        response = client.put(f'/api/invoices/{invoice_id}', headers=auth_headers)
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'No data provided'
        
        # Test status update with no data
        response = client.put(f'/api/invoices/{invoice_id}/status', headers=auth_headers)
        assert response.status_code == 400
        
        # Test adding item with no data
        response = client.post(f'/api/invoices/{invoice_id}/items', headers=auth_headers)
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'No data provided'
        
        # Test status update with no data
        response = client.put('/api/invoices/1/status', headers=auth_headers)
        assert response.status_code == 400
        
        # Test adding item with no data
        response = client.post('/api/invoices/1/items', headers=auth_headers)
        assert response.status_code == 400
    
    def test_invoice_date_handling(self, client, auth_headers, sample_customer):
        """Test invoice date handling"""
        # Test with string date
        invoice_data = {
            'invoice_date': '2025-01-15',
            'customer_id': sample_customer.id
        }
        
        response = client.post('/api/invoices',
                              json=invoice_data,
                              headers=auth_headers)
        assert response.status_code == 201
        
        # Test with invalid date format
        invoice_data = {
            'invoice_date': 'invalid-date',
            'customer_id': sample_customer.id
        }
        
        response = client.post('/api/invoices',
                              json=invoice_data,
                              headers=auth_headers)
        assert response.status_code == 400  # Should fail with date parsing error
        data = response.get_json()
        assert 'Invalid date format' in data['error']
    
    def test_invoice_complex_calculations(self, client, auth_headers, sample_invoice, sample_product):
        """Test complex invoice calculations with multiple items"""
        # Add multiple items with different rates and discounts
        items = [
            {
                'product_id': sample_product.id,
                'description': 'Item 1',
                'quantity': 10.0,
                'unit': 'KG',
                'rate': 100.00,
                'discount_percent': 5.0
            },
            {
                'product_id': sample_product.id,
                'description': 'Item 2',
                'quantity': 5.0,
                'unit': 'PCS',
                'rate': 200.00,
                'discount_percent': 10.0
            },
            {
                'product_id': sample_product.id,
                'description': 'Item 3',
                'quantity': 3.0,
                'unit': 'KG',
                'rate': 150.00,
                'discount_percent': 0.0
            }
        ]
        
        # Update invoice with multiple items
        update_data = {'items': items}
        response = client.put(f'/api/invoices/{sample_invoice.id}', 
                             json=update_data,
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        invoice = data['invoice']
        
        # Verify calculations
        # Item 1: 10 * 100 * 0.95 = 950
        # Item 2: 5 * 200 * 0.90 = 900
        # Item 3: 3 * 150 * 1.00 = 450
        # Subtotal: 950 + 900 + 450 = 2300
        # GST: 2300 * 0.18 = 414
        # Total: 2300 + 414 = 2714
        
        expected_subtotal = 2300.0
        expected_gst = 414.0
        expected_total = 2714.0
        
        assert abs(invoice['subtotal'] - expected_subtotal) < 0.01
        assert abs(invoice['gst_amount'] - expected_gst) < 0.01
        assert abs(invoice['total_amount'] - expected_total) < 0.01
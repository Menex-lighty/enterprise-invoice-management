"""
Test Configuration and Fixtures
Pytest configuration for the invoice management system tests
"""

import pytest
import os
import tempfile
from datetime import datetime, date
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# Import your app components
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app
from database import db  # Import db from database module
from models import User, Company, Customer, Product, Invoice, InvoiceItem  # Import models separately

@pytest.fixture
def app():
    """Create and configure a test Flask app"""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Configure the app for testing
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False
    })
    
    # Create the database tables
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test runner"""
    return app.test_cli_runner()

@pytest.fixture
def db_session(app):
    """Create a database session for testing"""
    with app.app_context():
        yield db.session

@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing"""
    user = User(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def sample_admin(db_session):
    """Create a sample admin user for testing"""
    admin = User(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        first_name='Admin',
        last_name='User',
        is_admin=True
    )
    db_session.add(admin)
    db_session.commit()
    return admin

@pytest.fixture
def sample_company(db_session):
    """Create a sample company for testing"""
    company = Company(
        name='Test Company',
        address='123 Test Street',
        city='Test City',
        state='Test State',
        pincode='123456',
        gstin='12ABCDE3456F1Z5',
        contact_phone='9876543210',
        email='company@test.com',
        bank_name='Test Bank',
        account_number='1234567890',
        ifsc_code='TEST0123456'
    )
    db_session.add(company)
    db_session.commit()
    return company

@pytest.fixture
def sample_customer(db_session):
    """Create a sample customer for testing"""
    customer = Customer(
        name='Test Customer',
        address='456 Customer Street',
        city='Customer City',
        state='Customer State',
        pincode='654321',
        gstin='12FGHIJ7890K1L2',
        contact_person='John Doe',
        phone='9876543210',
        email='customer@test.com'
    )
    db_session.add(customer)
    db_session.commit()
    return customer

@pytest.fixture
def sample_product(db_session):
    """Create a sample product for testing"""
    product = Product(
        category='Test Category',
        name='Test Product',
        description='Test product description',
        unit='KG',
        rate=100.00,
        hsn_code='1234'
    )
    db_session.add(product)
    db_session.commit()
    return product

@pytest.fixture
def sample_invoice(db_session, sample_company, sample_customer):
    """Create a sample invoice for testing"""
    invoice = Invoice(
        invoice_number='INV-2025-01-0001',
        invoice_date=date.today(),
        company_id=sample_company.id,
        customer_id=sample_customer.id,
        po_number='PO-123',
        po_date=date.today(),
        payment_mode='RTGS/NEFT',
        transport='Road',
        dispatch_from='Test Location'
    )
    db_session.add(invoice)
    db_session.commit()
    return invoice

@pytest.fixture
def sample_invoice_item(db_session, sample_invoice, sample_product):
    """Create a sample invoice item for testing"""
    item = InvoiceItem(
        invoice_id=sample_invoice.id,
        product_id=sample_product.id,
        description='Test item',
        quantity=5.0,
        unit='KG',
        rate=100.00,
        discount_percent=10.0
    )
    item.calculate_amount()
    db_session.add(item)
    db_session.commit()
    return item

@pytest.fixture
def auth_headers(client, sample_user):
    """Create authentication headers for testing"""
    # Login to get token
    response = client.post('/api/auth/login', json={
        'username': sample_user.username,
        'password': 'testpass123'
    })
    
    assert response.status_code == 200
    token = response.json['access_token']
    
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def admin_headers(client, sample_admin):
    """Create admin authentication headers for testing"""
    # Login to get token
    response = client.post('/api/auth/login', json={
        'username': sample_admin.username,
        'password': 'adminpass123'
    })
    
    assert response.status_code == 200
    token = response.json['access_token']
    
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def sample_invoice_data():
    """Sample invoice data for testing"""
    return {
        'invoice_number': 'INV-2025-01-TEST',
        'invoice_date': date.today().isoformat(),
        'po_number': 'PO-TEST-123',
        'po_date': date.today().isoformat(),
        'payment_mode': 'RTGS/NEFT',
        'transport': 'Road',
        'dispatch_from': 'Test Location'
    }

@pytest.fixture
def sample_company_data():
    """Sample company data for testing"""
    return {
        'name': 'New Test Company',
        'address': '789 New Street',
        'city': 'New City',
        'state': 'New State',
        'pincode': '789012',
        'gstin': '12NEWCO7890N1M2',
        'contact_phone': '9876543210',
        'email': 'newcompany@test.com',
        'bank_name': 'New Bank',
        'account_number': '0987654321',
        'ifsc_code': 'NEWB0123456'
    }

@pytest.fixture
def sample_customer_data():
    """Sample customer data for testing"""
    return {
        'name': 'New Test Customer',
        'address': '789 New Customer Street',
        'city': 'New Customer City',
        'state': 'New Customer State',
        'pincode': '789012',
        'gstin': '12NEWCU7890N1M2',
        'contact_person': 'Jane Doe',
        'phone': '9876543210',
        'email': 'newcustomer@test.com'
    }

@pytest.fixture
def sample_product_data():
    """Sample product data for testing"""
    return {
        'category': 'New Category',
        'name': 'New Test Product',
        'description': 'New test product description',
        'unit': 'PCS',
        'rate': 150.00,
        'hsn_code': '5678'
    }

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        'username': 'newuser',
        'email': 'newuser@test.com',
        'password': 'newpass123',
        'first_name': 'New',
        'last_name': 'User'
    }

# Helper functions for tests
def create_test_invoice_with_items(db_session, company, customer, product, num_items=3):
    """Helper to create invoice with multiple items"""
    invoice = Invoice(
        invoice_number='INV-TEST-MULTI',
        invoice_date=date.today(),
        company_id=company.id,
        customer_id=customer.id,
        po_number='PO-MULTI-123',
        payment_mode='RTGS/NEFT'
    )
    db_session.add(invoice)
    db_session.flush()
    
    for i in range(num_items):
        item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=product.id,
            description=f'Test item {i+1}',
            quantity=float(i+1),
            unit='KG',
            rate=100.00,
            discount_percent=5.0
        )
        item.calculate_amount()
        db_session.add(item)
    
    invoice.calculate_totals()
    db_session.commit()
    return invoice
"""
Model Tests
Tests for all database models in the invoice management system
"""

import pytest
from datetime import date, datetime
from models import User, Company, Customer, Product, Invoice, InvoiceItem

class TestUser:
    """Test cases for User model"""
    
    def test_user_creation(self, db_session):
        """Test creating a new user"""
        user = User(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.password_hash is not None
        assert user.is_admin is False
        assert user.is_active is True
    
    def test_user_password_hashing(self, db_session):
        """Test password hashing and verification"""
        user = User(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Password should be hashed
        assert user.password_hash != 'testpass123'
        
        # Should be able to verify correct password
        assert user.check_password('testpass123') is True
        
        # Should not verify incorrect password
        assert user.check_password('wrongpass') is False
    
    def test_user_validation(self, db_session):
        """Test user validation"""
        # Valid user
        user = User(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        errors = user.validate()
        assert len(errors) == 0
        
        # Invalid user - no username
        user = User(
            username='',
            email='test@example.com',
            password='testpass123'
        )
        errors = user.validate()
        assert 'Username is required' in errors
        
        # Invalid user - no email
        user = User(
            username='testuser',
            email='',
            password='testpass123'
        )
        errors = user.validate()
        assert 'Email is required' in errors
        
        # Invalid user - invalid email
        user = User(
            username='testuser',
            email='invalid-email',
            password='testpass123'
        )
        errors = user.validate()
        assert 'Invalid email format' in errors
    
    def test_user_full_name(self, db_session):
        """Test get_full_name method"""
        user = User(
            username='testuser',
            email='test@example.com',
            first_name='John',
            last_name='Doe'
        )
        assert user.get_full_name() == 'John Doe'
        
        user.last_name = None
        assert user.get_full_name() == 'John'
        
        user.first_name = None
        user.last_name = 'Doe'
        assert user.get_full_name() == 'Doe'
        
        user.first_name = None
        user.last_name = None
        assert user.get_full_name() == 'testuser'
    
    def test_user_authentication(self, db_session):
        """Test user authentication"""
        user = User(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        db_session.add(user)
        db_session.commit()
        
        # Should authenticate with correct credentials
        authenticated_user = User.authenticate('testuser', 'testpass123')
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        
        # Should not authenticate with wrong password
        authenticated_user = User.authenticate('testuser', 'wrongpass')
        assert authenticated_user is None
        
        # Should not authenticate with wrong username
        authenticated_user = User.authenticate('wronguser', 'testpass123')
        assert authenticated_user is None
    
    def test_user_to_dict(self, db_session):
        """Test user serialization"""
        user = User(
            username='testuser',
            email='test@example.com',
            first_name='John',
            last_name='Doe'
        )
        
        user_dict = user.to_dict()
        assert user_dict['username'] == 'testuser'
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['first_name'] == 'John'
        assert user_dict['last_name'] == 'Doe'
        assert 'password_hash' not in user_dict


class TestCompany:
    """Test cases for Company model"""
    
    def test_company_creation(self, db_session):
        """Test creating a new company"""
        company = Company(
            name='Test Company',
            address='123 Test Street',
            city='Test City',
            state='Test State',
            pincode='123456',
            gstin='12ABCDE3456F1Z5'
        )
        db_session.add(company)
        db_session.commit()
        
        assert company.id is not None
        assert company.name == 'Test Company'
        assert company.address == '123 Test Street'
        assert company.gstin == '12ABCDE3456F1Z5'
    
    def test_company_validation(self, db_session):
        """Test company validation"""
        # Valid company
        company = Company(name='Test Company')
        errors = company.validate()
        assert len(errors) == 0
        
        # Invalid company - no name
        company = Company(name='')
        errors = company.validate()
        assert 'Company name is required' in errors
        
        # Invalid company - invalid email
        company = Company(name='Test Company', email='invalid-email')
        errors = company.validate()
        assert 'Invalid email format' in errors
        
        # Invalid company - invalid GSTIN length
        company = Company(name='Test Company', gstin='123')
        errors = company.validate()
        assert 'GSTIN must be 15 characters' in errors
        
        # Invalid company - non-numeric pincode
        company = Company(name='Test Company', pincode='abc123')
        errors = company.validate()
        assert 'Pincode must be numeric' in errors
    
    def test_company_full_address(self, db_session):
        """Test get_full_address method"""
        company = Company(
            name='Test Company',
            address='123 Test Street',
            city='Test City',
            state='Test State',
            pincode='123456'
        )
        
        full_address = company.get_full_address()
        assert full_address == '123 Test Street, Test City, Test State, 123456'
        
        # Test with missing components
        company.city = None
        full_address = company.get_full_address()
        assert full_address == '123 Test Street, Test State, 123456'
    
    def test_company_to_dict(self, db_session):
        """Test company serialization"""
        company = Company(
            name='Test Company',
            address='123 Test Street',
            gstin='12ABCDE3456F1Z5'
        )
        
        company_dict = company.to_dict()
        assert company_dict['name'] == 'Test Company'
        assert company_dict['address'] == '123 Test Street'
        assert company_dict['gstin'] == '12ABCDE3456F1Z5'


class TestCustomer:
    """Test cases for Customer model"""
    
    def test_customer_creation(self, db_session):
        """Test creating a new customer"""
        customer = Customer(
            name='Test Customer',
            address='456 Customer Street',
            city='Customer City',
            contact_person='John Doe',
            phone='9876543210'
        )
        db_session.add(customer)
        db_session.commit()
        
        assert customer.id is not None
        assert customer.name == 'Test Customer'
        assert customer.contact_person == 'John Doe'
        assert customer.phone == '9876543210'
    
    def test_customer_validation(self, db_session):
        """Test customer validation"""
        # Valid customer
        customer = Customer(name='Test Customer')
        errors = customer.validate()
        assert len(errors) == 0
        
        # Invalid customer - no name
        customer = Customer(name='')
        errors = customer.validate()
        assert 'Customer name is required' in errors
        
        # Invalid customer - invalid phone
        customer = Customer(name='Test Customer', phone='invalid-phone')
        errors = customer.validate()
        assert 'Invalid phone number format' in errors
    
    def test_customer_display_name(self, db_session):
        """Test get_display_name method"""
        customer = Customer(name='Test Customer')
        assert customer.get_display_name() == 'Test Customer'
        
        customer.contact_person = 'John Doe'
        assert customer.get_display_name() == 'Test Customer (Attn: John Doe)'
    
    def test_customer_to_dict(self, db_session):
        """Test customer serialization"""
        customer = Customer(
            name='Test Customer',
            contact_person='John Doe',
            phone='9876543210'
        )
        
        customer_dict = customer.to_dict()
        assert customer_dict['name'] == 'Test Customer'
        assert customer_dict['contact_person'] == 'John Doe'
        assert customer_dict['phone'] == '9876543210'


class TestProduct:
    """Test cases for Product model"""
    
    def test_product_creation(self, db_session):
        """Test creating a new product"""
        product = Product(
            category='Test Category',
            name='Test Product',
            description='Test description',
            unit='KG',
            rate=100.00,
            hsn_code='1234'
        )
        db_session.add(product)
        db_session.commit()
        
        assert product.id is not None
        assert product.name == 'Test Product'
        assert product.category == 'Test Category'
        assert float(product.rate) == 100.00
        assert product.unit == 'KG'
    
    def test_product_validation(self, db_session):
        """Test product validation"""
        # Valid product
        product = Product(name='Test Product')
        errors = product.validate()
        assert len(errors) == 0
        
        # Invalid product - no name
        product = Product(name='')
        errors = product.validate()
        assert 'Product name is required' in errors
        
        # Invalid product - negative rate
        product = Product(name='Test Product', rate=-10.00)
        errors = product.validate()
        assert 'Rate cannot be negative' in errors
        
        # Invalid product - no unit
        product = Product(name='Test Product', unit='')
        errors = product.validate()
        assert 'Unit is required' in errors
    
    def test_product_display_name(self, db_session):
        """Test get_display_name method"""
        product = Product(name='Test Product')
        assert product.get_display_name() == 'Test Product'
        
        product.category = 'Test Category'
        assert product.get_display_name() == 'Test Category - Test Product'
    
    def test_product_formatted_rate(self, db_session):
        """Test get_formatted_rate method"""
        product = Product(name='Test Product', rate=100.00, unit='KG')
        assert product.get_formatted_rate() == '₹100.00 per KG'
        
        product.rate = None
        assert product.get_formatted_rate() == 'Rate not set'
    
    def test_product_calculate_amount(self, db_session):
        """Test calculate_amount method"""
        product = Product(name='Test Product', rate=100.00)
        
        # Without discount
        amount = product.calculate_amount(5, 0)
        assert amount == 500.00
        
        # With discount
        amount = product.calculate_amount(5, 10)
        assert amount == 450.00
        
        # No rate
        product.rate = None
        amount = product.calculate_amount(5, 0)
        assert amount == 0


class TestInvoice:
    """Test cases for Invoice model"""
    
    def test_invoice_creation(self, db_session, sample_company, sample_customer):
        """Test creating a new invoice"""
        invoice = Invoice(
            invoice_number='INV-2025-01-0001',
            invoice_date=date.today(),
            company_id=sample_company.id,
            customer_id=sample_customer.id,
            po_number='PO-123'
        )
        db_session.add(invoice)
        db_session.commit()
        
        assert invoice.id is not None
        assert invoice.invoice_number == 'INV-2025-01-0001'
        assert invoice.company_id == sample_company.id
        assert invoice.customer_id == sample_customer.id
        assert invoice.status == 'DRAFT'
    
    def test_invoice_validation(self, db_session):
        """Test invoice validation"""
        # Valid invoice
        invoice = Invoice(
            invoice_number='INV-2025-01-0001',
            invoice_date=date.today(),
            customer_id=1
        )
        errors = invoice.validate()
        assert len(errors) == 0
        
        # Invalid invoice - no invoice number
        invoice = Invoice(
            invoice_number='',
            invoice_date=date.today(),
            customer_id=1
        )
        errors = invoice.validate()
        assert 'Invoice number is required' in errors
        
        # Invalid invoice - no customer
        invoice = Invoice(
            invoice_number='INV-2025-01-0001',
            invoice_date=date.today()
        )
        errors = invoice.validate()
        assert 'Customer is required' in errors
    
    def test_invoice_number_generation(self, db_session):
        """Test invoice number generation"""
        invoice_number = Invoice.generate_invoice_number()
        assert 'INV-' in invoice_number
        assert str(datetime.now().year) in invoice_number
    
    def test_invoice_calculate_totals(self, db_session, sample_invoice, sample_invoice_item):
        """Test invoice total calculations"""
        # Ensure we have a clean state - clear any existing items
        sample_invoice.items = []
        
        # Add the single test item
        sample_invoice.items.append(sample_invoice_item)
        
        # Calculate totals
        sample_invoice.calculate_totals()
        
        # Item amount should be 450.00 (5 * 100 - 10% discount)
        assert float(sample_invoice_item.amount) == 450.00
        
        # Subtotal should be 450.00 (only one item)
        assert float(sample_invoice.subtotal) == 450.00
        
        # GST should be 18% of subtotal
        assert float(sample_invoice.gst_amount) == 81.00
        
        # Total should be subtotal + GST
        assert float(sample_invoice.total_amount) == 531.00
    
    def test_invoice_to_dict(self, db_session, sample_invoice):
        """Test invoice serialization"""
        invoice_dict = sample_invoice.to_dict()
        
        assert invoice_dict['invoice_number'] == sample_invoice.invoice_number
        assert invoice_dict['status'] == sample_invoice.status
        assert invoice_dict['company_id'] == sample_invoice.company_id
        assert invoice_dict['customer_id'] == sample_invoice.customer_id
        assert 'items' in invoice_dict


class TestInvoiceItem:
    """Test cases for InvoiceItem model"""
    
    def test_invoice_item_creation(self, db_session, sample_invoice, sample_product):
        """Test creating a new invoice item"""
        item = InvoiceItem(
            invoice_id=sample_invoice.id,
            product_id=sample_product.id,
            description='Test item',
            quantity=5.0,
            unit='KG',
            rate=100.00,
            discount_percent=10.0
        )
        db_session.add(item)
        db_session.commit()
        
        assert item.id is not None
        assert item.invoice_id == sample_invoice.id
        assert item.product_id == sample_product.id
        assert item.description == 'Test item'
        assert float(item.quantity) == 5.0
        assert float(item.rate) == 100.00
    
    def test_invoice_item_validation(self, db_session):
        """Test invoice item validation"""
        # Valid item
        item = InvoiceItem(
            invoice_id=1,
            description='Test item',
            quantity=5.0,
            unit='KG',
            rate=100.00
        )
        errors = item.validate()
        assert len(errors) == 0
        
        # Invalid item - no description
        item = InvoiceItem(
            invoice_id=1,
            description='',
            quantity=5.0,
            unit='KG',
            rate=100.00
        )
        errors = item.validate()
        assert 'Item description is required' in errors
        
        # Invalid item - negative quantity
        item = InvoiceItem(
            invoice_id=1,
            description='Test item',
            quantity=-5.0,
            unit='KG',
            rate=100.00
        )
        errors = item.validate()
        assert 'Quantity must be greater than 0' in errors
        
        # Invalid item - invalid discount
        item = InvoiceItem(
            invoice_id=1,
            description='Test item',
            quantity=5.0,
            unit='KG',
            rate=100.00,
            discount_percent=150.0
        )
        errors = item.validate()
        assert 'Discount percent must be between 0 and 100' in errors
    
    def test_invoice_item_calculate_amount(self, db_session):
        """Test amount calculation"""
        item = InvoiceItem(
            invoice_id=1,
            description='Test item',
            quantity=5.0,
            unit='KG',
            rate=100.00,
            discount_percent=10.0
        )
        
        # Calculate amount
        amount = item.calculate_amount()
        assert amount == 450.00  # 5 * 100 - 10% discount
        assert float(item.amount) == 450.00
        
        # No discount
        item.discount_percent = 0
        amount = item.calculate_amount()
        assert amount == 500.00
        
        # No rate
        item.rate = None
        amount = item.calculate_amount()
        assert amount == 0
    
    def test_invoice_item_formatted_amount(self, db_session):
        """Test formatted amount display"""
        item = InvoiceItem(
            invoice_id=1,
            description='Test item',
            quantity=5.0,
            unit='KG',
            rate=100.00
        )
        item.calculate_amount()
        
        formatted = item.get_formatted_amount()
        assert formatted == '₹500.00'
        
        item.amount = None
        formatted = item.get_formatted_amount()
        assert formatted == '₹0.00'
    
    def test_invoice_item_to_dict(self, db_session, sample_invoice_item):
        """Test invoice item serialization"""
        item_dict = sample_invoice_item.to_dict()
        
        assert item_dict['invoice_id'] == sample_invoice_item.invoice_id
        assert item_dict['product_id'] == sample_invoice_item.product_id
        assert item_dict['description'] == sample_invoice_item.description
        assert item_dict['quantity'] == float(sample_invoice_item.quantity)
        assert item_dict['rate'] == float(sample_invoice_item.rate)
        assert item_dict['discount_percent'] == float(sample_invoice_item.discount_percent)
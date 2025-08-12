"""
Invoice and InvoiceItem Models
Represents invoice and its items for the invoice management system
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Numeric, ForeignKey
from sqlalchemy.orm import relationship

# Import shared db instance
from database import db

class Invoice(db.Model):
    """Invoice model for storing invoice information"""
    
    __tablename__ = 'invoices'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Invoice identification
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    
    # Foreign keys
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    
    # Purchase order information
    po_number = db.Column(db.String(50))
    po_date = db.Column(db.Date)
    
    # Invoice details
    payment_mode = db.Column(db.String(50), default='RTGS/NEFT')
    transport = db.Column(db.String(100))
    dispatch_from = db.Column(db.String(100))
    
    # Financial information
    subtotal = db.Column(db.Numeric(12, 2))
    gst_amount = db.Column(db.Numeric(12, 2))
    total_amount = db.Column(db.Numeric(12, 2))
    
    # Status
    status = db.Column(db.String(20), default='DRAFT')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, invoice_number, invoice_date, company_id=None, customer_id=None,
                 po_number=None, po_date=None, payment_mode='RTGS/NEFT', 
                 transport=None, dispatch_from=None, status='DRAFT'):
        self.invoice_number = invoice_number
        self.invoice_date = invoice_date
        self.company_id = company_id
        self.customer_id = customer_id
        self.po_number = po_number
        self.po_date = po_date
        self.payment_mode = payment_mode
        self.transport = transport
        self.dispatch_from = dispatch_from
        self.status = status
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'
    
    def to_dict(self):
        """Convert invoice object to dictionary"""
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'company_id': self.company_id,
            'customer_id': self.customer_id,
            'po_number': self.po_number,
            'po_date': self.po_date.isoformat() if self.po_date else None,
            'payment_mode': self.payment_mode,
            'transport': self.transport,
            'dispatch_from': self.dispatch_from,
            'subtotal': float(self.subtotal) if self.subtotal else None,
            'gst_amount': float(self.gst_amount) if self.gst_amount else None,
            'total_amount': float(self.total_amount) if self.total_amount else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items]
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create invoice object from dictionary"""
        invoice_date = None
        po_date = None
        
        if data.get('invoice_date'):
            if isinstance(data['invoice_date'], str):
                invoice_date = datetime.strptime(data['invoice_date'], '%Y-%m-%d').date()
            else:
                invoice_date = data['invoice_date']
        
        if data.get('po_date'):
            if isinstance(data['po_date'], str):
                po_date = datetime.strptime(data['po_date'], '%Y-%m-%d').date()
            else:
                po_date = data['po_date']
        
        return cls(
            invoice_number=data.get('invoice_number'),
            invoice_date=invoice_date,
            company_id=data.get('company_id'),
            customer_id=data.get('customer_id'),
            po_number=data.get('po_number'),
            po_date=po_date,
            payment_mode=data.get('payment_mode', 'RTGS/NEFT'),
            transport=data.get('transport'),
            dispatch_from=data.get('dispatch_from'),
            status=data.get('status', 'DRAFT')
        )
    
    def validate(self):
        """Validate invoice data"""
        errors = []
        
        if not self.invoice_number or not self.invoice_number.strip():
            errors.append("Invoice number is required")
        
        if not self.invoice_date:
            errors.append("Invoice date is required")
        
        if self.invoice_date and self.invoice_date > date.today():
            errors.append("Invoice date cannot be in the future")
        
        if not self.customer_id:
            errors.append("Customer is required")
        
        if self.status not in ['DRAFT', 'SENT', 'PAID', 'CANCELLED']:
            errors.append("Invalid status")
        
        return errors
    
    def calculate_totals(self):
        """Calculate invoice totals from items"""
        subtotal = 0
        
        # Get current items from database to ensure we have all current items
        from database import db
        current_items = db.session.query(InvoiceItem).filter_by(invoice_id=self.id).all()
        
        for item in current_items:
            if item.amount:
                subtotal += float(item.amount)
        
        # Calculate GST (18% as per terms)
        gst_amount = subtotal * 0.18
        total_amount = subtotal + gst_amount
        
        self.subtotal = subtotal
        self.gst_amount = gst_amount
        self.total_amount = total_amount
    
    def add_item(self, product_id, description, quantity, unit, rate, discount_percent=0):
        """Add item to invoice"""
        item = InvoiceItem(
            invoice_id=self.id,
            product_id=product_id,
            description=description,
            quantity=quantity,
            unit=unit,
            rate=rate,
            discount_percent=discount_percent
        )
        item.calculate_amount()
        self.items.append(item)
        return item
    
    def remove_item(self, item_id):
        """Remove item from invoice"""
        item = InvoiceItem.query.get(item_id)
        if item and item.invoice_id == self.id:
            db.session.delete(item)
            return True
        return False
    
    @staticmethod
    def generate_invoice_number():
        """Generate next invoice number"""
        from datetime import datetime
        today = datetime.now()
        prefix = f"INV-{today.year}-{today.month:02d}-"
        
        # Get last invoice number for this month
        last_invoice = Invoice.query.filter(
            Invoice.invoice_number.like(f"{prefix}%")
        ).order_by(Invoice.invoice_number.desc()).first()
        
        if last_invoice:
            last_number = int(last_invoice.invoice_number.split('-')[-1])
            next_number = last_number + 1
        else:
            next_number = 1
        
        return f"{prefix}{next_number:04d}"


class InvoiceItem(db.Model):
    """Invoice item model for storing individual invoice items"""
    
    __tablename__ = 'invoice_items'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    
    # Item details
    description = db.Column(db.String(255))
    quantity = db.Column(db.Numeric(10, 3))
    unit = db.Column(db.String(20))
    rate = db.Column(db.Numeric(10, 2))
    discount_percent = db.Column(db.Numeric(5, 2), default=0)
    amount = db.Column(db.Numeric(12, 2))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, invoice_id, product_id=None, description=None, quantity=None,
                 unit=None, rate=None, discount_percent=0):
        self.invoice_id = invoice_id
        self.product_id = product_id
        self.description = description
        self.quantity = quantity
        self.unit = unit
        self.rate = rate
        self.discount_percent = discount_percent
    
    def __repr__(self):
        return f'<InvoiceItem {self.description}>'
    
    def to_dict(self):
        """Convert invoice item object to dictionary"""
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'product_id': self.product_id,
            'description': self.description,
            'quantity': float(self.quantity) if self.quantity else None,
            'unit': self.unit,
            'rate': float(self.rate) if self.rate else None,
            'discount_percent': float(self.discount_percent) if self.discount_percent else 0,
            'amount': float(self.amount) if self.amount else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create invoice item object from dictionary"""
        return cls(
            invoice_id=data.get('invoice_id'),
            product_id=data.get('product_id'),
            description=data.get('description'),
            quantity=data.get('quantity'),
            unit=data.get('unit'),
            rate=data.get('rate'),
            discount_percent=data.get('discount_percent', 0)
        )
    
    def validate(self):
        """Validate invoice item data"""
        errors = []
        
        if not self.description or not self.description.strip():
            errors.append("Item description is required")
        
        if not self.quantity or self.quantity <= 0:
            errors.append("Quantity must be greater than 0")
        
        if not self.rate or self.rate <= 0:
            errors.append("Rate must be greater than 0")
        
        if self.discount_percent and (self.discount_percent < 0 or self.discount_percent > 100):
            errors.append("Discount percent must be between 0 and 100")
        
        if not self.unit or not self.unit.strip():
            errors.append("Unit is required")
        
        return errors
    
    def calculate_amount(self):
        """Calculate amount for this item"""
        if self.quantity and self.rate:
            base_amount = float(self.quantity) * float(self.rate)
            discount_amount = base_amount * (float(self.discount_percent or 0) / 100)
            self.amount = base_amount - discount_amount
        else:
            self.amount = 0
        
        return self.amount
    
    def get_formatted_amount(self):
        """Get formatted amount string"""
        if self.amount:
            return f"₹{self.amount:.2f}"
        return "₹0.00"
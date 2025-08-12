"""
Product Model
Represents product information for invoice generation
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric

# Import shared db instance
from database import db

class Product(db.Model):
    """Product model for storing product information"""
    
    __tablename__ = 'products'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Product information
    category = db.Column(db.String(100))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    unit = db.Column(db.String(20), default='KG')
    rate = db.Column(db.Numeric(10, 2))
    hsn_code = db.Column(db.String(20))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoice_items = db.relationship('InvoiceItem', backref='product', lazy=True)
    
    def __init__(self, name, category=None, description=None, unit='KG', 
                 rate=None, hsn_code=None):
        self.name = name
        self.category = category
        self.description = description
        self.unit = unit
        self.rate = rate
        self.hsn_code = hsn_code
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def to_dict(self):
        """Convert product object to dictionary"""
        return {
            'id': self.id,
            'category': self.category,
            'name': self.name,
            'description': self.description,
            'unit': self.unit,
            'rate': float(self.rate) if self.rate else None,
            'hsn_code': self.hsn_code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create product object from dictionary"""
        return cls(
            name=data.get('name'),
            category=data.get('category'),
            description=data.get('description'),
            unit=data.get('unit', 'KG'),
            rate=data.get('rate'),
            hsn_code=data.get('hsn_code')
        )
    
    def validate(self):
        """Validate product data"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("Product name is required")
        
        if self.rate is not None and self.rate < 0:
            errors.append("Rate cannot be negative")
        
        if self.hsn_code and not self.hsn_code.replace(' ', '').isalnum():
            errors.append("HSN code must be alphanumeric")
        
        if not self.unit or not self.unit.strip():
            errors.append("Unit is required")
        
        return errors
    
    def get_display_name(self):
        """Get display name with category if available"""
        if self.category:
            return f"{self.category} - {self.name}"
        return self.name
    
    def get_formatted_rate(self):
        """Get formatted rate string"""
        if self.rate:
            return f"₹{self.rate:.2f} per {self.unit}"
        return "Rate not set"
    
    @staticmethod
    def get_categories():
        """Get all unique categories"""
        categories = db.session.query(Product.category).distinct().all()
        return [cat[0] for cat in categories if cat[0]]
    
    @staticmethod
    def get_by_category(category):
        """Get products by category"""
        return Product.query.filter_by(category=category).all()
    
    def calculate_amount(self, quantity, discount_percent=0):
        """Calculate amount for given quantity and discount"""
        if not self.rate:
            return 0
        
        base_amount = float(self.rate) * float(quantity)
        discount_amount = base_amount * (float(discount_percent) / 100)
        return base_amount - discount_amount
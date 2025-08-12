"""
Customer Model
Represents customer information for invoice generation
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

# Import shared db instance
from database import db

class Customer(db.Model):
    """Customer model for storing customer information"""
    
    __tablename__ = 'customers'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Customer basic information
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    
    # Tax information
    gstin = db.Column(db.String(20))
    
    # Contact information
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoices = db.relationship('Invoice', backref='customer', lazy=True)
    
    def __init__(self, name, address=None, city=None, state=None, pincode=None,
                 gstin=None, contact_person=None, phone=None, email=None):
        self.name = name
        self.address = address
        self.city = city
        self.state = state
        self.pincode = pincode
        self.gstin = gstin
        self.contact_person = contact_person
        self.phone = phone
        self.email = email
    
    def __repr__(self):
        return f'<Customer {self.name}>'
    
    def to_dict(self):
        """Convert customer object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'gstin': self.gstin,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create customer object from dictionary"""
        return cls(
            name=data.get('name'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            pincode=data.get('pincode'),
            gstin=data.get('gstin'),
            contact_person=data.get('contact_person'),
            phone=data.get('phone'),
            email=data.get('email')
        )
    
    def validate(self):
        """Validate customer data"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("Customer name is required")
        
        if self.email and '@' not in self.email:
            errors.append("Invalid email format")
        
        if self.gstin and len(self.gstin) != 15:
            errors.append("GSTIN must be 15 characters")
        
        if self.pincode and not self.pincode.isdigit():
            errors.append("Pincode must be numeric")
        
        if self.phone and not self.phone.replace(' ', '').replace('-', '').replace('+', '').isdigit():
            errors.append("Invalid phone number format")
        
        return errors
    
    def get_full_address(self):
        """Get formatted full address"""
        address_parts = [
            self.address,
            self.city,
            self.state,
            self.pincode
        ]
        return ', '.join(part for part in address_parts if part)
    
    def get_display_name(self):
        """Get display name with contact person if available"""
        if self.contact_person:
            return f"{self.name} (Attn: {self.contact_person})"
        return self.name
"""
Company Model
Represents company information for invoice generation
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

# Import shared db instance
from database import db

class Company(db.Model):
    """Company model for storing company information"""
    
    __tablename__ = 'companies'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Company basic information
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    
    # Tax information
    gstin = db.Column(db.String(20))
    
    # Contact information
    contact_phone = db.Column(db.String(50))
    email = db.Column(db.String(100))
    
    # Banking information
    bank_name = db.Column(db.String(255))
    account_number = db.Column(db.String(50))
    ifsc_code = db.Column(db.String(20))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoices = db.relationship('Invoice', backref='company', lazy=True)
    
    def __init__(self, name, address=None, city=None, state=None, pincode=None,
                 gstin=None, contact_phone=None, email=None, bank_name=None,
                 account_number=None, ifsc_code=None):
        self.name = name
        self.address = address
        self.city = city
        self.state = state
        self.pincode = pincode
        self.gstin = gstin
        self.contact_phone = contact_phone
        self.email = email
        self.bank_name = bank_name
        self.account_number = account_number
        self.ifsc_code = ifsc_code
    
    def __repr__(self):
        return f'<Company {self.name}>'
    
    def to_dict(self):
        """Convert company object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'gstin': self.gstin,
            'contact_phone': self.contact_phone,
            'email': self.email,
            'bank_name': self.bank_name,
            'account_number': self.account_number,
            'ifsc_code': self.ifsc_code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create company object from dictionary"""
        return cls(
            name=data.get('name'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            pincode=data.get('pincode'),
            gstin=data.get('gstin'),
            contact_phone=data.get('contact_phone'),
            email=data.get('email'),
            bank_name=data.get('bank_name'),
            account_number=data.get('account_number'),
            ifsc_code=data.get('ifsc_code')
        )
    
    def validate(self):
        """Validate company data"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("Company name is required")
        
        if self.email and '@' not in self.email:
            errors.append("Invalid email format")
        
        if self.gstin and len(self.gstin) != 15:
            errors.append("GSTIN must be 15 characters")
        
        if self.pincode and not self.pincode.isdigit():
            errors.append("Pincode must be numeric")
        
        if self.ifsc_code and len(self.ifsc_code) != 11:
            errors.append("IFSC code must be 11 characters")
        
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
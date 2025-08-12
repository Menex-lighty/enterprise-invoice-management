"""
Routes Package
Contains all API route blueprints for the invoice management system
"""

from .auth import auth_bp
from .company import company_bp
from .customer import customer_bp
from .product import product_bp
from .invoice import invoice_bp

__all__ = [
    'auth_bp',
    'company_bp',
    'customer_bp',
    'product_bp',
    'invoice_bp'
]
"""
Database initialization and configuration
Creates a single SQLAlchemy instance to be shared across the application
"""

from flask_sqlalchemy import SQLAlchemy

# Create a single SQLAlchemy instance
db = SQLAlchemy()

def init_database(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Import all models to register them with SQLAlchemy
        from models.user import User
        from models.company import Company
        from models.customer import Customer
        from models.product import Product
        from models.invoice import Invoice, InvoiceItem
        
        # Create all tables
        db.create_all()
        
        print("[SUCCESS] Database initialized successfully!")
        return db

def get_db():
    """Get the database instance"""
    return db

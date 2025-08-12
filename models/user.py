"""
User Model
Represents user authentication and authorization for the invoice system
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token

# Import shared db instance
from database import db

class User(db.Model):
    """User model for authentication and authorization"""
    
    __tablename__ = 'users'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # User identification
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # User information
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    
    # Authorization
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def __init__(self, username, email, password=None, first_name=None, 
                 last_name=None, phone=None, is_admin=False, is_active=True):
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.is_admin = is_admin
        self.is_active = is_active
        if password:
            self.set_password(password)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_sensitive=False):
        """Convert user object to dictionary"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
        
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create user object from dictionary"""
        return cls(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=data.get('phone'),
            is_admin=data.get('is_admin', False),
            is_active=data.get('is_active', True)
        )
    
    def validate(self):
        """Validate user data"""
        errors = []
        
        if not self.username or not self.username.strip():
            errors.append("Username is required")
        
        if len(self.username) < 3:
            errors.append("Username must be at least 3 characters")
        
        if not self.email or not self.email.strip():
            errors.append("Email is required")
        
        if '@' not in self.email:
            errors.append("Invalid email format")
        
        if not self.password_hash:
            errors.append("Password is required")
        
        # Check if username already exists (for new users)
        if not self.id:
            existing_user = User.query.filter_by(username=self.username).first()
            if existing_user:
                errors.append("Username already exists")
        
        # Check if email already exists (for new users)
        if not self.id:
            existing_email = User.query.filter_by(email=self.email).first()
            if existing_email:
                errors.append("Email already exists")
        
        return errors
    
    def get_full_name(self):
        """Get full name of user"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def generate_tokens(self):
        """Generate JWT tokens for user"""
        access_token = create_access_token(identity=self.id)
        refresh_token = create_refresh_token(identity=self.id)
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': self.to_dict()
        }
    
    def can_access_admin(self):
        """Check if user can access admin features"""
        return self.is_admin and self.is_active
    
    def can_create_invoices(self):
        """Check if user can create invoices"""
        return self.is_active
    
    def can_edit_invoice(self, invoice):
        """Check if user can edit specific invoice"""
        if not self.is_active:
            return False
        
        if self.is_admin:
            return True
        
        # Regular users can only edit draft invoices
        return invoice.status == 'DRAFT'
    
    def can_delete_invoice(self, invoice):
        """Check if user can delete specific invoice"""
        if not self.is_active:
            return False
        
        if self.is_admin:
            return True
        
        # Regular users can only delete draft invoices
        return invoice.status == 'DRAFT'
    
    @staticmethod
    def authenticate(username, password):
        """Authenticate user with username and password"""
        user = User.query.filter_by(username=username, is_active=True).first()
        if user and user.check_password(password):
            user.update_last_login()
            return user
        return None
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_by_email(email):
        """Get user by email"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def get_all_active():
        """Get all active users"""
        return User.query.filter_by(is_active=True).all()
    
    @staticmethod
    def get_all_admins():
        """Get all admin users"""
        return User.query.filter_by(is_admin=True, is_active=True).all()
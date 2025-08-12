#!/usr/bin/env python3
"""
Invoice Management System - Complete Flask Application
Backend API + Web Interface in Pure Python
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from datetime import datetime, date
from flask_wtf.csrf import generate_csrf
# Import database initialization
from database import db, init_database

# Import API route blueprints (existing)
from routes.auth import auth_bp
from routes.company import company_bp
from routes.customer import customer_bp
from routes.product import product_bp
from routes.invoice import invoice_bp

# Import WEB route blueprints (new)
try:
    from web.auth import web_auth_bp
    from web.dashboard import web_dashboard_bp
    from web.companies import web_companies_bp
    from web.customers import web_customers_bp
    from web.products import web_products_bp
    from web.invoices import web_invoices_bp
    WEB_INTERFACE_ENABLED = True
except ImportError:
    print("⚠️  Web interface modules not found. Running in API-only mode.")
    print("   Run the setup script to enable web interface.")
    WEB_INTERFACE_ENABLED = False

# Import models to ensure they're registered
from models.user import User
from models.company import Company
from models.customer import Customer
from models.product import Product
from models.invoice import Invoice, InvoiceItem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration class
class Config:
    """Flask configuration for both API and Web interface"""
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///invoice_system.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('FLASK_ENV') == 'development'
    
    # Database engine options (conditional based on database type)
    @staticmethod
    def get_engine_options():
        database_url = os.getenv('DATABASE_URL', 'sqlite:///invoice_system.db')
        if database_url.startswith('sqlite://'):
            return {}  # No special options for SQLite
        else:
            return {
                'pool_size': 10,
                'pool_recycle': 120,
                'pool_pre_ping': True
            }
    
    SQLALCHEMY_ENGINE_OPTIONS = get_engine_options()
    
    # JWT Configuration (for API)
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production-2024')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    BCRYPT_LOG_ROUNDS = int(os.getenv('BCRYPT_LOG_ROUNDS', '13'))
    
    # Session configuration (for Web interface)
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'invoice_system:'
    SESSION_FILE_DIR = os.path.join(os.getcwd(), 'flask_session')
    
    # WTF CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:8080,http://localhost:3000').split(',')
    
    # File Upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))  # 16MB
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "1000 per hour"



def create_sample_data():
    """Create sample data for development"""
    try:
        # Check if sample data already exists
        if Company.query.count() > 0:
            return
        
        # Create sample company
        sample_company = Company(
            name="Acme Corporation",
            email="info@acme.com",
            phone="+1-555-0123",
            address="123 Business Street, Suite 100\nBusiness City, BC 12345",
            website="https://acme.com",
            tax_number="TAX123456789"
        )
        
        # Create sample customers
        customers = [
            Customer(
                name="John Smith",
                email="john.smith@email.com",
                phone="+1-555-0001",
                address="456 Main Street\nCity, State 67890"
            ),
            Customer(
                name="Jane Doe",
                email="jane.doe@email.com",
                phone="+1-555-0002",
                address="789 Oak Avenue\nTown, State 54321"
            ),
            Customer(
                name="ABC Corp",
                email="contact@abccorp.com",
                phone="+1-555-0003",
                address="321 Corporate Blvd\nBusiness Park, State 98765"
            )
        ]
        
        # Create sample products
        products = [
            Product(
                name="Web Development Service",
                description="Custom website development",
                unit_price=150.00,
                unit="hour"
            ),
            Product(
                name="Mobile App Development",
                description="iOS and Android app development",
                unit_price=200.00,
                unit="hour"
            ),
            Product(
                name="Consulting Service",
                description="Technical consulting and advice",
                unit_price=125.00,
                unit="hour"
            ),
            Product(
                name="Software License",
                description="Annual software license",
                unit_price=599.00,
                unit="license"
            )
        ]
        
        # Add all to database
        db.session.add(sample_company)
        for customer in customers:
            db.session.add(customer)
        for product in products:
            db.session.add(product)
        
        db.session.commit()
        logger.info("Sample data created successfully")
        
    except Exception as e:
        logger.error(f"Error creating sample data: {str(e)}")
        db.session.rollback()

def create_default_data():
    """Create default admin user and sample data if needed"""
    try:
        # Create default admin user if none exists
        if User.query.filter_by(is_admin=True).count() == 0:
            admin_user = User(
                username='admin',
                email='admin@invoicesystem.com',
                password='admin123',
                first_name='System',
                last_name='Administrator',
                is_admin=True,
                is_active=True
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            logger.info("Default admin user created: admin/admin123")
        
        # Create sample data if in development
        if os.getenv('FLASK_ENV') == 'development' and Company.query.count() == 0:
            create_sample_data()
            
    except Exception as e:
        logger.error(f"Error creating default admin: {str(e)}")
        db.session.rollback()

def create_app(config_class=Config):
    """Application factory pattern"""
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    # Initialize extensions
    init_database(app)  # Initialize database first
    migrate = Migrate(app, db)
    
    # Initialize session management for web interface
    Session(app)
    
    # Initialize CSRF protection for web forms
    csrf = CSRFProtect(app)
    
    # Exempt API routes from CSRF protection
    csrf.exempt(auth_bp)
    csrf.exempt(company_bp)
    csrf.exempt(customer_bp)
    csrf.exempt(product_bp)
    csrf.exempt(invoice_bp)
    
    # CORS Configuration (for API)
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # JWT Configuration (for API)
    jwt = JWTManager(app)
    
    # Rate limiting
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[app.config['RATELIMIT_DEFAULT']]
    )
    
    # ============================================================================
    # REGISTER API BLUEPRINTS (existing functionality)
    # ============================================================================
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(company_bp, url_prefix='/api/companies')
    app.register_blueprint(customer_bp, url_prefix='/api/customers')
    app.register_blueprint(product_bp, url_prefix='/api/products')
    app.register_blueprint(invoice_bp, url_prefix='/api/invoices')
    
    # ============================================================================
    # REGISTER WEB BLUEPRINTS (new web interface)
    # ============================================================================
    if WEB_INTERFACE_ENABLED:
        app.register_blueprint(web_auth_bp, url_prefix='/auth')
        app.register_blueprint(web_dashboard_bp, url_prefix='/dashboard')
        app.register_blueprint(web_companies_bp, url_prefix='/companies')
        app.register_blueprint(web_customers_bp, url_prefix='/customers')
        app.register_blueprint(web_products_bp, url_prefix='/products')
        app.register_blueprint(web_invoices_bp, url_prefix='/invoices')
    
    # ============================================================================
    # ROOT ROUTES
    # ============================================================================
    @app.route('/')
    def index():
        """Root route - redirect to appropriate interface"""
        if WEB_INTERFACE_ENABLED:
            if 'user_id' in session:
                return redirect(url_for('web_dashboard.dashboard'))
            return redirect(url_for('web_auth.login'))
        else:
            return jsonify({
                'message': 'Invoice Management System API',
                'version': '1.0.0',
                'status': 'running',
                'api_base': '/api',
                'endpoints': {
                    'health': '/api/health',
                    'auth': '/api/auth',
                    'companies': '/api/companies',
                    'customers': '/api/customers',
                    'products': '/api/products',
                    'invoices': '/api/invoices'
                }
            })
    
    # ============================================================================
    # API ROUTES
    # ============================================================================
    @app.route('/api')
    def api_info():
        """API information endpoint"""
        return jsonify({
            'message': 'Invoice Management System API',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'health': '/api/health',
                'auth': '/api/auth/*',
                'companies': '/api/companies/*',
                'customers': '/api/customers/*',
                'products': '/api/products/*',
                'invoices': '/api/invoices/*',
                'dashboard': '/api/dashboard/stats'
            }
        })
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            # Test database connection
            db.session.execute('SELECT 1')
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)}'
            
        return jsonify({
            'status': 'healthy',
            'message': 'Invoice Management System is running',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'database': db_status,
            'environment': os.getenv('FLASK_ENV', 'development'),
            'web_interface': WEB_INTERFACE_ENABLED,
            'features': {
                'api': True,
                'web_interface': WEB_INTERFACE_ENABLED,
                'authentication': True,
                'pdf_generation': True,
                'excel_export': True
            }
        }), 200
    
    @app.route('/api/dashboard/stats', methods=['GET'])
    def dashboard_stats():
        """Dashboard statistics for API"""
        try:
            from datetime import datetime
            from sqlalchemy import func
            
            # Calculate various statistics
            total_invoices = Invoice.query.count()
            total_revenue = db.session.query(func.sum(Invoice.total_amount)).scalar() or 0
            pending_amount = db.session.query(func.sum(Invoice.total_amount)).filter(
                Invoice.status.in_(['pending', 'sent'])
            ).scalar() or 0
            
            stats = {
                'total_companies': Company.query.count(),
                'total_customers': Customer.query.count(),
                'total_products': Product.query.count(),
                'total_invoices': total_invoices,
                'total_revenue': float(total_revenue),
                'pending_amount': float(pending_amount),
                'invoice_status_breakdown': {
                    'draft': Invoice.query.filter_by(status='draft').count(),
                    'pending': Invoice.query.filter_by(status='pending').count(),
                    'sent': Invoice.query.filter_by(status='sent').count(),
                    'paid': Invoice.query.filter_by(status='paid').count(),
                    'overdue': Invoice.query.filter(
                        Invoice.due_date < datetime.now(),
                        Invoice.status.in_(['pending', 'sent'])
                    ).count()
                },
                'recent_activity': {
                    'recent_invoices': Invoice.query.order_by(Invoice.created_at.desc()).limit(5).count(),
                    'this_month_invoices': Invoice.query.filter(
                        func.date_trunc('month', Invoice.created_at) == func.date_trunc('month', datetime.now())
                    ).count()
                }
            }
            
            return jsonify(stats), 200
            
        except Exception as e:
            logger.error(f"Dashboard stats error: {str(e)}")
            return jsonify({'error': 'Unable to fetch dashboard statistics'}), 500
    
    # ============================================================================
    # CORS PREFLIGHT HANDLER
    # ============================================================================
    @app.before_request
    def handle_preflight():
        """Handle CORS preflight requests"""
        if request.method == "OPTIONS":
            response = jsonify({'message': 'CORS preflight successful'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            return response

    @app.after_request
    def after_request(response):
        """Add CORS headers to all responses"""
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    # ============================================================================
    # ERROR HANDLERS
    # ============================================================================
    @app.errorhandler(400)
    def bad_request(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Bad request'}), 400
        flash('Bad request', 'danger')
        return redirect(url_for('index'))

    @app.errorhandler(401)
    def unauthorized(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Unauthorized'}), 401
        flash('Please log in to access this page', 'warning')
        if WEB_INTERFACE_ENABLED:
            return redirect(url_for('web_auth.login'))
        return jsonify({'error': 'Unauthorized'}), 401

    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden'}), 403
        flash('Access denied', 'danger')
        if WEB_INTERFACE_ENABLED:
            return redirect(url_for('web_dashboard.dashboard'))
        return jsonify({'error': 'Forbidden'}), 403

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Endpoint not found'}), 404
        if WEB_INTERFACE_ENABLED:
            return render_template('errors/404.html'), 404
        return jsonify({'error': 'Endpoint not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        db.session.rollback()
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        flash('An error occurred. Please try again.', 'danger')
        if WEB_INTERFACE_ENABLED:
            return redirect(url_for('index'))
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        """Rate limit error handler"""
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Rate limit exceeded', 'retry_after': str(e.retry_after)}), 429
        flash('Too many requests. Please wait before trying again.', 'warning')
        return redirect(url_for('index'))
    # ============================================================================
    # TEMPLATE CONTEXT PROCESSORS (ADD THIS SECTION)
    # ============================================================================
    from datetime import datetime, date
    from flask_wtf.csrf import generate_csrf
    
    @app.context_processor
    def inject_template_vars():
        """Inject common variables into all templates"""
        def today():
            return date.today()
        
        def now():
            return datetime.now()
        
        def moment():
            """Simple moment-like object for date formatting"""
            class Moment:
                def format(self, format_string):
                    now = datetime.now()
                    if format_string == 'dddd, MMMM Do YYYY':
                        return now.strftime('%A, %B %d, %Y')
                    elif format_string == 'YYYY-MM-DD HH:mm:ss':
                        return now.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        return now.strftime('%Y-%m-%d')
            return Moment()
        
        return dict(
            today=today,
            now=now,
            moment=moment,
            csrf_token=generate_csrf
        )
    # ============================================================================
    # JWT ERROR HANDLERS (for API)
    # ============================================================================
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Authorization token required'}), 401
    
    # ============================================================================
    # INITIALIZE DEFAULT DATA
    # ============================================================================
    with app.app_context():
        create_default_data()
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 Invoice Management System Starting...")
    print("=" * 80)
    
    # Display interface information
    if WEB_INTERFACE_ENABLED:
        print("🌐 WEB INTERFACE: http://localhost:5000")
        print("📱 API INTERFACE: http://localhost:5000/api")
        print("🔐 Login: http://localhost:5000/auth/login")
        print("📊 Dashboard: http://localhost:5000/dashboard")
    else:
        print("📱 API-ONLY MODE: http://localhost:5000/api")
        print("⚠️  Web interface not enabled. Run setup script to enable.")
    
    print("=" * 80)
    print("📍 Available Endpoints:")
    print("   💓 Health Check: /api/health")
    print("   📊 API Info: /api")
    print("   🔑 Authentication: /api/auth/*")
    print("   🏢 Companies: /api/companies/*")
    print("   👥 Customers: /api/customers/*")
    print("   📦 Products: /api/products/*")
    print("   📄 Invoices: /api/invoices/*")
    print("   📈 Dashboard Stats: /api/dashboard/stats")
    
    if WEB_INTERFACE_ENABLED:
        print("   🌐 Web Dashboard: /dashboard")
        print("   🏢 Web Companies: /companies")
        print("   👥 Web Customers: /customers")
        print("   📦 Web Products: /products")
        print("   📄 Web Invoices: /invoices")
    
    print("=" * 80)
    print("🔐 Default Admin Credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("   Email: admin@invoicesystem.com")
    print("=" * 80)
    print("💡 Features Available:")
    print("   ✅ RESTful API with JWT authentication")
    print("   ✅ Database models with relationships")
    print("   ✅ PDF invoice generation")
    print("   ✅ Excel data export")
    print("   ✅ Input validation and error handling")
    print("   ✅ Rate limiting and CORS support")
    print("   ✅ Comprehensive test suite")
    if WEB_INTERFACE_ENABLED:
        print("   ✅ Responsive web interface")
        print("   ✅ Session-based authentication")
        print("   ✅ Bootstrap UI with charts")
    else:
        print("   ⏳ Web interface (run setup script to enable)")
    print("=" * 80)
    
    # Run the application
    app.run(
        debug=os.getenv('FLASK_ENV') == 'development',
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        threaded=True
    )
# 📊 Enterprise Invoice Management System

A comprehensive, production-ready Flask-based invoice management system with multi-company support, role-based authentication, and professional PDF/Excel reporting capabilities.

![Flask](https://img.shields.io/badge/Flask-2.3.3-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9+-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![Tests](https://img.shields.io/badge/Test%20Coverage-85%2B%25-green.svg)

## 🎯 **Overview**

This enterprise-grade invoice management system demonstrates modern backend architecture with Flask, featuring comprehensive business logic, security implementation, and scalable design patterns. Built with production deployment in mind, it showcases professional software development practices including comprehensive testing, Docker containerization, and clean API design.

**Key Business Value:**
- **Multi-company support** with isolated data management
- **Complete invoice lifecycle** from draft to payment tracking
- **Professional PDF generation** with tax calculations
- **Role-based access control** for secure operations
- **Export capabilities** for business intelligence integration

## 🚀 **Core Features**

### **📋 Invoice Management**
- **Complete invoice lifecycle** (Draft → Sent → Paid)
- **Line item management** with product references
- **Automatic calculations** (subtotals, GST, discounts, totals)
- **Invoice duplication** for recurring billing
- **Advanced filtering** (date ranges, status, customer, company)
- **Professional PDF generation** with company branding

### **🏢 Multi-Company Architecture**
- **Company profiles** with complete contact information
- **Data isolation** between companies
- **Customer management** per company with GST support
- **Product catalogs** with HSN codes and rates
- **User role management** (Admin vs Regular users)

### **🔐 Security & Authentication**
- **JWT-based authentication** with refresh tokens
- **Password hashing** using bcrypt
- **Role-based access control** (RBAC)
- **CSRF protection** for web interface
- **Environment-based configuration** for secrets

### **📈 Reporting & Analytics**
- **PDF invoice generation** using ReportLab
- **Excel exports** for customers, products, invoices
- **Business statistics** and summaries
- **Flexible report generation** utilities

### **🔧 Production Features**
- **Docker containerization** with multi-service setup
- **Database migrations** with Flask-Migrate
- **Comprehensive testing** (85%+ coverage goal)
- **API rate limiting** and CORS support
- **Environment-based deployment** (dev/staging/production)

## 🛠️ **Tech Stack**

### **Backend Framework**
- **Flask 2.3.3** - Web framework
- **SQLAlchemy 2.0** - ORM with PostgreSQL
- **Flask-JWT-Extended** - Authentication
- **Flask-Migrate** - Database migrations

### **Database & Storage**
- **PostgreSQL 16** - Primary database
- **SQLite** - Development/testing
- **Redis** - Caching (production)

### **Document Generation**
- **ReportLab** - Professional PDF generation
- **OpenPyXL** - Excel file creation
- **Num2Words** - Number to words conversion

### **Development & Deployment**
- **Docker Compose** - Multi-service orchestration
- **Pytest** - Comprehensive testing framework
- **Nginx** - Reverse proxy (production)
- **Gunicorn** - WSGI server

## 📁 **Project Structure**

```
invoice-management-system/
├── app.py                      # Main Flask application
├── database.py                 # Database initialization
├── docker-compose.yml          # Multi-service setup
├── requirements.txt            # Dependencies
├── models/                     # Data models
│   ├── user.py                 # User authentication
│   ├── company.py              # Company management
│   ├── customer.py             # Customer profiles
│   ├── product.py              # Product catalog
│   └── invoice.py              # Invoice & line items
├── routes/                     # API endpoints
│   ├── auth.py                 # Authentication routes
│   ├── company.py              # Company CRUD
│   ├── customer.py             # Customer CRUD
│   ├── product.py              # Product CRUD
│   └── invoice.py              # Invoice management
├── utils/                      # Utility functions
│   ├── pdf_generator.py        # PDF creation
│   └── excel_generator.py      # Excel exports
└── tests/                      # Comprehensive test suite
    ├── test_models.py          # Model tests
    ├── test_auth_routes.py     # Auth tests
    ├── test_*_routes.py        # Route tests
    ├── test_utils.py           # Utility tests
    └── test_integration.py     # Integration tests
```

## 🚀 **Quick Start**

### **1. Clone & Setup**
```bash
git clone https://github.com/yourusername/invoice-management-system.git
cd invoice-management-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **2. Environment Configuration**
```bash
# Create .env file
cp .env.example .env

# Configure environment variables
DATABASE_URL=postgresql://user:password@localhost:5432/invoice_system
JWT_SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

### **3. Database Setup**
```bash
# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Create default admin user
python -c "from app import create_app; app = create_app(); app.app_context().push(); from app import create_default_data; create_default_data()"
```

### **4. Run Development Server**
```bash
python app.py
```

**Default Admin Credentials:**
- Username: `admin`
- Password: `admin123`

### **5. Docker Deployment** (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## 📊 **API Documentation**

### **Authentication**
```bash
# Login
POST /api/auth/login
{
  "username": "admin",
  "password": "admin123"
}

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {...}
}
```

### **Invoice Management**
```bash
# Create invoice
POST /api/invoices
Authorization: Bearer <token>
{
  "invoice_date": "2024-01-15",
  "company_id": 1,
  "customer_id": 1,
  "po_number": "PO-2024-001"
}

# Add invoice items
POST /api/invoices/{id}/items
{
  "product_id": 1,
  "quantity": 10.0,
  "rate": 100.00,
  "discount_percent": 10.0
}

# Generate PDF
GET /api/invoices/{id}/pdf
Authorization: Bearer <token>
```

### **Advanced Filtering**
```bash
# Filter invoices
GET /api/invoices?status=DRAFT&customer_id=1&date_from=2024-01-01&date_to=2024-01-31&page=1&per_page=10
```

## 🧪 **Testing**

### **Run Tests**
```bash
# Run all tests
python run_tests.py --mode all

# Run specific categories
python run_tests.py --mode unit      # Model tests
python run_tests.py --mode routes    # API tests
python run_tests.py --mode integration

# Generate coverage report
python run_tests.py --mode report
```

### **Test Categories**
- **Unit Tests**: Model validation, business logic
- **Route Tests**: API endpoints, authentication
- **Integration Tests**: Complete workflows
- **Utility Tests**: PDF/Excel generation

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Security
JWT_SECRET_KEY=your-jwt-secret-key
SECRET_KEY=your-flask-secret-key

# Application
FLASK_ENV=development|production
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# File Storage
UPLOAD_FOLDER=./uploads
MAX_CONTENT_LENGTH=16777216  # 16MB
```

## 📈 **Architecture Highlights**

### **Database Design**
- **Normalized schema** with proper foreign key relationships
- **Cascade delete operations** for data integrity
- **Timestamp tracking** on all entities
- **Flexible multi-company** data isolation

### **Security Implementation**
- **JWT authentication** with configurable expiration
- **Password hashing** with bcrypt and configurable rounds
- **Role-based permissions** (Admin vs Regular users)
- **CSRF protection** for web forms
- **Environment-based secrets** management

### **Scalability Features**
- **Connection pooling** for database optimization
- **Pagination support** for large datasets
- **Rate limiting** to prevent abuse
- **Caching layer** (Redis) for production
- **Horizontal scaling** ready with Docker

### **Testing Strategy**
- **Comprehensive test coverage** across all layers
- **Fixture-based testing** for consistent data
- **Integration testing** for complete workflows
- **Performance testing** with benchmarks
- **CI/CD pipeline** ready

## 🚀 **Production Deployment**

### **Docker Production**
```bash
# Production deployment
docker-compose --profile production up -d

# With SSL/HTTPS
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### **Environment Setup**
```bash
# Production environment variables
FLASK_ENV=production
DATABASE_URL=postgresql://user:password@prod-db:5432/invoice_system
JWT_SECRET_KEY=secure-production-key
CORS_ORIGINS=https://yourdomain.com
```

## 📋 **Business Logic Features**

### **Invoice Calculations**
- **Automatic subtotal calculation** from line items
- **GST calculation** (18% configurable)
- **Discount application** at item level
- **Total amount computation** with tax
- **Number to words conversion** for amounts

### **Workflow Management**
- **Status progression**: Draft → Sent → Paid
- **Invoice numbering**: Auto-generated sequential
- **Duplicate prevention** with validation
- **Date range filtering** for reporting

### **Multi-Company Support**
- **Data isolation** between companies
- **User access control** per company
- **Separate invoice sequences** per company
- **Company-specific branding** in PDFs

## 🎯 **Business Value Delivered**

### **Operational Efficiency**
- **Automated invoice generation** reduces manual work
- **Professional PDF output** improves brand image
- **Multi-company support** enables business scaling
- **Role-based access** ensures security compliance

### **Technical Excellence**
- **Production-ready architecture** with Docker
- **Comprehensive testing** ensures reliability
- **API-first design** enables frontend flexibility
- **Modern Flask patterns** for maintainability

### **Scalability & Maintenance**
- **Modular architecture** for easy extensions
- **Environment-based configuration** for deployments
- **Database migration support** for schema evolution
- **Comprehensive logging** for troubleshooting

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 **Contact**

**Developer**: Your Name  
**Email**: your.email@example.com  
**LinkedIn**: [Your LinkedIn Profile](https://linkedin.com/in/yourprofile)  
**Portfolio**: [Your Portfolio Website](https://yourportfolio.com)

---

**⭐ Star this repository if you find it useful!**

*This project demonstrates enterprise-level Flask development with modern architecture patterns, comprehensive testing, and production-ready deployment configuration.*

# Invoice Management System - Test Suite

This directory contains comprehensive tests for the Invoice Management System, covering models, routes, utilities, and integration scenarios.

## 📁 Test Structure

```
tests/
├── README.md                  # This file
├── conftest.py               # Test configuration and fixtures
├── test_models.py            # Model tests
├── test_auth_routes.py       # Authentication route tests
├── test_company_routes.py    # Company route tests
├── test_customer_routes.py   # Customer route tests
├── test_product_routes.py    # Product route tests
├── test_invoice_routes.py    # Invoice route tests
├── test_utils.py             # Utility function tests
└── test_integration.py       # Integration tests
```

## 🚀 Quick Start

### Prerequisites

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

2. **Set Environment Variables**
   ```bash
   export FLASK_ENV=testing
   export DATABASE_URL=sqlite:///:memory:
   export JWT_SECRET_KEY=test-secret-key
   ```

### Running Tests

#### Using the Test Runner (Recommended)

```bash
# Run all tests
python run_tests.py --mode all

# Run specific test categories
python run_tests.py --mode unit
python run_tests.py --mode routes
python run_tests.py --mode integration

# Run with coverage report
python run_tests.py --mode report

# Run CI pipeline
python run_tests.py --mode ci
```

#### Using Pytest Directly

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_models.py

# Run with coverage
pytest tests/ --cov=models --cov=routes --cov=utils --cov=app

# Run specific test function
pytest tests/test_models.py::TestUser::test_user_creation

# Run tests with markers
pytest tests/ -m "unit"
pytest tests/ -m "integration"
```

## 📊 Test Categories

### 1. **Model Tests** (`test_models.py`)
- User model validation and authentication
- Company model CRUD operations
- Customer model validation
- Product model calculations
- Invoice and InvoiceItem model relationships
- Data serialization and deserialization

### 2. **Authentication Route Tests** (`test_auth_routes.py`)
- User login/logout functionality
- JWT token management
- User registration (admin only)
- Password change operations
- User management endpoints
- Permission-based access control

### 3. **Company Route Tests** (`test_company_routes.py`)
- Company CRUD operations
- Company search functionality
- Company statistics
- Company-invoice relationships
- Admin-only operations

### 4. **Customer Route Tests** (`test_customer_routes.py`)
- Customer CRUD operations
- Customer search and filtering
- Customer statistics
- Customer-invoice relationships
- Data export functionality

### 5. **Product Route Tests** (`test_product_routes.py`)
- Product CRUD operations
- Category management
- Product search and filtering
- Bulk operations (import/export)
- Product statistics
- Rate calculations

### 6. **Invoice Route Tests** (`test_invoice_routes.py`)
- Invoice CRUD operations
- Invoice item management
- Automatic calculations (subtotal, GST, total)
- Status workflow management
- Invoice duplication
- Complex filtering and search

### 7. **Utility Tests** (`test_utils.py`)
- PDF generation functionality
- Excel export functionality
- File handling and error cases
- Report generation

### 8. **Integration Tests** (`test_integration.py`)
- Complete invoice lifecycle
- User permission workflows
- Search and filter integration
- Statistics across entities
- Data consistency checks
- Bulk operations

## 🔧 Test Configuration

### Environment Variables

- `FLASK_ENV=testing`: Set Flask to testing mode
- `DATABASE_URL=sqlite:///:memory:`: Use in-memory database for tests
- `JWT_SECRET_KEY=test-secret-key`: Test JWT secret
- `TESTING=True`: Enable testing mode

### Pytest Configuration (`pytest.ini`)

- **Coverage**: 85% minimum coverage required
- **Markers**: Tests are categorized with markers for selective execution
- **Reporting**: HTML and XML coverage reports generated
- **Timeout**: 300 seconds maximum per test

## 📈 Test Markers

Use markers to run specific test categories:

```bash
# Run only unit tests
pytest tests/ -m "unit"

# Run only route tests
pytest tests/ -m "routes"

# Run only integration tests
pytest tests/ -m "integration"

# Run authentication tests
pytest tests/ -m "auth"

# Run calculation tests
pytest tests/ -m "calculations"

# Run validation tests
pytest tests/ -m "validation"

# Combine markers
pytest tests/ -m "unit and models"
pytest tests/ -m "routes and not slow"
```

## 📊 Coverage Reports

### Generate Coverage Reports

```bash
# HTML report (interactive)
pytest tests/ --cov=models --cov=routes --cov=utils --cov=app --cov-report=html

# Terminal report
pytest tests/ --cov=models --cov=routes --cov=utils --cov=app --cov-report=term-missing

# XML report (for CI/CD)
pytest tests/ --cov=models --cov=routes --cov=utils --cov=app --cov-report=xml
```

### Coverage Targets

- **Models**: 95%+ coverage
- **Routes**: 90%+ coverage
- **Utils**: 90%+ coverage
- **Overall**: 85%+ coverage

## 🔍 Test Data and Fixtures

### Available Fixtures

- `app`: Flask application instance
- `client`: Test client for API requests
- `db_session`: Database session for testing
- `sample_user`: Regular user for testing
- `sample_admin`: Admin user for testing
- `sample_company`: Company entity
- `sample_customer`: Customer entity
- `sample_product`: Product entity
- `sample_invoice`: Invoice entity
- `sample_invoice_item`: Invoice item entity
- `auth_headers`: Authentication headers for regular user
- `admin_headers`: Authentication headers for admin user

### Using Fixtures

```python
def test_example(client, auth_headers, sample_invoice):
    response = client.get(f'/api/invoices/{sample_invoice.id}', 
                         headers=auth_headers)
    assert response.status_code == 200
```

## 🚨 Test Patterns

### 1. **API Testing Pattern**

```python
def test_api_endpoint(client, auth_headers):
    # Test data
    data = {'key': 'value'}
    
    # Make request
    response = client.post('/api/endpoint', 
                          json=data, 
                          headers=auth_headers)
    
    # Assert response
    assert response.status_code == 201
    assert response.get_json()['key'] == 'value'
```

### 2. **Model Testing Pattern**

```python
def test_model_validation(db_session):
    # Create model instance
    model = Model(required_field='value')
    
    # Test validation
    errors = model.validate()
    assert len(errors) == 0
    
    # Test database operations
    db_session.add(model)
    db_session.commit()
    assert model.id is not None
```

### 3. **Integration Testing Pattern**

```python
def test_integration_workflow(client, admin_headers):
    # Step 1: Create entity
    response = client.post('/api/entities', 
                          json=data, 
                          headers=admin_headers)
    entity_id = response.get_json()['entity']['id']
    
    # Step 2: Use entity
    response = client.get(f'/api/entities/{entity_id}', 
                         headers=admin_headers)
    assert response.status_code == 200
    
    # Step 3: Update entity
    response = client.put(f'/api/entities/{entity_id}', 
                         json=update_data, 
                         headers=admin_headers)
    assert response.status_code == 200
```

## 🔧 Debugging Tests

### Running Single Test with Debug

```bash
# Run specific test with maximum verbosity
pytest tests/test_models.py::TestUser::test_user_creation -vvv -s

# Run with pdb debugger
pytest tests/test_models.py::TestUser::test_user_creation --pdb

# Run failed tests only
pytest tests/ --lf

# Run tests that failed last time
pytest tests/ --ff
```

### Debug Test Database

```python
# In test, print database state
def test_debug_database(db_session):
    # Your test code here
    
    # Debug: Print all users
    users = db_session.query(User).all()
    print(f"Users in database: {[u.username for u in users]}")
```

## 🚀 Performance Testing

### Benchmark Tests

```bash
# Run performance benchmarks
python run_tests.py --mode performance

# Run with benchmark comparison
pytest tests/ --benchmark-compare
```

### Load Testing

```bash
# Run tests in parallel
python run_tests.py --mode parallel

# Run with specific worker count
pytest tests/ -n 4
```

## 📋 Best Practices

### 1. **Test Naming**
- Use descriptive test names: `test_user_creation_with_valid_data`
- Follow pattern: `test_[what]_[condition]_[expected_result]`

### 2. **Test Structure**
- **Arrange**: Set up test data
- **Act**: Execute the code under test
- **Assert**: Verify the results

### 3. **Test Independence**
- Each test should be independent
- Use fixtures for common setup
- Clean up after tests

### 4. **Test Coverage**
- Aim for high coverage but focus on quality
- Test edge cases and error conditions
- Test both success and failure scenarios

### 5. **Test Data**
- Use fixtures for consistent test data
- Avoid hardcoded values
- Test with realistic data volumes

## 🛠️ Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Ensure test database URL is set
   export DATABASE_URL=sqlite:///:memory:
   ```

2. **JWT Token Issues**
   ```bash
   # Set test JWT secret
   export JWT_SECRET_KEY=test-secret-key
   ```

3. **Import Errors**
   ```bash
   # Add project root to Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

4. **Permission Errors**
   ```bash
   # Ensure test directories exist
   mkdir -p reports logs generated_files
   ```

### Getting Help

1. **Check test output**: Read error messages carefully
2. **Use verbose mode**: `pytest -vvv` for detailed output
3. **Check fixtures**: Ensure required fixtures are available
4. **Verify environment**: Check environment variables are set
5. **Review logs**: Check application logs for errors

## 📈 Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    - name: Run tests
      run: python run_tests.py --mode ci
```

### Test Reporting

- **HTML Reports**: `reports/test_report.html`
- **Coverage Reports**: `reports/coverage/index.html`
- **XML Reports**: `coverage.xml` (for CI/CD)

## 🎯 Goals

- **Comprehensive Coverage**: Test all critical functionality
- **Fast Execution**: Keep tests fast and reliable
- **Clear Documentation**: Make tests self-documenting
- **Maintainable**: Easy to update and extend
- **Reliable**: Consistent results across environments

---

For questions or issues with the test suite, please refer to the main project documentation or create an issue in the project repository.
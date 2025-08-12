"""
Customer Routes
Handles customer management operations
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.customer import Customer
from database import db
from models.user import User
from datetime import datetime

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('', methods=['GET'])
@jwt_required()
def get_customers():
    """Get all customers"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get customers with pagination
        customers_query = Customer.query.order_by(Customer.name)
        customers_paginated = customers_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'customers': [customer.to_dict() for customer in customers_paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': customers_paginated.total,
                'pages': customers_paginated.pages,
                'has_next': customers_paginated.has_next,
                'has_prev': customers_paginated.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_customer(customer_id):
    """Get specific customer"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        customer = Customer.query.get(customer_id)
        
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        return jsonify({'customer': customer.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('', methods=['POST'])
@jwt_required()
def create_customer():
    """Create new customer"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create customer from data
        customer = Customer.from_dict(data)
        
        # Validate customer data
        errors = customer.validate()
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        # Save customer to database
        db.session.add(customer)
        db.session.commit()
        
        return jsonify({
            'message': 'Customer created successfully',
            'customer': customer.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/<int:customer_id>', methods=['PUT'])
@jwt_required()
def update_customer(customer_id):
    """Update specific customer"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        customer = Customer.query.get(customer_id)
        
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update customer fields
        allowed_fields = [
            'name', 'address', 'city', 'state', 'pincode', 'gstin',
            'contact_person', 'phone', 'email'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(customer, field, data[field])
        
        customer.updated_at = datetime.utcnow()
        
        # Validate updated customer
        errors = customer.validate()
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': 'Customer updated successfully',
            'customer': customer.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/<int:customer_id>', methods=['DELETE'])
@jwt_required()
def delete_customer(customer_id):
    """Delete specific customer"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        customer = Customer.query.get(customer_id)
        
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Check if customer has associated invoices
        if customer.invoices:
            return jsonify({
                'error': 'Cannot delete customer with associated invoices',
                'invoice_count': len(customer.invoices)
            }), 400
        
        db.session.delete(customer)
        db.session.commit()
        
        return jsonify({'message': 'Customer deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/<int:customer_id>/invoices', methods=['GET'])
@jwt_required()
def get_customer_invoices(customer_id):
    """Get all invoices for a specific customer"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        customer = Customer.query.get(customer_id)
        
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get invoices with pagination
        invoices = customer.invoices
        
        # Apply filters if provided
        status = request.args.get('status')
        if status:
            invoices = [inv for inv in invoices if inv.status == status]
        
        # Sort by date (newest first)
        invoices.sort(key=lambda x: x.created_at, reverse=True)
        
        # Manual pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated_invoices = invoices[start:end]
        
        return jsonify({
            'customer': customer.to_dict(),
            'invoices': [invoice.to_dict() for invoice in paginated_invoices],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(invoices),
                'pages': (len(invoices) + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/search', methods=['GET'])
@jwt_required()
def search_customers():
    """Search customers"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        query = request.args.get('q', '')
        
        if not query:
            return jsonify({'customers': []}), 200
        
        # Search in customer name, city, state, and contact person
        customers = Customer.query.filter(
            (Customer.name.ilike(f'%{query}%')) |
            (Customer.city.ilike(f'%{query}%')) |
            (Customer.state.ilike(f'%{query}%')) |
            (Customer.contact_person.ilike(f'%{query}%'))
        ).all()
        
        return jsonify({
            'customers': [customer.to_dict() for customer in customers],
            'query': query
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/<int:customer_id>/validate', methods=['POST'])
@jwt_required()
def validate_customer(customer_id):
    """Validate customer data"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        customer = Customer.query.get(customer_id)
        
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        errors = customer.validate()
        
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_customer_stats():
    """Get customer statistics"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        total_customers = Customer.query.count()
        
        # Get customers with invoices
        customers_with_invoices = Customer.query.join(Customer.invoices).distinct().count()
        
        # Get customers by state
        customers_by_state = db.session.query(
            Customer.state,
            db.func.count(Customer.id).label('count')
        ).group_by(Customer.state).all()
        
        # Get top customers by invoice count
        top_customers = db.session.query(
            Customer.id,
            Customer.name,
            db.func.count(Customer.invoices).label('invoice_count')
        ).join(Customer.invoices).group_by(Customer.id, Customer.name).order_by(
            db.func.count(Customer.invoices).desc()
        ).limit(10).all()
        
        return jsonify({
            'total_customers': total_customers,
            'customers_with_invoices': customers_with_invoices,
            'customers_by_state': [
                {'state': state, 'count': count}
                for state, count in customers_by_state
            ],
            'top_customers': [
                {'id': customer_id, 'name': name, 'invoice_count': count}
                for customer_id, name, count in top_customers
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/export', methods=['GET'])
@jwt_required()
def export_customers():
    """Export customers to CSV"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        customers = Customer.query.all()
        
        # Prepare CSV data
        csv_data = []
        csv_data.append([
            'ID', 'Name', 'Address', 'City', 'State', 'Pincode',
            'GSTIN', 'Contact Person', 'Phone', 'Email', 'Created At'
        ])
        
        for customer in customers:
            csv_data.append([
                customer.id,
                customer.name,
                customer.address or '',
                customer.city or '',
                customer.state or '',
                customer.pincode or '',
                customer.gstin or '',
                customer.contact_person or '',
                customer.phone or '',
                customer.email or '',
                customer.created_at.strftime('%Y-%m-%d %H:%M:%S') if customer.created_at else ''
            ])
        
        return jsonify({
            'csv_data': csv_data,
            'filename': f'customers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
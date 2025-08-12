"""
Company Routes
Handles company management operations
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.company import Company
from database import db
from models.user import User
from datetime import datetime

company_bp = Blueprint('company', __name__)

@company_bp.route('', methods=['GET'])
@jwt_required()
def get_companies():
    """Get all companies"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        companies = Company.query.all()
        
        return jsonify({
            'companies': [company.to_dict() for company in companies]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@company_bp.route('/<int:company_id>', methods=['GET'])
@jwt_required()
def get_company(company_id):
    """Get specific company"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        company = Company.query.get(company_id)
        
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        return jsonify({'company': company.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@company_bp.route('', methods=['POST'])
@jwt_required()
def create_company():
    """Create new company"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create company from data
        company = Company.from_dict(data)
        
        # Validate company data
        errors = company.validate()
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        # Save company to database
        db.session.add(company)
        db.session.commit()
        
        return jsonify({
            'message': 'Company created successfully',
            'company': company.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@company_bp.route('/<int:company_id>', methods=['PUT'])
@jwt_required()
def update_company(company_id):
    """Update specific company"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        company = Company.query.get(company_id)
        
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update company fields
        allowed_fields = [
            'name', 'address', 'city', 'state', 'pincode', 'gstin',
            'contact_phone', 'email', 'bank_name', 'account_number', 'ifsc_code'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(company, field, data[field])
        
        company.updated_at = datetime.utcnow()
        
        # Validate updated company
        errors = company.validate()
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': 'Company updated successfully',
            'company': company.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@company_bp.route('/<int:company_id>', methods=['DELETE'])
@jwt_required()
def delete_company(company_id):
    """Delete specific company"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        company = Company.query.get(company_id)
        
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        # Check if company has associated invoices
        if company.invoices:
            return jsonify({
                'error': 'Cannot delete company with associated invoices',
                'invoice_count': len(company.invoices)
            }), 400
        
        db.session.delete(company)
        db.session.commit()
        
        return jsonify({'message': 'Company deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@company_bp.route('/<int:company_id>/invoices', methods=['GET'])
@jwt_required()
def get_company_invoices(company_id):
    """Get all invoices for a specific company"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        company = Company.query.get(company_id)
        
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get invoices with pagination
        invoices = company.invoices
        
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
            'company': company.to_dict(),
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

@company_bp.route('/search', methods=['GET'])
@jwt_required()
def search_companies():
    """Search companies"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        query = request.args.get('q', '')
        
        if not query:
            return jsonify({'companies': []}), 200
        
        # Search in company name, city, and state
        companies = Company.query.filter(
            (Company.name.ilike(f'%{query}%')) |
            (Company.city.ilike(f'%{query}%')) |
            (Company.state.ilike(f'%{query}%'))
        ).all()
        
        return jsonify({
            'companies': [company.to_dict() for company in companies],
            'query': query
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@company_bp.route('/<int:company_id>/validate', methods=['POST'])
@jwt_required()
def validate_company(company_id):
    """Validate company data"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        company = Company.query.get(company_id)
        
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        errors = company.validate()
        
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@company_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_company_stats():
    """Get company statistics"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        total_companies = Company.query.count()
        
        # Get companies with invoices
        companies_with_invoices = Company.query.join(Company.invoices).distinct().count()
        
        # Get companies by state
        companies_by_state = db.session.query(
            Company.state,
            db.func.count(Company.id).label('count')
        ).group_by(Company.state).all()
        
        return jsonify({
            'total_companies': total_companies,
            'companies_with_invoices': companies_with_invoices,
            'companies_by_state': [
                {'state': state, 'count': count}
                for state, count in companies_by_state
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
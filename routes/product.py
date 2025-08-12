"""
Product Routes
Handles product management operations
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.product import Product
from database import db
from models.user import User
from datetime import datetime

product_bp = Blueprint('product', __name__)

@product_bp.route('', methods=['GET'])
@jwt_required()
def get_products():
    """Get all products"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get filter parameters
        category = request.args.get('category')
        
        # Build query
        query = Product.query
        
        if category:
            query = query.filter(Product.category == category)
        
        # Order by category then name
        query = query.order_by(Product.category, Product.name)
        
        # Apply pagination
        products_paginated = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'products': [product.to_dict() for product in products_paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': products_paginated.total,
                'pages': products_paginated.pages,
                'has_next': products_paginated.has_next,
                'has_prev': products_paginated.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    """Get specific product"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({'product': product.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('', methods=['POST'])
@jwt_required()
def create_product():
    """Create new product"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create product from data
        product = Product.from_dict(data)
        
        # Validate product data
        errors = product.validate()
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        # Save product to database
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'message': 'Product created successfully',
            'product': product.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """Update specific product"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update product fields
        allowed_fields = [
            'category', 'name', 'description', 'unit', 'rate', 'hsn_code'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(product, field, data[field])
        
        product.updated_at = datetime.utcnow()
        
        # Validate updated product
        errors = product.validate()
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': 'Product updated successfully',
            'product': product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """Delete specific product"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Check if product has associated invoice items
        if product.invoice_items:
            return jsonify({
                'error': 'Cannot delete product with associated invoice items',
                'invoice_item_count': len(product.invoice_items)
            }), 400
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({'message': 'Product deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@product_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Get all product categories"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        categories = Product.get_categories()
        
        return jsonify({'categories': categories}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/categories/<category_name>', methods=['GET'])
@jwt_required()
def get_products_by_category(category_name):
    """Get products by category"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        products = Product.get_by_category(category_name)
        
        return jsonify({
            'category': category_name,
            'products': [product.to_dict() for product in products]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/search', methods=['GET'])
@jwt_required()
def search_products():
    """Search products"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        query = request.args.get('q', '')
        
        if not query:
            return jsonify({'products': []}), 200
        
        # Search in product name, description, and category
        products = Product.query.filter(
            (Product.name.ilike(f'%{query}%')) |
            (Product.description.ilike(f'%{query}%')) |
            (Product.category.ilike(f'%{query}%'))
        ).all()
        
        return jsonify({
            'products': [product.to_dict() for product in products],
            'query': query
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<int:product_id>/validate', methods=['POST'])
@jwt_required()
def validate_product(product_id):
    """Validate product data"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        errors = product.validate()
        
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_product_stats():
    """Get product statistics"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        total_products = Product.query.count()
        
        # Get products by category
        products_by_category = db.session.query(
            Product.category,
            db.func.count(Product.id).label('count')
        ).group_by(Product.category).all()
        
        # Get average rate by category
        avg_rate_by_category = db.session.query(
            Product.category,
            db.func.avg(Product.rate).label('avg_rate')
        ).group_by(Product.category).all()
        
        # Get products with highest and lowest rates
        highest_rate_product = Product.query.order_by(Product.rate.desc()).first()
        lowest_rate_product = Product.query.order_by(Product.rate.asc()).first()
        
        return jsonify({
            'total_products': total_products,
            'products_by_category': [
                {'category': category, 'count': count}
                for category, count in products_by_category
            ],
            'avg_rate_by_category': [
                {'category': category, 'avg_rate': float(avg_rate) if avg_rate else 0}
                for category, avg_rate in avg_rate_by_category
            ],
            'highest_rate_product': highest_rate_product.to_dict() if highest_rate_product else None,
            'lowest_rate_product': lowest_rate_product.to_dict() if lowest_rate_product else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/bulk-update', methods=['POST'])
@jwt_required()
def bulk_update_products():
    """Bulk update products"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        
        if not data or 'products' not in data:
            return jsonify({'error': 'No products data provided'}), 400
        
        updated_count = 0
        errors = []
        
        for product_data in data['products']:
            try:
                product_id = product_data.get('id')
                if not product_id:
                    errors.append({'product': product_data, 'error': 'Product ID is required'})
                    continue
                
                product = Product.query.get(product_id)
                if not product:
                    errors.append({'product_id': product_id, 'error': 'Product not found'})
                    continue
                
                # Update fields
                allowed_fields = ['category', 'name', 'description', 'unit', 'rate', 'hsn_code']
                for field in allowed_fields:
                    if field in product_data:
                        setattr(product, field, product_data[field])
                
                product.updated_at = datetime.utcnow()
                
                # Validate
                validation_errors = product.validate()
                if validation_errors:
                    errors.append({'product_id': product_id, 'errors': validation_errors})
                    continue
                
                updated_count += 1
                
            except Exception as e:
                errors.append({'product_id': product_id, 'error': str(e)})
        
        if updated_count > 0:
            db.session.commit()
        
        return jsonify({
            'message': f'Successfully updated {updated_count} products',
            'updated_count': updated_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@product_bp.route('/export', methods=['GET'])
@jwt_required()
def export_products():
    """Export products to CSV"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        products = Product.query.all()
        
        # Prepare CSV data
        csv_data = []
        csv_data.append([
            'ID', 'Category', 'Name', 'Description', 'Unit', 'Rate', 'HSN Code', 'Created At'
        ])
        
        for product in products:
            csv_data.append([
                product.id,
                product.category or '',
                product.name,
                product.description or '',
                product.unit,
                float(product.rate) if product.rate else 0,
                product.hsn_code or '',
                product.created_at.strftime('%Y-%m-%d %H:%M:%S') if product.created_at else ''
            ])
        
        return jsonify({
            'csv_data': csv_data,
            'filename': f'products_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/import', methods=['POST'])
@jwt_required()
def import_products():
    """Import products from CSV data"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        
        if not data or 'csv_data' not in data:
            return jsonify({'error': 'No CSV data provided'}), 400
        
        csv_data = data['csv_data']
        
        if not csv_data or len(csv_data) < 2:
            return jsonify({'error': 'Invalid CSV data'}), 400
        
        # Skip header row
        rows = csv_data[1:]
        
        imported_count = 0
        errors = []
        
        for i, row in enumerate(rows):
            try:
                if len(row) < 6:
                    errors.append({'row': i + 2, 'error': 'Insufficient columns'})
                    continue
                
                product = Product(
                    category=row[1] if row[1] else None,
                    name=row[2],
                    description=row[3] if row[3] else None,
                    unit=row[4] if row[4] else 'KG',
                    rate=float(row[5]) if row[5] else None,
                    hsn_code=row[6] if len(row) > 6 and row[6] else None
                )
                
                # Validate
                validation_errors = product.validate()
                if validation_errors:
                    errors.append({'row': i + 2, 'errors': validation_errors})
                    continue
                
                db.session.add(product)
                imported_count += 1
                
            except Exception as e:
                errors.append({'row': i + 2, 'error': str(e)})
        
        if imported_count > 0:
            db.session.commit()
        
        return jsonify({
            'message': f'Successfully imported {imported_count} products',
            'imported_count': imported_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
"""
Invoice Routes
Handles invoice management operations including items and calculations
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.invoice import Invoice, InvoiceItem
from database import db
from models.user import User
from models.company import Company
from models.customer import Customer
from models.product import Product
from datetime import datetime, date
from sqlalchemy import desc, func

invoice_bp = Blueprint('invoice', __name__)

@invoice_bp.route('', methods=['GET'])
@jwt_required()
def get_invoices():
    """Get all invoices"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get filter parameters
        status = request.args.get('status')
        customer_id = request.args.get('customer_id', type=int)
        company_id = request.args.get('company_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query
        query = Invoice.query
        
        if status:
            query = query.filter(Invoice.status == status)
        
        if customer_id:
            query = query.filter(Invoice.customer_id == customer_id)
        
        if company_id:
            query = query.filter(Invoice.company_id == company_id)
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Invoice.invoice_date >= date_from_obj)
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Invoice.invoice_date <= date_to_obj)
        
        # Order by date (newest first)
        query = query.order_by(desc(Invoice.invoice_date))
        
        # Apply pagination
        invoices_paginated = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'invoices': [invoice.to_dict() for invoice in invoices_paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': invoices_paginated.total,
                'pages': invoices_paginated.pages,
                'has_next': invoices_paginated.has_next,
                'has_prev': invoices_paginated.has_prev
            }
        }), 200
        
    except ValueError as e:
        return jsonify({'error': 'Invalid date format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@invoice_bp.route('/<int:invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice(invoice_id):
    """Get specific invoice"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        invoice = Invoice.query.get(invoice_id)
        
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404
        
        return jsonify({'invoice': invoice.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@invoice_bp.route('', methods=['POST'])
@jwt_required()
def create_invoice():
    """Create new invoice"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Generate invoice number if not provided
        if not data.get('invoice_number'):
            data['invoice_number'] = Invoice.generate_invoice_number()
        
        try:
            # Create invoice from data with proper error handling
            invoice = Invoice.from_dict(data)
        except ValueError as e:
            return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
        
        # Validate invoice data
        errors = invoice.validate()
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        # Save invoice to database
        db.session.add(invoice)
        db.session.flush()  # Get the invoice ID
        
        # Add items if provided
        if 'items' in data:
            for item_data in data['items']:
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=item_data.get('product_id'),
                    description=item_data.get('description'),
                    quantity=item_data.get('quantity'),
                    unit=item_data.get('unit'),
                    rate=item_data.get('rate'),
                    discount_percent=item_data.get('discount_percent', 0)
                )
                item.calculate_amount()
                db.session.add(item)
        
        # Calculate totals
        invoice.calculate_totals()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Invoice created successfully',
            'invoice': invoice.to_dict()
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': 'Invalid date format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@invoice_bp.route('/<int:invoice_id>', methods=['PUT'])
@jwt_required()
def update_invoice(invoice_id):
    """Update specific invoice"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        invoice = Invoice.query.get(invoice_id)
        
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404
        
        # Check if user can edit this invoice
        if not current_user.can_edit_invoice(invoice):
            return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update invoice fields
        allowed_fields = [
            'invoice_number', 'invoice_date', 'company_id', 'customer_id',
            'po_number', 'po_date', 'payment_mode', 'transport', 'dispatch_from', 'status'
        ]
        
        for field in allowed_fields:
            if field in data:
                if field == 'invoice_date' and isinstance(data[field], str):
                    setattr(invoice, field, datetime.strptime(data[field], '%Y-%m-%d').date())
                elif field == 'po_date' and isinstance(data[field], str):
                    setattr(invoice, field, datetime.strptime(data[field], '%Y-%m-%d').date())
                else:
                    setattr(invoice, field, data[field])
        
        invoice.updated_at = datetime.utcnow()
        
        # Validate updated invoice
        errors = invoice.validate()
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        # Update items if provided
        if 'items' in data:
            # Remove existing items
            InvoiceItem.query.filter_by(invoice_id=invoice.id).delete()
            
            # Add new items
            for item_data in data['items']:
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=item_data.get('product_id'),
                    description=item_data.get('description'),
                    quantity=item_data.get('quantity'),
                    unit=item_data.get('unit'),
                    rate=item_data.get('rate'),
                    discount_percent=item_data.get('discount_percent', 0)
                )
                item.calculate_amount()
                db.session.add(item)
            
            # Flush to ensure items are saved before calculating totals
            db.session.flush()
        
        # Recalculate totals
        invoice.calculate_totals()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Invoice updated successfully',
            'invoice': invoice.to_dict()
        }), 200
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': 'Invalid date format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@invoice_bp.route('/<int:invoice_id>', methods=['DELETE'])
@jwt_required()
def delete_invoice(invoice_id):
    """Delete specific invoice"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        invoice = Invoice.query.get(invoice_id)
        
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404
        
        # Check if user can delete this invoice
        if not current_user.can_delete_invoice(invoice):
            return jsonify({'error': 'Permission denied'}), 403
        
        db.session.delete(invoice)
        db.session.commit()
        
        return jsonify({'message': 'Invoice deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@invoice_bp.route('/<int:invoice_id>/items', methods=['GET'])
@jwt_required()
def get_invoice_items(invoice_id):
    """Get all items for specific invoice"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        invoice = Invoice.query.get(invoice_id)
        
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404
        
        items = InvoiceItem.query.filter_by(invoice_id=invoice_id).all()
        
        return jsonify({
            'items': [item.to_dict() for item in items]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@invoice_bp.route('/<int:invoice_id>/items', methods=['POST'])
@jwt_required()
def add_invoice_item(invoice_id):
    """Add item to invoice"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        invoice = Invoice.query.get(invoice_id)
        
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404
        
        # Check if user can edit this invoice
        if not current_user.can_edit_invoice(invoice):
            return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create item
        item = InvoiceItem(
            invoice_id=invoice_id,
            product_id=data.get('product_id'),
            description=data.get('description'),
            quantity=data.get('quantity'),
            unit=data.get('unit'),
            rate=data.get('rate'),
            discount_percent=data.get('discount_percent', 0)
        )
        
        # Validate item
        errors = item.validate()
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        item.calculate_amount()
        db.session.add(item)
        
        # Recalculate invoice totals
        invoice.calculate_totals()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Item added successfully',
            'item': item.to_dict(),
            'invoice': invoice.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@invoice_bp.route('/<int:invoice_id>/items/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_invoice_item(invoice_id, item_id):
    """Update specific invoice item"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        invoice = Invoice.query.get(invoice_id)
        
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404
        
        # Check if user can edit this invoice
        if not current_user.can_edit_invoice(invoice):
            return jsonify({'error': 'Permission denied'}), 403
        
        item = InvoiceItem.query.get(item_id)
        
        if not item or item.invoice_id != invoice_id:
            return jsonify({'error': 'Item not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update item fields
        allowed_fields = [
            'product_id', 'description', 'quantity', 'unit', 'rate', 'discount_percent'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(item, field, data[field])
        
        # Validate updated item
        errors = item.validate()
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        item.calculate_amount()
        
        # Recalculate invoice totals
        invoice.calculate_totals()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Item updated successfully',
            'item': item.to_dict(),
            'invoice': invoice.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@invoice_bp.route('/<int:invoice_id>/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_invoice_item(invoice_id, item_id):
    """Delete specific invoice item"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        invoice = Invoice.query.get(invoice_id)
        
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404
        
        # Check if user can edit this invoice
        if not current_user.can_edit_invoice(invoice):
            return jsonify({'error': 'Permission denied'}), 403
        
        item = InvoiceItem.query.get(item_id)
        
        if not item or item.invoice_id != invoice_id:
            return jsonify({'error': 'Item not found'}), 404
        
        db.session.delete(item)
        
        # Recalculate invoice totals
        invoice.calculate_totals()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Item deleted successfully',
            'invoice': invoice.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@invoice_bp.route('/<int:invoice_id>/calculate', methods=['POST'])
@jwt_required()
def calculate_invoice_totals(invoice_id):
    """Recalculate invoice totals"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        invoice = Invoice.query.get(invoice_id)
        
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404
        
        # Recalculate all item amounts
        for item in invoice.items:
            item.calculate_amount()
        
        # Calculate invoice totals
        invoice.calculate_totals()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Invoice totals calculated successfully',
            'invoice': invoice.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@invoice_bp.route('/<int:invoice_id>/status', methods=['PUT'])
@jwt_required()
def update_invoice_status(invoice_id):
    """Update invoice status"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        invoice = Invoice.query.get(invoice_id)
        
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404
        
        data = request.get_json()
        
        if not data or 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
        
        new_status = data['status']
        
        if new_status not in ['DRAFT', 'SENT', 'PAID', 'CANCELLED']:
            return jsonify({'error': 'Invalid status'}), 400
        
        invoice.status = new_status
        invoice.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Invoice status updated successfully',
            'invoice': invoice.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@invoice_bp.route('/next-number', methods=['GET'])
@jwt_required()
def get_next_invoice_number():
    """Get next invoice number"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        next_number = Invoice.generate_invoice_number()
        
        return jsonify({'next_invoice_number': next_number}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@invoice_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_invoice_stats():
    """Get invoice statistics"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Basic counts
        total_invoices = Invoice.query.count()
        draft_invoices = Invoice.query.filter_by(status='DRAFT').count()
        sent_invoices = Invoice.query.filter_by(status='SENT').count()
        paid_invoices = Invoice.query.filter_by(status='PAID').count()
        cancelled_invoices = Invoice.query.filter_by(status='CANCELLED').count()
        
        # Total amounts
        total_amount = db.session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.status != 'CANCELLED'
        ).scalar() or 0
        
        paid_amount = db.session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.status == 'PAID'
        ).scalar() or 0
        
        pending_amount = db.session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.status == 'SENT'
        ).scalar() or 0
        
        # Monthly stats (current year)
        current_year = datetime.now().year
        monthly_stats = db.session.query(
            func.extract('month', Invoice.invoice_date).label('month'),
            func.count(Invoice.id).label('count'),
            func.sum(Invoice.total_amount).label('total')
        ).filter(
            func.extract('year', Invoice.invoice_date) == current_year,
            Invoice.status != 'CANCELLED'
        ).group_by(func.extract('month', Invoice.invoice_date)).all()
        
        return jsonify({
            'total_invoices': total_invoices,
            'status_breakdown': {
                'draft': draft_invoices,
                'sent': sent_invoices,
                'paid': paid_invoices,
                'cancelled': cancelled_invoices
            },
            'amounts': {
                'total': float(total_amount),
                'paid': float(paid_amount),
                'pending': float(pending_amount)
            },
            'monthly_stats': [
                {
                    'month': int(month),
                    'count': count,
                    'total': float(total or 0)
                }
                for month, count, total in monthly_stats
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@invoice_bp.route('/search', methods=['GET'])
@jwt_required()
def search_invoices():
    """Search invoices"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        query = request.args.get('q', '')
        
        if not query:
            return jsonify({'invoices': []}), 200
        
        # Search in invoice number and PO number
        invoices = Invoice.query.filter(
            (Invoice.invoice_number.ilike(f'%{query}%')) |
            (Invoice.po_number.ilike(f'%{query}%'))
        ).order_by(desc(Invoice.invoice_date)).all()
        
        return jsonify({
            'invoices': [invoice.to_dict() for invoice in invoices],
            'query': query
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@invoice_bp.route('/duplicate/<int:invoice_id>', methods=['POST'])
@jwt_required()
def duplicate_invoice(invoice_id):
    """Duplicate an existing invoice"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        original_invoice = Invoice.query.get(invoice_id)
        
        if not original_invoice:
            return jsonify({'error': 'Invoice not found'}), 404
        
        # Create new invoice with same data
        new_invoice = Invoice(
            invoice_number=Invoice.generate_invoice_number(),
            invoice_date=date.today(),
            company_id=original_invoice.company_id,
            customer_id=original_invoice.customer_id,
            po_number=original_invoice.po_number,
            po_date=original_invoice.po_date,
            payment_mode=original_invoice.payment_mode,
            transport=original_invoice.transport,
            dispatch_from=original_invoice.dispatch_from,
            status='DRAFT'
        )
        
        db.session.add(new_invoice)
        db.session.flush()
        
        # Copy items
        for original_item in original_invoice.items:
            new_item = InvoiceItem(
                invoice_id=new_invoice.id,
                product_id=original_item.product_id,
                description=original_item.description,
                quantity=original_item.quantity,
                unit=original_item.unit,
                rate=original_item.rate,
                discount_percent=original_item.discount_percent
            )
            new_item.calculate_amount()
            db.session.add(new_item)
        
        # Calculate totals
        new_invoice.calculate_totals()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Invoice duplicated successfully',
            'invoice': new_invoice.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
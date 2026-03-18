"""
Shared POS API routes for both admin and employee
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import db, Product, Category, ProductVariant, Order, OrderItem, User, Employee
from werkzeug.security import generate_password_hash
from datetime import datetime
import random

# Create separate blueprints for admin and employee to avoid name conflicts
admin_pos_api_bp = Blueprint('admin_pos_api', __name__)
employee_pos_api_bp = Blueprint('employee_pos_api', __name__)


def register_pos_routes(bp):
    """Register POS routes to a blueprint"""
    
    @bp.route('/api/products')
    @login_required
    def api_products():
        """API to get products for POS"""
        try:
            category_id = request.args.get('category_id', type=int)
            
            query = Product.query.filter_by(is_active=True)
            if category_id:
                query = query.filter_by(category_id=category_id)
            
            products = query.all()
            
            products_data = []
            for product in products:
                variants = ProductVariant.query.filter_by(product_id=product.id).all()
                products_data.append({
                    'id': product.id,
                    'name': product.name,
                    'brand': product.brand.name if product.brand else 'Unknown',
                    'price': float(product.price),
                    'image': product.image_filename,
                    'category': product.category.name if product.category else 'Unknown',
                    'variants': [
                        {
                            'id': variant.id,
                            'size': variant.size,
                            'stock_quantity': variant.stock_quantity,
                            'barcode': variant.barcode
                        }
                        for variant in variants
                    ]
                })
            
            return jsonify({'success': True, 'products': products_data})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/api/categories')
    @login_required
    def api_categories():
        """API to get categories for POS"""
        try:
            categories = Category.query.all()
            return jsonify({
                'success': True,
                'categories': [
                    {'id': cat.id, 'name': cat.name}
                    for cat in categories
                ]
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/api/pos/complete-sale', methods=['POST'])
    @login_required
    def complete_pos_sale():
        """Complete a POS sale"""
        try:
            data = request.get_json()
            
            cart_items = data.get('cart_items', [])
            customer_id = data.get('customer_id')
            customer_name = data.get('customer_name', 'Walk-in Customer')
            employee_code = data.get('employee_code')
            subtotal = data.get('subtotal', 0)
            tax = data.get('tax', 0)
            total_amount = data.get('total_amount')
            
            if not cart_items:
                return jsonify({'success': False, 'error': 'Cart is empty'}), 400
            
            # Generate order number
            order_number = f"POS-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            
            # Create or get walk-in customer
            if not customer_id and customer_name == 'Walk-in Customer':
                walkin = User.query.filter_by(username='walkin').first()
                if not walkin:
                    walkin = User(
                        username='walkin',
                        email='walkin@mbmaniyar.local',
                        full_name='Walk-in Customer',
                        password_hash=generate_password_hash('walkin123'),
                        role='customer'
                    )
                    db.session.add(walkin)
                    db.session.flush()
                customer_id = walkin.id
            
            # Create POS order
            order = Order(
                order_number=order_number,
                user_id=customer_id,
                order_type='pos',
                status='completed',
                subtotal=subtotal,
                tax_amount=tax,
                total_amount=total_amount,
                payment_method='cash',
                payment_status='paid',
                processed_by_id=current_user.id,
                customer_notes=f"Employee code: {employee_code}" if employee_code else None
            )
            
            db.session.add(order)
            db.session.flush()  # Get order ID
            
            # Add order items
            for item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['product_id'],
                    variant_id=item['variant_id'],
                    quantity=item['quantity'],
                    unit_price=item['price'],
                    total_price=item['price'] * item['quantity']
                )
                db.session.add(order_item)
                
                # Update stock
                variant = ProductVariant.query.get(item['variant_id'])
                if variant and variant.stock_quantity >= item['quantity']:
                    variant.stock_quantity -= item['quantity']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'order_number': order_number,
                'message': 'Sale completed successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/api/customer/lookup', methods=['POST'])
    @login_required
    def lookup_customer():
        """Lookup customer by phone number"""
        try:
            data = request.get_json()
            phone_number = data.get('phone', '').strip()
            
            if not phone_number:
                return jsonify({
                    'success': False,
                    'error': 'Phone number is required'
                }), 400
            
            # Validate phone number (should be 10 digits)
            clean_phone = ''.join(filter(str.isdigit, phone_number))
            if len(clean_phone) < 10:
                return jsonify({
                    'success': False,
                    'error': 'Please enter a valid 10-digit phone number'
                }), 400
            
            # Get customer insights
            from app.customer_insights import get_customer_insights_by_phone
            insights = get_customer_insights_by_phone(phone_number)
            
            if not insights:
                return jsonify({
                    'success': False,
                    'error': 'Customer not found with this phone number'
                }), 404
            
            return jsonify({
                'success': True,
                'customer': insights
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'An error occurred while looking up customer'
            }), 500

# Register routes to both blueprints
register_pos_routes(admin_pos_api_bp)
register_pos_routes(employee_pos_api_bp)

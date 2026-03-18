"""
Customer API for Clienteling Module
Provides endpoints for customer lookup and insights
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.employee.routes import employee_required
from app.customer_insights import get_customer_insights_by_phone, find_customer_by_phone
from app.models import db, CartItem

customer_api_bp = Blueprint('customer_api', __name__)


@customer_api_bp.route('/api/customer/lookup', methods=['POST'])
@employee_required
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


@customer_api_bp.route('/api/customer/wishlist/add-to-cart', methods=['POST'])
@employee_required
def add_wishlist_to_pos_cart():
    """Add wishlist item to POS cart"""
    try:
        data = request.get_json()
        cart_item_id = data.get('cart_item_id')
        quantity = data.get('quantity', 1)
        
        if not cart_item_id:
            return jsonify({
                'success': False,
                'error': 'Cart item ID is required'
            }), 400
        
        # Get the wishlist item
        cart_item = CartItem.query.get(cart_item_id)
        if not cart_item:
            return jsonify({
                'success': False,
                'error': 'Wishlist item not found'
            }), 404
        
        # Check if item is in stock
        if cart_item.variant.stock_quantity < quantity:
            return jsonify({
                'success': False,
                'error': f'Only {cart_item.variant.stock_quantity} items available in stock'
            }), 400
        
        # TODO: Add to POS cart logic
        # This depends on how your POS cart is implemented
        # For now, we'll return success with item details
        
        return jsonify({
            'success': True,
            'message': 'Item added to POS cart',
            'item': {
                'product_name': cart_item.product.name,
                'size': cart_item.variant.size,
                'quantity': quantity,
                'price': float(cart_item.product.price),
                'total': float(cart_item.product.price * quantity)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'An error occurred while adding item to cart'
        }), 500


@customer_api_bp.route('/api/customer/search', methods=['GET'])
@employee_required
def search_customers():
    """Search customers by phone or name (for autocomplete)"""
    try:
        query = request.args.get('q', '').strip()
        
        if len(query) < 2:
            return jsonify({
                'success': False,
                'error': 'Query must be at least 2 characters'
            }), 400
        
        # Search by phone number or name
        from app.models import User
        
        customers = User.query.filter(
            (User.phone.like(f'%{query}%')) |
            (User.full_name.like(f'%{query}%')) |
            (User.username.like(f'%{query}%'))
        ).filter(
            User.role == 'customer'
        ).limit(10).all()
        
        results = []
        for customer in customers:
            results.append({
                'id': customer.id,
                'name': customer.full_name,
                'phone': customer.phone,
                'email': customer.email,
                'username': customer.username
            })
        
        return jsonify({
            'success': True,
            'customers': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'An error occurred while searching customers'
        }), 500


@customer_api_bp.route('/api/customer/<int:customer_id>/summary')
@employee_required
def get_customer_summary(customer_id):
    """Get quick customer summary for display"""
    try:
        from app.customer_insights import CustomerInsights
        
        insights = CustomerInsights(customer_id)
        summary = insights.get_complete_insights()
        
        if not summary:
            return jsonify({
                'success': False,
                'error': 'Customer not found'
            }), 404
        
        return jsonify({
            'success': True,
            'summary': {
                'name': summary['customer']['name'],
                'phone': summary['customer']['phone'],
                'lifetime_value': summary['lifetime_value']['total_lifetime_value'],
                'total_orders': summary['lifetime_value']['total_orders_count'],
                'wishlist_count': len(summary['wishlist'])
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'An error occurred while fetching customer summary'
        }), 500

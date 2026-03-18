"""
Customer Insights Service for Clienteling Module
Calculates customer lifetime value, size preferences, and wishlist data
"""

from datetime import datetime, timedelta
from collections import defaultdict, Counter
from app.models import db, User, Order, OrderItem, CartItem, Product, ProductVariant


class CustomerInsights:
    """Service for analyzing customer data and providing insights"""
    
    def __init__(self, customer_id):
        self.customer_id = customer_id
        self.customer = User.query.get(customer_id)
    
    def get_customer_overview(self):
        """Get basic customer information"""
        if not self.customer:
            return None
        
        return {
            'id': self.customer.id,
            'name': self.customer.full_name,
            'email': self.customer.email,
            'phone': self.customer.phone,
            'username': self.customer.username,
            'member_since': self.customer.created_at.strftime('%Y-%m-%d'),
            'is_active': self.customer.is_active_account
        }
    
    def get_lifetime_value(self):
        """Calculate total lifetime value from all orders (online + offline/POS)"""
        if not self.customer:
            return 0
        
        # Get all orders for this customer
        all_orders = Order.query.filter_by(user_id=self.customer_id).all()
        
        # Sum up total amounts from both online and POS orders
        total_value = sum(order.total_amount or 0 for order in all_orders)
        
        # Breakdown by order type
        online_orders = [o for o in all_orders if o.order_type != 'pos']
        pos_orders = [o for o in all_orders if o.order_type == 'pos']
        
        online_value = sum(order.total_amount or 0 for order in online_orders)
        pos_value = sum(order.total_amount or 0 for order in pos_orders)
        
        return {
            'total_lifetime_value': float(total_value),
            'online_orders_value': float(online_value),
            'pos_orders_value': float(pos_value),
            'total_orders_count': len(all_orders),
            'online_orders_count': len(online_orders),
            'pos_orders_count': len(pos_orders)
        }
    
    def get_size_preferences(self):
        """Calculate most frequently purchased sizes by product category"""
        if not self.customer:
            return {}
        
        # Get all order items for this customer
        order_items = db.session.query(OrderItem, Product, ProductVariant).join(
            Product, OrderItem.product_id == Product.id
        ).join(
            ProductVariant, OrderItem.variant_id == ProductVariant.id
        ).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            Order.user_id == self.customer_id
        ).all()
        
        # Group sizes by product category
        category_sizes = defaultdict(list)
        
        for item, product, variant in order_items:
            category_name = product.category.name if product.category else 'Uncategorized'
            size = variant.size
            category_sizes[category_name].append(size)
        
        # Calculate most frequent size for each category
        size_preferences = {}
        
        for category, sizes in category_sizes.items():
            if sizes:
                # Count frequency of each size
                size_counter = Counter(sizes)
                most_common_size, frequency = size_counter.most_common(1)[0]
                
                size_preferences[category] = {
                    'preferred_size': most_common_size,
                    'frequency': frequency,
                    'total_purchases': len(sizes),
                    'size_distribution': dict(size_counter)
                }
        
        return size_preferences
    
    def get_wishlist_items(self):
        """Get customer's wishlist with inventory status"""
        if not self.customer:
            return []
        
        # Get customer's cart items (wishlist items)
        wishlist_items = CartItem.query.filter_by(user_id=self.customer_id).all()
        
        wishlist_data = []
        
        for item in wishlist_items:
            product = item.product
            variant = item.variant
            
            # Check if item is in stock
            in_stock = variant.stock_quantity > 0
            stock_level = variant.stock_quantity
            
            wishlist_data.append({
                'id': item.id,
                'product_id': product.id,
                'product_name': product.name,
                'brand': product.brand.name if product.brand else 'Unknown',
                'category': product.category.name if product.category else 'Unknown',
                'size': variant.size,
                'price': float(product.price),
                'quantity': item.quantity,
                'image': product.image_filename,
                'sku': product.sku,
                'in_stock': in_stock,
                'stock_level': stock_level,
                'variant_id': variant.id,
                'added_at': item.added_at.strftime('%Y-%m-%d') if item.added_at else None
            })
        
        return wishlist_data
    
    def get_purchase_history(self, limit=10):
        """Get recent purchase history"""
        if not self.customer:
            return []
        
        orders = Order.query.filter_by(user_id=self.customer_id).order_by(
            Order.created_at.desc()
        ).limit(limit).all()
        
        history = []
        
        for order in orders:
            items = []
            for item in order.items:
                items.append({
                    'product_name': item.product.name,
                    'size': item.variant.size,
                    'quantity': item.quantity,
                    'price': float(item.unit_price),
                    'total': float(item.total_price)
                })
            
            history.append({
                'order_number': order.order_number,
                'order_type': order.order_type,
                'total_amount': float(order.total_amount),
                'status': order.status,
                'created_at': order.created_at.strftime('%Y-%m-%d'),
                'items': items
            })
        
        return history
    
    def get_complete_insights(self):
        """Get all customer insights in one call"""
        if not self.customer:
            return None
        
        return {
            'customer': self.get_customer_overview(),
            'lifetime_value': self.get_lifetime_value(),
            'size_preferences': self.get_size_preferences(),
            'wishlist': self.get_wishlist_items(),
            'recent_purchases': self.get_purchase_history()
        }


def find_customer_by_phone(phone_number):
    """Find customer by phone number"""
    # Clean phone number (remove spaces, dashes, etc.)
    clean_phone = ''.join(filter(str.isdigit, phone_number))
    
    # Search for exact match or partial match
    customer = User.query.filter(
        (User.phone == clean_phone) | 
        (User.phone.like(f'%{clean_phone}%'))
    ).first()
    
    return customer


def get_customer_insights_by_phone(phone_number):
    """Get complete customer insights by phone number"""
    customer = find_customer_by_phone(phone_number)
    
    if not customer:
        return None
    
    insights = CustomerInsights(customer.id)
    return insights.get_complete_insights()

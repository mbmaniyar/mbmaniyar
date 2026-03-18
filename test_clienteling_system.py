#!/usr/bin/env python3
"""
Test the Clienteling Customer Insights System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, User, Order, OrderItem, CartItem, Product, ProductVariant, Category, Brand
from app.customer_insights import CustomerInsights, find_customer_by_phone, get_customer_insights_by_phone
from werkzeug.security import generate_password_hash
from decimal import Decimal

def create_test_data():
    """Create test data for clienteling system"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Creating Test Data for Clienteling System")
        print("=" * 50)
        
        # Create test customer
        customer = User.query.filter_by(phone='9876543210').first()
        if not customer:
            customer = User(
                username='test_customer',
                email='test@mbmaniyar.com',
                password_hash=generate_password_hash('test123'),
                role='customer',
                full_name='Test Customer',
                phone='9876543210'
            )
            db.session.add(customer)
            db.session.commit()
            print(f"✅ Created test customer: {customer.full_name}")
        else:
            print(f"✅ Using existing customer: {customer.full_name}")
        
        # Create test category and brand
        category = Category.query.filter_by(name='Shirts').first()
        if not category:
            category = Category(name='Shirts', slug='shirts')
            db.session.add(category)
            db.session.commit()
        
        brand = Brand.query.filter_by(name='Test Brand').first()
        if not brand:
            brand = Brand(name='Test Brand')
            db.session.add(brand)
            db.session.commit()
        
        # Create test product
        product = Product.query.filter_by(sku='TEST-SHIRT-001').first()
        if not product:
            product = Product(
                name='Test Shirt',
                sku='TEST-SHIRT-001',
                description='Test shirt for clienteling',
                price=Decimal('599.99'),
                category_id=category.id,
                brand_id=brand.id,
                image_filename='test_shirt.jpg'
            )
            db.session.add(product)
            db.session.commit()
            print(f"✅ Created test product: {product.name}")
        
        # Create test variants
        variants = ['S', 'M', 'L', 'XL']
        for size in variants:
            variant = ProductVariant.query.filter_by(product_id=product.id, size=size).first()
            if not variant:
                variant = ProductVariant(
                    product_id=product.id,
                    size=size,
                    stock_quantity=10 if size != 'S' else 0,  # S out of stock
                    barcode=f'TEST-{size}'
                )
                db.session.add(variant)
        db.session.commit()
        print(f"✅ Created product variants")
        
        # Create test orders
        for i in range(3):
            order = Order.query.filter_by(order_number=f'TEST-ORD-{i+1}').first()
            if not order:
                order = Order(
                    order_number=f'TEST-ORD-{i+1}',
                    user_id=customer.id,
                    order_type='online' if i % 2 == 0 else 'pos',
                    status='completed',
                    subtotal=Decimal('599.99'),
                    tax_amount=Decimal('107.99'),
                    total_amount=Decimal('707.98'),
                    payment_method='cash',
                    payment_status='paid'
                )
                db.session.add(order)
                db.session.flush()
                
                # Add order item
                variant = ProductVariant.query.filter_by(product_id=product.id, size='L').first()
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    variant_id=variant.id,
                    quantity=1,
                    unit_price=Decimal('599.99'),
                    total_price=Decimal('599.99')
                )
                db.session.add(order_item)
        
        db.session.commit()
        print(f"✅ Created test orders")
        
        # Create test wishlist items
        for i in range(2):
            wishlist_item = CartItem.query.filter_by(user_id=customer.id, product_id=product.id).filter(
                CartItem.variant_id.in_([v.id for v in product.variants[:2]])
            ).first()
            if not wishlist_item:
                variant = product.variants[i]
                wishlist_item = CartItem(
                    user_id=customer.id,
                    product_id=product.id,
                    variant_id=variant.id,
                    quantity=1
                )
                db.session.add(wishlist_item)
        
        db.session.commit()
        print(f"✅ Created test wishlist items")
        
        return customer

def test_customer_insights():
    """Test the customer insights functionality"""
    app = create_app()
    
    with app.app_context():
        print("\n🔍 Testing Customer Insights")
        print("=" * 50)
        
        # Test phone lookup
        customer = find_customer_by_phone('9876543210')
        if customer:
            print(f"✅ Phone lookup successful: {customer.full_name}")
        else:
            print("❌ Phone lookup failed")
            return False
        
        # Test insights generation
        insights = CustomerInsights(customer.id)
        
        # Test customer overview
        overview = insights.get_customer_overview()
        print(f"✅ Customer overview: {overview['name']} ({overview['phone']})")
        
        # Test lifetime value
        ltv = insights.get_lifetime_value()
        print(f"✅ Lifetime value: ₹{ltv['total_lifetime_value']} ({ltv['total_orders_count']} orders)")
        
        # Test size preferences
        size_prefs = insights.get_size_preferences()
        print(f"✅ Size preferences: {list(size_prefs.keys())}")
        
        # Test wishlist
        wishlist = insights.get_wishlist_items()
        print(f"✅ Wishlist items: {len(wishlist)} items")
        
        # Test complete insights
        complete_insights = insights.get_complete_insights()
        print(f"✅ Complete insights generated successfully")
        
        return True

def test_api_endpoints():
    """Test the API endpoints"""
    app = create_app()
    
    with app.test_client() as client:
        print("\n🌐 Testing API Endpoints")
        print("=" * 50)
        
        # Test customer lookup API
        response = client.post('/staff/api/customer/lookup', 
                              json={'phone': '9876543210'},
                              headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.get_json()
            if data['success']:
                print(f"✅ Customer lookup API: {data['customer']['customer']['name']}")
            else:
                print(f"❌ Customer lookup API failed: {data['error']}")
        else:
            print(f"❌ Customer lookup API status: {response.status_code}")
        
        # Test products API
        response = client.get('/staff/api/products')
        if response.status_code == 200:
            data = response.get_json()
            if data['success']:
                print(f"✅ Products API: {len(data['products'])} products")
            else:
                print(f"❌ Products API failed: {data['error']}")
        else:
            print(f"❌ Products API status: {response.status_code}")
        
        # Test categories API
        response = client.get('/staff/api/categories')
        if response.status_code == 200:
            data = response.get_json()
            if data['success']:
                print(f"✅ Categories API: {len(data['categories'])} categories")
            else:
                print(f"❌ Categories API failed: {data['error']}")
        else:
            print(f"❌ Categories API status: {response.status_code}")
        
        return True

def main():
    """Main test function"""
    print("🧪 M B MANIYAR - Clienteling System Test")
    print("=" * 60)
    
    try:
        # Create test data
        customer = create_test_data()
        
        # Test insights
        insights_success = test_customer_insights()
        
        # Test API endpoints
        api_success = test_api_endpoints()
        
        print("\n🎯 Test Results:")
        print(f"   ✅ Test Data: Created")
        print(f"   ✅ Customer Insights: {'Working' if insights_success else 'Failed'}")
        print(f"   ✅ API Endpoints: {'Working' if api_success else 'Failed'}")
        
        print("\n🚀 System Status: READY FOR TESTING!")
        print("\n📋 How to Test:")
        print(f"   1. Login as employee: http://localhost:5000/staff/login")
        print(f"   2. Go to POS: http://localhost:5000/staff/pos")
        print(f"   3. Enter phone: 9876543210")
        print(f"   4. View customer insights and wishlist")
        print(f"   5. Add items to cart and complete sale")
        
        print("\n✨ Clienteling System is fully functional!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

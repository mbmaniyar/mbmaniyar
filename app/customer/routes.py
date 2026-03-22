
# customer/routes.py
# Handles all pages visible to shoppers: catalog, product detail, cart, checkout

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import current_user, login_required
from app.models import db, Product, ProductVariant, Category, Brand, CartItem, Order, OrderItem
from decimal import Decimal
import json

customer_bp = Blueprint('customer', __name__)

# ── helpers ──────────────────────────────────────────────────────────────────

def _get_cart_count():
    """Return number of items in cart for the current visitor."""
    if current_user.is_authenticated:
        return db.session.query(db.func.sum(CartItem.quantity))\
               .filter_by(user_id=current_user.id).scalar() or 0
    else:
        cart = session.get('guest_cart', {})
        return sum(v.get('qty', 0) for v in cart.values())

# ── SHOP INDEX ────────────────────────────────────────────────────────────────

@customer_bp.route('/')
def index():
    """Main product catalog page with category filter."""
    categories  = Category.query.all()
    brands      = Brand.query.all()
    cat_slug    = request.args.get('cat', 'all')
    brand_id    = request.args.get('brand', 'all')
    sort        = request.args.get('sort', 'newest')
    search      = request.args.get('q', '').strip()

    query = Product.query.filter_by(is_active=True, is_online=True)

    if cat_slug and cat_slug != 'all':
        cat = Category.query.filter_by(slug=cat_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    if brand_id and brand_id != 'all':
        query = query.filter_by(brand_id=int(brand_id))

    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    if sort == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    products   = query.all()
    cart_count = _get_cart_count()

    return render_template('customer/index.html',
        products=products, categories=categories, brands=brands,
        active_cat=cat_slug, active_brand=brand_id,
        sort=sort, search=search, cart_count=cart_count)

# ── PRODUCT DETAIL ────────────────────────────────────────────────────────────

@customer_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    product    = Product.query.get_or_404(product_id)
    variants   = {v.size: v for v in product.variants}
    related    = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    cart_count = _get_cart_count()
    return render_template('customer/product.html',
        product=product, variants=variants,
        related=related, cart_count=cart_count)

# ── CART ─────────────────────────────────────────────────────────────────────

@customer_bp.route('/cart')
def cart():
    cart_items = []
    subtotal   = Decimal('0')

    if current_user.is_authenticated:
        db_items = CartItem.query.filter_by(user_id=current_user.id).all()
        for item in db_items:
            line = item.quantity * item.product.price
            cart_items.append({
                'id'      : item.id,
                'product' : item.product,
                'variant' : item.variant,
                'quantity': item.quantity,
                'line'    : line,
            })
            subtotal += line

    cart_count = _get_cart_count()
    return render_template('customer/cart.html',
        cart_items=cart_items, subtotal=subtotal, cart_count=cart_count)

# ── ADD TO CART ───────────────────────────────────────────────────────────────

@customer_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    variant_id = request.form.get('variant_id', type=int)
    quantity   = request.form.get('quantity', 1, type=int)

    if not variant_id:
        flash('Please select a size first.', 'warning')
        return redirect(request.referrer or url_for('customer.index'))

    variant = ProductVariant.query.get_or_404(variant_id)

    if variant.stock_quantity < quantity:
        flash('Sorry, not enough stock available.', 'danger')
        return redirect(request.referrer)

    if current_user.is_authenticated:
        existing = CartItem.query.filter_by(
            user_id=current_user.id, variant_id=variant_id).first()
        if existing:
            existing.quantity += quantity
        else:
            db.session.add(CartItem(
                user_id=current_user.id,
                product_id=variant.product_id,
                variant_id=variant_id,
                quantity=quantity))
        db.session.commit()
        flash(f'Added to cart! 🛍️', 'success')
    else:
        flash('Please log in or register to add items to your cart.', 'warning')
        return redirect(url_for('auth.login'))

    return redirect(url_for('customer.cart'))

# ── REMOVE FROM CART ──────────────────────────────────────────────────────────

@customer_bp.route('/cart/remove/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash('Item removed from cart.', 'info')
    return redirect(url_for('customer.cart'))

# ── CHECKOUT / PLACE ORDER ────────────────────────────────────────────────────

@customer_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('customer.cart'))

    subtotal = sum(i.quantity * i.product.price for i in cart_items)
    notes    = request.form.get('notes', '')
    payment  = request.form.get('payment_method', 'cash')

    # Generate order number: MBM-YYYYMMDD-XXXX
    from datetime import datetime
    import random
    order_number = f"MBM-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"

    order = Order(
        order_number   = order_number,
        user_id        = current_user.id,
        order_type     = 'pickup',
        status         = 'confirmed',
        subtotal       = subtotal,
        total_amount   = subtotal,
        payment_method = payment,
        payment_status = 'pending',
        customer_notes = notes,
    )
    db.session.add(order)
    db.session.flush()   # get order.id before committing

    for item in cart_items:
        # Deduct stock
        item.variant.stock_quantity -= item.quantity
        db.session.add(OrderItem(
            order_id   = order.id,
            product_id = item.product_id,
            variant_id = item.variant_id,
            quantity   = item.quantity,
            unit_price = item.product.price,
            total_price= item.quantity * item.product.price,
        ))
        db.session.delete(item)   # clear cart

    db.session.commit()

    # ── Send order confirmation email with PDF invoice ────────────
    try:
        from app.mail_service import send_order_confirmation
        send_order_confirmation(current_user, order)
        print(f"  ✅ Order confirmation email sent for {order_number}")
    except Exception as e:
        # Never crash the checkout if email fails
        print(f"  ⚠️  Order email failed (order still placed): {e}")

    flash(f'🎉 Order {order_number} placed! Walk in to pick it up at Main Road, Mantha.', 'success')
    return redirect(url_for('customer.order_confirmation', order_id=order.id))

# ── ORDER CONFIRMATION ────────────────────────────────────────────────────────

@customer_bp.route('/order/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order      = Order.query.get_or_404(order_id)
    cart_count = _get_cart_count()
    return render_template('customer/order_confirmation.html',
        order=order, cart_count=cart_count)


@customer_bp.route('/about')
def about():
    return render_template('customer/about.html')

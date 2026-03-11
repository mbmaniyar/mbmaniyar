import os

BASE = os.path.expanduser("~/Desktop/mbmaniyar")

# ─────────────────────────────────────────────
# FILE 1 — customer/routes.py
# ─────────────────────────────────────────────
routes = '''
# customer/routes.py
# Handles all pages visible to shoppers: catalog, product detail, cart, checkout

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import current_user, login_required
from app.models import db, Product, ProductVariant, Category, Brand, CartItem, Order, OrderItem
from decimal import Decimal
import json

customer_bp = Blueprint(\'customer\', __name__)

# ── helpers ──────────────────────────────────────────────────────────────────

def _get_cart_count():
    """Return number of items in cart for the current visitor."""
    if current_user.is_authenticated:
        return db.session.query(db.func.sum(CartItem.quantity))\\
               .filter_by(user_id=current_user.id).scalar() or 0
    else:
        cart = session.get(\'guest_cart\', {})
        return sum(v.get(\'qty\', 0) for v in cart.values())

# ── SHOP INDEX ────────────────────────────────────────────────────────────────

@customer_bp.route(\'/\')
def index():
    """Main product catalog page with category filter."""
    categories  = Category.query.all()
    brands      = Brand.query.all()
    cat_slug    = request.args.get(\'cat\', \'all\')
    brand_id    = request.args.get(\'brand\', \'all\')
    sort        = request.args.get(\'sort\', \'newest\')
    search      = request.args.get(\'q\', \'\').strip()

    query = Product.query.filter_by(is_active=True, is_online=True)

    if cat_slug and cat_slug != \'all\':
        cat = Category.query.filter_by(slug=cat_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    if brand_id and brand_id != \'all\':
        query = query.filter_by(brand_id=int(brand_id))

    if search:
        query = query.filter(Product.name.ilike(f\'%{search}%\'))

    if sort == \'price_low\':
        query = query.order_by(Product.price.asc())
    elif sort == \'price_high\':
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    products   = query.all()
    cart_count = _get_cart_count()

    return render_template(\'customer/index.html\',
        products=products, categories=categories, brands=brands,
        active_cat=cat_slug, active_brand=brand_id,
        sort=sort, search=search, cart_count=cart_count)

# ── PRODUCT DETAIL ────────────────────────────────────────────────────────────

@customer_bp.route(\'/product/<int:product_id>\')
def product_detail(product_id):
    product    = Product.query.get_or_404(product_id)
    variants   = {v.size: v for v in product.variants}
    related    = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    cart_count = _get_cart_count()
    return render_template(\'customer/product.html\',
        product=product, variants=variants,
        related=related, cart_count=cart_count)

# ── CART ─────────────────────────────────────────────────────────────────────

@customer_bp.route(\'/cart\')
def cart():
    cart_items = []
    subtotal   = Decimal(\'0\')

    if current_user.is_authenticated:
        db_items = CartItem.query.filter_by(user_id=current_user.id).all()
        for item in db_items:
            line = item.quantity * item.product.price
            cart_items.append({
                \'id\'      : item.id,
                \'product\' : item.product,
                \'variant\' : item.variant,
                \'quantity\': item.quantity,
                \'line\'    : line,
            })
            subtotal += line

    cart_count = _get_cart_count()
    return render_template(\'customer/cart.html\',
        cart_items=cart_items, subtotal=subtotal, cart_count=cart_count)

# ── ADD TO CART ───────────────────────────────────────────────────────────────

@customer_bp.route(\'/cart/add\', methods=[\'POST\'])
def add_to_cart():
    variant_id = request.form.get(\'variant_id\', type=int)
    quantity   = request.form.get(\'quantity\', 1, type=int)

    if not variant_id:
        flash(\'Please select a size first.\', \'warning\')
        return redirect(request.referrer or url_for(\'customer.index\'))

    variant = ProductVariant.query.get_or_404(variant_id)

    if variant.stock_quantity < quantity:
        flash(\'Sorry, not enough stock available.\', \'danger\')
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
        flash(f\'Added to cart! 🛍️\', \'success\')
    else:
        flash(\'Please log in or register to add items to your cart.\', \'warning\')
        return redirect(url_for(\'auth.login\'))

    return redirect(url_for(\'customer.cart\'))

# ── REMOVE FROM CART ──────────────────────────────────────────────────────────

@customer_bp.route(\'/cart/remove/<int:item_id>\')
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash(\'Item removed from cart.\', \'info\')
    return redirect(url_for(\'customer.cart\'))

# ── CHECKOUT / PLACE ORDER ────────────────────────────────────────────────────

@customer_bp.route(\'/checkout\', methods=[\'POST\'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash(\'Your cart is empty.\', \'warning\')
        return redirect(url_for(\'customer.cart\'))

    subtotal = sum(i.quantity * i.product.price for i in cart_items)
    notes    = request.form.get(\'notes\', \'\')
    payment  = request.form.get(\'payment_method\', \'cash\')

    # Generate order number: MBM-YYYYMMDD-XXXX
    from datetime import datetime
    import random
    order_number = f"MBM-{datetime.now().strftime(\'%Y%m%d\')}-{random.randint(1000,9999)}"

    order = Order(
        order_number   = order_number,
        user_id        = current_user.id,
        order_type     = \'pickup\',
        status         = \'confirmed\',
        subtotal       = subtotal,
        total_amount   = subtotal,
        payment_method = payment,
        payment_status = \'pending\',
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
    flash(f\'🎉 Order {order_number} placed! Walk in to pick it up at Main Road, Mantha.\', \'success\')
    return redirect(url_for(\'customer.order_confirmation\', order_id=order.id))

# ── ORDER CONFIRMATION ────────────────────────────────────────────────────────

@customer_bp.route(\'/order/<int:order_id>\')
@login_required
def order_confirmation(order_id):
    order      = Order.query.get_or_404(order_id)
    cart_count = _get_cart_count()
    return render_template(\'customer/order_confirmation.html\',
        order=order, cart_count=cart_count)
'''

with open(f"{BASE}/app/customer/routes.py", "w") as f:
    f.write(routes)
print("✅ customer/routes.py")

# ─────────────────────────────────────────────
# FILE 2 — templates/customer/index.html
# ─────────────────────────────────────────────
index_html = r'''{% extends 'base.html' %}
{% block title %}Shop{% endblock %}

{% block extra_css %}
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

:root{
  --ink:#1C1108;--sand:#F5EDD9;--rust:#B5451B;
  --jade:#1B6B4A;--navy:#0F1F3D;--fog:#EDE8DF;
  --gold:#C9922A;--gold2:#F0C060;
  --ff-disp:'Cormorant Garamond',Georgia,serif;
  --ff-body:'DM Sans',sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--ff-body);background:var(--sand);color:var(--ink)}

/* ── SHOP HERO BANNER ── */
.shop-hero{
  background:linear-gradient(105deg,var(--navy) 0%,#1a3560 50%,var(--rust) 100%);
  padding:4rem 0 3rem;position:relative;overflow:hidden;
}
.shop-hero::before{
  content:'';position:absolute;inset:0;
  background:url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}
.shop-hero-title{
  font-family:var(--ff-disp);font-size:clamp(2rem,5vw,4rem);
  color:#fff;line-height:1.1;font-weight:600;
}
.shop-hero-title em{color:var(--gold2);font-style:italic}
.shop-hero-sub{color:rgba(255,255,255,.6);font-size:.95rem;margin-top:.6rem;font-weight:300}
.search-bar-wrap{position:relative;max-width:460px}
.search-bar{
  width:100%;padding:.85rem 1rem .85rem 3rem;
  border:2px solid rgba(255,255,255,.2);border-radius:50px;
  background:rgba(255,255,255,.1);backdrop-filter:blur(8px);
  color:#fff;font-size:.95rem;font-family:var(--ff-body);
  transition:border-color .2s;outline:none;
}
.search-bar::placeholder{color:rgba(255,255,255,.5)}
.search-bar:focus{border-color:var(--gold2)}
.search-icon{position:absolute;left:1rem;top:50%;transform:translateY(-50%);color:rgba(255,255,255,.5)}
.cart-pill{
  display:inline-flex;align-items:center;gap:.5rem;
  background:var(--gold);color:#fff;font-weight:600;
  border-radius:50px;padding:.6rem 1.4rem;font-size:.9rem;
  text-decoration:none;transition:all .25s;box-shadow:0 4px 20px rgba(201,146,42,.4);
}
.cart-pill:hover{background:var(--gold2);color:var(--ink);transform:translateY(-2px)}
.cart-pill .badge-count{
  background:#fff;color:var(--rust);border-radius:50px;
  font-size:.75rem;padding:.1rem .5rem;font-weight:700;min-width:22px;text-align:center;
}

/* ── CATEGORY PILLS ── */
.cat-strip{background:#fff;border-bottom:1px solid var(--fog);padding:.75rem 0;position:sticky;top:0;z-index:100}
.cat-scroll{display:flex;gap:.5rem;overflow-x:auto;padding-bottom:2px}
.cat-scroll::-webkit-scrollbar{height:3px}
.cat-scroll::-webkit-scrollbar-thumb{background:var(--gold);border-radius:3px}
.cat-pill{
  white-space:nowrap;padding:.4rem 1.1rem;border-radius:50px;font-size:.82rem;
  font-weight:500;border:2px solid var(--fog);background:transparent;
  color:#666;cursor:pointer;text-decoration:none;transition:all .2s;
}
.cat-pill:hover,.cat-pill.active{
  background:var(--navy);border-color:var(--navy);color:#fff;
}

/* ── SORT BAR ── */
.sort-bar{display:flex;align-items:center;gap:1rem;flex-wrap:wrap;padding:1.2rem 0 .5rem}
.sort-bar label{font-size:.82rem;color:#888;font-weight:500}
.sort-select{
  border:1.5px solid var(--fog);border-radius:8px;padding:.35rem .8rem;
  font-family:var(--ff-body);font-size:.85rem;background:#fff;color:var(--ink);
  cursor:pointer;outline:none;
}
.results-count{margin-left:auto;font-size:.83rem;color:#999}

/* ── PRODUCT GRID ── */
.product-grid{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(230px,1fr));
  gap:1.5rem;padding:1rem 0 3rem;
}

/* ── PRODUCT CARD ── */
.p-card{
  background:#fff;border-radius:16px;overflow:hidden;
  transition:transform .3s cubic-bezier(.34,1.56,.64,1),box-shadow .3s;
  position:relative;cursor:pointer;
  border:1px solid rgba(0,0,0,.05);
}
.p-card:hover{transform:translateY(-8px);box-shadow:0 20px 50px rgba(15,31,61,.12)}
.p-card-img-wrap{
  position:relative;overflow:hidden;
  aspect-ratio:3/4;background:var(--fog);
}
.p-card-img-wrap img{
  width:100%;height:100%;object-fit:cover;
  transition:transform .5s cubic-bezier(.25,.46,.45,.94);
}
.p-card:hover .p-card-img-wrap img{transform:scale(1.07)}

/* Placeholder when no image */
.img-placeholder{
  width:100%;height:100%;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:.5rem;
  background:linear-gradient(135deg,var(--fog),#e8e0d0);
}
.img-placeholder span{font-size:3rem}
.img-placeholder small{font-size:.75rem;color:#999;font-family:var(--ff-body)}

.p-card-badge{
  position:absolute;top:.75rem;left:.75rem;
  background:var(--rust);color:#fff;
  font-size:.68rem;font-weight:600;letter-spacing:.5px;text-transform:uppercase;
  padding:.25rem .65rem;border-radius:50px;
}
.p-card-badge.brand{background:var(--navy)}

.quick-add{
  position:absolute;bottom:.75rem;right:.75rem;
  background:rgba(255,255,255,.95);backdrop-filter:blur(4px);
  border:none;border-radius:50px;width:38px;height:38px;
  display:flex;align-items:center;justify-content:center;
  font-size:1.1rem;cursor:pointer;
  box-shadow:0 4px 12px rgba(0,0,0,.12);
  transform:translateY(10px);opacity:0;
  transition:all .25s;text-decoration:none;color:var(--ink);
}
.p-card:hover .quick-add{transform:translateY(0);opacity:1}

.p-card-body{padding:1rem 1rem .9rem}
.p-brand{
  font-size:.7rem;font-weight:600;letter-spacing:1.5px;
  text-transform:uppercase;color:var(--gold);margin-bottom:.25rem;
}
.p-name{
  font-family:var(--ff-disp);font-size:1.05rem;font-weight:600;
  color:var(--ink);line-height:1.3;margin-bottom:.6rem;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;
}
.p-price-row{display:flex;align-items:baseline;gap:.6rem}
.p-price{font-size:1.1rem;font-weight:700;color:var(--navy)}
.p-mrp{font-size:.8rem;color:#bbb;text-decoration:line-through}
.p-discount{font-size:.75rem;color:var(--jade);font-weight:600}
.size-chips{display:flex;gap:.3rem;flex-wrap:wrap;margin-top:.6rem}
.sz{
  font-size:.68rem;border:1px solid #ddd;border-radius:4px;
  padding:.15rem .4rem;color:#888;background:#fafafa;
}
.sz.oos{opacity:.4;text-decoration:line-through}

/* ── EMPTY STATE ── */
.empty-state{
  text-align:center;padding:5rem 1rem;
}
.empty-state .empty-icon{font-size:4rem;margin-bottom:1rem}
.empty-state h3{font-family:var(--ff-disp);font-size:1.8rem;color:var(--navy);margin-bottom:.5rem}
.empty-state p{color:#999;margin-bottom:1.5rem}

/* ── FADE IN ANIMATION ── */
@keyframes fadeUp{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}
.p-card{animation:fadeUp .5s ease both}
.p-card:nth-child(1){animation-delay:.05s}
.p-card:nth-child(2){animation-delay:.1s}
.p-card:nth-child(3){animation-delay:.15s}
.p-card:nth-child(4){animation-delay:.2s}
.p-card:nth-child(5){animation-delay:.25s}
.p-card:nth-child(6){animation-delay:.3s}
.p-card:nth-child(n+7){animation-delay:.35s}

/* ── FLOATING CART ── */
.float-cart{
  position:fixed;bottom:2rem;right:2rem;
  background:linear-gradient(135deg,var(--navy),#1a3560);
  color:#fff;border-radius:50px;padding:.8rem 1.5rem;
  display:flex;align-items:center;gap:.6rem;
  box-shadow:0 8px 30px rgba(15,31,61,.35);
  text-decoration:none;font-weight:600;font-size:.9rem;
  transition:all .3s;z-index:999;
}
.float-cart:hover{transform:translateY(-3px);box-shadow:0 12px 40px rgba(15,31,61,.45);color:#fff}
.float-cart .fc-count{
  background:var(--gold);color:#fff;border-radius:50%;
  width:22px;height:22px;font-size:.72rem;font-weight:700;
  display:flex;align-items:center;justify-content:center;
}

/* Responsive */
@media(max-width:576px){
  .product-grid{grid-template-columns:repeat(2,1fr);gap:1rem}
  .p-card-body{padding:.75rem}
  .p-name{font-size:.9rem}
}
</style>
{% endblock %}

{% block content %}

<!-- ── SHOP HERO ── -->
<section class="shop-hero">
  <div class="container">
    <div class="row align-items-center gy-3">
      <div class="col-lg-6">
        <h1 class="shop-hero-title">
          Discover <em>Fashion</em><br>Made for Mantha
        </h1>
        <p class="shop-hero-sub">{{ products|length }} styles in stock. Buy online, pick up at Main Road.</p>
      </div>
      <div class="col-lg-6">
        <div class="d-flex flex-column flex-sm-row align-items-start align-items-sm-center gap-3">
          <form method="GET" action="{{ url_for('customer.index') }}" class="search-bar-wrap flex-grow-1">
            <i class="bi bi-search search-icon"></i>
            <input class="search-bar" type="text" name="q"
                   placeholder="Search shirts, kurtas, brands…"
                   value="{{ search }}">
            <!-- preserve other filters -->
            {% if active_cat != 'all' %}<input type="hidden" name="cat" value="{{ active_cat }}">{% endif %}
          </form>
          <a href="{{ url_for('customer.cart') }}" class="cart-pill">
            <i class="bi bi-bag"></i> Cart
            {% if cart_count > 0 %}
              <span class="badge-count">{{ cart_count }}</span>
            {% endif %}
          </a>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ── CATEGORY STRIP ── -->
<div class="cat-strip">
  <div class="container">
    <div class="cat-scroll">
      <a href="{{ url_for('customer.index', sort=sort) }}"
         class="cat-pill {% if active_cat == 'all' %}active{% endif %}">
        ✦ All Items
      </a>
      {% for cat in categories %}
      <a href="{{ url_for('customer.index', cat=cat.slug, sort=sort) }}"
         class="cat-pill {% if active_cat == cat.slug %}active{% endif %}">
        {{ cat.name }}
      </a>
      {% endfor %}
    </div>
  </div>
</div>

<!-- ── MAIN SHOP BODY ── -->
<div class="container">

  <!-- Sort + results bar -->
  <div class="sort-bar">
    <!-- Brand filter -->
    <form method="GET" id="filterForm" style="display:contents">
      {% if active_cat != 'all' %}<input type="hidden" name="cat" value="{{ active_cat }}">{% endif %}
      {% if search %}<input type="hidden" name="q" value="{{ search }}">{% endif %}

      <label for="brandSel">Brand:</label>
      <select class="sort-select" name="brand" id="brandSel"
              onchange="document.getElementById('filterForm').submit()">
        <option value="all" {% if active_brand=='all' %}selected{% endif %}>All Brands</option>
        {% for b in brands %}
        <option value="{{ b.id }}" {% if active_brand==b.id|string %}selected{% endif %}>{{ b.name }}</option>
        {% endfor %}
      </select>

      <label for="sortSel">Sort:</label>
      <select class="sort-select" name="sort" id="sortSel"
              onchange="document.getElementById('filterForm').submit()">
        <option value="newest"     {% if sort=='newest' %}selected{% endif %}>Newest First</option>
        <option value="price_low"  {% if sort=='price_low' %}selected{% endif %}>Price: Low → High</option>
        <option value="price_high" {% if sort=='price_high' %}selected{% endif %}>Price: High → Low</option>
      </select>
    </form>

    <span class="results-count">
      <strong>{{ products|length }}</strong> product{% if products|length != 1 %}s{% endif %}
      {% if search %}for "<em>{{ search }}</em>"{% endif %}
    </span>
  </div>

  <!-- Product grid -->
  {% if products %}
  <div class="product-grid">
    {% for p in products %}
    {% set has_stock = p.variants | selectattr('stock_quantity', 'gt', 0) | list %}
    <div class="p-card">
      <a href="{{ url_for('customer.product_detail', product_id=p.id) }}" style="text-decoration:none;color:inherit">

        <!-- Image -->
        <div class="p-card-img-wrap">
          {% if p.image_filename %}
            <img src="{{ url_for('static', filename='images/products/' + p.image_filename) }}"
                 alt="{{ p.name }}" loading="lazy">
          {% else %}
            <div class="img-placeholder">
              <span>{% if 'shirt' in p.name.lower() %}👔
                    {% elif 'trouser' in p.name.lower() or 'pant' in p.name.lower() %}👖
                    {% elif 'kurta' in p.name.lower() %}🧣
                    {% elif 'kid' in p.name.lower() %}👕
                    {% else %}🛍️{% endif %}</span>
              <small>{{ p.category.name }}</small>
            </div>
          {% endif %}

          <!-- Badge -->
          {% if p.brand.name == 'k satish' %}
            <span class="p-card-badge brand">k satish</span>
          {% elif p.mrp and p.price < p.mrp %}
            {% set disc = ((p.mrp - p.price) / p.mrp * 100)|int %}
            <span class="p-card-badge">{{ disc }}% OFF</span>
          {% endif %}

          {% if not has_stock %}
            <span class="p-card-badge" style="background:#888;left:auto;right:.75rem">Out of Stock</span>
          {% endif %}
        </div>

      </a>

      <!-- Quick view button -->
      <a href="{{ url_for('customer.product_detail', product_id=p.id) }}"
         class="quick-add" title="View Product">👁</a>

      <!-- Info -->
      <div class="p-card-body">
        <div class="p-brand">{{ p.brand.name }}</div>
        <a href="{{ url_for('customer.product_detail', product_id=p.id) }}"
           style="text-decoration:none">
          <div class="p-name">{{ p.name }}</div>
        </a>
        <div class="p-price-row">
          <span class="p-price">₹{{ "%.0f"|format(p.price) }}</span>
          {% if p.mrp and p.mrp > p.price %}
            <span class="p-mrp">₹{{ "%.0f"|format(p.mrp) }}</span>
            <span class="p-discount">{{ ((p.mrp-p.price)/p.mrp*100)|int }}% off</span>
          {% endif %}
        </div>
        <!-- Size chips -->
        <div class="size-chips">
          {% for v in p.variants %}
            <span class="sz {% if v.is_out_of_stock %}oos{% endif %}">{{ v.size }}</span>
          {% endfor %}
        </div>
      </div>
    </div>
    {% endfor %}
  </div>

  {% else %}
  <!-- Empty state -->
  <div class="empty-state">
    <div class="empty-icon">🔍</div>
    <h3>No products found</h3>
    <p>Try a different category or search term</p>
    <a href="{{ url_for('customer.index') }}"
       class="btn btn-maroon rounded-pill px-4">Clear Filters</a>
  </div>
  {% endif %}

</div>

<!-- Floating cart button (only when items in cart) -->
{% if cart_count > 0 %}
<a href="{{ url_for('customer.cart') }}" class="float-cart">
  <i class="bi bi-bag-check"></i>
  View Cart
  <span class="fc-count">{{ cart_count }}</span>
</a>
{% endif %}

{% endblock %}
'''

with open(f"{BASE}/app/templates/customer/index.html", "w") as f:
    f.write(index_html)
print("✅ templates/customer/index.html")

# ─────────────────────────────────────────────
# FILE 3 — templates/customer/product.html
# ─────────────────────────────────────────────
product_html = r'''{% extends 'base.html' %}
{% block title %}{{ product.name }}{% endblock %}

{% block extra_css %}
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');
:root{--ff-disp:'Cormorant Garamond',Georgia,serif;--ff-body:'DM Sans',sans-serif;
  --navy:#0F1F3D;--rust:#B5451B;--gold:#C9922A;--jade:#1B6B4A;--sand:#F5EDD9;--fog:#EDE8DF;}
body{font-family:var(--ff-body)}

/* breadcrumb */
.breadcrumb-custom{background:none;padding:1rem 0 .5rem;font-size:.82rem}
.breadcrumb-custom a{color:var(--gold);text-decoration:none}

/* main image */
.product-img-wrap{
  border-radius:20px;overflow:hidden;
  aspect-ratio:4/5;background:var(--fog);
  position:relative;
}
.product-img-wrap img{width:100%;height:100%;object-fit:cover}
.img-placeholder-lg{
  width:100%;height:100%;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:1rem;
  background:linear-gradient(135deg,var(--fog),#e0d8cc);
}
.img-placeholder-lg span{font-size:6rem}
.img-placeholder-lg p{font-family:var(--ff-disp);font-size:1.2rem;color:#888}

/* sticky side */
.product-detail-sticky{position:sticky;top:80px}
.prod-brand{font-size:.75rem;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:var(--gold);margin-bottom:.4rem}
.prod-name{font-family:var(--ff-disp);font-size:2.2rem;font-weight:700;color:var(--navy);line-height:1.2;margin-bottom:.8rem}
.price-block{margin-bottom:1.5rem}
.price-main{font-size:2rem;font-weight:700;color:var(--navy)}
.price-mrp{font-size:1rem;color:#bbb;text-decoration:line-through;margin-left:.5rem}
.price-disc{background:#E8F5E9;color:var(--jade);font-size:.82rem;font-weight:600;padding:.2rem .6rem;border-radius:50px;margin-left:.5rem}

/* size selector */
.size-label{font-size:.82rem;font-weight:600;letter-spacing:.5px;text-transform:uppercase;color:#666;margin-bottom:.6rem}
.size-grid{display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:1.5rem}
.sz-btn{
  min-width:52px;padding:.45rem .8rem;border-radius:8px;border:2px solid #ddd;
  background:#fff;font-family:var(--ff-body);font-size:.88rem;font-weight:500;
  cursor:pointer;transition:all .2s;text-align:center;position:relative;
}
.sz-btn:hover:not(.oos-btn){border-color:var(--navy);color:var(--navy)}
.sz-btn.selected{border-color:var(--navy);background:var(--navy);color:#fff}
.sz-btn.oos-btn{opacity:.4;cursor:not-allowed;text-decoration:line-through;background:#f5f5f5}
.stock-chip{font-size:.72rem;color:var(--rust);font-weight:500;margin-left:.3rem}
.stock-chip.ok{color:var(--jade)}

/* qty selector */
.qty-row{display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem}
.qty-wrap{display:flex;align-items:center;border:2px solid #ddd;border-radius:10px;overflow:hidden}
.qty-btn{width:36px;height:36px;border:none;background:#fff;font-size:1.1rem;cursor:pointer;transition:background .15s}
.qty-btn:hover{background:var(--fog)}
.qty-val{width:40px;text-align:center;font-weight:600;border:none;outline:none;font-family:var(--ff-body)}

/* add to cart btn */
.btn-add-cart{
  width:100%;padding:.9rem;border:none;border-radius:12px;
  background:linear-gradient(135deg,var(--navy),#1a3560);
  color:#fff;font-family:var(--ff-body);font-size:1rem;font-weight:600;
  cursor:pointer;transition:all .25s;margin-bottom:.75rem;
  box-shadow:0 6px 20px rgba(15,31,61,.2);
}
.btn-add-cart:hover{transform:translateY(-2px);box-shadow:0 10px 28px rgba(15,31,61,.3)}
.btn-add-cart:disabled{opacity:.5;cursor:not-allowed;transform:none}

/* info chips */
.info-chips{display:flex;gap:.6rem;flex-wrap:wrap;margin-bottom:1.5rem}
.info-chip{display:flex;align-items:center;gap:.4rem;background:var(--fog);border-radius:8px;padding:.4rem .9rem;font-size:.8rem;color:#555}
.info-chip i{color:var(--gold)}

/* description */
.desc-box{background:var(--fog);border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1.5rem}
.desc-box h6{font-family:var(--ff-disp);font-size:1rem;color:var(--navy);margin-bottom:.5rem}
.desc-box p{font-size:.88rem;color:#666;line-height:1.7;margin:0}

/* related */
.related-title{font-family:var(--ff-disp);font-size:1.8rem;color:var(--navy);margin:2.5rem 0 1.2rem}
.rel-card{background:#fff;border-radius:12px;overflow:hidden;transition:transform .3s;border:1px solid rgba(0,0,0,.06);text-decoration:none;color:inherit;display:block}
.rel-card:hover{transform:translateY(-4px);box-shadow:0 12px 30px rgba(0,0,0,.1)}
.rel-img{aspect-ratio:1;background:var(--fog);display:flex;align-items:center;justify-content:center;font-size:3rem}
.rel-body{padding:.8rem}
.rel-name{font-family:var(--ff-disp);font-size:.95rem;font-weight:600;color:var(--navy);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.rel-price{font-size:.9rem;font-weight:700;color:var(--navy);margin-top:.3rem}
</style>
{% endblock %}

{% block content %}
<div class="container py-3">

  <!-- Breadcrumb -->
  <nav aria-label="breadcrumb">
    <ol class="breadcrumb breadcrumb-custom">
      <li class="breadcrumb-item"><a href="{{ url_for('customer.index') }}">Shop</a></li>
      <li class="breadcrumb-item"><a href="{{ url_for('customer.index', cat=product.category.slug) }}">{{ product.category.name }}</a></li>
      <li class="breadcrumb-item active text-muted">{{ product.name }}</li>
    </ol>
  </nav>

  <div class="row g-5">

    <!-- LEFT: Image -->
    <div class="col-lg-6">
      <div class="product-img-wrap">
        {% if product.image_filename %}
          <img src="{{ url_for('static', filename='images/products/' + product.image_filename) }}"
               alt="{{ product.name }}">
        {% else %}
          <div class="img-placeholder-lg">
            <span>{% if 'shirt' in product.name.lower() %}👔
                  {% elif 'trouser' in product.name.lower() %}👖
                  {% elif 'kurta' in product.name.lower() %}🧣
                  {% else %}🛍️{% endif %}</span>
            <p>{{ product.name }}</p>
          </div>
        {% endif %}
      </div>
    </div>

    <!-- RIGHT: Details -->
    <div class="col-lg-6">
      <div class="product-detail-sticky">

        <div class="prod-brand">{{ product.brand.name }}</div>
        <h1 class="prod-name">{{ product.name }}</h1>

        <!-- Price -->
        <div class="price-block">
          <span class="price-main">₹{{ "%.0f"|format(product.price) }}</span>
          {% if product.mrp and product.mrp > product.price %}
            <span class="price-mrp">₹{{ "%.0f"|format(product.mrp) }}</span>
            <span class="price-disc">{{ ((product.mrp-product.price)/product.mrp*100)|int }}% off</span>
          {% endif %}
        </div>

        <!-- Size selector form -->
        <form method="POST" action="{{ url_for('customer.add_to_cart') }}" id="cartForm">
          <input type="hidden" name="variant_id" id="variantId" value="">
          <input type="hidden" name="quantity" id="qtyInput" value="1">

          <div class="size-label">Select Size</div>
          <div class="size-grid">
            {% for size, variant in variants.items() %}
            <button type="button"
                    class="sz-btn {% if variant.is_out_of_stock %}oos-btn{% endif %}"
                    data-variant-id="{{ variant.id }}"
                    data-stock="{{ variant.stock_quantity }}"
                    {% if variant.is_out_of_stock %}disabled{% endif %}
                    onclick="selectSize(this)">
              {{ size }}
              {% if not variant.is_out_of_stock and variant.stock_quantity <= variant.low_stock_threshold %}
                <span class="stock-chip">{{ variant.stock_quantity }} left</span>
              {% endif %}
            </button>
            {% endfor %}
          </div>

          <!-- Quantity -->
          <div class="qty-row">
            <div class="qty-label" style="font-size:.82rem;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:#666">Qty:</div>
            <div class="qty-wrap">
              <button type="button" class="qty-btn" onclick="changeQty(-1)">−</button>
              <span class="qty-val" id="qtyDisplay">1</span>
              <button type="button" class="qty-btn" onclick="changeQty(1)">+</button>
            </div>
          </div>

          <!-- Add to cart -->
          <button type="submit" class="btn-add-cart" id="addCartBtn" disabled>
            <i class="bi bi-bag-plus me-2"></i>Select a Size to Add to Cart
          </button>

        </form>

        <!-- Info chips -->
        <div class="info-chips">
          <div class="info-chip"><i class="bi bi-geo-alt"></i>Pickup at Main Road, Mantha</div>
          <div class="info-chip"><i class="bi bi-shield-check"></i>Quality Guaranteed</div>
          <div class="info-chip"><i class="bi bi-arrow-return-left"></i>In-store exchange</div>
        </div>

        <!-- Description -->
        {% if product.description %}
        <div class="desc-box">
          <h6>About this Product</h6>
          <p>{{ product.description }}</p>
        </div>
        {% endif %}

        <!-- SKU info -->
        <p style="font-size:.75rem;color:#bbb">SKU: {{ product.sku }} &nbsp;|&nbsp; Category: {{ product.category.name }}</p>

      </div>
    </div>
  </div>

  <!-- Related Products -->
  {% if related %}
  <div>
    <h2 class="related-title">You May Also Like</h2>
    <div class="row g-3">
      {% for r in related %}
      <div class="col-6 col-md-3">
        <a href="{{ url_for('customer.product_detail', product_id=r.id) }}" class="rel-card">
          <div class="rel-img">
            {% if r.image_filename %}
              <img src="{{ url_for('static', filename='images/products/' + r.image_filename) }}"
                   alt="{{ r.name }}" style="width:100%;height:100%;object-fit:cover">
            {% else %}
              🛍️
            {% endif %}
          </div>
          <div class="rel-body">
            <div class="rel-name">{{ r.name }}</div>
            <div class="rel-price">₹{{ "%.0f"|format(r.price) }}</div>
          </div>
        </a>
      </div>
      {% endfor %}
    </div>
  </div>
  {% endif %}

</div>

<script>
let currentQty = 1;
let maxStock = 99;

function selectSize(btn) {
  // Deselect all
  document.querySelectorAll('.sz-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  document.getElementById('variantId').value = btn.dataset.variantId;
  maxStock = parseInt(btn.dataset.stock);
  currentQty = 1;
  document.getElementById('qtyDisplay').textContent = 1;
  document.getElementById('qtyInput').value = 1;

  const addBtn = document.getElementById('addCartBtn');
  addBtn.disabled = false;
  addBtn.innerHTML = '<i class="bi bi-bag-plus me-2"></i>Add to Cart';
}

function changeQty(delta) {
  currentQty = Math.min(Math.max(1, currentQty + delta), maxStock);
  document.getElementById('qtyDisplay').textContent = currentQty;
  document.getElementById('qtyInput').value = currentQty;
}
</script>
{% endblock %}
'''

with open(f"{BASE}/app/templates/customer/product.html", "w") as f:
    f.write(product_html)
print("✅ templates/customer/product.html")

# ─────────────────────────────────────────────
# FILE 4 — templates/customer/cart.html
# ─────────────────────────────────────────────
cart_html = r'''{% extends 'base.html' %}
{% block title %}Your Cart{% endblock %}

{% block extra_css %}
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=DM+Sans:wght@300;400;500;600&display=swap');
:root{--ff-disp:'Cormorant Garamond',Georgia,serif;--ff-body:'DM Sans',sans-serif;
  --navy:#0F1F3D;--gold:#C9922A;--sand:#F5EDD9;--fog:#EDE8DF;--rust:#B5451B;--jade:#1B6B4A;}
body{font-family:var(--ff-body)}

.cart-page{padding:2.5rem 0 5rem}
.cart-title{font-family:var(--ff-disp);font-size:2.5rem;color:var(--navy);margin-bottom:.3rem}
.cart-sub{color:#999;font-size:.9rem;margin-bottom:2rem}

/* Cart item row */
.cart-item{
  background:#fff;border-radius:16px;padding:1.2rem;
  display:flex;gap:1rem;align-items:center;
  margin-bottom:1rem;border:1px solid rgba(0,0,0,.06);
  transition:box-shadow .2s;
}
.cart-item:hover{box-shadow:0 6px 24px rgba(0,0,0,.07)}
.cart-item-img{
  width:80px;height:100px;border-radius:10px;
  background:var(--fog);flex-shrink:0;
  display:flex;align-items:center;justify-content:center;font-size:2rem;overflow:hidden;
}
.cart-item-img img{width:100%;height:100%;object-fit:cover}
.cart-item-info{flex:1;min-width:0}
.ci-brand{font-size:.7rem;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:var(--gold)}
.ci-name{font-family:var(--ff-disp);font-size:1.05rem;font-weight:600;color:var(--navy);line-height:1.3}
.ci-size{display:inline-block;background:var(--fog);border-radius:4px;padding:.1rem .5rem;font-size:.75rem;color:#555;margin-top:.3rem}
.ci-price{font-size:1.1rem;font-weight:700;color:var(--navy);white-space:nowrap}
.ci-remove{
  background:none;border:none;color:#ccc;font-size:1.1rem;cursor:pointer;
  padding:.3rem;border-radius:6px;transition:color .2s,background .2s;
}
.ci-remove:hover{color:var(--rust);background:#fff0ee}

/* Order summary card */
.summary-card{
  background:#fff;border-radius:20px;padding:1.8rem;
  border:1px solid rgba(0,0,0,.07);position:sticky;top:90px;
}
.summary-title{font-family:var(--ff-disp);font-size:1.5rem;color:var(--navy);margin-bottom:1.2rem}
.summary-row{display:flex;justify-content:space-between;font-size:.9rem;color:#666;margin-bottom:.6rem}
.summary-total{display:flex;justify-content:space-between;font-weight:700;font-size:1.15rem;color:var(--navy);border-top:2px solid var(--fog);padding-top:.8rem;margin-top:.8rem}

/* Payment options */
.pay-label{font-size:.82rem;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:#666;margin:.8rem 0 .4rem}
.pay-opts{display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:1rem}
.pay-opt{
  display:flex;align-items:center;gap:.4rem;cursor:pointer;
  border:2px solid var(--fog);border-radius:8px;padding:.5rem .9rem;
  font-size:.85rem;font-weight:500;transition:all .2s;
}
.pay-opt input{accent-color:var(--navy)}
.pay-opt:has(input:checked){border-color:var(--navy);background:#f0f4ff}

/* Checkout btn */
.btn-checkout{
  width:100%;padding:1rem;border:none;border-radius:14px;
  background:linear-gradient(135deg,var(--navy),#1a3560);
  color:#fff;font-family:var(--ff-body);font-size:1rem;font-weight:600;
  cursor:pointer;transition:all .25s;
  box-shadow:0 6px 20px rgba(15,31,61,.2);margin-top:.5rem;
}
.btn-checkout:hover{transform:translateY(-2px);box-shadow:0 10px 28px rgba(15,31,61,.3)}

/* Pickup badge */
.pickup-badge{
  background:linear-gradient(135deg,#E8F5E9,#F1F8E9);
  border:1px solid #A5D6A7;border-radius:12px;padding:1rem 1.2rem;
  display:flex;align-items:flex-start;gap:.75rem;margin-bottom:1rem;
}
.pickup-badge i{color:var(--jade);font-size:1.3rem;margin-top:.1rem}
.pickup-badge strong{font-size:.88rem;color:var(--jade);display:block}
.pickup-badge small{font-size:.8rem;color:#666}

/* Empty cart */
.empty-cart{text-align:center;padding:5rem 1rem}
.empty-cart .ec-icon{font-size:5rem;margin-bottom:1rem}
.empty-cart h3{font-family:var(--ff-disp);font-size:2rem;color:var(--navy);margin-bottom:.5rem}
.empty-cart p{color:#999;margin-bottom:2rem}
</style>
{% endblock %}

{% block content %}
<div class="container cart-page">

  <div class="row">
    <div class="col-12">
      <h1 class="cart-title">Your Cart</h1>
      <p class="cart-sub">
        {% if cart_items %}{{ cart_items|length }} item{% if cart_items|length != 1 %}s{% endif %} ready for pickup
        {% else %}Your cart is empty{% endif %}
      </p>
    </div>
  </div>

  {% if cart_items %}
  <div class="row g-4">

    <!-- Left: Cart Items -->
    <div class="col-lg-7">

      {% for item in cart_items %}
      <div class="cart-item">
        <!-- Product image -->
        <div class="cart-item-img">
          {% if item.product.image_filename %}
            <img src="{{ url_for('static', filename='images/products/' + item.product.image_filename) }}"
                 alt="{{ item.product.name }}">
          {% else %}
            {% if 'shirt' in item.product.name.lower() %}👔
            {% elif 'trouser' in item.product.name.lower() %}👖
            {% elif 'kurta' in item.product.name.lower() %}🧣
            {% else %}🛍️{% endif %}
          {% endif %}
        </div>

        <!-- Info -->
        <div class="cart-item-info">
          <div class="ci-brand">{{ item.product.brand.name }}</div>
          <div class="ci-name">{{ item.product.name }}</div>
          <span class="ci-size">Size: {{ item.variant.size }}</span>
          <div style="font-size:.82rem;color:#999;margin-top:.3rem">
            ₹{{ "%.0f"|format(item.product.price) }} × {{ item.quantity }}
          </div>
        </div>

        <!-- Line price -->
        <div class="text-end">
          <div class="ci-price">₹{{ "%.0f"|format(item.line) }}</div>
          <a href="{{ url_for('customer.remove_from_cart', item_id=item.id) }}"
             class="ci-remove mt-2 d-inline-block"
             onclick="return confirm('Remove this item?')">
            <i class="bi bi-trash3"></i>
          </a>
        </div>
      </div>
      {% endfor %}

      <!-- Continue shopping link -->
      <a href="{{ url_for('customer.index') }}"
         style="color:var(--gold);font-size:.88rem;font-weight:500;text-decoration:none">
        <i class="bi bi-arrow-left me-1"></i>Continue Shopping
      </a>

    </div>

    <!-- Right: Order Summary -->
    <div class="col-lg-5">
      <div class="summary-card">

        <div class="summary-title">Order Summary</div>

        <div class="summary-row">
          <span>Subtotal ({{ cart_items|length }} items)</span>
          <span>₹{{ "%.0f"|format(subtotal) }}</span>
        </div>
        <div class="summary-row">
          <span>Pickup Charge</span>
          <span style="color:var(--jade);font-weight:600">FREE</span>
        </div>
        <div class="summary-total">
          <span>Total</span>
          <span>₹{{ "%.0f"|format(subtotal) }}</span>
        </div>

        <!-- Pickup info -->
        <div class="pickup-badge mt-3">
          <i class="bi bi-shop"></i>
          <div>
            <strong>Free In-Store Pickup</strong>
            <small>We'll have your order ready at <b>M B MANIYAR, Main Road, Mantha</b>.<br>You'll be notified when it's ready.</small>
          </div>
        </div>

        <!-- Checkout form -->
        <form method="POST" action="{{ url_for('customer.checkout') }}">

          <div class="pay-label">Payment at Counter</div>
          <div class="pay-opts">
            <label class="pay-opt">
              <input type="radio" name="payment_method" value="cash" checked> 💵 Cash
            </label>
            <label class="pay-opt">
              <input type="radio" name="payment_method" value="upi"> 📱 UPI
            </label>
            <label class="pay-opt">
              <input type="radio" name="payment_method" value="card"> 💳 Card
            </label>
          </div>

          <div class="mb-2" style="font-size:.82rem;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:#666">
            Notes (optional)
          </div>
          <textarea name="notes" rows="2"
            style="width:100%;border:2px solid var(--fog);border-radius:10px;padding:.6rem .9rem;font-family:var(--ff-body);font-size:.88rem;resize:none;outline:none"
            placeholder="e.g. Please keep ready by 6 PM…"></textarea>

          <button type="submit" class="btn-checkout">
            <i class="bi bi-bag-check me-2"></i>Place Pickup Order — ₹{{ "%.0f"|format(subtotal) }}
          </button>

        </form>

        <p class="text-center mt-3" style="font-size:.75rem;color:#bbb">
          <i class="bi bi-lock me-1"></i>Secure order. Pay when you pick up at the store.
        </p>

      </div>
    </div>

  </div>

  {% else %}
  <!-- Empty cart -->
  <div class="empty-cart">
    <div class="ec-icon">🛍️</div>
    <h3>Your cart is empty</h3>
    <p>Looks like you haven't added anything yet. Explore our latest collection!</p>
    <a href="{{ url_for('customer.index') }}"
       class="btn btn-maroon rounded-pill px-5 py-2 fs-6">
      Start Shopping
    </a>
  </div>
  {% endif %}

</div>
{% endblock %}
'''

with open(f"{BASE}/app/templates/customer/cart.html", "w") as f:
    f.write(cart_html)
print("✅ templates/customer/cart.html")

# ─────────────────────────────────────────────
# FILE 5 — templates/customer/order_confirmation.html
# ─────────────────────────────────────────────
confirm_html = r'''{% extends 'base.html' %}
{% block title %}Order Confirmed!{% endblock %}

{% block extra_css %}
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=DM+Sans:wght@400;500;600&display=swap');
:root{--ff-disp:'Cormorant Garamond',Georgia,serif;--ff-body:'DM Sans',sans-serif;--navy:#0F1F3D;--gold:#C9922A;--jade:#1B6B4A;}
body{font-family:var(--ff-body)}
@keyframes popIn{0%{transform:scale(.4);opacity:0}70%{transform:scale(1.15)}100%{transform:scale(1);opacity:1}}
.confirm-wrap{min-height:80vh;display:flex;align-items:center;padding:3rem 0}
.confirm-card{background:#fff;border-radius:24px;padding:3rem 2.5rem;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.08);max-width:560px;margin:0 auto}
.check-circle{width:90px;height:90px;border-radius:50%;background:linear-gradient(135deg,#43A047,#1B6B4A);display:flex;align-items:center;justify-content:center;margin:0 auto 1.5rem;animation:popIn .5s cubic-bezier(.34,1.56,.64,1)}
.check-circle i{font-size:2.5rem;color:#fff}
.confirm-title{font-family:var(--ff-disp);font-size:2.2rem;color:var(--navy);margin-bottom:.4rem}
.order-num{background:#F0F4FF;border-radius:8px;display:inline-block;padding:.4rem 1.2rem;font-size:1rem;font-weight:700;color:var(--navy);letter-spacing:1px;margin-bottom:1.5rem}
.pickup-steps{background:#F9F9F6;border-radius:16px;padding:1.5rem;text-align:left;margin-bottom:1.5rem}
.step-row{display:flex;align-items:flex-start;gap:.8rem;margin-bottom:.9rem}
.step-row:last-child{margin-bottom:0}
.step-num{width:28px;height:28px;border-radius:50%;background:var(--navy);color:#fff;font-size:.75rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:.1rem}
.step-text strong{display:block;font-size:.88rem;color:var(--navy)}
.step-text small{color:#999;font-size:.8rem}
.order-items-list{background:#F5EDD9;border-radius:12px;padding:1rem 1.2rem;margin-bottom:1.5rem;text-align:left}
.oi-row{display:flex;justify-content:space-between;font-size:.87rem;padding:.3rem 0;border-bottom:1px solid rgba(0,0,0,.06)}
.oi-row:last-child{border:none;font-weight:700;color:var(--navy);padding-top:.6rem}
</style>
{% endblock %}

{% block content %}
<div class="confirm-wrap">
  <div class="container">
    <div class="confirm-card">

      <div class="check-circle">
        <i class="bi bi-check-lg"></i>
      </div>

      <h2 class="confirm-title">Order Placed!</h2>
      <p class="text-muted mb-2" style="font-size:.9rem">Your pickup order has been confirmed</p>
      <div class="order-num">{{ order.order_number }}</div>

      <!-- Order Items -->
      <div class="order-items-list">
        {% for item in order.items %}
        <div class="oi-row">
          <span>{{ item.product.name }} ({{ item.variant.size }}) × {{ item.quantity }}</span>
          <span>₹{{ "%.0f"|format(item.total_price) }}</span>
        </div>
        {% endfor %}
        <div class="oi-row">
          <span>Total</span>
          <span>₹{{ "%.0f"|format(order.total_amount) }}</span>
        </div>
      </div>

      <!-- Pickup steps -->
      <div class="pickup-steps">
        <div class="step-row">
          <div class="step-num">1</div>
          <div class="step-text">
            <strong>We received your order</strong>
            <small>Our team is preparing your items</small>
          </div>
        </div>
        <div class="step-row">
          <div class="step-num">2</div>
          <div class="step-text">
            <strong>Visit the store</strong>
            <small>M B MANIYAR, Main Road, Mantha — Mon–Sat 10AM–9PM</small>
          </div>
        </div>
        <div class="step-row">
          <div class="step-num">3</div>
          <div class="step-text">
            <strong>Show order number & pay</strong>
            <small>Pay ₹{{ "%.0f"|format(order.total_amount) }} by {{ order.payment_method.upper() }} at the counter</small>
          </div>
        </div>
      </div>

      <a href="{{ url_for('customer.index') }}"
         class="btn btn-maroon rounded-pill px-5 py-2 fw-semibold">
        Continue Shopping
      </a>

    </div>
  </div>
</div>
{% endblock %}
'''

with open(f"{BASE}/app/templates/customer/order_confirmation.html", "w") as f:
    f.write(confirm_html)
print("✅ templates/customer/order_confirmation.html")

# ─────────────────────────────────────────────
# FILE 6 — Seed demo products in __init__.py
# ─────────────────────────────────────────────
seed_script = '''
# Run this ONCE to add demo products to the database
import sys, os
sys.path.insert(0, os.path.expanduser("~/Desktop/mbmaniyar"))

from app import create_app
from app.models import db, Product, ProductVariant, Category, Brand

app = create_app()

with app.app_context():
    ksatish = Brand.query.filter_by(name="k satish").first()
    raymond = Brand.query.filter_by(name="Raymond").first()
    allen   = Brand.query.filter_by(name="Allen Solly").first()
    generic = Brand.query.filter_by(name="Generic").first()

    shirts   = Category.query.filter_by(slug="shirts").first()
    trousers = Category.query.filter_by(slug="trousers").first()
    kurtas   = Category.query.filter_by(slug="kurtas").first()
    tshirts  = Category.query.filter_by(slug="t-shirts").first()
    kids     = Category.query.filter_by(slug="kids-wear").first()

    if Product.query.first():
        print("Products already exist. Skipping.")
        exit()

    products = [
        # k satish shirts
        dict(name="k satish White Classic Shirt",  sku="KS-SH-001", price=899,  mrp=1199, category=shirts,   brand=ksatish,
             sizes=[("S",8),("M",12),("L",10),("XL",5),("XXL",3)]),
        dict(name="k satish Blue Formal Shirt",    sku="KS-SH-002", price=949,  mrp=1299, category=shirts,   brand=ksatish,
             sizes=[("S",4),("M",8), ("L",9), ("XL",6),("XXL",2)]),
        dict(name="k satish Check Casual Shirt",   sku="KS-SH-003", price=799,  mrp=999,  category=shirts,   brand=ksatish,
             sizes=[("S",6),("M",10),("L",7), ("XL",4),("XXL",1)]),
        dict(name="k satish Cotton Kurta",         sku="KS-KU-001", price=1199, mrp=1599, category=kurtas,   brand=ksatish,
             sizes=[("S",5),("M",9), ("L",11),("XL",4),("XXL",2)]),
        # Raymond
        dict(name="Raymond Grey Wool Trouser",     sku="RM-TR-001", price=1899, mrp=2499, category=trousers, brand=raymond,
             sizes=[("28",4),("30",8),("32",10),("34",6),("36",3)]),
        dict(name="Raymond Navy Formal Trouser",   sku="RM-TR-002", price=2099, mrp=2799, category=trousers, brand=raymond,
             sizes=[("28",3),("30",6),("32",9), ("34",7),("36",2)]),
        # Allen Solly
        dict(name="Allen Solly Polo T-Shirt",      sku="AS-TS-001", price=699,  mrp=899,  category=tshirts,  brand=allen,
             sizes=[("S",10),("M",15),("L",12),("XL",8),("XXL",4)]),
        dict(name="Allen Solly Chino Trouser",     sku="AS-TR-001", price=1499, mrp=1899, category=trousers, brand=allen,
             sizes=[("28",5),("30",10),("32",8),("34",5),("36",2)]),
        # Generic kids
        dict(name="Cotton Kids Shirt Set",         sku="GN-KD-001", price=499,  mrp=699,  category=kids,     brand=generic,
             sizes=[("2Y",6),("4Y",8),("6Y",7),("8Y",5),("10Y",3)]),
        dict(name="Kids Festive Kurta",            sku="GN-KD-002", price=649,  mrp=899,  category=kids,     brand=generic,
             sizes=[("2Y",4),("4Y",6),("6Y",8),("8Y",6),("10Y",4)]),
    ]

    for p in products:
        prod = Product(
            name=p["name"], sku=p["sku"],
            price=p["price"], mrp=p.get("mrp"),
            category_id=p["category"].id,
            brand_id=p["brand"].id,
            description=f"Premium quality {p['category'].name.lower()} from {p['brand'].name}. "
                        "Available in multiple sizes at M B MANIYAR, Mantha.",
            is_active=True, is_online=True,
        )
        db.session.add(prod)
        db.session.flush()
        for size, qty in p["sizes"]:
            db.session.add(ProductVariant(product_id=prod.id, size=size, stock_quantity=qty))

    db.session.commit()
    print(f"✅ Seeded {len(products)} demo products with variants!")
'''

with open(f"{BASE}/seed_products.py", "w") as f:
    f.write(seed_script)
print("✅ seed_products.py")

print()
print("=" * 50)
print("All Step 3 files written successfully!")
print("=" * 50)

#!/usr/bin/env python3
"""
POS Builder — Complete Point of Sale System for M B MANIYAR
Run: python3 build_pos.py
"""
import os

BASE = os.path.expanduser("~/Desktop/mbmaniyar")

def w(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ {path}")

# ═══════════════════════════════════════════════════════════════
# 1. ADD POS ROUTES TO admin/routes.py  (append only)
# ═══════════════════════════════════════════════════════════════
pos_routes = '''

# ═══════════════════════════════════════════════════════════════
# POS ROUTES
# ═══════════════════════════════════════════════════════════════

@admin_bp.route('/pos')
@admin_required
def pos():
    """Main POS page."""
    products  = Product.query.filter_by(is_active=True).all()
    categories = Category.query.all()
    employees  = Employee.query.join(User).filter(User.is_active_account==True).all()
    return render_template('admin/pos.html',
        products=products, categories=categories, employees=employees)


@admin_bp.route('/pos/search')
@admin_required
def pos_search():
    """AJAX — search products by name, SKU, or barcode."""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    results = Product.query.filter(
        Product.is_active == True,
        db.or_(
            Product.name.ilike(f'%{q}%'),
            Product.sku.ilike(f'%{q}%'),
        )
    ).limit(10).all()
    data = []
    for p in results:
        for v in p.variants:
            if v.stock_quantity > 0:
                data.append({
                    'variant_id'  : v.id,
                    'product_id'  : p.id,
                    'name'        : p.name,
                    'brand'       : p.brand.name,
                    'sku'         : p.sku,
                    'size'        : v.size,
                    'price'       : float(p.price),
                    'mrp'         : float(p.mrp) if p.mrp else None,
                    'stock'       : v.stock_quantity,
                    'barcode'     : v.barcode or '',
                    'category'    : p.category.name,
                })
    return jsonify(data)


@admin_bp.route('/pos/checkout', methods=['POST'])
@admin_required
def pos_checkout():
    """
    Finalize a POS sale:
      - Create an Order record
      - Deduct stock from every variant
      - Optionally link to an employee for commission
      - Return receipt data as JSON
    """
    data         = request.json
    items        = data.get('items', [])
    payment_method = data.get('payment_method', 'cash')
    discount_type  = data.get('discount_type', 'flat')   # 'flat' or 'percent'
    discount_val   = float(data.get('discount_value', 0))
    employee_code  = data.get('employee_code', '').strip()
    customer_name  = data.get('customer_name', 'Walk-in Customer').strip()
    notes          = data.get('notes', '')

    if not items:
        return jsonify({'error': 'Cart is empty'}), 400

    # ── Calculate totals ───────────────────────────────────────
    subtotal = sum(float(i['price']) * int(i['qty']) for i in items)

    if discount_type == 'percent':
        discount_amount = round(subtotal * discount_val / 100, 2)
    else:
        discount_amount = min(discount_val, subtotal)

    taxable     = subtotal - discount_amount
    tax_rate    = 0.0          # Set to e.g. 0.05 for 5% GST if needed
    tax_amount  = round(taxable * tax_rate, 2)
    total       = round(taxable + tax_amount, 2)

    # ── Find or create a walk-in user ──────────────────────────
    walkin = User.query.filter_by(username='walkin').first()
    if not walkin:
        from werkzeug.security import generate_password_hash
        walkin = User(
            username='walkin', email='walkin@mbmaniyar.local',
            full_name='Walk-in Customer',
            password_hash=generate_password_hash('walkin123'),
            role='customer'
        )
        db.session.add(walkin)
        db.session.flush()

    # ── Generate order number ──────────────────────────────────
    import random
    order_number = f"POS-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"

    # ── Find employee if code provided ────────────────────────
    emp = None
    if employee_code:
        emp = Employee.query.filter_by(employee_code=employee_code).first()

    order = Order(
        order_number    = order_number,
        user_id         = walkin.id,
        order_type      = 'pos',
        status          = 'completed',
        subtotal        = subtotal,
        discount_amount = discount_amount,
        tax_amount      = tax_amount,
        total_amount    = total,
        payment_method  = payment_method,
        payment_status  = 'paid',
        customer_notes  = f"{customer_name}. {notes}".strip('. '),
        processed_by_id = current_user.id,
    )
    db.session.add(order)
    db.session.flush()

    receipt_items = []
    for i in items:
        variant = ProductVariant.query.get(int(i['variant_id']))
        if not variant:
            continue
        qty = int(i['qty'])
        # Deduct stock — real-time sync with online store
        variant.stock_quantity = max(0, variant.stock_quantity - qty)

        oi = OrderItem(
            order_id    = order.id,
            product_id  = variant.product_id,
            variant_id  = variant.id,
            quantity    = qty,
            unit_price  = float(i['price']),
            total_price = float(i['price']) * qty,
        )
        db.session.add(oi)
        receipt_items.append({
            'name'  : i['name'],
            'size'  : i['size'],
            'qty'   : qty,
            'price' : float(i['price']),
            'total' : float(i['price']) * qty,
        })

    # ── Commission for employee ───────────────────────────────
    if emp:
        commission = round(total * float(emp.commission_rate), 2)
        # Record in monthly salary
        today = date.today()
        sal = MonthlySalary.query.filter_by(
            employee_id=emp.id, month=today.month, year=today.year).first()
        if sal:
            sal.commission_earned = float(sal.commission_earned or 0) + commission
        else:
            sal = MonthlySalary(
                employee_id=emp.id, month=today.month, year=today.year,
                base_salary=emp.base_salary,
                commission_earned=commission,
            )
            db.session.add(sal)

    db.session.commit()

    return jsonify({
        'ok'            : True,
        'order_number'  : order_number,
        'customer_name' : customer_name,
        'items'         : receipt_items,
        'subtotal'      : subtotal,
        'discount'      : discount_amount,
        'tax'           : tax_amount,
        'total'         : total,
        'payment_method': payment_method,
        'employee'      : emp.user.full_name if emp else None,
        'commission'    : round(total * float(emp.commission_rate), 2) if emp else 0,
        'timestamp'     : datetime.now().strftime('%d %b %Y, %I:%M %p'),
        'store_name'    : 'M B MANIYAR',
        'store_address' : 'Main Road, Mantha, India',
    })
'''

# Append POS routes to existing routes.py
routes_path = os.path.join(BASE, "app/admin/routes.py")
with open(routes_path, 'r') as f:
    existing = f.read()

if 'def pos(' not in existing:
    with open(routes_path, 'a') as f:
        f.write(pos_routes)
    print("  ✅ POS routes appended to admin/routes.py")
else:
    print("  ⏭️  POS routes already exist in routes.py")

# ═══════════════════════════════════════════════════════════════
# 2. ADD POS LINK TO SIDEBAR
# ═══════════════════════════════════════════════════════════════
base_admin_path = os.path.join(BASE, "app/templates/admin/base_admin.html")
with open(base_admin_path, 'r') as f:
    base_content = f.read()

pos_nav = '''    <a href="{{ url_for('admin.pos') }}"
       class="nav-item {% if request.endpoint=='admin.pos' %}active{% endif %}"
       style="{% if request.endpoint=='admin.pos' %}background:rgba(245,166,35,.15);color:var(--accent){% endif %}">
      <i class="bi bi-cash-register"></i> POS Billing
    </a>'''

if 'admin.pos' not in base_content:
    base_content = base_content.replace(
        '<div class="nav-section-label">Sales</div>',
        '<div class="nav-section-label">Sales</div>\n' + pos_nav
    )
    with open(base_admin_path, 'w') as f:
        f.write(base_content)
    print("  ✅ POS link added to sidebar")
else:
    print("  ⏭️  POS link already in sidebar")

# ═══════════════════════════════════════════════════════════════
# 3. POS TEMPLATE
# ═══════════════════════════════════════════════════════════════
w("app/templates/admin/pos.html", r"""{% extends 'admin/base_admin.html' %}
{% block title %}POS Billing{% endblock %}
{% block page_title %}⚡ Point of Sale{% endblock %}

{% block extra_css %}
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Mono:wght@400;500;600&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── POS LAYOUT ── */
:root{
  --pos-bg:#080C14;--pos-panel:#0E1520;--pos-border:rgba(255,255,255,.07);
  --amber:#F5A623;--amber2:#FFD166;--green:#06D6A0;--red:#EF476F;
  --blue:#4A90E2;--purple:#9B5DE5;--ff-mono:'DM Mono',monospace;
}

.pos-wrap{
  display:grid;
  grid-template-columns:1fr 380px;
  gap:0;
  height:calc(100vh - 60px);
  margin:-1.8rem;
  background:var(--pos-bg);
  overflow:hidden;
}

/* ── LEFT PANEL ── */
.pos-left{
  display:flex;flex-direction:column;
  border-right:1px solid var(--pos-border);
  overflow:hidden;
}

/* Search bar */
.pos-search-wrap{
  padding:1rem 1.2rem;
  background:var(--pos-panel);
  border-bottom:1px solid var(--pos-border);
}
.pos-search-row{display:flex;gap:.7rem;align-items:center}
.pos-search-input{
  flex:1;background:rgba(255,255,255,.05);
  border:1.5px solid var(--pos-border);
  border-radius:10px;padding:.7rem 1rem .7rem 2.8rem;
  color:#fff;font-family:var(--ff-mono);font-size:.95rem;
  outline:none;transition:border-color .2s;
}
.pos-search-input:focus{border-color:var(--amber)}
.pos-search-input::placeholder{color:rgba(255,255,255,.25)}
.search-icon-pos{position:relative}
.search-icon-pos i{position:absolute;left:.85rem;top:50%;transform:translateY(-50%);color:rgba(255,255,255,.3);z-index:1}

/* Search results dropdown */
.search-results{
  position:absolute;top:calc(100% + 4px);left:0;right:0;z-index:500;
  background:#141C2E;border:1px solid var(--amber);border-radius:10px;
  overflow:hidden;box-shadow:0 12px 40px rgba(0,0,0,.5);display:none;
}
.search-result-item{
  padding:.7rem 1rem;cursor:pointer;border-bottom:1px solid var(--pos-border);
  transition:background .15s;display:flex;align-items:center;justify-content:space-between;
}
.search-result-item:hover{background:rgba(245,166,35,.1)}
.search-result-item:last-child{border-bottom:none}
.sri-name{font-size:.88rem;font-weight:600;color:#fff}
.sri-meta{font-size:.75rem;color:rgba(255,255,255,.4);margin-top:.1rem}
.sri-right{text-align:right}
.sri-price{font-family:var(--ff-mono);font-size:.9rem;color:var(--amber);font-weight:600}
.sri-size{font-size:.72rem;background:rgba(255,255,255,.08);padding:.1rem .45rem;border-radius:4px;margin-bottom:.2rem;display:inline-block}
.sri-stock{font-size:.7rem;color:var(--green)}

/* Category quick tiles */
.cat-bar{
  padding:.7rem 1.2rem;border-bottom:1px solid var(--pos-border);
  display:flex;gap:.5rem;overflow-x:auto;flex-shrink:0;
}
.cat-bar::-webkit-scrollbar{height:3px}
.cat-bar::-webkit-scrollbar-thumb{background:var(--amber);border-radius:2px}
.cat-chip{
  white-space:nowrap;padding:.35rem .9rem;border-radius:6px;
  font-size:.75rem;font-weight:600;border:1px solid var(--pos-border);
  color:rgba(255,255,255,.5);cursor:pointer;transition:all .2s;background:none;
}
.cat-chip:hover,.cat-chip.active{
  background:rgba(245,166,35,.15);border-color:var(--amber);color:var(--amber);
}

/* Quick product tiles grid */
.quick-grid{
  flex:1;overflow-y:auto;padding:1rem 1.2rem;
  display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:.7rem;
  align-content:start;
}
.quick-grid::-webkit-scrollbar{width:4px}
.quick-grid::-webkit-scrollbar-thumb{background:var(--pos-border);border-radius:2px}

.q-tile{
  background:var(--pos-panel);border:1px solid var(--pos-border);
  border-radius:12px;padding:.8rem;cursor:pointer;
  transition:all .2s cubic-bezier(.34,1.56,.64,1);
  position:relative;overflow:hidden;
}
.q-tile:hover{border-color:var(--amber);transform:translateY(-2px);box-shadow:0 6px 20px rgba(245,166,35,.15)}
.q-tile:active{transform:scale(.97)}
.q-tile-emoji{font-size:1.8rem;margin-bottom:.4rem}
.q-tile-brand{font-size:.62rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--amber);margin-bottom:.2rem}
.q-tile-name{font-size:.78rem;font-weight:600;color:#fff;line-height:1.3;margin-bottom:.4rem;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.q-tile-price{font-family:var(--ff-mono);font-size:.9rem;font-weight:700;color:var(--amber2)}
.q-tile-sizes{display:flex;gap:.2rem;flex-wrap:wrap;margin-top:.4rem}
.q-sz{font-size:.62rem;padding:.1rem .35rem;background:rgba(255,255,255,.07);border-radius:3px;color:rgba(255,255,255,.5);cursor:pointer;transition:all .15s}
.q-sz:hover{background:var(--amber);color:#000}
.q-sz.oos{opacity:.3;cursor:not-allowed;text-decoration:line-through}
.q-tile-stock{position:absolute;top:.5rem;right:.5rem;font-size:.62rem;font-weight:700;padding:.1rem .4rem;border-radius:50px}
.stock-ok{background:rgba(6,214,160,.15);color:var(--green)}
.stock-low{background:rgba(245,166,35,.15);color:var(--amber)}
.stock-oos{background:rgba(239,71,111,.15);color:var(--red)}

/* ── RIGHT PANEL — CART ── */
.pos-right{
  display:flex;flex-direction:column;
  background:var(--pos-panel);
  overflow:hidden;
}

.cart-header{
  padding:1rem 1.2rem;border-bottom:1px solid var(--pos-border);
  display:flex;align-items:center;justify-content:space-between;
  flex-shrink:0;
}
.cart-title{font-family:'Syne',sans-serif;font-size:1rem;font-weight:800;letter-spacing:.5px}
.cart-clear-btn{
  background:rgba(239,71,111,.1);border:1px solid rgba(239,71,111,.2);
  color:var(--red);border-radius:6px;padding:.3rem .7rem;
  font-size:.75rem;cursor:pointer;transition:all .2s;
}
.cart-clear-btn:hover{background:var(--red);color:#fff}

/* Customer + Employee row */
.cart-meta{
  padding:.7rem 1.2rem;border-bottom:1px solid var(--pos-border);
  display:flex;gap:.6rem;flex-shrink:0;
}
.meta-input{
  flex:1;background:rgba(255,255,255,.04);border:1px solid var(--pos-border);
  color:#fff;border-radius:7px;padding:.45rem .7rem;font-size:.8rem;
  font-family:'DM Sans',sans-serif;outline:none;transition:border-color .2s;
}
.meta-input:focus{border-color:var(--amber)}
.meta-input::placeholder{color:rgba(255,255,255,.25)}

/* Cart items list */
.cart-items{
  flex:1;overflow-y:auto;padding:.5rem 0;
}
.cart-items::-webkit-scrollbar{width:3px}
.cart-items::-webkit-scrollbar-thumb{background:var(--pos-border)}

.cart-empty{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  height:100%;color:rgba(255,255,255,.15);text-align:center;padding:2rem;
}
.cart-empty i{font-size:3rem;display:block;margin-bottom:.75rem}
.cart-empty p{font-size:.85rem;line-height:1.6}

.cart-item{
  padding:.65rem 1.2rem;border-bottom:1px solid rgba(255,255,255,.04);
  display:flex;align-items:center;gap:.7rem;transition:background .15s;
}
.cart-item:hover{background:rgba(255,255,255,.02)}
.ci-info{flex:1;min-width:0}
.ci-name{font-size:.82rem;font-weight:600;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ci-sub{font-size:.7rem;color:rgba(255,255,255,.35);margin-top:.1rem}
.ci-qty-wrap{display:flex;align-items:center;gap:.3rem}
.ci-qty-btn{
  width:22px;height:22px;border-radius:5px;border:none;
  background:rgba(255,255,255,.07);color:#fff;font-size:.85rem;
  cursor:pointer;display:flex;align-items:center;justify-content:center;
  transition:all .15s;font-weight:700;
}
.ci-qty-btn:hover{background:var(--amber);color:#000}
.ci-qty{
  font-family:var(--ff-mono);font-size:.85rem;font-weight:700;
  width:24px;text-align:center;color:#fff;
}
.ci-price{
  font-family:var(--ff-mono);font-size:.85rem;font-weight:700;
  color:var(--amber2);white-space:nowrap;min-width:60px;text-align:right;
}
.ci-remove{background:none;border:none;color:rgba(255,255,255,.15);cursor:pointer;font-size:.9rem;padding:.1rem;transition:color .15s}
.ci-remove:hover{color:var(--red)}

/* Discount row */
.discount-row{
  padding:.7rem 1.2rem;border-top:1px solid var(--pos-border);
  display:flex;gap:.5rem;align-items:center;flex-shrink:0;
}
.disc-select{
  background:rgba(255,255,255,.05);border:1px solid var(--pos-border);
  color:#fff;border-radius:7px;padding:.4rem .6rem;font-size:.8rem;outline:none;
}
.disc-input{
  flex:1;background:rgba(255,255,255,.04);border:1px solid var(--pos-border);
  color:#fff;border-radius:7px;padding:.4rem .7rem;font-size:.85rem;
  font-family:var(--ff-mono);outline:none;transition:border-color .2s;
}
.disc-input:focus{border-color:var(--amber)}
.disc-apply-btn{
  background:rgba(245,166,35,.15);border:1px solid rgba(245,166,35,.3);
  color:var(--amber);border-radius:7px;padding:.4rem .9rem;font-size:.8rem;
  font-weight:600;cursor:pointer;transition:all .2s;white-space:nowrap;
}
.disc-apply-btn:hover{background:var(--amber);color:#000}

/* Totals block */
.totals-block{
  padding:.9rem 1.2rem;border-top:1px solid var(--pos-border);
  flex-shrink:0;background:rgba(0,0,0,.2);
}
.total-row{
  display:flex;justify-content:space-between;align-items:center;
  margin-bottom:.4rem;font-size:.83rem;color:rgba(255,255,255,.5);
}
.total-row.grand{
  font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;
  color:#fff;margin-top:.5rem;padding-top:.5rem;border-top:1px solid var(--pos-border);
}
.total-row.grand span:last-child{color:var(--amber2)}
.total-row .disc-val{color:var(--green)}

/* Payment methods */
.payment-section{
  padding:.8rem 1.2rem;border-top:1px solid var(--pos-border);
  flex-shrink:0;
}
.pay-label-pos{font-size:.68rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:rgba(255,255,255,.3);margin-bottom:.5rem}
.pay-methods{display:flex;gap:.5rem}
.pay-btn{
  flex:1;padding:.55rem .5rem;border-radius:8px;border:1.5px solid var(--pos-border);
  background:none;color:rgba(255,255,255,.5);font-size:.78rem;font-weight:600;
  cursor:pointer;transition:all .2s;text-align:center;font-family:'DM Sans',sans-serif;
}
.pay-btn:hover{border-color:rgba(255,255,255,.3);color:#fff}
.pay-btn.active{border-color:var(--amber);background:rgba(245,166,35,.12);color:var(--amber)}
.pay-btn i{display:block;font-size:1.1rem;margin-bottom:.2rem}

/* CHARGE button */
.charge-btn{
  margin:0 1.2rem .9rem;border:none;border-radius:12px;padding:1rem;
  background:linear-gradient(135deg,var(--amber),#E8903A);
  color:#1A0E00;font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800;
  cursor:pointer;transition:all .25s;letter-spacing:.5px;
  box-shadow:0 6px 24px rgba(245,166,35,.3);
  display:flex;align-items:center;justify-content:center;gap:.6rem;
  flex-shrink:0;
}
.charge-btn:hover{transform:translateY(-2px);box-shadow:0 10px 32px rgba(245,166,35,.4)}
.charge-btn:active{transform:scale(.98)}
.charge-btn:disabled{opacity:.4;cursor:not-allowed;transform:none}

/* ── RECEIPT MODAL ── */
.receipt-overlay{
  position:fixed;inset:0;background:rgba(0,0,0,.8);z-index:9999;
  display:none;align-items:center;justify-content:center;
  backdrop-filter:blur(6px);
}
.receipt-modal{
  background:#fff;color:#111;border-radius:16px;width:360px;max-height:90vh;
  overflow-y:auto;box-shadow:0 30px 80px rgba(0,0,0,.5);
}
.receipt-body{padding:1.5rem}
.receipt-store{text-align:center;margin-bottom:1rem;padding-bottom:1rem;border-bottom:2px dashed #ddd}
.receipt-store h3{font-family:'Syne',sans-serif;font-size:1.3rem;color:#111}
.receipt-store p{font-size:.78rem;color:#888;margin:.1rem 0}
.receipt-order{
  background:#F8F8F8;border-radius:8px;padding:.6rem .9rem;margin-bottom:1rem;
  font-size:.82rem;display:flex;justify-content:space-between;
}
.receipt-items table{width:100%;border-collapse:collapse;font-size:.82rem;margin-bottom:.8rem}
.receipt-items th{text-align:left;padding:.3rem .4rem;color:#888;font-weight:600;border-bottom:1px solid #eee;font-size:.72rem;text-transform:uppercase}
.receipt-items td{padding:.35rem .4rem;border-bottom:1px solid #f5f5f5}
.receipt-items td:last-child{text-align:right;font-weight:600}
.receipt-totals{border-top:1px solid #eee;padding-top:.6rem}
.rt-row{display:flex;justify-content:space-between;font-size:.83rem;margin-bottom:.25rem;color:#555}
.rt-total{display:flex;justify-content:space-between;font-size:1.1rem;font-weight:800;color:#111;margin-top:.4rem;padding-top:.4rem;border-top:2px solid #111}
.receipt-footer{text-align:center;margin-top:1rem;padding-top:1rem;border-top:2px dashed #ddd;font-size:.75rem;color:#aaa}
.receipt-actions{display:flex;gap:.6rem;padding:1rem 1.5rem 1.5rem}
.btn-print{flex:1;padding:.7rem;border:none;border-radius:8px;background:#111;color:#fff;font-weight:700;cursor:pointer;font-size:.9rem}
.btn-new-sale{flex:1;padding:.7rem;border:2px solid #111;border-radius:8px;background:#fff;color:#111;font-weight:700;cursor:pointer;font-size:.9rem}

/* Animations */
@keyframes slideInCart{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:translateX(0)}}
.cart-item{animation:slideInCart .2s ease}
@keyframes popIn{0%{transform:scale(.8);opacity:0}70%{transform:scale(1.05)}100%{transform:scale(1);opacity:1}}
.receipt-modal{animation:popIn .3s cubic-bezier(.34,1.56,.64,1)}

/* Size picker popup */
.size-picker-overlay{
  position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:8000;
  display:none;align-items:center;justify-content:center;
}
.size-picker-modal{
  background:#141C2E;border:1px solid var(--pos-border);border-radius:16px;
  padding:1.5rem;min-width:300px;box-shadow:0 20px 60px rgba(0,0,0,.5);
}
.sp-title{font-family:'Syne',sans-serif;font-size:1rem;font-weight:800;margin-bottom:.4rem}
.sp-price{font-family:var(--ff-mono);color:var(--amber);margin-bottom:1rem;font-size:.9rem}
.sp-grid{display:flex;flex-wrap:wrap;gap:.5rem}
.sp-btn{
  padding:.6rem 1.2rem;border-radius:8px;border:1.5px solid var(--pos-border);
  background:none;color:#fff;font-size:.9rem;font-weight:600;cursor:pointer;
  transition:all .2s;font-family:'DM Sans',sans-serif;
}
.sp-btn:hover{border-color:var(--amber);color:var(--amber);background:rgba(245,166,35,.1)}
.sp-btn.oos-sp{opacity:.3;cursor:not-allowed;text-decoration:line-through}
.sp-cancel{
  margin-top:1rem;width:100%;padding:.55rem;background:rgba(255,255,255,.05);
  border:1px solid var(--pos-border);color:rgba(255,255,255,.5);border-radius:8px;
  cursor:pointer;font-size:.85rem;transition:all .2s;
}
.sp-cancel:hover{background:rgba(239,71,111,.1);color:var(--red);border-color:var(--red)}
</style>
{% endblock %}

{% block content %}
<div class="pos-wrap">

  <!-- ══════════════════ LEFT: PRODUCTS ══════════════════ -->
  <div class="pos-left">

    <!-- Search bar -->
    <div class="pos-search-wrap">
      <div class="pos-search-row">
        <div class="search-icon-pos" style="position:relative;flex:1">
          <i class="bi bi-upc-scan" style="position:absolute;left:.85rem;top:50%;transform:translateY(-50%);color:rgba(255,255,255,.3);z-index:1"></i>
          <input type="text" id="posSearch" class="pos-search-input"
                 placeholder="Scan barcode or search by name / SKU…"
                 autocomplete="off" autofocus>
          <div class="search-results" id="searchResults"></div>
        </div>
        <button onclick="clearSearch()" class="cart-clear-btn" style="white-space:nowrap">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
    </div>

    <!-- Category filter bar -->
    <div class="cat-bar">
      <button class="cat-chip active" onclick="filterCat('all', this)">All</button>
      {% for cat in categories %}
      <button class="cat-chip" onclick="filterCat('{{ cat.slug }}', this)">{{ cat.name }}</button>
      {% endfor %}
    </div>

    <!-- Quick product tiles -->
    <div class="quick-grid" id="quickGrid">
      {% for p in products %}
      {% set total_stock = p.variants | sum(attribute='stock_quantity') %}
      <div class="q-tile"
           data-cat="{{ p.category.slug }}"
           data-product-id="{{ p.id }}"
           onclick="openSizePicker({{ p.id }}, '{{ p.name|replace("'","") }}', {{ p.price }}, {{ p.brand.name|tojson }})">
        <!-- Stock badge -->
        <span class="q-tile-stock {% if total_stock == 0 %}stock-oos{% elif total_stock < 10 %}stock-low{% else %}stock-ok{% endif %}">
          {{ total_stock }}
        </span>
        <div class="q-tile-emoji">
          {% if 'shirt' in p.name.lower() %}👔
          {% elif 'trouser' in p.name.lower() or 'pant' in p.name.lower() %}👖
          {% elif 'kurta' in p.name.lower() %}🧣
          {% elif 'kid' in p.name.lower() %}👕
          {% elif 't-shirt' in p.name.lower() or 'polo' in p.name.lower() %}👕
          {% else %}🛍️{% endif %}
        </div>
        <div class="q-tile-brand">{{ p.brand.name }}</div>
        <div class="q-tile-name">{{ p.name }}</div>
        <div class="q-tile-price">₹{{ "%.0f"|format(p.price) }}</div>
        <div class="q-tile-sizes">
          {% for v in p.variants %}
          <span class="q-sz {% if v.is_out_of_stock %}oos{% endif %}"
                onclick="event.stopPropagation(); {% if not v.is_out_of_stock %}addToCart({{ v.id }}, '{{ p.name|replace("'","") }}', '{{ v.size }}', {{ p.price }}, {{ v.stock_quantity }}){% endif %}">
            {{ v.size }}
          </span>
          {% endfor %}
        </div>
      </div>
      {% endfor %}
    </div>
  </div>

  <!-- ══════════════════ RIGHT: CART ══════════════════ -->
  <div class="pos-right">

    <!-- Cart header -->
    <div class="cart-header">
      <div class="cart-title">🛒 Current Bill</div>
      <button class="cart-clear-btn" onclick="clearCart()">
        <i class="bi bi-trash3 me-1"></i>Clear
      </button>
    </div>

    <!-- Customer & Employee -->
    <div class="cart-meta">
      <input type="text" id="customerName" class="meta-input"
             placeholder="👤 Customer name (optional)">
      <input type="text" id="employeeCode" class="meta-input"
             placeholder="🏷 Employee code"
             list="empList">
      <datalist id="empList">
        {% for emp in employees %}
        <option value="{{ emp.employee_code }}">{{ emp.user.full_name }}</option>
        {% endfor %}
      </datalist>
    </div>

    <!-- Cart items -->
    <div class="cart-items" id="cartItems">
      <div class="cart-empty" id="cartEmpty">
        <i class="bi bi-bag-x"></i>
        <p>Cart is empty.<br>Search or tap a product to add it.</p>
      </div>
    </div>

    <!-- Discount row -->
    <div class="discount-row">
      <select id="discType" class="disc-select">
        <option value="flat">₹ Flat</option>
        <option value="percent">% Off</option>
      </select>
      <input type="number" id="discValue" class="disc-input"
             placeholder="0" min="0" step="0.01">
      <button class="disc-apply-btn" onclick="applyDiscount()">
        Apply Discount
      </button>
    </div>

    <!-- Totals -->
    <div class="totals-block">
      <div class="total-row">
        <span>Subtotal</span>
        <span id="subtotalDisplay">₹0.00</span>
      </div>
      <div class="total-row" id="discountRow" style="display:none">
        <span>Discount</span>
        <span class="disc-val" id="discountDisplay">-₹0.00</span>
      </div>
      <div class="total-row" id="taxRow" style="display:none">
        <span>Tax</span>
        <span id="taxDisplay">₹0.00</span>
      </div>
      <div class="total-row grand">
        <span>TOTAL</span>
        <span id="totalDisplay">₹0.00</span>
      </div>
    </div>

    <!-- Payment methods -->
    <div class="payment-section">
      <div class="pay-label-pos">Payment Method</div>
      <div class="pay-methods">
        <button class="pay-btn active" data-method="cash" onclick="selectPayment('cash', this)">
          <i class="bi bi-cash"></i>Cash
        </button>
        <button class="pay-btn" data-method="upi" onclick="selectPayment('upi', this)">
          <i class="bi bi-phone"></i>UPI
        </button>
        <button class="pay-btn" data-method="card" onclick="selectPayment('card', this)">
          <i class="bi bi-credit-card"></i>Card
        </button>
      </div>
    </div>

    <!-- CHARGE button -->
    <button class="charge-btn" id="chargeBtn" onclick="finalizeSale()" disabled>
      <i class="bi bi-lightning-charge-fill"></i>
      <span id="chargeBtnText">ADD ITEMS TO CHARGE</span>
    </button>

  </div>
</div>

<!-- ══════════════════ SIZE PICKER MODAL ══════════════════ -->
<div class="size-picker-overlay" id="sizePickerOverlay" onclick="closeSizePicker()">
  <div class="size-picker-modal" onclick="event.stopPropagation()">
    <div class="sp-title" id="spTitle">Select Size</div>
    <div class="sp-price" id="spPrice"></div>
    <div class="sp-grid" id="spGrid"></div>
    <button class="sp-cancel" onclick="closeSizePicker()">Cancel</button>
  </div>
</div>

<!-- ══════════════════ RECEIPT MODAL ══════════════════ -->
<div class="receipt-overlay" id="receiptOverlay">
  <div class="receipt-modal">
    <div class="receipt-body" id="receiptBody"></div>
    <div class="receipt-actions">
      <button class="btn-print" onclick="window.print()">🖨 Print Receipt</button>
      <button class="btn-new-sale" onclick="newSale()">✚ New Sale</button>
    </div>
  </div>
</div>

<!-- Product data for JS -->
<script>
const PRODUCTS = {{ products | tojson(indent=0) if false else '{}' }};

// Build variant map from server data
const VARIANTS = {};
{% for p in products %}
  {% for v in p.variants %}
  VARIANTS[{{ v.id }}] = {
    id: {{ v.id }},
    product_id: {{ p.id }},
    name: {{ p.name | tojson }},
    brand: {{ p.brand.name | tojson }},
    size: {{ v.size | tojson }},
    price: {{ p.price }},
    stock: {{ v.stock_quantity }},
    sku: {{ p.sku | tojson }},
  };
  {% endfor %}
{% endfor %}

// Product sizes map for size picker
const PRODUCT_SIZES = {};
{% for p in products %}
PRODUCT_SIZES[{{ p.id }}] = [
  {% for v in p.variants %}
  { id: {{ v.id }}, size: {{ v.size | tojson }}, stock: {{ v.stock_quantity }} },
  {% endfor %}
];
{% endfor %}
</script>

{% endblock %}

{% block extra_js %}
<script>
// ── STATE ────────────────────────────────────────────────────
let cart = {};        // { variantId: { ...info, qty } }
let discountAmount = 0;
let discountType   = 'flat';
let discountValue  = 0;
let paymentMethod  = 'cash';
let TAX_RATE       = 0;   // Set to 0.05 for 5% GST

// ── SEARCH ───────────────────────────────────────────────────
let searchTimer;
document.getElementById('posSearch').addEventListener('input', function() {
  clearTimeout(searchTimer);
  const q = this.value.trim();
  if (!q) { hideResults(); return; }
  searchTimer = setTimeout(() => doSearch(q), 200);
});

document.getElementById('posSearch').addEventListener('keydown', function(e) {
  if (e.key === 'Escape') { clearSearch(); }
});

async function doSearch(q) {
  const res  = await fetch(`/admin/pos/search?q=${encodeURIComponent(q)}`);
  const data = await res.json();
  const box  = document.getElementById('searchResults');

  if (!data.length) {
    box.innerHTML = `<div class="search-result-item" style="color:rgba(255,255,255,.3);cursor:default">No results for "${q}"</div>`;
    box.style.display = 'block';
    return;
  }

  box.innerHTML = data.map(r => `
    <div class="search-result-item" onclick="addToCart(${r.variant_id},'${r.name.replace(/'/g,"\\'")}','${r.size}',${r.price},${r.stock}); hideResults(); document.getElementById('posSearch').value=''">
      <div>
        <div class="sri-name">${r.name}</div>
        <div class="sri-meta">${r.brand} · ${r.sku}</div>
      </div>
      <div class="sri-right">
        <span class="sri-size">${r.size}</span><br>
        <span class="sri-price">₹${r.price.toFixed(0)}</span><br>
        <span class="sri-stock">${r.stock} in stock</span>
      </div>
    </div>`).join('');
  box.style.display = 'block';
}

function hideResults() {
  document.getElementById('searchResults').style.display = 'none';
}
function clearSearch() {
  document.getElementById('posSearch').value = '';
  hideResults();
}
document.addEventListener('click', (e) => {
  if (!e.target.closest('.search-icon-pos')) hideResults();
});

// ── SIZE PICKER ───────────────────────────────────────────────
let _sp_pid, _sp_name, _sp_price;
function openSizePicker(pid, name, price, brand) {
  _sp_pid = pid; _sp_name = name; _sp_price = price;
  document.getElementById('spTitle').textContent = name;
  document.getElementById('spPrice').textContent = `₹${price.toFixed(0)} · ${brand}`;
  const sizes = PRODUCT_SIZES[pid] || [];
  document.getElementById('spGrid').innerHTML = sizes.map(v => `
    <button class="sp-btn ${v.stock === 0 ? 'oos-sp' : ''}"
      ${v.stock === 0 ? 'disabled' : `onclick="addToCart(${v.id},'${name.replace(/'/g,"\\'")}','${v.size}',${price},${v.stock}); closeSizePicker()"`}>
      ${v.size}
      <span style="font-size:.65rem;opacity:.5;display:block">${v.stock > 0 ? v.stock+' left' : 'OOS'}</span>
    </button>`).join('');
  document.getElementById('sizePickerOverlay').style.display = 'flex';
}
function closeSizePicker() {
  document.getElementById('sizePickerOverlay').style.display = 'none';
}

// ── CART ──────────────────────────────────────────────────────
function addToCart(variantId, name, size, price, stock) {
  const key = variantId;
  if (cart[key]) {
    if (cart[key].qty >= stock) {
      showToast(`Only ${stock} in stock!`, 'error');
      return;
    }
    cart[key].qty++;
  } else {
    cart[key] = { variantId, name, size, price, stock, qty: 1 };
  }
  renderCart();
  showToast(`${name} (${size}) added`, 'success');
}

function changeQty(variantId, delta) {
  if (!cart[variantId]) return;
  const newQty = cart[variantId].qty + delta;
  if (newQty <= 0) { removeFromCart(variantId); return; }
  if (newQty > cart[variantId].stock) { showToast('Not enough stock!', 'error'); return; }
  cart[variantId].qty = newQty;
  renderCart();
}

function removeFromCart(variantId) {
  delete cart[variantId];
  renderCart();
}

function clearCart() {
  cart = {};
  discountAmount = 0;
  discountValue  = 0;
  document.getElementById('discValue').value = '';
  renderCart();
}

function renderCart() {
  const keys = Object.keys(cart);
  const empty = document.getElementById('cartEmpty');
  const itemsDiv = document.getElementById('cartItems');

  // Remove old item rows (keep empty div)
  itemsDiv.querySelectorAll('.cart-item').forEach(el => el.remove());

  if (!keys.length) {
    empty.style.display = 'flex';
    updateTotals();
    updateChargeBtn();
    return;
  }
  empty.style.display = 'none';

  keys.forEach(key => {
    const item = cart[key];
    const div  = document.createElement('div');
    div.className = 'cart-item';
    div.innerHTML = `
      <div class="ci-info">
        <div class="ci-name">${item.name}</div>
        <div class="ci-sub">Size: ${item.size} &nbsp;·&nbsp; ₹${item.price.toFixed(0)} each</div>
      </div>
      <div class="ci-qty-wrap">
        <button class="ci-qty-btn" onclick="changeQty(${key}, -1)">−</button>
        <span class="ci-qty">${item.qty}</span>
        <button class="ci-qty-btn" onclick="changeQty(${key}, 1)">+</button>
      </div>
      <div class="ci-price">₹${(item.price * item.qty).toFixed(0)}</div>
      <button class="ci-remove" onclick="removeFromCart(${key})">
        <i class="bi bi-x-lg"></i>
      </button>
    `;
    itemsDiv.appendChild(div);
  });

  updateTotals();
  updateChargeBtn();
}

// ── DISCOUNT ─────────────────────────────────────────────────
function applyDiscount() {
  discountType  = document.getElementById('discType').value;
  discountValue = parseFloat(document.getElementById('discValue').value) || 0;
  const subtotal = calcSubtotal();
  if (discountType === 'percent') {
    discountAmount = subtotal * discountValue / 100;
  } else {
    discountAmount = Math.min(discountValue, subtotal);
  }
  updateTotals();
  showToast('Discount applied!', 'success');
}

// ── TOTALS ────────────────────────────────────────────────────
function calcSubtotal() {
  return Object.values(cart).reduce((s, i) => s + i.price * i.qty, 0);
}

function updateTotals() {
  const subtotal = calcSubtotal();
  const taxable  = subtotal - discountAmount;
  const tax      = taxable * TAX_RATE;
  const total    = taxable + tax;

  document.getElementById('subtotalDisplay').textContent = `₹${subtotal.toFixed(2)}`;
  document.getElementById('totalDisplay').textContent    = `₹${total.toFixed(2)}`;

  const discRow = document.getElementById('discountRow');
  if (discountAmount > 0) {
    discRow.style.display = 'flex';
    document.getElementById('discountDisplay').textContent = `-₹${discountAmount.toFixed(2)}`;
  } else { discRow.style.display = 'none'; }

  const taxRow = document.getElementById('taxRow');
  if (TAX_RATE > 0) {
    taxRow.style.display = 'flex';
    document.getElementById('taxDisplay').textContent = `₹${tax.toFixed(2)}`;
  } else { taxRow.style.display = 'none'; }
}

function updateChargeBtn() {
  const btn  = document.getElementById('chargeBtn');
  const text = document.getElementById('chargeBtnText');
  const has  = Object.keys(cart).length > 0;
  btn.disabled = !has;
  if (has) {
    const total = calcSubtotal() - discountAmount;
    text.textContent = `CHARGE  ₹${total.toFixed(2)}`;
  } else {
    text.textContent = 'ADD ITEMS TO CHARGE';
  }
}

// ── PAYMENT ───────────────────────────────────────────────────
function selectPayment(method, btn) {
  paymentMethod = method;
  document.querySelectorAll('.pay-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

// ── FINALIZE SALE ─────────────────────────────────────────────
async function finalizeSale() {
  const keys = Object.keys(cart);
  if (!keys.length) return;

  const btn = document.getElementById('chargeBtn');
  btn.disabled = true;
  btn.innerHTML = '<i class="bi bi-arrow-repeat" style="animation:spin 1s linear infinite"></i> Processing…';

  const items = keys.map(k => ({
    variant_id: cart[k].variantId,
    name      : cart[k].name,
    size      : cart[k].size,
    price     : cart[k].price,
    qty       : cart[k].qty,
  }));

  const payload = {
    items,
    payment_method : paymentMethod,
    discount_type  : document.getElementById('discType').value,
    discount_value : parseFloat(document.getElementById('discValue').value) || 0,
    employee_code  : document.getElementById('employeeCode').value.trim(),
    customer_name  : document.getElementById('customerName').value.trim() || 'Walk-in Customer',
    notes          : '',
  };

  try {
    const res  = await fetch('/admin/pos/checkout', {
      method : 'POST',
      headers: {'Content-Type':'application/json'},
      body   : JSON.stringify(payload),
    });
    const data = await res.json();

    if (data.ok) {
      showReceipt(data);
    } else {
      showToast(data.error || 'Checkout failed!', 'error');
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-lightning-charge-fill"></i><span>CHARGE</span>';
    }
  } catch(e) {
    showToast('Network error. Please try again.', 'error');
    btn.disabled = false;
  }
}

// ── RECEIPT ───────────────────────────────────────────────────
function showReceipt(data) {
  const itemRows = data.items.map(i =>
    `<tr><td>${i.name}<br><small style="color:#888">${i.size}</small></td>
     <td style="text-align:center">${i.qty}</td>
     <td style="text-align:right">₹${i.price.toFixed(0)}</td>
     <td>₹${i.total.toFixed(0)}</td></tr>`
  ).join('');

  let totalsHtml = `
    <div class="rt-row"><span>Subtotal</span><span>₹${data.subtotal.toFixed(2)}</span></div>`;
  if (data.discount > 0)
    totalsHtml += `<div class="rt-row"><span>Discount</span><span style="color:green">-₹${data.discount.toFixed(2)}</span></div>`;
  if (data.tax > 0)
    totalsHtml += `<div class="rt-row"><span>Tax</span><span>₹${data.tax.toFixed(2)}</span></div>`;
  totalsHtml += `<div class="rt-total"><span>TOTAL</span><span>₹${data.total.toFixed(2)}</span></div>`;

  document.getElementById('receiptBody').innerHTML = `
    <div class="receipt-store">
      <h3>${data.store_name}</h3>
      <p>${data.store_address}</p>
      <p style="margin-top:.3rem;font-size:.7rem">${data.timestamp}</p>
    </div>
    <div class="receipt-order">
      <span><b>Order:</b> ${data.order_number}</span>
      <span><b>Pay:</b> ${data.payment_method.toUpperCase()}</span>
    </div>
    ${data.employee ? `<div style="font-size:.78rem;color:#888;margin-bottom:.7rem;padding:.4rem .6rem;background:#f5f5f5;border-radius:6px">Staff: ${data.employee} · Commission: ₹${data.commission.toFixed(2)}</div>` : ''}
    <div class="receipt-items">
      <table>
        <thead><tr><th>Item</th><th style="text-align:center">Qty</th><th style="text-align:right">Price</th><th>Total</th></tr></thead>
        <tbody>${itemRows}</tbody>
      </table>
    </div>
    <div class="receipt-totals">${totalsHtml}</div>
    <div class="receipt-footer">
      <p>Thank you, ${data.customer_name}!</p>
      <p>Visit again at M B MANIYAR, Mantha</p>
    </div>
  `;

  document.getElementById('receiptOverlay').style.display = 'flex';
}

function newSale() {
  document.getElementById('receiptOverlay').style.display = 'none';
  clearCart();
  document.getElementById('customerName').value = '';
  document.getElementById('employeeCode').value = '';
  document.getElementById('discValue').value    = '';
  discountAmount = 0;
  document.getElementById('posSearch').focus();

  // Re-enable charge button
  const btn = document.getElementById('chargeBtn');
  btn.disabled = true;
  btn.innerHTML = '<i class="bi bi-lightning-charge-fill"></i><span id="chargeBtnText">ADD ITEMS TO CHARGE</span>';
}

// ── CATEGORY FILTER ───────────────────────────────────────────
function filterCat(slug, btn) {
  document.querySelectorAll('.cat-chip').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.q-tile').forEach(tile => {
    tile.style.display = (slug === 'all' || tile.dataset.cat === slug) ? '' : 'none';
  });
}

// ── TOAST ─────────────────────────────────────────────────────
function showToast(msg, type='success') {
  const t = document.createElement('div');
  t.style.cssText = `
    position:fixed;bottom:2rem;left:50%;transform:translateX(-50%);
    background:${type==='error'?'#EF476F':'#06D6A0'};color:#fff;
    padding:.6rem 1.4rem;border-radius:50px;font-size:.85rem;font-weight:600;
    z-index:99999;box-shadow:0 4px 20px rgba(0,0,0,.3);
    animation:slideUp .3s ease;pointer-events:none;
  `;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2000);
}

// Spin animation for loading
const style = document.createElement('style');
style.textContent = '@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}} @keyframes slideUp{from{opacity:0;transform:translate(-50%,20px)}to{opacity:1;transform:translate(-50%,0)}}';
document.head.appendChild(style);

// Init
renderCart();
</script>
{% endblock %}
""")

print()
print("="*55)
print("  🎉 POS system built successfully!")
print("  Run: python3 run.py")
print("  URL: http://localhost:5000/admin/pos")
print("="*55)

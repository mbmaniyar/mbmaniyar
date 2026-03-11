#!/usr/bin/env python3
"""
Step 4 Builder — Full Admin Dashboard
Run: python3 build_admin.py
"""
import os, sys

BASE = os.path.expanduser("~/Desktop/mbmaniyar")

def w(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ {path}")

# ══════════════════════════════════════════════════════════════════════════════
# 1. ADMIN ROUTES
# ══════════════════════════════════════════════════════════════════════════════
w("app/admin/routes.py", r"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from app.models import (db, User, Product, ProductVariant, Category, Brand,
                         Employee, Order, OrderItem, Shift, Task, MonthlySalary)
from decimal import Decimal
from datetime import date, datetime
import os, json

admin_bp = Blueprint('admin', __name__)
ALLOWED_IMG = {'png','jpg','jpeg','gif','webp'}

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def allowed_file(fn):
    return '.' in fn and fn.rsplit('.',1)[1].lower() in ALLOWED_IMG

@admin_bp.route('/')
@admin_required
def dashboard():
    stats = {
        'total_products' : Product.query.filter_by(is_active=True).count(),
        'total_orders'   : Order.query.count(),
        'pending_orders' : Order.query.filter_by(status='confirmed').count(),
        'total_customers': User.query.filter_by(role='customer').count(),
        'total_employees': Employee.query.count(),
        'low_stock'      : ProductVariant.query.filter(
                             ProductVariant.stock_quantity <= ProductVariant.low_stock_threshold,
                             ProductVariant.stock_quantity > 0).count(),
        'out_of_stock'   : ProductVariant.query.filter_by(stock_quantity=0).count(),
        'total_revenue'  : db.session.query(db.func.sum(Order.total_amount))
                             .filter_by(payment_status='paid').scalar() or 0,
    }
    recent_orders   = Order.query.order_by(Order.created_at.desc()).limit(8).all()
    low_stock_items = ProductVariant.query.filter(
        ProductVariant.stock_quantity <= ProductVariant.low_stock_threshold,
        ProductVariant.stock_quantity > 0).limit(6).all()
    return render_template('admin/dashboard.html',
        stats=stats, recent_orders=recent_orders, low_stock_items=low_stock_items)

@admin_bp.route('/products')
@admin_required
def products():
    search=request.args.get('q','').strip(); cat_id=request.args.get('cat','all'); brand_id=request.args.get('brand','all')
    q=Product.query
    if search: q=q.filter(Product.name.ilike(f'%{search}%'))
    if cat_id!='all': q=q.filter_by(category_id=int(cat_id))
    if brand_id!='all': q=q.filter_by(brand_id=int(brand_id))
    return render_template('admin/products.html',
        products=q.order_by(Product.created_at.desc()).all(),
        categories=Category.query.all(), brands=Brand.query.all(),
        search=search, active_cat=cat_id, active_brand=brand_id)

@admin_bp.route('/products/add', methods=['GET','POST'])
@admin_required
def add_product():
    categories=Category.query.all(); brands=Brand.query.all()
    if request.method=='POST':
        name=request.form.get('name','').strip(); sku=request.form.get('sku','').strip()
        price=request.form.get('price',type=float); mrp=request.form.get('mrp',type=float) or None
        cat_id=request.form.get('category_id',type=int); brand_id=request.form.get('brand_id',type=int)
        description=request.form.get('description','').strip()
        is_online=bool(request.form.get('is_online'))
        sizes_raw=request.form.get('sizes_json','[]')
        if not all([name,sku,price,cat_id,brand_id]):
            flash('Fill all required fields.','danger')
            return render_template('admin/product_form.html',categories=categories,brands=brands,product=None)
        if Product.query.filter_by(sku=sku).first():
            flash(f'SKU {sku} already exists.','danger')
            return render_template('admin/product_form.html',categories=categories,brands=brands,product=None)
        img_filename=None
        if 'image' in request.files:
            file=request.files['image']
            if file and file.filename and allowed_file(file.filename):
                from flask import current_app
                filename=secure_filename(f"{sku}_{file.filename}")
                upload_path=current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_path,exist_ok=True)
                file.save(os.path.join(upload_path,filename))
                img_filename=filename
        product=Product(name=name,sku=sku,price=price,mrp=mrp,category_id=cat_id,
            brand_id=brand_id,description=description,is_online=is_online,
            is_active=True,image_filename=img_filename)
        db.session.add(product); db.session.flush()
        try:
            for s in json.loads(sizes_raw):
                if s.get('size','').strip():
                    db.session.add(ProductVariant(product_id=product.id,size=s['size'].strip(),
                        stock_quantity=int(s.get('stock',0)),low_stock_threshold=int(s.get('threshold',3))))
        except: pass
        db.session.commit()
        flash(f'Product "{name}" added! ✅','success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html',categories=categories,brands=brands,product=None)

@admin_bp.route('/products/edit/<int:pid>', methods=['GET','POST'])
@admin_required
def edit_product(pid):
    product=Product.query.get_or_404(pid); categories=Category.query.all(); brands=Brand.query.all()
    if request.method=='POST':
        product.name=request.form.get('name','').strip()
        product.price=request.form.get('price',type=float)
        product.mrp=request.form.get('mrp',type=float) or None
        product.category_id=request.form.get('category_id',type=int)
        product.brand_id=request.form.get('brand_id',type=int)
        product.description=request.form.get('description','').strip()
        product.is_online=bool(request.form.get('is_online'))
        product.is_active=bool(request.form.get('is_active'))
        if 'image' in request.files:
            file=request.files['image']
            if file and file.filename and allowed_file(file.filename):
                from flask import current_app
                filename=secure_filename(f"{product.sku}_{file.filename}")
                upload_path=current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_path,exist_ok=True)
                file.save(os.path.join(upload_path,filename))
                product.image_filename=filename
        sizes_raw=request.form.get('sizes_json','[]')
        try:
            for v in product.variants: db.session.delete(v)
            db.session.flush()
            for s in json.loads(sizes_raw):
                if s.get('size','').strip():
                    db.session.add(ProductVariant(product_id=product.id,size=s['size'].strip(),
                        stock_quantity=int(s.get('stock',0)),low_stock_threshold=int(s.get('threshold',3))))
        except: pass
        db.session.commit(); flash('Product updated! ✅','success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html',categories=categories,brands=brands,product=product)

@admin_bp.route('/products/delete/<int:pid>', methods=['POST'])
@admin_required
def delete_product(pid):
    p=Product.query.get_or_404(pid); p.is_active=False; db.session.commit()
    flash(f'"{p.name}" removed from shop.','info')
    return redirect(url_for('admin.products'))

@admin_bp.route('/products/toggle/<int:pid>', methods=['POST'])
@admin_required
def toggle_product(pid):
    p=Product.query.get_or_404(pid); p.is_online=not p.is_online; db.session.commit()
    return jsonify({'is_online':p.is_online})

@admin_bp.route('/inventory')
@admin_required
def inventory():
    brands=Brand.query.all(); brand_id=request.args.get('brand_id',type=int)
    sel_brand=Brand.query.get(brand_id) if brand_id else Brand.query.filter_by(is_special_tracked=True).first()
    products=[]; all_sizes=[]
    if sel_brand:
        products=Product.query.filter_by(brand_id=sel_brand.id,is_active=True).all()
        size_set=set()
        for p in products:
            for v in p.variants: size_set.add(v.size)
        size_order=['2Y','4Y','6Y','8Y','10Y','XS','S','M','L','XL','XXL','XXXL','26','28','30','32','34','36','38','40','42']
        all_sizes=sorted(size_set,key=lambda x:size_order.index(x) if x in size_order else 99)
    return render_template('admin/inventory.html',
        brands=brands,sel_brand=sel_brand,products=products,all_sizes=all_sizes)

@admin_bp.route('/inventory/update', methods=['POST'])
@admin_required
def update_stock():
    data=request.json; variant_id=data.get('variant_id'); new_qty=data.get('qty',0)
    variant=ProductVariant.query.get(variant_id)
    if not variant: return jsonify({'error':'Not found'}),404
    variant.stock_quantity=max(0,int(new_qty)); db.session.commit()
    return jsonify({'ok':True,'qty':variant.stock_quantity,'low':variant.is_low_stock,'oos':variant.is_out_of_stock})

@admin_bp.route('/employees')
@admin_required
def employees():
    return render_template('admin/employees.html',employees=Employee.query.join(User).all())

@admin_bp.route('/employees/add', methods=['GET','POST'])
@admin_required
def add_employee():
    if request.method=='POST':
        full_name=request.form.get('full_name','').strip(); username=request.form.get('username','').strip()
        email=request.form.get('email','').strip(); phone=request.form.get('phone','').strip()
        password=request.form.get('password','').strip(); emp_code=request.form.get('employee_code','').strip()
        designation=request.form.get('designation','').strip(); department=request.form.get('department','').strip()
        base_salary=request.form.get('base_salary',type=float) or 0
        comm_rate=request.form.get('commission_rate',type=float) or 0
        doj_str=request.form.get('date_of_joining','')
        if User.query.filter_by(username=username).first():
            flash('Username taken.','danger')
            return render_template('admin/employee_form.html',emp=None)
        user=User(full_name=full_name,username=username,email=email,phone=phone,
            password_hash=generate_password_hash(password),role='employee')
        db.session.add(user); db.session.flush()
        doj=datetime.strptime(doj_str,'%Y-%m-%d').date() if doj_str else date.today()
        emp=Employee(user_id=user.id,employee_code=emp_code,designation=designation,
            department=department,date_of_joining=doj,base_salary=base_salary,
            commission_rate=comm_rate/100)
        db.session.add(emp); db.session.commit()
        flash(f'Employee {full_name} added! Credentials: {username} / {password}','success')
        return redirect(url_for('admin.employees'))
    return render_template('admin/employee_form.html',emp=None)

@admin_bp.route('/employees/edit/<int:eid>', methods=['GET','POST'])
@admin_required
def edit_employee(eid):
    emp=Employee.query.get_or_404(eid)
    if request.method=='POST':
        emp.user.full_name=request.form.get('full_name','').strip()
        emp.user.phone=request.form.get('phone','').strip()
        emp.designation=request.form.get('designation','').strip()
        emp.department=request.form.get('department','').strip()
        emp.base_salary=request.form.get('base_salary',type=float) or 0
        emp.commission_rate=(request.form.get('commission_rate',type=float) or 0)/100
        new_pass=request.form.get('new_password','').strip()
        if new_pass: emp.user.password_hash=generate_password_hash(new_pass)
        db.session.commit(); flash('Employee updated! ✅','success')
        return redirect(url_for('admin.employees'))
    return render_template('admin/employee_form.html',emp=emp)

@admin_bp.route('/employees/delete/<int:eid>', methods=['POST'])
@admin_required
def delete_employee(eid):
    emp=Employee.query.get_or_404(eid); emp.user.is_active_account=False; db.session.commit()
    flash(f'{emp.user.full_name} deactivated.','info')
    return redirect(url_for('admin.employees'))

@admin_bp.route('/orders')
@admin_required
def orders():
    status=request.args.get('status','all')
    q=Order.query
    if status!='all': q=q.filter_by(status=status)
    return render_template('admin/orders.html',orders=q.order_by(Order.created_at.desc()).all(),status=status)

@admin_bp.route('/orders/update/<int:oid>', methods=['POST'])
@admin_required
def update_order(oid):
    order=Order.query.get_or_404(oid)
    ns=request.form.get('status'); pm=request.form.get('payment_status')
    if ns: order.status=ns
    if pm: order.payment_status=pm
    db.session.commit(); flash(f'Order {order.order_number} updated!','success')
    return redirect(url_for('admin.orders'))

@admin_bp.route('/categories/add', methods=['POST'])
@admin_required
def add_category():
    name=request.form.get('name','').strip()
    if name:
        slug=name.lower().replace(' ','-')
        if not Category.query.filter_by(slug=slug).first():
            db.session.add(Category(name=name,slug=slug)); db.session.commit()
            flash(f'Category "{name}" added!','success')
        else: flash('Already exists.','warning')
    return redirect(url_for('admin.products'))

@admin_bp.route('/brands/add', methods=['POST'])
@admin_required
def add_brand():
    name=request.form.get('name','').strip(); special=bool(request.form.get('is_special_tracked'))
    if name:
        if not Brand.query.filter_by(name=name).first():
            db.session.add(Brand(name=name,is_special_tracked=special)); db.session.commit()
            flash(f'Brand "{name}" added!','success')
        else: flash('Already exists.','warning')
    return redirect(url_for('admin.products'))
""")

# ══════════════════════════════════════════════════════════════════════════════
# 2. ADMIN BASE LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
w("app/templates/admin/base_admin.html", r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{% block title %}Admin{% endblock %} | MBM Control</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#0A0E1A;--sidebar:#0D1120;--surface:#131929;--surface2:#1A2238;
  --border:rgba(255,255,255,.07);--accent:#F5A623;--accent2:#E8463A;
  --green:#2ECC71;--blue:#4A9EFF;--purple:#9B59B6;
  --text:#E8EAF0;--muted:#6B7494;
  --ff-head:'Syne',sans-serif;--ff-body:'DM Sans',sans-serif;--ff-mono:'DM Mono',monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--ff-body);background:var(--bg);color:var(--text);min-height:100vh;display:flex}

/* ── SIDEBAR ── */
.sidebar{
  width:240px;min-height:100vh;background:var(--sidebar);
  border-right:1px solid var(--border);
  display:flex;flex-direction:column;flex-shrink:0;
  position:fixed;left:0;top:0;bottom:0;z-index:200;
  transition:transform .3s;
}
.sidebar-logo{
  padding:1.4rem 1.2rem;border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:.75rem;
}
.sidebar-logo-icon{
  width:38px;height:38px;border-radius:10px;
  background:linear-gradient(135deg,var(--accent),#E8903A);
  display:flex;align-items:center;justify-content:center;
  font-size:1.1rem;font-weight:800;color:#fff;font-family:var(--ff-head);
  flex-shrink:0;
}
.sidebar-logo-text{font-family:var(--ff-head);font-size:.95rem;font-weight:700;line-height:1.2}
.sidebar-logo-text small{display:block;font-family:var(--ff-body);font-size:.65rem;color:var(--muted);font-weight:400;letter-spacing:1px}

.nav-section-label{
  font-size:.62rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
  color:var(--muted);padding:.9rem 1.2rem .3rem;
}
.nav-item{
  display:flex;align-items:center;gap:.7rem;
  padding:.6rem 1.2rem;margin:.1rem .7rem;
  border-radius:8px;color:var(--muted);font-size:.875rem;
  font-weight:500;text-decoration:none;transition:all .2s;cursor:pointer;
}
.nav-item:hover{background:var(--surface2);color:var(--text)}
.nav-item.active{background:rgba(245,166,35,.1);color:var(--accent);border:1px solid rgba(245,166,35,.15)}
.nav-item i{font-size:1rem;width:18px;text-align:center}
.nav-badge{margin-left:auto;background:var(--accent2);color:#fff;border-radius:50px;font-size:.65rem;padding:.1rem .45rem;font-weight:700}

.sidebar-bottom{margin-top:auto;padding:1rem;border-top:1px solid var(--border)}
.store-status{
  background:var(--surface2);border-radius:10px;padding:.8rem;
  display:flex;align-items:center;gap:.6rem;
}
.status-dot{width:8px;height:8px;border-radius:50%;background:var(--green);
  box-shadow:0 0 8px var(--green);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}

/* ── MAIN CONTENT ── */
.main-content{margin-left:240px;flex:1;min-height:100vh;display:flex;flex-direction:column}
.topbar{
  background:var(--sidebar);border-bottom:1px solid var(--border);
  padding:.9rem 1.8rem;display:flex;align-items:center;justify-content:space-between;
  position:sticky;top:0;z-index:100;
}
.topbar-title{font-family:var(--ff-head);font-size:1.2rem;font-weight:700}
.topbar-actions{display:flex;align-items:center;gap:.75rem}
.admin-avatar{
  width:34px;height:34px;border-radius:50%;
  background:linear-gradient(135deg,var(--accent),#E8903A);
  display:flex;align-items:center;justify-content:center;
  font-size:.85rem;font-weight:700;color:#fff;cursor:pointer;
}
.page-body{padding:1.8rem;flex:1}

/* ── STAT CARDS ── */
.stat-card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:16px;padding:1.3rem 1.5rem;position:relative;overflow:hidden;
  transition:transform .2s,box-shadow .2s;
}
.stat-card:hover{transform:translateY(-3px);box-shadow:0 12px 40px rgba(0,0,0,.3)}
.stat-card::before{content:'';position:absolute;top:-20px;right:-20px;width:80px;height:80px;border-radius:50%;opacity:.06}
.stat-card.orange::before{background:var(--accent)}
.stat-card.red::before{background:var(--accent2)}
.stat-card.green::before{background:var(--green)}
.stat-card.blue::before{background:var(--blue)}
.stat-label{font-size:.72rem;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);margin-bottom:.5rem}
.stat-value{font-family:var(--ff-head);font-size:2rem;font-weight:800;line-height:1}
.stat-icon{position:absolute;top:1.2rem;right:1.2rem;font-size:1.4rem;opacity:.4}

/* ── TABLES ── */
.data-table{width:100%;border-collapse:separate;border-spacing:0}
.data-table th{
  font-size:.68rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
  color:var(--muted);padding:.75rem 1rem;border-bottom:1px solid var(--border);
  white-space:nowrap;
}
.data-table td{
  padding:.7rem 1rem;border-bottom:1px solid rgba(255,255,255,.04);
  font-size:.875rem;vertical-align:middle;
}
.data-table tr:hover td{background:rgba(255,255,255,.02)}
.data-table tr:last-child td{border-bottom:none}

/* ── BADGES ── */
.badge-status{display:inline-flex;align-items:center;gap:.3rem;border-radius:50px;padding:.25rem .7rem;font-size:.7rem;font-weight:600}
.badge-confirmed{background:rgba(74,158,255,.15);color:var(--blue)}
.badge-pending{background:rgba(245,166,35,.15);color:var(--accent)}
.badge-completed{background:rgba(46,204,113,.15);color:var(--green)}
.badge-paid{background:rgba(46,204,113,.15);color:var(--green)}
.badge-online{background:rgba(46,204,113,.15);color:var(--green)}
.badge-offline{background:rgba(107,116,148,.15);color:var(--muted)}
.badge-low{background:rgba(245,166,35,.15);color:var(--accent)}
.badge-oos{background:rgba(232,70,58,.15);color:var(--accent2)}

/* ── CARDS / PANELS ── */
.panel{background:var(--surface);border:1px solid var(--border);border-radius:16px;overflow:hidden}
.panel-head{padding:1rem 1.4rem;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.panel-head h5{font-family:var(--ff-head);font-size:1rem;font-weight:700;margin:0}
.panel-body{padding:1.4rem}

/* ── FORM CONTROLS ── */
.ctrl{
  background:var(--surface2);border:1px solid var(--border);
  color:var(--text);border-radius:10px;padding:.65rem 1rem;
  font-family:var(--ff-body);font-size:.9rem;width:100%;
  transition:border-color .2s;outline:none;
}
.ctrl:focus{border-color:var(--accent)}
.ctrl-label{font-size:.75rem;font-weight:600;letter-spacing:.5px;text-transform:uppercase;color:var(--muted);margin-bottom:.4rem;display:block}
textarea.ctrl{resize:vertical;min-height:90px}
select.ctrl option{background:var(--surface)}

/* ── BUTTONS ── */
.btn-accent{background:var(--accent);color:#1A1A00;border:none;border-radius:8px;padding:.55rem 1.2rem;font-weight:600;font-size:.875rem;cursor:pointer;transition:all .2s;display:inline-flex;align-items:center;gap:.4rem;text-decoration:none}
.btn-accent:hover{background:#F0B233;color:#1A1A00;transform:translateY(-1px)}
.btn-ghost{background:transparent;border:1px solid var(--border);color:var(--text);border-radius:8px;padding:.55rem 1.2rem;font-weight:500;font-size:.875rem;cursor:pointer;transition:all .2s;display:inline-flex;align-items:center;gap:.4rem;text-decoration:none}
.btn-ghost:hover{border-color:var(--text);color:var(--text);background:var(--surface2)}
.btn-danger{background:rgba(232,70,58,.15);border:1px solid rgba(232,70,58,.3);color:var(--accent2);border-radius:8px;padding:.4rem .9rem;font-size:.8rem;font-weight:600;cursor:pointer;transition:all .2s}
.btn-danger:hover{background:var(--accent2);color:#fff}
.btn-success{background:rgba(46,204,113,.15);border:1px solid rgba(46,204,113,.3);color:var(--green);border-radius:8px;padding:.4rem .9rem;font-size:.8rem;font-weight:600;cursor:pointer;transition:all .2s;text-decoration:none;display:inline-flex;align-items:center;gap:.3rem}
.btn-success:hover{background:var(--green);color:#fff}
.btn-edit{background:rgba(74,158,255,.12);border:1px solid rgba(74,158,255,.25);color:var(--blue);border-radius:8px;padding:.4rem .9rem;font-size:.8rem;font-weight:600;cursor:pointer;transition:all .2s;text-decoration:none;display:inline-flex;align-items:center;gap:.3rem}
.btn-edit:hover{background:var(--blue);color:#fff}

/* ── SEARCH BAR ── */
.search-wrap{position:relative}
.search-wrap i{position:absolute;left:.9rem;top:50%;transform:translateY(-50%);color:var(--muted)}
.search-wrap .ctrl{padding-left:2.5rem}

/* ── ALERTS ── */
.alert-mbm{border-radius:10px;padding:.75rem 1rem;margin-bottom:1rem;font-size:.875rem;display:flex;align-items:center;gap:.5rem}
.alert-success-mbm{background:rgba(46,204,113,.1);border:1px solid rgba(46,204,113,.2);color:#7DEFA7}
.alert-danger-mbm{background:rgba(232,70,58,.1);border:1px solid rgba(232,70,58,.2);color:#F87878}
.alert-warning-mbm{background:rgba(245,166,35,.1);border:1px solid rgba(245,166,35,.2);color:#FAC858}
.alert-info-mbm{background:rgba(74,158,255,.1);border:1px solid rgba(74,158,255,.2);color:#7ABFFF}

/* ── MOBILE ── */
@media(max-width:768px){
  .sidebar{transform:translateX(-100%)}
  .sidebar.open{transform:translateX(0)}
  .main-content{margin-left:0}
  .mobile-toggle{display:block!important}
}
.mobile-toggle{display:none;background:none;border:none;color:var(--text);font-size:1.4rem;cursor:pointer}
</style>
{% block extra_css %}{% endblock %}
</head>
<body>

<!-- SIDEBAR -->
<nav class="sidebar" id="sidebar">
  <div class="sidebar-logo">
    <div class="sidebar-logo-icon">M</div>
    <div class="sidebar-logo-text">
      MBM Admin
      <small>Control Panel</small>
    </div>
  </div>

  <div style="flex:1;overflow-y:auto;padding-bottom:1rem">
    <div class="nav-section-label">Overview</div>
    <a href="{{ url_for('admin.dashboard') }}"
       class="nav-item {% if request.endpoint=='admin.dashboard' %}active{% endif %}">
      <i class="bi bi-speedometer2"></i> Dashboard
    </a>

    <div class="nav-section-label">Catalogue</div>
    <a href="{{ url_for('admin.products') }}"
       class="nav-item {% if 'product' in request.endpoint %}active{% endif %}">
      <i class="bi bi-boxes"></i> Products
    </a>
    <a href="{{ url_for('admin.inventory') }}"
       class="nav-item {% if request.endpoint=='admin.inventory' %}active{% endif %}">
      <i class="bi bi-grid-3x3-gap"></i> Inventory Matrix
    </a>

    <div class="nav-section-label">Sales</div>
    <a href="{{ url_for('admin.orders') }}"
       class="nav-item {% if request.endpoint=='admin.orders' %}active{% endif %}">
      <i class="bi bi-receipt"></i> Orders
      {% set pending = stats.pending_orders if stats is defined else 0 %}
      {% if pending > 0 %}<span class="nav-badge">{{ pending }}</span>{% endif %}
    </a>
    <a href="{{ url_for('admin.orders', status='confirmed') }}"
       class="nav-item">
      <i class="bi bi-clock-history"></i> Pending Pickup
    </a>

    <div class="nav-section-label">Staff</div>
    <a href="{{ url_for('admin.employees') }}"
       class="nav-item {% if 'employee' in request.endpoint %}active{% endif %}">
      <i class="bi bi-people"></i> Employees
    </a>

    <div class="nav-section-label">Store</div>
    <a href="{{ url_for('customer.index') }}" target="_blank" class="nav-item">
      <i class="bi bi-shop"></i> View Live Shop
    </a>
    <a href="{{ url_for('auth.logout') }}" class="nav-item"
       style="color:var(--accent2)">
      <i class="bi bi-box-arrow-left"></i> Logout
    </a>
  </div>

  <div class="sidebar-bottom">
    <div class="store-status">
      <div class="status-dot"></div>
      <div>
        <div style="font-size:.78rem;font-weight:600">Store Online</div>
        <div style="font-size:.68rem;color:var(--muted)">Main Road, Mantha</div>
      </div>
    </div>
  </div>
</nav>

<!-- MAIN -->
<div class="main-content">
  <div class="topbar">
    <div style="display:flex;align-items:center;gap:.9rem">
      <button class="mobile-toggle" onclick="document.getElementById('sidebar').classList.toggle('open')">
        <i class="bi bi-list"></i>
      </button>
      <div class="topbar-title">{% block page_title %}Dashboard{% endblock %}</div>
    </div>
    <div class="topbar-actions">
      <a href="{{ url_for('admin.add_product') }}" class="btn-accent" style="font-size:.8rem;padding:.45rem 1rem">
        <i class="bi bi-plus-lg"></i> Add Product
      </a>
      <div class="admin-avatar">{{ current_user.full_name[0] }}</div>
    </div>
  </div>

  <!-- Flash messages -->
  <div style="padding:.6rem 1.8rem 0">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}{% for cat, msg in messages %}
        <div class="alert-mbm alert-{{ cat }}-mbm">
          <i class="bi bi-{% if cat=='success' %}check-circle{% elif cat=='danger' %}exclamation-circle{% elif cat=='warning' %}exclamation-triangle{% else %}info-circle{% endif %}"></i>
          {{ msg }}
        </div>
      {% endfor %}{% endif %}
    {% endwith %}
  </div>

  <div class="page-body">
    {% block content %}{% endblock %}
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
{% block extra_js %}{% endblock %}
</body>
</html>
""")

# ══════════════════════════════════════════════════════════════════════════════
# 3. DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
w("app/templates/admin/dashboard.html", r"""{% extends 'admin/base_admin.html' %}
{% block title %}Dashboard{% endblock %}
{% block page_title %}Dashboard{% endblock %}
{% block extra_css %}
<style>
.greeting{font-family:var(--ff-head);font-size:1.6rem;font-weight:800;margin-bottom:.25rem}
.greeting span{color:var(--accent)}
@keyframes countUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.stat-card{animation:countUp .4s ease both}
.stat-card:nth-child(1){animation-delay:.05s}
.stat-card:nth-child(2){animation-delay:.1s}
.stat-card:nth-child(3){animation-delay:.15s}
.stat-card:nth-child(4){animation-delay:.2s}
.stat-card:nth-child(5){animation-delay:.25s}
.stat-card:nth-child(6){animation-delay:.3s}
</style>
{% endblock %}
{% block content %}

<div class="greeting mb-4">
  Good {% if now().hour < 12 %}Morning{% elif now().hour < 17 %}Afternoon{% else %}Evening{% endif %},
  <span>{{ current_user.full_name.split()[0] }} 👋</span>
</div>

<!-- Stats Row 1 -->
<div class="row g-3 mb-4">
  <div class="col-6 col-lg-3">
    <div class="stat-card orange">
      <div class="stat-label">Total Products</div>
      <div class="stat-value" style="color:var(--accent)">{{ stats.total_products }}</div>
      <i class="bi bi-boxes stat-icon" style="color:var(--accent)"></i>
    </div>
  </div>
  <div class="col-6 col-lg-3">
    <div class="stat-card blue">
      <div class="stat-label">Total Orders</div>
      <div class="stat-value" style="color:var(--blue)">{{ stats.total_orders }}</div>
      <i class="bi bi-receipt stat-icon" style="color:var(--blue)"></i>
    </div>
  </div>
  <div class="col-6 col-lg-3">
    <div class="stat-card green">
      <div class="stat-label">Customers</div>
      <div class="stat-value" style="color:var(--green)">{{ stats.total_customers }}</div>
      <i class="bi bi-people stat-icon" style="color:var(--green)"></i>
    </div>
  </div>
  <div class="col-6 col-lg-3">
    <div class="stat-card red">
      <div class="stat-label">Pending Pickup</div>
      <div class="stat-value" style="color:var(--accent2)">{{ stats.pending_orders }}</div>
      <i class="bi bi-clock stat-icon" style="color:var(--accent2)"></i>
    </div>
  </div>
</div>

<div class="row g-3 mb-4">
  <div class="col-6 col-lg-3">
    <div class="stat-card">
      <div class="stat-label">Employees</div>
      <div class="stat-value">{{ stats.total_employees }}</div>
      <i class="bi bi-person-badge stat-icon"></i>
    </div>
  </div>
  <div class="col-6 col-lg-3">
    <div class="stat-card">
      <div class="stat-label">Low Stock Items</div>
      <div class="stat-value" style="color:var(--accent)">{{ stats.low_stock }}</div>
      <i class="bi bi-exclamation-triangle stat-icon" style="color:var(--accent)"></i>
    </div>
  </div>
  <div class="col-6 col-lg-3">
    <div class="stat-card">
      <div class="stat-label">Out of Stock</div>
      <div class="stat-value" style="color:var(--accent2)">{{ stats.out_of_stock }}</div>
      <i class="bi bi-x-circle stat-icon" style="color:var(--accent2)"></i>
    </div>
  </div>
  <div class="col-6 col-lg-3">
    <div class="stat-card green">
      <div class="stat-label">Revenue Collected</div>
      <div class="stat-value" style="color:var(--green);font-size:1.4rem">₹{{ "%.0f"|format(stats.total_revenue) }}</div>
      <i class="bi bi-currency-rupee stat-icon" style="color:var(--green)"></i>
    </div>
  </div>
</div>

<div class="row g-4">
  <!-- Recent Orders -->
  <div class="col-lg-8">
    <div class="panel">
      <div class="panel-head">
        <h5><i class="bi bi-receipt me-2" style="color:var(--blue)"></i>Recent Orders</h5>
        <a href="{{ url_for('admin.orders') }}" class="btn-ghost" style="font-size:.78rem;padding:.3rem .8rem">View All</a>
      </div>
      <div style="overflow-x:auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>Order #</th><th>Customer</th><th>Amount</th>
              <th>Status</th><th>Payment</th><th>Date</th><th>Action</th>
            </tr>
          </thead>
          <tbody>
            {% for o in recent_orders %}
            <tr>
              <td><span style="font-family:var(--ff-mono);font-size:.8rem;color:var(--accent)">{{ o.order_number }}</span></td>
              <td>{{ o.customer.full_name }}</td>
              <td style="font-weight:600">₹{{ "%.0f"|format(o.total_amount) }}</td>
              <td><span class="badge-status badge-{{ o.status }}">{{ o.status|title }}</span></td>
              <td><span class="badge-status badge-{{ o.payment_status }}">{{ o.payment_status|title }}</span></td>
              <td style="color:var(--muted);font-size:.8rem">{{ o.created_at.strftime('%d %b %Y') }}</td>
              <td>
                <form method="POST" action="{{ url_for('admin.update_order', oid=o.id) }}" style="display:inline">
                  <select name="status" class="ctrl" style="padding:.3rem .6rem;font-size:.78rem;width:130px"
                          onchange="this.form.submit()">
                    <option value="">Change status…</option>
                    {% for s in ['confirmed','ready_for_pickup','completed','cancelled'] %}
                    <option value="{{ s }}" {% if o.status==s %}selected{% endif %}>{{ s|replace('_',' ')|title }}</option>
                    {% endfor %}
                  </select>
                </form>
              </td>
            </tr>
            {% else %}
            <tr><td colspan="7" style="text-align:center;color:var(--muted);padding:2rem">No orders yet</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Low Stock Alert -->
  <div class="col-lg-4">
    <div class="panel">
      <div class="panel-head">
        <h5><i class="bi bi-exclamation-triangle me-2" style="color:var(--accent)"></i>Low Stock Alert</h5>
        <a href="{{ url_for('admin.inventory') }}" class="btn-ghost" style="font-size:.78rem;padding:.3rem .8rem">Fix</a>
      </div>
      <div class="panel-body" style="padding:.8rem">
        {% for v in low_stock_items %}
        <div style="display:flex;align-items:center;justify-content:space-between;padding:.6rem .6rem;border-bottom:1px solid var(--border)">
          <div>
            <div style="font-size:.83rem;font-weight:500">{{ v.product.name[:28] }}{% if v.product.name|length > 28 %}…{% endif %}</div>
            <div style="font-size:.72rem;color:var(--muted)">Size: {{ v.size }}</div>
          </div>
          <span class="badge-status {% if v.stock_quantity==0 %}badge-oos{% else %}badge-low{% endif %}">
            {{ v.stock_quantity }} left
          </span>
        </div>
        {% else %}
        <div style="text-align:center;padding:2rem;color:var(--muted)">
          <i class="bi bi-check-circle" style="font-size:1.8rem;color:var(--green);display:block;margin-bottom:.5rem"></i>
          All stock levels OK!
        </div>
        {% endfor %}
      </div>
    </div>

    <!-- Quick actions -->
    <div class="panel mt-3">
      <div class="panel-head"><h5>⚡ Quick Actions</h5></div>
      <div class="panel-body" style="display:flex;flex-direction:column;gap:.6rem;padding:1rem">
        <a href="{{ url_for('admin.add_product') }}" class="btn-accent"><i class="bi bi-plus-circle"></i> Add New Product</a>
        <a href="{{ url_for('admin.add_employee') }}" class="btn-ghost"><i class="bi bi-person-plus"></i> Add Employee</a>
        <a href="{{ url_for('admin.inventory') }}" class="btn-ghost"><i class="bi bi-grid-3x3-gap"></i> Update Stock</a>
        <a href="{{ url_for('admin.orders', status='confirmed') }}" class="btn-ghost"><i class="bi bi-clock"></i> Pending Pickups</a>
      </div>
    </div>
  </div>
</div>
{% endblock %}
{% block extra_js %}
<script>
// Helper for template
</script>
{% endblock %}
""")

# ══════════════════════════════════════════════════════════════════════════════
# 4. PRODUCTS LIST
# ══════════════════════════════════════════════════════════════════════════════
w("app/templates/admin/products.html", r"""{% extends 'admin/base_admin.html' %}
{% block title %}Products{% endblock %}
{% block page_title %}Product Management{% endblock %}
{% block content %}

<!-- Top action row -->
<div class="d-flex flex-wrap gap-3 mb-4 align-items-center">
  <form method="GET" style="display:contents">
    <div class="search-wrap" style="flex:1;min-width:200px">
      <i class="bi bi-search"></i>
      <input type="text" name="q" value="{{ search }}" class="ctrl" placeholder="Search products…">
    </div>
    <select name="cat" class="ctrl" style="width:160px" onchange="this.form.submit()">
      <option value="all">All Categories</option>
      {% for c in categories %}<option value="{{ c.id }}" {% if active_cat==c.id|string %}selected{% endif %}>{{ c.name }}</option>{% endfor %}
    </select>
    <select name="brand" class="ctrl" style="width:160px" onchange="this.form.submit()">
      <option value="all">All Brands</option>
      {% for b in brands %}<option value="{{ b.id }}" {% if active_brand==b.id|string %}selected{% endif %}>{{ b.name }}</option>{% endfor %}
    </select>
    <button type="submit" class="btn-ghost"><i class="bi bi-funnel"></i> Filter</button>
  </form>
  <a href="{{ url_for('admin.add_product') }}" class="btn-accent ms-auto"><i class="bi bi-plus-lg"></i> Add Product</a>
</div>

<!-- Products table -->
<div class="panel">
  <div class="panel-head">
    <h5><i class="bi bi-boxes me-2"></i>{{ products|length }} Products</h5>
    <div style="display:flex;gap:.5rem">
      <!-- Add Category -->
      <button class="btn-ghost" style="font-size:.78rem" onclick="document.getElementById('catModal').style.display='flex'">+ Category</button>
      <!-- Add Brand -->
      <button class="btn-ghost" style="font-size:.78rem" onclick="document.getElementById('brandModal').style.display='flex'">+ Brand</button>
    </div>
  </div>
  <div style="overflow-x:auto">
    <table class="data-table">
      <thead>
        <tr><th>Product</th><th>SKU</th><th>Category</th><th>Brand</th><th>Price</th><th>Sizes / Stock</th><th>Online</th><th>Actions</th></tr>
      </thead>
      <tbody>
        {% for p in products %}
        <tr>
          <td>
            <div style="display:flex;align-items:center;gap:.75rem">
              <div style="width:44px;height:44px;border-radius:8px;background:var(--surface2);display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0">
                {% if p.image_filename %}<img src="{{ url_for('static',filename='images/products/'+p.image_filename) }}" style="width:100%;height:100%;object-fit:cover;border-radius:8px">
                {% elif 'shirt' in p.name.lower() %}👔{% elif 'trouser' in p.name.lower() %}👖{% elif 'kurta' in p.name.lower() %}🧣{% else %}🛍️{% endif %}
              </div>
              <div>
                <div style="font-weight:600;font-size:.88rem">{{ p.name }}</div>
                <div style="font-size:.72rem;color:var(--muted)">₹{{ "%.0f"|format(p.price) }}{% if p.mrp %} / MRP ₹{{ "%.0f"|format(p.mrp) }}{% endif %}</div>
              </div>
            </div>
          </td>
          <td><span style="font-family:var(--ff-mono);font-size:.78rem;color:var(--muted)">{{ p.sku }}</span></td>
          <td style="font-size:.85rem">{{ p.category.name }}</td>
          <td style="font-size:.85rem">{{ p.brand.name }}</td>
          <td style="font-weight:600">₹{{ "%.0f"|format(p.price) }}</td>
          <td>
            {% for v in p.variants %}
            <span style="display:inline-block;margin:.1rem;padding:.15rem .45rem;border-radius:4px;font-size:.7rem;font-weight:600;
              background:{% if v.is_out_of_stock %}rgba(232,70,58,.15){% elif v.is_low_stock %}rgba(245,166,35,.15){% else %}rgba(46,204,113,.1){% endif %};
              color:{% if v.is_out_of_stock %}var(--accent2){% elif v.is_low_stock %}var(--accent){% else %}var(--green){% endif %}">
              {{ v.size }}: {{ v.stock_quantity }}
            </span>
            {% endfor %}
          </td>
          <td>
            <button onclick="toggleOnline({{ p.id }}, this)" data-online="{{ p.is_online|lower }}"
                    class="badge-status {% if p.is_online %}badge-online{% else %}badge-offline{% endif %}"
                    style="border:none;cursor:pointer;background:{% if p.is_online %}rgba(46,204,113,.15){% else %}rgba(107,116,148,.15){% endif %}">
              {{ 'Online' if p.is_online else 'Hidden' }}
            </button>
          </td>
          <td>
            <div style="display:flex;gap:.4rem;flex-wrap:nowrap">
              <a href="{{ url_for('admin.edit_product', pid=p.id) }}" class="btn-edit"><i class="bi bi-pencil"></i></a>
              <form method="POST" action="{{ url_for('admin.delete_product', pid=p.id) }}"
                    onsubmit="return confirm('Remove {{ p.name }} from shop?')">
                <button type="submit" class="btn-danger"><i class="bi bi-trash3"></i></button>
              </form>
            </div>
          </td>
        </tr>
        {% else %}
        <tr><td colspan="8" style="text-align:center;padding:3rem;color:var(--muted)">
          No products yet. <a href="{{ url_for('admin.add_product') }}" style="color:var(--accent)">Add your first product →</a>
        </td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<!-- Category Modal -->
<div id="catModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:9999;align-items:center;justify-content:center">
  <div class="panel" style="width:360px;padding:1.5rem">
    <h5 style="margin-bottom:1rem;font-family:var(--ff-head)">Add Category</h5>
    <form method="POST" action="{{ url_for('admin.add_category') }}">
      <label class="ctrl-label">Category Name</label>
      <input type="text" name="name" class="ctrl mb-3" placeholder="e.g. Winter Wear" required>
      <div style="display:flex;gap:.5rem;justify-content:flex-end">
        <button type="button" class="btn-ghost" onclick="document.getElementById('catModal').style.display='none'">Cancel</button>
        <button type="submit" class="btn-accent">Add</button>
      </div>
    </form>
  </div>
</div>

<!-- Brand Modal -->
<div id="brandModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:9999;align-items:center;justify-content:center">
  <div class="panel" style="width:360px;padding:1.5rem">
    <h5 style="margin-bottom:1rem;font-family:var(--ff-head)">Add Brand</h5>
    <form method="POST" action="{{ url_for('admin.add_brand') }}">
      <label class="ctrl-label">Brand Name</label>
      <input type="text" name="name" class="ctrl mb-3" placeholder="e.g. Wills Lifestyle" required>
      <label style="display:flex;align-items:center;gap:.5rem;cursor:pointer;margin-bottom:1rem;font-size:.875rem">
        <input type="checkbox" name="is_special_tracked"> Enable inventory matrix tracking
      </label>
      <div style="display:flex;gap:.5rem;justify-content:flex-end">
        <button type="button" class="btn-ghost" onclick="document.getElementById('brandModal').style.display='none'">Cancel</button>
        <button type="submit" class="btn-accent">Add</button>
      </div>
    </form>
  </div>
</div>

{% endblock %}
{% block extra_js %}
<script>
async function toggleOnline(pid, btn) {
  const res = await fetch(`/admin/products/toggle/${pid}`, {method:'POST'});
  const data = await res.json();
  btn.textContent = data.is_online ? 'Online' : 'Hidden';
  btn.className = `badge-status ${data.is_online ? 'badge-online' : 'badge-offline'}`;
  btn.style.background = data.is_online ? 'rgba(46,204,113,.15)' : 'rgba(107,116,148,.15)';
}
</script>
{% endblock %}
""")

# ══════════════════════════════════════════════════════════════════════════════
# 5. PRODUCT FORM
# ══════════════════════════════════════════════════════════════════════════════
w("app/templates/admin/product_form.html", r"""{% extends 'admin/base_admin.html' %}
{% block title %}{{ 'Edit' if product else 'Add' }} Product{% endblock %}
{% block page_title %}{{ 'Edit Product' if product else 'Add New Product' }}{% endblock %}
{% block content %}
<div style="max-width:780px">
  <a href="{{ url_for('admin.products') }}" class="btn-ghost mb-4" style="display:inline-flex">
    <i class="bi bi-arrow-left"></i> Back to Products
  </a>

  <form method="POST" enctype="multipart/form-data">
    <div class="row g-4">

      <!-- Left col -->
      <div class="col-lg-8">
        <div class="panel mb-4">
          <div class="panel-head"><h5>Product Information</h5></div>
          <div class="panel-body">
            <div class="mb-3">
              <label class="ctrl-label">Product Name *</label>
              <input type="text" name="name" class="ctrl" required
                     value="{{ product.name if product else '' }}"
                     placeholder="e.g. k satish Blue Formal Shirt">
            </div>
            <div class="row g-3">
              <div class="col-6">
                <label class="ctrl-label">SKU (Unique Code) *</label>
                <input type="text" name="sku" class="ctrl" required
                       value="{{ product.sku if product else '' }}"
                       placeholder="e.g. KS-SH-001"
                       {% if product %}readonly style="opacity:.6"{% endif %}>
              </div>
              <div class="col-6">
                <label class="ctrl-label">Category *</label>
                <select name="category_id" class="ctrl" required>
                  {% for c in categories %}
                  <option value="{{ c.id }}" {% if product and product.category_id==c.id %}selected{% endif %}>{{ c.name }}</option>
                  {% endfor %}
                </select>
              </div>
            </div>
            <div class="row g-3 mt-1">
              <div class="col-6">
                <label class="ctrl-label">Brand *</label>
                <select name="brand_id" class="ctrl" required>
                  {% for b in brands %}
                  <option value="{{ b.id }}" {% if product and product.brand_id==b.id %}selected{% endif %}>{{ b.name }}</option>
                  {% endfor %}
                </select>
              </div>
              <div class="col-3">
                <label class="ctrl-label">Selling Price (₹) *</label>
                <input type="number" name="price" class="ctrl" step="0.01" required
                       value="{{ product.price if product else '' }}" placeholder="999">
              </div>
              <div class="col-3">
                <label class="ctrl-label">MRP (₹)</label>
                <input type="number" name="mrp" class="ctrl" step="0.01"
                       value="{{ product.mrp if product else '' }}" placeholder="1299">
              </div>
            </div>
            <div class="mt-3">
              <label class="ctrl-label">Description</label>
              <textarea name="description" class="ctrl">{{ product.description if product else '' }}</textarea>
            </div>
          </div>
        </div>

        <!-- Size & Stock -->
        <div class="panel">
          <div class="panel-head">
            <h5>Sizes & Stock Levels</h5>
            <button type="button" class="btn-ghost" style="font-size:.78rem" onclick="addSizeRow()">+ Add Size</button>
          </div>
          <div class="panel-body">
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:.5rem;margin-bottom:.5rem">
              <span style="font-size:.72rem;text-transform:uppercase;letter-spacing:1px;color:var(--muted)">Size</span>
              <span style="font-size:.72rem;text-transform:uppercase;letter-spacing:1px;color:var(--muted)">Stock Qty</span>
              <span style="font-size:.72rem;text-transform:uppercase;letter-spacing:1px;color:var(--muted)">Low Stock At</span>
              <span></span>
            </div>
            <div id="sizeRows">
              {% if product and product.variants %}
                {% for v in product.variants %}
                <div class="size-row" style="display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:.5rem;margin-bottom:.5rem">
                  <input type="text" class="ctrl sz-size" placeholder="e.g. M" value="{{ v.size }}">
                  <input type="number" class="ctrl sz-stock" placeholder="0" value="{{ v.stock_quantity }}" min="0">
                  <input type="number" class="ctrl sz-threshold" placeholder="3" value="{{ v.low_stock_threshold }}" min="0">
                  <button type="button" class="btn-danger" onclick="this.parentElement.remove()" style="width:36px;padding:.5rem">×</button>
                </div>
                {% endfor %}
              {% else %}
                <!-- Default size row -->
                <div class="size-row" style="display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:.5rem;margin-bottom:.5rem">
                  <input type="text" class="ctrl sz-size" placeholder="S">
                  <input type="number" class="ctrl sz-stock" placeholder="0" min="0">
                  <input type="number" class="ctrl sz-threshold" placeholder="3" min="0">
                  <button type="button" class="btn-danger" onclick="this.parentElement.remove()" style="width:36px;padding:.5rem">×</button>
                </div>
              {% endif %}
            </div>
            <div style="margin-top:.5rem">
              <button type="button" class="btn-ghost" onclick="addCommonSizes()">⚡ Add All Common Sizes (S/M/L/XL/XXL)</button>
            </div>
            <input type="hidden" name="sizes_json" id="sizesJson">
          </div>
        </div>
      </div>

      <!-- Right col -->
      <div class="col-lg-4">
        <div class="panel mb-4">
          <div class="panel-head"><h5>Product Image</h5></div>
          <div class="panel-body">
            <div id="imgPreview" style="width:100%;aspect-ratio:1;background:var(--surface2);border-radius:10px;
                 display:flex;align-items:center;justify-content:center;font-size:4rem;margin-bottom:1rem;overflow:hidden">
              {% if product and product.image_filename %}
                <img src="{{ url_for('static',filename='images/products/'+product.image_filename) }}"
                     style="width:100%;height:100%;object-fit:cover">
              {% else %}🛍️{% endif %}
            </div>
            <label for="imgInput" class="btn-ghost" style="width:100%;justify-content:center;cursor:pointer">
              <i class="bi bi-upload"></i> Upload Image
            </label>
            <input type="file" name="image" id="imgInput" accept="image/*" style="display:none"
                   onchange="previewImg(this)">
            <p style="font-size:.72rem;color:var(--muted);margin-top:.5rem;text-align:center">PNG, JPG, WEBP — max 5MB</p>
          </div>
        </div>

        <div class="panel mb-4">
          <div class="panel-head"><h5>Visibility</h5></div>
          <div class="panel-body">
            <label style="display:flex;align-items:center;gap:.7rem;cursor:pointer;margin-bottom:.8rem">
              <input type="checkbox" name="is_online" id="isOnline"
                     {% if not product or product.is_online %}checked{% endif %}
                     style="width:18px;height:18px;accent-color:var(--accent)">
              <div>
                <div style="font-size:.875rem;font-weight:600">Show on Website</div>
                <div style="font-size:.75rem;color:var(--muted)">Customers can browse and buy</div>
              </div>
            </label>
            {% if product %}
            <label style="display:flex;align-items:center;gap:.7rem;cursor:pointer">
              <input type="checkbox" name="is_active" id="isActive"
                     {% if product.is_active %}checked{% endif %}
                     style="width:18px;height:18px;accent-color:var(--green)">
              <div>
                <div style="font-size:.875rem;font-weight:600">Active</div>
                <div style="font-size:.75rem;color:var(--muted)">Uncheck to archive product</div>
              </div>
            </label>
            {% endif %}
          </div>
        </div>

        <button type="submit" class="btn-accent" style="width:100%;justify-content:center;padding:.8rem;font-size:1rem">
          <i class="bi bi-check-lg me-2"></i>{{ 'Update Product' if product else 'Add Product' }}
        </button>
      </div>

    </div>
  </form>
</div>
{% endblock %}
{% block extra_js %}
<script>
function addSizeRow(size='', stock='', threshold='3') {
  const row = document.createElement('div');
  row.className = 'size-row';
  row.style = 'display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:.5rem;margin-bottom:.5rem';
  row.innerHTML = `
    <input type="text" class="ctrl sz-size" placeholder="e.g. XL" value="${size}">
    <input type="number" class="ctrl sz-stock" placeholder="0" value="${stock}" min="0">
    <input type="number" class="ctrl sz-threshold" placeholder="3" value="${threshold}" min="0">
    <button type="button" class="btn-danger" onclick="this.parentElement.remove()" style="width:36px;padding:.5rem">×</button>
  `;
  document.getElementById('sizeRows').appendChild(row);
}

function addCommonSizes() {
  ['S','M','L','XL','XXL'].forEach(s => addSizeRow(s,'0','3'));
}

// Before form submit, collect all sizes into JSON
document.querySelector('form').addEventListener('submit', function() {
  const rows = document.querySelectorAll('.size-row');
  const data = [];
  rows.forEach(r => {
    const size = r.querySelector('.sz-size').value.trim();
    const stock = r.querySelector('.sz-stock').value || '0';
    const threshold = r.querySelector('.sz-threshold').value || '3';
    if (size) data.push({size, stock, threshold});
  });
  document.getElementById('sizesJson').value = JSON.stringify(data);
});

function previewImg(input) {
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = e => {
      document.getElementById('imgPreview').innerHTML =
        `<img src="${e.target.result}" style="width:100%;height:100%;object-fit:cover">`;
    };
    reader.readAsDataURL(input.files[0]);
  }
}
</script>
{% endblock %}
""")

# ══════════════════════════════════════════════════════════════════════════════
# 6. INVENTORY MATRIX (k satish brand table)
# ══════════════════════════════════════════════════════════════════════════════
w("app/templates/admin/inventory.html", r"""{% extends 'admin/base_admin.html' %}
{% block title %}Inventory Matrix{% endblock %}
{% block page_title %}Inventory Matrix{% endblock %}
{% block extra_css %}
<style>
.matrix-wrap{overflow-x:auto}
.matrix-table{border-collapse:separate;border-spacing:0;min-width:600px}
.matrix-table th{
  background:var(--surface2);padding:.65rem 1rem;font-size:.7rem;
  font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
  color:var(--muted);border-bottom:1px solid var(--border);white-space:nowrap;
}
.matrix-table th.size-col{text-align:center;min-width:72px}
.matrix-table td{padding:.5rem .4rem;border-bottom:1px solid rgba(255,255,255,.04);vertical-align:middle}
.matrix-table tr:hover td{background:rgba(255,255,255,.015)}
.prod-name-cell{padding:.5rem 1rem;font-size:.875rem;font-weight:500;white-space:nowrap;max-width:200px;overflow:hidden;text-overflow:ellipsis}

.stock-cell{text-align:center;padding:.3rem}
.stock-input{
  width:60px;text-align:center;background:var(--surface2);
  border:1px solid var(--border);color:var(--text);
  border-radius:6px;padding:.3rem .2rem;font-family:var(--ff-mono);
  font-size:.85rem;font-weight:600;outline:none;transition:border-color .2s;
}
.stock-input:focus{border-color:var(--accent)}
.stock-input.low{border-color:rgba(245,166,35,.5);background:rgba(245,166,35,.06);color:var(--accent)}
.stock-input.oos{border-color:rgba(232,70,58,.4);background:rgba(232,70,58,.06);color:var(--accent2)}
.stock-input.good{border-color:rgba(46,204,113,.3);color:var(--green)}
.no-variant{text-align:center;color:var(--border);font-size:1.1rem}

.brand-tabs{display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:1.5rem}
.brand-tab{
  padding:.45rem 1.1rem;border-radius:8px;font-size:.83rem;font-weight:600;
  text-decoration:none;border:1px solid var(--border);color:var(--muted);transition:all .2s;
}
.brand-tab:hover,.brand-tab.active{background:var(--accent);color:#1A1A00;border-color:var(--accent)}

.save-dot{
  width:8px;height:8px;border-radius:50%;background:var(--accent);
  display:none;animation:blink .8s infinite;
}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
</style>
{% endblock %}
{% block content %}

<div class="brand-tabs">
  {% for b in brands %}
  <a href="{{ url_for('admin.inventory', brand_id=b.id) }}"
     class="brand-tab {% if sel_brand and sel_brand.id==b.id %}active{% endif %}">
    {{ b.name }}
    {% if b.is_special_tracked %}<span style="font-size:.6rem;opacity:.6">★</span>{% endif %}
  </a>
  {% endfor %}
</div>

{% if sel_brand %}
<div class="panel">
  <div class="panel-head">
    <h5>
      <i class="bi bi-grid-3x3-gap me-2" style="color:var(--accent)"></i>
      {{ sel_brand.name }} — Stock Matrix
      {% if sel_brand.is_special_tracked %}
        <span style="font-size:.65rem;background:rgba(245,166,35,.15);color:var(--accent);border-radius:50px;padding:.15rem .6rem;margin-left:.5rem">★ Tracked</span>
      {% endif %}
    </h5>
    <div style="display:flex;align-items:center;gap:.75rem">
      <div class="save-dot" id="saveDot"></div>
      <span style="font-size:.78rem;color:var(--muted)" id="saveStatus">Click any cell to edit stock</span>
    </div>
  </div>

  <div class="matrix-wrap">
    {% if products and all_sizes %}
    <table class="matrix-table">
      <thead>
        <tr>
          <th style="min-width:200px">Item Name</th>
          {% for size in all_sizes %}
          <th class="size-col">{{ size }}</th>
          {% endfor %}
          <th style="text-align:center">Total</th>
        </tr>
      </thead>
      <tbody>
        {% for p in products %}
        {% set variant_map = {} %}
        {% for v in p.variants %}{% set _ = variant_map.update({v.size: v}) %}{% endfor %}
        <tr>
          <td class="prod-name-cell" title="{{ p.name }}">{{ p.name }}</td>
          {% set row_total = namespace(val=0) %}
          {% for size in all_sizes %}
            {% if size in variant_map %}
              {% set v = variant_map[size] %}
              {% set _ = row_total.__setattr__('val', row_total.val + v.stock_quantity) %}
              <td class="stock-cell">
                <input type="number" min="0"
                       class="stock-input {% if v.is_out_of_stock %}oos{% elif v.is_low_stock %}low{% else %}good{% endif %}"
                       value="{{ v.stock_quantity }}"
                       data-variant-id="{{ v.id }}"
                       onchange="updateStock(this)">
              </td>
            {% else %}
              <td class="no-variant">—</td>
            {% endif %}
          {% endfor %}
          <td style="text-align:center;font-weight:700;font-family:var(--ff-mono);color:{% if row_total.val == 0 %}var(--accent2){% elif row_total.val < 10 %}var(--accent){% else %}var(--green){% endif %}">
            {{ row_total.val }}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% elif products %}
    <div style="padding:3rem;text-align:center;color:var(--muted)">
      No size variants added yet. <a href="{{ url_for('admin.products') }}" style="color:var(--accent)">Edit products to add sizes →</a>
    </div>
    {% else %}
    <div style="padding:3rem;text-align:center;color:var(--muted)">
      No products found for {{ sel_brand.name }}.
      <a href="{{ url_for('admin.add_product') }}" style="color:var(--accent)">Add a product →</a>
    </div>
    {% endif %}
  </div>

  <!-- Legend -->
  <div style="padding:.8rem 1.4rem;border-top:1px solid var(--border);display:flex;gap:1.5rem;flex-wrap:wrap">
    <span style="font-size:.75rem;color:var(--green)">● Good stock</span>
    <span style="font-size:.75rem;color:var(--accent)">● Low stock (≤ threshold)</span>
    <span style="font-size:.75rem;color:var(--accent2)">● Out of stock</span>
    <span style="font-size:.75rem;color:var(--muted)">— Size not available for this item</span>
  </div>
</div>
{% endif %}

{% endblock %}
{% block extra_js %}
<script>
async function updateStock(input) {
  const dot = document.getElementById('saveDot');
  const status = document.getElementById('saveStatus');
  dot.style.display = 'block';
  status.textContent = 'Saving…';
  const res = await fetch('/admin/inventory/update', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({variant_id: parseInt(input.dataset.variantId), qty: parseInt(input.value)||0})
  });
  const data = await res.json();
  if (data.ok) {
    input.className = 'stock-input ' + (data.oos ? 'oos' : data.low ? 'low' : 'good');
    status.textContent = '✓ Saved!';
    setTimeout(() => { dot.style.display='none'; status.textContent='Click any cell to edit stock'; }, 1500);
    // Update row total
    const row = input.closest('tr');
    let total = 0;
    row.querySelectorAll('.stock-input').forEach(i => total += parseInt(i.value)||0);
    const totalCell = row.querySelector('td:last-child');
    if (totalCell) {
      totalCell.textContent = total;
      totalCell.style.color = total===0 ? 'var(--accent2)' : total < 10 ? 'var(--accent)' : 'var(--green)';
    }
  }
}
</script>
{% endblock %}
""")

# ══════════════════════════════════════════════════════════════════════════════
# 7. EMPLOYEES
# ══════════════════════════════════════════════════════════════════════════════
w("app/templates/admin/employees.html", r"""{% extends 'admin/base_admin.html' %}
{% block title %}Employees{% endblock %}
{% block page_title %}Employee Management{% endblock %}
{% block content %}

<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.5rem">
  <div>
    <div style="font-size:.85rem;color:var(--muted)">{{ employees|length }} staff member{% if employees|length!=1 %}s{% endif %} registered</div>
  </div>
  <a href="{{ url_for('admin.add_employee') }}" class="btn-accent">
    <i class="bi bi-person-plus"></i> Add Employee
  </a>
</div>

{% if employees %}
<div class="row g-3">
  {% for emp in employees %}
  <div class="col-md-6 col-xl-4">
    <div class="panel" style="padding:1.3rem;transition:transform .2s;cursor:default" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
      <div style="display:flex;align-items:flex-start;gap:1rem;margin-bottom:1rem">
        <!-- Avatar -->
        <div style="width:48px;height:48px;border-radius:12px;background:linear-gradient(135deg,var(--accent),#E8903A);
             display:flex;align-items:center;justify-content:center;font-family:var(--ff-head);
             font-size:1.3rem;font-weight:800;color:#fff;flex-shrink:0">
          {{ emp.user.full_name[0] }}
        </div>
        <div style="flex:1;min-width:0">
          <div style="font-family:var(--ff-head);font-size:1.05rem;font-weight:700">{{ emp.user.full_name }}</div>
          <div style="font-size:.78rem;color:var(--muted)">{{ emp.designation or 'Staff' }}</div>
          <span style="display:inline-block;margin-top:.25rem;font-size:.68rem;background:rgba(74,158,255,.15);color:var(--blue);border-radius:50px;padding:.1rem .55rem;font-weight:600">
            {{ emp.department or 'General' }}
          </span>
        </div>
        <span class="badge-status {% if emp.user.is_active_account %}badge-online{% else %}badge-offline{% endif %}">
          {{ 'Active' if emp.user.is_active_account else 'Inactive' }}
        </span>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:.6rem;margin-bottom:1rem">
        <div style="background:var(--surface2);border-radius:8px;padding:.6rem .8rem">
          <div style="font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px">EMP ID</div>
          <div style="font-family:var(--ff-mono);font-size:.82rem;color:var(--accent)">{{ emp.employee_code }}</div>
        </div>
        <div style="background:var(--surface2);border-radius:8px;padding:.6rem .8rem">
          <div style="font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px">Base Salary</div>
          <div style="font-weight:700;font-size:.88rem">₹{{ "%.0f"|format(emp.base_salary or 0) }}/mo</div>
        </div>
        <div style="background:var(--surface2);border-radius:8px;padding:.6rem .8rem">
          <div style="font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px">Commission</div>
          <div style="font-size:.82rem;color:var(--green)">{{ "%.1f"|format((emp.commission_rate or 0)*100) }}%</div>
        </div>
        <div style="background:var(--surface2);border-radius:8px;padding:.6rem .8rem">
          <div style="font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px">Joined</div>
          <div style="font-size:.78rem">{{ emp.date_of_joining.strftime('%d %b %Y') if emp.date_of_joining else '—' }}</div>
        </div>
      </div>

      <div style="font-size:.78rem;color:var(--muted);margin-bottom:.9rem">
        <i class="bi bi-envelope me-1"></i>{{ emp.user.email }}<br>
        <i class="bi bi-phone me-1 mt-1"></i>{{ emp.user.phone or '—' }}
      </div>
      <div style="font-size:.78rem;color:var(--muted);margin-bottom:1rem">
        <i class="bi bi-person-circle me-1"></i>Login: <code style="color:var(--accent)">{{ emp.user.username }}</code>
      </div>

      <div style="display:flex;gap:.5rem">
        <a href="{{ url_for('admin.edit_employee', eid=emp.id) }}" class="btn-edit" style="flex:1;justify-content:center">
          <i class="bi bi-pencil"></i> Edit
        </a>
        <form method="POST" action="{{ url_for('admin.delete_employee', eid=emp.id) }}"
              onsubmit="return confirm('Deactivate {{ emp.user.full_name }}?')">
          <button type="submit" class="btn-danger"><i class="bi bi-person-x"></i></button>
        </form>
      </div>
    </div>
  </div>
  {% endfor %}
</div>

{% else %}
<div style="text-align:center;padding:5rem;color:var(--muted)">
  <i class="bi bi-people" style="font-size:3rem;display:block;margin-bottom:1rem;opacity:.3"></i>
  <h4 style="font-family:var(--ff-head)">No employees yet</h4>
  <p>Add your first staff member to get started.</p>
  <a href="{{ url_for('admin.add_employee') }}" class="btn-accent">Add Employee</a>
</div>
{% endif %}
{% endblock %}
""")

# ══════════════════════════════════════════════════════════════════════════════
# 8. EMPLOYEE FORM
# ══════════════════════════════════════════════════════════════════════════════
w("app/templates/admin/employee_form.html", r"""{% extends 'admin/base_admin.html' %}
{% block title %}{{ 'Edit' if emp else 'Add' }} Employee{% endblock %}
{% block page_title %}{{ 'Edit Employee' if emp else 'Add New Employee' }}{% endblock %}
{% block content %}
<div style="max-width:700px">
  <a href="{{ url_for('admin.employees') }}" class="btn-ghost mb-4" style="display:inline-flex">
    <i class="bi bi-arrow-left"></i> Back to Employees
  </a>
  <form method="POST">
    <div class="panel mb-4">
      <div class="panel-head"><h5>Personal Information</h5></div>
      <div class="panel-body">
        <div class="row g-3">
          <div class="col-md-6">
            <label class="ctrl-label">Full Name *</label>
            <input type="text" name="full_name" class="ctrl" required
                   value="{{ emp.user.full_name if emp else '' }}" placeholder="Ravi Kumar">
          </div>
          <div class="col-md-6">
            <label class="ctrl-label">Phone</label>
            <input type="tel" name="phone" class="ctrl"
                   value="{{ emp.user.phone if emp else '' }}" placeholder="9876543210">
          </div>
          {% if not emp %}
          <div class="col-md-6">
            <label class="ctrl-label">Username (for login) *</label>
            <input type="text" name="username" class="ctrl" required placeholder="ravi.kumar">
          </div>
          <div class="col-md-6">
            <label class="ctrl-label">Email *</label>
            <input type="email" name="email" class="ctrl" required placeholder="ravi@mbmaniyar.com">
          </div>
          <div class="col-md-6">
            <label class="ctrl-label">Password *</label>
            <input type="text" name="password" class="ctrl" required placeholder="Set login password">
          </div>
          {% else %}
          <div class="col-md-6">
            <label class="ctrl-label">New Password (leave blank to keep)</label>
            <input type="text" name="new_password" class="ctrl" placeholder="Enter new password">
          </div>
          {% endif %}
        </div>
      </div>
    </div>

    <div class="panel mb-4">
      <div class="panel-head"><h5>Job Details</h5></div>
      <div class="panel-body">
        <div class="row g-3">
          <div class="col-md-4">
            <label class="ctrl-label">Employee Code *</label>
            <input type="text" name="employee_code" class="ctrl" required
                   value="{{ emp.employee_code if emp else '' }}" placeholder="MBM-001"
                   {% if emp %}readonly style="opacity:.6"{% endif %}>
          </div>
          <div class="col-md-4">
            <label class="ctrl-label">Designation</label>
            <input type="text" name="designation" class="ctrl"
                   value="{{ emp.designation if emp else '' }}" placeholder="Sales Associate">
          </div>
          <div class="col-md-4">
            <label class="ctrl-label">Department</label>
            <select name="department" class="ctrl">
              {% for d in ['Sales Floor','Billing Counter','Stock Room','Management','Security'] %}
              <option {% if emp and emp.department==d %}selected{% endif %}>{{ d }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="col-md-4">
            <label class="ctrl-label">Date of Joining</label>
            <input type="date" name="date_of_joining" class="ctrl"
                   value="{{ emp.date_of_joining.strftime('%Y-%m-%d') if emp and emp.date_of_joining else '' }}">
          </div>
          <div class="col-md-4">
            <label class="ctrl-label">Base Salary (₹/month)</label>
            <input type="number" name="base_salary" class="ctrl" step="0.01"
                   value="{{ emp.base_salary if emp else '' }}" placeholder="15000">
          </div>
          <div class="col-md-4">
            <label class="ctrl-label">Commission Rate (%)</label>
            <input type="number" name="commission_rate" class="ctrl" step="0.01" min="0" max="100"
                   value="{{ (emp.commission_rate*100)|round(2) if emp else '0' }}" placeholder="2.0">
            <div style="font-size:.72rem;color:var(--muted);margin-top:.3rem">% of sales they handle</div>
          </div>
        </div>
      </div>
    </div>

    <button type="submit" class="btn-accent" style="padding:.8rem 2.5rem;font-size:1rem">
      <i class="bi bi-check-lg me-2"></i>{{ 'Update Employee' if emp else 'Add Employee' }}
    </button>
  </form>
</div>
{% endblock %}
""")

# ══════════════════════════════════════════════════════════════════════════════
# 9. ORDERS
# ══════════════════════════════════════════════════════════════════════════════
w("app/templates/admin/orders.html", r"""{% extends 'admin/base_admin.html' %}
{% block title %}Orders{% endblock %}
{% block page_title %}Order Management{% endblock %}
{% block content %}

<!-- Status tabs -->
<div style="display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:1.5rem">
  {% for s in [('all','All Orders'),('confirmed','Pending Pickup'),('ready_for_pickup','Ready'),('completed','Completed'),('cancelled','Cancelled')] %}
  <a href="{{ url_for('admin.orders', status=s[0]) }}"
     style="padding:.4rem 1rem;border-radius:8px;font-size:.82rem;font-weight:600;text-decoration:none;transition:all .2s;
            {% if status==s[0] %}background:var(--accent);color:#1A1A00{% else %}background:var(--surface2);color:var(--muted){% endif %}">
    {{ s[1] }}
  </a>
  {% endfor %}
</div>

<div class="panel">
  <div class="panel-head">
    <h5><i class="bi bi-receipt me-2"></i>{{ orders|length }} Order{% if orders|length!=1 %}s{% endif %}</h5>
  </div>
  <div style="overflow-x:auto">
    <table class="data-table">
      <thead>
        <tr><th>Order #</th><th>Customer</th><th>Items</th><th>Total</th><th>Payment</th><th>Status</th><th>Date</th><th>Update</th></tr>
      </thead>
      <tbody>
        {% for o in orders %}
        <tr>
          <td><span style="font-family:var(--ff-mono);font-size:.82rem;color:var(--accent)">{{ o.order_number }}</span></td>
          <td>
            <div style="font-size:.875rem;font-weight:500">{{ o.customer.full_name }}</div>
            <div style="font-size:.75rem;color:var(--muted)">{{ o.customer.phone or o.customer.email }}</div>
          </td>
          <td>
            {% for item in o.items %}
            <div style="font-size:.78rem;color:var(--muted)">{{ item.product.name[:20] }}… × {{ item.quantity }} ({{ item.variant.size }})</div>
            {% endfor %}
          </td>
          <td style="font-weight:700;font-family:var(--ff-mono)">₹{{ "%.0f"|format(o.total_amount) }}</td>
          <td>
            <form method="POST" action="{{ url_for('admin.update_order', oid=o.id) }}">
              <input type="hidden" name="status" value="{{ o.status }}">
              <select name="payment_status" class="ctrl" style="padding:.3rem .5rem;font-size:.78rem;width:110px;margin-bottom:.25rem"
                      onchange="this.form.submit()">
                <option value="pending" {% if o.payment_status=='pending' %}selected{% endif %}>⏳ Pending</option>
                <option value="paid" {% if o.payment_status=='paid' %}selected{% endif %}>✅ Paid</option>
              </select>
            </form>
            <div style="font-size:.72rem;color:var(--muted)">{{ o.payment_method or '—' }}</div>
          </td>
          <td>
            <span class="badge-status badge-{{ o.status }}">{{ o.status|replace('_',' ')|title }}</span>
          </td>
          <td style="font-size:.8rem;color:var(--muted);white-space:nowrap">{{ o.created_at.strftime('%d %b %y') }}<br>{{ o.created_at.strftime('%I:%M %p') }}</td>
          <td>
            <form method="POST" action="{{ url_for('admin.update_order', oid=o.id) }}">
              <input type="hidden" name="payment_status" value="{{ o.payment_status }}">
              <select name="status" class="ctrl" style="padding:.3rem .5rem;font-size:.78rem;width:150px"
                      onchange="this.form.submit()">
                {% for s in ['confirmed','ready_for_pickup','completed','cancelled'] %}
                <option value="{{ s }}" {% if o.status==s %}selected{% endif %}>{{ s|replace('_',' ')|title }}</option>
                {% endfor %}
              </select>
            </form>
          </td>
        </tr>
        {% else %}
        <tr><td colspan="8" style="text-align:center;padding:3rem;color:var(--muted)">No orders found</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
""")

# ══════════════════════════════════════════════════════════════════════════════
# 10. FIX __init__.py  — add `now` to Jinja context
# ══════════════════════════════════════════════════════════════════════════════
init_path = os.path.join(BASE, "app/__init__.py")
with open(init_path, 'r') as f:
    init_content = f.read()

if 'jinja_env' not in init_content:
    inject = '''
    # Make datetime.now() available in all templates
    from datetime import datetime
    app.jinja_env.globals['now'] = datetime.now
'''
    init_content = init_content.replace(
        '    with app.app_context():',
        inject + '\n    with app.app_context():'
    )
    with open(init_path, 'w') as f:
        f.write(init_content)
    print("  ✅ app/__init__.py (patched with now() helper)")

print()
print("=" * 55)
print("  🎉 Admin dashboard built successfully!")
print("  Run: python3 run.py")
print("  URL: http://localhost:5000/admin/")
print("=" * 55)

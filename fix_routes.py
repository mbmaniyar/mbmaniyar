import os

BASE = os.path.expanduser("~/Desktop/mbmaniyar")

content = '''
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from app.models import (db, User, Product, ProductVariant, Category, Brand,
                         Employee, Order, OrderItem, Shift, Task, MonthlySalary)
from datetime import date, datetime
import os, json

admin_bp = Blueprint(\'admin\', __name__)
ALLOWED_IMG = {\'png\',\'jpg\',\'jpeg\',\'gif\',\'webp\'}

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != \'admin\':
            flash(\'Admin access required.\', \'danger\')
            return redirect(url_for(\'auth.login\'))
        return f(*args, **kwargs)
    return decorated

def allowed_file(fn):
    return \'.\' in fn and fn.rsplit(\'.\',1)[1].lower() in ALLOWED_IMG

# ── DASHBOARD ────────────────────────────────────────────────────
@admin_bp.route(\'/\')
@admin_required
def dashboard():
    stats = {
        \'total_products\' : Product.query.filter_by(is_active=True).count(),
        \'total_orders\'   : Order.query.count(),
        \'pending_orders\' : Order.query.filter_by(status=\'confirmed\').count(),
        \'total_customers\': User.query.filter_by(role=\'customer\').count(),
        \'total_employees\': Employee.query.count(),
        \'low_stock\'      : ProductVariant.query.filter(
                             ProductVariant.stock_quantity <= ProductVariant.low_stock_threshold,
                             ProductVariant.stock_quantity > 0).count(),
        \'out_of_stock\'   : ProductVariant.query.filter_by(stock_quantity=0).count(),
        \'total_revenue\'  : db.session.query(db.func.sum(Order.total_amount))
                             .filter_by(payment_status=\'paid\').scalar() or 0,
    }
    recent_orders   = Order.query.order_by(Order.created_at.desc()).limit(8).all()
    low_stock_items = ProductVariant.query.filter(
        ProductVariant.stock_quantity <= ProductVariant.low_stock_threshold,
        ProductVariant.stock_quantity > 0).limit(6).all()
    return render_template(\'admin/dashboard.html\',
        stats=stats, recent_orders=recent_orders, low_stock_items=low_stock_items)

# ── PRODUCTS ─────────────────────────────────────────────────────
@admin_bp.route(\'/products\')
@admin_required
def products():
    search=request.args.get(\'q\',\'\').strip()
    cat_id=request.args.get(\'cat\',\'all\')
    brand_id=request.args.get(\'brand\',\'all\')
    q=Product.query
    if search: q=q.filter(Product.name.ilike(f\'%{search}%\'))
    if cat_id!=\'all\': q=q.filter_by(category_id=int(cat_id))
    if brand_id!=\'all\': q=q.filter_by(brand_id=int(brand_id))
    return render_template(\'admin/products.html\',
        products=q.order_by(Product.created_at.desc()).all(),
        categories=Category.query.all(), brands=Brand.query.all(),
        search=search, active_cat=cat_id, active_brand=brand_id)

@admin_bp.route(\'/products/add\', methods=[\'GET\',\'POST\'])
@admin_required
def add_product():
    categories=Category.query.all(); brands=Brand.query.all()
    if request.method==\'POST\':
        name=request.form.get(\'name\',\'\').strip()
        sku=request.form.get(\'sku\',\'\').strip()
        price=request.form.get(\'price\',type=float)
        mrp=request.form.get(\'mrp\',type=float) or None
        cat_id=request.form.get(\'category_id\',type=int)
        brand_id=request.form.get(\'brand_id\',type=int)
        description=request.form.get(\'description\',\'\').strip()
        is_online=bool(request.form.get(\'is_online\'))
        sizes_raw=request.form.get(\'sizes_json\',\'[]\')
        if not all([name,sku,price,cat_id,brand_id]):
            flash(\'Fill all required fields.\',\'danger\')
            return render_template(\'admin/product_form.html\',categories=categories,brands=brands,product=None)
        if Product.query.filter_by(sku=sku).first():
            flash(f\'SKU {sku} already exists.\',\'danger\')
            return render_template(\'admin/product_form.html\',categories=categories,brands=brands,product=None)
        img_filename=None
        if \'image\' in request.files:
            file=request.files[\'image\']
            if file and file.filename and allowed_file(file.filename):
                from flask import current_app
                filename=secure_filename(f"{sku}_{file.filename}")
                upload_path=current_app.config[\'UPLOAD_FOLDER\']
                os.makedirs(upload_path,exist_ok=True)
                file.save(os.path.join(upload_path,filename))
                img_filename=filename
        product=Product(name=name,sku=sku,price=price,mrp=mrp,
            category_id=cat_id,brand_id=brand_id,description=description,
            is_online=is_online,is_active=True,image_filename=img_filename)
        db.session.add(product); db.session.flush()
        try:
            for s in json.loads(sizes_raw):
                if s.get(\'size\',\'\').strip():
                    db.session.add(ProductVariant(product_id=product.id,
                        size=s[\'size\'].strip(),
                        stock_quantity=int(s.get(\'stock\',0)),
                        low_stock_threshold=int(s.get(\'threshold\',3))))
        except: pass
        db.session.commit()
        flash(f\'Product "{name}" added! \u2705\',\'success\')
        return redirect(url_for(\'admin.products\'))
    return render_template(\'admin/product_form.html\',categories=categories,brands=brands,product=None)

@admin_bp.route(\'/products/edit/<int:pid>\', methods=[\'GET\',\'POST\'])
@admin_required
def edit_product(pid):
    product=Product.query.get_or_404(pid)
    categories=Category.query.all(); brands=Brand.query.all()
    if request.method==\'POST\':
        product.name=request.form.get(\'name\',\'\').strip()
        product.price=request.form.get(\'price\',type=float)
        product.mrp=request.form.get(\'mrp\',type=float) or None
        product.category_id=request.form.get(\'category_id\',type=int)
        product.brand_id=request.form.get(\'brand_id\',type=int)
        product.description=request.form.get(\'description\',\'\').strip()
        product.is_online=bool(request.form.get(\'is_online\'))
        product.is_active=bool(request.form.get(\'is_active\'))
        if \'image\' in request.files:
            file=request.files[\'image\']
            if file and file.filename and allowed_file(file.filename):
                from flask import current_app
                filename=secure_filename(f"{product.sku}_{file.filename}")
                upload_path=current_app.config[\'UPLOAD_FOLDER\']
                os.makedirs(upload_path,exist_ok=True)
                file.save(os.path.join(upload_path,filename))
                product.image_filename=filename
        sizes_raw=request.form.get(\'sizes_json\',\'[]\')
        try:
            for v in product.variants: db.session.delete(v)
            db.session.flush()
            for s in json.loads(sizes_raw):
                if s.get(\'size\',\'\').strip():
                    db.session.add(ProductVariant(product_id=product.id,
                        size=s[\'size\'].strip(),
                        stock_quantity=int(s.get(\'stock\',0)),
                        low_stock_threshold=int(s.get(\'threshold\',3))))
        except: pass
        db.session.commit()
        flash(\'Product updated! \u2705\',\'success\')
        return redirect(url_for(\'admin.products\'))
    return render_template(\'admin/product_form.html\',categories=categories,brands=brands,product=product)

@admin_bp.route(\'/products/delete/<int:pid>\', methods=[\'POST\'])
@admin_required
def delete_product(pid):
    p=Product.query.get_or_404(pid); p.is_active=False; db.session.commit()
    flash(f\'"{p.name}" removed.\',\'info\')
    return redirect(url_for(\'admin.products\'))

@admin_bp.route(\'/products/toggle/<int:pid>\', methods=[\'POST\'])
@admin_required
def toggle_product(pid):
    p=Product.query.get_or_404(pid); p.is_online=not p.is_online; db.session.commit()
    return jsonify({\'is_online\':p.is_online})

# ── INVENTORY ─────────────────────────────────────────────────────
@admin_bp.route(\'/inventory\')
@admin_required
def inventory():
    brands=Brand.query.all()
    brand_id=request.args.get(\'brand_id\',type=int)
    sel_brand=Brand.query.get(brand_id) if brand_id else Brand.query.filter_by(is_special_tracked=True).first()
    products=[]; all_sizes=[]
    if sel_brand:
        products=Product.query.filter_by(brand_id=sel_brand.id,is_active=True).all()
        size_set=set()
        for p in products:
            for v in p.variants: size_set.add(v.size)
        size_order=[\'2Y\',\'4Y\',\'6Y\',\'8Y\',\'10Y\',\'XS\',\'S\',\'M\',\'L\',\'XL\',\'XXL\',\'XXXL\',\'26\',\'28\',\'30\',\'32\',\'34\',\'36\',\'38\',\'40\',\'42\']
        all_sizes=sorted(size_set,key=lambda x:size_order.index(x) if x in size_order else 99)
    return render_template(\'admin/inventory.html\',
        brands=brands,sel_brand=sel_brand,products=products,all_sizes=all_sizes)

@admin_bp.route(\'/inventory/update\', methods=[\'POST\'])
@admin_required
def update_stock():
    data=request.json; variant_id=data.get(\'variant_id\'); new_qty=data.get(\'qty\',0)
    variant=ProductVariant.query.get(variant_id)
    if not variant: return jsonify({\'error\':\'Not found\'}),404
    variant.stock_quantity=max(0,int(new_qty)); db.session.commit()
    return jsonify({\'ok\':True,\'qty\':variant.stock_quantity,
        \'low\':variant.is_low_stock,\'oos\':variant.is_out_of_stock})

# ── CATEGORIES & BRANDS ───────────────────────────────────────────
@admin_bp.route(\'/categories/add\', methods=[\'POST\'])
@admin_required
def add_category():
    name=request.form.get(\'name\',\'\').strip()
    if name:
        slug=name.lower().replace(\' \',\'-\')
        if not Category.query.filter_by(slug=slug).first():
            db.session.add(Category(name=name,slug=slug)); db.session.commit()
            flash(f\'Category "{name}" added!\',\'success\')
        else: flash(\'Already exists.\',\'warning\')
    return redirect(url_for(\'admin.products\'))

@admin_bp.route(\'/brands/add\', methods=[\'POST\'])
@admin_required
def add_brand():
    name=request.form.get(\'name\',\'\').strip()
    special=bool(request.form.get(\'is_special_tracked\'))
    if name:
        if not Brand.query.filter_by(name=name).first():
            db.session.add(Brand(name=name,is_special_tracked=special)); db.session.commit()
            flash(f\'Brand "{name}" added!\',\'success\')
        else: flash(\'Already exists.\',\'warning\')
    return redirect(url_for(\'admin.products\'))

# ── EMPLOYEES ─────────────────────────────────────────────────────
@admin_bp.route(\'/employees\')
@admin_required
def employees():
    return render_template(\'admin/employees.html\',employees=Employee.query.join(User).all())

@admin_bp.route(\'/employees/add\', methods=[\'GET\',\'POST\'])
@admin_required
def add_employee():
    if request.method==\'POST\':
        full_name=request.form.get(\'full_name\',\'\').strip()
        username=request.form.get(\'username\',\'\').strip()
        email=request.form.get(\'email\',\'\').strip()
        phone=request.form.get(\'phone\',\'\').strip()
        password=request.form.get(\'password\',\'\').strip()
        emp_code=request.form.get(\'employee_code\',\'\').strip()
        designation=request.form.get(\'designation\',\'\').strip()
        department=request.form.get(\'department\',\'\').strip()
        base_salary=request.form.get(\'base_salary\',type=float) or 0
        comm_rate=request.form.get(\'commission_rate\',type=float) or 0
        doj_str=request.form.get(\'date_of_joining\',\'\')
        if User.query.filter_by(username=username).first():
            flash(\'Username taken.\',\'danger\')
            return render_template(\'admin/employee_form.html\',emp=None)
        user=User(full_name=full_name,username=username,email=email,phone=phone,
            password_hash=generate_password_hash(password),role=\'employee\')
        db.session.add(user); db.session.flush()
        doj=datetime.strptime(doj_str,\'%Y-%m-%d\').date() if doj_str else date.today()
        emp=Employee(user_id=user.id,employee_code=emp_code,designation=designation,
            department=department,date_of_joining=doj,base_salary=base_salary,
            commission_rate=comm_rate/100)
        db.session.add(emp); db.session.commit()
        flash(f\'Employee {full_name} added! Login: {username} / {password}\',\'success\')
        return redirect(url_for(\'admin.employees\'))
    return render_template(\'admin/employee_form.html\',emp=None)

@admin_bp.route(\'/employees/edit/<int:eid>\', methods=[\'GET\',\'POST\'])
@admin_required
def edit_employee(eid):
    emp=Employee.query.get_or_404(eid)
    if request.method==\'POST\':
        emp.user.full_name=request.form.get(\'full_name\',\'\').strip()
        emp.user.phone=request.form.get(\'phone\',\'\').strip()
        emp.designation=request.form.get(\'designation\',\'\').strip()
        emp.department=request.form.get(\'department\',\'\').strip()
        emp.base_salary=request.form.get(\'base_salary\',type=float) or 0
        emp.commission_rate=(request.form.get(\'commission_rate\',type=float) or 0)/100
        new_pass=request.form.get(\'new_password\',\'\').strip()
        if new_pass: emp.user.password_hash=generate_password_hash(new_pass)
        db.session.commit(); flash(\'Employee updated! \u2705\',\'success\')
        return redirect(url_for(\'admin.employees\'))
    return render_template(\'admin/employee_form.html\',emp=emp)

@admin_bp.route(\'/employees/delete/<int:eid>\', methods=[\'POST\'])
@admin_required
def delete_employee(eid):
    emp=Employee.query.get_or_404(eid)
    emp.user.is_active_account=False; db.session.commit()
    flash(f\'{emp.user.full_name} deactivated.\',\'info\')
    return redirect(url_for(\'admin.employees\'))

# ── CUSTOMERS ─────────────────────────────────────────────────────
@admin_bp.route(\'/customers\')
@admin_required
def customers():
    all_customers=User.query.filter_by(role=\'customer\').order_by(User.created_at.desc()).all()
    return render_template(\'admin/customers.html\',customers=all_customers)

# ── ORDERS ────────────────────────────────────────────────────────
@admin_bp.route(\'/orders\')
@admin_required
def orders():
    status=request.args.get(\'status\',\'all\')
    q=Order.query
    if status!=\'all\': q=q.filter_by(status=status)
    return render_template(\'admin/orders.html\',
        orders=q.order_by(Order.created_at.desc()).all(),status=status)

@admin_bp.route(\'/orders/update/<int:oid>\', methods=[\'POST\'])
@admin_required
def update_order(oid):
    order=Order.query.get_or_404(oid)
    ns=request.form.get(\'status\'); pm=request.form.get(\'payment_status\')
    if ns: order.status=ns
    if pm: order.payment_status=pm
    db.session.commit()
    flash(f\'Order {order.order_number} updated!\',\'success\')
    return redirect(url_for(\'admin.orders\'))
'''

path = os.path.join(BASE, "app/admin/routes.py")
with open(path, "w") as f:
    f.write(content)

print("✅ admin/routes.py completely rewritten — no more duplicates!")
print("   Now run: python3 run.py")

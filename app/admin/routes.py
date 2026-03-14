from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user
from functools import wraps
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from app.models import (db, User, Product, ProductVariant, Category, Brand,
                        Employee, Order, OrderItem, Shift, Task, MonthlySalary)
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

# ── DASHBOARD ────────────────────────────────────────────────────
@admin_bp.route('/')
@admin_required
def dashboard():
    stats = {
        'total_products':  Product.query.filter_by(is_active=True).count(),
        'total_orders':    Order.query.count(),
        'pending_orders':  Order.query.filter_by(status='confirmed').count(),
        'total_customers': User.query.filter_by(role='customer').count(),
        'total_employees': Employee.query.count(),
        'low_stock':       ProductVariant.query.filter(
                               ProductVariant.stock_quantity <= ProductVariant.low_stock_threshold,
                               ProductVariant.stock_quantity > 0).count(),
        'out_of_stock':    ProductVariant.query.filter_by(stock_quantity=0).count(),
        'total_revenue':   db.session.query(db.func.sum(Order.total_amount))
                               .filter_by(payment_status='paid').scalar() or 0,
    }
    recent_orders   = Order.query.order_by(Order.created_at.desc()).limit(8).all()
    low_stock_items = ProductVariant.query.filter(
        ProductVariant.stock_quantity <= ProductVariant.low_stock_threshold,
        ProductVariant.stock_quantity > 0).limit(6).all()
    return render_template('admin/dashboard.html',
        stats=stats, recent_orders=recent_orders, low_stock_items=low_stock_items)

# ── PRODUCTS ─────────────────────────────────────────────────────
@admin_bp.route('/products')
@admin_required
def products():
    search   = request.args.get('q', '').strip()
    cat_id   = request.args.get('cat', 'all')
    brand_id = request.args.get('brand', 'all')
    q = Product.query
    if search:
        q = q.filter(Product.name.ilike(f'%{search}%'))
    if cat_id != 'all':
        q = q.filter_by(category_id=int(cat_id))
    if brand_id != 'all':
        q = q.filter_by(brand_id=int(brand_id))
    return render_template('admin/products.html',
        products=q.order_by(Product.created_at.desc()).all(),
        categories=Category.query.all(),
        brands=Brand.query.all(),
        search=search, active_cat=cat_id, active_brand=brand_id)

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    categories = Category.query.all()
    brands     = Brand.query.all()
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        sku         = request.form.get('sku', '').strip()
        price       = request.form.get('price', type=float)
        mrp         = request.form.get('mrp', type=float) or None
        cat_id      = request.form.get('category_id', type=int)
        brand_id    = request.form.get('brand_id', type=int)
        description = request.form.get('description', '').strip()
        is_online   = bool(request.form.get('is_online'))
        sizes_raw   = request.form.get('sizes_json', '[]')
        if not all([name, sku, price, cat_id, brand_id]):
            flash('Fill all required fields.', 'danger')
            return render_template('admin/product_form.html', categories=categories, brands=brands, product=None)
        if Product.query.filter_by(sku=sku).first():
            flash(f'SKU {sku} already exists.', 'danger')
            return render_template('admin/product_form.html', categories=categories, brands=brands, product=None)
        img_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                from flask import current_app
                filename    = secure_filename(f"{sku}_{file.filename}")
                upload_path = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                img_filename = filename
        product = Product(name=name, sku=sku, price=price, mrp=mrp,
            category_id=cat_id, brand_id=brand_id, description=description,
            is_online=is_online, is_active=True, image_filename=img_filename)
        db.session.add(product)
        db.session.flush()
        try:
            for s in json.loads(sizes_raw):
                if s.get('size', '').strip():
                    db.session.add(ProductVariant(
                        product_id=product.id, size=s['size'].strip(),
                        stock_quantity=int(s.get('stock', 0)),
                        low_stock_threshold=int(s.get('threshold', 3))))
        except Exception:
            pass
        db.session.commit()
        flash(f'Product "{name}" added!', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', categories=categories, brands=brands, product=None)

@admin_bp.route('/products/edit/<int:pid>', methods=['GET', 'POST'])
@admin_required
def edit_product(pid):
    product    = Product.query.get_or_404(pid)
    categories = Category.query.all()
    brands     = Brand.query.all()
    if request.method == 'POST':
        product.name        = request.form.get('name', '').strip()
        product.price       = request.form.get('price', type=float)
        product.mrp         = request.form.get('mrp', type=float) or None
        product.category_id = request.form.get('category_id', type=int)
        product.brand_id    = request.form.get('brand_id', type=int)
        product.description = request.form.get('description', '').strip()
        product.is_online   = bool(request.form.get('is_online'))
        product.is_active   = bool(request.form.get('is_active'))
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                from flask import current_app
                filename    = secure_filename(f"{product.sku}_{file.filename}")
                upload_path = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                product.image_filename = filename
        sizes_raw = request.form.get('sizes_json', '[]')
        try:
            for v in product.variants:
                db.session.delete(v)
            db.session.flush()
            for s in json.loads(sizes_raw):
                if s.get('size', '').strip():
                    db.session.add(ProductVariant(
                        product_id=product.id, size=s['size'].strip(),
                        stock_quantity=int(s.get('stock', 0)),
                        low_stock_threshold=int(s.get('threshold', 3))))
        except Exception:
            pass
        db.session.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', categories=categories, brands=brands, product=product)

@admin_bp.route('/products/delete/<int:pid>', methods=['POST'])
@admin_required
def delete_product(pid):
    p = Product.query.get_or_404(pid)
    p.is_active = False
    db.session.commit()
    flash(f'"{p.name}" removed.', 'info')
    return redirect(url_for('admin.products'))

@admin_bp.route('/products/toggle/<int:pid>', methods=['POST'])
@admin_required
def toggle_product(pid):
    p = Product.query.get_or_404(pid)
    p.is_online = not p.is_online
    db.session.commit()
    return jsonify({'is_online': p.is_online})

# ── INVENTORY ─────────────────────────────────────────────────────
@admin_bp.route('/inventory')
@admin_required
def inventory():
    brands    = Brand.query.all()
    brand_id  = request.args.get('brand_id', type=int)
    sel_brand = Brand.query.get(brand_id) if brand_id else Brand.query.filter_by(is_special_tracked=True).first()
    products  = []
    all_sizes = []
    if sel_brand:
        products = Product.query.filter_by(brand_id=sel_brand.id, is_active=True).all()
        size_set = set()
        for p in products:
            for v in p.variants:
                size_set.add(v.size)
        size_order = ['2Y','4Y','6Y','8Y','10Y','XS','S','M','L','XL','XXL','XXXL',
                      '26','28','30','32','34','36','38','40','42']
        all_sizes = sorted(size_set, key=lambda x: size_order.index(x) if x in size_order else 99)
    return render_template('admin/inventory.html',
        brands=brands, sel_brand=sel_brand, products=products, all_sizes=all_sizes)

@admin_bp.route('/inventory/update', methods=['POST'])
@admin_required
def update_stock():
    data       = request.json
    variant_id = data.get('variant_id')
    new_qty    = data.get('qty', 0)
    variant    = ProductVariant.query.get(variant_id)
    if not variant:
        return jsonify({'error': 'Not found'}), 404
    variant.stock_quantity = max(0, int(new_qty))
    db.session.commit()
    return jsonify({'ok': True, 'qty': variant.stock_quantity,
                    'low': variant.is_low_stock, 'oos': variant.is_out_of_stock})

# ── CATEGORIES & BRANDS ───────────────────────────────────────────
@admin_bp.route('/categories/add', methods=['POST'])
@admin_required
def add_category():
    name = request.form.get('name', '').strip()
    if name:
        slug = name.lower().replace(' ', '-')
        if not Category.query.filter_by(slug=slug).first():
            db.session.add(Category(name=name, slug=slug))
            db.session.commit()
            flash(f'Category "{name}" added!', 'success')
        else:
            flash('Category already exists.', 'warning')
    return redirect(url_for('admin.products'))

@admin_bp.route('/brands/add', methods=['POST'])
@admin_required
def add_brand():
    name    = request.form.get('name', '').strip()
    special = bool(request.form.get('is_special_tracked'))
    if name:
        if not Brand.query.filter_by(name=name).first():
            db.session.add(Brand(name=name, is_special_tracked=special))
            db.session.commit()
            flash(f'Brand "{name}" added!', 'success')
        else:
            flash('Brand already exists.', 'warning')
    return redirect(url_for('admin.products'))

# ── EMPLOYEES ─────────────────────────────────────────────────────
@admin_bp.route('/employees')
@admin_required
def employees():
    return render_template('admin/employees.html', employees=Employee.query.join(User).all())

@admin_bp.route('/employees/add', methods=['GET', 'POST'])
@admin_required
def add_employee():
    if request.method == 'POST':
        full_name   = request.form.get('full_name', '').strip()
        username    = request.form.get('username', '').strip()
        email       = request.form.get('email', '').strip()
        phone       = request.form.get('phone', '').strip()
        password    = request.form.get('password', '').strip()
        emp_code    = request.form.get('employee_code', '').strip()
        designation = request.form.get('designation', '').strip()
        department  = request.form.get('department', '').strip()
        base_salary = request.form.get('base_salary', type=float) or 0
        comm_rate   = request.form.get('commission_rate', type=float) or 0
        doj_str     = request.form.get('date_of_joining', '')
        if User.query.filter_by(username=username).first():
            flash('Username already taken. Choose a different one.', 'danger')
            return render_template('admin/employee_form.html', emp=None)
        if not email:
            email = f"{username}@mbmaniyar.local"
        if User.query.filter_by(email=email).first():
            flash('Email already in use. Leave email blank or use a different one.', 'danger')
            return render_template('admin/employee_form.html', emp=None)
        user = User(full_name=full_name, username=username, email=email,
                    phone=phone, password_hash=generate_password_hash(password),
                    role='employee')
        db.session.add(user)
        db.session.flush()
        doj = datetime.strptime(doj_str, '%Y-%m-%d').date() if doj_str else date.today()
        emp = Employee(user_id=user.id, employee_code=emp_code,
                       designation=designation, department=department,
                       date_of_joining=doj, base_salary=base_salary,
                       commission_rate=comm_rate / 100)
        db.session.add(emp)
        db.session.commit()
        flash(f'Employee {full_name} added! Login: {username} / {password}', 'success')
        return redirect(url_for('admin.employees'))
    return render_template('admin/employee_form.html', emp=None)

@admin_bp.route('/employees/edit/<int:eid>', methods=['GET', 'POST'])
@admin_required
def edit_employee(eid):
    emp = Employee.query.get_or_404(eid)
    if request.method == 'POST':
        emp.user.full_name  = request.form.get('full_name', '').strip()
        emp.user.phone      = request.form.get('phone', '').strip()
        emp.designation     = request.form.get('designation', '').strip()
        emp.department      = request.form.get('department', '').strip()
        emp.base_salary     = request.form.get('base_salary', type=float) or 0
        emp.commission_rate = (request.form.get('commission_rate', type=float) or 0) / 100
        new_pass = request.form.get('new_password', '').strip()
        if new_pass:
            emp.user.password_hash = generate_password_hash(new_pass)
        db.session.commit()
        flash('Employee updated!', 'success')
        return redirect(url_for('admin.employees'))
    return render_template('admin/employee_form.html', emp=emp)

@admin_bp.route('/employees/delete/<int:eid>', methods=['POST'])
@admin_required
def delete_employee(eid):
    emp = Employee.query.get_or_404(eid)
    emp.user.is_active_account = False
    db.session.commit()
    flash(f'{emp.user.full_name} deactivated.', 'info')
    return redirect(url_for('admin.employees'))

# ── CUSTOMERS ─────────────────────────────────────────────────────
@admin_bp.route('/customers')
@admin_required
def customers():
    all_customers = User.query.filter_by(role='customer').order_by(User.created_at.desc()).all()
    return render_template('admin/customers.html', customers=all_customers)

# ── ORDERS ────────────────────────────────────────────────────────
@admin_bp.route('/orders')
@admin_required
def orders():
    status = request.args.get('status', 'all')
    q      = Order.query
    if status != 'all':
        q = q.filter_by(status=status)
    return render_template('admin/orders.html',
        orders=q.order_by(Order.created_at.desc()).all(), status=status)

@admin_bp.route('/orders/update/<int:oid>', methods=['POST'])
@admin_required
def update_order(oid):
    order = Order.query.get_or_404(oid)
    ns    = request.form.get('status')
    pm    = request.form.get('payment_status')
    if ns:
        order.status = ns
    if pm:
        order.payment_status = pm
    db.session.commit()
    # Email customer about status change
    try:
        from app.email_utils import send_order_status_email
        email_sent = send_order_status_email(order)
        if email_sent:
            flash(f'✅ Status updated & email sent to customer!', 'success')
        else:
            flash(f'✅ Status updated. (No email — status not tracked or no customer email)', 'info')
    except Exception as e:
        print(f"Email error: {e}")
        flash(f'✅ Status updated. (Email failed: {e})', 'warning')
    flash(f'Order {order.order_number} updated!', 'success')
    return redirect(url_for('admin.orders'))

# ── POS ───────────────────────────────────────────────────────────
@admin_bp.route('/pos')
@admin_required
def pos():
    products   = Product.query.filter_by(is_active=True).all()
    categories = Category.query.all()
    employees  = Employee.query.join(User).filter(User.is_active_account == True).all()
    return render_template('admin/pos.html',
        products=products, categories=categories, employees=employees)

@admin_bp.route('/pos/search')
@admin_required
def pos_search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    results = Product.query.filter(
        Product.is_active == True,
        db.or_(Product.name.ilike(f'%{q}%'), Product.sku.ilike(f'%{q}%'))
    ).limit(10).all()
    data = []
    for p in results:
        for v in p.variants:
            if v.stock_quantity > 0:
                data.append({
                    'variant_id': v.id, 'product_id': p.id,
                    'name': p.name, 'brand': p.brand.name,
                    'sku': p.sku, 'size': v.size,
                    'price': float(p.price),
                    'mrp': float(p.mrp) if p.mrp else None,
                    'stock': v.stock_quantity,
                    'barcode': v.barcode or '',
                    'category': p.category.name,
                })
    return jsonify(data)

@admin_bp.route('/pos/checkout', methods=['POST'])
@admin_required
def pos_checkout():
    import random
    data           = request.json
    items          = data.get('items', [])
    payment_method = data.get('payment_method', 'cash')
    discount_type  = data.get('discount_type', 'flat')
    discount_val   = float(data.get('discount_value', 0))
    employee_code  = data.get('employee_code', '').strip()
    customer_name  = data.get('customer_name', 'Walk-in Customer').strip()
    notes          = data.get('notes', '')
    if not items:
        return jsonify({'error': 'Cart is empty'}), 400
    subtotal = sum(float(i['price']) * int(i['qty']) for i in items)
    if discount_type == 'percent':
        discount_amount = round(subtotal * discount_val / 100, 2)
    else:
        discount_amount = min(discount_val, subtotal)
    taxable    = subtotal - discount_amount
    tax_rate   = 0.0
    tax_amount = round(taxable * tax_rate, 2)
    total      = round(taxable + tax_amount, 2)
    walkin = User.query.filter_by(username='walkin').first()
    if not walkin:
        walkin = User(username='walkin', email='walkin@mbmaniyar.local',
                      full_name='Walk-in Customer',
                      password_hash=generate_password_hash('walkin123'),
                      role='customer')
        db.session.add(walkin)
        db.session.flush()
    order_number = f"POS-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"
    emp = None
    if employee_code:
        emp = Employee.query.filter_by(employee_code=employee_code).first()
    order = Order(
        order_number=order_number, user_id=walkin.id,
        order_type='pos', status='completed',
        subtotal=subtotal, discount_amount=discount_amount,
        tax_amount=tax_amount, total_amount=total,
        payment_method=payment_method, payment_status='paid',
        customer_notes=f"{customer_name}. {notes}".strip('. '),
        processed_by_id=current_user.id,
    )
    db.session.add(order)
    db.session.flush()
    receipt_items = []
    for i in items:
        variant = ProductVariant.query.get(int(i['variant_id']))
        if not variant:
            continue
        qty = int(i['qty'])
        variant.stock_quantity = max(0, variant.stock_quantity - qty)
        oi = OrderItem(order_id=order.id, product_id=variant.product_id,
                       variant_id=variant.id, quantity=qty,
                       unit_price=float(i['price']),
                       total_price=float(i['price']) * qty)
        db.session.add(oi)
        receipt_items.append({'name': i['name'], 'size': i['size'],
                               'qty': qty, 'price': float(i['price']),
                               'total': float(i['price']) * qty})
    if emp:
        commission = round(total * float(emp.commission_rate), 2)
        today = date.today()
        sal = MonthlySalary.query.filter_by(
            employee_id=emp.id, month=today.month, year=today.year).first()
        if sal:
            sal.commission_earned = float(sal.commission_earned or 0) + commission
        else:
            db.session.add(MonthlySalary(
                employee_id=emp.id, month=today.month, year=today.year,
                base_salary=emp.base_salary, commission_earned=commission))
    db.session.commit()
    return jsonify({
        'ok': True, 'order_number': order_number,
        'customer_name': customer_name, 'items': receipt_items,
        'subtotal': subtotal, 'discount': discount_amount,
        'tax': tax_amount, 'total': total,
        'payment_method': payment_method,
        'employee': emp.user.full_name if emp else None,
        'commission': round(total * float(emp.commission_rate), 2) if emp else 0,
        'timestamp': datetime.now().strftime('%d %b %Y, %I:%M %p'),
        'store_name': 'M B MANIYAR',
        'store_address': 'Main Road, Mantha, India',
    })

# ── TASKS ─────────────────────────────────────────────────────────
@admin_bp.route('/tasks')
@admin_required
def tasks():
    employees = Employee.query.join(User).all()
    emp_id    = request.args.get('emp_id', type=int)
    sel_emp   = Employee.query.get(emp_id) if emp_id else (employees[0] if employees else None)
    all_tasks = Task.query.filter_by(employee_id=sel_emp.id).order_by(
        Task.is_completed, Task.due_date).all() if sel_emp else []
    return render_template('admin/tasks.html',
        employees=employees, sel_emp=sel_emp, tasks=all_tasks)

@admin_bp.route('/tasks/add', methods=['POST'])
@admin_required
def add_task():
    emp_id = request.form.get('employee_id', type=int)
    title  = request.form.get('title', '').strip()
    desc   = request.form.get('description', '').strip()
    due    = request.form.get('due_date', '')
    if emp_id and title:
        due_date = datetime.strptime(due, '%Y-%m-%d').date() if due else None
        db.session.add(Task(employee_id=emp_id, title=title,
                            description=desc, due_date=due_date))
        db.session.commit()
        flash('Task assigned!', 'success')
    return redirect(url_for('admin.tasks', emp_id=emp_id))

@admin_bp.route('/tasks/delete/<int:tid>', methods=['POST'])
@admin_required
def delete_task(tid):
    task   = Task.query.get_or_404(tid)
    emp_id = task.employee_id
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted.', 'info')
    return redirect(url_for('admin.tasks', emp_id=emp_id))

# ── SHIFTS ────────────────────────────────────────────────────────
@admin_bp.route('/shifts')
@admin_required
def shifts():
    employees = Employee.query.join(User).all()
    emp_id    = request.args.get('emp_id', type=int)
    sel_emp   = Employee.query.get(emp_id) if emp_id else (employees[0] if employees else None)
    today     = date.today()
    all_shifts = Shift.query.filter_by(employee_id=sel_emp.id).order_by(
        Shift.date.desc()).limit(30).all() if sel_emp else []
    return render_template('admin/shifts.html',
        employees=employees, sel_emp=sel_emp, shifts=all_shifts, today=today)

@admin_bp.route('/shifts/add', methods=['POST'])
@admin_required
def add_shift():
    emp_id    = request.form.get('employee_id', type=int)
    date_str  = request.form.get('date', '')
    start_str = request.form.get('start_time', '')
    end_str   = request.form.get('end_time', '')
    notes     = request.form.get('notes', '').strip()
    if emp_id and date_str and start_str and end_str:
        shift_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time   = datetime.strptime(end_str, '%H:%M').time()
        db.session.add(Shift(employee_id=emp_id, date=shift_date,
            start_time=start_time, end_time=end_time, notes=notes))
        db.session.commit()
        flash('Shift added!', 'success')
    return redirect(url_for('admin.shifts', emp_id=emp_id))

@admin_bp.route('/shifts/update/<int:sid>', methods=['POST'])
@admin_required
def update_shift(sid):
    shift        = Shift.query.get_or_404(sid)
    shift.status = request.form.get('status', shift.status)
    db.session.commit()
    flash('Shift updated!', 'success')
    return redirect(url_for('admin.shifts', emp_id=shift.employee_id))


# ── NOTICES (Admin posts) ─────────────────────────────────────────
@admin_bp.route('/notices')
@admin_required
def notices():
    notices = Notice.query.order_by(Notice.created_at.desc()).all()
    return render_template('admin/notices.html', notices=notices)

@admin_bp.route('/notices/add', methods=['POST'])
@admin_required
def add_notice():
    from app.models import Notice
    title    = request.form.get('title','').strip()
    body     = request.form.get('body','').strip()
    priority = request.form.get('priority','normal')
    if title and body:
        db.session.add(Notice(title=title, body=body, priority=priority,
                              posted_by=current_user.id))
        db.session.commit()
        flash('Notice posted!','success')
    return redirect(url_for('admin.notices'))

@admin_bp.route('/notices/delete/<int:nid>', methods=['POST'])
@admin_required
def delete_notice(nid):
    from app.models import Notice
    n = Notice.query.get_or_404(nid)
    db.session.delete(n); db.session.commit()
    flash('Notice deleted.','info')
    return redirect(url_for('admin.notices'))

# ── LEAVE MANAGEMENT (Admin approves) ────────────────────────────
@admin_bp.route('/leave')
@admin_required
def leave_requests():
    from app.models import LeaveRequest
    status = request.args.get('status','pending')
    q      = LeaveRequest.query
    if status != 'all':
        q = q.filter_by(status=status)
    requests = q.order_by(LeaveRequest.created_at.desc()).all()
    return render_template('admin/leave_requests.html',
        requests=requests, status=status)

@admin_bp.route('/leave/update/<int:lid>', methods=['POST'])
@admin_required
def update_leave(lid):
    from app.models import LeaveRequest
    leave      = LeaveRequest.query.get_or_404(lid)
    leave.status     = request.form.get('status', leave.status)
    leave.admin_note = request.form.get('admin_note','').strip()
    db.session.commit()
    flash(f'Leave request {leave.status}.','success')
    return redirect(url_for('admin.leave_requests'))

# ── TRAINING RESOURCES (Admin manages) ───────────────────────────
@admin_bp.route('/training')
@admin_required
def training():
    from app.models import TrainingResource
    resources = TrainingResource.query.order_by(TrainingResource.created_at.desc()).all()
    return render_template('admin/training.html', resources=resources)

@admin_bp.route('/training/add', methods=['POST'])
@admin_required
def add_training():
    from app.models import TrainingResource
    title   = request.form.get('title','').strip()
    desc    = request.form.get('description','').strip()
    rtype   = request.form.get('resource_type','guide')
    content = request.form.get('content','').strip()
    cat     = request.form.get('category','General').strip()
    if title:
        db.session.add(TrainingResource(title=title, description=desc,
            resource_type=rtype, content=content, category=cat))
        db.session.commit()
        flash('Resource added!','success')
    return redirect(url_for('admin.training'))

@admin_bp.route('/training/delete/<int:rid>', methods=['POST'])
@admin_required
def delete_training(rid):
    from app.models import TrainingResource
    r = TrainingResource.query.get_or_404(rid)
    db.session.delete(r); db.session.commit()
    flash('Resource deleted.','info')
    return redirect(url_for('admin.training'))

# ── SALES TARGETS (Admin sets) ────────────────────────────────────
@admin_bp.route('/targets')
@admin_required
def sales_targets():
    from app.models import SalesTarget, MonthlySalary
    from datetime import date
    today     = date.today()
    employees = Employee.query.join(User).all()
    targets   = {t.employee_id: t for t in SalesTarget.query.filter_by(
        month=today.month, year=today.year).all()}
    salaries  = {s.employee_id: s for s in MonthlySalary.query.filter_by(
        month=today.month, year=today.year).all()}
    return render_template('admin/sales_targets.html',
        employees=employees, targets=targets, salaries=salaries,
        month=today.strftime('%B %Y'))

@admin_bp.route('/targets/set', methods=['POST'])
@admin_required
def set_target():
    from app.models import SalesTarget
    from datetime import date
    today   = date.today()
    emp_id  = request.form.get('employee_id', type=int)
    amount  = request.form.get('target_amount', type=float) or 0
    target  = SalesTarget.query.filter_by(
        employee_id=emp_id, month=today.month, year=today.year).first()
    if target:
        target.target_amount = amount
    else:
        db.session.add(SalesTarget(employee_id=emp_id, month=today.month,
            year=today.year, target_amount=amount))
    db.session.commit()
    flash('Target set!','success')
    return redirect(url_for('admin.sales_targets'))


# ── ADMIN: RESET ANY USER'S PASSWORD ─────────────────────────────
@admin_bp.route('/users')
@admin_required
def users():
    all_users = User.query.order_by(User.role, User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)

@admin_bp.route('/users/reset-password/<int:uid>', methods=['POST'])
@admin_required
def admin_reset_password(uid):
    from werkzeug.security import generate_password_hash
    user   = User.query.get_or_404(uid)
    new_pw = request.form.get('new_password','').strip()
    if len(new_pw) < 6:
        flash('Password must be at least 6 characters.','danger')
        return redirect(url_for('admin.users'))
    user.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    flash(f'Password for {user.full_name} updated!','success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/toggle/<int:uid>', methods=['POST'])
@admin_required
def toggle_user(uid):
    user = User.query.get_or_404(uid)
    if user.id == current_user.id:
        return 'Cannot deactivate yourself', 400
    user.is_active_account = not user.is_active_account
    db.session.commit()
    return {'active': user.is_active_account}

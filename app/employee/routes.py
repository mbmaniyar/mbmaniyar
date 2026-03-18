
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import (db, User, Employee, Shift, Task, MonthlySalary, Order,
                        OrderItem, LeaveRequest, ClockRecord, Notice,
                        TrainingResource, SalesTarget, Product, Category, ProductVariant)
from datetime import date, datetime, timedelta
import calendar

employee_bp = Blueprint('employee', __name__)

def employee_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('employee','admin'):
            flash('Employee access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def get_emp():
    return Employee.query.filter_by(user_id=current_user.id).first()

# ── DASHBOARD ─────────────────────────────────────────────────────
@employee_bp.route('/')
@employee_required
def dashboard():
    emp   = get_emp()
    if not emp:
        flash('Employee profile not found. Contact admin.','warning')
        return redirect(url_for('auth.logout'))
    today  = date.today()
    month  = today.month
    year   = today.year

    todays_shift   = Shift.query.filter_by(employee_id=emp.id, date=today).first()
    pending_tasks  = Task.query.filter_by(employee_id=emp.id, is_completed=False).order_by(Task.due_date).limit(5).all()
    salary         = MonthlySalary.query.filter_by(employee_id=emp.id, month=month, year=year).first()
    clock_today    = ClockRecord.query.filter_by(employee_id=emp.id, date=today).first()
    notices        = Notice.query.order_by(Notice.created_at.desc()).limit(5).all()

    # Shifts this month
    shifts_month = Shift.query.filter_by(employee_id=emp.id).filter(
        db.extract('month', Shift.date)==month,
        db.extract('year',  Shift.date)==year).all()
    completed_shifts = sum(1 for s in shifts_month if s.status=='completed')

    # Sales this month (from POS orders where employee code matched)
    # We approximate via commission records
    sales_this_month = float(salary.commission_earned or 0) / float(emp.commission_rate or 0.01) if (salary and emp.commission_rate) else 0

    # Sales target
    target = SalesTarget.query.filter_by(employee_id=emp.id, month=month, year=year).first()
    target_amount = target.target_amount if target else 0

    # Leaderboard — top 5 by commission this month
    leaderboard = db.session.query(Employee, MonthlySalary).join(
        MonthlySalary, (Employee.id==MonthlySalary.employee_id) &
        (MonthlySalary.month==month) & (MonthlySalary.year==year)
    ).order_by(MonthlySalary.commission_earned.desc()).limit(5).all()

    return render_template('employee/dashboard.html',
        emp=emp, today=today, todays_shift=todays_shift,
        pending_tasks=pending_tasks, salary=salary,
        clock_today=clock_today, notices=notices,
        completed_shifts=completed_shifts, total_shifts=len(shifts_month),
        sales_this_month=sales_this_month, target_amount=target_amount,
        leaderboard=leaderboard)

# ── CLOCK IN/OUT ──────────────────────────────────────────────────
@employee_bp.route('/clock', methods=['POST'])
@employee_required
def clock():
    emp   = get_emp()
    today = date.today()
    now   = datetime.utcnow()
    rec   = ClockRecord.query.filter_by(employee_id=emp.id, date=today).first()
    if not rec:
        rec = ClockRecord(employee_id=emp.id, date=today, clock_in=now)
        db.session.add(rec)
        db.session.commit()
        return jsonify({'action':'clocked_in','time': now.strftime('%I:%M %p')})
    elif rec.clock_in and not rec.clock_out:
        rec.clock_out = now
        db.session.commit()
        hours = rec.hours_worked
        return jsonify({'action':'clocked_out','time': now.strftime('%I:%M %p'),'hours': hours})
    else:
        return jsonify({'action':'already_done','msg':'Already clocked out today.'})

# ── PROFILE ───────────────────────────────────────────────────────
@employee_bp.route('/profile')
@employee_required
def profile():
    emp = get_emp()
    return render_template('employee/profile.html', emp=emp)

@employee_bp.route('/profile/update', methods=['POST'])
@employee_required
def update_profile():
    emp = get_emp()
    current_user.phone = request.form.get('phone','').strip()
    emp.emergency_contact = request.form.get('emergency_contact','').strip()
    emp.emergency_phone   = request.form.get('emergency_phone','').strip()
    db.session.commit()
    flash('Profile updated!','success')
    return redirect(url_for('employee.profile'))

# ── SCHEDULE ──────────────────────────────────────────────────────
@employee_bp.route('/schedule')
@employee_required
def schedule():
    emp   = get_emp()
    today = date.today()
    month = int(request.args.get('month', today.month))
    year  = int(request.args.get('year',  today.year))
    shifts = Shift.query.filter_by(employee_id=emp.id).filter(
        db.extract('month', Shift.date)==month,
        db.extract('year',  Shift.date)==year).order_by(Shift.date).all()
    cal        = calendar.monthcalendar(year, month)
    shift_map  = {s.date.day: s for s in shifts}
    month_name = calendar.month_name[month]
    prev_month = 12 if month==1 else month-1
    prev_year  = year-1 if month==1 else year
    next_month = 1 if month==12 else month+1
    next_year  = year+1 if month==12 else year
    return render_template('employee/schedule.html',
        emp=emp, today=today, cal=cal, shift_map=shift_map,
        month=month, year=year, month_name=month_name,
        prev_month=prev_month, prev_year=prev_year,
        next_month=next_month, next_year=next_year, shifts=shifts)

# ── SALARY & COMMISSIONS ──────────────────────────────────────────
@employee_bp.route('/salary')
@employee_required
def salary():
    emp     = get_emp()
    today   = date.today()
    records = MonthlySalary.query.filter_by(employee_id=emp.id).order_by(
        MonthlySalary.year.desc(), MonthlySalary.month.desc()).all()
    current_sal = MonthlySalary.query.filter_by(
        employee_id=emp.id, month=today.month, year=today.year).first()

    # Commission breakdown from orders this month
    # Get all POS orders processed this month that match employee code
    month_start = date(today.year, today.month, 1)
    pos_orders  = Order.query.filter(
        Order.order_type=='pos',
        Order.created_at >= month_start,
        Order.payment_status=='paid'
    ).all()

    commission_log = []
    for o in pos_orders:
        note = o.customer_notes or ''
        if emp.employee_code and emp.employee_code in note:
            commission_log.append({
                'date'      : o.created_at.strftime('%d %b'),
                'order'     : o.order_number,
                'amount'    : float(o.total_amount),
                'commission': round(float(o.total_amount) * float(emp.commission_rate or 0), 2),
            })

    return render_template('employee/salary.html',
        emp=emp, records=records, current_sal=current_sal,
        today=today, commission_log=commission_log)

# ── TASKS ─────────────────────────────────────────────────────────
@employee_bp.route('/tasks')
@employee_required
def tasks():
    emp   = get_emp()
    today = date.today()
    all_tasks = Task.query.filter_by(employee_id=emp.id).order_by(
        Task.is_completed, Task.due_date).all()
    return render_template('employee/tasks.html', emp=emp, tasks=all_tasks, today=today)

@employee_bp.route('/tasks/toggle/<int:tid>', methods=['POST'])
@employee_required
def toggle_task(tid):
    task = Task.query.get_or_404(tid)
    emp  = get_emp()
    if task.employee_id != emp.id:
        return jsonify({'error':'Forbidden'}),403
    task.is_completed = not task.is_completed
    task.completed_at = datetime.utcnow() if task.is_completed else None
    db.session.commit()
    return jsonify({'ok':True,'done':task.is_completed})

# ── LEAVE REQUESTS ────────────────────────────────────────────────
@employee_bp.route('/leave')
@employee_required
def leave():
    emp      = get_emp()
    today    = date.today()
    requests = LeaveRequest.query.filter_by(employee_id=emp.id).order_by(
        LeaveRequest.created_at.desc()).all()
    # Count approved leaves this year
    approved = [r for r in requests if r.status=='approved' and r.start_date.year==today.year]
    used_casual = sum(r.days for r in approved if r.leave_type=='casual')
    used_sick   = sum(r.days for r in approved if r.leave_type=='sick')
    return render_template('employee/leave.html',
        emp=emp, requests=requests, today=today,
        used_casual=used_casual, used_sick=used_sick,
        balance_casual=max(0,12-used_casual),
        balance_sick=max(0,7-used_sick))

@employee_bp.route('/leave/apply', methods=['POST'])
@employee_required
def apply_leave():
    emp        = get_emp()
    leave_type = request.form.get('leave_type','casual')
    start_str  = request.form.get('start_date','')
    end_str    = request.form.get('end_date','')
    reason     = request.form.get('reason','').strip()
    if start_str and end_str:
        start = datetime.strptime(start_str,'%Y-%m-%d').date()
        end   = datetime.strptime(end_str,'%Y-%m-%d').date()
        if end >= start:
            db.session.add(LeaveRequest(employee_id=emp.id,
                leave_type=leave_type, start_date=start,
                end_date=end, reason=reason))
            db.session.commit()
            flash('Leave request submitted!','success')
        else:
            flash('End date must be after start date.','danger')
    return redirect(url_for('employee.leave'))

# ── NOTICE BOARD ──────────────────────────────────────────────────
@employee_bp.route('/notices')
@employee_required
def notices():
    emp     = get_emp()
    notices = Notice.query.order_by(Notice.created_at.desc()).all()
    return render_template('employee/notices.html', emp=emp, notices=notices)

# ── TRAINING HUB ──────────────────────────────────────────────────
@employee_bp.route('/training')
@employee_required
def training():
    emp       = get_emp()
    category  = request.args.get('cat','All')
    resources = TrainingResource.query
    if category != 'All':
        resources = resources.filter_by(category=category)
    resources = resources.order_by(TrainingResource.created_at.desc()).all()
    categories = db.session.query(TrainingResource.category).distinct().all()
    categories = ['All'] + [c[0] for c in categories]
    return render_template('employee/training.html',
        emp=emp, resources=resources, categories=categories, active_cat=category)

@employee_bp.route('/training/<int:rid>')
@employee_required
def training_detail(rid):
    emp      = get_emp()
    resource = TrainingResource.query.get_or_404(rid)
    return render_template('employee/training_detail.html', emp=emp, resource=resource)


# ── POS BILLING ─────────────────────────────────────────────────────
@employee_bp.route('/pos')
@employee_required
def pos_billing():
    """Unified POS billing screen with customer lookup"""
    emp = get_emp()
    if not emp:
        flash('Employee profile not found. Contact admin.', 'warning')
        return redirect(url_for('auth.logout'))
    
    products = Product.query.filter_by(is_active=True).all()
    categories = Category.query.all()
    employees = Employee.query.join(User).filter(User.is_active_account == True).all()
    
    return render_template('shared/pos_unified.html',
        products=products, categories=categories, employees=employees, emp=emp)


@employee_bp.route('/api/products')
@employee_required
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


@employee_bp.route('/api/categories')
@employee_required
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


@employee_bp.route('/api/pos/complete-sale', methods=['POST'])
@employee_required
def complete_pos_sale():
    """Complete a POS sale"""
    try:
        emp = get_emp()
        data = request.get_json()
        
        cart_items = data.get('cart_items', [])
        customer_id = data.get('customer_id')
        total_amount = data.get('total_amount')
        
        if not cart_items:
            return jsonify({'success': False, 'error': 'Cart is empty'}), 400
        
        # Generate order number
        order_number = f"POS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create POS order
        order = Order(
            order_number=order_number,
            user_id=customer_id or None,  # None for walk-in customers
            order_type='pos',
            status='completed',
            subtotal=data.get('subtotal', 0),
            tax_amount=data.get('tax', 0),
            total_amount=total_amount,
            payment_method='cash',
            payment_status='paid',
            processed_by_id=emp.id,
            customer_notes=f"Employee code: {emp.employee_code}" if emp.employee_code else None
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

#!/usr/bin/env python3
"""
Step 5 — Complete Employee Portal
Run: python3 build_step5_part1.py  (adds models + routes)
Then: python3 build_step5_part2.py (adds templates)
"""
import os

BASE = os.path.expanduser("~/Desktop/mbmaniyar")

def w(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ {path}")

def append_if_missing(path, marker, content):
    with open(path, 'r') as f:
        existing = f.read()
    if marker not in existing:
        with open(path, 'a') as f:
            f.write(content)
        print(f"  ✅ Appended to {os.path.basename(path)}")
    else:
        print(f"  ⏭️  Already exists in {os.path.basename(path)}")

# ══════════════════════════════════════════════════════════════════
# 1. PATCH models.py — add LeaveRequest, Notice, TrainingResource
# ══════════════════════════════════════════════════════════════════
models_patch = '''

# ── LEAVE REQUESTS ────────────────────────────────────────────────
class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    id            = db.Column(db.Integer, primary_key=True)
    employee_id   = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type    = db.Column(db.String(30), default='casual')   # casual / sick / earned
    start_date    = db.Column(db.Date, nullable=False)
    end_date      = db.Column(db.Date, nullable=False)
    reason        = db.Column(db.Text)
    status        = db.Column(db.String(20), default='pending')  # pending/approved/rejected
    admin_note    = db.Column(db.Text)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    employee      = db.relationship('Employee', backref='leave_requests')

    @property
    def days(self):
        return (self.end_date - self.start_date).days + 1

# ── CLOCK IN/OUT ──────────────────────────────────────────────────
class ClockRecord(db.Model):
    __tablename__ = 'clock_records'
    id          = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date        = db.Column(db.Date, default=date.today)
    clock_in    = db.Column(db.DateTime)
    clock_out   = db.Column(db.DateTime)
    employee    = db.relationship('Employee', backref='clock_records')

    @property
    def hours_worked(self):
        if self.clock_in and self.clock_out:
            delta = self.clock_out - self.clock_in
            return round(delta.total_seconds() / 3600, 2)
        return None

# ── NOTICE BOARD ──────────────────────────────────────────────────
class Notice(db.Model):
    __tablename__ = 'notices'
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    priority   = db.Column(db.String(20), default='normal')  # normal/important/urgent
    posted_by  = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    author     = db.relationship('User', foreign_keys=[posted_by])

# ── TRAINING RESOURCES ────────────────────────────────────────────
class TrainingResource(db.Model):
    __tablename__ = 'training_resources'
    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    description  = db.Column(db.Text)
    resource_type = db.Column(db.String(20), default='guide')   # guide/video/policy
    content      = db.Column(db.Text)   # markdown text or URL
    category     = db.Column(db.String(60), default='General')
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

# ── SALES TARGET ──────────────────────────────────────────────────
class SalesTarget(db.Model):
    __tablename__ = 'sales_targets'
    id          = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    month       = db.Column(db.Integer)
    year        = db.Column(db.Integer)
    target_amount = db.Column(db.Float, default=0)
    employee    = db.relationship('Employee', backref='sales_targets')
'''

models_path = os.path.join(BASE, "app/models.py")
append_if_missing(models_path, "class LeaveRequest", models_patch)

# ══════════════════════════════════════════════════════════════════
# 2. FULL EMPLOYEE ROUTES
# ══════════════════════════════════════════════════════════════════
w("app/employee/routes.py", r"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import (db, User, Employee, Shift, Task, MonthlySalary, Order,
                        OrderItem, LeaveRequest, ClockRecord, Notice,
                        TrainingResource, SalesTarget)
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
""")

# ══════════════════════════════════════════════════════════════════
# 3. ADMIN ROUTES for notices, leave approval, targets, training
# ══════════════════════════════════════════════════════════════════
admin_additions = '''

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
'''

admin_routes_path = os.path.join(BASE, "app/admin/routes.py")
append_if_missing(admin_routes_path, "def notices(", admin_additions)

# ══════════════════════════════════════════════════════════════════
# 4. Patch admin sidebar with new links
# ══════════════════════════════════════════════════════════════════
base_admin_path = os.path.join(BASE, "app/templates/admin/base_admin.html")
with open(base_admin_path, 'r') as f:
    base = f.read()

new_nav = """    <a href="{{ url_for('admin.notices') }}"
       class="nav-item {% if request.endpoint=='admin.notices' %}active{% endif %}">
      <i class="bi bi-megaphone"></i> Notice Board
    </a>
    <a href="{{ url_for('admin.leave_requests') }}"
       class="nav-item {% if request.endpoint=='admin.leave_requests' %}active{% endif %}">
      <i class="bi bi-calendar-x"></i> Leave Requests
    </a>
    <a href="{{ url_for('admin.sales_targets') }}"
       class="nav-item {% if request.endpoint=='admin.sales_targets' %}active{% endif %}">
      <i class="bi bi-bullseye"></i> Sales Targets
    </a>
    <a href="{{ url_for('admin.training') }}"
       class="nav-item {% if request.endpoint=='admin.training' %}active{% endif %}">
      <i class="bi bi-book"></i> Training Hub
    </a>"""

if 'admin.notices' not in base:
    base = base.replace(
        '<div class="nav-section-label">Store</div>',
        new_nav + '\n    <div class="nav-section-label">Store</div>'
    )
    with open(base_admin_path, 'w') as f:
        f.write(base)
    print("  ✅ Admin sidebar updated")

# ══════════════════════════════════════════════════════════════════
# 5. Patch models.py — add emergency_contact fields to Employee if missing
# ══════════════════════════════════════════════════════════════════
with open(os.path.join(BASE, "app/models.py"), 'r') as f:
    models_content = f.read()

if 'emergency_contact' not in models_content:
    models_content = models_content.replace(
        "commission_rate    = db.Column(db.Float, default=0.0)",
        "commission_rate    = db.Column(db.Float, default=0.0)\n    emergency_contact  = db.Column(db.String(100))\n    emergency_phone    = db.Column(db.String(20))"
    )
    with open(os.path.join(BASE, "app/models.py"), 'w') as f:
        f.write(models_content)
    print("  ✅ Emergency contact fields added to Employee model")

# ══════════════════════════════════════════════════════════════════
# 6. Seed some sample notices and training resources
# ══════════════════════════════════════════════════════════════════
seed_script = '''
import sys
sys.path.insert(0, ".")
from app import create_app
from app.models import db, Notice, TrainingResource, User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(role="admin").first()
    
    if Notice.query.count() == 0:
        notices = [
            Notice(title="Welcome to the New Staff Portal!",
                   body="We have launched our new digital staff portal. You can view your shifts, salary, and tasks all in one place. Please explore and let the manager know if you have any questions.",
                   priority="important", posted_by=admin.id if admin else None),
            Notice(title="Summer Sale — 20% off all Kurtas",
                   body="Starting this weekend, all Kurta items will have a 20% discount. Please ensure displays are updated and price tags are correct before Saturday morning.",
                   priority="urgent", posted_by=admin.id if admin else None),
            Notice(title="New Stock Arriving Thursday",
                   body="Raymond and k satish new collection arriving Thursday. All floor staff please clear the designated display area by Wednesday evening.",
                   priority="normal", posted_by=admin.id if admin else None),
        ]
        for n in notices:
            db.session.add(n)

    if TrainingResource.query.count() == 0:
        resources = [
            TrainingResource(
                title="How to Process a POS Sale",
                description="Step-by-step guide for billing customers at the counter.",
                resource_type="guide", category="POS & Billing",
                content="""## Processing a POS Sale

### Step 1: Open the POS
Go to Admin → POS Billing from the sidebar.

### Step 2: Find the Product
- Type the product name or SKU in the search bar
- OR tap the product tile on the left panel
- Select the correct SIZE from the popup

### Step 3: Review the Cart
- Check item name, size, quantity, and price
- Use +/- buttons to adjust quantity
- Apply discount if applicable (flat ₹ or percentage %)

### Step 4: Enter Your Employee Code
Type your employee code (e.g. MBM-001) in the field — this ensures you get credit for the sale commission!

### Step 5: Select Payment Method
Choose Cash, UPI, or Card.

### Step 6: Click CHARGE
Confirm the total and click the orange CHARGE button. The receipt will appear automatically.

### Step 7: Print Receipt
Click "Print Receipt" and hand it to the customer."""
            ),
            TrainingResource(
                title="How to Fold & Stack Shirts",
                description="Proper folding technique to keep the floor display neat.",
                resource_type="guide", category="Store Operations",
                content="""## Shirt Folding Guide

### Formal Shirts
1. Lay flat, buttons facing down
2. Fold one sleeve diagonally across the back
3. Fold the other sleeve the same way
4. Fold the bottom third up
5. Fold again so the collar is on top

### T-Shirts
1. Lay flat, design facing down
2. Fold left side (with sleeve) to the center
3. Fold right side the same way
4. Fold bottom half up to the collar

### Display Tips
- All sizes in a stack: XS at top, XXL at bottom
- Face the collar outward on shelves
- Keep folds tight and even
- Check and refold every 2 hours during busy periods"""
            ),
            TrainingResource(
                title="How to Handle Customer Returns",
                description="Policy and procedure for processing returns and exchanges.",
                resource_type="policy", category="Customer Service",
                content="""## Return & Exchange Policy

### What We Accept
- Items returned within **7 days** of purchase
- Original receipt must be present
- Item must be **unworn, unwashed, with all tags attached**

### What We DO NOT Accept
- Items without receipt
- Items that have been worn/washed
- Sale items (20%+ discount) — exchange only

### Return Process
1. Verify receipt and check item condition
2. Call the manager if unsure — **do not process without approval**
3. For cash returns: manager must authorize and give cash from the till
4. For exchange: find the replacement item and process as new sale at ₹0

### Important
Always be polite and empathetic. If a customer is upset, stay calm and say: *"Let me check with my manager to make sure we give you the best solution."*"""
            ),
            TrainingResource(
                title="New Brand: Raymond Collection Guide",
                description="Overview of the new Raymond premium collection we now stock.",
                resource_type="guide", category="Product Knowledge",
                content="""## Raymond Collection — Staff Guide

### About the Brand
Raymond is India's largest integrated manufacturer of worsted suiting fabric. Premium positioning — target customers are professionals aged 30-55.

### Key Selling Points
- "The Complete Man" brand identity
- Superior wool-blend fabric
- Machine washable options available
- 2-year fabric quality guarantee

### Products We Stock
| Item | Price Range | Key Feature |
|------|------------|-------------|
| Wool Trousers | ₹1,899–₹2,499 | Wrinkle-resistant |
| Formal Shirts | ₹1,299–₹1,799 | Stain-guard treated |
| Suit Fabric | ₹2,500/metre | Custom tailoring |

### How to Pitch
"Raymond fabric is crafted for the modern professional. It looks sharp all day without ironing, and the quality will last you years — it's an investment piece."
"""
            ),
        ]
        for r in resources:
            db.session.add(r)
    
    db.session.commit()
    print("✅ Sample notices and training resources seeded!")
'''

w("seed_step5.py", seed_script)

print()
print("="*55)
print("  ✅ Part 1 complete!")
print("  Now run: python3 build_step5_part2.py")
print("="*55)

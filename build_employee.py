#!/usr/bin/env python3
"""
Employee Portal Builder — M B MANIYAR
Run: python3 build_employee.py
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
# 1. EMPLOYEE ROUTES
# ═══════════════════════════════════════════════════════════════
w("app/employee/routes.py", r"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import db, User, Employee, Shift, Task, MonthlySalary, Order
from datetime import date, datetime, timedelta
import calendar

employee_bp = Blueprint('employee', __name__)

def employee_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('employee', 'admin'):
            flash('Employee access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def get_emp():
    """Get the Employee record for the current user."""
    return Employee.query.filter_by(user_id=current_user.id).first()

# ── DASHBOARD ────────────────────────────────────────────────────────────────
@employee_bp.route('/')
@employee_required
def dashboard():
    emp = get_emp()
    if not emp:
        flash('Employee profile not found. Contact admin.', 'warning')
        return redirect(url_for('auth.logout'))

    today      = date.today()
    month      = today.month
    year       = today.year

    # Shifts this month
    shifts_this_month = Shift.query.filter_by(employee_id=emp.id).filter(
        db.extract('month', Shift.date) == month,
        db.extract('year',  Shift.date) == year
    ).order_by(Shift.date).all()

    # Today's shift
    todays_shift = Shift.query.filter_by(
        employee_id=emp.id, date=today).first()

    # Pending tasks
    pending_tasks = Task.query.filter_by(
        employee_id=emp.id, is_completed=False
    ).order_by(Task.due_date).limit(5).all()

    # This month's salary
    salary = MonthlySalary.query.filter_by(
        employee_id=emp.id, month=month, year=year).first()

    # Stats
    completed_shifts = sum(1 for s in shifts_this_month if s.status == 'completed')
    total_shifts     = len(shifts_this_month)

    return render_template('employee/dashboard.html',
        emp=emp, today=today,
        todays_shift=todays_shift,
        shifts_this_month=shifts_this_month,
        pending_tasks=pending_tasks,
        salary=salary,
        completed_shifts=completed_shifts,
        total_shifts=total_shifts,
    )

# ── SCHEDULE ─────────────────────────────────────────────────────────────────
@employee_bp.route('/schedule')
@employee_required
def schedule():
    emp   = get_emp()
    today = date.today()
    # Get month from query param or default to current
    month = int(request.args.get('month', today.month))
    year  = int(request.args.get('year',  today.year))

    # All shifts for this month
    shifts = Shift.query.filter_by(employee_id=emp.id).filter(
        db.extract('month', Shift.date) == month,
        db.extract('year',  Shift.date) == year
    ).order_by(Shift.date).all()

    # Build calendar grid
    cal     = calendar.monthcalendar(year, month)
    shift_map = {s.date.day: s for s in shifts}
    month_name = calendar.month_name[month]

    # Prev / next month
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    return render_template('employee/schedule.html',
        emp=emp, today=today, cal=cal, shift_map=shift_map,
        month=month, year=year, month_name=month_name,
        prev_month=prev_month, prev_year=prev_year,
        next_month=next_month, next_year=next_year,
        shifts=shifts,
    )

# ── SALARY ───────────────────────────────────────────────────────────────────
@employee_bp.route('/salary')
@employee_required
def salary():
    emp = get_emp()
    # All salary records newest first
    records = MonthlySalary.query.filter_by(
        employee_id=emp.id
    ).order_by(MonthlySalary.year.desc(), MonthlySalary.month.desc()).all()

    today        = date.today()
    current_sal  = MonthlySalary.query.filter_by(
        employee_id=emp.id, month=today.month, year=today.year).first()

    return render_template('employee/salary.html',
        emp=emp, records=records, current_sal=current_sal,
        today=today,
    )

# ── TASKS ────────────────────────────────────────────────────────────────────
@employee_bp.route('/tasks')
@employee_required
def tasks():
    emp   = get_emp()
    today = date.today()
    all_tasks = Task.query.filter_by(employee_id=emp.id).order_by(
        Task.is_completed, Task.due_date).all()
    return render_template('employee/tasks.html',
        emp=emp, tasks=all_tasks, today=today)

@employee_bp.route('/tasks/complete/<int:tid>', methods=['POST'])
@employee_required
def complete_task(tid):
    task = Task.query.get_or_404(tid)
    emp  = get_emp()
    if task.employee_id != emp.id:
        return jsonify({'error': 'Forbidden'}), 403
    task.is_completed = True
    task.completed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'ok': True})

@employee_bp.route('/tasks/uncomplete/<int:tid>', methods=['POST'])
@employee_required
def uncomplete_task(tid):
    task = Task.query.get_or_404(tid)
    emp  = get_emp()
    if task.employee_id != emp.id:
        return jsonify({'error': 'Forbidden'}), 403
    task.is_completed = False
    task.completed_at = None
    db.session.commit()
    return jsonify({'ok': True})
""")

# ═══════════════════════════════════════════════════════════════
# 2. EMPLOYEE BASE TEMPLATE
# ═══════════════════════════════════════════════════════════════
w("app/templates/employee/base_employee.html", r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{% block title %}Staff Portal{% endblock %} | MBM</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#F0F4FF;--sidebar:#1E2A4A;--sidebar2:#162040;
  --accent:#4F8EF7;--gold:#F5A623;--green:#27AE60;
  --red:#E74C3C;--purple:#8B5CF6;
  --text:#1A2340;--muted:#7B8BAD;--border:#E2E8F5;
  --card:#FFFFFF;
  --ff:'Outfit',sans-serif;--ff-mono:'DM Mono',monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--ff);background:var(--bg);color:var(--text);min-height:100vh;display:flex}

/* ── SIDEBAR ── */
.emp-sidebar{
  width:230px;min-height:100vh;background:var(--sidebar);
  display:flex;flex-direction:column;flex-shrink:0;
  position:fixed;left:0;top:0;bottom:0;z-index:200;
}
.sidebar-top{
  padding:1.4rem 1.2rem 1rem;
  border-bottom:1px solid rgba(255,255,255,.07);
}
.emp-logo{display:flex;align-items:center;gap:.75rem;margin-bottom:1rem}
.emp-logo-icon{
  width:38px;height:38px;border-radius:10px;
  background:linear-gradient(135deg,var(--accent),#2563EB);
  display:flex;align-items:center;justify-content:center;
  font-size:1rem;font-weight:800;color:#fff;
}
.emp-logo-text{font-size:.95rem;font-weight:700;color:#fff;line-height:1.2}
.emp-logo-text small{font-size:.62rem;color:rgba(255,255,255,.4);font-weight:400;letter-spacing:1px;display:block}

/* Profile card in sidebar */
.emp-profile-card{
  background:rgba(255,255,255,.06);border-radius:12px;
  padding:.8rem;display:flex;align-items:center;gap:.7rem;
}
.emp-avatar{
  width:40px;height:40px;border-radius:50%;
  background:linear-gradient(135deg,var(--gold),#E8903A);
  display:flex;align-items:center;justify-content:center;
  font-size:1.1rem;font-weight:800;color:#fff;flex-shrink:0;
}
.emp-profile-name{font-size:.83rem;font-weight:700;color:#fff;line-height:1.2}
.emp-profile-role{font-size:.68rem;color:rgba(255,255,255,.4);margin-top:.1rem}
.emp-code-badge{
  display:inline-block;margin-top:.3rem;
  font-size:.62rem;font-family:var(--ff-mono);
  background:rgba(79,142,247,.2);color:var(--accent);
  border-radius:4px;padding:.1rem .45rem;
}

/* Nav */
.emp-nav{padding:.8rem 0;flex:1}
.nav-section-lbl{
  font-size:.6rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
  color:rgba(255,255,255,.25);padding:.7rem 1.2rem .3rem;
}
.emp-nav-item{
  display:flex;align-items:center;gap:.7rem;
  padding:.6rem 1.2rem;margin:.1rem .7rem;
  border-radius:8px;color:rgba(255,255,255,.5);
  font-size:.875rem;font-weight:500;text-decoration:none;
  transition:all .2s;
}
.emp-nav-item:hover{background:rgba(255,255,255,.07);color:#fff}
.emp-nav-item.active{background:rgba(79,142,247,.2);color:var(--accent);border:1px solid rgba(79,142,247,.2)}
.emp-nav-item i{font-size:.95rem;width:18px;text-align:center}

.emp-sidebar-bottom{
  padding:1rem;border-top:1px solid rgba(255,255,255,.07);
}
.logout-btn{
  display:flex;align-items:center;gap:.6rem;
  color:rgba(255,255,255,.35);font-size:.83rem;text-decoration:none;
  padding:.5rem .7rem;border-radius:8px;transition:all .2s;
}
.logout-btn:hover{background:rgba(231,76,60,.1);color:#E74C3C}

/* ── MAIN ── */
.emp-main{margin-left:230px;flex:1;min-height:100vh;display:flex;flex-direction:column}
.emp-topbar{
  background:#fff;border-bottom:1px solid var(--border);
  padding:.9rem 1.8rem;display:flex;align-items:center;justify-content:space-between;
  position:sticky;top:0;z-index:100;
}
.topbar-title{font-size:1.1rem;font-weight:700;color:var(--text)}
.topbar-date{font-size:.82rem;color:var(--muted)}

.emp-body{padding:1.8rem;flex:1}

/* ── CARDS ── */
.e-card{
  background:var(--card);border-radius:16px;
  border:1px solid var(--border);
  box-shadow:0 2px 12px rgba(30,42,74,.06);
}
.e-card-head{
  padding:1rem 1.4rem;border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;
}
.e-card-head h5{font-size:.95rem;font-weight:700;color:var(--text);margin:0}
.e-card-body{padding:1.4rem}

/* ── STAT CARDS ── */
.e-stat{
  background:var(--card);border-radius:14px;padding:1.2rem 1.4rem;
  border:1px solid var(--border);position:relative;overflow:hidden;
  transition:transform .2s,box-shadow .2s;
}
.e-stat:hover{transform:translateY(-3px);box-shadow:0 8px 24px rgba(30,42,74,.1)}
.e-stat-label{font-size:.7rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);margin-bottom:.5rem}
.e-stat-val{font-size:1.8rem;font-weight:800;line-height:1;color:var(--text)}
.e-stat-sub{font-size:.75rem;color:var(--muted);margin-top:.4rem}
.e-stat-icon{position:absolute;top:1rem;right:1.2rem;font-size:1.6rem;opacity:.12}

/* ── FLASH ── */
.flash-mbm{border-radius:10px;padding:.7rem 1rem;margin-bottom:.8rem;font-size:.875rem;
  display:flex;align-items:center;gap:.5rem;border:1px solid transparent}
.flash-success{background:#EBF9F1;border-color:#A8E6C3;color:#166534}
.flash-danger{background:#FEF0EF;border-color:#FBBBB7;color:#991B1B}
.flash-warning{background:#FFFBEB;border-color:#FDE68A;color:#92400E}
.flash-info{background:#EFF6FF;border-color:#BFDBFE;color:#1E40AF}

/* ── BADGES ── */
.badge-emp{display:inline-flex;align-items:center;gap:.25rem;border-radius:50px;padding:.25rem .7rem;font-size:.7rem;font-weight:600}
.b-green{background:#EBF9F1;color:#166534}
.b-blue{background:#EFF6FF;color:#1E40AF}
.b-yellow{background:#FFFBEB;color:#92400E}
.b-red{background:#FEF0EF;color:#991B1B}
.b-gray{background:#F1F5F9;color:#64748B}
.b-purple{background:#F3F0FF;color:#5B21B6}

/* Mobile */
@media(max-width:768px){
  .emp-sidebar{transform:translateX(-100%)}
  .emp-main{margin-left:0}
}
</style>
{% block extra_css %}{% endblock %}
</head>
<body>

<nav class="emp-sidebar">
  <div class="sidebar-top">
    <div class="emp-logo">
      <div class="emp-logo-icon">M</div>
      <div class="emp-logo-text">MBM Staff<small>Employee Portal</small></div>
    </div>
    {% if current_user.employee_profile %}
    {% set emp = current_user.employee_profile %}
    <div class="emp-profile-card">
      <div class="emp-avatar">{{ current_user.full_name[0] }}</div>
      <div>
        <div class="emp-profile-name">{{ current_user.full_name }}</div>
        <div class="emp-profile-role">{{ emp.designation or 'Staff' }}</div>
        <span class="emp-code-badge">{{ emp.employee_code }}</span>
      </div>
    </div>
    {% endif %}
  </div>

  <div class="emp-nav">
    <div class="nav-section-lbl">My Portal</div>
    <a href="{{ url_for('employee.dashboard') }}"
       class="emp-nav-item {% if request.endpoint=='employee.dashboard' %}active{% endif %}">
      <i class="bi bi-house"></i> Dashboard
    </a>
    <a href="{{ url_for('employee.schedule') }}"
       class="emp-nav-item {% if request.endpoint=='employee.schedule' %}active{% endif %}">
      <i class="bi bi-calendar3"></i> My Schedule
    </a>
    <a href="{{ url_for('employee.salary') }}"
       class="emp-nav-item {% if request.endpoint=='employee.salary' %}active{% endif %}">
      <i class="bi bi-wallet2"></i> Salary & Commission
    </a>
    <a href="{{ url_for('employee.tasks') }}"
       class="emp-nav-item {% if request.endpoint=='employee.tasks' %}active{% endif %}">
      <i class="bi bi-check2-square"></i> My Tasks
    </a>
  </div>

  <div class="emp-sidebar-bottom">
    <a href="{{ url_for('auth.logout') }}" class="logout-btn">
      <i class="bi bi-box-arrow-left"></i> Sign Out
    </a>
  </div>
</nav>

<div class="emp-main">
  <div class="emp-topbar">
    <div class="topbar-title">{% block page_title %}Dashboard{% endblock %}</div>
    <div class="topbar-date">
      <i class="bi bi-calendar3 me-1"></i>
      {{ now().strftime('%A, %d %B %Y') }}
    </div>
  </div>

  <div class="emp-body">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}{% for cat, msg in messages %}
        <div class="flash-mbm flash-{{ cat }}">
          <i class="bi bi-info-circle"></i> {{ msg }}
        </div>
      {% endfor %}{% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
{% block extra_js %}{% endblock %}
</body>
</html>
""")

# ═══════════════════════════════════════════════════════════════
# 3. EMPLOYEE DASHBOARD
# ═══════════════════════════════════════════════════════════════
w("app/templates/employee/dashboard.html", r"""{% extends 'employee/base_employee.html' %}
{% block title %}My Dashboard{% endblock %}
{% block page_title %}My Dashboard{% endblock %}
{% block extra_css %}
<style>
@keyframes fadeUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
.e-stat{animation:fadeUp .4s ease both}
.e-stat:nth-child(1){animation-delay:.05s}
.e-stat:nth-child(2){animation-delay:.1s}
.e-stat:nth-child(3){animation-delay:.15s}
.e-stat:nth-child(4){animation-delay:.2s}

.shift-card{
  border-radius:16px;padding:1.4rem;
  background:linear-gradient(135deg,#1E2A4A,#2563EB);
  color:#fff;position:relative;overflow:hidden;margin-bottom:1.5rem;
}
.shift-card::before{
  content:'';position:absolute;top:-30px;right:-30px;
  width:120px;height:120px;border-radius:50%;
  background:rgba(255,255,255,.05);
}
.shift-time{font-size:2rem;font-weight:800;font-family:var(--ff-mono);margin:.4rem 0}
.shift-label{font-size:.72rem;text-transform:uppercase;letter-spacing:1.5px;opacity:.6}
.no-shift{text-align:center;padding:1.5rem;color:var(--muted)}

.task-item{
  display:flex;align-items:center;gap:.8rem;padding:.75rem 0;
  border-bottom:1px solid var(--border);
}
.task-item:last-child{border-bottom:none}
.task-check{
  width:22px;height:22px;border-radius:6px;border:2px solid var(--border);
  display:flex;align-items:center;justify-content:center;cursor:pointer;
  flex-shrink:0;transition:all .2s;
}
.task-check.done{background:var(--green);border-color:var(--green);color:#fff}
.task-info{flex:1;min-width:0}
.task-title{font-size:.88rem;font-weight:600;color:var(--text)}
.task-title.done{text-decoration:line-through;color:var(--muted)}
.task-due{font-size:.73rem;color:var(--muted);margin-top:.1rem}
.task-overdue{color:var(--red)}

.progress-ring-wrap{display:flex;align-items:center;gap:1rem;padding:.5rem 0}
.progress-bar-custom{height:8px;border-radius:50px;background:#E2E8F5;overflow:hidden;flex:1}
.progress-fill{height:100%;border-radius:50px;background:linear-gradient(90deg,var(--accent),var(--purple));transition:width .8s ease}
</style>
{% endblock %}

{% block content %}

<!-- Greeting -->
<div style="margin-bottom:1.5rem">
  <h2 style="font-size:1.5rem;font-weight:800;margin-bottom:.2rem">
    {% set hr = now().hour %}
    {% if hr < 12 %}Good Morning{% elif hr < 17 %}Good Afternoon{% else %}Good Evening{% endif %},
    {{ current_user.full_name.split()[0] }}! 👋
  </h2>
  <p style="color:var(--muted);font-size:.9rem">
    {{ emp.designation or 'Staff' }} · {{ emp.department or 'M B MANIYAR' }}
  </p>
</div>

<!-- Stats row -->
<div class="row g-3 mb-4">
  <div class="col-6 col-lg-3">
    <div class="e-stat">
      <div class="e-stat-label">Shifts This Month</div>
      <div class="e-stat-val" style="color:var(--accent)">{{ total_shifts }}</div>
      <div class="e-stat-sub">{{ completed_shifts }} completed</div>
      <i class="bi bi-calendar-check e-stat-icon" style="color:var(--accent)"></i>
    </div>
  </div>
  <div class="col-6 col-lg-3">
    <div class="e-stat">
      <div class="e-stat-label">Base Salary</div>
      <div class="e-stat-val" style="color:var(--green);font-size:1.4rem">
        ₹{{ "%.0f"|format(emp.base_salary or 0) }}
      </div>
      <div class="e-stat-sub">per month</div>
      <i class="bi bi-wallet2 e-stat-icon" style="color:var(--green)"></i>
    </div>
  </div>
  <div class="col-6 col-lg-3">
    <div class="e-stat">
      <div class="e-stat-label">Commission Rate</div>
      <div class="e-stat-val" style="color:var(--gold)">
        {{ "%.1f"|format((emp.commission_rate or 0)*100) }}%
      </div>
      <div class="e-stat-sub">of sales handled</div>
      <i class="bi bi-percent e-stat-icon" style="color:var(--gold)"></i>
    </div>
  </div>
  <div class="col-6 col-lg-3">
    <div class="e-stat">
      <div class="e-stat-label">Commission Earned</div>
      <div class="e-stat-val" style="color:var(--purple);font-size:1.4rem">
        ₹{{ "%.0f"|format(salary.commission_earned if salary else 0) }}
      </div>
      <div class="e-stat-sub">this month</div>
      <i class="bi bi-graph-up e-stat-icon" style="color:var(--purple)"></i>
    </div>
  </div>
</div>

<div class="row g-4">

  <!-- Left col -->
  <div class="col-lg-7">

    <!-- Today's shift -->
    {% if todays_shift %}
    <div class="shift-card mb-4">
      <div class="shift-label">Today's Shift</div>
      <div class="shift-time">
        {{ todays_shift.start_time.strftime('%I:%M %p') }} —
        {{ todays_shift.end_time.strftime('%I:%M %p') }}
      </div>
      <div style="display:flex;align-items:center;gap:1rem;margin-top:.5rem">
        <span style="font-size:.8rem;opacity:.7">
          <i class="bi bi-building me-1"></i>{{ emp.department or 'Main Floor' }}
        </span>
        <span style="font-size:.75rem;background:rgba(255,255,255,.15);padding:.2rem .7rem;border-radius:50px">
          {{ todays_shift.status|title }}
        </span>
      </div>
      {% if todays_shift.notes %}
      <div style="margin-top:.8rem;font-size:.8rem;opacity:.65;border-top:1px solid rgba(255,255,255,.1);padding-top:.6rem">
        📝 {{ todays_shift.notes }}
      </div>
      {% endif %}
    </div>
    {% else %}
    <div class="e-card mb-4">
      <div class="e-card-head"><h5>Today's Shift</h5></div>
      <div class="no-shift">
        <i class="bi bi-calendar-x" style="font-size:2rem;color:var(--muted);display:block;margin-bottom:.5rem"></i>
        No shift scheduled for today
      </div>
    </div>
    {% endif %}

    <!-- This month's schedule preview -->
    <div class="e-card">
      <div class="e-card-head">
        <h5><i class="bi bi-calendar3 me-2" style="color:var(--accent)"></i>This Month</h5>
        <a href="{{ url_for('employee.schedule') }}"
           style="font-size:.8rem;color:var(--accent);text-decoration:none">View Full →</a>
      </div>
      <div class="e-card-body" style="padding:1rem">

        <!-- Attendance progress -->
        <div style="margin-bottom:1rem">
          <div style="display:flex;justify-content:space-between;font-size:.78rem;color:var(--muted);margin-bottom:.4rem">
            <span>Attendance</span>
            <span>{{ completed_shifts }}/{{ total_shifts }} shifts</span>
          </div>
          <div class="progress-bar-custom">
            <div class="progress-fill"
                 style="width:{% if total_shifts > 0 %}{{ (completed_shifts/total_shifts*100)|int }}{% else %}0{% endif %}%">
            </div>
          </div>
        </div>

        <!-- Upcoming shifts -->
        {% set upcoming = shifts_this_month | selectattr('date', 'ge', today) | list %}
        {% if upcoming %}
          {% for s in upcoming[:5] %}
          <div style="display:flex;align-items:center;gap:.8rem;padding:.5rem 0;border-bottom:1px solid var(--border)">
            <div style="width:42px;height:42px;border-radius:10px;
                 background:{% if s.status=='completed' %}#EBF9F1{% elif s.date==today %}#EFF6FF{% else %}#F8FAFF{% endif %};
                 display:flex;flex-direction:column;align-items:center;justify-content:center;flex-shrink:0">
              <span style="font-size:.62rem;font-weight:700;color:var(--muted);text-transform:uppercase">
                {{ s.date.strftime('%a') }}
              </span>
              <span style="font-size:.95rem;font-weight:800;
                color:{% if s.date==today %}var(--accent){% else %}var(--text){% endif %}">
                {{ s.date.day }}
              </span>
            </div>
            <div style="flex:1">
              <div style="font-size:.85rem;font-weight:600">
                {{ s.start_time.strftime('%I:%M %p') }} – {{ s.end_time.strftime('%I:%M %p') }}
              </div>
              <div style="font-size:.73rem;color:var(--muted)">{{ emp.department or 'Main Floor' }}</div>
            </div>
            <span class="badge-emp {% if s.status=='completed' %}b-green{% elif s.status=='absent' %}b-red{% else %}b-blue{% endif %}">
              {{ s.status|title }}
            </span>
          </div>
          {% endfor %}
        {% else %}
          <div style="text-align:center;padding:1.5rem;color:var(--muted);font-size:.85rem">
            No upcoming shifts this month
          </div>
        {% endif %}
      </div>
    </div>
  </div>

  <!-- Right col -->
  <div class="col-lg-5">

    <!-- Salary card -->
    <div class="e-card mb-4">
      <div class="e-card-head">
        <h5><i class="bi bi-wallet2 me-2" style="color:var(--green)"></i>This Month's Salary</h5>
        <a href="{{ url_for('employee.salary') }}"
           style="font-size:.8rem;color:var(--accent);text-decoration:none">Details →</a>
      </div>
      <div class="e-card-body">
        {% if salary %}
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:.8rem;margin-bottom:1rem">
          {% for label, val, color in [
            ('Base Salary', salary.base_salary, 'var(--text)'),
            ('Commission', salary.commission_earned, 'var(--purple)'),
            ('Bonus', salary.bonus, 'var(--gold)'),
            ('Deductions', salary.deductions, 'var(--red)'),
          ] %}
          <div style="background:#F8FAFF;border-radius:10px;padding:.7rem .9rem">
            <div style="font-size:.68rem;text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin-bottom:.3rem">{{ label }}</div>
            <div style="font-size:1rem;font-weight:700;color:{{ color }}">₹{{ "%.0f"|format(val or 0) }}</div>
          </div>
          {% endfor %}
        </div>
        <div style="background:linear-gradient(135deg,var(--accent),var(--purple));border-radius:12px;padding:1rem;text-align:center">
          <div style="font-size:.72rem;color:rgba(255,255,255,.7);text-transform:uppercase;letter-spacing:1px">Net Salary</div>
          <div style="font-size:1.8rem;font-weight:800;color:#fff;font-family:var(--ff-mono)">
            ₹{{ "%.0f"|format(salary.net_salary or ((salary.base_salary or 0) + (salary.commission_earned or 0) + (salary.bonus or 0) - (salary.deductions or 0))) }}
          </div>
          <span style="font-size:.72rem;background:{% if salary.payment_status=='paid' %}rgba(46,204,113,.3){% else %}rgba(255,255,255,.15){% endif %};color:#fff;border-radius:50px;padding:.2rem .7rem">
            {{ salary.payment_status|title }}
          </span>
        </div>
        {% else %}
        <div style="text-align:center;padding:2rem;color:var(--muted)">
          <i class="bi bi-hourglass" style="font-size:2rem;display:block;margin-bottom:.5rem"></i>
          No salary record yet this month
        </div>
        {% endif %}
      </div>
    </div>

    <!-- Pending tasks -->
    <div class="e-card">
      <div class="e-card-head">
        <h5><i class="bi bi-check2-square me-2" style="color:var(--accent)"></i>Pending Tasks</h5>
        <a href="{{ url_for('employee.tasks') }}"
           style="font-size:.8rem;color:var(--accent);text-decoration:none">All →</a>
      </div>
      <div class="e-card-body" style="padding:.5rem 1.4rem">
        {% if pending_tasks %}
          {% for task in pending_tasks %}
          <div class="task-item" id="task-{{ task.id }}">
            <div class="task-check {% if task.is_completed %}done{% endif %}"
                 onclick="toggleTask({{ task.id }}, this)">
              {% if task.is_completed %}<i class="bi bi-check-lg" style="font-size:.7rem"></i>{% endif %}
            </div>
            <div class="task-info">
              <div class="task-title {% if task.is_completed %}done{% endif %}">{{ task.title }}</div>
              {% if task.due_date %}
              <div class="task-due {% if task.due_date < today and not task.is_completed %}task-overdue{% endif %}">
                Due: {{ task.due_date.strftime('%d %b') }}
                {% if task.due_date < today and not task.is_completed %}⚠ Overdue{% endif %}
              </div>
              {% endif %}
            </div>
          </div>
          {% endfor %}
        {% else %}
        <div style="text-align:center;padding:2rem;color:var(--muted)">
          <i class="bi bi-check-circle" style="font-size:2rem;color:var(--green);display:block;margin-bottom:.5rem"></i>
          All tasks completed! 🎉
        </div>
        {% endif %}
      </div>
    </div>

  </div>
</div>
{% endblock %}
{% block extra_js %}
<script>
async function toggleTask(id, el) {
  const done = el.classList.contains('done');
  const url  = done ? `/staff/tasks/uncomplete/${id}` : `/staff/tasks/complete/${id}`;
  const res  = await fetch(url, {method:'POST'});
  const data = await res.json();
  if (data.ok) {
    el.classList.toggle('done');
    const titleEl = el.nextElementSibling.querySelector('.task-title');
    titleEl.classList.toggle('done');
    if (!done) el.innerHTML = '<i class="bi bi-check-lg" style="font-size:.7rem"></i>';
    else el.innerHTML = '';
  }
}
</script>
{% endblock %}
""")

# ═══════════════════════════════════════════════════════════════
# 4. SCHEDULE PAGE
# ═══════════════════════════════════════════════════════════════
w("app/templates/employee/schedule.html", r"""{% extends 'employee/base_employee.html' %}
{% block title %}My Schedule{% endblock %}
{% block page_title %}My Schedule{% endblock %}
{% block extra_css %}
<style>
.cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:.4rem}
.cal-head{text-align:center;font-size:.7rem;font-weight:700;text-transform:uppercase;
  letter-spacing:1px;color:var(--muted);padding:.5rem 0}
.cal-cell{
  aspect-ratio:1;border-radius:10px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;font-size:.85rem;
  font-weight:600;position:relative;transition:all .2s;cursor:default;
  background:#F8FAFF;border:1px solid transparent;
}
.cal-cell.has-shift{background:#EFF6FF;border-color:#BFDBFE;cursor:pointer}
.cal-cell.has-shift:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(79,142,247,.2)}
.cal-cell.today{border-color:var(--accent);background:#EFF6FF;box-shadow:0 0 0 2px rgba(79,142,247,.3)}
.cal-cell.completed{background:#EBF9F1;border-color:#A8E6C3}
.cal-cell.absent{background:#FEF0EF;border-color:#FBBBB7}
.cal-cell.empty{background:transparent;border:none}
.cal-cell .day-num{font-size:.9rem;font-weight:700}
.cal-cell .shift-dot{width:6px;height:6px;border-radius:50%;margin-top:.15rem}
.cal-cell .shift-time-mini{font-size:.55rem;color:var(--muted);margin-top:.1rem;text-align:center;line-height:1.2}

.month-nav{display:flex;align-items:center;gap:1rem}
.month-nav-btn{
  width:34px;height:34px;border-radius:8px;border:1px solid var(--border);
  background:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;
  color:var(--text);transition:all .2s;text-decoration:none;
}
.month-nav-btn:hover{background:var(--accent);color:#fff;border-color:var(--accent)}
.month-title{font-size:1.1rem;font-weight:700;min-width:160px;text-align:center}

.shift-list-item{
  display:flex;align-items:center;gap:1rem;padding:.9rem;
  background:#F8FAFF;border-radius:10px;margin-bottom:.6rem;
  border-left:3px solid transparent;transition:all .2s;
}
.shift-list-item.completed{border-left-color:var(--green)}
.shift-list-item.absent{border-left-color:var(--red)}
.shift-list-item.scheduled{border-left-color:var(--accent)}
</style>
{% endblock %}

{% block content %}
<div class="row g-4">

  <div class="col-lg-8">
    <div class="e-card">
      <div class="e-card-head">
        <div class="month-nav">
          <a href="{{ url_for('employee.schedule', month=prev_month, year=prev_year) }}"
             class="month-nav-btn"><i class="bi bi-chevron-left"></i></a>
          <div class="month-title">{{ month_name }} {{ year }}</div>
          <a href="{{ url_for('employee.schedule', month=next_month, year=next_year) }}"
             class="month-nav-btn"><i class="bi bi-chevron-right"></i></a>
        </div>
        <span style="font-size:.8rem;color:var(--muted)">{{ shifts|length }} shifts scheduled</span>
      </div>
      <div class="e-card-body">

        <!-- Calendar -->
        <div class="cal-grid mb-3">
          {% for d in ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'] %}
          <div class="cal-head">{{ d }}</div>
          {% endfor %}
        </div>

        <div class="cal-grid">
          {% for week in cal %}
            {% for day in week %}
              {% if day == 0 %}
              <div class="cal-cell empty"></div>
              {% else %}
                {% set shift = shift_map.get(day) %}
                <div class="cal-cell
                  {% if shift %}has-shift {{ shift.status }}{% endif %}
                  {% if day == today.day and month == today.month and year == today.year %}today{% endif %}">
                  <span class="day-num">{{ day }}</span>
                  {% if shift %}
                  <span class="shift-dot" style="background:{% if shift.status=='completed' %}var(--green){% elif shift.status=='absent' %}var(--red){% else %}var(--accent){% endif %}"></span>
                  <span class="shift-time-mini">
                    {{ shift.start_time.strftime('%I%p')|lower }}–{{ shift.end_time.strftime('%I%p')|lower }}
                  </span>
                  {% endif %}
                </div>
              {% endif %}
            {% endfor %}
          {% endfor %}
        </div>

        <!-- Legend -->
        <div style="display:flex;gap:1.2rem;margin-top:1rem;flex-wrap:wrap">
          {% for label, color in [('Scheduled','var(--accent)'),('Completed','var(--green)'),('Absent','var(--red)'),('Today','var(--accent)')] %}
          <div style="display:flex;align-items:center;gap:.4rem;font-size:.75rem;color:var(--muted)">
            <span style="width:10px;height:10px;border-radius:50%;background:{{ color }};display:inline-block"></span>
            {{ label }}
          </div>
          {% endfor %}
        </div>
      </div>
    </div>
  </div>

  <!-- Shift list -->
  <div class="col-lg-4">
    <div class="e-card">
      <div class="e-card-head"><h5>Shift Details</h5></div>
      <div class="e-card-body" style="padding:.8rem">
        {% if shifts %}
          {% for s in shifts %}
          <div class="shift-list-item {{ s.status }}">
            <div style="text-align:center;min-width:40px">
              <div style="font-size:.62rem;font-weight:700;text-transform:uppercase;color:var(--muted)">{{ s.date.strftime('%a') }}</div>
              <div style="font-size:1.1rem;font-weight:800;color:var(--text)">{{ s.date.day }}</div>
            </div>
            <div style="flex:1">
              <div style="font-size:.85rem;font-weight:600">
                {{ s.start_time.strftime('%I:%M %p') }} – {{ s.end_time.strftime('%I:%M %p') }}
              </div>
              {% if s.notes %}
              <div style="font-size:.73rem;color:var(--muted);margin-top:.15rem">{{ s.notes }}</div>
              {% endif %}
            </div>
            <span class="badge-emp {% if s.status=='completed' %}b-green{% elif s.status=='absent' %}b-red{% elif s.status=='half_day' %}b-yellow{% else %}b-blue{% endif %}">
              {{ s.status|replace('_',' ')|title }}
            </span>
          </div>
          {% endfor %}
        {% else %}
        <div style="text-align:center;padding:2rem;color:var(--muted)">
          No shifts scheduled this month
        </div>
        {% endif %}
      </div>
    </div>
  </div>
</div>
{% endblock %}
""")

# ═══════════════════════════════════════════════════════════════
# 5. SALARY PAGE
# ═══════════════════════════════════════════════════════════════
w("app/templates/employee/salary.html", r"""{% extends 'employee/base_employee.html' %}
{% block title %}Salary & Commission{% endblock %}
{% block page_title %}Salary & Commission{% endblock %}
{% block extra_css %}
<style>
.salary-hero{
  background:linear-gradient(135deg,#1E2A4A,#2563EB,#8B5CF6);
  border-radius:20px;padding:2rem;color:#fff;margin-bottom:1.5rem;
  position:relative;overflow:hidden;
}
.salary-hero::before{content:'';position:absolute;top:-40px;right:-40px;width:200px;height:200px;border-radius:50%;background:rgba(255,255,255,.04)}
.salary-table{width:100%;border-collapse:collapse}
.salary-table th{font-size:.7rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
  color:var(--muted);padding:.7rem 1rem;border-bottom:1px solid var(--border);text-align:left}
.salary-table td{padding:.8rem 1rem;border-bottom:1px solid var(--border);font-size:.875rem;vertical-align:middle}
.salary-table tr:last-child td{border-bottom:none}
.salary-table tr:hover td{background:#F8FAFF}
.month-badge{font-weight:700;color:var(--text)}
.net-pill{
  font-weight:700;font-family:var(--ff-mono);
  padding:.3rem .8rem;border-radius:50px;
  background:linear-gradient(135deg,var(--accent),var(--purple));
  color:#fff;font-size:.85rem;
}
</style>
{% endblock %}

{% block content %}

<!-- Current month hero -->
<div class="salary-hero">
  <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:2px;opacity:.6;margin-bottom:.5rem">
    Current Month — {{ today.strftime('%B %Y') }}
  </div>
  {% if current_sal %}
  <div class="row g-3">
    <div class="col-6 col-md-3">
      <div style="opacity:.7;font-size:.72rem;margin-bottom:.2rem">Base</div>
      <div style="font-size:1.3rem;font-weight:800;font-family:var(--ff-mono)">₹{{ "%.0f"|format(current_sal.base_salary or 0) }}</div>
    </div>
    <div class="col-6 col-md-3">
      <div style="opacity:.7;font-size:.72rem;margin-bottom:.2rem">Commission</div>
      <div style="font-size:1.3rem;font-weight:800;font-family:var(--ff-mono);color:#FFD166">₹{{ "%.0f"|format(current_sal.commission_earned or 0) }}</div>
    </div>
    <div class="col-6 col-md-3">
      <div style="opacity:.7;font-size:.72rem;margin-bottom:.2rem">Bonus</div>
      <div style="font-size:1.3rem;font-weight:800;font-family:var(--ff-mono);color:#06D6A0">₹{{ "%.0f"|format(current_sal.bonus or 0) }}</div>
    </div>
    <div class="col-6 col-md-3">
      <div style="opacity:.7;font-size:.72rem;margin-bottom:.2rem">Net Payable</div>
      <div style="font-size:1.6rem;font-weight:800;font-family:var(--ff-mono);color:#fff">
        ₹{{ "%.0f"|format(current_sal.net_salary or ((current_sal.base_salary or 0)+(current_sal.commission_earned or 0)+(current_sal.bonus or 0)-(current_sal.deductions or 0))) }}
      </div>
    </div>
  </div>
  <div style="margin-top:.8rem;padding-top:.8rem;border-top:1px solid rgba(255,255,255,.15);display:flex;align-items:center;gap:.8rem">
    <span style="font-size:.8rem;opacity:.7">Status:</span>
    <span style="font-size:.8rem;background:{% if current_sal.payment_status=='paid' %}rgba(6,214,160,.3){% else %}rgba(255,255,255,.1){% endif %};
          border-radius:50px;padding:.2rem .8rem;font-weight:600">
      {% if current_sal.payment_status=='paid' %}✓ Paid{% else %}⏳ Pending{% endif %}
    </span>
    <span style="font-size:.78rem;opacity:.6;margin-left:auto">
      Commission rate: {{ "%.1f"|format((emp.commission_rate or 0)*100) }}% of your sales
    </span>
  </div>
  {% else %}
  <div style="opacity:.6;margin-top:.5rem">Salary record will be generated at month end.</div>
  {% endif %}
</div>

<!-- History -->
<div class="e-card">
  <div class="e-card-head">
    <h5><i class="bi bi-clock-history me-2" style="color:var(--accent)"></i>Salary History</h5>
  </div>
  <div style="overflow-x:auto">
    <table class="salary-table">
      <thead>
        <tr>
          <th>Month</th><th>Base</th><th>Commission</th>
          <th>Bonus</th><th>Deductions</th><th>Net</th><th>Status</th>
        </tr>
      </thead>
      <tbody>
        {% for r in records %}
        <tr>
          <td class="month-badge">
            {{ ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][r.month] }} {{ r.year }}
          </td>
          <td>₹{{ "%.0f"|format(r.base_salary or 0) }}</td>
          <td style="color:var(--purple);font-weight:600">₹{{ "%.0f"|format(r.commission_earned or 0) }}</td>
          <td style="color:var(--green)">₹{{ "%.0f"|format(r.bonus or 0) }}</td>
          <td style="color:var(--red)">₹{{ "%.0f"|format(r.deductions or 0) }}</td>
          <td><span class="net-pill">₹{{ "%.0f"|format(r.net_salary or ((r.base_salary or 0)+(r.commission_earned or 0)+(r.bonus or 0)-(r.deductions or 0))) }}</span></td>
          <td>
            <span class="badge-emp {% if r.payment_status=='paid' %}b-green{% else %}b-yellow{% endif %}">
              {{ r.payment_status|title }}
            </span>
          </td>
        </tr>
        {% else %}
        <tr><td colspan="7" style="text-align:center;padding:3rem;color:var(--muted)">No records yet</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
""")

# ═══════════════════════════════════════════════════════════════
# 6. TASKS PAGE
# ═══════════════════════════════════════════════════════════════
w("app/templates/employee/tasks.html", r"""{% extends 'employee/base_employee.html' %}
{% block title %}My Tasks{% endblock %}
{% block page_title %}Daily Task Checklist{% endblock %}
{% block extra_css %}
<style>
.task-card{
  background:#fff;border-radius:14px;padding:1rem 1.2rem;
  border:1px solid var(--border);margin-bottom:.7rem;
  display:flex;align-items:flex-start;gap:1rem;
  transition:all .2s;
}
.task-card:hover{box-shadow:0 4px 16px rgba(30,42,74,.07)}
.task-card.completed{opacity:.6;background:#F8FAFF}
.task-checkbox{
  width:26px;height:26px;border-radius:8px;border:2px solid var(--border);
  display:flex;align-items:center;justify-content:center;cursor:pointer;
  flex-shrink:0;margin-top:.1rem;transition:all .25s;
}
.task-checkbox.checked{background:var(--green);border-color:var(--green);color:#fff}
.task-body{flex:1}
.task-name{font-size:.9rem;font-weight:600;color:var(--text);line-height:1.4}
.task-name.done{text-decoration:line-through;color:var(--muted)}
.task-desc{font-size:.8rem;color:var(--muted);margin-top:.2rem}
.task-footer{display:flex;align-items:center;gap:.6rem;margin-top:.5rem;flex-wrap:wrap}
.due-tag{font-size:.72rem;padding:.15rem .55rem;border-radius:50px;font-weight:600}
.due-ok{background:#EFF6FF;color:#1E40AF}
.due-today{background:#FFFBEB;color:#92400E}
.due-over{background:#FEF0EF;color:#991B1B}

.tasks-summary{
  display:flex;gap:1rem;margin-bottom:1.5rem;flex-wrap:wrap;
}
.ts-chip{
  background:#fff;border:1px solid var(--border);border-radius:10px;
  padding:.6rem 1rem;display:flex;align-items:center;gap:.5rem;
  font-size:.82rem;font-weight:600;
}
</style>
{% endblock %}

{% block content %}

<!-- Summary chips -->
{% set done_count = tasks | selectattr('is_completed') | list | length %}
{% set total_count = tasks | length %}
{% set pending_count = total_count - done_count %}
<div class="tasks-summary">
  <div class="ts-chip">
    <span style="width:10px;height:10px;background:var(--accent);border-radius:50%;display:inline-block"></span>
    {{ total_count }} Total
  </div>
  <div class="ts-chip">
    <span style="width:10px;height:10px;background:var(--green);border-radius:50%;display:inline-block"></span>
    {{ done_count }} Completed
  </div>
  <div class="ts-chip">
    <span style="width:10px;height:10px;background:var(--gold);border-radius:50%;display:inline-block"></span>
    {{ pending_count }} Pending
  </div>
</div>

{% if tasks %}
  <!-- Pending tasks -->
  {% set pending = tasks | rejectattr('is_completed') | list %}
  {% if pending %}
  <h6 style="font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin-bottom:.8rem">
    Pending ({{ pending|length }})
  </h6>
  {% for task in pending %}
  <div class="task-card" id="tcard-{{ task.id }}">
    <div class="task-checkbox" onclick="toggleTask({{ task.id }}, this)">
      <i class="bi bi-check-lg" style="font-size:.75rem;display:none"></i>
    </div>
    <div class="task-body">
      <div class="task-name" id="tname-{{ task.id }}">{{ task.title }}</div>
      {% if task.description %}
      <div class="task-desc">{{ task.description }}</div>
      {% endif %}
      <div class="task-footer">
        {% if task.due_date %}
          {% if task.due_date < today %}
          <span class="due-tag due-over">⚠ Overdue: {{ task.due_date.strftime('%d %b') }}</span>
          {% elif task.due_date == today %}
          <span class="due-tag due-today">📅 Due Today</span>
          {% else %}
          <span class="due-tag due-ok">📅 {{ task.due_date.strftime('%d %b') }}</span>
          {% endif %}
        {% endif %}
      </div>
    </div>
  </div>
  {% endfor %}
  {% endif %}

  <!-- Completed tasks -->
  {% set done = tasks | selectattr('is_completed') | list %}
  {% if done %}
  <h6 style="font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin:1.5rem 0 .8rem">
    Completed ({{ done|length }})
  </h6>
  {% for task in done %}
  <div class="task-card completed" id="tcard-{{ task.id }}">
    <div class="task-checkbox checked" onclick="toggleTask({{ task.id }}, this)">
      <i class="bi bi-check-lg" style="font-size:.75rem"></i>
    </div>
    <div class="task-body">
      <div class="task-name done" id="tname-{{ task.id }}">{{ task.title }}</div>
      {% if task.completed_at %}
      <div class="task-desc">✓ Done {{ task.completed_at.strftime('%d %b, %I:%M %p') }}</div>
      {% endif %}
    </div>
  </div>
  {% endfor %}
  {% endif %}

{% else %}
<div style="text-align:center;padding:5rem 1rem;color:var(--muted)">
  <i class="bi bi-check-circle" style="font-size:3.5rem;color:var(--green);display:block;margin-bottom:1rem"></i>
  <h4 style="font-weight:700;margin-bottom:.5rem">No tasks assigned yet</h4>
  <p>Your manager will assign tasks here. Check back later!</p>
</div>
{% endif %}

{% endblock %}

{% block extra_js %}
<script>
async function toggleTask(id, checkEl) {
  const isDone = checkEl.classList.contains('checked');
  const url    = isDone ? `/staff/tasks/uncomplete/${id}` : `/staff/tasks/complete/${id}`;
  const res    = await fetch(url, {method:'POST'});
  const data   = await res.json();
  if (!data.ok) return;

  const card  = document.getElementById(`tcard-${id}`);
  const title = document.getElementById(`tname-${id}`);
  const icon  = checkEl.querySelector('i');

  if (!isDone) {
    checkEl.classList.add('checked');
    icon.style.display = '';
    title.classList.add('done');
    card.classList.add('completed');
  } else {
    checkEl.classList.remove('checked');
    icon.style.display = 'none';
    title.classList.remove('done');
    card.classList.remove('completed');
  }
}
</script>
{% endblock %}
""")

# ═══════════════════════════════════════════════════════════════
# 7. ADD TASK MANAGEMENT TO ADMIN (so admin can assign tasks)
# ═══════════════════════════════════════════════════════════════
task_route = r"""

# ── TASK MANAGEMENT (Admin assigns tasks to employees) ────────────────────────
@admin_bp.route('/tasks')
@admin_required
def tasks():
    employees = Employee.query.join(User).all()
    emp_id    = request.args.get('emp_id', type=int)
    sel_emp   = Employee.query.get(emp_id) if emp_id else (employees[0] if employees else None)
    tasks     = Task.query.filter_by(employee_id=sel_emp.id).order_by(
        Task.is_completed, Task.due_date).all() if sel_emp else []
    return render_template('admin/tasks.html',
        employees=employees, sel_emp=sel_emp, tasks=tasks)

@admin_bp.route('/tasks/add', methods=['POST'])
@admin_required
def add_task():
    emp_id = request.form.get('employee_id', type=int)
    title  = request.form.get('title','').strip()
    desc   = request.form.get('description','').strip()
    due    = request.form.get('due_date','')
    if emp_id and title:
        from datetime import datetime as dt
        due_date = dt.strptime(due,'%Y-%m-%d').date() if due else None
        db.session.add(Task(employee_id=emp_id, title=title,
                            description=desc, due_date=due_date))
        db.session.commit()
        flash(f'Task assigned!','success')
    return redirect(url_for('admin.tasks', emp_id=emp_id))

@admin_bp.route('/tasks/delete/<int:tid>', methods=['POST'])
@admin_required
def delete_task(tid):
    task = Task.query.get_or_404(tid)
    emp_id = task.employee_id
    db.session.delete(task); db.session.commit()
    flash('Task deleted.','info')
    return redirect(url_for('admin.tasks', emp_id=emp_id))

# ── SHIFT MANAGEMENT ─────────────────────────────────────────────────────────
@admin_bp.route('/shifts')
@admin_required
def shifts():
    employees = Employee.query.join(User).all()
    emp_id    = request.args.get('emp_id', type=int)
    sel_emp   = Employee.query.get(emp_id) if emp_id else (employees[0] if employees else None)
    from datetime import date
    today     = date.today()
    shifts    = Shift.query.filter_by(employee_id=sel_emp.id).order_by(
        Shift.date.desc()).limit(30).all() if sel_emp else []
    return render_template('admin/shifts.html',
        employees=employees, sel_emp=sel_emp, shifts=shifts, today=today)

@admin_bp.route('/shifts/add', methods=['POST'])
@admin_required
def add_shift():
    from datetime import datetime as dt, time
    emp_id     = request.form.get('employee_id', type=int)
    date_str   = request.form.get('date','')
    start_str  = request.form.get('start_time','')
    end_str    = request.form.get('end_time','')
    notes      = request.form.get('notes','').strip()
    if emp_id and date_str and start_str and end_str:
        shift_date  = dt.strptime(date_str,'%Y-%m-%d').date()
        start_time  = dt.strptime(start_str,'%H:%M').time()
        end_time    = dt.strptime(end_str,'%H:%M').time()
        db.session.add(Shift(employee_id=emp_id, date=shift_date,
            start_time=start_time, end_time=end_time, notes=notes))
        db.session.commit()
        flash('Shift added!','success')
    return redirect(url_for('admin.shifts', emp_id=emp_id))

@admin_bp.route('/shifts/update/<int:sid>', methods=['POST'])
@admin_required
def update_shift(sid):
    shift = Shift.query.get_or_404(sid)
    shift.status = request.form.get('status', shift.status)
    db.session.commit()
    flash('Shift updated!','success')
    return redirect(url_for('admin.shifts', emp_id=shift.employee_id))
"""

routes_path = os.path.join(BASE, "app/admin/routes.py")
with open(routes_path, 'r') as f:
    existing = f.read()
if 'def tasks(' not in existing:
    with open(routes_path, 'a') as f:
        f.write(task_route)
    print("  ✅ Task + Shift admin routes appended")

# Add shifts/tasks to admin sidebar
base_admin_path = os.path.join(BASE, "app/templates/admin/base_admin.html")
with open(base_admin_path, 'r') as f:
    base_content = f.read()
staff_nav = """    <a href="{{ url_for('admin.shifts') }}"
       class="nav-item {% if request.endpoint=='admin.shifts' %}active{% endif %}">
      <i class="bi bi-calendar-week"></i> Manage Shifts
    </a>
    <a href="{{ url_for('admin.tasks') }}"
       class="nav-item {% if request.endpoint=='admin.tasks' %}active{% endif %}">
      <i class="bi bi-list-check"></i> Assign Tasks
    </a>"""
if 'admin.shifts' not in base_content:
    base_content = base_content.replace(
        '<div class="nav-section-label">Store</div>',
        staff_nav + '\n    <div class="nav-section-label">Store</div>'
    )
    with open(base_admin_path, 'w') as f:
        f.write(base_content)
    print("  ✅ Shifts & Tasks added to admin sidebar")

# Minimal admin task/shift templates
w("app/templates/admin/tasks.html", r"""{% extends 'admin/base_admin.html' %}
{% block title %}Assign Tasks{% endblock %}
{% block page_title %}Task Management{% endblock %}
{% block content %}
<div class="row g-4">
  <div class="col-lg-4">
    <div class="panel">
      <div class="panel-head"><h5>Assign New Task</h5></div>
      <div class="panel-body">
        <form method="POST" action="{{ url_for('admin.add_task') }}">
          <label class="ctrl-label">Employee</label>
          <select name="employee_id" class="ctrl mb-3" required>
            {% for e in employees %}
            <option value="{{ e.id }}" {% if sel_emp and sel_emp.id==e.id %}selected{% endif %}>
              {{ e.user.full_name }} ({{ e.employee_code }})
            </option>
            {% endfor %}
          </select>
          <label class="ctrl-label">Task Title *</label>
          <input type="text" name="title" class="ctrl mb-3" placeholder="e.g. Fold and stack new arrivals" required>
          <label class="ctrl-label">Description</label>
          <textarea name="description" class="ctrl mb-3" rows="2" placeholder="Details…"></textarea>
          <label class="ctrl-label">Due Date</label>
          <input type="date" name="due_date" class="ctrl mb-3">
          <button type="submit" class="btn-accent w-100"><i class="bi bi-plus-circle me-2"></i>Assign Task</button>
        </form>
      </div>
    </div>
  </div>
  <div class="col-lg-8">
    <div class="panel">
      <div class="panel-head">
        <h5>Tasks for {{ sel_emp.user.full_name if sel_emp else 'Select Employee' }}</h5>
        <form method="GET" style="display:flex;gap:.5rem">
          <select name="emp_id" class="ctrl" style="width:200px" onchange="this.form.submit()">
            {% for e in employees %}
            <option value="{{ e.id }}" {% if sel_emp and sel_emp.id==e.id %}selected{% endif %}>
              {{ e.user.full_name }}
            </option>
            {% endfor %}
          </select>
        </form>
      </div>
      <div style="overflow-x:auto">
        <table class="data-table">
          <thead><tr><th>Task</th><th>Due</th><th>Status</th><th>Action</th></tr></thead>
          <tbody>
            {% for t in tasks %}
            <tr>
              <td>
                <div style="font-weight:600;font-size:.875rem">{{ t.title }}</div>
                {% if t.description %}<div style="font-size:.75rem;color:var(--muted)">{{ t.description }}</div>{% endif %}
              </td>
              <td style="font-size:.82rem">{{ t.due_date.strftime('%d %b %Y') if t.due_date else '—' }}</td>
              <td>
                <span class="badge-status {% if t.is_completed %}badge-completed{% else %}badge-pending{% endif %}">
                  {{ 'Done' if t.is_completed else 'Pending' }}
                </span>
              </td>
              <td>
                <form method="POST" action="{{ url_for('admin.delete_task', tid=t.id) }}"
                      onsubmit="return confirm('Delete this task?')">
                  <button type="submit" class="btn-danger"><i class="bi bi-trash3"></i></button>
                </form>
              </td>
            </tr>
            {% else %}
            <tr><td colspan="4" style="text-align:center;padding:2rem;color:var(--muted)">No tasks assigned yet</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
{% endblock %}
""")

w("app/templates/admin/shifts.html", r"""{% extends 'admin/base_admin.html' %}
{% block title %}Manage Shifts{% endblock %}
{% block page_title %}Shift Management{% endblock %}
{% block content %}
<div class="row g-4">
  <div class="col-lg-4">
    <div class="panel">
      <div class="panel-head"><h5>Add Shift</h5></div>
      <div class="panel-body">
        <form method="POST" action="{{ url_for('admin.add_shift') }}">
          <label class="ctrl-label">Employee</label>
          <select name="employee_id" class="ctrl mb-3">
            {% for e in employees %}
            <option value="{{ e.id }}" {% if sel_emp and sel_emp.id==e.id %}selected{% endif %}>
              {{ e.user.full_name }}
            </option>
            {% endfor %}
          </select>
          <label class="ctrl-label">Date</label>
          <input type="date" name="date" class="ctrl mb-3" value="{{ today }}" required>
          <div class="row g-2 mb-3">
            <div class="col-6">
              <label class="ctrl-label">Start Time</label>
              <input type="time" name="start_time" class="ctrl" value="10:00" required>
            </div>
            <div class="col-6">
              <label class="ctrl-label">End Time</label>
              <input type="time" name="end_time" class="ctrl" value="21:00" required>
            </div>
          </div>
          <label class="ctrl-label">Notes</label>
          <input type="text" name="notes" class="ctrl mb-3" placeholder="Optional note">
          <button type="submit" class="btn-accent w-100"><i class="bi bi-plus-circle me-2"></i>Add Shift</button>
        </form>
      </div>
    </div>
  </div>
  <div class="col-lg-8">
    <div class="panel">
      <div class="panel-head">
        <h5>Shifts for {{ sel_emp.user.full_name if sel_emp else '—' }}</h5>
        <form method="GET" style="display:flex;gap:.5rem">
          <select name="emp_id" class="ctrl" style="width:200px" onchange="this.form.submit()">
            {% for e in employees %}
            <option value="{{ e.id }}" {% if sel_emp and sel_emp.id==e.id %}selected{% endif %}>
              {{ e.user.full_name }}
            </option>
            {% endfor %}
          </select>
        </form>
      </div>
      <div style="overflow-x:auto">
        <table class="data-table">
          <thead><tr><th>Date</th><th>Time</th><th>Status</th><th>Notes</th><th>Update</th></tr></thead>
          <tbody>
            {% for s in shifts %}
            <tr>
              <td style="font-weight:600">{{ s.date.strftime('%d %b %Y') }}</td>
              <td style="font-family:var(--ff-mono);font-size:.82rem">
                {{ s.start_time.strftime('%I:%M %p') }} – {{ s.end_time.strftime('%I:%M %p') }}
              </td>
              <td><span class="badge-status badge-{{ 'completed' if s.status=='completed' else 'pending' }}">{{ s.status|title }}</span></td>
              <td style="font-size:.8rem;color:var(--muted)">{{ s.notes or '—' }}</td>
              <td>
                <form method="POST" action="{{ url_for('admin.update_shift', sid=s.id) }}" style="display:flex;gap:.4rem">
                  <select name="status" class="ctrl" style="padding:.3rem .5rem;font-size:.78rem;width:130px">
                    {% for st in ['scheduled','completed','absent','half_day'] %}
                    <option value="{{ st }}" {% if s.status==st %}selected{% endif %}>{{ st|replace('_',' ')|title }}</option>
                    {% endfor %}
                  </select>
                  <button type="submit" class="btn-success" style="padding:.3rem .6rem">✓</button>
                </form>
              </td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="text-align:center;padding:2rem;color:var(--muted)">No shifts yet</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
{% endblock %}
""")

print()
print("="*55)
print("  🎉 Employee Portal built successfully!")
print("  Run: python3 run.py")
print("  Employee login → http://localhost:5000/login")
print("="*55)

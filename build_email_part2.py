#!/usr/bin/env python3
"""
📧 MBM Email & Password System - Part 2
All routes + templates for:
- Email verification
- Password reset
- Change password (users + admin)
"""
import os

BASE = os.path.expanduser("~/Desktop/mbmaniyar")

def w(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ {path}")

print("\n📧 Building Routes & Templates\n" + "="*45)

# ══════════════════════════════════════════════
# 1. PATCH AUTH ROUTES
# ══════════════════════════════════════════════
print("\n🔧 Rewriting auth/routes.py...")
w("app/auth/routes.py", r"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User
from datetime import datetime, timedelta
import secrets

auth_bp = Blueprint('auth', __name__)

# ── HOME REDIRECT ──────────────────────────────────────────────────
@auth_bp.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'employee':
            return redirect(url_for('employee.dashboard'))
        else:
            return redirect(url_for('customer.index'))
    return redirect(url_for('customer.index'))

@auth_bp.route('/about')
def about():
    return render_template('customer/about.html')

# ── LOGIN ──────────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.home'))
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()
        user     = User.query.filter(
            (User.username==username) | (User.email==username)
        ).first()
        if user and check_password_hash(user.password_hash, password):
            if not user.is_active_account:
                flash('Account deactivated. Contact admin.','danger')
                return render_template('auth/login.html')
            login_user(user)
            nxt = request.args.get('next')
            if nxt:
                return redirect(nxt)
            return redirect(url_for('auth.home'))
        flash('Invalid username or password.','danger')
    return render_template('auth/login.html')

# ── REGISTER ───────────────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name','').strip()
        username  = request.form.get('username','').strip()
        email     = request.form.get('email','').strip()
        phone     = request.form.get('phone','').strip()
        password  = request.form.get('password','').strip()
        if User.query.filter_by(username=username).first():
            flash('Username taken.','danger')
            return render_template('auth/register.html')
        if email and User.query.filter_by(email=email).first():
            flash('Email already registered.','danger')
            return render_template('auth/register.html')
        if not email:
            email = f"{username}@mbmaniyar.local"
        token = secrets.token_urlsafe(32)
        user  = User(full_name=full_name, username=username, email=email,
                     phone=phone, password_hash=generate_password_hash(password),
                     role='customer', verification_token=token,
                     email_verified=email.endswith('@mbmaniyar.local'))
        db.session.add(user)
        db.session.commit()
        # Send verification email
        if not email.endswith('@mbmaniyar.local'):
            try:
                from app.mail_service import send_verification_email
                send_verification_email(user, token)
                flash('Account created! Check your email to verify your account.','success')
            except Exception as e:
                flash('Account created! You can log in now.','success')
        else:
            flash('Account created! You can log in now.','success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

# ── EMAIL VERIFICATION ─────────────────────────────────────────────
@auth_bp.route('/verify/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        flash('Invalid or expired verification link.','danger')
        return redirect(url_for('auth.login'))
    user.email_verified      = True
    user.verification_token  = None
    db.session.commit()
    try:
        from app.mail_service import send_welcome_email
        send_welcome_email(user)
    except:
        pass
    flash('Email verified! Welcome to M.B Maniyar 🎉','success')
    return redirect(url_for('auth.login'))

# ── RESEND VERIFICATION ────────────────────────────────────────────
@auth_bp.route('/resend-verification', methods=['GET','POST'])
def resend_verification():
    if request.method == 'POST':
        email = request.form.get('email','').strip()
        user  = User.query.filter_by(email=email).first()
        if user and not user.email_verified:
            token = secrets.token_urlsafe(32)
            user.verification_token = token
            db.session.commit()
            try:
                from app.mail_service import send_verification_email
                send_verification_email(user, token)
            except:
                pass
        flash('If that email exists, a verification link has been sent.','info')
        return redirect(url_for('auth.login'))
    return render_template('auth/resend_verification.html')

# ── FORGOT PASSWORD ────────────────────────────────────────────────
@auth_bp.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email','').strip()
        user  = User.query.filter(
            (User.email==email) | (User.username==email)
        ).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token        = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            try:
                from app.mail_service import send_password_reset_email
                send_password_reset_email(user, token)
            except:
                pass
        flash('If that account exists, a reset link has been sent to your email.','info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html')

# ── RESET PASSWORD ─────────────────────────────────────────────────
@auth_bp.route('/reset-password/<token>', methods=['GET','POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or (user.reset_token_expiry and user.reset_token_expiry < datetime.utcnow()):
        flash('Invalid or expired reset link. Please request a new one.','danger')
        return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        pw  = request.form.get('password','').strip()
        pw2 = request.form.get('confirm_password','').strip()
        if len(pw) < 6:
            flash('Password must be at least 6 characters.','danger')
            return render_template('auth/reset_password.html', token=token)
        if pw != pw2:
            flash('Passwords do not match.','danger')
            return render_template('auth/reset_password.html', token=token)
        user.password_hash   = generate_password_hash(pw)
        user.reset_token     = None
        user.reset_token_expiry = None
        db.session.commit()
        flash('Password reset! You can now log in.','success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', token=token)

# ── CHANGE PASSWORD (logged in users) ─────────────────────────────
@auth_bp.route('/change-password', methods=['GET','POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pw = request.form.get('current_password','').strip()
        new_pw     = request.form.get('new_password','').strip()
        confirm_pw = request.form.get('confirm_password','').strip()
        if not check_password_hash(current_user.password_hash, current_pw):
            flash('Current password is incorrect.','danger')
            return render_template('auth/change_password.html')
        if len(new_pw) < 6:
            flash('New password must be at least 6 characters.','danger')
            return render_template('auth/change_password.html')
        if new_pw != confirm_pw:
            flash('New passwords do not match.','danger')
            return render_template('auth/change_password.html')
        current_user.password_hash = generate_password_hash(new_pw)
        db.session.commit()
        flash('Password changed successfully! 🔐','success')
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'employee':
            return redirect(url_for('employee.profile'))
        return redirect(url_for('customer.index'))
    return render_template('auth/change_password.html')

# ── LOGOUT ─────────────────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.','info')
    return redirect(url_for('auth.login'))
""")

# ══════════════════════════════════════════════
# 2. PATCH ORDER ROUTES to send emails
# ══════════════════════════════════════════════
print("\n🔧 Patching order confirmation emails...")
customer_routes = os.path.join(BASE, "app/customer/routes.py")
with open(customer_routes, 'r') as f:
    cr = f.read()

if 'send_order_confirmation' not in cr:
    cr = cr.replace(
        "db.session.commit()\n        flash(",
        """db.session.commit()
        # Send confirmation email
        try:
            from app.mail_service import send_order_confirmation
            send_order_confirmation(current_user, order)
        except Exception as e:
            print(f"Email error: {e}")
        flash("""
    )
    with open(customer_routes, 'w') as f:
        f.write(cr)
    print("  ✅ Order confirmation email added")

# Patch admin order update to send status email
admin_routes = os.path.join(BASE, "app/admin/routes.py")
with open(admin_routes, 'r') as f:
    ar = f.read()
if 'send_order_status_update' not in ar:
    ar = ar.replace(
        "def update_order(oid):\n    order = Order.query.get_or_404(oid)\n    ns    = request.form.get('status')\n    pm    = request.form.get('payment_status')\n    if ns:\n        order.status = ns\n    if pm:\n        order.payment_status = pm\n    db.session.commit()\n    flash(",
        """def update_order(oid):
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
        from app.mail_service import send_order_status_update
        if order.user and not order.user.email.endswith('@mbmaniyar.local'):
            send_order_status_update(order.user, order)
    except Exception as e:
        print(f"Email error: {e}")
    flash("""
    )
    with open(admin_routes, 'w') as f:
        f.write(ar)
    print("  ✅ Order status email added")

# ══════════════════════════════════════════════
# 3. ALL AUTH TEMPLATES
# ══════════════════════════════════════════════
print("\n🎨 Building auth templates...")

FORM_BASE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | M.B Maniyar</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Playfair+Display:wght@700;900&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Outfit',sans-serif;background:linear-gradient(135deg,#560D1E 0%,#7B1C2E 50%,#3D0A15 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:1rem}}
.card{{background:#fff;border-radius:24px;padding:2.5rem;width:100%;max-width:440px;box-shadow:0 20px 60px rgba(0,0,0,.3)}}
.logo{{text-align:center;margin-bottom:2rem}}
.logo-icon{{width:56px;height:56px;border-radius:16px;background:linear-gradient(135deg,#7B1C2E,#9E2A3F);display:flex;align-items:center;justify-content:center;margin:0 auto .6rem;font-size:1.4rem}}
.logo-name{{font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:#560D1E}}
.logo-sub{{font-size:.72rem;color:#9A8578;letter-spacing:1px}}
h2{{font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;color:#2C1810;margin-bottom:.3rem}}
.subtitle{{font-size:.85rem;color:#9A8578;margin-bottom:1.8rem}}
label{{display:block;font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#7A6358;margin-bottom:.35rem}}
input{{width:100%;background:#FAF6F0;border:1.5px solid #E8DDD4;border-radius:10px;padding:.7rem 1rem;font-size:.9rem;font-family:'Outfit',sans-serif;outline:none;transition:border-color .2s;margin-bottom:1.1rem}}
input:focus{{border-color:#7B1C2E;background:#fff}}
.btn{{width:100%;background:linear-gradient(135deg,#7B1C2E,#9E2A3F);color:#E8B96A;border:none;border-radius:50px;padding:.85rem;font-size:.95rem;font-weight:700;cursor:pointer;font-family:'Outfit',sans-serif;transition:all .2s;letter-spacing:.5px}}
.btn:hover{{transform:translateY(-2px);box-shadow:0 8px 20px rgba(123,28,46,.3)}}
.link-row{{text-align:center;margin-top:1.2rem;font-size:.83rem;color:#9A8578}}
.link-row a{{color:#7B1C2E;font-weight:600;text-decoration:none}}
.flash{{border-radius:8px;padding:.65rem .9rem;margin-bottom:1rem;font-size:.82rem;display:flex;align-items:center;gap:.5rem}}
.flash-danger{{background:#FEF2F2;border:1px solid #FECACA;color:#991B1B}}
.flash-success{{background:#F0FDF4;border:1px solid #A7F3D0;color:#065F46}}
.flash-info{{background:#EFF6FF;border:1px solid #BFDBFE;color:#1E40AF}}
.flash-warning{{background:#FFFBEB;border:1px solid #FDE68A;color:#92400E}}
.input-wrap{{position:relative}}
.eye-btn{{position:absolute;right:.8rem;top:.7rem;background:none;border:none;cursor:pointer;color:#9A8578;padding:0;font-size:1rem}}
</style>
</head>
<body>
<div class="card">
  <div class="logo">
    <div class="logo-icon">👔</div>
    <div class="logo-name">M.B Maniyar</div>
    <div class="logo-sub">Cloth Store · Mantha</div>
  </div>
  {{% with messages = get_flashed_messages(with_categories=true) %}}
    {{% for cat, msg in messages %}}
    <div class="flash flash-{{{{ cat }}}}"><i class="bi bi-info-circle"></i>{{{{ msg }}}}</div>
    {{% endfor %}}
  {{% endwith %}}
  {body}
</div>
<script>
function togglePw(id){{
  const i=document.getElementById(id);
  i.type=i.type==='password'?'text':'password';
}}
</script>
</body></html>"""

# ── LOGIN ──
w("app/templates/auth/login.html", FORM_BASE.format(title="Login", body="""
  <h2>Welcome Back</h2>
  <p class="subtitle">Login to your M.B Maniyar account</p>
  <form method="POST">
    <label>Username or Email</label>
    <input type="text" name="username" placeholder="Enter username or email" required autofocus>
    <label>Password</label>
    <div class="input-wrap">
      <input type="password" name="password" id="pw" placeholder="Enter your password" required style="margin-bottom:.5rem;padding-right:2.5rem">
      <button type="button" class="eye-btn" onclick="togglePw('pw')"><i class="bi bi-eye"></i></button>
    </div>
    <div style="text-align:right;margin-bottom:1.2rem">
      <a href="/forgot-password" style="font-size:.8rem;color:#7B1C2E;text-decoration:none">Forgot password?</a>
    </div>
    <button type="submit" class="btn">Sign In →</button>
  </form>
  <div class="link-row">Don't have an account? <a href="/register">Create one</a></div>
"""))

# ── REGISTER ──
w("app/templates/auth/register.html", FORM_BASE.format(title="Register", body="""
  <h2>Create Account</h2>
  <p class="subtitle">Join the M.B Maniyar family</p>
  <form method="POST">
    <label>Full Name</label>
    <input type="text" name="full_name" placeholder="Your full name" required>
    <label>Username</label>
    <input type="text" name="username" placeholder="Choose a username" required>
    <label>Email</label>
    <input type="email" name="email" placeholder="your@email.com (for order updates)">
    <label>Phone</label>
    <input type="tel" name="phone" placeholder="+91 XXXXX XXXXX">
    <label>Password</label>
    <div class="input-wrap">
      <input type="password" name="password" id="pw" placeholder="Min 6 characters" required style="padding-right:2.5rem">
      <button type="button" class="eye-btn" onclick="togglePw('pw')"><i class="bi bi-eye"></i></button>
    </div>
    <button type="submit" class="btn">Create Account →</button>
  </form>
  <div class="link-row">Already have an account? <a href="/login">Sign in</a></div>
"""))

# ── FORGOT PASSWORD ──
w("app/templates/auth/forgot_password.html", FORM_BASE.format(title="Forgot Password", body="""
  <h2>Forgot Password?</h2>
  <p class="subtitle">Enter your email and we'll send a reset link</p>
  <form method="POST">
    <label>Email or Username</label>
    <input type="text" name="email" placeholder="your@email.com or username" required autofocus>
    <button type="submit" class="btn">Send Reset Link →</button>
  </form>
  <div class="link-row">Remember it? <a href="/login">Back to Login</a></div>
"""))

# ── RESET PASSWORD ──
w("app/templates/auth/reset_password.html", FORM_BASE.format(title="Reset Password", body="""
  <h2>Set New Password</h2>
  <p class="subtitle">Choose a strong new password for your account</p>
  <form method="POST">
    <label>New Password</label>
    <div class="input-wrap">
      <input type="password" name="password" id="pw1" placeholder="Min 6 characters" required style="padding-right:2.5rem">
      <button type="button" class="eye-btn" onclick="togglePw('pw1')"><i class="bi bi-eye"></i></button>
    </div>
    <label>Confirm New Password</label>
    <div class="input-wrap">
      <input type="password" name="confirm_password" id="pw2" placeholder="Repeat new password" required style="padding-right:2.5rem">
      <button type="button" class="eye-btn" onclick="togglePw('pw2')"><i class="bi bi-eye"></i></button>
    </div>
    <button type="submit" class="btn">Reset Password →</button>
  </form>
"""))

# ── CHANGE PASSWORD ──
w("app/templates/auth/change_password.html", FORM_BASE.format(title="Change Password", body="""
  <h2>Change Password</h2>
  <p class="subtitle">Keep your account secure with a strong password</p>
  <form method="POST" action="/change-password">
    <label>Current Password</label>
    <div class="input-wrap">
      <input type="password" name="current_password" id="pw0" placeholder="Your current password" required style="padding-right:2.5rem">
      <button type="button" class="eye-btn" onclick="togglePw('pw0')"><i class="bi bi-eye"></i></button>
    </div>
    <label>New Password</label>
    <div class="input-wrap">
      <input type="password" name="new_password" id="pw1" placeholder="Min 6 characters" required style="padding-right:2.5rem">
      <button type="button" class="eye-btn" onclick="togglePw('pw1')"><i class="bi bi-eye"></i></button>
    </div>
    <label>Confirm New Password</label>
    <div class="input-wrap">
      <input type="password" name="confirm_password" id="pw2" placeholder="Repeat new password" required style="padding-right:2.5rem">
      <button type="button" class="eye-btn" onclick="togglePw('pw2')"><i class="bi bi-eye"></i></button>
    </div>
    <button type="submit" class="btn">Update Password 🔐</button>
  </form>
  <div class="link-row"><a href="javascript:history.back()">← Go Back</a></div>
"""))

# ── RESEND VERIFICATION ──
w("app/templates/auth/resend_verification.html", FORM_BASE.format(title="Resend Verification", body="""
  <h2>Resend Verification</h2>
  <p class="subtitle">Enter your email to get a new verification link</p>
  <form method="POST">
    <label>Email Address</label>
    <input type="email" name="email" placeholder="your@email.com" required autofocus>
    <button type="submit" class="btn">Resend Verification Email →</button>
  </form>
  <div class="link-row"><a href="/login">← Back to Login</a></div>
"""))

# ══════════════════════════════════════════════
# 4. Add Change Password links to portals
# ══════════════════════════════════════════════
print("\n🔧 Adding change password links to sidebars...")

# Employee sidebar
emp_base = os.path.join(BASE, "app/templates/employee/base_employee.html")
with open(emp_base, 'r') as f:
    eb = f.read()
if 'change-password' not in eb:
    eb = eb.replace(
        '<a href="{{ url_for(\'auth.logout\') }}" class="sb-logout">',
        '''<a href="/change-password" class="sb-logout" style="color:rgba(255,255,255,.3)">
      <i class="bi bi-key"></i> Change Password
    </a>
    <a href="{{ url_for('auth.logout') }}" class="sb-logout">'''
    )
    with open(emp_base, 'w') as f:
        f.write(eb)
    print("  ✅ Change password added to employee sidebar")

# Admin sidebar
adm_base = os.path.join(BASE, "app/templates/admin/base_admin.html")
with open(adm_base, 'r') as f:
    ab = f.read()
if 'change-password' not in ab:
    ab = ab.replace(
        'href="{{ url_for(\'auth.logout\') }}"',
        'href="/change-password" style="margin-bottom:.3rem">🔐 Change Password</a>\n    <a href="{{ url_for(\'auth.logout\') }}"'
    )
    with open(adm_base, 'w') as f:
        f.write(ab)
    print("  ✅ Change password added to admin sidebar")

# ══════════════════════════════════════════════
# 5. Admin: manage user passwords
# ══════════════════════════════════════════════
print("\n🔧 Adding admin user management route...")
admin_routes = os.path.join(BASE, "app/admin/routes.py")
with open(admin_routes, 'r') as f:
    ar = f.read()

admin_user_mgmt = """

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
"""
if 'admin_reset_password' not in ar:
    with open(admin_routes, 'a') as f:
        f.write(admin_user_mgmt)
    print("  ✅ Admin user management routes added")

# Add Users link to admin sidebar
with open(adm_base, 'r') as f:
    ab = f.read()
if 'admin.users' not in ab:
    ab = ab.replace(
        '<div class="nav-section-label">Store</div>',
        '''<a href="{{ url_for('admin.users') }}"
       class="nav-item {% if request.endpoint=='admin.users' %}active{% endif %}">
      <i class="bi bi-people"></i> User Management
    </a>
    <div class="nav-section-label">Store</div>'''
    )
    with open(adm_base, 'w') as f:
        f.write(ab)
    print("  ✅ User Management added to admin sidebar")

# Admin users template
w("app/templates/admin/users.html", r"""{% extends 'admin/base_admin.html' %}
{% block title %}User Management{% endblock %}
{% block page_title %}User Management{% endblock %}
{% block content %}
<div class="panel">
  <div class="panel-head"><h5><i class="bi bi-people me-2"></i>All Users ({{ users|length }})</h5></div>
  <div style="overflow-x:auto">
    <table class="data-table">
      <thead>
        <tr><th>Name</th><th>Username</th><th>Email</th><th>Role</th><th>Verified</th><th>Status</th><th>Reset Password</th></tr>
      </thead>
      <tbody>
        {% for u in users %}
        <tr>
          <td style="font-weight:600">{{ u.full_name }}</td>
          <td style="font-family:var(--ff-mono);font-size:.82rem">{{ u.username }}</td>
          <td style="font-size:.82rem;color:var(--muted)">{{ u.email }}</td>
          <td>
            <span class="badge-status {% if u.role=='admin' %}badge-completed{% elif u.role=='employee' %}badge-confirmed{% else %}badge-pending{% endif %}">
              {{ u.role|title }}
            </span>
          </td>
          <td style="text-align:center">
            {% if u.email_verified %}✅{% else %}⏳{% endif %}
          </td>
          <td>
            {% if u.is_active_account %}
            <span class="badge-status badge-completed">Active</span>
            {% else %}
            <span class="badge-status badge-pending">Inactive</span>
            {% endif %}
          </td>
          <td>
            {% if u.id != current_user.id %}
            <form method="POST" action="{{ url_for('admin.admin_reset_password', uid=u.id) }}"
                  style="display:flex;gap:.4rem;align-items:center"
                  onsubmit="return confirm('Reset password for {{ u.full_name }}?')">
              <input type="password" name="new_password" class="ctrl"
                     style="padding:.3rem .6rem;font-size:.78rem;width:130px" placeholder="New password" required minlength="6">
              <button type="submit" class="btn-success" style="padding:.3rem .7rem;font-size:.8rem">Set</button>
            </form>
            {% else %}
            <a href="/change-password" class="btn-accent" style="font-size:.78rem;padding:.3rem .7rem;text-decoration:none">Change Mine</a>
            {% endif %}
          </td>
        </tr>
        {% else %}
        <tr><td colspan="7" style="text-align:center;padding:2rem;color:var(--muted)">No users</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
""")

print("""
╔══════════════════════════════════════════════╗
║  🎉 Email & Password System Complete!        ║
╠══════════════════════════════════════════════╣
║  Now do:                                     ║
║  1. Set up Gmail (see instructions below)    ║
║  2. git add . && git commit -m "Email system"║
║  3. git push origin main                     ║
╚══════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📧 GMAIL SETUP (to actually send emails)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Go to myaccount.google.com/security
  2. Enable 2-Step Verification
  3. Search "App Passwords" → Create one
     App: Mail | Device: Other → name it "MBM"
  4. Copy the 16-character password

  Then add to Render environment variables:
  MAIL_USERNAME = your-gmail@gmail.com
  MAIL_PASSWORD = xxxx-xxxx-xxxx-xxxx

  Done! Emails will send automatically for:
  ✅ Registration verification
  ✅ Order confirmations
  ✅ Order status updates
  ✅ Password reset
  ✅ Welcome email after verify
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

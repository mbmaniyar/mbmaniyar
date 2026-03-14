
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
            try:
                from app.security_emails import send_login_alert
                send_login_alert(user, request)
            except Exception as e:
                print(f'Login alert error: {e}')
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
        try:
            from app.security_emails import send_password_changed_alert
            send_password_changed_alert(current_user, request)
        except Exception as e:
            print(f'Password alert error: {e}')
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

# auth/routes.py — Authentication Routes
#
# This file handles everything related to logging in, logging out,
# and registering new customer accounts.
#
# A "route" in Flask = a URL that does something.
# @auth_bp.route('/login') means: when someone visits /auth/login, run this function.

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User

# Blueprint groups all auth-related routes together under one name 'auth'
auth_bp = Blueprint('auth', __name__)


# =============================================================================
# HOME ROUTE — The store's landing page
# =============================================================================

@auth_bp.route('/')
def home():
    """
    The front door of M B MANIYAR.
    If someone is already logged in, send them to their correct portal.
    Otherwise, show the public landing page.
    """
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)
    return render_template('index.html')


# =============================================================================
# LOGIN ROUTE
# =============================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET  → Show the login form
    POST → Process the login form (check username/password)
    
    'methods=['GET', 'POST']' means this route accepts both types of requests.
    GET  = browser just visiting the page
    POST = browser submitting a form
    """

    # If user is already logged in, no need to show login page
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    # When the form is submitted (POST request)
    if request.method == 'POST':

        # Get the values typed into the form fields
        # request.form['name'] reads what the user typed in the input named 'name'
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        # 'remember me' checkbox — keeps them logged in after browser closes
        remember = True if request.form.get('remember') else False

        # --- Validate inputs aren't empty ---
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('auth/login.html')

        # --- Look up the user in the database ---
        # We check both username AND email so user can log in with either
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        # --- Check if user exists and password is correct ---
        # check_password_hash compares the typed password with the stored hash
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('auth/login.html')

        # --- Check if account is active ---
        if not user.is_active_account:
            flash('Your account has been deactivated. Please contact the store.', 'warning')
            return render_template('auth/login.html')

        # --- All checks passed! Log the user in ---
        # login_user() from Flask-Login creates a session for this user
        login_user(user, remember=remember)

        flash(f'Welcome back, {user.full_name}! 👋', 'success')

        # Redirect to the correct portal based on their role
        return _redirect_by_role(user.role)

    # GET request — just show the login form
    return render_template('auth/login.html')


# =============================================================================
# LOGOUT ROUTE
# =============================================================================

@auth_bp.route('/logout')
@login_required  # Only logged-in users can log out (makes sense!)
def logout():
    """Logs the current user out and sends them to the home page."""
    logout_user()  # Flask-Login clears the session
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.home'))


# =============================================================================
# REGISTER ROUTE (Customers only — employees/admin are created by admin)
# =============================================================================

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Only customers register themselves.
    Employee and admin accounts are created by the store owner in the admin panel.
    """

    # Already logged in? Send them home.
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    if request.method == 'POST':

        # Collect all form fields
        full_name = request.form.get('full_name', '').strip()
        username  = request.form.get('username', '').strip()
        email     = request.form.get('email', '').strip().lower()
        phone     = request.form.get('phone', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')

        # --- Basic validation ---
        if not all([full_name, username, email, password, confirm]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html')

        if password != confirm:
            flash('Passwords do not match. Please try again.', 'danger')
            return render_template('auth/register.html')

        # --- Check if username or email already exists ---
        if User.query.filter_by(username=username).first():
            flash('That username is already taken. Please choose another.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'danger')
            return render_template('auth/register.html')

        # --- Create the new customer account ---
        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
            phone=phone,
            # NEVER store plain password — always hash it!
            password_hash=generate_password_hash(password),
            role='customer'  # All self-registered users are customers
        )

        # Save to database
        db.session.add(new_user)
        db.session.commit()

        # Automatically log them in after registration
        login_user(new_user)
        flash(f'Welcome to M B MANIYAR, {full_name}! Your account is ready. 🎉', 'success')
        return redirect(url_for('customer.index'))

    # GET — show the registration form
    return render_template('auth/register.html')


# =============================================================================
# HELPER FUNCTION
# =============================================================================

def _redirect_by_role(role):
    """
    Send the user to the correct portal based on their role.
    This is called after login and on home page if already logged in.
    """
    if role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif role == 'employee':
        return redirect(url_for('employee.dashboard'))
    else:  # customer
        return redirect(url_for('customer.index'))

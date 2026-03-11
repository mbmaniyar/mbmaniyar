from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15))
    is_active_account = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='customer', lazy=True,
                              foreign_keys='Order.user_id')
    cart_items = db.relationship('CartItem', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'


class Brand(db.Model):
    __tablename__ = 'brands'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_special_tracked = db.Column(db.Boolean, default=False)
    products = db.relationship('Product', backref='brand', lazy=True)

    def __repr__(self):
        return f'<Brand {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    mrp = db.Column(db.Numeric(10, 2))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    image_filename = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    is_online = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow)
    variants = db.relationship('ProductVariant', backref='product', lazy=True,
                                cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.name}>'


class ProductVariant(db.Model):
    __tablename__ = 'product_variants'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    size = db.Column(db.String(10), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    low_stock_threshold = db.Column(db.Integer, default=3)
    barcode = db.Column(db.String(50), unique=True)
    __table_args__ = (
        db.UniqueConstraint('product_id', 'size', name='unique_product_size'),
    )

    def __repr__(self):
        return f'<Variant {self.product_id} - {self.size}: {self.stock_quantity}>'

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def is_out_of_stock(self):
        return self.stock_quantity == 0


class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'),
                            nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    variant = db.relationship('ProductVariant')


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_type = db.Column(db.String(20), nullable=False, default='pickup')
    status = db.Column(db.String(20), nullable=False, default='pending')
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(20))
    payment_status = db.Column(db.String(20), default='pending')
    customer_notes = db.Column(db.Text)
    processed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True,
                             cascade='all, delete-orphan')
    processed_by = db.relationship('User', foreign_keys=[processed_by_id])

    def __repr__(self):
        return f'<Order {self.order_number}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'),
                            nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    product = db.relationship('Product')
    variant = db.relationship('ProductVariant')


class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True,
                         nullable=False)
    employee_code = db.Column(db.String(20), unique=True, nullable=False)
    designation = db.Column(db.String(100))
    department = db.Column(db.String(50))
    date_of_joining = db.Column(db.Date)
    base_salary = db.Column(db.Numeric(10, 2))
    commission_rate = db.Column(db.Numeric(5, 4), default=0.0)
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(15))
    user = db.relationship('User',
                            backref=db.backref('employee_profile', uselist=False))

    def __repr__(self):
        return f'<Employee {self.employee_code}>'


class Shift(db.Model):
    __tablename__ = 'shifts'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='scheduled')
    notes = db.Column(db.String(200))
    employee = db.relationship('Employee', backref='shifts')


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    employee = db.relationship('Employee', backref='tasks')


class MonthlySalary(db.Model):
    __tablename__ = 'monthly_salaries'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    base_salary = db.Column(db.Numeric(10, 2))
    commission_earned = db.Column(db.Numeric(10, 2), default=0)
    bonus = db.Column(db.Numeric(10, 2), default=0)
    deductions = db.Column(db.Numeric(10, 2), default=0)
    net_salary = db.Column(db.Numeric(10, 2))
    payment_status = db.Column(db.String(20), default='pending')
    payment_date = db.Column(db.Date)
    employee = db.relationship('Employee', backref='salary_records')
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'month', 'year',
                             name='unique_employee_month_salary'),
    )


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
    date        = db.Column(db.Date, default=lambda: __import__('datetime').date.today())
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

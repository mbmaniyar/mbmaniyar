from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_mail import Mail
from app.models import db

login_manager = LoginManager()
socketio = SocketIO()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    socketio.init_app(app, cors_allowed_origins="*")
    mail.init_app(app)
    app.config['MAIL_ENABLED'] = bool(app.config.get('MAIL_USERNAME', ''))

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='')

    from app.admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.customer.routes import customer_bp
    app.register_blueprint(customer_bp, url_prefix='/shop')

    from app.employee.routes import employee_bp
    app.register_blueprint(employee_bp, url_prefix='/staff')

    # Make datetime.now() available in all templates
    from datetime import datetime
    app.jinja_env.globals['now'] = datetime.now

    with app.app_context():
        db.create_all()
        _seed_initial_data(app)

    return app


def _seed_initial_data(app):
    from app.models import User, Brand, Category
    from werkzeug.security import generate_password_hash

    if User.query.first() is not None:
        return

    print("Seeding initial data for M B MANIYAR...")

    admin_user = User(
        username='admin',
        email='mbmaniyar@gmail.com',
        password_hash=generate_password_hash('admin123'),
        role='admin',
        full_name='Store Admin',
        phone='9999999999'
    )
    db.session.add(admin_user)

    ksatish_brand = Brand(name='k satish', is_special_tracked=True)
    db.session.add(ksatish_brand)

    for brand_name in ['Raymond', 'Allen Solly', 'Peter England', 'Generic']:
        db.session.add(Brand(name=brand_name, is_special_tracked=False))

    categories_data = [
        ('Shirts', 'shirts'), ('Trousers', 'trousers'),
        ('Kurtas', 'kurtas'), ('T-Shirts', 't-shirts'),
        ('Kids Wear', 'kids-wear'), ('Accessories', 'accessories'),
    ]
    for name, slug in categories_data:
        db.session.add(Category(name=name, slug=slug))

    db.session.commit()
    print("Initial data seeded! Admin login: admin / admin123")

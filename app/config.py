import os
from dotenv import load_dotenv
load_dotenv()

def get_db_url():
    url = os.environ.get('DATABASE_URL', 'sqlite:///mbmaniyar.db')
    # Render gives postgres:// but SQLAlchemy needs postgresql://
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url

class Config:
    SECRET_KEY        = os.environ.get('SECRET_KEY') or 'mbm-super-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = get_db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STORE_NAME    = os.environ.get('STORE_NAME', 'M.B Maniyar Cloth Store')
    STORE_ADDRESS = os.environ.get('STORE_ADDRESS', 'Main Road, Opposite Bus Stand, Mantha, Jalna')
    STORE_PHONE   = os.environ.get('STORE_PHONE', '+91 94214 74678')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images', 'products')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    MAIL_SERVER   = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'M.B Maniyar <noreply@mbmaniyar.com>')
    MAIL_ENABLED  = bool(os.environ.get('MAIL_USERNAME', ''))

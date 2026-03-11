import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY        = os.environ.get('SECRET_KEY') or 'mbm-super-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///mbmaniyar.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STORE_NAME    = os.environ.get('STORE_NAME', 'M.B Maniyar Cloth Store')
    STORE_ADDRESS = os.environ.get('STORE_ADDRESS', 'Main Road, Opposite Bus Stand, Mantha, Jalna')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images', 'products')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

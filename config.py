import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-fallback-secret-key-shopsmart-ai')
    DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't')
    
    # MySQL Database Config
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'ai_shopping_assistant')
    
    # Construct Database URI (supports DATABASE_URL override, remote MySQL, or SQLite fallback)
    _custom_db_url = os.environ.get('DATABASE_URL')
    if _custom_db_url and _custom_db_url.strip():
        _url = _custom_db_url.strip()
        if _url.startswith('mysql://'):
            _url = _url.replace('mysql://', 'mysql+pymysql://', 1)
        elif _url.startswith('postgres://'):
            _url = _url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = _url
    elif DB_HOST and DB_HOST != 'localhost':
        _encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ''
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{_encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    elif DB_HOST == 'localhost' and DB_PASSWORD:
        _encoded_password = quote_plus(DB_PASSWORD)
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{_encoded_password}@localhost:{DB_PORT}/{DB_NAME}"
    else:
        _base_dir = os.path.abspath(os.path.dirname(__file__))
        _db_path = os.path.join(_base_dir, 'shopsmart.db')
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{_db_path}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Admin Registration Invite Authorization Code
    ADMIN_INVITE_CODE = os.environ.get('ADMIN_INVITE_CODE', 'change_this_secure_code')

    # AI Configuration
    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'gemini')
    AI_API_KEY = os.environ.get('AI_API_KEY', '')

    # Mail Settings (Password Reset)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() in ('true', '1', 't')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@shopsmart.ai')

    # Razorpay Payment Gateway Configuration (Google Pay / UPI / Cards / Netbanking)
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_shopsmart_key_id')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'rzp_test_shopsmart_secret_key')


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

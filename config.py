import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'foodbridge-hackathon-secure-secret-key-2025')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(basedir, 'instance', 'foodbridge.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads configuration
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    # Impact conversion factors (Transparent, documented formulas)
    # Average adult portion: 400g (0.4 kg) -> 2.5 meals per kg
    MEALS_PER_KG = 2.5
    MEALS_PER_LITER = 2.0
    MEALS_PER_SERVING = 1.0
    CO2_SAVED_PER_KG = 2.5  # kg CO2-equivalent avoided per kg food rescued
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Pagination
    ITEMS_PER_PAGE = 9

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    DEBUG = False

class ProductionConfig(Config):
    DEBUG = False
    # Enforce secure environment variables in production
    SECRET_KEY = os.environ.get('SECRET_KEY')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

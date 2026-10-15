import os
from flask import Flask, render_template
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from config import config
from app.models import db, User, utcnow

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

csrf = CSRFProtect()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Ensure required runtime folders exist safely
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except OSError:
        pass
    try:
        os.makedirs(os.path.join(app.root_path, '..', 'instance'), exist_ok=True)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Exempt api blueprint from CSRF for clean JSON POSTs where requested,
    # or keep CSRF on if preferred. Let's exempt only specific API paths if needed or pass CSRF header.
    # Actually, keep CSRF globally safe and let front-end pass X-CSRFToken.

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.donor import donor_bp
    from app.routes.recipient import recipient_bp
    from app.routes.donations import donations_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(donor_bp)
    app.register_blueprint(recipient_bp)
    app.register_blueprint(donations_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Register custom template filters
    @app.template_filter('datetime_format')
    def datetime_format(value, format='%b %d, %Y at %I:%M %p'):
        if value is None:
            return ""
        return value.strftime(format)

    @app.template_filter('date_format')
    def date_format(value, format='%b %d, %Y'):
        if value is None:
            return ""
        return value.strftime(format)

    @app.template_filter('time_remaining')
    def time_remaining_filter(deadline):
        if not deadline:
            return ""
        diff = deadline - utcnow()
        seconds = diff.total_seconds()
        if seconds <= 0:
            return "Expired"
        hours = seconds / 3600.0
        if hours < 1:
            minutes = int(seconds / 60)
            return f"{minutes} min left"
        elif hours < 24:
            return f"{round(hours, 1)}h left"
        else:
            days = round(hours / 24.0, 1)
            return f"{days} days left"

    @app.template_filter('status_badge')
    def status_badge_filter(status):
        badges = {
            'Available': 'badge-success',
            'Request Pending': 'badge-warning',
            'Accepted': 'badge-primary',
            'Ready for Pickup': 'badge-accent',
            'Collected': 'badge-info',
            'Completed': 'badge-completed',
            'Cancelled': 'badge-danger',
            'Expired': 'badge-secondary',
            'Pending': 'badge-warning',
            'Rejected': 'badge-danger',
            'verified': 'badge-success',
            'pending': 'badge-warning',
            'rejected': 'badge-danger'
        }
        return badges.get(status, 'badge-secondary')

    # Context processors
    @app.context_processor
    def inject_context():
        unread_count = 0
        if current_user.is_authenticated:
            try:
                unread_count = current_user.unread_notifications_count
            except Exception:
                unread_count = 0
        return {
            'unread_notifications_count': unread_count,
            'current_time': utcnow()
        }

    # Error handlers
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app

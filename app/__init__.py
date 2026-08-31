import datetime
from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_mail import Mail
from sqlalchemy.exc import OperationalError
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    @app.route('/health')
    def health():
        return {'status': 'ok'}, 200

    # Global Template Context Processor
    @app.context_processor
    def inject_global_vars():
        cart_count = 0
        wishlist_count = 0
        compare_count = len(session.get('compare_ids', []))

        if current_user.is_authenticated:
            from app.models.cart import CartItem
            from app.models.wishlist import WishlistItem
            try:
                cart_count = db.session.query(db.func.sum(CartItem.quantity)).filter_by(user_id=current_user.id).scalar() or 0
                wishlist_count = WishlistItem.query.filter_by(user_id=current_user.id).count()
            except Exception:
                pass
        else:
            cart = session.get('cart', {})
            cart_count = sum(item.get('quantity', 1) for item in cart.values())

        return {
            'current_year': datetime.datetime.now().year,
            'cart_count': cart_count,
            'wishlist_count': wishlist_count,
            'compare_count': compare_count
        }

    # Error Handlers
    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template('errors/400.html'), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        return render_template('errors/401.html'), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(OperationalError)
    def db_connection_error(error):
        db.session.rollback()
        db_host = app.config.get('DB_HOST', 'localhost')
        db_name = app.config.get('DB_NAME', 'defaultdb')
        db_user = app.config.get('DB_USER', 'avnadmin')
        db_port = app.config.get('DB_PORT', '3306')
        return render_template('errors/db_error.html', error=error, db_host=db_host, db_name=db_name, db_user=db_user, db_port=db_port), 500

    return app

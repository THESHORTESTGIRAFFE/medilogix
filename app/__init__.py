from flask import Flask, redirect, url_for, render_template
import logging
from flask_login import LoginManager, current_user
from .models import User # Import User model
import datetime # Import datetime module

def create_app(config_class='config.Config'):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Configure logging
    logging.basicConfig(level=logging.INFO) # Basic logging configuration
    if not app.debug and not app.testing:
        # More sophisticated logging for production can be added here
        # For example, logging to a file:
        # from logging.handlers import RotatingFileHandler
        # file_handler = RotatingFileHandler('sams_app.log', maxBytes=10240, backupCount=10)
        # file_handler.setFormatter(logging.Formatter(
        #    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        # ))
        # file_handler.setLevel(logging.INFO)
        # app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
    else:
        app.logger.setLevel(logging.DEBUG) # More verbose logging in debug mode

    app.logger.info('SAMS application starting up...')

    # db.py is at the project root. Import it directly.
    import db as project_db_module # Using an alias for clarity
    project_db_module.init_app(app)
    # Initialize Flask-Login (to be fully implemented in auth phase)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login_page' # The route name for your login page
    login_manager.login_message_category = "info"

    # Register Blueprints
    from .routes import auth as auth_bp
    from .routes import main as main_bp # Import the new main blueprint
    from .routes import inventory as inventory_bp # Import inventory blueprint
    from .routes import locations as locations_bp # Import locations blueprint
    from .routes import stock as stock_bp # Import stock blueprint
    from .routes import requisitions as requisitions_bp # Import requisitions blueprint
    from .routes import account as account_bp # Import account blueprint
    from .routes import admin as admin_bp # Import admin blueprint
    from .routes import assets as assets_bp # Import assets blueprint
    from .routes import transfers as transfers_bp # Import transfers blueprint
    from .routes import suppliers as suppliers_bp # Import suppliers blueprint
    from .routes import purchase_orders as purchase_orders_bp # Import purchase_orders blueprint
    from .routes import grns as grns_bp # Import grns blueprint

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('main.dashboard'))
        total_requisition_items = project_db_module.query_db("SELECT COUNT(*) as count FROM requisition_items;", one=True)['count']
        total_users = project_db_module.query_db("SELECT COUNT(*) as count FROM users WHERE is_active = TRUE;", one=True)['count']
        total_locations = project_db_module.query_db("SELECT COUNT(*) as count FROM item_locations;", one=True)['count']
        return render_template('main/landing.html', total_requisition_items=total_requisition_items,
                               total_users=total_users,
                               total_locations=total_locations)
        
        
    @login_manager.user_loader
    def load_user(user_id):
        # This function is now directly responsible for loading the user.
        # It uses the query_db function, so ensure db is available in the app context.
        # Use query_db from the project_db_module imported in the create_app scope
        user_record = project_db_module.query_db("SELECT * FROM users WHERE id = %s", (user_id,), one=True)
        if user_record:
            return User(id=user_record['id'], 
                        username=user_record['username'], 
                        role=user_record['role'],
                        full_name=user_record['full_name'],
                        department_id=user_record['department_id'],
                        email=user_record['email'],
                        is_active=bool(user_record['is_active']),
                        last_login_at=user_record.get('last_login_at')) # Get last_login_at
        return None
    app.register_blueprint(auth_bp.bp) # Register blueprint after login_manager setup
    app.register_blueprint(main_bp.bp) # Register the main blueprint
    app.register_blueprint(inventory_bp.bp) # Register inventory blueprint
    app.register_blueprint(locations_bp.bp) # Register locations blueprint
    app.register_blueprint(stock_bp.bp) # Register stock blueprint
    app.register_blueprint(requisitions_bp.bp) # Register requisitions blueprint
    app.register_blueprint(account_bp.bp) # Register account blueprint
    app.register_blueprint(admin_bp.bp) # Register admin blueprint
    app.register_blueprint(assets_bp.bp) # Register assets blueprint
    app.register_blueprint(transfers_bp.bp) # Register transfers blueprint
    app.register_blueprint(suppliers_bp.bp) # Register suppliers blueprint
    app.register_blueprint(purchase_orders_bp.bp) # Register purchase_orders blueprint
    app.register_blueprint(grns_bp.bp) # Register grns blueprint
    app.register_blueprint(invoices_bp.bp) # Register invoices blueprint

    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.datetime.utcnow().year}

    return app
# Import os needed for db path check in create_app
import os
from flask import Flask
from config import Config
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
import pymysql # Ensure pymysql is imported if not automatically handled by SQLAlchemy
from datetime import datetime, timezone # Import timezone
from markupsafe import Markup
import logging
import sys

# Configure logging to handle potential console issues on Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)


# Explicitly tell SQLAlchemy to use pymysql (though we switched to SQLite, keep for reference)
# pymysql.install_as_MySQLdb()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login" # Use auth blueprint for login
login_manager.login_message_category = "info"
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    Bootstrap(app)
    mail.init_app(app)

    # Initialize app-specific configurations
    config_class.init_app(app)

    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register nl2br filter
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        if not s:
            return ""
        return Markup(s.replace('\n', '<br>\n'))

    # Import and register blueprints
    from app.routes import bp as main_bp
    from app.admin_routes import admin as admin_bp
    from app.assistant_routes import assistant_bp
    from app.auth_routes import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(assistant_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Context processor to inject variables into templates
    @app.context_processor
    def inject_now():
        return {"now": datetime.now(timezone.utc)}

    # Create database tables if they don't exist
    with app.app_context():
        # Check if the database file exists before creating tables
        db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
        if not os.path.exists(db_path):
             print(f"Database file not found at {db_path}. Creating tables...")
             db.create_all()
        else:
             # Optionally check if tables exist, but create_all is safe
             # print("Database file found. Ensuring tables exist...")
             db.create_all() # Safe to call even if tables exist

    return app




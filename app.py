from flask import Flask, render_template, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from config import Config
from models import initialize_db
from blueprints.auth import auth_bp
from blueprints.admin import admin_bp
from werkzeug.utils import secure_filename
import os

# Define the folder where uploads will be stored (relative to app.py)
UPLOAD_FOLDER = 'kyc_doc'
ALLOWED_EXTENSIONS = {'jpg'} # Only allow PNG

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
# Configure upload folder
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    # Create the folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # Initialize CORS for API access
    CORS(app) 
    # ... other initializations ...

    # --- Frontend HTML Routes (for demonstration) ---
    # Add a route to serve the uploaded files securely
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        # This is a crucial security step: ensure the file is within the UPLOAD_FOLDER
        from flask import send_from_directory
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Initialize Database
    initialize_db(app)

    # Initialize Rate Limiter
    limiter = Limiter(
        key_func=get_remote_address,
        app=app
    )
    # The limiter object must be passed to blueprints if decorators are used there, 
    # but the global default limit is already applied.

    # Register Blueprints for modularity
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # --- Frontend HTML Routes (for demonstration) ---
    @app.route('/')
    def index():
        return render_template('register.html')

    @app.route('/login')
    def login_page():
        return render_template('login.html')

    @app.route('/profile')
    def profile_page():
        return render_template('profile.html')

    @app.route('/kyc')
    def kyc_page():
        return render_template('upload_kyc.html')

    @app.route('/admin')
    def admin_page():
        return render_template('admin_dashboard.html')

    # Example Admin User Creation (Run this once manually)
    @app.cli.command("create-admin")
    def create_admin():
        from models import get_users_collection, find_user_by_email
        from blueprints.auth import hash_password
        from datetime import datetime, timezone
        import getpass

        print("--- Creating Initial Bank Admin User ---")
        admin_email = input("Enter Admin Email: ")
        admin_password = getpass.getpass("Enter Admin Password: ")
        admin_name = input("Enter Admin Name: ")
        
        if find_user_by_email(admin_email):
            print("Admin user already exists.")
            return

        hashed_password = hash_password(admin_password)

        admin_data = {
            "name": admin_name,
            "email": admin_email,
            "password": hashed_password,
            "kyc_status": "APPROVED",
            "kyc_document": "Internal Admin Record",
            "is_admin": True,
            "created_at": datetime.now(timezone.utc)
        }
        
        get_users_collection().insert_one(admin_data)
        print(f"Admin user '{admin_email}' created successfully!")
        
    return app

if __name__ == '__main__':
    app = create_app()
    # To run: flask run
    # To create admin: flask create-admin
    app.run(debug=True)
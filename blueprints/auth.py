import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Blueprint, request, jsonify, current_app, make_response
from models import find_user_by_email, get_users_collection, find_user_by_id
from flask_limiter import Limiter, util
from werkzeug.utils import secure_filename
import os

auth_bp = Blueprint('auth', __name__, url_prefix='/api')
# Helper function to check allowed extensions
ALLOWED_EXTENSIONS = {'jpg'} # Only allow PNG
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
# Decorator for JWT required
def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check for token in 'Authorization' header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # Decode token using the app's secret key
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            # Find the user in the database
            current_user = find_user_by_id(data['user_id'])
            if current_user is None:
                 return jsonify({'message': 'Token is invalid or user deleted!'}), 401
        except jwt.ExpiredSignatureError:
             return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)

    return decorated

# Helper to hash password
def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

# Helper to check password
def check_password(hashed_password, password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

# 1. POST /api/register
@auth_bp.route('/register', methods=['POST'])
# Rate limiting example (1 per minute per IP)
# @limiter.limit("1/minute") 
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')

    if not email or not password or not name:
        return jsonify({'message': 'Missing email, name, or password'}), 400

    if find_user_by_email(email):
        return jsonify({'message': 'User already exists with that email'}), 409

    hashed_password = hash_password(password)

    user_data = {
        "name": name,
        "email": email,
        "password": hashed_password,
        "kyc_status": "PENDING", # PENDING, REVIEWING, APPROVED, REJECTED
        "kyc_document": None,
        "is_admin": False,
        "created_at": datetime.now(timezone.utc)
    }

    try:
        result = get_users_collection().insert_one(user_data)
        return jsonify({
            'message': 'Registration successful. Please login and complete KYC.', 
            'user_id': str(result.inserted_id)
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error during registration: {e}")
        return jsonify({'message': 'Registration failed due to server error.'}), 500

# 2. POST /api/login
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = find_user_by_email(email)

    if user and check_password(user['password'], password):
        # User is authenticated. Create JWT.
        
        # We need to convert ObjectId to string for JWT payload
        user_id_str = str(user['_id'])
        
        payload = {
            'user_id': user_id_str,
            'is_admin': user.get('is_admin', False),
            'exp': datetime.now(timezone.utc) + timedelta(hours=24) # Token expires in 24 hours
        }

        token = jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            'message': 'Login successful', 
            'token': token,
            'user_id': user_id_str,
            'is_admin': user.get('is_admin', False),
            'kyc_status': user.get('kyc_status')
        }), 200
    else:
        # Authentication failed
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

# 3. POST /api/upload_kyc
@auth_bp.route('/upload_kyc', methods=['POST'])
@jwt_required
def upload_kyc(current_user):
    # Check if a file was included in the request
    if 'kyc_file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400
    
    file = request.files['kyc_file']
    
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # 1. Secure the filename
        filename = secure_filename(file.filename)
        # Prepend user ID to ensure uniqueness and link to user
        user_id_str = str(current_user['_id'])
        final_filename = f"{user_id_str}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        
        # 2. Save the file to the UPLOAD_FOLDER
        try:
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], final_filename)
            file.save(save_path)
        except Exception as e:
            current_app.logger.error(f"File save error: {e}")
            return jsonify({'message': 'Failed to save file on server.'}), 500

        # 3. Update the user's document path in MongoDB
        document_url = f"/uploads/{final_filename}" # This is the link to serve the file
        
        if current_user['kyc_status'] == 'APPROVED':
            return jsonify({'message': 'KYC already approved. Re-submission not allowed.'}), 400

        try:
            get_users_collection().update_one(
                {"_id": current_user['_id']},
                {
                    "$set": {
                        "kyc_document": document_url,
                        "kyc_status": "REVIEWING",
                        "kyc_submitted_at": datetime.now(timezone.utc)
                    }
                }
            )
            return jsonify({'message': 'KYC document submitted successfully. Status updated to REVIEWING.', 'filename': final_filename}), 200
        except Exception as e:
            current_app.logger.error(f"Error during KYC upload database update: {e}")
            return jsonify({'message': 'KYC submission failed.'}), 500
    else:
        return jsonify({'message': 'Invalid file type. Only PNG is allowed.'}), 400

# 4. GET /api/profile
@auth_bp.route('/profile', methods=['GET'])
@jwt_required
def get_profile(current_user):
    # Sanitize the user data before sending
    profile = {
        'user_id': str(current_user['_id']),
        'name': current_user['name'],
        'email': current_user['email'],
        'kyc_status': current_user['kyc_status'],
        'kyc_document': current_user['kyc_document'] if current_user['kyc_document'] else 'Not Uploaded',
        'is_admin': current_user.get('is_admin', False)
    }
    # Remove the hashed password
    # profile.pop('password', None)
    
    return jsonify(profile), 200
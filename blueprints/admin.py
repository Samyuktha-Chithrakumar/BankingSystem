from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from blueprints.auth import jwt_required
from models import get_users_collection, find_user_by_id
from datetime import datetime, timezone
from bson.objectid import ObjectId
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from blueprints.auth import jwt_required
from models import get_users_collection

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Decorator to ensure the authenticated user is an Admin
def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not current_user.get('is_admin', False):
            return jsonify({'message': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

# 6. GET /api/admin/pending_kyc
@admin_bp.route('/pending_kyc', methods=['GET'])
@jwt_required
@admin_required
def get_pending_kyc(current_user):
    try:
        # Find all users whose kyc_status is PENDING or REVIEWING
        pending_users = get_users_collection().find(
            {"kyc_status": {"$in": ["PENDING", "REVIEWING"]}, "is_admin": False},
            {"name": 1, "email": 1, "kyc_status": 1, "kyc_document": 1, "kyc_submitted_at": 1}
        ).sort("kyc_submitted_at", 1) # Sort by submission time

        result = []
        for user in pending_users:
            result.append({
                'user_id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'status': user['kyc_status'],
                'document_link': user.get('kyc_document', 'N/A'),
                'submitted_at': user.get('kyc_submitted_at').isoformat() if user.get('kyc_submitted_at') else 'N/A'
            })
            
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching pending KYC: {e}")
        return jsonify({'message': 'Failed to fetch pending KYC list.'}), 500

# 7. GET /api/admin/users (NEW ENDPOINT)
@admin_bp.route('/users', methods=['GET'])
@jwt_required
@admin_required
def get_all_users(current_user):
    try:
        # Find all users who are NOT admins
        all_users = get_users_collection().find(
            {"is_admin": {"$ne": True}},
            # Project only the necessary fields (excluding password)
            {"name": 1, "email": 1, "kyc_status": 1, "kyc_document": 1, "created_at": 1}
        ).sort("created_at", -1) # Sort newest first

        result = []
        for user in all_users:
            result.append({
                'user_id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'status': user['kyc_status'],
                'document_link': user.get('kyc_document', 'N/A'),
                'joined_at': user.get('created_at').isoformat() if user.get('created_at') else 'N/A'
            })
            
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching all users: {e}")
        return jsonify({'message': 'Failed to fetch the full user list.'}), 500

# 5. PATCH /api/admin/verify_kyc/<user_id>
@admin_bp.route('/verify_kyc/<user_id>', methods=['PATCH'])
@jwt_required
@admin_required
def verify_kyc(current_user, user_id):
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['APPROVED', 'REJECTED']:
        return jsonify({'message': 'Invalid status. Must be APPROVED or REJECTED.'}), 400

    try:
        # Ensure user_id is a valid ObjectId
        target_user = find_user_by_id(user_id)
    except:
        return jsonify({'message': 'Invalid user ID format.'}), 400

    if not target_user or target_user.get('is_admin'):
        return jsonify({'message': 'User not found or is an Admin.'}), 404

    # Update the user's KYC status
    try:
        result = get_users_collection().update_one(
            {"_id": target_user['_id']},
            {
                "$set": {
                    "kyc_status": new_status,
                    "kyc_verified_by_admin_id": str(current_user['_id']),
                    "kyc_verification_date": datetime.now(timezone.utc)
                }
            }
        )

        if result.modified_count == 1:
            return jsonify({
                'message': f'KYC for user {target_user["email"]} updated to {new_status}.',
                'user_id': user_id
            }), 200
        else:
            return jsonify({'message': 'User found, but KYC status not modified (perhaps already set).'}), 200

    except Exception as e:
        current_app.logger.error(f"Error during KYC verification: {e}")
        return jsonify({'message': 'KYC verification failed due to server error.'}), 500
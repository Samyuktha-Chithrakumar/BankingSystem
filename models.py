from flask_pymongo import PyMongo
from flask import current_app

mongo = PyMongo()

def initialize_db(app):
    """Initializes the MongoDB connection."""
    app.config["MONGO_URI"] = app.config["MONGO_URI"]
    mongo.init_app(app)

def get_users_collection():
    """Returns the MongoDB 'users' collection."""
    if not hasattr(mongo, 'db') or mongo.db is None:
        # Fallback for when current_app is not available (e.g., in a test)
        raise RuntimeError("Database not initialized or accessible.")
    return mongo.db.users

# --- Helper Functions for Database Interaction ---

def find_user_by_email(email):
    """Finds a user by email."""
    return get_users_collection().find_one({"email": email})

def find_user_by_id(user_id):
    """Finds a user by MongoDB ObjectId string."""
    from bson.objectid import ObjectId
    try:
        return get_users_collection().find_one({"_id": ObjectId(user_id)})
    except:
        return None
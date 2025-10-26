import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # MongoDB Configuration
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/kyc_db")
    
    # Security/Auth Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "SECRET@2025") 
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "JWT@2025")
    
    # Rate Limiting Configuration (using in-memory storage for simplicity)
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "200 per day; 50 per hour"
    ALLOWED_EXTENSIONS = {'jpg'} # Define the allowed file types here

# Example .env file content:
# MONGO_URI="mongodb://localhost:27017/kyc_db"
# SECRET_KEY="a_secure_app_key_here"
# JWT_SECRET_KEY="a_secure_jwt_key_here"
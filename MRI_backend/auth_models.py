"""
Auth models for MRI backend.
"""
import os
from pymongo import MongoClient
import bcrypt
from datetime import datetime

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://mongodb:27017/")
MONGO_DB = os.environ.get("MONGO_DB", "MRI")
MONGO_USERS_COLLECTION = "users"

_coll = None

def _get_coll():
    global _coll
    if _coll is None:
        c = MongoClient(MONGO_URI)
        _coll = c[MONGO_DB][MONGO_USERS_COLLECTION]
        _coll.create_index("username", unique=True)
        _coll.create_index("email", unique=True)
    return _coll

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

def create_user(username, email, password):
    coll = _get_coll()
    if coll.find_one({"username": username}):
        raise ValueError("username exists")
    if coll.find_one({"email": email}):
        raise ValueError("email exists")
    doc = {"username": username, "email": email, "password_hash": hash_password(password), "created_at": datetime.utcnow(), "last_login": None}
    result = coll.insert_one(doc)
    return {"username": username, "email": email, "created_at": doc["created_at"].isoformat()}

def get_user_by_username(username):
    """Get user without password_hash (for public display)"""
    return _get_coll().find_one({"username": username}, {"password_hash": 0})

def get_user_with_password(username):
    """Get user WITH password_hash (for authentication)"""
    return _get_coll().find_one({"username": username})

def get_user_by_email(email):
    return _get_coll().find_one({"email": email}, {"password_hash": 0})

def update_last_login(username):
    _get_coll().update_one({"username": username}, {"$set": {"last_login": datetime.utcnow()}})

"""Authentication middleware using credential database."""
from functools import wraps
from typing import Optional, Dict, Any

import requests
from flask import request, jsonify, session

from .config import settings


def verify_credentials(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Verify credentials against the credential database API.
    Returns user info if authenticated, None otherwise.
    """
    try:
        response = requests.post(
            f"{settings.credential_db_url}/verify",
            json={"username": username, "password": password},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("user"):
                return {
                    "id": data["user"]["id"],
                    "username": data["user"]["username"],
                    "authenticated": True
                }
        
        return None
    except Exception as e:
        print(f"Error verifying credentials: {e}")
        return None


def check_session() -> Optional[Dict[str, Any]]:
    """
    Check Flask session for authenticated user.
    Returns user info if authenticated, None otherwise.
    """
    if session.get("authenticated") and session.get("user_id"):
        return {
            "id": session.get("user_id"),
            "username": session.get("username"),
            "authenticated": True
        }
    return None


def require_auth(f):
    """
    Decorator to require authentication for a route.
    Checks Flask session for authenticated user.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_info = check_session()
        
        if not user_info:
            # No valid session - return 401 with redirect info
            return jsonify({
                "error": "Unauthorized",
                "redirect": "/login"
            }), 401
        
        # Add user_info to kwargs so routes can access it
        kwargs['user_info'] = user_info
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get current user info without requiring auth.
    Useful for optional authentication.
    """
    return check_session()

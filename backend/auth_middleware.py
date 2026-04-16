"""Authentication middleware using shared THIS Nexus auth sessions."""
from functools import wraps
from hashlib import sha256
import base64
import hmac
import json
from typing import Optional, Dict, Any
from urllib.parse import urlencode

from flask import request, jsonify, session

from .config import settings


def _normalize_base64url(value: str) -> str:
    return value.replace("-", "+").replace("_", "/")


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _base64url_decode(value: str) -> str:
    normalized = _normalize_base64url(value)
    padding = len(normalized) % 4
    if padding:
        normalized += "=" * (4 - padding)
    return base64.b64decode(normalized).decode("utf-8")


def _sign_value(value: str) -> str:
    if not settings.auth_session_secret:
        raise RuntimeError("AUTH_SESSION_SECRET is required")
    digest = hmac.new(
        settings.auth_session_secret.encode("utf-8"),
        value.encode("utf-8"),
        sha256,
    ).digest()
    return _base64url_encode(digest)


def verify_auth_session_token(token: str | None) -> Optional[Dict[str, Any]]:
    """Verify the shared THIS Nexus auth cookie."""
    if not token or "." not in token:
        return None

    encoded_payload, signature = token.split(".", 1)
    expected_signature = _sign_value(encoded_payload)

    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        payload = json.loads(_base64url_decode(encoded_payload))
        exp = payload.get("exp")
        if exp and int(exp) * 1000 < __import__("time").time() * 1000:
            return None
        return payload
    except Exception:
        return None


def is_teacher_auth_session(auth_session: Optional[Dict[str, Any]]) -> bool:
    return bool(auth_session) and auth_session.get("role") != "student"


def _normalize_user_info(auth_session: Dict[str, Any]) -> Dict[str, Any]:
    email = str(auth_session.get("email") or "").strip().lower() or None
    display_name = str(auth_session.get("name") or "").strip() or None
    username = (
        str(auth_session.get("username") or "").strip()
        or display_name
        or email
        or "Teacher"
    )

    return {
        "id": email or username,
        "username": username,
        "display_name": display_name or username,
        "email": email,
        "authenticated": True,
        "auth_method": auth_session.get("authMethod") or "microsoft",
    }


def establish_local_session(auth_session: Dict[str, Any]) -> Dict[str, Any]:
    user_info = _normalize_user_info(auth_session)
    session["authenticated"] = True
    session["user_id"] = user_info["id"]
    session["username"] = user_info["username"]
    session["display_name"] = user_info["display_name"]
    session["email"] = user_info["email"]
    session["auth_method"] = user_info["auth_method"]
    return user_info


def clear_local_session() -> None:
    session.clear()


def get_shared_auth_session() -> Optional[Dict[str, Any]]:
    token = request.cookies.get(settings.session_cookie_name)
    return verify_auth_session_token(token)


def build_microsoft_login_url(redirect_path: str = "/") -> str:
    callback_url = f"{settings.translate_base_url.rstrip('/')}/api/auth/microsoft?redirect={redirect_path}"
    return f"{settings.auth_service_base_url.rstrip('/')}/api/auth/microsoft?{urlencode({'returnTo': callback_url})}"


def build_logout_url(return_path: str = "/login") -> str:
    return_to = f"{settings.translate_base_url.rstrip('/')}{return_path}"
    return f"{settings.auth_service_base_url.rstrip('/')}/api/auth/logout?{urlencode({'returnTo': return_to})}"


def check_session() -> Optional[Dict[str, Any]]:
    """Check local session first, then fall back to the shared THIS Nexus cookie."""
    if session.get("authenticated") and session.get("user_id"):
        return {
            "id": session.get("user_id"),
            "username": session.get("username"),
            "display_name": session.get("display_name") or session.get("username"),
            "email": session.get("email"),
            "authenticated": True,
            "auth_method": session.get("auth_method") or "microsoft",
        }

    shared_session = get_shared_auth_session()
    if not shared_session or not is_teacher_auth_session(shared_session):
        clear_local_session()
        return None

    return establish_local_session(shared_session)

    return None


def require_auth(f):
    """Decorator to require a valid teacher auth session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_info = check_session()

        if not user_info:
            return jsonify({
                "error": "Unauthorized",
                "redirect": "/login"
            }), 401

        kwargs['user_info'] = user_info
        return f(*args, **kwargs)

    return decorated_function


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current teacher session, if any."""
    return check_session()

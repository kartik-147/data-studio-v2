"""
DATA STUDIO v2 — User Storage Abstraction Layer (Module 5)
=============================================================================
Decoupled local JSON-based user storage repository for development.
Designed with a clean interface that can later be replaced with
Firebase, Supabase, or PostgreSQL without altering the authentication UI.
"""
import os
import json
import uuid
import datetime
from typing import Optional, Dict, Any, List

# Base Storage Directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(BASE_DIR, "user_data")
USERS_FILE = os.path.join(STORAGE_DIR, "users_db.json")


def init_storage() -> None:
    """Ensure the user storage directory and JSON database file exist."""
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR, exist_ok=True)

    if not os.path.exists(USERS_FILE):
        initial_data = {
            "version": "1.0",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "users": []
        }
        _write_db(initial_data)


def _read_db() -> Dict[str, Any]:
    """Read the user database JSON file safely."""
    init_storage()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # Return fallback empty structure
        return {"version": "1.0", "users": []}


def _write_db(data: Dict[str, Any]) -> bool:
    """Write user database safely."""
    try:
        temp_file = f"{USERS_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Atomic replace
        if os.path.exists(USERS_FILE):
            os.replace(temp_file, USERS_FILE)
        else:
            os.rename(temp_file, USERS_FILE)
        return True
    except Exception as e:
        print(f"[UserStorage Error] Failed to write DB: {e}")
        return False


def get_all_users() -> List[Dict[str, Any]]:
    """Retrieve all stored user records."""
    db = _read_db()
    return db.get("users", [])


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve user record by email address (case-insensitive).
    Returns user dict if found, None otherwise.
    """
    if not email:
        return None
    normalized_email = email.strip().lower()
    users = get_all_users()
    for user in users:
        if user.get("email", "").strip().lower() == normalized_email:
            return user
    return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve user record by unique user_id."""
    if not user_id:
        return None
    users = get_all_users()
    for user in users:
        if user.get("user_id") == user_id:
            return user
    return None


def email_exists(email: str) -> bool:
    """Check if an email address is already registered."""
    return get_user_by_email(email) is not None


def save_user(full_name: str, email: str, password_hash: str) -> Optional[Dict[str, Any]]:
    """
    Create and persist a new user record.
    Never stores plaintext passwords.
    Returns the created user record (excluding sensitive internal fields if needed).
    """
    db = _read_db()
    users = db.get("users", [])
    
    normalized_email = email.strip().lower()
    
    # Double check uniqueness
    for u in users:
        if u.get("email", "").strip().lower() == normalized_email:
            return None

    new_user = {
        "user_id": f"usr_{uuid.uuid4().hex[:12]}",
        "full_name": full_name.strip(),
        "email": normalized_email,
        "password_hash": password_hash,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    users.append(new_user)
    db["users"] = users
    
    if _write_db(db):
        return new_user
    return None


def get_or_create_google_user(
    email: str,
    full_name: str,
    google_id: str,
    picture: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Retrieve an existing user by email or register a new Google-authenticated user.
    Sets auth_provider to 'google' and stores Google metadata.
    """
    if not email:
        return None
    normalized_email = email.strip().lower()
    
    existing = get_user_by_email(normalized_email)
    if existing:
        # Update google metadata if needed
        db = _read_db()
        users = db.get("users", [])
        for u in users:
            if u.get("email", "").strip().lower() == normalized_email:
                u["google_id"] = google_id
                u["picture"] = picture or u.get("picture", "")
                u["auth_provider"] = "google"
                u["last_login_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                if not u.get("full_name") and full_name:
                    u["full_name"] = full_name.strip()
                _write_db(db)
                return u
        return existing

    # Create new Google user
    db = _read_db()
    users = db.get("users", [])
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    new_user = {
        "user_id": f"usr_g_{uuid.uuid4().hex[:10]}",
        "full_name": full_name.strip() if full_name else normalized_email.split("@")[0],
        "email": normalized_email,
        "password_hash": None, # Google OAuth users do not use local password
        "auth_provider": "google",
        "google_id": google_id,
        "picture": picture,
        "created_at": now_iso,
        "last_login_at": now_iso
    }
    users.append(new_user)
    db["users"] = users
    if _write_db(db):
        return new_user
    return None


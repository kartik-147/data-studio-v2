"""
DATA STUDIO v2 — Authentication and Security Architecture (Module 5)
=============================================================================
Provides secure password hashing (bcrypt), account registration, credential
verification, session lifecycle management, and guest session handling.
"""
import re
from typing import Optional, Dict, Any, Tuple
import streamlit as st
import bcrypt

from modules.user_storage import (
    init_storage,
    get_user_by_email,
    email_exists,
    save_user
)

# Email Regex Pattern
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
MIN_PASSWORD_LENGTH = 8


def initialize_auth_storage() -> None:
    """Initialize the backend user repository."""
    init_storage()


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt with a secure salt.
    Returns the utf-8 decoded hash string.
    """
    if not password:
        return ""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Safely verify a plaintext password against a stored bcrypt hash.
    Constant-time comparison prevents timing attacks.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def validate_email_format(email: str) -> bool:
    """Validate that the provided string matches a standard email format."""
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password requirements.
    Must be at least 8 characters long.
    """
    if not password:
        return False, "Password cannot be blank."
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
    return True, ""


def register_user(
    full_name: str,
    email: str,
    password: str,
    confirm_password: str
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Register a new user account with validation and bcrypt hashing.
    Never stores plaintext passwords.
    
    Returns:
        (success: bool, message: str, user_info: Optional[Dict])
    """
    # 1. Required field checks
    if not full_name or not full_name.strip():
        return False, "Please enter your full name.", None
    if not email or not email.strip():
        return False, "Please enter a valid email address.", None
    if not password:
        return False, "Please enter a password.", None
    if not confirm_password:
        return False, "Please confirm your password.", None

    cleaned_name = full_name.strip()
    cleaned_email = email.strip().lower()

    # 2. Email format validation
    if not validate_email_format(cleaned_email):
        return False, "Invalid email format. Please provide a valid address.", None

    # 3. Password match validation
    if password != confirm_password:
        return False, "Passwords do not match. Please verify and try again.", None

    # 4. Password strength validation
    valid_pwd, pwd_msg = validate_password_strength(password)
    if not valid_pwd:
        return False, pwd_msg, None

    # 5. Email uniqueness check
    initialize_auth_storage()
    if email_exists(cleaned_email):
        return False, "An account with this email address already exists.", None

    # 6. Hash password and persist
    pwd_hash = hash_password(password)
    new_user = save_user(
        full_name=cleaned_name,
        email=cleaned_email,
        password_hash=pwd_hash
    )

    if not new_user:
        return False, "An unexpected error occurred while creating your account. Please try again.", None

    # Safe user payload for session
    user_info = {
        "user_id": new_user["user_id"],
        "full_name": new_user["full_name"],
        "email": new_user["email"]
    }

    return True, "Account created successfully! You can now sign in.", user_info


def authenticate_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Authenticate user credentials against stored bcrypt hashes.
    Uses generic error messages to avoid revealing whether an email exists.
    
    Returns:
        (success: bool, message: str, user_info: Optional[Dict])
    """
    if not email or not email.strip():
        return False, "Please enter your email address.", None
    if not password:
        return False, "Please enter your password.", None

    cleaned_email = email.strip().lower()
    if not validate_email_format(cleaned_email):
        return False, "Invalid email format.", None

    initialize_auth_storage()
    user = get_user_by_email(cleaned_email)

    # Generic rejection if user not found or password does not match
    if not user or not verify_password(password, user.get("password_hash", "")):
        return False, "Invalid email or password.", None

    user_info = {
        "user_id": user["user_id"],
        "full_name": user["full_name"],
        "email": user["email"]
    }

    return True, "Authentication successful.", user_info


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

def is_authenticated() -> bool:
    """Check if the active session is currently authenticated."""
    return bool(st.session_state.get("authenticated", False))


def get_current_user() -> Dict[str, Any]:
    """Retrieve metadata of the currently authenticated identity."""
    if not is_authenticated():
        return {
            "user_id": "anonymous",
            "full_name": "Anonymous",
            "email": "",
            "is_guest": True,
            "auth_provider": None,
            "authenticated": False
        }

    user_info = st.session_state.get("user_info", {})
    return {
        "user_id": user_info.get("user_id", "usr_unknown"),
        "full_name": user_info.get("full_name", "User"),
        "email": user_info.get("email", ""),
        "is_guest": bool(st.session_state.get("is_guest", False)),
        "auth_provider": st.session_state.get("auth_provider", "email"),
        "authenticated": True
    }


def login_user_session(user_info: Dict[str, Any]) -> None:
    """Establish an authenticated session for a registered user."""
    st.session_state["authenticated"] = True
    st.session_state["auth_provider"] = "email"
    st.session_state["is_guest"] = False
    st.session_state["user_info"] = {
        "user_id": user_info["user_id"],
        "full_name": user_info["full_name"],
        "email": user_info["email"]
    }
    st.session_state["current_page"] = "Overview"


def start_guest_session() -> None:
    """
    Establish an ephemeral guest demo session.
    Guest data exists strictly for the duration of the current session.
    """
    st.session_state["authenticated"] = True
    st.session_state["auth_provider"] = "guest"
    st.session_state["is_guest"] = True
    st.session_state["user_info"] = {
        "user_id": "guest_session",
        "full_name": "Guest User",
        "email": "guest@datastudio.internal"
    }
    st.session_state["current_page"] = "Overview"


def logout_user() -> None:
    """
    Terminate authenticated session, purge user state and clear active dataset.
    Preserves theme preference and system configurations.
    """
    # 1. Clear Authentication State
    st.session_state["authenticated"] = False
    st.session_state["auth_provider"] = None
    st.session_state["user_info"] = None
    st.session_state["is_guest"] = False
    
    # 2. Reset Dataset State
    st.session_state["dataset"] = None
    st.session_state["original_dataset"] = None
    st.session_state["cleaned_dataset"] = None
    st.session_state["dataset_name"] = None
    st.session_state["dataset_metadata"] = None
    st.session_state["dataset_file_type"] = None
    
    # 3. Reset Route to Default
    st.session_state["current_page"] = "Overview"

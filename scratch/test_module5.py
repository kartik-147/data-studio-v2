"""
Automated unit & integration test suite for Module 5 (Authentication & Login)
"""
import os
import sys
import json
import shutil
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from modules.config import init_session_state
from modules.user_storage import (
    init_storage,
    get_all_users,
    get_user_by_email,
    email_exists,
    USERS_FILE,
    STORAGE_DIR
)
from modules.auth import (
    hash_password,
    verify_password,
    validate_email_format,
    validate_password_strength,
    register_user,
    authenticate_user,
    start_guest_session,
    login_user_session,
    logout_user,
    is_authenticated,
    get_current_user
)

def run_tests():
    print("=== STARTING MODULE 5 AUTHENTICATION TEST SUITE ===")

    # 1. Test Password Hashing and Verification
    print("\n--- Test 1: Bcrypt Password Hashing & Verification ---")
    plain_pw = "SuperSecurePassword123!"
    hash1 = hash_password(plain_pw)
    hash2 = hash_password(plain_pw)
    
    assert hash1 != plain_pw, "Password was not hashed!"
    assert hash1 != hash2, "Bcrypt salt should generate unique hashes for the same password!"
    assert hash1.startswith("$2b$") or hash1.startswith("$2a$"), "Invalid bcrypt format!"
    assert verify_password(plain_pw, hash1) is True, "Valid password verification failed!"
    assert verify_password("WrongPassword999", hash1) is False, "Invalid password was incorrectly accepted!"
    assert verify_password("", hash1) is False, "Empty password was incorrectly accepted!"
    assert verify_password(plain_pw, "") is False, "Empty hash was incorrectly accepted!"
    print("Bcrypt password hashing and secure verification verified.")

    # 2. Test Email Format Validation
    print("\n--- Test 2: Email Format Validation ---")
    valid_emails = ["kartik@example.com", "user.name+tag@sub.domain.co", "analyst123@datastudio.io"]
    invalid_emails = ["notanemail", "user@", "@domain.com", "user@domain", "user@.com", ""]
    
    for ve in valid_emails:
        assert validate_email_format(ve) is True, f"Valid email rejected: {ve}"
    for ie in invalid_emails:
        assert validate_email_format(ie) is False, f"Invalid email accepted: {ie}"
    print("Email validation rules verified.")

    # 3. Test Password Strength Validation
    print("\n--- Test 3: Password Strength Validation ---")
    valid_pws = ["12345678", "ValidPassword2026", "a" * 50]
    invalid_pws = ["short", "1234567", "", None]
    
    for vp in valid_pws:
        ok, _ = validate_password_strength(vp)
        assert ok is True, f"Valid password rejected: {vp}"
    for ip in invalid_pws:
        ok, _ = validate_password_strength(ip)
        assert ok is False, f"Invalid password accepted: {ip}"
    print("Password strength requirements verified (min 8 chars).")

    # 4. Test User Storage & Registration
    print("\n--- Test 4: Account Registration & Storage ---")
    # Clean test DB
    if os.path.exists(USERS_FILE):
        os.remove(USERS_FILE)
    init_storage()

    # 4a. Successful registration
    success, msg, user_info = register_user(
        full_name="Kartik Bendre",
        email="kartik@example.com",
        password="MySecretPassword123",
        confirm_password="MySecretPassword123"
    )
    assert success is True, f"Registration failed: {msg}"
    assert user_info["email"] == "kartik@example.com"
    assert user_info["full_name"] == "Kartik Bendre"
    assert "password" not in user_info and "password_hash" not in user_info
    print("User registered successfully.")

    # 4b. Verify Database Record
    stored_user = get_user_by_email("kartik@example.com")
    assert stored_user is not None, "Stored user not found in database!"
    assert stored_user["email"] == "kartik@example.com"
    assert stored_user["password_hash"] != "MySecretPassword123", "Plaintext password stored in DB!"
    assert verify_password("MySecretPassword123", stored_user["password_hash"]) is True
    print("Database security verified: only bcrypt hash stored.")

    # 4c. Duplicate email rejection
    dup_ok, dup_msg, _ = register_user(
        full_name="Kartik Duplicate",
        email="KARTIK@EXAMPLE.COM", # Case-insensitivity check
        password="AnotherPassword123",
        confirm_password="AnotherPassword123"
    )
    assert dup_ok is False, "Duplicate email was allowed to register!"
    assert "already exists" in dup_msg
    print("Duplicate email prevention verified.")

    # 4d. Password mismatch rejection
    mismatch_ok, mismatch_msg, _ = register_user(
        full_name="User Two",
        email="user2@example.com",
        password="PasswordOne123",
        confirm_password="PasswordTwo123"
    )
    assert mismatch_ok is False, "Password mismatch was allowed!"
    assert "do not match" in mismatch_msg
    print("Password mismatch rejection verified.")

    # 5. Test Authentication
    print("\n--- Test 5: Credential Authentication ---")
    # Correct login
    auth_ok, auth_msg, auth_user = authenticate_user("kartik@example.com", "MySecretPassword123")
    assert auth_ok is True, f"Correct login failed: {auth_msg}"
    assert auth_user["email"] == "kartik@example.com"
    print("Valid user login verified.")

    # Wrong password
    wrong_pw_ok, wrong_pw_msg, _ = authenticate_user("kartik@example.com", "WrongPassword123")
    assert wrong_pw_ok is False, "Wrong password was accepted!"
    assert wrong_pw_msg == "Invalid email or password."
    print("Wrong password rejection verified.")

    # Non-existent user
    no_user_ok, no_user_msg, _ = authenticate_user("ghost@example.com", "MySecretPassword123")
    assert no_user_ok is False, "Non-existent user was accepted!"
    assert no_user_msg == "Invalid email or password."
    print("Non-existent user rejection verified (generic error message).")

    # 6. Test Session State & Lifecycle Management
    print("\n--- Test 6: Session Management & Guest Demo Mode ---")
    # Initialize mock session state
    init_session_state()
    st.session_state["theme"] = "Light" # Custom theme
    st.session_state["dataset"] = "MockDataFrame" # Mock active dataset

    assert is_authenticated() is False, "Initial state should not be authenticated"

    # Log in as registered user
    login_user_session(auth_user)
    assert is_authenticated() is True
    assert st.session_state["auth_provider"] == "email"
    assert st.session_state["is_guest"] is False
    current_u = get_current_user()
    assert current_u["email"] == "kartik@example.com"
    print("Registered user session lifecycle verified.")

    # Logout
    logout_user()
    assert is_authenticated() is False
    assert st.session_state["user_info"] is None
    assert st.session_state["dataset"] is None, "Dataset state was not purged on logout!"
    assert st.session_state["theme"] == "Light", "Theme preference was not preserved on logout!"
    print("Logout cleanup verified: auth and dataset state purged, theme preserved.")

    # Guest Demo Session
    start_guest_session()
    assert is_authenticated() is True
    assert st.session_state["auth_provider"] == "guest"
    assert st.session_state["is_guest"] is True
    guest_u = get_current_user()
    assert guest_u["full_name"] == "Guest User"
    print("Guest demo session verified.")

    # Logout from guest
    logout_user()
    assert is_authenticated() is False
    print("Guest logout verified.")

    print("\n=== ALL MODULE 5 AUTHENTICATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()

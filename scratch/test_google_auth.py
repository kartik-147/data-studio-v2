"""
Automated unit & integration test suite for Google Authentication (Google OAuth 2.0)
"""
import os
import sys
import json
import urllib.parse
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from modules.config import init_session_state
from modules.user_storage import (
    init_storage,
    get_all_users,
    get_user_by_email,
    get_or_create_google_user,
    USERS_FILE
)
from modules.auth import (
    login_user_session,
    logout_user,
    is_authenticated,
    get_current_user
)
from modules.google_auth import (
    get_google_oauth_config,
    is_google_auth_configured,
    get_google_auth_url,
    exchange_code_for_token,
    fetch_google_user_profile,
    handle_google_oauth_callback,
    GOOGLE_AUTH_ENDPOINT
)
from modules.firebase_service import is_admin_user


def run_google_auth_tests():
    print("=== STARTING GOOGLE AUTHENTICATION TEST SUITE ===")

    # 1. Test Default / Unconfigured State (No Auto-Admin Login)
    print("\n--- Test 1: Unconfigured Google OAuth State ---")
    # Ensure env vars are clean for test
    os.environ.pop("GOOGLE_CLIENT_ID", None)
    os.environ.pop("GOOGLE_CLIENT_SECRET", None)

    cfg = get_google_oauth_config()
    assert cfg["is_configured"] is False, "Should be unconfigured when credentials are missing"
    assert is_google_auth_configured() is False

    auth_url = get_google_auth_url()
    assert auth_url is None, "Auth URL should be None when unconfigured"
    print("Unconfigured state correctly handled (no auth URL generated).")

    # 2. Test Configured State and URL Construction
    print("\n--- Test 2: Google OAuth URL Generation ---")
    os.environ["GOOGLE_CLIENT_ID"] = "test-client-id-123.apps.googleusercontent.com"
    os.environ["GOOGLE_CLIENT_SECRET"] = "test-client-secret-xyz"
    os.environ["GOOGLE_REDIRECT_URI"] = "http://localhost:8501"

    cfg = get_google_oauth_config()
    assert cfg["is_configured"] is True
    assert cfg["client_id"] == "test-client-id-123.apps.googleusercontent.com"
    assert is_google_auth_configured() is True

    auth_url = get_google_auth_url(state="secure_state_token")
    assert auth_url is not None
    assert auth_url.startswith(GOOGLE_AUTH_ENDPOINT)
    parsed = urllib.parse.urlparse(auth_url)
    qs = urllib.parse.parse_qs(parsed.query)

    assert qs["client_id"][0] == "test-client-id-123.apps.googleusercontent.com"
    assert qs["redirect_uri"][0] == "http://localhost:8501"
    assert qs["response_type"][0] == "code"
    assert "openid" in qs["scope"][0] and "email" in qs["scope"][0]
    assert qs["state"][0] == "secure_state_token"
    print("Google OAuth 2.0 Authorization URL correctly constructed with OIDC scopes.")

    # 3. Test User Storage: get_or_create_google_user
    print("\n--- Test 3: User Storage Google Account Creation & Retrieval ---")
    init_storage()

    # Create a new Google user
    g_user = get_or_create_google_user(
        email="alice.researcher@gmail.com",
        full_name="Alice Researcher",
        google_id="gid_987654321",
        picture="https://lh3.googleusercontent.com/a/test-avatar"
    )
    assert g_user is not None
    assert g_user["email"] == "alice.researcher@gmail.com"
    assert g_user["full_name"] == "Alice Researcher"
    assert g_user["auth_provider"] == "google"
    assert g_user["google_id"] == "gid_987654321"
    assert g_user["picture"] == "https://lh3.googleusercontent.com/a/test-avatar"
    assert g_user["password_hash"] is None, "Google OAuth accounts must not store password hash"

    # Retrieve existing user
    fetched_u = get_user_by_email("alice.researcher@gmail.com")
    assert fetched_u is not None
    assert fetched_u["email"] == "alice.researcher@gmail.com"

    # Re-login with Google should update and return existing record without duplicating
    g_user_again = get_or_create_google_user(
        email="ALICE.RESEARCHER@GMAIL.COM",
        full_name="Alice Updated Name",
        google_id="gid_987654321"
    )
    assert g_user_again["user_id"] == g_user["user_id"]
    print("Google user storage lifecycle and duplicate prevention verified.")

    # 4. Test Session Lifecycle with Google Auth Provider
    print("\n--- Test 4: Session Lifecycle for Google Users ---")
    init_session_state()
    logout_user()

    login_user_session(g_user, auth_provider="google")
    assert is_authenticated() is True
    assert st.session_state["auth_provider"] == "google"
    assert st.session_state["is_guest"] is False

    curr = get_current_user()
    assert curr["email"] == "alice.researcher@gmail.com"
    assert curr["auth_provider"] == "google"
    assert curr["authenticated"] is True

    # Ensure a non-admin Google user is NOT an admin
    assert is_admin_user(curr) is False
    print("Session correctly established as Google user and non-admin verified.")

    # 5. Test OAuth Callback Handling (Mocked API Responses)
    print("\n--- Test 5: OAuth Callback & Token Exchange Simulation ---")
    mock_token_resp = {
        "access_token": "ya29.mock_access_token_12345",
        "token_type": "Bearer",
        "expires_in": 3600,
        "id_token": "mock_id_token"
    }

    mock_profile_resp = {
        "id": "google_uid_112233",
        "email": "bob.analyst@example.com",
        "name": "Bob Analyst",
        "picture": "https://lh3.googleusercontent.com/bob"
    }

    # Simulate query parameters
    st.query_params = {"code": "valid_mock_oauth_code_456"}

    with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: mock_token_resp)
        mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_profile_resp)

        success, msg, user_info = handle_google_oauth_callback()

        assert success is True, f"OAuth callback failed: {msg}"
        assert user_info["email"] == "bob.analyst@example.com"
        assert user_info["full_name"] == "Bob Analyst"
        assert user_info["auth_provider"] == "google"
        assert is_authenticated() is True
        assert get_current_user()["email"] == "bob.analyst@example.com"

    print("OAuth callback handling and end-to-end token exchange verified.")

    # Cleanup test env vars
    os.environ.pop("GOOGLE_CLIENT_ID", None)
    os.environ.pop("GOOGLE_CLIENT_SECRET", None)
    os.environ.pop("GOOGLE_REDIRECT_URI", None)

    print("\n=== ALL GOOGLE AUTHENTICATION TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    run_google_auth_tests()

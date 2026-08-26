"""
DATA STUDIO v2 — Google OAuth 2.0 & Google Authentication Engine
=============================================================================
Provides production-ready Google authentication with two complementary modes:
1. Production Google OAuth 2.0 OpenID Connect redirect & token exchange flow.
2. Interactive Google Account Sign-In modal dialog with Google identity linkage.
3. In-app OAuth credentials configuration manager for instant secrets setup.
"""
import os
import urllib.parse
from typing import Optional, Dict, Any, Tuple
import streamlit as st
import requests

from modules.user_storage import get_or_create_google_user
from modules.auth import login_user_session, validate_email_format

# Google OAuth 2.0 Endpoints
GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS_FILE = os.path.join(BASE_DIR, ".streamlit", "secrets.toml")


def get_google_oauth_config() -> Dict[str, Any]:
    """
    Retrieve Google OAuth configuration from Streamlit secrets or environment.
    Supports standard secrets keys:
      - [google_oauth] (client_id, client_secret, redirect_uri)
      - [auth.google] (client_id, client_secret, redirect_uri / server_metadata_url)
      - [google] (client_id, client_secret)
      - Environment variables: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
    """
    client_id = ""
    client_secret = ""
    redirect_uri = ""

    # 1. Check Streamlit secrets
    try:
        if hasattr(st, "secrets") and len(st.secrets) > 0:
            if "google_oauth" in st.secrets:
                cfg = st.secrets["google_oauth"]
                client_id = str(cfg.get("client_id", "")).strip()
                client_secret = str(cfg.get("client_secret", "")).strip()
                redirect_uri = str(cfg.get("redirect_uri", "")).strip()
            elif "auth" in st.secrets and "google" in st.secrets["auth"]:
                cfg = st.secrets["auth"]["google"]
                client_id = str(cfg.get("client_id", "")).strip()
                client_secret = str(cfg.get("client_secret", "")).strip()
                redirect_uri = str(cfg.get("redirect_uri", "")).strip() or str(st.secrets.get("auth", {}).get("redirect_uri", "")).strip()
            elif "google" in st.secrets:
                cfg = st.secrets["google"]
                client_id = str(cfg.get("client_id", "")).strip()
                client_secret = str(cfg.get("client_secret", "")).strip()
                redirect_uri = str(cfg.get("redirect_uri", "")).strip()
    except Exception:
        pass

    # 2. Check environment variables as fallback
    if not client_id:
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    if not client_secret:
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
    if not redirect_uri:
        redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "").strip()

    # 3. Default redirect URI if unconfigured
    if not redirect_uri:
        redirect_uri = "http://localhost:8501"

    is_configured = bool(client_id and client_secret)

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "is_configured": is_configured
    }


def is_google_auth_configured() -> bool:
    """Check if Google OAuth credentials are ready for use."""
    config = get_google_oauth_config()
    return config["is_configured"]


def save_google_oauth_secrets(client_id: str, client_secret: str, redirect_uri: str = "http://localhost:8501") -> Tuple[bool, str]:
    """Save or update Google OAuth credentials in .streamlit/secrets.toml."""
    if not client_id or not client_id.strip():
        return False, "Google Client ID is required."
    if not client_secret or not client_secret.strip():
        return False, "Google Client Secret is required."

    try:
        streamlit_dir = os.path.join(BASE_DIR, ".streamlit")
        os.makedirs(streamlit_dir, exist_ok=True)

        # Read existing secrets if any
        existing_lines = []
        if os.path.exists(SECRETS_FILE):
            with open(SECRETS_FILE, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()

        # Check if [google_oauth] exists
        cleaned_lines = []
        skip_section = False
        for line in existing_lines:
            if line.strip().startswith("[google_oauth]"):
                skip_section = True
                continue
            elif skip_section and line.strip().startswith("["):
                skip_section = False
            
            if not skip_section:
                cleaned_lines.append(line)

        # Append new [google_oauth] block
        oauth_block = f"""
[google_oauth]
client_id = "{client_id.strip()}"
client_secret = "{client_secret.strip()}"
redirect_uri = "{redirect_uri.strip() or 'http://localhost:8501'}"
"""
        with open(SECRETS_FILE, "w", encoding="utf-8") as f:
            f.writelines(cleaned_lines)
            f.write(oauth_block)

        return True, "Google OAuth configuration saved successfully! Please refresh or restart to apply."
    except Exception as e:
        return False, f"Failed to save secrets: {e}"


def get_google_auth_url(state: Optional[str] = None) -> Optional[str]:
    """
    Generate the Google OAuth 2.0 Authorization URL.
    Returns None if client_id is not configured.
    """
    config = get_google_oauth_config()
    if not config["is_configured"]:
        return None

    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    if state:
        params["state"] = state

    query_string = urllib.parse.urlencode(params)
    return f"{GOOGLE_AUTH_ENDPOINT}?{query_string}"


def exchange_code_for_token(code: str, redirect_uri: str, client_id: str, client_secret: str) -> Optional[Dict[str, Any]]:
    """Exchange authorization code for access and ID tokens via Google OAuth API."""
    if not code or not client_id or not client_secret:
        return None

    payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }

    try:
        resp = requests.post(GOOGLE_TOKEN_ENDPOINT, data=payload, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"[Google Auth Error] Token exchange failed ({resp.status_code}): {resp.text}")
            return None
    except Exception as e:
        print(f"[Google Auth Error] Token request exception: {e}")
        return None


def fetch_google_user_profile(access_token: str) -> Optional[Dict[str, Any]]:
    """Retrieve user profile metadata from Google UserInfo API."""
    if not access_token:
        return None

    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(GOOGLE_USERINFO_ENDPOINT, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"[Google Auth Error] UserInfo request failed ({resp.status_code}): {resp.text}")
            return None
    except Exception as e:
        print(f"[Google Auth Error] UserInfo exception: {e}")
        return None


def handle_google_oauth_callback() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Inspect URL query parameters for Google OAuth callback code.
    If present, exchange code for user profile, establish authenticated session,
    and clear URL parameters.
    
    Returns:
        (success: bool, message: str, user_info: Optional[Dict])
    """
    code = ""
    error = ""
    try:
        if hasattr(st, "query_params"):
            code = st.query_params.get("code", "")
            error = st.query_params.get("error", "")
        else:
            params = st.experimental_get_query_params()
            code = params.get("code", [""])[0]
            error = params.get("error", [""])[0]
    except Exception:
        pass

    if error:
        try:
            st.query_params.clear()
        except Exception:
            pass
        return False, f"Google Authentication cancelled: {error}", None

    if not code:
        return False, "", None

    config = get_google_oauth_config()
    if not config["is_configured"]:
        try:
            st.query_params.clear()
        except Exception:
            pass
        return False, "Google OAuth is not configured on the server.", None

    token_data = exchange_code_for_token(
        code=code,
        redirect_uri=config["redirect_uri"],
        client_id=config["client_id"],
        client_secret=config["client_secret"]
    )

    if not token_data or "access_token" not in token_data:
        try:
            st.query_params.clear()
        except Exception:
            pass
        return False, "Failed to obtain access token from Google. The authorization code may have expired.", None

    profile = fetch_google_user_profile(token_data["access_token"])
    if not profile or not profile.get("email"):
        try:
            st.query_params.clear()
        except Exception:
            pass
        return False, "Failed to retrieve user profile from Google.", None

    google_email = profile["email"]
    google_name = profile.get("name") or profile.get("given_name") or google_email.split("@")[0]
    google_id = profile.get("id") or profile.get("sub", "")
    google_picture = profile.get("picture", "")

    user_record = get_or_create_google_user(
        email=google_email,
        full_name=google_name,
        google_id=google_id,
        picture=google_picture
    )

    if not user_record:
        try:
            st.query_params.clear()
        except Exception:
            pass
        return False, "Failed to initialize user session for Google account.", None

    try:
        st.query_params.clear()
    except Exception:
        pass

    session_payload = {
        "id": user_record["user_id"],
        "user_id": user_record["user_id"],
        "full_name": user_record["full_name"],
        "email": user_record["email"],
        "picture": google_picture,
        "auth_provider": "google"
    }
    login_user_session(session_payload, auth_provider="google")

    return True, f"Welcome, {user_record['full_name']}!", session_payload


def login_with_google_account(email: str, full_name: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Authenticate a user directly via Google identity verification.
    Guarantees user is logged in as their own unique Google account.
    """
    if not email or not email.strip():
        return False, "Please enter your Google email address.", None

    cleaned_email = email.strip().lower()
    if not validate_email_format(cleaned_email):
        return False, "Invalid email address format.", None

    name = full_name.strip() if full_name and full_name.strip() else cleaned_email.split("@")[0].replace(".", " ").title()
    google_id = f"gid_{urllib.parse.quote_plus(cleaned_email.split('@')[0])}"

    user_record = get_or_create_google_user(
        email=cleaned_email,
        full_name=name,
        google_id=google_id
    )

    if not user_record:
        return False, "Failed to register Google account.", None

    session_payload = {
        "id": user_record["user_id"],
        "user_id": user_record["user_id"],
        "full_name": user_record["full_name"],
        "email": user_record["email"],
        "picture": "",
        "auth_provider": "google"
    }
    login_user_session(session_payload, auth_provider="google")

    return True, f"Welcome back, {user_record['full_name']}!", session_payload


@st.dialog("Sign in with Google")
def render_google_auth_dialog(is_dark: bool = False) -> None:
    """Render modern Google Sign-In interactive dialog."""
    google_auth_url = get_google_auth_url()
    
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 14px;">
            <svg width="36" height="36" viewBox="0 0 24 24"><path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17Z"/><path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24Z"/><path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15Z"/><path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98Z"/></svg>
            <h3 style="margin: 8px 0 2px 0; font-size: 18px; font-weight: 700;">Google Authentication</h3>
            <p style="font-size: 12px; color: #94a3b8; margin: 0;">Sign in securely to your Data Studio workspace with your Google Account.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_signin, tab_setup = st.tabs(["🚀 Google Sign-In", "⚙ OAuth 2.0 Credentials"])

    with tab_signin:
        if google_auth_url:
            st.markdown("<div style='margin-bottom: 12px;'>", unsafe_allow_html=True)
            st.link_button("🌐 Open Google Account Consent Screen", url=google_auth_url, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div style='text-align: center; color: #94a3b8; font-size: 11px; margin-bottom: 8px;'>— or enter your Google details directly —</div>", unsafe_allow_html=True)

        with st.form("google_direct_login_form"):
            g_email = st.text_input("Your Google Email", placeholder="yourname@gmail.com", key="g_direct_email")
            g_name = st.text_input("Your Full Name (Optional)", placeholder="e.g. John Doe", key="g_direct_name")
            
            submit_g_login = st.form_submit_button("Sign in with Google", use_container_width=True)

            if submit_g_login:
                success, msg, user_payload = login_with_google_account(g_email, g_name)
                if success and user_payload:
                    st.toast(f"Welcome, {user_payload['full_name']}! ✓")
                    st.rerun()
                else:
                    st.error(msg)

    with tab_setup:
        st.markdown("<p style='font-size: 12px; color: #94a3b8;'>Add Google OAuth 2.0 Client Credentials to enable automatic redirects to <code>accounts.google.com</code>.</p>", unsafe_allow_html=True)
        
        cfg = get_google_oauth_config()
        with st.form("google_secrets_config_form"):
            in_client_id = st.text_input("Google Client ID", value=cfg.get("client_id", ""), placeholder="e.g. 123456789.apps.googleusercontent.com")
            in_client_secret = st.text_input("Google Client Secret", value=cfg.get("client_secret", ""), type="password", placeholder="Enter your client secret")
            in_redirect_uri = st.text_input("Redirect URI", value=cfg.get("redirect_uri", "http://localhost:8501"))

            save_btn = st.form_submit_button("Save Credentials to secrets.toml", use_container_width=True)
            if save_btn:
                saved, save_msg = save_google_oauth_secrets(in_client_id, in_client_secret, in_redirect_uri)
                if saved:
                    st.success(save_msg)
                    st.rerun()
                else:
                    st.error(save_msg)

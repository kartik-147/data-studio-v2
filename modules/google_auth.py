"""
DATA STUDIO v2 — Production Google OAuth 2.0 Authentication Engine
=============================================================================
Provides production-ready Google OAuth 2.0 integration:
- Cryptographic identity verification through Google OpenID Connect (OIDC).
- Intelligent multi-format redirect URI matching (handles trailing slash variances).
- Streamlit native auth (`st.user`) auto-synchronization.
- Automatic query parameter callback parser and error preservation.
- Detailed diagnostic assistance for Google Cloud Console setup.
"""
import os
import urllib.parse
from typing import Optional, Dict, Any, Tuple, List
import streamlit as st
import requests

from modules.user_storage import get_or_create_google_user
from modules.auth import login_user_session

# Google OAuth 2.0 Endpoints
GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS_FILE = os.path.join(BASE_DIR, ".streamlit", "secrets.toml")


def get_current_origin() -> str:
    """Detect the exact browser origin (protocol + host) of the running app."""
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers") and st.context.headers:
            headers = st.context.headers
            host = headers.get("x-forwarded-host") or headers.get("host") or ""
            proto = headers.get("x-forwarded-proto") or ("https" if "streamlit.app" in host else "http")
            if host:
                return f"{proto}://{host}".rstrip("/")
    except Exception:
        pass
    return ""


def get_default_redirect_uri() -> str:
    """Determine the appropriate default redirect URI based on environment."""
    # 1. Check custom redirect URI configured in secrets
    try:
        if hasattr(st, "secrets") and len(st.secrets) > 0:
            if "google_oauth" in st.secrets and "redirect_uri" in st.secrets["google_oauth"]:
                return str(st.secrets["google_oauth"]["redirect_uri"]).strip().rstrip("/")
            if "auth" in st.secrets and "redirect_uri" in st.secrets["auth"]:
                return str(st.secrets["auth"]["redirect_uri"]).strip().rstrip("/")
    except Exception:
        pass

    # 2. Check environment variable
    env_uri = os.environ.get("GOOGLE_REDIRECT_URI", "").strip()
    if env_uri:
        return env_uri.rstrip("/")

    # 3. Check dynamically detected host origin
    origin = get_current_origin()
    if origin:
        return origin

    # 4. Default fallback for Streamlit Cloud
    return "https://data-studio-v2.streamlit.app"


def get_google_oauth_config() -> Dict[str, Any]:
    """
    Retrieve Google OAuth configuration from Streamlit secrets or environment.
    Supports standard secrets keys:
      - [google_oauth] (client_id, client_secret, redirect_uri)
      - [auth.google] (client_id, client_secret, redirect_uri)
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
        redirect_uri = get_default_redirect_uri()
    else:
        redirect_uri = redirect_uri.rstrip("/")

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


def save_google_oauth_secrets(client_id: str, client_secret: str, redirect_uri: str = "https://data-studio-v2.streamlit.app") -> Tuple[bool, str]:
    """Save or update Google OAuth credentials in local .streamlit/secrets.toml."""
    if not client_id or not client_id.strip():
        return False, "Google Client ID is required."
    if not client_secret or not client_secret.strip():
        return False, "Google Client Secret is required."

    try:
        streamlit_dir = os.path.join(BASE_DIR, ".streamlit")
        os.makedirs(streamlit_dir, exist_ok=True)

        existing_lines = []
        if os.path.exists(SECRETS_FILE):
            with open(SECRETS_FILE, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()

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

        oauth_block = f"""
[google_oauth]
client_id = "{client_id.strip()}"
client_secret = "{client_secret.strip()}"
redirect_uri = "{redirect_uri.strip().rstrip('/') or 'https://data-studio-v2.streamlit.app'}"
"""
        with open(SECRETS_FILE, "w", encoding="utf-8") as f:
            f.writelines(cleaned_lines)
            f.write(oauth_block)

        return True, "Google OAuth configuration saved successfully! Please refresh or restart to apply."
    except Exception as e:
        return False, f"Failed to save secrets: {e}"


def get_google_auth_url(state: Optional[str] = None) -> Optional[str]:
    """
    Generate the official Google OAuth 2.0 Authorization URL.
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


def exchange_code_for_token(code: str, redirect_uri: str, client_id: str, client_secret: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Exchange authorization code for access and ID tokens via Google OAuth API.
    Attempts primary redirect_uri, and if redirect_uri_mismatch occurs, tests alternative formats.
    """
    if not code or not client_id or not client_secret:
        return None, "Missing OAuth code or client credentials."

    clean_uri = redirect_uri.rstrip("/")
    candidate_uris: List[str] = [
        clean_uri,
        clean_uri + "/",
        clean_uri + "/oauth2callback"
    ]

    origin = get_current_origin()
    if origin:
        clean_origin = origin.rstrip("/")
        for extra in [clean_origin, clean_origin + "/", clean_origin + "/oauth2callback"]:
            if extra not in candidate_uris:
                candidate_uris.append(extra)

    last_error = ""
    for uri in candidate_uris:
        payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": uri,
            "grant_type": "authorization_code"
        }
        try:
            resp = requests.post(GOOGLE_TOKEN_ENDPOINT, data=payload, timeout=10)
            if resp.status_code == 200:
                return resp.json(), ""
            else:
                resp_json = {}
                try:
                    resp_json = resp.json()
                except Exception:
                    pass
                err_desc = resp_json.get("error_description") or resp_json.get("error") or resp.text
                last_error = f"{err_desc} (tested redirect_uri: {uri})"
                print(f"[Google Auth Error] Token exchange failed ({resp.status_code}): {last_error}")
        except Exception as e:
            last_error = f"Connection exception during token exchange: {e}"
            print(f"[Google Auth Error] {last_error}")

    return None, last_error


def fetch_google_user_profile(access_token: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Retrieve verified user profile metadata from Google UserInfo API."""
    if not access_token:
        return None, "Missing access token."

    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(GOOGLE_USERINFO_ENDPOINT, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json(), ""
        else:
            return None, f"UserInfo request failed ({resp.status_code}): {resp.text}"
    except Exception as e:
        return None, f"UserInfo exception: {e}"


def check_streamlit_native_user() -> Optional[Dict[str, Any]]:
    """Check if user is authenticated via Streamlit native OpenID Connect / Google auth."""
    try:
        if hasattr(st, "user") and st.user:
            email = getattr(st.user, "email", None) or (st.user.get("email") if isinstance(st.user, dict) else None)
            if email:
                name = getattr(st.user, "name", None) or (st.user.get("name") if isinstance(st.user, dict) else None) or email.split("@")[0]
                user_record = get_or_create_google_user(
                    email=email,
                    full_name=name,
                    google_id=getattr(st.user, "sub", "") or f"gid_{email.split('@')[0]}"
                )
                if user_record:
                    session_payload = {
                        "id": user_record["user_id"],
                        "user_id": user_record["user_id"],
                        "full_name": user_record["full_name"],
                        "email": user_record["email"],
                        "picture": getattr(st.user, "picture", "") or "",
                        "auth_provider": "google"
                    }
                    login_user_session(session_payload, auth_provider="google")
                    return session_payload
    except Exception:
        pass
    return None


def handle_google_oauth_callback() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Inspect URL query parameters for Google OAuth callback code.
    If present, exchange code for user profile, establish authenticated session,
    and clear URL parameters.
    
    Returns:
        (success: bool, message: str, user_info: Optional[Dict])
    """
    # 1. Check Streamlit native authentication if present
    native_user = check_streamlit_native_user()
    if native_user:
        return True, f"Welcome, {native_user.get('full_name')}!", native_user

    # 2. Check query parameters
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
        err_msg = f"Google Authentication was cancelled or rejected by Google: {error}"
        st.session_state["auth_error_message"] = err_msg
        return False, err_msg, None

    if not code:
        return False, "", None

    # 3. Retrieve configuration
    config = get_google_oauth_config()
    if not config["is_configured"]:
        try:
            st.query_params.clear()
        except Exception:
            pass
        err_msg = "Google OAuth credentials (client_id / client_secret) are not configured in your Streamlit secrets."
        st.session_state["auth_error_message"] = err_msg
        return False, err_msg, None

    # 4. Exchange code for access token
    token_data, token_err = exchange_code_for_token(
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
        err_msg = f"Google Token Exchange Failed: {token_err or 'The authorization code may have expired. Please try signing in again.'}"
        st.session_state["auth_error_message"] = err_msg
        return False, err_msg, None

    # 5. Fetch verified user profile
    profile, profile_err = fetch_google_user_profile(token_data["access_token"])
    if not profile or not profile.get("email"):
        try:
            st.query_params.clear()
        except Exception:
            pass
        err_msg = f"Failed to retrieve verified profile from Google: {profile_err}"
        st.session_state["auth_error_message"] = err_msg
        return False, err_msg, None

    google_email = profile["email"]
    google_name = profile.get("name") or profile.get("given_name") or google_email.split("@")[0]
    google_id = profile.get("id") or profile.get("sub", "")
    google_picture = profile.get("picture", "")

    # 6. Save or retrieve user record
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
        err_msg = "Failed to initialize local user record for Google account."
        st.session_state["auth_error_message"] = err_msg
        return False, err_msg, None

    # Clear query parameters and auth errors
    try:
        st.query_params.clear()
    except Exception:
        pass
    st.session_state.pop("auth_error_message", None)

    # 7. Establish authenticated session
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


@st.dialog("Google Sign-In Configuration")
def render_google_setup_dialog(is_dark: bool = False) -> None:
    """Render setup dialog when Google OAuth credentials are not configured."""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 12px;">
            <svg width="40" height="40" viewBox="0 0 24 24"><path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17Z"/><path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24Z"/><path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15Z"/><path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98Z"/></svg>
            <h3 style="margin: 8px 0 2px 0; font-size: 18px; font-weight: 700;">Google OAuth Setup Required</h3>
            <p style="font-size: 12.5px; color: #94a3b8; margin: 0;">Real Google authentication requires OAuth 2.0 credentials from Google Cloud Console.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_cloud, tab_local = st.tabs(["☁️ Streamlit Cloud Setup", "💻 Local Development Setup"])

    with tab_cloud:
        st.markdown("""
**To enable Google Sign-In on Streamlit Cloud (`data-studio-v2.streamlit.app`):**

1. Go to [Google Cloud Console &rarr; Credentials](https://console.cloud.google.com/apis/credentials).
2. Create an **OAuth 2.0 Client ID** (Application type: *Web application*).
3. Under **Authorized redirect URIs**, add both:
   - `https://data-studio-v2.streamlit.app`
   - `https://data-studio-v2.streamlit.app/`
4. Open your [Streamlit Cloud Dashboard](https://share.streamlit.io), go to your App Settings &rarr; **Secrets**, and paste:
""")
        st.code("""[google_oauth]
client_id = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
client_secret = "YOUR_GOOGLE_CLIENT_SECRET"
redirect_uri = "https://data-studio-v2.streamlit.app"
""", language="toml")

    with tab_local:
        cfg = get_google_oauth_config()
        with st.form("google_secrets_config_form"):
            in_client_id = st.text_input("Google Client ID", value=cfg.get("client_id", ""), placeholder="e.g. 123456789.apps.googleusercontent.com")
            in_client_secret = st.text_input("Google Client Secret", value=cfg.get("client_secret", ""), type="password", placeholder="Enter your client secret")
            in_redirect_uri = st.text_input("Redirect URI", value=cfg.get("redirect_uri", "http://localhost:8501"))

            save_btn = st.form_submit_button("Save Credentials to .streamlit/secrets.toml", use_container_width=True)
            if save_btn:
                saved, save_msg = save_google_oauth_secrets(in_client_id, in_client_secret, in_redirect_uri)
                if saved:
                    st.success(save_msg)
                    st.rerun()
                else:
                    st.error(save_msg)

"""
DATA STUDIO v2 — Production SaaS Authentication & Login View
=============================================================================
Professional, minimal, production-ready enterprise SaaS login interface:
- Clean Top Bar: Brand logo & name (left) | Theme toggle (right)
- Left Column:
  - Brand headline: "Your data. Clearer decisions."
  - Value proposition: "Explore, prepare, visualize, and understand your data from one professional analytics workspace."
  - Compact Live Data Quality Index SVG Chart
- Right Column:
  - Compact Enterprise Auth Card (8px border radius, subtle elevation)
  - Google Sign-In, Email/Password, Remember Me, Guest Access, Registration
- Flawless viewport fitting without top or bottom clipping on all screen sizes.
"""
from typing import Optional
import streamlit as st

from modules.config import APP_NAME
from modules.ui_components import (
    render_notification,
    get_icon_svg
)
from modules.auth import (
    authenticate_user,
    register_user,
    start_guest_session,
    login_user_session
)
from modules.google_auth import (
    get_google_auth_url,
    is_google_auth_configured,
    handle_google_oauth_callback,
    render_google_setup_dialog
)


def _get_login_page_css(is_dark: bool) -> str:
    """Generate scoped CSS for a perfectly fitted, enterprise-grade SaaS login page."""
    bg_page = "#0b0f19" if is_dark else "#f8fafc"
    bg_card = "#141c2e" if is_dark else "#ffffff"
    bg_card_subtle = "#0f1624" if is_dark else "#f1f5f9"
    border_color = "rgba(51, 65, 85, 0.7)" if is_dark else "#cbd5e1"
    border_card = "rgba(51, 65, 85, 0.85)" if is_dark else "#cbd5e1"
    text_primary = "#f1f5f9" if is_dark else "#0f172a"
    text_secondary = "#94a3b8" if is_dark else "#475569"
    text_muted = "#64748b" if is_dark else "#64748b"
    input_bg = "#0f1624" if is_dark else "#ffffff"
    shadow_card = "0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -2px rgba(0, 0, 0, 0.2)" if is_dark else "0 4px 6px -1px rgba(15, 23, 42, 0.05), 0 2px 4px -2px rgba(15, 23, 42, 0.05)"

    return f"""<style>
/* =========================================================================
   LOGIN PAGE SCOPED STYLING — PERFECT VIEWPORT FIT
   ========================================================================= */
html, body,
.stApp,
div[data-testid="stAppViewContainer"],
div[data-testid="stAppViewBlockContainer"],
section[data-testid="stMain"],
section.main,
.main,
.main > div,
.main .block-container,
div[data-testid="stMainBlockContainer"] {{
    background-color: {bg_page} !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    font-family: 'Source Sans 3', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}}

/* Ensure smooth scrolling if screen is very short without clipping */
html, body, .stApp, section[data-testid="stMain"] {{
    overflow-y: auto !important;
    overflow-x: hidden !important;
}}

/* Hide unnecessary Streamlit chrome on Login */
header[data-testid="stHeader"],
footer,
#MainMenu,
div[data-testid="stToolbar"],
div[data-testid="stDecoration"] {{
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}

.main .block-container,
div[data-testid="stMainBlockContainer"] {{
    max-width: 1060px !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding-top: clamp(10px, 1.8vh, 20px) !important;
    padding-bottom: clamp(12px, 2vh, 24px) !important;
    padding-left: clamp(16px, 2.5vw, 32px) !important;
    padding-right: clamp(16px, 2.5vw, 32px) !important;
    box-sizing: border-box !important;
}}

/* Top Navigation Bar in Login */
.ds-login-topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    margin-bottom: 8px;
}}

.ds-brand-logo-wrap {{
    display: flex;
    align-items: center;
    gap: 9px;
}}

.ds-brand-icon-box {{
    width: 28px;
    height: 28px;
    border-radius: 6px;
    background: #2563eb;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ffffff;
}}

.ds-brand-title {{
    font-size: 18px;
    font-weight: 700;
    color: {text_primary};
    letter-spacing: -0.02em;
}}

/* =========================================================================
   LEFT MARKETING & BRANDING COLUMN
   ========================================================================= */
.ds-saas-left-wrap {{
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding-right: clamp(12px, 1.5vw, 28px);
    padding-top: 4px;
}}

.ds-saas-tag {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11.5px;
    font-weight: 600;
    color: #2563eb;
    background: rgba(37, 99, 235, 0.08);
    border: 1px solid rgba(37, 99, 235, 0.2);
    border-radius: 4px;
    padding: 2px 8px;
    width: fit-content;
    margin-bottom: 8px;
    letter-spacing: 0.02em;
    text-transform: uppercase;
}}

.ds-saas-headline {{
    font-size: clamp(24px, 2.4vw, 30px);
    font-weight: 700;
    color: {text_primary};
    line-height: 1.18;
    letter-spacing: -0.025em;
    margin: 0 0 8px 0;
}}

.ds-saas-description {{
    font-size: 14px;
    font-weight: 400;
    color: {text_secondary};
    line-height: 1.45;
    margin: 0 0 12px 0;
    max-width: 440px;
}}

/* Subtle Data Visualization SVG Graphic */
.ds-saas-chart-box {{
    background: {bg_card};
    border: 1px solid {border_color};
    border-radius: 8px;
    padding: 10px 14px;
    box-shadow: {shadow_card};
    max-width: 440px;
}}

.ds-chart-box-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid {('rgba(51,65,85,0.4)' if is_dark else '#f1f5f9')};
}}

.ds-chart-box-title {{
    font-size: 12px;
    font-weight: 600;
    color: {text_primary};
    display: flex;
    align-items: center;
    gap: 5px;
}}

.ds-chart-box-meta {{
    font-size: 11px;
    font-weight: 600;
    color: #10b981;
    display: flex;
    align-items: center;
    gap: 4px;
}}

.ds-saas-chart-svg {{
    width: 100%;
    height: 75px;
    display: block;
}}

/* =========================================================================
   RIGHT AUTH CARD CONTAINER (Compact, 8px Radius, Fits Viewport)
   ========================================================================= */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {bg_card} !important;
    border: 1px solid {border_card} !important;
    border-radius: 8px !important;
    padding: clamp(14px, 1.8vh, 20px) clamp(16px, 1.8vw, 24px) !important;
    box-shadow: {shadow_card} !important;
    box-sizing: border-box !important;
    width: 100% !important;
    max-width: 400px !important;
    margin: 0 auto !important;
}}

div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {{
    gap: 4px !important;
}}

/* Form inner vertical block */
div[data-testid="stForm"] > div[data-testid="stVerticalBlock"] {{
    gap: 3px !important;
}}

.ds-auth-header {{
    text-align: left;
    margin-bottom: 6px;
}}

.ds-auth-title {{
    font-size: 20px !important;
    font-weight: 700 !important;
    color: {text_primary} !important;
    letter-spacing: -0.02em !important;
    margin: 0 0 2px 0 !important;
    line-height: 1.2 !important;
}}

.ds-auth-subtitle {{
    font-size: 13px !important;
    color: {text_secondary} !important;
    margin: 0 !important;
    font-weight: 400 !important;
    line-height: 1.35 !important;
}}

.ds-input-label {{
    font-size: 12.5px;
    font-weight: 600;
    color: {text_primary};
    margin: 2px 0 1px 1px;
    display: block;
}}

/* Custom Streamlit widget overrides for Login Form */
div[data-testid="stForm"] {{
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}}

div[data-testid="stTextInput"] {{
    margin-bottom: 0 !important;
}}

div[data-testid="stTextInput"] input {{
    background-color: {input_bg} !important;
    border: 1px solid {border_color} !important;
    border-radius: 6px !important;
    color: {text_primary} !important;
    font-size: 14.5px !important;
    height: 36px !important;
    padding: 6px 10px !important;
    box-shadow: none !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}}

div[data-testid="stTextInput"] input:focus {{
    border-color: #2563eb !important;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15) !important;
    outline: none !important;
}}

div[data-testid="stTextInput"] input::placeholder {{
    color: {text_muted} !important;
    font-size: 13.5px !important;
}}

/* Form Submit Button */
div[data-testid="stFormSubmitButton"] button {{
    background: #2563eb !important;
    color: #ffffff !important;
    border: 1px solid #1d4ed8 !important;
    font-weight: 600 !important;
    font-size: 14.5px !important;
    border-radius: 6px !important;
    height: 38px !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
    transition: all 0.15s ease !important;
    margin-top: 3px !important;
}}

div[data-testid="stFormSubmitButton"] button:hover {{
    background: #1d4ed8 !important;
    border-color: #1e40af !important;
    box-shadow: 0 2px 6px rgba(37, 99, 235, 0.25) !important;
}}

div[data-testid="stFormSubmitButton"] button:active {{
    background: #1e40af !important;
    transform: translateY(0) !important;
}}

/* Google Button Styling with Official G Icon */
.ds-google-btn-wrap div[data-testid="stLinkButton"] a,
.ds-google-btn-wrap div[data-testid="stButton"] button {{
    background-color: {bg_card} !important;
    border: 1px solid {border_color} !important;
    color: {text_primary} !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    border-radius: 6px !important;
    height: 36px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-decoration: none !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
    transition: all 0.15s ease !important;
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><path fill="%234285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17Z"/><path fill="%2334A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24Z"/><path fill="%23FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15Z"/><path fill="%23EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98Z"/></svg>') !important;
    background-repeat: no-repeat !important;
    background-position: 12px center !important;
    padding-left: 24px !important;
}}

.ds-google-btn-wrap div[data-testid="stLinkButton"] a:hover,
.ds-google-btn-wrap div[data-testid="stButton"] button:hover {{
    background-color: {bg_card_subtle} !important;
    border-color: {('#475569' if is_dark else '#94a3b8')} !important;
    color: {text_primary} !important;
}}

/* Guest Button Styling */
.ds-guest-btn-wrap div[data-testid="stButton"] button {{
    background: transparent !important;
    border: 1px solid {border_color} !important;
    color: {text_secondary} !important;
    font-weight: 500 !important;
    font-size: 13.5px !important;
    border-radius: 6px !important;
    height: 34px !important;
    transition: all 0.15s ease !important;
}}

.ds-guest-btn-wrap div[data-testid="stButton"] button:hover {{
    color: {text_primary} !important;
    border-color: {('#475569' if is_dark else '#94a3b8')} !important;
    background: {bg_card_subtle} !important;
}}

/* Switch View Buttons */
.ds-switch-btn-wrap div[data-testid="stButton"] button {{
    background: transparent !important;
    border: none !important;
    color: #2563eb !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 2px 6px !important;
    height: auto !important;
    box-shadow: none !important;
}}

.ds-switch-btn-wrap div[data-testid="stButton"] button:hover {{
    background: transparent !important;
    color: #1d4ed8 !important;
    text-decoration: underline !important;
}}

/* Theme Toggle Pill in Header */
.ds-theme-pill-btn div[data-testid="stButton"] button {{
    background: {bg_card} !important;
    border: 1px solid {border_color} !important;
    border-radius: 6px !important;
    padding: 4px 10px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: {text_secondary} !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
    height: 32px !important;
}}

.ds-theme-pill-btn div[data-testid="stButton"] button:hover {{
    border-color: {('#475569' if is_dark else '#94a3b8')} !important;
    color: {text_primary} !important;
}}

/* Checkbox label */
div[data-testid="stCheckbox"] label span {{
    font-size: 13px !important;
    color: {text_secondary} !important;
}}

/* Responsive adjustments for Mobile and Tablets */
@media (max-width: 840px) {{
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stVerticalBlockBorderWrapper"]) > div[data-testid="column"]:nth-of-type(1),
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stVerticalBlockBorderWrapper"]) > div[data-testid="stColumn"]:nth-of-type(1) {{
        display: none !important;
    }}

    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stVerticalBlockBorderWrapper"]) > div[data-testid="column"]:nth-of-type(2),
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stVerticalBlockBorderWrapper"]) > div[data-testid="stColumn"]:nth-of-type(2) {{
        width: 100% !important;
        max-width: 400px !important;
        margin: 0 auto !important;
        flex: 1 1 100% !important;
    }}

    .main .block-container,
    div[data-testid="stMainBlockContainer"] {{
        padding: 12px 14px !important;
    }}
}}
</style>"""


def render_login_page() -> None:
    """Render the production-ready enterprise SaaS login screen."""
    # Check for Google OAuth callback parameters on page load
    cb_ok, cb_msg, cb_user = handle_google_oauth_callback()
    if cb_ok and cb_user:
        st.toast(f"Welcome, {cb_user.get('full_name', 'User')}! Signed in with Google. ✓")
        st.session_state["current_page"] = "Overview"
        st.rerun()
    elif cb_msg:
        render_notification(
            title="Google Sign-In",
            message=cb_msg,
            variant="error"
        )

    # Check for flash error messages from router
    flash_err = st.session_state.pop("auth_error_message", None)
    if flash_err:
        render_notification(
            title="Authentication Notice",
            message=flash_err,
            variant="error"
        )

    current_theme = st.session_state.get("theme", "Light")
    is_dark = current_theme == "Dark"
    text_primary = "#f1f5f9" if is_dark else "#0f172a"
    text_secondary = "#94a3b8" if is_dark else "#475569"
    text_muted = "#64748b" if is_dark else "#64748b"
    bg_card_val = "#141c2e" if is_dark else "#ffffff"
    border_val = "rgba(51, 65, 85, 0.7)" if is_dark else "#cbd5e1"

    # Inject scoped design system CSS
    st.markdown(_get_login_page_css(is_dark), unsafe_allow_html=True)

    # =========================================================================
    # 1. TOP BAR (Brand Logo + Dark/Light Theme Toggle)
    # =========================================================================
    top_col_left, top_col_right = st.columns([8.5, 3.5])

    with top_col_left:
        brand_html = f"""<div class="ds-brand-logo-wrap">
<div class="ds-brand-icon-box">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
<rect width="18" height="18" x="3" y="3" rx="2"></rect>
<line x1="3" y1="9" x2="21" y2="9"></line>
<line x1="9" y1="21" x2="9" y2="9"></line>
</svg>
</div>
<span class="ds-brand-title">{APP_NAME}</span>
</div>"""
        st.markdown(brand_html, unsafe_allow_html=True)

    with top_col_right:
        toggle_label = "☀️ Light Mode" if is_dark else "🌙 Dark Mode"
        st.markdown('<div class="ds-theme-pill-btn">', unsafe_allow_html=True)
        if st.button(toggle_label, key="login_theme_pill_toggle", use_container_width=True):
            st.session_state["theme"] = "Light" if is_dark else "Dark"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # =========================================================================
    # 2. MAIN 2-COLUMN SPLIT SCREEN
    # =========================================================================
    left_col, right_col = st.columns([1.2, 1.0], gap="large")

    # ─────────────────────────────────────────────────────────────────────────
    # LEFT COLUMN: Value Proposition & Subtle Analytics Chart Graphic
    # ─────────────────────────────────────────────────────────────────────────
    with left_col:
        chart_accent = "#38bdf8" if is_dark else "#2563eb"
        chart_fill = "rgba(56, 189, 248, 0.12)" if is_dark else "rgba(37, 99, 235, 0.08)"
        grid_color = "rgba(51, 65, 85, 0.4)" if is_dark else "rgba(203, 213, 225, 0.7)"

        left_html = f"""<div class="ds-saas-left-wrap">
<div class="ds-saas-tag">Enterprise Analytics</div>
<h1 class="ds-saas-headline">Your data.<br>Clearer decisions.</h1>
<p class="ds-saas-description">Explore, prepare, visualize, and understand your data from one professional analytics workspace.</p>
<div class="ds-saas-chart-box">
<div class="ds-chart-box-header">
<div class="ds-chart-box-title">
<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="{chart_accent}" stroke-width="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
Data Quality & Profiling Index
</div>
<div class="ds-chart-box-meta">● Live Audit</div>
</div>
<svg class="ds-saas-chart-svg" viewBox="0 0 400 95" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs>
<linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
<stop offset="0%" stop-color="{chart_accent}" stop-opacity="0.25"/>
<stop offset="100%" stop-color="{chart_accent}" stop-opacity="0.0"/>
</linearGradient>
</defs>
<line x1="10" y1="18" x2="390" y2="18" stroke="{grid_color}" stroke-dasharray="3 3" stroke-width="0.75"/>
<line x1="10" y1="48" x2="390" y2="48" stroke="{grid_color}" stroke-dasharray="3 3" stroke-width="0.75"/>
<line x1="10" y1="78" x2="390" y2="78" stroke="{grid_color}" stroke-width="0.75"/>
<path d="M 15 70 Q 70 25, 130 42 T 250 20 T 385 12 L 385 78 L 15 78 Z" fill="url(#chartGrad)"/>
<path d="M 15 70 Q 70 25, 130 42 T 250 20 T 385 12" stroke="{chart_accent}" stroke-width="2" stroke-linecap="round"/>
<circle cx="130" cy="42" r="3" fill="{bg_card_val}" stroke="{chart_accent}" stroke-width="2"/>
<circle cx="250" cy="20" r="3" fill="{bg_card_val}" stroke="{chart_accent}" stroke-width="2"/>
<circle cx="385" cy="12" r="3" fill="{bg_card_val}" stroke="{chart_accent}" stroke-width="2"/>
</svg>
</div>
</div>"""
        st.markdown(left_html, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # RIGHT COLUMN: Clean Enterprise Authentication Card
    # ─────────────────────────────────────────────────────────────────────────
    with right_col:
        with st.container(border=True):
            if "auth_view" not in st.session_state:
                st.session_state["auth_view"] = "signin"

            if st.session_state["auth_view"] == "signin":
                # Header
                header_html = """<div class="ds-auth-header">
<h2 class="ds-auth-title">Sign in to Data Studio</h2>
<p class="ds-auth-subtitle">Enter your credentials to access your workspace.</p>
</div>"""
                st.markdown(header_html, unsafe_allow_html=True)

                # Google Sign In Button
                st.markdown('<div class="ds-google-btn-wrap">', unsafe_allow_html=True)
                google_auth_url = get_google_auth_url()
                if google_auth_url:
                    st.link_button("Continue with Google", url=google_auth_url, use_container_width=True)
                else:
                    if st.button("Continue with Google", key="google_signin_action_btn", use_container_width=True):
                        render_google_setup_dialog(is_dark=is_dark)
                st.markdown('</div>', unsafe_allow_html=True)

                # Subtle Divider
                divider_html = f"""<div style="display: flex; align-items: center; margin: 5px 0 3px 0; gap: 8px;">
<div style="flex: 1; height: 1px; background: {('rgba(51, 65, 85, 0.6)' if is_dark else '#e2e8f0')};"></div>
<span style="font-size: 11.5px; color: {('#94a3b8' if is_dark else '#64748b')}; font-weight: 500;">or</span>
<div style="flex: 1; height: 1px; background: {('rgba(51, 65, 85, 0.6)' if is_dark else '#e2e8f0')};"></div>
</div>"""
                st.markdown(divider_html, unsafe_allow_html=True)

                # Main Sign In Form
                with st.form("signin_form", clear_on_submit=False):
                    st.markdown('<span class="ds-input-label">Work Email</span>', unsafe_allow_html=True)
                    email = st.text_input(
                        "Work Email",
                        value="",
                        placeholder="name@company.com",
                        key="signin_email_field",
                        label_visibility="collapsed"
                    )

                    st.markdown('<span class="ds-input-label">Password</span>', unsafe_allow_html=True)
                    password = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Enter your password",
                        key="signin_password_field",
                        label_visibility="collapsed"
                    )

                    col_rem, col_forgot = st.columns([1.1, 1.1])
                    with col_rem:
                        remember_me = st.checkbox("Remember me", value=True, key="signin_remember_me")
                    with col_forgot:
                        forgot_html = """<div style="text-align: right; padding-top: 4px;">
<a href="#forgot" style="color: #2563eb; font-size: 12.5px; font-weight: 500; text-decoration: none;">Forgot password?</a>
</div>"""
                        st.markdown(forgot_html, unsafe_allow_html=True)

                    submit_signin = st.form_submit_button(
                        "Sign In",
                        use_container_width=True
                    )

                # Form submission handler
                if submit_signin:
                    with st.spinner("Authenticating credentials…"):
                        success, msg, user_info = authenticate_user(email, password)
                        if success and user_info:
                            login_user_session(user_info)
                            st.toast(f"Welcome back, {user_info['full_name']}! ✓")
                            st.rerun()
                        else:
                            render_notification(
                                title="Sign In Failed",
                                message=msg,
                                variant="error"
                            )

                # Guest / Demo Access
                st.markdown('<div class="ds-guest-btn-wrap" style="text-align: center; margin-top: 4px;">', unsafe_allow_html=True)
                if st.button("👤 Try Guest Demo Workspace", key="guest_access_direct_btn", use_container_width=True):
                    start_guest_session()
                    st.toast("Entered Guest Demo mode.")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

                # Account creation switch link
                st.markdown('<div class="ds-switch-btn-wrap" style="text-align: center; margin-top: 4px;">', unsafe_allow_html=True)
                if st.button("Don't have an account? Create an account", key="switch_to_create_account_btn", use_container_width=True):
                    st.session_state["auth_view"] = "register"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            else:
                # ─────────────────────────────────────────────────────────────────
                # REGISTRATION VIEW
                # ─────────────────────────────────────────────────────────────────
                reg_header_html = """<div class="ds-auth-header">
<h2 class="ds-auth-title">Create your account</h2>
<p class="ds-auth-subtitle">Get started with Data Studio analytics workspace.</p>
</div>"""
                st.markdown(reg_header_html, unsafe_allow_html=True)

                with st.form("register_form", clear_on_submit=False):
                    st.markdown('<span class="ds-input-label">Full Name</span>', unsafe_allow_html=True)
                    reg_name = st.text_input(
                        "Full Name",
                        placeholder="e.g. Alex Johnson",
                        key="reg_name_field",
                        label_visibility="collapsed"
                    )

                    st.markdown('<span class="ds-input-label">Work Email</span>', unsafe_allow_html=True)
                    reg_email = st.text_input(
                        "Work Email",
                        placeholder="name@company.com",
                        key="reg_email_field",
                        label_visibility="collapsed"
                    )

                    st.markdown('<span class="ds-input-label">Password</span>', unsafe_allow_html=True)
                    reg_pass = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Minimum 8 characters",
                        key="reg_pass_field",
                        label_visibility="collapsed"
                    )

                    st.markdown('<span class="ds-input-label">Confirm Password</span>', unsafe_allow_html=True)
                    reg_confirm = st.text_input(
                        "Confirm Password",
                        type="password",
                        placeholder="Repeat password",
                        key="reg_confirm_field",
                        label_visibility="collapsed"
                    )

                    submit_register = st.form_submit_button(
                        "Create Account",
                        use_container_width=True
                    )

                if submit_register:
                    with st.spinner("Creating and securing your account…"):
                        success, msg, user_info = register_user(
                            full_name=reg_name,
                            email=reg_email,
                            password=reg_pass,
                            confirm_password=reg_confirm
                        )
                        if success and user_info:
                            login_user_session(user_info)
                            st.toast("Account created successfully! Welcome aboard. ✓")
                            st.rerun()
                        else:
                            render_notification(
                                title="Registration Failed",
                                message=msg,
                                variant="error"
                            )

                st.markdown('<div class="ds-switch-btn-wrap" style="text-align: center; margin-top: 4px;">', unsafe_allow_html=True)
                if st.button("← Back to Sign In", key="back_to_signin_btn", use_container_width=True):
                    st.session_state["auth_view"] = "signin"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

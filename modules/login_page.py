"""
DATA STUDIO v2 — Authentication & Login View (Exact Mockup Matched)
=============================================================================
High-fidelity modern split-screen SaaS login page matching the user's UI/UX design:
- Top Header: Activity Pulse Wave Logo + 'Data Studio' (left) | Dark Mode Pill (right)
- Left Column:
  - Background: Ambient Dot Grid & Fluid Wave with Connecting Accent Node
  - Hero Title: "Exploratory Data\nAnalysis Workbench ." (royal blue accent dot)
  - Hero Subtitle: "Automated profiling, statistical quality audits, interactive visualization..."
  - 4 Feature Cards Grid: Dataset Profiling, Quality Scoring, Visual Analytics, Automated Insights
- Right Column:
  - Floating Rounded Auth Card (Welcome to Data Studio)
  - Email Field with Mail SVG Icon
  - Password Field with Lock & Eye SVG Icons
  - Remember me checkbox & Forgot password? link
  - Vibrant Blue Primary "Sign In" Button
  - Centered "or" Divider
  - "Sign in with Google" card button with official multi-color Google 'G' icon
  - "Guest / Demo Access" quick action & Account Registration toggle
All underlying backend authentication, bcrypt verification, guest sessions, and Firebase logging
are preserved completely intact. Strictly unindented HTML for 100% CommonMark compliance.
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
    """Generate scoped CSS matching the mockup layout and aesthetics."""
    bg_page = "#0b0f19" if is_dark else "#fcfdff"
    bg_card = "#141c2e" if is_dark else "#ffffff"
    bg_card_subtle = "#0f1624" if is_dark else "#f8fafc"
    border_color = "rgba(30, 45, 69, 0.8)" if is_dark else "rgba(226, 232, 240, 0.85)"
    border_card = "rgba(30, 45, 69, 0.9)" if is_dark else "#e2e8f0"
    text_primary = "#f1f5f9" if is_dark else "#0f172a"
    text_secondary = "#94a3b8" if is_dark else "#475569"
    text_muted = "#64748b" if is_dark else "#64748b"
    input_bg = "#0f1624" if is_dark else "#f8fafc"
    shadow_card = "0 20px 45px -12px rgba(0, 0, 0, 0.45)" if is_dark else "0 20px 45px -12px rgba(15, 23, 42, 0.08), 0 4px 12px rgba(15, 23, 42, 0.03)"

    return f"""<style>
/* =========================================================================
   LOGIN PAGE SCOPED STYLING
   ========================================================================= */
.stApp {{
    background-color: {bg_page} !important;
}}

.main .block-container {{
    max-width: 1440px !important;
    padding-top: 18px !important;
    padding-bottom: 36px !important;
    padding-left: 48px !important;
    padding-right: 48px !important;
}}

/* Top Navigation Bar */
.ds-brand-logo-wrap {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.ds-brand-title {{
    font-size: 20px;
    font-weight: 800;
    color: {text_primary};
    letter-spacing: -0.03em;
}}

/* Left Hero Presentation */
.ds-hero-wrap {{
    padding-top: 20px;
    padding-bottom: 20px;
    position: relative;
}}

.ds-dot-matrix {{
    display: grid;
    grid-template-columns: repeat(6, 6px);
    gap: 10px;
    margin-bottom: 24px;
    opacity: {("0.25" if is_dark else "0.35")};
}}

.ds-dot-matrix span {{
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background-color: #3b82f6;
    display: block;
}}

.ds-hero-title {{
    font-size: 46px !important;
    font-weight: 800 !important;
    color: {text_primary} !important;
    letter-spacing: -0.04em !important;
    line-height: 1.12 !important;
    margin: 0 0 16px 0 !important;
}}

.ds-hero-dot {{
    color: #2563eb !important;
    font-size: 50px !important;
    line-height: 0 !important;
}}

.ds-hero-subtitle {{
    font-size: 15px !important;
    color: {text_secondary} !important;
    line-height: 1.55 !important;
    max-width: 520px !important;
    margin: 0 0 32px 0 !important;
    font-weight: 450 !important;
}}

/* 4 Feature Cards Grid */
.ds-features-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-top: 8px;
}}

.ds-feature-card {{
    background: {bg_card};
    border: 1px solid {border_color};
    border-radius: 16px;
    padding: 22px 16px 18px 16px;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    box-shadow: 0 2px 8px {("rgba(0,0,0,0.2)" if is_dark else "rgba(15,23,42,0.03)")};
    min-height: 180px;
}}

.ds-feature-card:hover {{
    transform: translateY(-3px);
    border-color: #2563eb;
    box-shadow: 0 10px 24px {("rgba(0,0,0,0.35)" if is_dark else "rgba(37,99,235,0.08)")};
}}

.ds-feature-icon-box {{
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
}}

.ds-feature-title {{
    font-size: 13.5px;
    font-weight: 700;
    color: {text_primary};
    margin-bottom: 6px;
    letter-spacing: -0.01em;
}}

.ds-feature-desc {{
    font-size: 11.5px;
    color: {text_muted};
    line-height: 1.45;
}}

/* Ambient Wave Graphic at Bottom Left */
.ds-bottom-wave-wrap {{
    margin-top: 44px;
    display: flex;
    align-items: center;
    gap: 10px;
    opacity: 0.7;
}}

.ds-bottom-node {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #3b82f6;
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
}}

.ds-bottom-line {{
    height: 2px;
    width: 80px;
    background: linear-gradient(90deg, #3b82f6, transparent);
}}

/* Right Auth Column Container Styling */
div[data-testid="column"]:nth-of-type(2) > div,
div[data-testid="stColumn"]:nth-of-type(2) > div {{
    background: {bg_card} !important;
    border: 1px solid {border_card} !important;
    border-radius: 24px !important;
    padding: 34px 32px 28px 32px !important;
    box-shadow: {shadow_card} !important;
    margin-top: 4px !important;
}}

.ds-auth-header {{
    text-align: center;
    margin-bottom: 24px;
}}

.ds-auth-title {{
    font-size: 24px !important;
    font-weight: 800 !important;
    color: {text_primary} !important;
    letter-spacing: -0.03em !important;
    margin: 0 0 6px 0 !important;
}}

.ds-auth-subtitle {{
    font-size: 13px !important;
    color: {text_secondary} !important;
    margin: 0 !important;
    font-weight: 450 !important;
}}

.ds-input-label {{
    font-size: 12.5px;
    font-weight: 600;
    color: {text_secondary};
    margin-bottom: 6px;
    display: block;
}}

/* Custom Streamlit widget overrides for Login Form */
div[data-testid="stForm"] {{
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}}

div[data-testid="stTextInput"] input {{
    background-color: {input_bg} !important;
    border: 1px solid {border_card} !important;
    border-radius: 10px !important;
    height: 44px !important;
    color: {text_primary} !important;
    font-size: 13.5px !important;
    padding-left: 40px !important;
    transition: all 0.15s ease-in-out !important;
}}

div[data-testid="stTextInput"] input:focus {{
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
    background-color: {bg_card} !important;
}}

/* Email Icon prefix in text input */
div[data-testid="stTextInput"]:has(input[aria-label="Email"]) input,
div[data-testid="stTextInput"]:has(input[key="signin_email_field"]) input {{
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="%2394a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>') !important;
    background-repeat: no-repeat !important;
    background-position: 13px center !important;
}}

/* Password Icon prefix in text input */
div[data-testid="stTextInput"]:has(input[type="password"]) input {{
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="%2394a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>') !important;
    background-repeat: no-repeat !important;
    background-position: 13px center !important;
}}

/* Sign In Submit Button */
div[data-testid="stFormSubmitButton"] button {{
    background: #2563eb !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    height: 44px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.28) !important;
    transition: all 0.2s ease !important;
    margin-top: 6px !important;
}}

div[data-testid="stFormSubmitButton"] button:hover {{
    background: #1d4ed8 !important;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.38) !important;
    transform: translateY(-1px) !important;
}}

/* Secondary Action Buttons (Google, Guest, etc.) */
.stButton>button {{
    border-radius: 10px !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}}

/* Google Button Styling with Authentic Google 'G' Icon */
.ds-google-btn-wrap div[data-testid="stButton"] button,
.ds-google-btn-wrap a[data-testid="stLinkButton"],
.ds-google-btn-wrap div[data-testid="stLinkButton"] a {{
    background: {bg_card} !important;
    border: 1px solid {border_card} !important;
    color: {text_primary} !important;
    height: 42px !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"><path fill="%234285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17Z"/><path fill="%2334A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24Z"/><path fill="%23FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15Z"/><path fill="%23EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98Z"/></svg>') !important;
    background-repeat: no-repeat !important;
    background-position: 85px center !important;
    padding-left: 36px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-decoration: none !important;
}}

.ds-google-btn-wrap div[data-testid="stButton"] button:hover,
.ds-google-btn-wrap a[data-testid="stLinkButton"]:hover,
.ds-google-btn-wrap div[data-testid="stLinkButton"] a:hover {{
    background-color: {bg_card_subtle} !important;
    border-color: #cbd5e1 !important;
    transform: translateY(-1px) !important;
    color: {text_primary} !important;
}}

/* Guest Button Styling */
.ds-guest-btn-wrap div[data-testid="stButton"] button {{
    background: transparent !important;
    border: none !important;
    color: #2563eb !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    box-shadow: none !important;
}}

.ds-guest-btn-wrap div[data-testid="stButton"] button:hover {{
    color: #1d4ed8 !important;
    background: rgba(37, 99, 235, 0.06) !important;
}}

/* Theme Toggle Pill in Header */
.ds-theme-pill-btn div[data-testid="stButton"] button {{
    background: {bg_card} !important;
    border: 1px solid {border_card} !important;
    border-radius: 9999px !important;
    padding: 5px 18px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: {text_secondary} !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    height: 38px !important;
}}

.ds-theme-pill-btn div[data-testid="stButton"] button:hover {{
    border-color: #3b82f6 !important;
    color: #2563eb !important;
}}

/* Responsive adjustments */
@media (max-width: 1024px) {{
    .ds-features-grid {{
        grid-template-columns: repeat(2, 1fr);
    }}
    .ds-hero-title {{
        font-size: 36px !important;
    }}
    .ds-google-btn-wrap div[data-testid="stButton"] button {{
        background-position: 24px center !important;
    }}
}}
</style>"""


def render_login_page() -> None:
    """Render the exact high-precision split layout matching the user design mockup."""
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

    # Inject scoped design system CSS
    st.markdown(_get_login_page_css(is_dark), unsafe_allow_html=True)

    # =========================================================================
    # 1. TOP HEADER BAR (Activity Logo + Brand on left | Dark Mode Pill on right)
    # =========================================================================
    top_col_left, top_col_right = st.columns([8.5, 3.5])

    with top_col_left:
        # Waveform / Activity Logo in Electric Blue + Brand Name
        brand_html = f"""<div class="ds-brand-logo-wrap">
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
</svg>
<span class="ds-brand-title">{APP_NAME}</span>
</div>"""
        st.markdown(brand_html, unsafe_allow_html=True)

    with top_col_right:
        # Pill shaped Dark Mode toggle with switch indicator
        toggle_label = "☀️ Light Mode  ●" if is_dark else "🌙 Dark Mode  ○"
        st.markdown('<div class="ds-theme-pill-btn">', unsafe_allow_html=True)
        if st.button(toggle_label, key="login_theme_pill_toggle", use_container_width=True):
            st.session_state["theme"] = "Light" if is_dark else "Dark"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # 2. MAIN 2-COLUMN SPLIT SCREEN (Left: Hero & 4 Cards | Right: Floating Auth Card)
    # =========================================================================
    left_col, right_col = st.columns([1.35, 1.0], gap="large")

    # ─────────────────────────────────────────────────────────────────────────
    # LEFT COLUMN: Hero Title, Subtitle, and 4 Feature Cards
    # ─────────────────────────────────────────────────────────────────────────
    with left_col:
        hero_html = """<div class="ds-hero-wrap">
<div class="ds-dot-matrix">
<span></span><span></span><span></span><span></span><span></span><span></span>
<span></span><span></span><span></span><span></span><span></span><span></span>
<span></span><span></span><span></span><span></span><span></span><span></span>
<span></span><span></span><span></span><span></span><span></span><span></span>
</div>
<h1 class="ds-hero-title">Exploratory Data<br>Analysis Workbench <span class="ds-hero-dot">.</span></h1>
<p class="ds-hero-subtitle">Automated profiling, statistical quality audits, interactive visualization, and targeted analytical workflows.</p>
</div>"""
        st.markdown(hero_html, unsafe_allow_html=True)

        # 4 Feature Cards Grid
        cards_html = """<div class="ds-features-grid">
<div class="ds-feature-card">
<div class="ds-feature-icon-box" style="background: rgba(37, 99, 235, 0.09); color: #2563eb;">
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path><path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"></path></svg>
</div>
<div class="ds-feature-title">Dataset Profiling</div>
<div class="ds-feature-desc">Schema inspection, null auditing, and type classification.</div>
</div>
<div class="ds-feature-card">
<div class="ds-feature-icon-box" style="background: rgba(16, 185, 129, 0.1); color: #059669;">
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><path d="m9 12 2 2 4-4"></path></svg>
</div>
<div class="ds-feature-title">Quality Scoring</div>
<div class="ds-feature-desc">Composite health rating across completeness and uniqueness.</div>
</div>
<div class="ds-feature-card">
<div class="ds-feature-icon-box" style="background: rgba(124, 58, 237, 0.1); color: #7c3aed;">
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"></path><rect width="4" height="7" x="7" y="10" rx="1"></rect><rect width="4" height="11" x="13" y="6" rx="1"></rect><rect width="4" height="4" x="19" y="13" rx="1"></rect></svg>
</div>
<div class="ds-feature-title">Visual Analytics</div>
<div class="ds-feature-desc">Correlation heatmaps, distribution grids, and outliers.</div>
</div>
<div class="ds-feature-card">
<div class="ds-feature-icon-box" style="background: rgba(217, 119, 6, 0.1); color: #d97706;">
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"></path><path d="M9 18h6"></path><path d="M10 22h4"></path></svg>
</div>
<div class="ds-feature-title">Automated Insights</div>
<div class="ds-feature-desc">Natural language querying and smart analytical summaries.</div>
</div>
</div>
<div class="ds-bottom-wave-wrap">
<div class="ds-bottom-node"></div>
<div class="ds-bottom-line"></div>
</div>"""
        st.markdown(cards_html, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # RIGHT COLUMN: Floating Auth Card (Welcome to Data Studio)
    # ─────────────────────────────────────────────────────────────────────────
    with right_col:
        # Auth View state (Sign In vs Registration vs Forgot Password modal)
        if "auth_view" not in st.session_state:
            st.session_state["auth_view"] = "signin"

        if st.session_state["auth_view"] == "signin":
            # Header
            header_html = """<div class="ds-auth-header">
<h2 class="ds-auth-title">Welcome to Data Studio</h2>
<p class="ds-auth-subtitle">Sign in to access your analytics workspace.</p>
</div>"""
            st.markdown(header_html, unsafe_allow_html=True)

            # Main Sign In Form
            with st.form("signin_form", clear_on_submit=False):
                # Email Input Field
                st.markdown('<span class="ds-input-label">Email</span>', unsafe_allow_html=True)
                email = st.text_input(
                    "Email",
                    value="",
                    placeholder="name@company.com",
                    key="signin_email_field",
                    label_visibility="collapsed"
                )

                # Password Input Field
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                st.markdown('<span class="ds-input-label">Password</span>', unsafe_allow_html=True)
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="signin_password_field",
                    label_visibility="collapsed"
                )

                # Remember Me & Forgot Password Row
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                col_rem, col_forgot = st.columns([1.1, 1.1])
                with col_rem:
                    remember_me = st.checkbox("Remember me", value=True, key="signin_remember_me")
                with col_forgot:
                    forgot_html = """<div style="text-align: right; padding-top: 4px;">
<a href="#forgot" style="color: #2563eb; font-size: 12.5px; font-weight: 500; text-decoration: none;">Forgot password?</a>
</div>"""
                    st.markdown(forgot_html, unsafe_allow_html=True)

                # Primary Sign In Action
                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
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

            # "or" Divider
            divider_html = f"""<div style="display: flex; align-items: center; margin: 16px 0 14px 0; gap: 12px;">
<div style="flex: 1; height: 1px; background: {('rgba(30, 45, 69, 0.9)' if is_dark else '#e2e8f0')};"></div>
<span style="font-size: 12px; color: {('#94a3b8' if is_dark else '#94a3b8')}; font-weight: 500;">or</span>
<div style="flex: 1; height: 1px; background: {('rgba(30, 45, 69, 0.9)' if is_dark else '#e2e8f0')};"></div>
</div>"""
            st.markdown(divider_html, unsafe_allow_html=True)

            # Google Sign In Button with Official Multi-Color Google G SVG Icon
            st.markdown('<div class="ds-google-btn-wrap">', unsafe_allow_html=True)
            google_auth_url = get_google_auth_url()
            if google_auth_url:
                st.link_button("Sign in with Google", url=google_auth_url, use_container_width=True)
            else:
                if st.button("Sign in with Google", key="google_signin_action_btn", use_container_width=True):
                    render_google_setup_dialog(is_dark=is_dark)
            st.markdown('</div>', unsafe_allow_html=True)

            # Guest / Demo Access & Registration switch
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            st.markdown('<div class="ds-guest-btn-wrap" style="text-align: center;">', unsafe_allow_html=True)
            if st.button("👤 Guest / Demo Access", key="guest_access_direct_btn", use_container_width=True):
                start_guest_session()
                st.toast("Entered Guest Demo mode.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            # Account creation switch link
            switch_html = """<div style="text-align: center; margin-top: 14px; font-size: 12.5px; color: #64748b;">Don't have an account?</div>"""
            st.markdown(switch_html, unsafe_allow_html=True)
            if st.button("Create an account", key="switch_to_create_account_btn", use_container_width=True):
                st.session_state["auth_view"] = "register"
                st.rerun()

        else:
            # ─────────────────────────────────────────────────────────────────
            # REGISTRATION VIEW
            # ─────────────────────────────────────────────────────────────────
            reg_header_html = """<div class="ds-auth-header">
<h2 class="ds-auth-title">Create Account</h2>
<p class="ds-auth-subtitle">Join Data Studio to unlock full analytics power.</p>
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

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                st.markdown('<span class="ds-input-label">Email</span>', unsafe_allow_html=True)
                reg_email = st.text_input(
                    "Email",
                    placeholder="name@company.com",
                    key="reg_email_field",
                    label_visibility="collapsed"
                )

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                st.markdown('<span class="ds-input-label">Password</span>', unsafe_allow_html=True)
                reg_pass = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Minimum 8 characters",
                    key="reg_pass_field",
                    label_visibility="collapsed"
                )

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                st.markdown('<span class="ds-input-label">Confirm Password</span>', unsafe_allow_html=True)
                reg_confirm = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Repeat password",
                    key="reg_confirm_field",
                    label_visibility="collapsed"
                )

                st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
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

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("← Back to Sign In", key="back_to_signin_btn", use_container_width=True):
                st.session_state["auth_view"] = "signin"
                st.rerun()

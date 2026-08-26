"""
DATA STUDIO v2 — Authentication & Login View (Pixel-Perfect Mockup Matched)
=============================================================================
High-fidelity modern split-screen SaaS login page matching the user's exact mockup:
- Top Header:
  - Brand Bar Chart Icon + 'Data Studio' (left)
  - 'Need help?' + Dark/Light Mode Pill Toggle (right)
- Left Column:
  - Two-line Hero Title:
    "Understand Your Data." (dark)
    "Make Better Decisions." (royal blue)
  - Subtitle: "Data Studio is your intelligent analytics workspace to explore, prepare, visualize, and gain insights from your data."
  - Ambient Analytics Artwork with connecting nodes, subtle charts & dot grids
  - 4 Feature Cards Grid:
    1. Dataset Profiling (Schema inspection, null auditing, and type classification)
    2. Quality Scoring (Composite health rating across completeness and uniqueness)
    3. Visual Analytics (Correlation heatmaps, distribution grids, and outliers)
    4. Automated Insights (Natural language querying and smart analytical summaries)
  - Security Badges Footer:
    "🔒 Your data is secure and private. | No data used for training | Enterprise-grade security"
- Right Column:
  - Elevated Rounded Auth Card (18px radius, soft shadow, clean white/dark surface)
  - Heading: "Sign in to Data Studio"
  - Subtitle: "Access your workspace and continue your analytics journey."
  - "Sign in with Google" button with official multi-color Google 'G' icon
  - Centered "OR" Divider
  - Email address & Password fields
  - Remember me & Forgot password? row
  - Royal Blue "Sign in" Primary Button
  - Centered "OR" Divider
  - "👤 Continue as Guest / Demo" Action Button
  - "Don't have an account? Create an account" Switch Link
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
    """Generate scoped CSS matching the user's mockup layout and aesthetics."""
    bg_page = "#0b0f19" if is_dark else "#f3f6fb"
    bg_card = "#141c2e" if is_dark else "#ffffff"
    bg_card_subtle = "#0f1624" if is_dark else "#f8fafc"
    border_color = "rgba(51, 65, 85, 0.7)" if is_dark else "#e2e8f0"
    border_card = "rgba(51, 65, 85, 0.85)" if is_dark else "#e2e8f0"
    text_primary = "#f1f5f9" if is_dark else "#0f172a"
    text_secondary = "#94a3b8" if is_dark else "#475569"
    text_muted = "#64748b" if is_dark else "#64748b"
    input_bg = "#0f1624" if is_dark else "#ffffff"
    shadow_card = "0 20px 45px -10px rgba(0, 0, 0, 0.45), 0 0 1px rgba(0, 0, 0, 0.2)" if is_dark else "0 20px 45px -10px rgba(15, 23, 42, 0.08), 0 0 1px rgba(0, 0, 0, 0.05)"
    feature_card_bg = "#111827" if is_dark else "#ffffff"

    return f"""<style>
/* =========================================================================
   LOGIN PAGE SCOPED STYLING — EXACT MOCKUP MATCH
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
    background-image: radial-gradient(circle at 10% 20%, {('rgba(37,99,235,0.06)' if not is_dark else 'rgba(37,99,235,0.12)')} 0%, transparent 40%),
                      radial-gradient(circle at 90% 80%, {('rgba(56,189,248,0.05)' if not is_dark else 'rgba(56,189,248,0.08)')} 0%, transparent 40%) !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    font-family: 'Source Sans 3', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}}

html, body, .stApp, section[data-testid="stMain"] {{
    overflow-y: auto !important;
    overflow-x: hidden !important;
}}

/* Hide default Streamlit chrome on Login */
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
    max-width: 1200px !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding-top: clamp(14px, 2.2vh, 28px) !important;
    padding-bottom: clamp(16px, 2.5vh, 32px) !important;
    padding-left: clamp(20px, 3vw, 40px) !important;
    padding-right: clamp(20px, 3vw, 40px) !important;
    box-sizing: border-box !important;
}}

/* =========================================================================
   TOP BRAND BAR
   ========================================================================= */
.ds-mock-topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    margin-bottom: clamp(14px, 2vh, 26px);
}}

.ds-mock-brand {{
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
}}

.ds-mock-logo-icon {{
    width: 32px;
    height: 32px;
    border-radius: 7px;
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ffffff;
    box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3);
}}

.ds-mock-brand-name {{
    font-size: 21px;
    font-weight: 700;
    color: {text_primary};
    letter-spacing: -0.025em;
}}

.ds-mock-top-actions {{
    display: flex;
    align-items: center;
    gap: 16px;
}}

.ds-mock-help-link {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 500;
    color: #2563eb;
    text-decoration: none;
    transition: opacity 0.15s ease;
}}

.ds-mock-help-link:hover {{
    text-decoration: underline;
    opacity: 0.85;
}}

/* Theme Toggle Pill in Header */
.ds-theme-pill-btn div[data-testid="stButton"] button {{
    background: {bg_card} !important;
    border: 1px solid {border_color} !important;
    border-radius: 6px !important;
    padding: 4px 12px !important;
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

/* =========================================================================
   LEFT MARKETING COLUMN
   ========================================================================= */
.ds-mock-left-wrap {{
    display: flex;
    flex-direction: column;
    justify-content: center;
    position: relative;
    padding-right: clamp(10px, 1.5vw, 24px);
}}

/* Background subtle analytics graphic behind feature cards */
.ds-mock-bg-art {{
    position: absolute;
    top: 30px;
    right: 0;
    width: 320px;
    height: 240px;
    pointer-events: none;
    opacity: {('0.25' if is_dark else '0.45')};
    z-index: 0;
}}

.ds-mock-hero-title {{
    font-size: clamp(30px, 3.2vw, 42px);
    font-weight: 800;
    color: {text_primary};
    line-height: 1.15;
    letter-spacing: -0.03em;
    margin: 0 0 14px 0;
    position: relative;
    z-index: 1;
}}

.ds-mock-hero-accent {{
    color: #2563eb;
    display: block;
}}

.ds-mock-hero-desc {{
    font-size: 15.5px;
    font-weight: 400;
    color: {text_secondary};
    line-height: 1.55;
    margin: 0 0 clamp(18px, 2.5vh, 28px) 0;
    max-width: 500px;
    position: relative;
    z-index: 1;
}}

/* 2x2 Feature Cards Grid */
.ds-mock-features-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin-bottom: clamp(16px, 2.2vh, 26px);
    position: relative;
    z-index: 1;
}}

.ds-mock-feature-card {{
    background: {feature_card_bg};
    border: 1px solid {border_color};
    border-radius: 14px;
    padding: 16px 16px 14px 16px;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
    display: flex;
    align-items: flex-start;
    gap: 12px;
    position: relative;
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}}

.ds-mock-feature-card:hover {{
    transform: translateY(-2px);
    border-color: rgba(37, 99, 235, 0.35);
    box-shadow: 0 8px 20px rgba(37, 99, 235, 0.08);
}}

.ds-mock-card-icon-box {{
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background: rgba(37, 99, 235, 0.08);
    color: #2563eb;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    border: 1px solid rgba(37, 99, 235, 0.15);
}}

.ds-mock-card-content {{
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 70px;
    justify-content: space-between;
}}

.ds-mock-card-title {{
    font-size: 15px;
    font-weight: 700;
    color: {text_primary};
    margin: 0 0 4px 0;
    letter-spacing: -0.01em;
}}

.ds-mock-card-desc {{
    font-size: 12.5px;
    color: {text_secondary};
    line-height: 1.4;
    margin: 0 0 6px 0;
}}

.ds-mock-card-arrow {{
    align-self: flex-end;
    color: #2563eb;
    font-size: 14px;
    font-weight: 700;
    line-height: 1;
}}

/* Security Trust Badges */
.ds-mock-trust-bar {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 12.5px;
    color: {text_secondary};
    flex-wrap: wrap;
    position: relative;
    z-index: 1;
}}

.ds-mock-trust-item {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
}}

.ds-mock-trust-divider {{
    color: {('rgba(51,65,85,0.6)' if is_dark else '#cbd5e1')};
}}

/* =========================================================================
   RIGHT AUTH CARD CONTAINER (Elevated, 18px Radius, Soft Shadow)
   ========================================================================= */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {bg_card} !important;
    border: 1px solid {border_card} !important;
    border-radius: 18px !important;
    padding: clamp(22px, 2.8vh, 32px) clamp(22px, 2.5vw, 34px) !important;
    box-shadow: {shadow_card} !important;
    box-sizing: border-box !important;
    width: 100% !important;
    max-width: 440px !important;
    margin: 0 auto !important;
}}

div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {{
    gap: 6px !important;
}}

div[data-testid="stForm"] > div[data-testid="stVerticalBlock"] {{
    gap: 4px !important;
}}

.ds-mock-auth-header {{
    text-align: center;
    margin-bottom: 12px;
}}

.ds-mock-auth-title {{
    font-size: 24px !important;
    font-weight: 750 !important;
    color: {text_primary} !important;
    letter-spacing: -0.025em !important;
    margin: 0 0 4px 0 !important;
    line-height: 1.2 !important;
}}

.ds-mock-auth-subtitle {{
    font-size: 13.5px !important;
    color: {text_secondary} !important;
    margin: 0 !important;
    font-weight: 400 !important;
    line-height: 1.4 !important;
}}

.ds-input-label {{
    font-size: 13.5px;
    font-weight: 600;
    color: {text_primary};
    margin: 4px 0 2px 1px;
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
    border-radius: 8px !important;
    color: {text_primary} !important;
    font-size: 14.5px !important;
    height: 40px !important;
    padding: 8px 12px !important;
    box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.02) !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}}

div[data-testid="stTextInput"] input:focus {{
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
    outline: none !important;
}}

div[data-testid="stTextInput"] input::placeholder {{
    color: {text_muted} !important;
    font-size: 14px !important;
}}

/* Form Submit Button */
div[data-testid="stFormSubmitButton"] button {{
    background: #2563eb !important;
    color: #ffffff !important;
    border: 1px solid #1d4ed8 !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    border-radius: 8px !important;
    height: 42px !important;
    box-shadow: 0 2px 6px rgba(37, 99, 235, 0.25) !important;
    transition: all 0.15s ease !important;
    margin-top: 6px !important;
}}

div[data-testid="stFormSubmitButton"] button:hover {{
    background: #1d4ed8 !important;
    border-color: #1e40af !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35) !important;
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
    font-weight: 600 !important;
    font-size: 14.5px !important;
    border-radius: 8px !important;
    height: 42px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-decoration: none !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
    transition: all 0.15s ease !important;
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"><path fill="%234285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17Z"/><path fill="%2334A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24Z"/><path fill="%23FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15Z"/><path fill="%23EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98Z"/></svg>') !important;
    background-repeat: no-repeat !important;
    background-position: 18px center !important;
    padding-left: 28px !important;
}}

.ds-google-btn-wrap div[data-testid="stLinkButton"] a:hover,
.ds-google-btn-wrap div[data-testid="stButton"] button:hover {{
    background-color: {bg_card_subtle} !important;
    border-color: {('#475569' if is_dark else '#94a3b8')} !important;
    color: {text_primary} !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
}}

/* Guest / Demo Button Styling */
.ds-guest-btn-wrap div[data-testid="stButton"] button {{
    background: {bg_card} !important;
    border: 1px solid {border_color} !important;
    color: {text_primary} !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    border-radius: 8px !important;
    height: 40px !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
}}

.ds-guest-btn-wrap div[data-testid="stButton"] button:hover {{
    color: #2563eb !important;
    border-color: rgba(37, 99, 235, 0.4) !important;
    background: {('rgba(37,99,235,0.08)' if is_dark else 'rgba(37,99,235,0.04)')} !important;
}}

/* Switch View Buttons */
.ds-switch-btn-wrap div[data-testid="stButton"] button {{
    background: transparent !important;
    border: none !important;
    color: #2563eb !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 3px 8px !important;
    height: auto !important;
    box-shadow: none !important;
}}

.ds-switch-btn-wrap div[data-testid="stButton"] button:hover {{
    background: transparent !important;
    color: #1d4ed8 !important;
    text-decoration: underline !important;
}}

/* Checkbox label */
div[data-testid="stCheckbox"] label span {{
    font-size: 13.5px !important;
    color: {text_secondary} !important;
}}

/* Responsive adjustments for Tablets and Mobile */
@media (max-width: 900px) {{
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stVerticalBlockBorderWrapper"]) > div[data-testid="column"]:nth-of-type(1),
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stVerticalBlockBorderWrapper"]) > div[data-testid="stColumn"]:nth-of-type(1) {{
        display: none !important;
    }}

    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stVerticalBlockBorderWrapper"]) > div[data-testid="column"]:nth-of-type(2),
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stVerticalBlockBorderWrapper"]) > div[data-testid="stColumn"]:nth-of-type(2) {{
        width: 100% !important;
        max-width: 440px !important;
        margin: 0 auto !important;
        flex: 1 1 100% !important;
    }}

    .main .block-container,
    div[data-testid="stMainBlockContainer"] {{
        padding: 16px 16px !important;
    }}
}}
</style>"""


def render_login_page() -> None:
    """Render the high-fidelity SaaS login screen matching the mockup."""
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
    border_val = "rgba(51, 65, 85, 0.7)" if is_dark else "#e2e8f0"

    # Inject scoped design system CSS
    st.markdown(_get_login_page_css(is_dark), unsafe_allow_html=True)

    # =========================================================================
    # 1. TOP HEADER (Brand Logo + Need help? + Light/Dark Toggle)
    # =========================================================================
    top_col_left, top_col_right = st.columns([7.5, 4.5])

    with top_col_left:
        brand_html = f"""<div class="ds-mock-topbar">
<div class="ds-mock-brand">
<div class="ds-mock-logo-icon">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
<line x1="18" y1="20" x2="18" y2="10"></line>
<line x1="12" y1="20" x2="12" y2="4"></line>
<line x1="6" y1="20" x2="6" y2="14"></line>
</svg>
</div>
<span class="ds-mock-brand-name">{APP_NAME}</span>
</div>
</div>"""
        st.markdown(brand_html, unsafe_allow_html=True)

    with top_col_right:
        help_col, theme_col = st.columns([1.1, 1.2])
        with help_col:
            help_html = """<div style="text-align: right; padding-top: 5px;">
<a href="#help" class="ds-mock-help-link">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>
Need help?
</a>
</div>"""
            st.markdown(help_html, unsafe_allow_html=True)

        with theme_col:
            toggle_label = "☀️ Light Mode" if is_dark else "🌙 Dark Mode"
            st.markdown('<div class="ds-theme-pill-btn">', unsafe_allow_html=True)
            if st.button(toggle_label, key="login_theme_pill_toggle", use_container_width=True):
                st.session_state["theme"] = "Light" if is_dark else "Dark"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # =========================================================================
    # 2. MAIN 2-COLUMN SPLIT SCREEN
    # =========================================================================
    left_col, right_col = st.columns([1.3, 1.0], gap="large")

    # ─────────────────────────────────────────────────────────────────────────
    # LEFT COLUMN: Hero Headline, 2x2 Feature Cards Grid & Security Badges
    # ─────────────────────────────────────────────────────────────────────────
    with left_col:
        chart_accent = "#38bdf8" if is_dark else "#2563eb"
        card_border = "rgba(51, 65, 85, 0.7)" if is_dark else "#e2e8f0"

        left_html = f"""<div class="ds-mock-left-wrap">
<!-- Subtle ambient background analytics art -->
<svg class="ds-mock-bg-art" viewBox="0 0 320 240" fill="none" xmlns="http://www.w3.org/2000/svg">
<circle cx="280" cy="50" r="3" fill="{chart_accent}" fill-opacity="0.6"/>
<circle cx="210" cy="80" r="3" fill="{chart_accent}" fill-opacity="0.6"/>
<circle cx="160" cy="120" r="3" fill="{chart_accent}" fill-opacity="0.6"/>
<circle cx="110" cy="90" r="3" fill="{chart_accent}" fill-opacity="0.6"/>
<line x1="110" y1="90" x2="160" y2="120" stroke="{chart_accent}" stroke-opacity="0.3" stroke-width="1.5" stroke-dasharray="3 3"/>
<line x1="160" y1="120" x2="210" y2="80" stroke="{chart_accent}" stroke-opacity="0.3" stroke-width="1.5" stroke-dasharray="3 3"/>
<line x1="210" y1="80" x2="280" y2="50" stroke="{chart_accent}" stroke-opacity="0.3" stroke-width="1.5" stroke-dasharray="3 3"/>
<rect x="230" y="110" width="12" height="60" rx="3" fill="{chart_accent}" fill-opacity="0.15"/>
<rect x="248" y="90" width="12" height="80" rx="3" fill="{chart_accent}" fill-opacity="0.25"/>
<rect x="266" y="70" width="12" height="100" rx="3" fill="{chart_accent}" fill-opacity="0.35"/>
<path d="M 120 180 A 50 50 0 0 1 170 130 L 170 180 Z" fill="{chart_accent}" fill-opacity="0.15"/>
<circle cx="240" cy="20" r="1.5" fill="{chart_accent}" fill-opacity="0.4"/>
<circle cx="255" cy="20" r="1.5" fill="{chart_accent}" fill-opacity="0.4"/>
<circle cx="270" cy="20" r="1.5" fill="{chart_accent}" fill-opacity="0.4"/>
<circle cx="240" cy="35" r="1.5" fill="{chart_accent}" fill-opacity="0.4"/>
<circle cx="255" cy="35" r="1.5" fill="{chart_accent}" fill-opacity="0.4"/>
<circle cx="270" cy="35" r="1.5" fill="{chart_accent}" fill-opacity="0.4"/>
</svg>

<h1 class="ds-mock-hero-title">
Understand Your Data.<br>
<span class="ds-mock-hero-accent">Make Better Decisions.</span>
</h1>

<p class="ds-mock-hero-desc">
Data Studio is your intelligent analytics workspace to explore, prepare, visualize, and gain insights from your data.
</p>

<!-- 2x2 Feature Cards Grid -->
<div class="ds-mock-features-grid">
<!-- Card 1: Dataset Profiling -->
<div class="ds-mock-feature-card">
<div class="ds-mock-card-icon-box">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
<polyline points="14 2 14 8 20 8"></polyline>
<line x1="16" y1="13" x2="8" y2="13"></line>
<line x1="16" y1="17" x2="8" y2="17"></line>
<polyline points="10 9 9 9 8 9"></polyline>
</svg>
</div>
<div class="ds-mock-card-content">
<div>
<div class="ds-mock-card-title">Dataset Profiling</div>
<div class="ds-mock-card-desc">Schema inspection, null auditing, and type classification.</div>
</div>
<span class="ds-mock-card-arrow">→</span>
</div>
</div>

<!-- Card 2: Quality Scoring -->
<div class="ds-mock-feature-card">
<div class="ds-mock-card-icon-box">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
<polygon points="12 8 13.3 11 16.5 11.3 14 13.5 14.8 16.7 12 15 9.2 16.7 10 13.5 7.5 11.3 10.7 11 12 8"></polygon>
</svg>
</div>
<div class="ds-mock-card-content">
<div>
<div class="ds-mock-card-title">Quality Scoring</div>
<div class="ds-mock-card-desc">Composite health rating across completeness and uniqueness.</div>
</div>
<span class="ds-mock-card-arrow">→</span>
</div>
</div>

<!-- Card 3: Visual Analytics -->
<div class="ds-mock-feature-card">
<div class="ds-mock-card-icon-box">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<line x1="18" y1="20" x2="18" y2="10"></line>
<line x1="12" y1="20" x2="12" y2="4"></line>
<line x1="6" y1="20" x2="6" y2="14"></line>
</svg>
</div>
<div class="ds-mock-card-content">
<div>
<div class="ds-mock-card-title">Visual Analytics</div>
<div class="ds-mock-card-desc">Correlation heatmaps, distribution grids, and outliers.</div>
</div>
<span class="ds-mock-card-arrow">→</span>
</div>
</div>

<!-- Card 4: Automated Insights -->
<div class="ds-mock-feature-card">
<div class="ds-mock-card-icon-box">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
<polygon points="12 7 12.8 9 14.8 9.2 13.2 10.7 13.7 12.8 12 11.7 10.3 12.8 10.8 10.7 9.2 9.2 11.2 9 12 7"></polygon>
</svg>
</div>
<div class="ds-mock-card-content">
<div>
<div class="ds-mock-card-title">Automated Insights</div>
<div class="ds-mock-card-desc">Natural language querying and smart analytical summaries.</div>
</div>
<span class="ds-mock-card-arrow">→</span>
</div>
</div>
</div>

<!-- Security Trust Badges -->
<div class="ds-mock-trust-bar">
<span class="ds-mock-trust-item">
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
Your data is secure and private.
</span>
<span class="ds-mock-trust-divider">|</span>
<span class="ds-mock-trust-item">No data used for training</span>
<span class="ds-mock-trust-divider">|</span>
<span class="ds-mock-trust-item">Enterprise-grade security</span>
</div>
</div>"""
        st.markdown(left_html, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # RIGHT COLUMN: Elevated Rounded Authentication Card
    # ─────────────────────────────────────────────────────────────────────────
    with right_col:
        with st.container(border=True):
            if "auth_view" not in st.session_state:
                st.session_state["auth_view"] = "signin"

            if st.session_state["auth_view"] == "signin":
                # Header
                header_html = """<div class="ds-mock-auth-header">
<h2 class="ds-mock-auth-title">Sign in to Data Studio</h2>
<p class="ds-mock-auth-subtitle">Access your workspace and continue your analytics journey.</p>
</div>"""
                st.markdown(header_html, unsafe_allow_html=True)

                # Google Sign In Button
                st.markdown('<div class="ds-google-btn-wrap">', unsafe_allow_html=True)
                google_auth_url = get_google_auth_url()
                if google_auth_url:
                    st.link_button("Sign in with Google", url=google_auth_url, use_container_width=True)
                else:
                    if st.button("Sign in with Google", key="google_signin_action_btn", use_container_width=True):
                        render_google_setup_dialog(is_dark=is_dark)
                st.markdown('</div>', unsafe_allow_html=True)

                # Centered "OR" Divider
                divider_html = f"""<div style="display: flex; align-items: center; margin: 12px 0 8px 0; gap: 10px;">
<div style="flex: 1; height: 1px; background: {('rgba(51, 65, 85, 0.6)' if is_dark else '#e2e8f0')};"></div>
<span style="font-size: 11px; color: {('#94a3b8' if is_dark else '#94a3b8')}; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">OR</span>
<div style="flex: 1; height: 1px; background: {('rgba(51, 65, 85, 0.6)' if is_dark else '#e2e8f0')};"></div>
</div>"""
                st.markdown(divider_html, unsafe_allow_html=True)

                # Main Sign In Form
                with st.form("signin_form", clear_on_submit=False):
                    st.markdown('<span class="ds-input-label">Email address</span>', unsafe_allow_html=True)
                    email = st.text_input(
                        "Email address",
                        value="",
                        placeholder="Enter your email",
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
                        "Sign in",
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

                # Second "OR" Divider
                divider_or2_html = f"""<div style="display: flex; align-items: center; margin: 8px 0 8px 0; gap: 10px;">
<div style="flex: 1; height: 1px; background: {('rgba(51, 65, 85, 0.6)' if is_dark else '#e2e8f0')};"></div>
<span style="font-size: 11px; color: {('#94a3b8' if is_dark else '#94a3b8')}; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">OR</span>
<div style="flex: 1; height: 1px; background: {('rgba(51, 65, 85, 0.6)' if is_dark else '#e2e8f0')};"></div>
</div>"""
                st.markdown(divider_or2_html, unsafe_allow_html=True)

                # Guest / Demo Access Button
                st.markdown('<div class="ds-guest-btn-wrap" style="text-align: center;">', unsafe_allow_html=True)
                if st.button("👤 Continue as Guest / Demo", key="guest_access_direct_btn", use_container_width=True):
                    start_guest_session()
                    st.toast("Entered Guest Demo mode.")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

                # Account creation switch link
                st.markdown('<div class="ds-switch-btn-wrap" style="text-align: center; margin-top: 8px;">', unsafe_allow_html=True)
                if st.button("Don't have an account? Create an account", key="switch_to_create_account_btn", use_container_width=True):
                    st.session_state["auth_view"] = "register"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            else:
                # ─────────────────────────────────────────────────────────────────
                # REGISTRATION VIEW
                # ─────────────────────────────────────────────────────────────────
                reg_header_html = """<div class="ds-mock-auth-header">
<h2 class="ds-mock-auth-title">Create your account</h2>
<p class="ds-mock-auth-subtitle">Get started with Data Studio analytics workspace.</p>
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

                    st.markdown('<span class="ds-input-label">Email address</span>', unsafe_allow_html=True)
                    reg_email = st.text_input(
                        "Email address",
                        placeholder="Enter your email",
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

                st.markdown('<div class="ds-switch-btn-wrap" style="text-align: center; margin-top: 6px;">', unsafe_allow_html=True)
                if st.button("← Back to Sign In", key="back_to_signin_btn", use_container_width=True):
                    st.session_state["auth_view"] = "signin"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

"""
DATA STUDIO v2 — Authentication & Login View (Premium UI v2)
=============================================================================
Professional full-screen authentication interface. Visual redesign only.
All auth business logic (authenticate_user, register_user, etc.) unchanged.
"""
from typing import Optional
import streamlit as st

from modules.config import APP_NAME, APP_VERSION
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


def render_login_page() -> None:
    """Render the full-screen premium light-first authentication page."""
    current_theme = st.session_state.get("theme", "Light")

    # Top bar: version info + theme toggle
    top_l, top_r = st.columns([8, 2])
    with top_l:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;padding:6px 0;">'
            f'<div style="width:24px;height:24px;background:var(--accent);border-radius:5px;'
            f'display:flex;align-items:center;justify-content:center;color:#fff;'
            f'font-weight:700;font-size:10px;">DS</div>'
            f'<span style="font-size:14px;font-weight:700;color:var(--text-primary);'
            f'letter-spacing:-0.025em;">{APP_NAME}</span>'
            f'<span style="font-size:10px;font-family:var(--font-mono);color:var(--text-muted);">'
            f'{APP_VERSION}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    with top_r:
        is_dark = current_theme == "Dark"
        icon_svg = get_icon_svg("sun" if is_dark else "moon", 13)
        toggle_label = f"{'☀️' if is_dark else '🌙'} {'Light' if is_dark else 'Dark'}"
        if st.button(toggle_label, key="login_theme_toggle_btn", use_container_width=True):
            st.session_state["theme"] = "Light" if is_dark else "Dark"
            st.rerun()

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    col_hero, col_auth = st.columns([5.5, 4.5], gap="large")

    # =========================================================================
    # LEFT COLUMN — Brand Showcase & Platform Capabilities
    # =========================================================================
    with col_hero:
        hero_html = (
            f'<div class="ds-login-hero">'
            # Header
            f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;">'
            f'<div class="ds-brand-badge" style="width:42px;height:42px;font-size:16px;">DS</div>'
            f'<div>'
            f'<div style="font-size:22px;font-weight:800;color:var(--text-primary);'
            f'letter-spacing:-0.035em;line-height:1.1;">{APP_NAME}</div>'
            f'<div style="font-size:11px;font-family:var(--font-mono);color:var(--accent);">'
            f'{APP_VERSION} · Analytics Platform</div>'
            f'</div>'
            f'</div>'
            # Headline
            f'<div style="font-size:17px;font-weight:700;color:var(--text-primary);'
            f'letter-spacing:-0.025em;margin-bottom:6px;">Upload, explore, and understand your data.</div>'
            f'<div style="font-size:13px;color:var(--text-secondary);line-height:1.55;margin-bottom:20px;">'
            f'A comprehensive local analytics platform providing data quality profiling, '
            f'dynamic dashboards, visualization studio, and AI-powered exploration.'
            f'</div>'
            # Feature cards
            f'<div class="ds-login-feature-list">'
            f'<div class="ds-login-feature">'
            f'<div class="ds-login-feature-icon">{get_icon_svg("database", 15)}</div>'
            f'<div>'
            f'<div class="ds-login-feature-title">Dataset Workspace</div>'
            f'<div class="ds-login-feature-desc">Multi-format CSV/XLSX loaders with automatic schema profiling and type inference.</div>'
            f'</div>'
            f'</div>'
            f'<div class="ds-login-feature">'
            f'<div class="ds-login-feature-icon">{get_icon_svg("layout-dashboard", 15)}</div>'
            f'<div>'
            f'<div class="ds-login-feature-title">Dynamic Dashboards</div>'
            f'<div class="ds-login-feature-desc">Automatic feature prioritization, theme-adaptive Plotly charts, and factual insights.</div>'
            f'</div>'
            f'</div>'
            f'<div class="ds-login-feature">'
            f'<div class="ds-login-feature-icon">{get_icon_svg("shield-check", 15)}</div>'
            f'<div>'
            f'<div class="ds-login-feature-title">Data Quality Engine</div>'
            f'<div class="ds-login-feature-desc">Transparent 0–100 health scoring across completeness, uniqueness, and validity.</div>'
            f'</div>'
            f'</div>'
            f'<div class="ds-login-feature">'
            f'<div class="ds-login-feature-icon">{get_icon_svg("bar-chart-3", 15)}</div>'
            f'<div>'
            f'<div class="ds-login-feature-title">Visualization Studio</div>'
            f'<div class="ds-login-feature-desc">Point-and-click chart builder with 8+ chart types, no-code configuration.</div>'
            f'</div>'
            f'</div>'
            f'</div>'
            # Trust badge footer
            f'<div class="ds-login-trust">'
            f'{get_icon_svg("shield", 13)}'
            f'<span>Secure bcrypt password hashing · Isolated session architecture</span>'
            f'</div>'
            f'</div>'
        )
        st.markdown(hero_html, unsafe_allow_html=True)

    # =========================================================================
    # RIGHT COLUMN — Auth Tabs & Guest Access
    # =========================================================================
    with col_auth:
        # Auth panel header
        st.markdown(
            '<div style="margin-bottom:14px;">'
            '<div style="font-size:18px;font-weight:700;color:var(--text-primary);'
            'letter-spacing:-0.025em;">Access Workspace</div>'
            '<div style="font-size:12.5px;color:var(--text-secondary);margin-top:3px;">'
            'Sign in with your credentials or explore in guest mode.</div>'
            '</div>',
            unsafe_allow_html=True
        )

        tab_signin, tab_register = st.tabs(["Sign In", "Create Account"])

        # ── Sign In Tab ────────────────────────────────────────────────────
        with tab_signin:
            with st.form("signin_form", clear_on_submit=False):
                email = st.text_input(
                    "Email Address",
                    placeholder="name@company.com",
                    key="signin_email_field"
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="••••••••",
                    key="signin_password_field"
                )
                st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
                submit_signin = st.form_submit_button(
                    "Sign In →",
                    type="primary",
                    use_container_width=True
                )

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

        # ── Register Tab ───────────────────────────────────────────────────
        with tab_register:
            with st.form("register_form", clear_on_submit=False):
                reg_name = st.text_input(
                    "Full Name",
                    placeholder="e.g. Alex Johnson",
                    key="reg_name_field"
                )
                reg_email = st.text_input(
                    "Email Address",
                    placeholder="name@company.com",
                    key="reg_email_field"
                )
                reg_pass = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Minimum 8 characters",
                    help="Password must be at least 8 characters long.",
                    key="reg_pass_field"
                )
                reg_confirm = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Repeat password",
                    key="reg_confirm_field"
                )
                st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
                submit_register = st.form_submit_button(
                    "Create Account →",
                    type="primary",
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

        # ── Guest Access Divider & Button ──────────────────────────────────
        divider_html = (
            '<div style="position:relative;text-align:center;margin:16px 0 12px 0;">'
            '<hr style="border:none;border-top:1px solid var(--border);margin:0;">'
            '<span style="position:absolute;top:-9px;left:50%;transform:translateX(-50%);'
            'background:var(--bg-primary);padding:0 10px;font-size:10px;color:var(--text-muted);'
            'font-weight:600;text-transform:uppercase;letter-spacing:0.06em;">or</span>'
            '</div>'
            '<div style="font-size:12px;color:var(--text-secondary);margin-bottom:8px;text-align:center;">'
            'Explore sample datasets, dashboards, and analytics tools without an account.'
            '</div>'
        )
        st.markdown(divider_html, unsafe_allow_html=True)

        if st.button(
            "Explore as Guest  →",
            key="guest_access_btn",
            use_container_width=True
        ):
            start_guest_session()
            st.toast("Entered Guest Demo mode.")
            st.rerun()

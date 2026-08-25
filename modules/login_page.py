"""
DATA STUDIO v2 — Authentication & Login View (Module 5)
=============================================================================
Professional full-screen authentication interface supporting Email/Password
login, Account Registration with validation & bcrypt hashing, and Guest Demo mode.
"""
from typing import Optional
import streamlit as st

from modules.config import APP_NAME, APP_SUBTITLE, APP_VERSION
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
    """Render the full-screen professional authentication page with theme switching."""
    current_theme = st.session_state.get("theme", "Dark")
    
    # Top theme switcher bar
    top_col_spacer, top_col_theme = st.columns([8.2, 1.8])
    with top_col_theme:
        theme_toggle_label = "Switch to Light Mode" if current_theme == "Dark" else "Switch to Dark Mode"
        if st.button(theme_toggle_label, key="login_theme_toggle_btn", use_container_width=True):
            st.session_state["theme"] = "Light" if current_theme == "Dark" else "Dark"
            st.rerun()

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    col_hero, col_auth = st.columns([5.5, 4.5], gap="large")

    # =========================================================================
    # LEFT COLUMN: BRAND SHOWCASE & PLATFORM CAPABILITIES
    # =========================================================================
    with col_hero:
        hero_html = (
            f'<div class="ds-login-hero">'
            f'<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">'
            f'<div class="ds-brand-badge" style="width: 38px; height: 38px; font-size: 15px;">DS</div>'
            f'<div>'
            f'<div style="font-size: 20px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.025em;">{APP_NAME}</div>'
            f'<div style="font-size: 11px; font-family: var(--font-mono); color: var(--accent);">{APP_VERSION} · Analytics Platform</div>'
            f'</div>'
            f'</div>'
            f'<div style="font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">Upload, explore, and understand your data.</div>'
            f'<div style="font-size: 13px; color: var(--text-secondary); line-height: 1.5;">'
            f'A comprehensive local analytics platform providing deterministic data quality profiling, '
            f'automatic dynamic dashboards, and high-performance tabular exploration.'
            f'</div>'
            f'<div class="ds-login-feature-list">'
            f'<div class="ds-login-feature">'
            f'<div class="ds-login-feature-icon">{get_icon_svg("database", size=16)}</div>'
            f'<div>'
            f'<div class="ds-login-feature-title">Dataset Workspace</div>'
            f'<div class="ds-login-feature-desc">Multi-format CSV/XLSX loaders with automatic schema profiling and type inference.</div>'
            f'</div>'
            f'</div>'
            f'<div class="ds-login-feature">'
            f'<div class="ds-login-feature-icon">{get_icon_svg("layout-dashboard", size=16)}</div>'
            f'<div>'
            f'<div class="ds-login-feature-title">Dynamic Dashboards</div>'
            f'<div class="ds-login-feature-desc">Automatic feature prioritization, theme-adaptive Plotly charts, and factual insights.</div>'
            f'</div>'
            f'</div>'
            f'<div class="ds-login-feature">'
            f'<div class="ds-login-feature-icon">{get_icon_svg("shield-check", size=16)}</div>'
            f'<div>'
            f'<div class="ds-login-feature-title">Data Quality Engine</div>'
            f'<div class="ds-login-feature-desc">Transparent 0–100 health scoring across completeness, uniqueness, and validity.</div>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'<div style="margin-top: auto; padding-top: 20px; font-size: 11px; color: var(--text-muted); display: flex; align-items: center; gap: 8px;">'
            f'{get_icon_svg("shield", size=14)} <span>Secure bcrypt password hashing · Isolated session state architecture</span>'
            f'</div>'
            f'</div>'
        )
        st.markdown(hero_html, unsafe_allow_html=True)

    # =========================================================================
    # RIGHT COLUMN: AUTHENTICATION TABS & GUEST ACCESS
    # =========================================================================
    with col_auth:
        header_html = (
            '<div style="margin-bottom: 12px;">'
            '<div style="font-size: 17px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.02em;">Access Workspace</div>'
            '<div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">Sign in with your credentials or explore in guest mode.</div>'
            '</div>'
        )
        st.markdown(header_html, unsafe_allow_html=True)

        tab_signin, tab_register = st.tabs(["Sign In", "Create Account"])

        # ---------------------------------------------------------------------
        # TAB 1: SIGN IN
        # ---------------------------------------------------------------------
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
                
                st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                submit_signin = st.form_submit_button(
                    "Sign In",
                    type="primary",
                    use_container_width=True
                )

            if submit_signin:
                with st.spinner("Authenticating credentials..."):
                    success, msg, user_info = authenticate_user(email, password)
                    if success and user_info:
                        login_user_session(user_info)
                        st.toast(f"Welcome back, {user_info['full_name']}!")
                        st.rerun()
                    else:
                        render_notification(
                            title="Sign In Failed",
                            message=msg,
                            variant="error"
                        )

        # ---------------------------------------------------------------------
        # TAB 2: CREATE ACCOUNT
        # ---------------------------------------------------------------------
        with tab_register:
            with st.form("register_form", clear_on_submit=False):
                reg_name = st.text_input(
                    "Full Name",
                    placeholder="e.g. Kartik Bendre",
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

                st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                submit_register = st.form_submit_button(
                    "Create Account",
                    type="primary",
                    use_container_width=True
                )

            if submit_register:
                with st.spinner("Securing and creating account..."):
                    success, msg, user_info = register_user(
                        full_name=reg_name,
                        email=reg_email,
                        password=reg_pass,
                        confirm_password=reg_confirm
                    )
                    if success and user_info:
                        login_user_session(user_info)
                        st.toast("Account created successfully! Logged in.")
                        st.rerun()
                    else:
                        render_notification(
                            title="Registration Failed",
                            message=msg,
                            variant="error"
                        )

        # ---------------------------------------------------------------------
        # GUEST DEMO ACCESS
        # ---------------------------------------------------------------------
        divider_html = (
            '<div style="position: relative; text-align: center; margin: 16px 0 12px 0;">'
            '<hr style="border: none; border-top: 1px solid var(--border); margin: 0;">'
            '<span style="position: absolute; top: -9px; left: 50%; transform: translateX(-50%); background: var(--bg-primary); padding: 0 10px; font-size: 10px; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">or</span>'
            '</div>'
            '<div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px; text-align: center;">'
            'Explore sample datasets, dashboards, and data quality tools without an account.'
            '</div>'
        )
        st.markdown(divider_html, unsafe_allow_html=True)

        if st.button("Explore as Guest", key="guest_access_btn", use_container_width=True):
            start_guest_session()
            st.toast("Entered Guest Demo mode.")
            st.rerun()

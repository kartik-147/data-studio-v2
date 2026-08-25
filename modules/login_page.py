"""
DATA STUDIO v2 — Authentication & Login View (Screenshot Matched UI)
=============================================================================
Centered, clean SaaS layout matching the user design screenshot.
Features:
- Top bar with Logo + Brand Name on left, "Dark Mode" pill on right.
- Centered Hero: "Exploratory Data Analysis Workbench." (with blue dot).
- Subtitle: "Automated profiling, statistical quality audits, interactive visualization, and targeted analytical workflows."
- 4 Feature Cards in a clean horizontal row (Dataset Profiling, Quality Scoring, Visual Analytics, Automated Insights).
- Centered Auth Box: "Welcome to Data Studio", subtitle, Email & Password fields, Sign In, Create Account & Guest Access.
All backend authentication logic is preserved completely intact.
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
    """Render the exact centered clean layout matching the user screenshot."""
    current_theme = st.session_state.get("theme", "Light")
    is_dark = current_theme == "Dark"

    # =========================================================================
    # 1. TOP HEADER BAR
    # =========================================================================
    top_l, top_r = st.columns([8, 2])
    with top_l:
        # Pulse / Activity logo + Brand Name
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; padding: 4px 0;">
                <span style="color: #3b82f6; display: flex; align-items: center;">
                    {get_icon_svg("activity", 20)}
                </span>
                <span style="font-size: 16px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.02em;">
                    {APP_NAME}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    with top_r:
        # Clean rounded outline toggle button like in screenshot
        toggle_label = "Light Mode" if is_dark else "Dark Mode"
        if st.button(toggle_label, key="login_theme_toggle_btn", use_container_width=True):
            st.session_state["theme"] = "Light" if is_dark else "Dark"
            st.rerun()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # 2. HERO HEADLINE & SUBTITLE (Centered)
    # =========================================================================
    st.markdown(
        """
        <div style="text-align: center; max-width: 820px; margin: 0 auto 24px auto;">
            <h1 style="font-size: 38px; font-weight: 800; color: var(--text-primary); letter-spacing: -0.035em; margin-bottom: 12px; line-height: 1.15;">
                Exploratory Data Analysis Workbench<span style="color: #2563eb;">.</span>
            </h1>
            <p style="font-size: 14px; color: var(--text-secondary); line-height: 1.6; margin: 0; font-weight: 450;">
                Automated profiling, statistical quality audits, interactive visualization, and targeted analytical workflows.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # =========================================================================
    # 3. 4 FEATURE CARDS (Horizontal Row matching screenshot)
    # =========================================================================
    f1, f2, f3, f4 = st.columns(4, gap="small")
    
    with f1:
        st.markdown(
            f"""
            <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px; display: flex; gap: 10px; align-items: flex-start; min-height: 96px; box-shadow: var(--shadow-xs);">
                <div style="color: #2563eb; background: rgba(37,99,235,0.08); border-radius: 6px; padding: 6px; display: flex; align-items: center; justify-content: center;">
                    {get_icon_svg("database", 16)}
                </div>
                <div>
                    <div style="font-size: 12px; font-weight: 700; color: var(--text-primary); margin-bottom: 3px;">Dataset Profiling</div>
                    <div style="font-size: 11px; color: var(--text-muted); line-height: 1.4;">Schema inspection, null auditing, and type classification.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with f2:
        st.markdown(
            f"""
            <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px; display: flex; gap: 10px; align-items: flex-start; min-height: 96px; box-shadow: var(--shadow-xs);">
                <div style="color: #059669; background: rgba(5,150,105,0.08); border-radius: 6px; padding: 6px; display: flex; align-items: center; justify-content: center;">
                    {get_icon_svg("shield-check", 16)}
                </div>
                <div>
                    <div style="font-size: 12px; font-weight: 700; color: var(--text-primary); margin-bottom: 3px;">Quality Scoring</div>
                    <div style="font-size: 11px; color: var(--text-muted); line-height: 1.4;">Composite health rating across completeness and uniqueness.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with f3:
        st.markdown(
            f"""
            <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px; display: flex; gap: 10px; align-items: flex-start; min-height: 96px; box-shadow: var(--shadow-xs);">
                <div style="color: #7c3aed; background: rgba(124,58,237,0.08); border-radius: 6px; padding: 6px; display: flex; align-items: center; justify-content: center;">
                    {get_icon_svg("bar-chart-3", 16)}
                </div>
                <div>
                    <div style="font-size: 12px; font-weight: 700; color: var(--text-primary); margin-bottom: 3px;">Visual Analytics</div>
                    <div style="font-size: 11px; color: var(--text-muted); line-height: 1.4;">Correlation heatmaps, distribution grids, and outliers.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with f4:
        st.markdown(
            f"""
            <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px; display: flex; gap: 10px; align-items: flex-start; min-height: 96px; box-shadow: var(--shadow-xs);">
                <div style="color: #d97706; background: rgba(217,119,6,0.08); border-radius: 6px; padding: 6px; display: flex; align-items: center; justify-content: center;">
                    {get_icon_svg("cpu", 16)}
                </div>
                <div>
                    <div style="font-size: 12px; font-weight: 700; color: var(--text-primary); margin-bottom: 3px;">Automated Insights</div>
                    <div style="font-size: 11px; color: var(--text-muted); line-height: 1.4;">Natural language querying and smart analytical summaries.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height: 36px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # 4. CENTERED LOGIN FORM (Clean card like screenshot)
    # =========================================================================
    _, col_center, _ = st.columns([1.2, 2.0, 1.2])

    with col_center:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 24px;">
                <h2 style="font-size: 26px; font-weight: 800; color: var(--text-primary); letter-spacing: -0.03em; margin: 0 0 8px 0;">
                    Welcome to Data Studio
                </h2>
                <p style="font-size: 13.5px; color: var(--text-secondary); margin: 0;">
                    Sign in to access your analytics workspace.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Mode switch state between Sign In and Registration
        if "auth_view" not in st.session_state:
            st.session_state["auth_view"] = "signin"

        if st.session_state["auth_view"] == "signin":
            with st.form("signin_form", clear_on_submit=False):
                st.markdown(
                    "<span style='font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em;'>EMAIL</span>",
                    unsafe_allow_html=True
                )
                email = st.text_input(
                    "EMAIL",
                    value="bendrekartik47@gmail.com",
                    placeholder="name@company.com",
                    key="signin_email_field",
                    label_visibility="collapsed"
                )

                st.markdown(
                    "<div style='height: 8px;'></div><span style='font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em;'>PASSWORD</span>",
                    unsafe_allow_html=True
                )
                password = st.text_input(
                    "PASSWORD",
                    type="password",
                    placeholder="Enter your password",
                    key="signin_password_field",
                    label_visibility="collapsed"
                )

                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                submit_signin = st.form_submit_button(
                    "Sign In",
                    type="secondary",
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

            # Bottom two action buttons in a row: [Create Account] [Guest Access]
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            act_col1, act_col2 = st.columns(2, gap="small")
            with act_col1:
                if st.button("Create Account", key="goto_register_btn", use_container_width=True):
                    st.session_state["auth_view"] = "register"
                    st.rerun()
            with act_col2:
                if st.button("Guest Access", key="guest_access_btn", use_container_width=True):
                    start_guest_session()
                    st.toast("Entered Guest Demo mode.")
                    st.rerun()

        else:
            # Registration View
            with st.form("register_form", clear_on_submit=False):
                st.markdown(
                    "<span style='font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em;'>FULL NAME</span>",
                    unsafe_allow_html=True
                )
                reg_name = st.text_input(
                    "FULL NAME",
                    placeholder="e.g. Alex Johnson",
                    key="reg_name_field",
                    label_visibility="collapsed"
                )

                st.markdown(
                    "<div style='height: 8px;'></div><span style='font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em;'>EMAIL</span>",
                    unsafe_allow_html=True
                )
                reg_email = st.text_input(
                    "EMAIL",
                    placeholder="name@company.com",
                    key="reg_email_field",
                    label_visibility="collapsed"
                )

                st.markdown(
                    "<div style='height: 8px;'></div><span style='font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em;'>PASSWORD</span>",
                    unsafe_allow_html=True
                )
                reg_pass = st.text_input(
                    "PASSWORD",
                    type="password",
                    placeholder="Minimum 8 characters",
                    key="reg_pass_field",
                    label_visibility="collapsed"
                )

                st.markdown(
                    "<div style='height: 8px;'></div><span style='font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em;'>CONFIRM PASSWORD</span>",
                    unsafe_allow_html=True
                )
                reg_confirm = st.text_input(
                    "CONFIRM PASSWORD",
                    type="password",
                    placeholder="Repeat password",
                    key="reg_confirm_field",
                    label_visibility="collapsed"
                )

                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                submit_register = st.form_submit_button(
                    "Create Account",
                    type="secondary",
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

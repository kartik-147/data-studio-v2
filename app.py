"""
DATA STUDIO v2 — Main Application Shell & Dynamic Router
=============================================================================
Professional Analytics Platform Architecture:
- Left Sidebar for grouped, hierarchical navigation (WORKSPACE, INTELLIGENCE, SYSTEM, ADMINISTRATION)
- Compact Top Header for dataset context & user state
- Clean, responsive Main Workspace
"""
import sys
import os
import html
import streamlit as st

# Ensure project root is in Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configuration, state, and theme
from modules.config import (
    APP_NAME, APP_VERSION, NAV_GROUPS, PAGE_METADATA,
    init_session_state, is_dataset_loaded
)
from modules.ui_components import (
    load_css, get_icon_svg, render_top_header
)
from modules.auth import (
    is_authenticated, get_current_user, logout_user
)
from modules.google_auth import handle_google_oauth_callback
from modules.firebase_service import is_admin_user

# Page view imports (routing targets)
from modules.login_page import render_login_page
from modules.overview import render_overview_page
from modules.dashboard import render_dashboard_page
from modules.data_profiler import render_dataset_page
from modules.data_quality import render_data_quality_page
from modules.data_preparation import render_data_preparation_page
from modules.eda_page import render_eda_page
from modules.visualization import render_visualization_page
from modules.ai_analyst import render_ai_analyst_page, render_data_story_page
from modules.settings import render_settings_page
from modules.admin_analytics import render_admin_analytics_page

# ── Streamlit Page Configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="Data Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state then inject CSS
init_session_state()
load_css(st.session_state.get("theme", "Light"))


def render_sidebar() -> str:
    """
    Render the professional fixed Left Sidebar navigation.
    Hierarchical grouping:
      - WORKSPACE: Dataset, Overview, Data Preparation, Data Quality, Analyze, Visualization, Dashboard
      - INTELLIGENCE: AI Analyst, Data Story
      - SYSTEM: Settings
      - ADMINISTRATION: Admin Analytics (Admins only)
    Bottom Area:
      - User Profile & Auth Status
      - Theme toggle
      - Sign Out
    """
    current_page = st.session_state.get("current_page", "Overview")
    current_theme = st.session_state.get("theme", "Light")
    user = get_current_user()
    is_dark = current_theme == "Dark"
    user_name = user.get("full_name", "User")
    is_guest = user.get("is_guest", False)
    is_admin = is_admin_user(user)

    with st.sidebar:
        # ── 1. Sidebar Brand Header ──────────────────────────────────────────
        st.markdown(
            f"""
            <div class="ds-sidebar-brand">
                <div class="ds-sidebar-brand-icon">
                    <span style="font-size: 13px; line-height: 1;">⚡</span>
                </div>
                <span class="ds-sidebar-brand-title">{APP_NAME.upper()}</span>
                <span class="ds-sidebar-brand-version">{APP_VERSION}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ── 2. Navigation Structure ──────────────────────────────────────────
        nav_sections = [
            (
                "WORKSPACE",
                [
                    ("Dataset", "Dataset"),
                    ("Overview", "Overview"),
                    ("Data Preparation", "Data Preparation"),
                    ("Data Quality", "Data Quality"),
                    ("Analyze", "Analyze"),
                    ("Visualization", "Visualization"),
                    ("Dashboard", "Dashboard"),
                ]
            ),
            (
                "INTELLIGENCE",
                [
                    ("AI Analyst", "AI Analyst"),
                    ("Data Story", "Data Story"),
                ]
            ),
            (
                "SYSTEM",
                [
                    ("Settings", "Settings"),
                ]
            )
        ]

        if is_admin:
            nav_sections.append(
                (
                    "ADMINISTRATION",
                    [
                        ("Admin Analytics", "Admin Analytics"),
                    ]
                )
            )

        for group_title, items in nav_sections:
            st.markdown(f'<div class="ds-sidebar-group-title">{group_title}</div>', unsafe_allow_html=True)
            for page_key, page_label in items:
                # Handle active state matching (e.g., Analyze vs EDA)
                is_active = (current_page == page_key) or (page_key == "Analyze" and current_page == "EDA")
                btn_type = "primary" if is_active else "secondary"

                if st.button(
                    page_label,
                    key=f"sidebar_nav_{page_key.replace(' ', '_')}",
                    use_container_width=True,
                    type=btn_type
                ):
                    if st.session_state.get("current_page") != page_key:
                        st.session_state["current_page"] = page_key
                        st.rerun()

        # ── 3. Sidebar Bottom Area ───────────────────────────────────────────
        st.markdown('<div class="ds-sidebar-footer">', unsafe_allow_html=True)

        auth_status = "Guest User" if is_guest else "Authenticated"
        role_tag = "ADMIN" if is_admin else ("GUEST" if is_guest else "MEMBER")
        st.markdown(
            f"""
            <div class="ds-sidebar-user-card">
                <div style="overflow: hidden; width: 100%;">
                    <div class="ds-sidebar-user-name">{html.escape(user_name)}</div>
                    <div class="ds-sidebar-user-status">{auth_status} · {role_tag}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        col_theme, col_logout = st.columns(2, gap="small")
        with col_theme:
            theme_btn_label = "☀ Light" if is_dark else "🌙 Dark"
            if st.button(theme_btn_label, key="sidebar_theme_btn", use_container_width=True):
                st.session_state["theme"] = "Light" if is_dark else "Dark"
                st.rerun()

        with col_logout:
            if st.button("Sign Out", key="sidebar_logout_btn", use_container_width=True):
                logout_user()
                st.toast("Signed out successfully.")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    return st.session_state.get("current_page", "Overview")


def main() -> None:
    """Main routing dispatcher with route-level authentication protection."""
    # Check for OAuth callback code in query parameters
    cb_ok, cb_msg, cb_user = handle_google_oauth_callback()
    if cb_ok and cb_user:
        st.toast(f"Welcome, {cb_user.get('full_name', 'User')}! Signed in with Google. ✓")
        st.session_state["current_page"] = "Overview"
        st.rerun()
    elif cb_msg:
        st.session_state["auth_error_message"] = cb_msg

    # Route protection — unauthenticated users see login
    if not is_authenticated():
        render_login_page()
        return

    # Render Left Sidebar Navigation
    active_page = render_sidebar()

    # Server-side Route Protection for Admin Analytics
    if active_page == "Admin Analytics" and not is_admin_user(get_current_user()):
        st.session_state["current_page"] = "Overview"
        st.rerun()

    # Render Compact Top Header Context Bar
    display_title = "Analyze" if active_page in ["Analyze", "EDA"] else active_page
    page_meta = PAGE_METADATA.get(display_title, {})
    page_icon = page_meta.get("icon", "layout-dashboard")

    render_top_header(
        page_title=display_title,
        page_icon=page_icon,
        dataset_name=st.session_state.get("dataset_name"),
        df=st.session_state.get("dataset"),
        user=get_current_user(),
        is_admin=is_admin_user(get_current_user())
    )

    # Page Router
    page_router = {
        "Dataset": render_dataset_page,
        "Overview": render_overview_page,
        "Data Preparation": render_data_preparation_page,
        "Data Quality": render_data_quality_page,
        "Analyze": render_eda_page,
        "EDA": render_eda_page,
        "Visualization": render_visualization_page,
        "Dashboard": render_dashboard_page,
        "AI Analyst": render_ai_analyst_page,
        "Data Story": render_data_story_page,
        "Settings": render_settings_page,
        "Admin Analytics": render_admin_analytics_page,
    }

    renderer = page_router.get(active_page, render_overview_page)
    renderer()


if __name__ == "__main__":
    main()

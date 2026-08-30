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
    load_css, get_icon_svg, render_top_header, render_workflow_indicator
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
      - WORKSPACE:
          01 Dataset
          02 Overview
          03 Data Quality
          04 Data Preparation
          05 Analyze
          06 Visualization
          07 Dashboard
      - INTELLIGENCE:
          08 AI Analyst
          09 Data Story
      - SYSTEM:
          10 Settings
          11 Admin Analytics (Admins only)
    Dataset State Card:
      - Active dataset name + row/col dimensions or empty helper state
    Bottom Area:
      - User Profile & Auth Status (ADMIN / MEMBER / GUEST)
      - Theme toggle (Light / Dark)
      - Sign Out
    """
    current_page = st.session_state.get("current_page", "Overview")
    current_theme = st.session_state.get("theme", "Light")
    is_collapsed = st.session_state.get("sidebar_collapsed", False)
    user = get_current_user()
    is_dark = current_theme == "Dark"
    user_name = user.get("full_name", "User")
    is_guest = user.get("is_guest", False)
    is_admin = is_admin_user(user)

    with st.sidebar:
        # ── 1. Sidebar Brand Header ──────────────────────────────────────────
        brand_icon_svg = get_icon_svg("layout-dashboard", 14)
        toggle_icon = "→" if is_collapsed else "←"
        toggle_help = "Expand sidebar" if is_collapsed else "Collapse sidebar"

        col_brand, col_toggle = st.columns([8, 2])
        with col_brand:
            if not is_collapsed:
                st.markdown(
                    f"""
                    <div class="ds-sidebar-brand">
                        <div class="ds-sidebar-brand-icon">
                            {brand_icon_svg}
                        </div>
                        <span class="ds-sidebar-brand-title">{APP_NAME.upper()}</span>
                        <span class="ds-sidebar-brand-version">{APP_VERSION}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div class="ds-sidebar-brand" style="justify-content: center; padding: 4px 0 10px 0;">
                        <div class="ds-sidebar-brand-icon">
                            {brand_icon_svg}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with col_toggle:
            if st.button(toggle_icon, key="sidebar_toggle_collapse_btn", help=toggle_help):
                st.session_state["sidebar_collapsed"] = not is_collapsed
                st.rerun()

        # ── 2. Active Dataset State Card ─────────────────────────────────────
        if not is_collapsed:
            df = st.session_state.get("dataset")
            ds_name = st.session_state.get("dataset_name")
            if df is not None:
                rows, cols = df.shape
                display_name = html.escape(ds_name or "Active Dataset")
                st.markdown(
                    f"""
                    <div class="ds-sidebar-dataset-card">
                        <div class="ds-sidebar-dataset-label">Active Dataset</div>
                        <div class="ds-sidebar-dataset-name">
                            <span class="ds-status-dot-active">●</span> {display_name}
                        </div>
                        <div class="ds-sidebar-dataset-stats">{rows:,} rows · {cols} columns</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """
                    <div class="ds-sidebar-dataset-card ds-dataset-card-empty">
                        <div class="ds-sidebar-dataset-label">Dataset</div>
                        <div class="ds-sidebar-dataset-name" style="color: var(--text-muted);">No dataset loaded</div>
                        <div class="ds-sidebar-dataset-stats">Upload a dataset to begin.</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # ── 3. Navigation Hierarchy ──────────────────────────────────────────
        nav_sections = [
            (
                "WORKSPACE",
                [
                    ("Dataset", "01  Dataset" if not is_collapsed else "01", "database"),
                    ("Overview", "02  Overview" if not is_collapsed else "02", "layout-dashboard"),
                    ("Data Quality", "03  Data Quality" if not is_collapsed else "03", "shield-check"),
                    ("Data Preparation", "04  Data Preparation" if not is_collapsed else "04", "sliders-horizontal"),
                    ("Analyze", "05  Analyze" if not is_collapsed else "05", "chart-no-axes-combined"),
                    ("Visualization", "06  Visualization" if not is_collapsed else "06", "chart-column"),
                    ("Dashboard", "07  Dashboard" if not is_collapsed else "07", "panels-top-left"),
                ]
            ),
            (
                "INTELLIGENCE",
                [
                    ("AI Analyst", "08  AI Analyst" if not is_collapsed else "08", "brain-circuit"),
                    ("Data Story", "09  Data Story" if not is_collapsed else "09", "book-open"),
                ]
            ),
            (
                "SYSTEM",
                [
                    ("Settings", "10  Settings" if not is_collapsed else "10", "settings"),
                ]
            )
        ]

        if is_admin:
            nav_sections[2][1].append(
                ("Admin Analytics", "11  Admin Analytics" if not is_collapsed else "11", "shield-check")
            )

        for group_title, items in nav_sections:
            if not is_collapsed:
                st.markdown(f'<div class="ds-sidebar-group-title">{group_title}</div>', unsafe_allow_html=True)
            for page_key, page_label, icon_key in items:
                # Handle active state matching (e.g., Analyze vs EDA)
                is_active = (current_page == page_key) or (page_key == "Analyze" and current_page == "EDA")
                btn_type = "primary" if is_active else "secondary"
                item_help = page_key if is_collapsed else None

                if st.button(
                    page_label,
                    key=f"sidebar_nav_{page_key.replace(' ', '_')}",
                    use_container_width=True,
                    type=btn_type,
                    help=item_help
                ):
                    if st.session_state.get("current_page") != page_key:
                        st.session_state["current_page"] = page_key
                        st.rerun()

        # ── 4. Sidebar Bottom Area ───────────────────────────────────────────
        st.markdown('<div class="ds-sidebar-footer">', unsafe_allow_html=True)

        if not is_collapsed:
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
                theme_btn_label = "Light" if is_dark else "Dark"
                if st.button(theme_btn_label, key="sidebar_theme_btn", use_container_width=True, help="Switch color theme"):
                    st.session_state["theme"] = "Light" if is_dark else "Dark"
                    st.rerun()

            with col_logout:
                if st.button("Sign Out", key="sidebar_logout_btn", use_container_width=True, help="Sign out of Data Studio"):
                    logout_user()
                    st.toast("Signed out successfully.")
                    st.rerun()
        else:
            theme_btn_label = "Light" if is_dark else "Dark"
            if st.button(theme_btn_label, key="sidebar_theme_btn_col", use_container_width=True, help="Switch Theme"):
                st.session_state["theme"] = "Light" if is_dark else "Dark"
                st.rerun()
            if st.button("Out", key="sidebar_logout_btn_col", use_container_width=True, help="Sign Out"):
                logout_user()
                st.toast("Signed out successfully.")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    return st.session_state.get("current_page", "Overview")


def render_mobile_navigation(is_admin: bool) -> None:
    """Render a compact navigation drawer for mobile viewports (< 768px)."""
    current_page = st.session_state.get("current_page", "Overview")
    
    with st.expander("Navigation Menu", expanded=False):
        st.markdown("<div class='ds-sidebar-group-title'>WORKSPACE</div>", unsafe_allow_html=True)
        m_c1, m_c2 = st.columns(2)
        workspace_items = [
            ("Dataset", "01 Dataset"),
            ("Overview", "02 Overview"),
            ("Data Quality", "03 Data Quality"),
            ("Data Preparation", "04 Data Preparation"),
            ("Analyze", "05 Analyze"),
            ("Visualization", "06 Visualization"),
            ("Dashboard", "07 Dashboard"),
        ]
        for idx, (p_key, p_label) in enumerate(workspace_items):
            target_col = m_c1 if idx % 2 == 0 else m_c2
            with target_col:
                is_active = (current_page == p_key) or (p_key == "Analyze" and current_page == "EDA")
                if st.button(
                    p_label,
                    key=f"mob_nav_{p_key.replace(' ', '_')}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    st.session_state["current_page"] = p_key
                    st.rerun()

        st.markdown("<div class='ds-sidebar-group-title'>INTELLIGENCE</div>", unsafe_allow_html=True)
        i_c1, i_c2 = st.columns(2)
        with i_c1:
            is_active = (current_page == "AI Analyst")
            if st.button("08 AI Analyst", key="mob_nav_ai", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state["current_page"] = "AI Analyst"
                st.rerun()
        with i_c2:
            is_active = (current_page == "Data Story")
            if st.button("09 Data Story", key="mob_nav_story", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state["current_page"] = "Data Story"
                st.rerun()

        st.markdown("<div class='ds-sidebar-group-title'>SYSTEM</div>", unsafe_allow_html=True)
        s_cols = st.columns(2 if is_admin else 1)
        with s_cols[0]:
            is_active = (current_page == "Settings")
            if st.button("10 Settings", key="mob_nav_settings", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state["current_page"] = "Settings"
                st.rerun()
        if is_admin and len(s_cols) > 1:
            with s_cols[1]:
                is_active = (current_page == "Admin Analytics")
                if st.button("11 Admin Analytics", key="mob_nav_admin", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.session_state["current_page"] = "Admin Analytics"
                    st.rerun()


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

    # Render Subtle Workflow Indicator Breadcrumb Bar
    render_workflow_indicator(active_page)

    # Page Router
    page_router = {
        "Dataset": render_dataset_page,
        "Overview": render_overview_page,
        "Data Quality": render_data_quality_page,
        "Data Preparation": render_data_preparation_page,
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

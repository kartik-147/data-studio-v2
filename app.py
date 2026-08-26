"""
DATA STUDIO v2 — Main Application Shell & Dynamic Router (Top Navigation Architecture)
=============================================================================
Option 1: Modern SaaS Top Navigation Bar
- Left sidebar is completely removed / deleted.
- Top bar contains Brand, dataset indicator, user profile, theme toggle, and sign out.
- Navigation pill bar allows instant 1-click switching across all workflow modules:
  ◉ Overview | ▣ Dataset | ◫ Data Prep | ◌ EDA | ◉ Visualization | ▥ Dashboard | ◈ Quality | ✦ AI Analyst | ⚙ Settings
"""
import sys
import os
import html
import streamlit as st

# Ensure project root is in Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configuration, state, and theme
from modules.config import (
    APP_NAME, APP_VERSION, NAV_GROUPS,
    init_session_state, is_dataset_loaded
)
from modules.ui_components import (
    load_css, get_icon_svg,
    render_dataset_context_bar
)
from modules.auth import (
    is_authenticated, get_current_user, logout_user
)
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
from modules.ai_analyst import render_ai_analyst_page
from modules.settings import render_settings_page
from modules.admin_analytics import render_admin_analytics_page

# ── Streamlit Page Configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="Data Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state then inject CSS
init_session_state()
load_css(st.session_state.get("theme", "Light"))


def render_top_navbar() -> str:
    """
    Render a clean, modern SaaS Top Navigation Bar (Option 1).
    Completely replaces the left sidebar with a responsive header and tabbed navigation.
    """
    current_page = st.session_state.get("current_page", "Overview")
    current_theme = st.session_state.get("theme", "Light")
    user = get_current_user()
    is_dark = current_theme == "Dark"
    user_name = user.get("full_name", "User")
    is_guest = user.get("is_guest", False)
    badge_label = "Guest" if is_guest else "Member"

    # ── Tier 1: Brand, Status, and User Profile ──────────────────────────────
    col_brand, col_status, col_user = st.columns([3.2, 4.3, 4.5], gap="small")
    
    with col_brand:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; padding: 2px 0;">
                <span class="mat-icon" style="color: var(--text-primary); font-size: 22px; font-weight: 700;">analytics</span>
                <span style="font-size: 18px; font-weight: 900; color: var(--text-primary); letter-spacing: -0.01em; font-family: var(--font-sans);">
                    DATA STUDIO
                </span>
                <span style="font-size: 10px; font-family: var(--font-mono); color: var(--text-muted); background: var(--surface-container-low); padding: 1px 5px; border-radius: 3px; border: 1px solid var(--border);">
                    v2
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col_status:
        df = st.session_state.get("dataset")
        ds_name = st.session_state.get("dataset_name", "")
        if df is not None:
            rows, cols = df.shape
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; justify-content: center; height: 100%; padding: 4px 0;">
                    <span style="font-size: 12px; color: var(--text-secondary); background: var(--surface); border: 1px solid var(--border); padding: 3px 12px; border-radius: 20px; display: inline-flex; align-items: center; gap: 6px; box-shadow: var(--shadow-xs);">
                        <span style="color: #10b981; font-size: 10px;">●</span> <strong style="color: var(--text-primary);">{html.escape(ds_name or 'Dataset')}</strong> &nbsp;({rows:,} rows × {cols:,} cols)
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div style="display: flex; align-items: center; justify-content: center; height: 100%; padding: 4px 0;">
                    <span style="font-size: 12px; color: var(--text-muted); background: var(--surface-container-low); border: 1px dashed var(--border); padding: 3px 12px; border-radius: 20px;">
                        No dataset loaded
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

    with col_user:
        badge_bg = "rgba(217,119,6,0.1)" if is_guest else "rgba(0,101,145,0.1)"
        badge_color = "#d97706" if is_guest else "#006591"
        badge_border = "rgba(217,119,6,0.2)" if is_guest else "rgba(0,101,145,0.2)"
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: flex-end; gap: 8px; height: 100%;">
                <span style="font-size: 13px; font-weight: 600; color: var(--text-primary);">{html.escape(user_name)}</span>
                <span style="font-size: 10px; font-weight: 700; text-transform: uppercase; padding: 2px 7px; border-radius: 3px; background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border}; letter-spacing: 0.04em;">{badge_label}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ── Tier 2: Navigation Pills & Quick Actions ─────────────────────────────
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    
    nav_items = [
        ("Dataset", "DATASET"),
        ("Overview", "OVERVIEW"),
        ("Data Preparation", "DATA PREP"),
        ("EDA", "ANALYZE"),
        ("Visualization", "VISUALIZATION"),
        ("Dashboard", "DASHBOARD"),
        ("Data Quality", "QUALITY"),
        ("AI Analyst", "AI ANALYST"),
        ("Settings", "SETTINGS"),
    ]
    if is_admin_user(user):
        nav_items.append(("Admin Analytics", "ADMIN"))

    # Render navigation pill buttons in a neat horizontal row
    cols = st.columns(len(nav_items) + 2, gap="small")
    for i, (page_key, page_label) in enumerate(nav_items):
        with cols[i]:
            is_active = current_page == page_key
            if st.button(
                page_label,
                key=f"topnav_{page_key.replace(' ', '_')}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                if st.session_state["current_page"] != page_key:
                    st.session_state["current_page"] = page_key
                    st.rerun()

    # Theme toggle and logout buttons
    with cols[-2]:
        theme_btn_label = "☀ Light" if is_dark else "🌙 Dark"
        if st.button(theme_btn_label, key="topnav_theme_btn", use_container_width=True):
            st.session_state["theme"] = "Light" if is_dark else "Dark"
            st.rerun()

    with cols[-1]:
        if st.button("Sign Out", key="topnav_logout_btn", use_container_width=True):
            logout_user()
            st.toast("Signed out successfully.")
            st.rerun()

    st.markdown("<hr style='border:none; border-top: 1px solid var(--border); margin: 8px 0 16px 0;'>", unsafe_allow_html=True)

    return st.session_state.get("current_page", "Overview")


def main() -> None:
    """Main routing dispatcher with route-level authentication protection."""

    # Route protection — unauthenticated users see login
    if not is_authenticated():
        render_login_page()
        return

    # Render sleek Top Navigation Bar (Option 1)
    active_page = render_top_navbar()

    # Dataset context bar (shows on other analytical pages when dataset is loaded)
    if is_dataset_loaded() and active_page != "Dataset":
        render_dataset_context_bar()

    # Page Router
    page_router = {
        "Overview": render_overview_page,
        "Dashboard": render_dashboard_page,
        "Dataset": render_dataset_page,
        "Data Quality": render_data_quality_page,
        "Data Preparation": render_data_preparation_page,
        "EDA": render_eda_page,
        "Visualization": render_visualization_page,
        "AI Analyst": render_ai_analyst_page,
        "Settings": render_settings_page,
        "Admin Analytics": render_admin_analytics_page,
    }

    renderer = page_router.get(active_page, render_overview_page)
    renderer()


if __name__ == "__main__":
    main()

"""
DATA STUDIO v2 — Main Application Shell & Dynamic Router
=============================================================================
Unified application entry point managing session state, theme injection,
sidebar navigation, and authentication route protection.
"""
import sys
import os
import importlib
import streamlit as st

# Ensure project root is in Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import configuration, state, and themes
from modules.config import (
    APP_NAME,
    APP_VERSION,
    NAV_GROUPS,
    init_session_state
)
from modules.ui_components import load_css
from modules.auth import (
    is_authenticated,
    get_current_user,
    logout_user
)
from modules.firebase_service import is_admin_user

# Import Page Views
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

# Streamlit Page Settings
st.set_page_config(
    page_title="Data Studio",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
init_session_state()

# Inject Centralized Theme-Aware CSS
load_css(st.session_state.get("theme", "Dark"))


def render_sidebar() -> str:
    """Render the structured sidebar navigation according to the design system."""
    current_page = st.session_state.get("current_page", "Overview")
    current_theme = st.session_state.get("theme", "Dark")
    user = get_current_user()
    
    with st.sidebar:
        # Application Brand
        brand_html = (
            f'<div class="ds-sidebar-brand">'
            f'<div class="ds-brand-badge">DS</div>'
            f'<div>'
            f'<div class="ds-brand-name">{APP_NAME}</div>'
            f'<div class="ds-brand-version">{APP_VERSION}</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(brand_html, unsafe_allow_html=True)
        
        # Navigation Groups
        for group_name, pages in NAV_GROUPS.items():
            if group_name == "SYSTEM":
                continue  # Render settings and admin in bottom area
                
            st.markdown(f'<div class="ds-nav-group-title">{group_name}</div>', unsafe_allow_html=True)
            for page in pages:
                is_active = (current_page == page)
                btn_type = "primary" if is_active else "secondary"
                
                # Single action button per navigation item
                if st.button(page, key=f"nav_{page}", use_container_width=True, type=btn_type):
                    if st.session_state["current_page"] != page:
                        st.session_state["current_page"] = page
                        st.rerun()
                        
        # Bottom Area
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="ds-nav-group-title">SYSTEM</div>', unsafe_allow_html=True)
        
        # Settings Navigation
        is_settings_active = (current_page == "Settings")
        if st.button("Settings", key="nav_Settings", use_container_width=True, type="primary" if is_settings_active else "secondary"):
            if st.session_state["current_page"] != "Settings":
                st.session_state["current_page"] = "Settings"
                st.rerun()

        # Admin Analytics Navigation (Visible only to authorized admin)
        if is_admin_user(user):
            is_admin_active = (current_page == "Admin Analytics")
            if st.button("Admin Analytics", key="nav_Admin_Analytics", use_container_width=True, type="primary" if is_admin_active else "secondary"):
                if st.session_state["current_page"] != "Admin Analytics":
                    st.session_state["current_page"] = "Admin Analytics"
                    st.rerun()
                
        # Theme Toggle
        theme_toggle_label = "Switch to Light Mode" if current_theme == "Dark" else "Switch to Dark Mode"
        if st.button(theme_toggle_label, key="sidebar_theme_toggle_btn", use_container_width=True):
            st.session_state["theme"] = "Light" if current_theme == "Dark" else "Dark"
            st.rerun()

        # Authenticated User Identity Card & Sign Out
        badge_cls = "ds-user-badge-guest" if user.get("is_guest") else "ds-user-badge-registered"
        badge_text = "Guest Session" if user.get("is_guest") else "Registered Account"
        
        user_card_html = (
            f'<div class="ds-sidebar-user-card">'
            f'<div class="ds-sidebar-user-name">{user.get("full_name", "User")}</div>'
            f'<div class="ds-sidebar-user-email">{user.get("email", "")}</div>'
            f'<span class="ds-sidebar-user-badge {badge_cls}">{badge_text}</span>'
            f'</div>'
        )
        st.markdown(user_card_html, unsafe_allow_html=True)

        if st.button("Sign Out", key="sidebar_logout_btn", use_container_width=True):
            logout_user()
            st.toast("Signed out successfully.")
            st.rerun()
            
    return st.session_state.get("current_page", "Overview")


def main():
    """Main routing dispatcher with route-level authentication protection."""
    # Route Protection (Module 5)
    if not is_authenticated():
        render_login_page()
        return

    active_page = render_sidebar()
    
    # Route matching for authenticated users
    if active_page == "Overview":
        render_overview_page()
    elif active_page == "Dashboard":
        render_dashboard_page()
    elif active_page == "Dataset":
        render_dataset_page()
    elif active_page == "Data Quality":
        render_data_quality_page()
    elif active_page == "Data Preparation":
        render_data_preparation_page()
    elif active_page == "EDA":
        render_eda_page()
    elif active_page == "Visualization":
        render_visualization_page()
    elif active_page == "AI Analyst":
        render_ai_analyst_page()
    elif active_page == "Settings":
        render_settings_page()
    elif active_page == "Admin Analytics":
        render_admin_analytics_page()
    else:
        render_overview_page()


if __name__ == "__main__":
    main()

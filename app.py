"""
DATA STUDIO v2 — Main Application Shell & Dynamic Router
=============================================================================
Clean, normal sidebar navigation matching the exact requested structure:
┌─────────────────────────┐
│ DATA STUDIO             │
│                         │
│ WORKSPACE               │
│ ◉ Overview              │
│                         │
│ DATA PIPELINE           │
│ ▣ Dataset               │
│ ◫ Data Preparation      │
│ ◌ EDA                   │
│                         │
│ ANALYTICS               │
│ ◉ Visualization         │
│ ▥ Dashboard             │
│ ◈ Data Quality          │
│                         │
│ INTELLIGENCE            │
│ ✦ AI Analyst            │
│                         │
│ ─────────────────────── │
│ ⚙ Settings              │
└─────────────────────────┘
"""
import sys
import os
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
    initial_sidebar_state="expanded"
)

# Initialize session state then inject CSS
init_session_state()
load_css(st.session_state.get("theme", "Light"))

# ── Unicode Symbols matching user exact order ─────────────────────────────────
NAV_PAGE_SYMBOLS = {
    "Overview": "◉",
    "Dataset": "▣",
    "Data Preparation": "◫",
    "EDA": "◌",
    "Visualization": "◉",
    "Dashboard": "▥",
    "Data Quality": "◈",
    "AI Analyst": "✦",
    "Settings": "⚙",
    "Admin Analytics": "🛡",
}


def render_sidebar() -> str:
    """Render clean, standard Streamlit sidebar navigation in the exact requested order."""
    current_page = st.session_state.get("current_page", "Overview")
    current_theme = st.session_state.get("theme", "Light")
    user = get_current_user()

    with st.sidebar:
        # Header Brand
        st.markdown(
            f"""
            <div style="padding: 10px 0 16px 0; border-bottom: 1px solid var(--border); margin-bottom: 14px;">
                <div style="font-size: 16px; font-weight: 800; color: var(--text-primary); letter-spacing: -0.02em;">
                    {APP_NAME.upper()}
                </div>
                <div style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); margin-top: 2px;">
                    {APP_VERSION} · Analytics Platform
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 1. WORKSPACE
        st.markdown("<div class='ds-nav-group-title'>WORKSPACE</div>", unsafe_allow_html=True)
        is_active = current_page == "Overview"
        symbol = NAV_PAGE_SYMBOLS.get("Overview", "◉")
        if st.button(
            f"{symbol}  Overview",
            key="nav_Overview",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            if st.session_state["current_page"] != "Overview":
                st.session_state["current_page"] = "Overview"
                st.rerun()

        # 2. DATA PIPELINE
        st.markdown("<div class='ds-nav-group-title'>DATA PIPELINE</div>", unsafe_allow_html=True)
        for page in ["Dataset", "Data Preparation", "EDA"]:
            is_active = current_page == page
            symbol = NAV_PAGE_SYMBOLS.get(page, "•")
            if st.button(
                f"{symbol}  {page}",
                key=f"nav_{page.replace(' ', '_')}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                if st.session_state["current_page"] != page:
                    st.session_state["current_page"] = page
                    st.rerun()

        # 3. ANALYTICS
        st.markdown("<div class='ds-nav-group-title'>ANALYTICS</div>", unsafe_allow_html=True)
        for page in ["Visualization", "Dashboard", "Data Quality"]:
            is_active = current_page == page
            symbol = NAV_PAGE_SYMBOLS.get(page, "•")
            if st.button(
                f"{symbol}  {page}",
                key=f"nav_{page.replace(' ', '_')}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                if st.session_state["current_page"] != page:
                    st.session_state["current_page"] = page
                    st.rerun()

        # 4. INTELLIGENCE
        st.markdown("<div class='ds-nav-group-title'>INTELLIGENCE</div>", unsafe_allow_html=True)
        is_active = current_page == "AI Analyst"
        symbol = NAV_PAGE_SYMBOLS.get("AI Analyst", "✦")
        if st.button(
            f"{symbol}  AI Analyst",
            key="nav_AI_Analyst",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            if st.session_state["current_page"] != "AI Analyst":
                st.session_state["current_page"] = "AI Analyst"
                st.rerun()

        # 5. DIVIDER & SYSTEM
        st.markdown("<hr style='border:none; border-top:1px solid var(--border); margin: 16px 0 12px 0;'>", unsafe_allow_html=True)

        is_active = current_page == "Settings"
        symbol = NAV_PAGE_SYMBOLS.get("Settings", "⚙")
        if st.button(
            f"{symbol}  Settings",
            key="nav_Settings",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            if st.session_state["current_page"] != "Settings":
                st.session_state["current_page"] = "Settings"
                st.rerun()

        # Admin Analytics (visible only to authorized admins)
        if is_admin_user(user):
            is_active = current_page == "Admin Analytics"
            if st.button(
                "🛡  Admin Analytics",
                key="nav_Admin_Analytics",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                if st.session_state["current_page"] != "Admin Analytics":
                    st.session_state["current_page"] = "Admin Analytics"
                    st.rerun()

        # 6. FOOTER (Theme & User Status & Sign Out)
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        st.markdown("<hr style='border:none; border-top:1px solid var(--border); margin: 6px 0 12px 0;'>", unsafe_allow_html=True)

        name = user.get("full_name", "User")
        email = user.get("email", "")
        is_guest = user.get("is_guest", False)
        badge_cls = "ds-user-badge-guest" if is_guest else "ds-user-badge-registered"
        badge_text = "Guest" if is_guest else "Registered"

        st.markdown(
            f"""
            <div style="padding: 6px 0 10px 0;">
                <div style="font-size: 13px; font-weight: 700; color: var(--text-primary);">{name}</div>
                <div style="font-size: 11px; color: var(--text-muted);">{email}</div>
                <div style="margin-top: 4px;"><span class="ds-sidebar-user-badge {badge_cls}">{badge_text}</span></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        col_thm, col_out = st.columns(2, gap="small")
        with col_thm:
            is_dark = current_theme == "Dark"
            toggle_label = "☀ Light" if is_dark else "🌙 Dark"
            if st.button(toggle_label, key="sidebar_theme_toggle_btn", use_container_width=True):
                st.session_state["theme"] = "Light" if is_dark else "Dark"
                st.rerun()

        with col_out:
            if st.button("Sign Out", key="sidebar_logout_btn", use_container_width=True):
                logout_user()
                st.toast("Signed out successfully.")
                st.rerun()

    return st.session_state.get("current_page", "Overview")


import streamlit.components.v1 as components


def ensure_sidebar_expanded() -> None:
    """Ensure the sidebar is automatically opened/expanded upon logging into the workspace."""
    components.html(
        """
        <script>
        (function() {
            function autoExpand() {
                try {
                    const doc = window.parent.document;
                    if (!doc) return;
                    const sidebar = doc.querySelector('section[data-testid="stSidebar"]');
                    const isCollapsed = !sidebar || sidebar.getAttribute('aria-expanded') === 'false' || sidebar.clientWidth < 50;
                    
                    if (isCollapsed) {
                        const btn = doc.querySelector(
                            'button[data-testid="stSidebarCollapseButton"], ' +
                            '[data-testid="stSidebarCollapsedControl"] button, ' +
                            '[data-testid="collapsedControl"] button, ' +
                            'button[aria-label="Expand sidebar"], ' +
                            'button[aria-label="Open sidebar"]'
                        );
                        if (btn) {
                            btn.click();
                        }
                    }
                } catch(e) {}
            }
            autoExpand();
            setTimeout(autoExpand, 100);
            setTimeout(autoExpand, 300);
            setTimeout(autoExpand, 700);
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def main() -> None:
    """Main routing dispatcher with route-level authentication protection."""

    # Route protection — unauthenticated users see login
    if not is_authenticated():
        render_login_page()
        return

    # Auto-expand sidebar on login/navigation
    ensure_sidebar_expanded()

    # Render clean sidebar and get active page
    active_page = render_sidebar()

    # Dataset context bar (shows on all pages when dataset is loaded)
    if is_dataset_loaded():
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

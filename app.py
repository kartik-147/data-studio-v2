"""
DATA STUDIO v2 — Main Application Shell & Dynamic Router (Premium UI v2)
=============================================================================
Unified application entry point managing session state, theme injection,
premium sidebar navigation with icon-labeled nav items, dataset context bar,
command palette overlay, and authentication route protection.
"""
import sys
import os
import streamlit as st

# Ensure project root is in Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configuration, state, and theme
from modules.config import (
    APP_NAME, APP_VERSION, NAV_GROUPS, NAV_PAGE_ICONS,
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

# Handle command palette query param navigation
if "page" in st.query_params:
    requested = st.query_params.get("page", "")
    all_pages = [p for pages in NAV_GROUPS.values() for p in pages]
    if requested in all_pages or requested in ["Admin Analytics"]:
        st.session_state["current_page"] = requested
    del st.query_params["page"]


# ── Sidebar Rendering ──────────────────────────────────────────────────────────

def _render_nav_item(page: str, current_page: str) -> bool:
    """
    Render a single nav item: visual HTML layer + invisible Streamlit button.
    Returns True if this item was clicked (triggers re-navigation).

    The visual nav item renders first (pointer-events: none).
    The transparent button renders immediately after with margin-top: -36px
    so it overlays the visual item and captures clicks.
    """
    is_active = current_page == page
    active_class = "ds-nav-item-active" if is_active else ""
    icon_name = NAV_PAGE_ICONS.get(page, "database")
    icon_svg = get_icon_svg(icon_name, 14)

    # Visual layer
    nav_html = (
        f'<div class="ds-nav-item {active_class}">'
        f'<span class="ds-nav-item-icon" style="display:flex;align-items:center;">'
        f'{icon_svg}'
        f'</span>'
        f'<span class="ds-nav-item-text">{page}</span>'
        f'</div>'
    )
    st.markdown(nav_html, unsafe_allow_html=True)

    # Invisible click target (transparent button overlaying the visual)
    clicked = st.button(
        f"__{page}__",        # Unique identifiable label for command palette JS targeting
        key=f"nav_{page.replace(' ', '_')}",
        use_container_width=True,
    )
    return clicked


def render_sidebar() -> str:
    """Render the premium sidebar navigation with icon-labelled nav items."""
    current_page = st.session_state.get("current_page", "Overview")
    current_theme = st.session_state.get("theme", "Light")
    user = get_current_user()

    with st.sidebar:
        # ── Brand Header ───────────────────────────────────────────────────
        brand_html = (
            f'<div class="ds-sidebar-brand">'
            f'<div class="ds-brand-badge">DS</div>'
            f'<div>'
            f'<div class="ds-brand-name">{APP_NAME}</div>'
            f'<div class="ds-brand-version">{APP_VERSION} · Analytics Platform</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(brand_html, unsafe_allow_html=True)

        # ── Navigation Groups ──────────────────────────────────────────────
        for group_name, pages in NAV_GROUPS.items():
            if group_name == "SYSTEM":
                continue  # System items handled in the footer area

            st.markdown(
                f'<div class="ds-nav-group-title">{group_name}</div>',
                unsafe_allow_html=True
            )

            for page in pages:
                if _render_nav_item(page, current_page):
                    if st.session_state["current_page"] != page:
                        st.session_state["current_page"] = page
                        st.rerun()

        # ── System Nav Items ───────────────────────────────────────────────
        st.markdown('<div class="ds-nav-group-title" style="margin-top:10px;">SYSTEM</div>', unsafe_allow_html=True)

        if _render_nav_item("Settings", current_page):
            st.session_state["current_page"] = "Settings"
            st.rerun()

        # Admin Analytics (visible only to authorized admins)
        if is_admin_user(user):
            if _render_nav_item("Admin Analytics", current_page):
                st.session_state["current_page"] = "Admin Analytics"
                st.rerun()

        # ── Spacer ─────────────────────────────────────────────────────────
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="ds-sidebar-divider"></div>', unsafe_allow_html=True)

        # ── User Card ──────────────────────────────────────────────────────
        name = user.get("full_name", "User")
        email = user.get("email", "")
        initials = "".join(p[0].upper() for p in name.split() if p)[:2] or "U"
        is_guest = user.get("is_guest", False)
        badge_cls = "ds-user-badge-guest" if is_guest else "ds-user-badge-registered"
        badge_text = "Guest" if is_guest else "Registered"

        user_card_html = (
            f'<div class="ds-sidebar-user-card">'
            f'<div class="ds-user-avatar">{initials}</div>'
            f'<div class="ds-user-info">'
            f'<div class="ds-sidebar-user-name">{name}</div>'
            f'<div class="ds-sidebar-user-email">{email}</div>'
            f'<span class="ds-sidebar-user-badge {badge_cls}">{badge_text}</span>'
            f'</div>'
            f'</div>'
        )
        st.markdown(user_card_html, unsafe_allow_html=True)

        # ── Theme Switcher Row ─────────────────────────────────────────────
        theme_col1, theme_col2 = st.columns(2)
        with theme_col1:
            is_dark = current_theme == "Dark"
            theme_icon = get_icon_svg("sun" if is_dark else "moon", 13)
            theme_label = "Light" if is_dark else "Dark"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:5px;font-size:11px;'
                f'color:var(--text-muted);margin-top:4px;padding-left:2px;">'
                f'{theme_icon}<span>{theme_label} Mode</span></div>',
                unsafe_allow_html=True
            )
            # Invisible toggle button (override sidebar transparent style via sidebar-action-btn wrapper)
            st.markdown('<div class="ds-sidebar-action-btn">', unsafe_allow_html=True)
            if st.button(
                f"{'☀' if is_dark else '🌙'} {theme_label}",
                key="sidebar_theme_toggle_btn",
                use_container_width=True
            ):
                st.session_state["theme"] = "Light" if is_dark else "Dark"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with theme_col2:
            st.markdown('<div class="ds-sidebar-action-btn" style="margin-top:20px;">', unsafe_allow_html=True)
            if st.button("Sign Out", key="sidebar_logout_btn", use_container_width=True):
                logout_user()
                st.toast("Signed out successfully.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    return st.session_state.get("current_page", "Overview")


# ── Command Palette ────────────────────────────────────────────────────────────

def inject_command_palette() -> None:
    """
    Inject a Ctrl+K command palette overlay using a zero-height component iframe.
    Navigation is done by redirecting to ?page=X which triggers a Streamlit rerun.
    """
    nav_items_js = []
    all_pages = [
        ("Overview", "home"),
        ("Dataset", "database"),
        ("Data Preparation", "wrench"),
        ("EDA", "search"),
        ("Visualization", "bar-chart-3"),
        ("Dashboard", "layout-dashboard"),
        ("Data Quality", "shield-check"),
        ("AI Analyst", "sparkles"),
        ("Settings", "settings"),
    ]

    items_html = ""
    for page, icon in all_pages:
        icon_svg = get_icon_svg(icon, 15)
        items_html += (
            f'<div class="ds-cmd-item" onclick="navigateTo(\'{page}\')">'
            f'<span class="ds-cmd-item-icon">{icon_svg}</span>'
            f'<span class="ds-cmd-item-label">{page}</span>'
            f'</div>'
        )

    palette_html = f"""
<div id="ds-cmd-overlay" class="ds-cmd-palette-overlay" onclick="closePalette(event)">
  <div class="ds-cmd-palette" onclick="event.stopPropagation()">
    <div class="ds-cmd-search-bar">
      <span class="ds-cmd-search-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
        </svg>
      </span>
      <input id="ds-cmd-input" class="ds-cmd-input" type="text"
             placeholder="Navigate to a page..." oninput="filterItems(this.value)" />
      <span class="ds-cmd-shortcut-label">ESC</span>
    </div>
    <div class="ds-cmd-section-title">Navigation</div>
    <div id="ds-cmd-items">
      {items_html}
    </div>
    <div class="ds-cmd-footer">
      <span><kbd>↑↓</kbd> navigate</span>
      <span><kbd>↵</kbd> open</span>
      <span><kbd>Esc</kbd> close</span>
    </div>
  </div>
</div>

<style>
.ds-cmd-palette-overlay {{
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(15,23,42,0.45);
  z-index: 99999;
  align-items: flex-start;
  justify-content: center;
  padding-top: 14vh;
  backdrop-filter: blur(4px);
}}
.ds-cmd-palette-overlay.active {{
  display: flex !important;
}}
</style>

<script>
(function() {{
  var overlay = document.getElementById('ds-cmd-overlay');
  var input = document.getElementById('ds-cmd-input');
  if (!overlay) return;

  // Listen for Ctrl+K on the parent window
  window.parent.document.addEventListener('keydown', function(e) {{
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {{
      e.preventDefault();
      overlay.classList.add('active');
      setTimeout(function() {{ input && input.focus(); }}, 80);
    }}
    if (e.key === 'Escape') {{
      overlay.classList.remove('active');
    }}
  }});

  window.closePalette = function(e) {{
    overlay.classList.remove('active');
  }};

  window.navigateTo = function(page) {{
    overlay.classList.remove('active');
    // Navigate via query param (triggers Streamlit rerun)
    var url = window.parent.location.href.split('?')[0] + '?page=' + encodeURIComponent(page);
    window.parent.location.href = url;
  }};

  window.filterItems = function(query) {{
    var items = document.querySelectorAll('#ds-cmd-items .ds-cmd-item');
    var q = query.toLowerCase();
    items.forEach(function(item) {{
      var label = item.querySelector('.ds-cmd-item-label');
      if (label && label.textContent.toLowerCase().includes(q)) {{
        item.style.display = '';
      }} else {{
        item.style.display = 'none';
      }}
    }});
  }};
}})();
</script>
"""

    st.components.v1.html(palette_html, height=0, scrolling=False)

    # Show keyboard shortcut hint
    st.markdown(
        '<div style="position:fixed;bottom:16px;right:20px;z-index:1000;'
        'display:flex;align-items:center;gap:6px;font-size:11px;color:var(--text-muted);'
        'background:var(--surface);border:1px solid var(--border);border-radius:6px;'
        'padding:4px 10px;box-shadow:var(--shadow-sm);">'
        '<kbd style="background:var(--bg-secondary);border:1px solid var(--border);'
        'border-radius:3px;padding:1px 5px;font-size:10px;font-family:monospace;">Ctrl+K</kbd>'
        '<span>Command Palette</span>'
        '</div>',
        unsafe_allow_html=True
    )


# ── Main Router ────────────────────────────────────────────────────────────────

def main() -> None:
    """Main routing dispatcher with route-level authentication protection."""

    # Route protection — unauthenticated users see login
    if not is_authenticated():
        render_login_page()
        return

    # Render premium sidebar and get active page
    active_page = render_sidebar()

    # Dataset context bar (shows on all pages when dataset is loaded)
    if is_dataset_loaded():
        render_dataset_context_bar()

    # Inject command palette overlay
    inject_command_palette()

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

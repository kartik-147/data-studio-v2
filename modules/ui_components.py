"""
DATA STUDIO v2 — Reusable Design System UI Components v2 (Premium)
=============================================================================
Linear / Stripe / Vercel / Notion Inspired UI Component Library.
Light-first premium SaaS design system.
Strictly generates unindented HTML to ensure seamless CommonMark rendering.
"""
from typing import Optional, Dict, Any, List
import os
import streamlit as st

# ============================================================================
# LUCIDE ICON LIBRARY (Minimalist SVG vectors)
# ============================================================================
LUCIDE_ICONS: Dict[str, str] = {
    "home": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>""",
    "layout-dashboard": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>""",
    "database": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/></svg>""",
    "shield-check": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/></svg>""",
    "shield": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/></svg>""",
    "wrench": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>""",
    "search": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>""",
    "bar-chart-3": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v16a2 2 0 0 0 2 2h16"/><rect x="7" y="10" width="3" height="7" rx="1"/><rect x="12" y="6" width="3" height="11" rx="1"/><rect x="17" y="13" width="3" height="4" rx="1"/></svg>""",
    "sparkles": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z"/></svg>""",
    "settings": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>""",
    "upload": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>""",
    "sun": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>""",
    "moon": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>""",
    "monitor": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="3" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/></svg>""",
    "info": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>""",
    "check-circle": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>""",
    "alert-triangle": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>""",
    "alert-circle": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>""",
    "arrow-right": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>""",
    "layers": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.9a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/></svg>""",
    "activity": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>""",
    "log-out": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>""",
    "zap": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>""",
    "trending-up": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>""",
    "file-text": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>""",
    "table": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"/></svg>""",
    "cpu": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/></svg>""",
    "eye": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>""",
    "users": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>""",
    "target": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>""",
    "check": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>""",
    "x": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>""",
    "chevron-right": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>""",
    "grid": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>""",
}


def get_icon_svg(name: str, size: int = 18) -> str:
    """Return raw SVG string for a requested Lucide icon name."""
    template = LUCIDE_ICONS.get(name, LUCIDE_ICONS["database"])
    return template.format(s=size)


# ============================================================================
# THEME & CSS INJECTION
# ============================================================================

def load_css(theme: str = "Light") -> None:
    """
    Inject the design system CSS with dynamic theme class application.
    Light is the default. Dark activates the .ds-theme-dark CSS class.
    """
    css_path = os.path.join(os.path.dirname(__file__), "..", "assets", "css", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()

    # Apply dark theme class on body via style injection when dark is active
    dark_override = ""
    if theme.lower() == "dark":
        dark_override = """
        /* Propagate dark theme tokens globally */
        .stApp, .main, [data-testid="stSidebar"], body {
            background-color: var(--bg-primary) !important;
        }
        """

    # Build theme class override block
    theme_class_block = ""
    if theme.lower() == "dark":
        theme_class_block = """
        :root {
            --bg-primary: #0b0f19;
            --bg-secondary: #0f1624;
            --surface: #141c2e;
            --surface-hover: #1a2540;
            --surface-active: #1f2d4d;
            --border: #1e2d45;
            --border-subtle: #172038;
            --border-focus: #3b82f6;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --text-inverted: #0b0f19;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --accent-subtle: rgba(59, 130, 246, 0.12);
            --accent-subtle-border: rgba(59, 130, 246, 0.25);
            --color-success: #10b981;
            --color-success-bg: rgba(16, 185, 129, 0.10);
            --color-success-border: rgba(16, 185, 129, 0.25);
            --color-success-text: #34d399;
            --color-warning: #f59e0b;
            --color-warning-bg: rgba(245, 158, 11, 0.10);
            --color-warning-border: rgba(245, 158, 11, 0.25);
            --color-warning-text: #fbbf24;
            --color-error: #ef4444;
            --color-error-bg: rgba(239, 68, 68, 0.10);
            --color-error-border: rgba(239, 68, 68, 0.25);
            --color-error-text: #f87171;
            --color-info: #3b82f6;
            --color-info-bg: rgba(59, 130, 246, 0.10);
            --color-info-border: rgba(59, 130, 246, 0.25);
            --color-info-text: #60a5fa;
            --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.20);
            --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.25), 0 1px 2px rgba(0, 0, 0, 0.20);
            --shadow-md: 0 4px 8px -2px rgba(0, 0, 0, 0.30), 0 2px 4px -2px rgba(0, 0, 0, 0.20);
            --shadow-lg: 0 12px 24px -4px rgba(0, 0, 0, 0.40), 0 4px 8px -4px rgba(0, 0, 0, 0.30);
            --shadow-xl: 0 20px 40px -8px rgba(0, 0, 0, 0.50), 0 8px 16px -8px rgba(0, 0, 0, 0.40);
            --nav-bg: #0f1624;
            --nav-item-text: #64748b;
            --nav-item-text-active: #60a5fa;
            --nav-item-bg-hover: #1a2540;
            --nav-item-bg-active: rgba(59, 130, 246, 0.12);
            --nav-group-title: #475569;
        }
        """

    full_css = f"<style>\n{css_content}\n{theme_class_block}\n{dark_override}\n</style>"
    st.markdown(full_css, unsafe_allow_html=True)


# ============================================================================
# PAGE HEADER COMPONENT
# ============================================================================

def render_page_header(
    title: str,
    subtitle: Optional[str] = None,
    icon: Optional[str] = None,
    badge: Optional[str] = None
) -> None:
    """Render a standardized, reusable page-level header component."""
    icon_html = f'<div class="ds-page-header-icon">{get_icon_svg(icon, 20)}</div>' if icon else ""
    subtitle_html = f'<p class="ds-page-subtitle">{subtitle}</p>' if subtitle else ""
    badge_html = f'<span style="font-size:10px;font-weight:700;background:var(--accent-subtle);color:var(--accent);border:1px solid var(--accent-subtle-border);border-radius:3px;padding:2px 8px;letter-spacing:0.04em;">{badge}</span>' if badge else ""

    html = (
        f'<div class="ds-page-header">'
        f'<div class="ds-page-header-main">'
        f'<div class="ds-page-title-row">'
        f'{icon_html}'
        f'<h1 class="ds-page-title">{title}</h1>'
        f'{badge_html}'
        f'</div>'
        f'{subtitle_html}'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# SECTION HEADER
# ============================================================================

def render_section_header(title: str, subtitle: Optional[str] = None) -> None:
    """Render a section header with standard typography."""
    sub_html = f'<p class="ds-section-subtitle">{subtitle}</p>' if subtitle else ""
    html = (
        f'<div class="ds-section-header">'
        f'<h2 class="ds-section-title">{title}</h2>'
        f'{sub_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# METRIC CARD v2
# ============================================================================

def render_metric_card(
    label: str,
    value: str,
    change: Optional[str] = None,
    change_type: str = "neutral",
    description: Optional[str] = None,
    status: Optional[str] = None,
    icon: Optional[str] = None
) -> None:
    """Render a premium analytics metric card with optional icon and status badge."""
    status_html = f'<span class="ds-metric-status">{status}</span>' if status else ""
    icon_html = f'<div style="color:var(--text-muted);display:flex;align-items:center;">{get_icon_svg(icon, 15)}</div>' if icon else ""

    footer_parts: list = []
    if change:
        change_class = f"ds-metric-change-{change_type}"
        footer_parts.append(f'<span class="{change_class}">{change}</span>')
    if description:
        footer_parts.append(f'<span class="ds-metric-desc">{description}</span>')

    footer_html = f'<div class="ds-metric-footer">{"&nbsp;·&nbsp;".join(footer_parts)}</div>' if footer_parts else ""

    html = (
        f'<div class="ds-metric-card">'
        f'<div class="ds-metric-header">'
        f'<div style="display:flex;align-items:center;gap:6px;">'
        f'{icon_html}'
        f'<span class="ds-metric-label">{label}</span>'
        f'</div>'
        f'{status_html}'
        f'</div>'
        f'<div class="ds-metric-value">{value}</div>'
        f'{footer_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# INSIGHT CARD (New Component)
# ============================================================================

def render_insight_card(
    title: str,
    description: str,
    priority: str = "info",
    actions: Optional[List[Dict[str, str]]] = None,
    icon: Optional[str] = None
) -> None:
    """
    Render a contextual insight card with priority badge and optional action buttons.
    priority: 'critical' | 'warning' | 'info' | 'healthy'
    actions: [{"label": "Explore", "page": "Data Quality"}]
    """
    icon_name = icon or {
        "critical": "alert-circle",
        "warning": "alert-triangle",
        "info": "info",
        "healthy": "check-circle"
    }.get(priority, "info")

    icon_svg = get_icon_svg(icon_name, 16)
    priority_label_map = {
        "critical": "Critical",
        "warning": "Warning",
        "info": "Info",
        "healthy": "Healthy"
    }

    actions_html = ""
    if actions:
        btns = "".join(
            f'<span class="ds-insight-action-btn">{a.get("label", "View")}</span>'
            for a in actions
        )
        actions_html = f'<div class="ds-insight-actions">{btns}</div>'

    html = (
        f'<div class="ds-insight-card">'
        f'<div class="ds-insight-icon ds-insight-icon-{priority}">{icon_svg}</div>'
        f'<div class="ds-insight-body">'
        f'<div class="ds-insight-title">{title}</div>'
        f'<div class="ds-insight-description">{description}</div>'
        f'{actions_html}'
        f'</div>'
        f'<span class="ds-insight-priority ds-priority-{priority}">{priority_label_map.get(priority, priority.capitalize())}</span>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# DATASET CONTEXT BAR (New Component)
# ============================================================================

def render_dataset_context_bar() -> None:
    """
    Render a compact dataset context bar at the top of content pages.
    Shows: dataset name, rows×cols, dataset state (original/prepared), quality score.
    Only renders if a dataset is loaded.
    """
    df = st.session_state.get("dataset")
    if df is None:
        return

    name = st.session_state.get("dataset_name", "dataset.csv")
    rows, cols = df.shape
    metadata = st.session_state.get("dataset_metadata") or {}
    quality_score = metadata.get("quality_score")
    is_prepared = st.session_state.get("cleaned_dataset") is not None

    db_icon = get_icon_svg("database", 14)

    quality_badge = ""
    if quality_score is not None:
        q_val = int(quality_score)
        quality_badge = (
            f'<span class="ds-context-bar-badge ds-context-badge-quality">'
            f'{get_icon_svg("shield-check", 11)}&nbsp;Quality&nbsp;{q_val}%'
            f'</span>'
        )

    state_class = "ds-context-badge-prepared" if is_prepared else "ds-context-badge-original"
    state_label = "Prepared" if is_prepared else "Original"
    state_badge = (
        f'<span class="ds-context-bar-badge {state_class}">'
        f'{state_label}'
        f'</span>'
    )

    html = (
        f'<div class="ds-context-bar">'
        f'<div class="ds-context-bar-left">'
        f'<div class="ds-context-bar-icon">{db_icon}</div>'
        f'<div>'
        f'<div class="ds-context-bar-name">{name}</div>'
        f'<div class="ds-context-bar-meta">{rows:,} rows &times; {cols} columns</div>'
        f'</div>'
        f'</div>'
        f'<div class="ds-context-bar-right">'
        f'{state_badge}'
        f'{quality_badge}'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# ACTIVITY ITEM (New Component)
# ============================================================================

def render_activity_list(max_items: int = 5) -> None:
    """Render the recent activity timeline from session state."""
    log: list = st.session_state.get("activity_log", [])

    if not log:
        st.markdown(
            '<div style="font-size:12px;color:var(--text-muted);padding:8px 0;">'
            'No activity recorded yet.</div>',
            unsafe_allow_html=True
        )
        return

    items_html = ""
    for entry in reversed(log[-max_items:]):
        items_html += (
            f'<div class="ds-activity-item">'
            f'<div class="ds-activity-dot"></div>'
            f'<div class="ds-activity-text">{entry.get("event", "")}</div>'
            f'<div class="ds-activity-time">{entry.get("timestamp", "")}</div>'
            f'</div>'
        )

    html = f'<div class="ds-activity-list">{items_html}</div>'
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# QUICK ACTION GRID (New Component)
# ============================================================================

def render_quick_action_grid(actions: List[Dict[str, str]]) -> None:
    """
    Render a responsive quick-action grid of cards (purely visual, no click handling).
    Each action dict: {"icon": "database", "title": "Upload", "desc": "..."}
    Click handling is done via st.button placed after this HTML.
    """
    cards_html = ""
    for a in actions:
        icon_svg = get_icon_svg(a.get("icon", "zap"), 18)
        cards_html += (
            f'<div class="ds-action-card">'
            f'<div class="ds-action-icon">{icon_svg}</div>'
            f'<div class="ds-action-title">{a.get("title", "")}</div>'
            f'<div class="ds-action-desc">{a.get("desc", "")}</div>'
            f'</div>'
        )
    html = f'<div class="ds-action-grid">{cards_html}</div>'
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# NOTIFICATION / ALERT
# ============================================================================

def render_notification(
    title: str,
    message: Optional[str] = None,
    variant: str = "info"
) -> None:
    """Render a semantic notification component."""
    icon_map = {
        "info": "info",
        "success": "check-circle",
        "warning": "alert-triangle",
        "error": "alert-circle"
    }
    icon_svg = get_icon_svg(icon_map.get(variant, "info"), 16)
    msg_html = f'<div class="ds-notif-desc">{message}</div>' if message else ""

    html = (
        f'<div class="ds-notification ds-notification-{variant}">'
        f'<div class="ds-notif-icon">{icon_svg}</div>'
        f'<div class="ds-notif-body">'
        f'<div class="ds-notif-title">{title}</div>'
        f'{msg_html}'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# EMPTY STATE
# ============================================================================

def render_empty_state(
    title: str = "No dataset loaded",
    description: str = "Upload a CSV or Excel file to start exploring your data.",
    icon: str = "database",
    action_label: Optional[str] = None
) -> None:
    """Render a clean empty state card."""
    icon_svg = get_icon_svg(icon, 22)
    action_html = (
        f'<div style="margin-top:16px;font-size:12px;font-weight:600;'
        f'color:var(--accent);cursor:pointer;">{action_label}</div>'
    ) if action_label else ""

    html = (
        f'<div class="ds-empty-state-card">'
        f'<div class="ds-empty-icon-circle">{icon_svg}</div>'
        f'<div class="ds-empty-heading">{title}</div>'
        f'<div class="ds-empty-body">{description}</div>'
        f'{action_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# SKELETON LOADER
# ============================================================================

def render_skeleton_loader(variant: str = "card") -> None:
    """Render skeleton placeholder shimmer components."""
    if variant == "card":
        html = (
            '<div class="ds-skeleton-card">'
            '<div class="ds-skeleton ds-skeleton-line" style="width: 40%;"></div>'
            '<div class="ds-skeleton ds-skeleton-line-lg"></div>'
            '<div class="ds-skeleton ds-skeleton-line" style="width: 70%;"></div>'
            '</div>'
        )
    elif variant == "chart":
        html = (
            '<div class="ds-skeleton-chart">'
            '<div class="ds-skeleton-bar" style="height: 35%;"></div>'
            '<div class="ds-skeleton-bar" style="height: 65%;"></div>'
            '<div class="ds-skeleton-bar" style="height: 90%;"></div>'
            '<div class="ds-skeleton-bar" style="height: 50%;"></div>'
            '<div class="ds-skeleton-bar" style="height: 75%;"></div>'
            '<div class="ds-skeleton-bar" style="height: 40%;"></div>'
            '</div>'
        )
    elif variant == "table":
        html = (
            '<div class="ds-skeleton-card">'
            '<div class="ds-skeleton ds-skeleton-line" style="width: 100%; height: 26px;"></div>'
            '<div class="ds-skeleton ds-skeleton-line" style="width: 100%; height: 18px;"></div>'
            '<div class="ds-skeleton ds-skeleton-line" style="width: 100%; height: 18px;"></div>'
            '<div class="ds-skeleton ds-skeleton-line" style="width: 100%; height: 18px;"></div>'
            '</div>'
        )
    else:  # dashboard
        html = (
            '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 18px;">'
            '<div class="ds-skeleton-card"><div class="ds-skeleton ds-skeleton-line" style="width: 50%;"></div>'
            '<div class="ds-skeleton ds-skeleton-line-lg"></div></div>'
            '<div class="ds-skeleton-card"><div class="ds-skeleton ds-skeleton-line" style="width: 50%;"></div>'
            '<div class="ds-skeleton ds-skeleton-line-lg"></div></div>'
            '<div class="ds-skeleton-card"><div class="ds-skeleton ds-skeleton-line" style="width: 50%;"></div>'
            '<div class="ds-skeleton ds-skeleton-line-lg"></div></div>'
            '<div class="ds-skeleton-card"><div class="ds-skeleton ds-skeleton-line" style="width: 50%;"></div>'
            '<div class="ds-skeleton ds-skeleton-line-lg"></div></div>'
            '</div>'
        )
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# TYPE BADGE UTILITY
# ============================================================================

def get_type_badge_html(detected_type: str) -> str:
    """Return styled HTML badge for semantic column data types."""
    type_class_map = {
        "Numeric": "ds-badge-numeric",
        "Categorical": "ds-badge-categorical",
        "Date/Time": "ds-badge-datetime",
        "Text": "ds-badge-text",
        "Boolean": "ds-badge-boolean"
    }
    css_class = type_class_map.get(detected_type, "ds-badge-neutral")
    return f'<span class="ds-badge {css_class}">{detected_type}</span>'


# ============================================================================
# PLACEHOLDER PAGE (for unimplemented modules)
# ============================================================================

def render_placeholder_page(
    title: str,
    subtitle: str,
    icon: str,
    module_phase: str = "Upcoming Module"
) -> None:
    """Render a polished placeholder screen for future analytics modules."""
    render_page_header(title=title, subtitle=subtitle, icon=icon, badge=module_phase)

    render_notification(
        title=f"{title} is scheduled for implementation",
        message=f"This module will be activated in an upcoming development phase. {subtitle}",
        variant="info"
    )

    render_empty_state(
        title="No active analysis dataset",
        description=(
            f"Once a dataset is loaded, the {title.lower()} engine will "
            f"generate analytical outputs here."
        ),
        icon=icon
    )

    st.markdown(
        "<h5 style='margin-top:20px;margin-bottom:12px;font-size:13px;"
        "font-weight:600;color:var(--text-muted);'>Preview Layout Architecture</h5>",
        unsafe_allow_html=True
    )
    render_skeleton_loader(variant="dashboard")

    col1, col2 = st.columns([6, 4])
    with col1:
        render_skeleton_loader(variant="chart")
    with col2:
        render_skeleton_loader(variant="table")

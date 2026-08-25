"""
DATA STUDIO v2 — Reusable Design System UI Components
=============================================================================
Linear / Stripe / Vercel / Notion Inspired UI Component Library.
Strictly generates unindented HTML to ensure seamless CommonMark rendering.
"""
from typing import Optional, Dict, Any, List
import os
import streamlit as st

# Lucide-style minimalist SVG icons (Clean vector paths, zero emojis)
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
    "info": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>""",
    "check-circle": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>""",
    "alert-triangle": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>""",
    "alert-circle": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>""",
    "arrow-right": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>""",
    "layers": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.9a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/></svg>"""
}

def get_icon_svg(name: str, size: int = 18) -> str:
    """Return raw SVG string for a requested icon."""
    template = LUCIDE_ICONS.get(name, LUCIDE_ICONS["database"])
    return template.format(s=size)


def load_css(theme: str = "Dark") -> None:
    """Inject custom design system CSS with dynamic light/dark theme overrides."""
    css_path = os.path.join(os.path.dirname(__file__), "..", "assets", "css", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
            
        theme_override = ""
        if theme.lower() == "light":
            theme_override = """
            :root {
                --bg-primary: #f8fafc;
                --bg-secondary: #ffffff;
                --surface: #ffffff;
                --surface-hover: #f1f5f9;
                --surface-active: #e2e8f0;
                --border: #e2e8f0;
                --border-subtle: #edf2f7;
                --border-focus: #2563eb;

                --text-primary: #0f172a;
                --text-secondary: #475569;
                --text-muted: #64748b;
                --text-inverted: #f8fafc;

                --accent: #2563eb;
                --accent-hover: #1d4ed8;
                --accent-subtle: rgba(37, 99, 235, 0.08);

                --color-success: #059669;
                --color-success-bg: rgba(5, 150, 105, 0.08);
                --color-success-border: rgba(5, 150, 105, 0.2);

                --color-warning: #d97706;
                --color-warning-bg: rgba(217, 119, 6, 0.08);
                --color-warning-border: rgba(217, 119, 6, 0.2);

                --color-error: #dc2626;
                --color-error-bg: rgba(220, 38, 38, 0.08);
                --color-error-border: rgba(220, 38, 38, 0.2);

                --color-info: #2563eb;
                --color-info-bg: rgba(37, 99, 235, 0.08);
                --color-info-border: rgba(37, 99, 235, 0.2);
            }
            """
            
        custom_html = f"<style>\n{css_content}\n{theme_override}\n</style>"
        st.markdown(custom_html, unsafe_allow_html=True)


def render_page_header(
    title: str,
    subtitle: Optional[str] = None,
    icon: Optional[str] = None
) -> None:
    """Render a standardized, reusable page header component."""
    icon_html = f'<div class="ds-page-header-icon">{get_icon_svg(icon, 24)}</div>' if icon else ""
    subtitle_html = f'<p class="ds-page-subtitle">{subtitle}</p>' if subtitle else ""
    
    html = (
        f'<div class="ds-page-header">'
        f'<div class="ds-page-header-main">'
        f'<div class="ds-page-title-row">'
        f'{icon_html}'
        f'<h1 class="ds-page-title">{title}</h1>'
        f'</div>'
        f'{subtitle_html}'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


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


def render_metric_card(
    label: str,
    value: str,
    change: Optional[str] = None,
    change_type: str = "neutral",
    description: Optional[str] = None,
    status: Optional[str] = None
) -> None:
    """Render a clean analytics metric card."""
    status_html = f'<span class="ds-metric-status">{status}</span>' if status else ""
    
    footer_parts = []
    if change:
        change_class = f"ds-metric-change-{change_type}"
        footer_parts.append(f'<span class="{change_class}">{change}</span>')
    if description:
        footer_parts.append(f'<span class="ds-metric-desc">{description}</span>')
        
    footer_html = f'<div class="ds-metric-footer">{" • ".join(footer_parts)}</div>' if footer_parts else ""
    
    html = (
        f'<div class="ds-metric-card">'
        f'<div class="ds-metric-header">'
        f'<span class="ds-metric-label">{label}</span>'
        f'{status_html}'
        f'</div>'
        f'<div class="ds-metric-value">{value}</div>'
        f'{footer_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_notification(
    title: str,
    message: Optional[str] = None,
    variant: str = "info"
) -> None:
    """Render a clean semantic notification component."""
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


def render_empty_state(
    title: str = "No dataset loaded",
    description: str = "Upload a CSV or Excel file to start exploring your data and generating insights.",
    icon: str = "database"
) -> None:
    """Render a clean empty state card."""
    icon_svg = get_icon_svg(icon, 20)
    html = (
        f'<div class="ds-empty-state-card">'
        f'<div class="ds-empty-icon-circle">{icon_svg}</div>'
        f'<div class="ds-empty-heading">{title}</div>'
        f'<div class="ds-empty-body">{description}</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_skeleton_loader(variant: str = "card") -> None:
    """Render skeleton placeholder components."""
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
    else: # dashboard
        html = (
            '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px;">'
            '<div class="ds-skeleton-card"><div class="ds-skeleton ds-skeleton-line" style="width: 50%;"></div><div class="ds-skeleton ds-skeleton-line-lg"></div></div>'
            '<div class="ds-skeleton-card"><div class="ds-skeleton ds-skeleton-line" style="width: 50%;"></div><div class="ds-skeleton ds-skeleton-line-lg"></div></div>'
            '<div class="ds-skeleton-card"><div class="ds-skeleton ds-skeleton-line" style="width: 50%;"></div><div class="ds-skeleton ds-skeleton-line-lg"></div></div>'
            '<div class="ds-skeleton-card"><div class="ds-skeleton ds-skeleton-line" style="width: 50%;"></div><div class="ds-skeleton ds-skeleton-line-lg"></div></div>'
            '</div>'
        )
    st.markdown(html, unsafe_allow_html=True)


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

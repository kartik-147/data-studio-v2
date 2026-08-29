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
    "sliders": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="1" x2="7" y1="14" y2="14"/><line x1="9" x2="15" y1="8" y2="8"/><line x1="17" x2="23" y1="16" y2="16"/></svg>""",
    "search": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>""",
    "bar-chart-3": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v16a2 2 0 0 0 2 2h16"/><rect x="7" y="10" width="3" height="7" rx="1"/><rect x="12" y="6" width="3" height="11" rx="1"/><rect x="17" y="13" width="3" height="4" rx="1"/></svg>""",
    "panels-top-left": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>""",
    "sparkles": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z"/></svg>""",
    "brain": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M12 18v4"/></svg>""",
    "book-open": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>""",
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
    "user": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>""",
    "users": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>""",
    "target": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>""",
    "check": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>""",
    "x": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>""",
    "chevron-right": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>""",
    "grid": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>""",
    "menu": """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>""",
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
    Light is the default. Dark activates dark mode tokens and overrides.
    Ensures all tables, dataframes, buttons, tabs, inputs, and cards are 100% visible and themed.
    """
    css_path = os.path.join(os.path.dirname(__file__), "..", "assets", "css", "style.css")
    css_content = ""
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()

    is_dark = theme.lower() == "dark"

    if is_dark:
        theme_block = """
        /* ══════════════════════════════════════════════════════════════════════
           DARK THEME CONFIGURATION & COMPLETE ELEMENT OVERRIDES
           ══════════════════════════════════════════════════════════════════════ */
        :root {
            --app-bg: #0b0f19;
            --bg-primary: #0b0f19;
            --bg-secondary: #0f1624;
            --surface: #141c2e;
            --surface-secondary: #0f1624;
            --surface-hover: #182234;
            --surface-active: #1f2d4d;
            --surface-container-low: #182234;
            --surface-container: #1e293b;
            --surface-container-high: #243048;
            --border: #1e2d45;
            --border-light: #1e2d45;
            --border-subtle: #172038;
            --border-dashed: #334155;
            --border-focus: #38bdf8;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --text-inverted: #0b0f19;
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --primary-action: #2563eb;
            --primary-action-text: #ffffff;
            --accent: #38bdf8;
            --accent-hover: #0ea5e9;
            --accent-subtle: rgba(56, 189, 248, 0.12);
            --accent-subtle-border: rgba(56, 189, 248, 0.25);
            --color-success: #10b981;
            --color-success-bg: rgba(16, 185, 129, 0.12);
            --color-success-border: rgba(16, 185, 129, 0.25);
            --color-success-text: #34d399;
            --color-warning: #f59e0b;
            --color-warning-bg: rgba(245, 158, 11, 0.12);
            --color-warning-border: rgba(245, 158, 11, 0.25);
            --color-warning-text: #fbbf24;
            --color-error: #ef4444;
            --color-error-bg: rgba(239, 68, 68, 0.12);
            --color-error-border: rgba(239, 68, 68, 0.25);
            --color-error-text: #f87171;
            --color-info: #38bdf8;
            --color-info-bg: rgba(56, 189, 248, 0.12);
            --color-info-border: rgba(56, 189, 248, 0.25);
            --color-info-text: #38bdf8;
            --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.20);
            --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.25), 0 1px 2px rgba(0, 0, 0, 0.20);
            --shadow-md: 0 4px 8px -2px rgba(0, 0, 0, 0.30), 0 2px 4px -2px rgba(0, 0, 0, 0.20);
            --shadow-lg: 0 12px 24px -4px rgba(0, 0, 0, 0.40), 0 4px 8px -4px rgba(0, 0, 0, 0.30);
            --shadow-xl: 0 20px 40px -8px rgba(0, 0, 0, 0.50), 0 8px 16px -8px rgba(0, 0, 0, 0.40);
            --nav-bg: #0f1624;
            --nav-item-text: #64748b;
            --nav-item-text-active: #f1f5f9;
            --nav-item-bg-hover: #182234;
            --nav-item-bg-active: rgba(56, 189, 248, 0.12);
            --nav-group-title: #475569;

            /* Streamlit Native Variables Override for Dark Mode */
            --background-color: #0b0f19;
            --secondary-background-color: #141c2e;
            --text-color: #f1f5f9;
            --primary-color: #38bdf8;
        }

        /* Global App Canvas in Dark Mode */
        .stApp, .main, body, section[data-testid="stMain"],
        div[data-testid="stAppViewContainer"],
        div[data-testid="stAppViewBlockContainer"],
        div[data-testid="stMainBlockContainer"] {
            background-color: #0b0f19 !important;
            color: #f1f5f9 !important;
        }

        /* Sidebar in Dark Mode */
        section[data-testid="stSidebar"],
        [data-testid="stSidebar"] {
            background-color: #141c2e !important;
            border-right: 1px solid #1e2d45 !important;
        }

        /* ── All Secondary / Standard Buttons in Dark Mode ─────────── */
        .stButton > button,
        div[data-testid="stButton"] button,
        button[data-testid="stBaseButton-secondary"],
        button[data-testid="baseButton-secondary"],
        button[data-testid="stBaseButton-minimal"],
        button[data-testid="stBaseButton-tertiary"],
        button[data-testid="stBaseButton-header"],
        button[data-testid="stBaseButton-icon"],
        .stButton > button[kind="secondary"],
        .stButton > button:not([kind="primary"]),
        div[data-testid="stDownloadButton"] button,
        div[data-testid="stFormSubmitButton"] button:not([kind="primary"]),
        div[data-testid="stFileUploader"] section button,
        div[data-testid="stFileUploader"] button,
        div[data-testid="stPills"] button:not([aria-selected="true"]),
        div[data-testid="stSegmentedControl"] button:not([aria-selected="true"]),
        div[data-testid="stPopover"] button,
        div[data-testid="stButtonGroup"] button,
        button[kind="secondary"],
        button[kind="secondaryFormSubmit"],
        div[data-testid="stLinkButton"] a {
            background-color: #182234 !important;
            color: #f8fafc !important;
            border: 1px solid #334155 !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
        }

        /* Universal Text inside Secondary Buttons in Dark Mode */
        .stButton > button *,
        div[data-testid="stButton"] button *,
        button[data-testid="stBaseButton-secondary"] *,
        button[data-testid="baseButton-secondary"] *,
        button[data-testid="stBaseButton-minimal"] *,
        button[data-testid="stBaseButton-tertiary"] *,
        button[data-testid="stBaseButton-header"] *,
        button[data-testid="stBaseButton-icon"] *,
        .stButton > button[kind="secondary"] *,
        .stButton > button:not([kind="primary"]) *,
        div[data-testid="stDownloadButton"] button *,
        div[data-testid="stFormSubmitButton"] button:not([kind="primary"]) *,
        div[data-testid="stFileUploader"] section button *,
        div[data-testid="stFileUploader"] button *,
        div[data-testid="stPills"] button:not([aria-selected="true"]) *,
        div[data-testid="stSegmentedControl"] button:not([aria-selected="true"]) *,
        div[data-testid="stPopover"] button *,
        div[data-testid="stButtonGroup"] button *,
        button[kind="secondary"] *,
        button[kind="secondaryFormSubmit"] *,
        div[data-testid="stLinkButton"] a * {
            color: #f8fafc !important;
            fill: #f8fafc !important;
            font-weight: 600 !important;
        }

        /* Secondary Buttons Hover State in Dark Mode */
        .stButton > button:hover,
        div[data-testid="stButton"] button:hover,
        button[data-testid="stBaseButton-secondary"]:hover,
        button[data-testid="baseButton-secondary"]:hover,
        button[data-testid="stBaseButton-minimal"]:hover,
        button[data-testid="stBaseButton-tertiary"]:hover,
        button[data-testid="stBaseButton-header"]:hover,
        button[data-testid="stBaseButton-icon"]:hover,
        .stButton > button[kind="secondary"]:hover,
        .stButton > button:not([kind="primary"]):hover,
        div[data-testid="stDownloadButton"] button:hover,
        div[data-testid="stFormSubmitButton"] button:not([kind="primary"]):hover,
        div[data-testid="stFileUploader"] section button:hover,
        div[data-testid="stFileUploader"] button:hover,
        div[data-testid="stPills"] button:hover,
        div[data-testid="stSegmentedControl"] button:hover,
        div[data-testid="stPopover"] button:hover,
        div[data-testid="stButtonGroup"] button:hover,
        button[kind="secondary"]:hover,
        button[kind="secondaryFormSubmit"]:hover,
        div[data-testid="stLinkButton"] a:hover {
            background-color: #243048 !important;
            border-color: #38bdf8 !important;
            color: #38bdf8 !important;
        }

        .stButton > button:hover *,
        div[data-testid="stButton"] button:hover *,
        button[data-testid="stBaseButton-secondary"]:hover *,
        button[data-testid="baseButton-secondary"]:hover *,
        button[data-testid="stBaseButton-minimal"]:hover *,
        button[data-testid="stBaseButton-tertiary"]:hover *,
        button[data-testid="stBaseButton-header"]:hover *,
        button[data-testid="stBaseButton-icon"]:hover *,
        .stButton > button[kind="secondary"]:hover *,
        .stButton > button:not([kind="primary"]):hover *,
        div[data-testid="stDownloadButton"] button:hover *,
        div[data-testid="stFormSubmitButton"] button:not([kind="primary"]):hover *,
        div[data-testid="stFileUploader"] section button:hover *,
        div[data-testid="stFileUploader"] button:hover *,
        div[data-testid="stPills"] button:hover *,
        div[data-testid="stSegmentedControl"] button:hover *,
        div[data-testid="stPopover"] button:hover *,
        div[data-testid="stButtonGroup"] button:hover *,
        button[kind="secondary"]:hover *,
        button[kind="secondaryFormSubmit"]:hover *,
        div[data-testid="stLinkButton"] a:hover * {
            color: #38bdf8 !important;
            fill: #38bdf8 !important;
        }

        /* ── All Primary Buttons in Dark Mode ──────────────────────── */
        .stButton > button[kind="primary"],
        div[data-testid="stButton"] button[kind="primary"],
        button[data-testid="stBaseButton-primary"],
        button[data-testid="baseButton-primary"],
        button[kind="primary"],
        button[kind="primaryFormSubmit"],
        div[data-testid="stFormSubmitButton"] button[kind="primary"] {
            background-color: #2563eb !important;
            border: 1px solid #3b82f6 !important;
            color: #ffffff !important;
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4) !important;
        }

        .stButton > button[kind="primary"] *,
        div[data-testid="stButton"] button[kind="primary"] *,
        button[data-testid="stBaseButton-primary"] *,
        button[data-testid="baseButton-primary"] *,
        button[kind="primary"] *,
        button[kind="primaryFormSubmit"] *,
        div[data-testid="stFormSubmitButton"] button[kind="primary"] * {
            color: #ffffff !important;
            fill: #ffffff !important;
            font-weight: 600 !important;
        }

        .stButton > button[kind="primary"]:hover,
        div[data-testid="stButton"] button[kind="primary"]:hover,
        button[data-testid="stBaseButton-primary"]:hover,
        button[data-testid="baseButton-primary"]:hover,
        button[kind="primary"]:hover,
        button[kind="primaryFormSubmit"]:hover,
        div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
            background-color: #1d4ed8 !important;
            border-color: #60a5fa !important;
            color: #ffffff !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.5) !important;
        }

        .stButton > button[kind="primary"]:hover *,
        div[data-testid="stButton"] button[kind="primary"]:hover *,
        button[data-testid="stBaseButton-primary"]:hover *,
        button[data-testid="baseButton-primary"]:hover *,
        button[kind="primary"]:hover *,
        button[kind="primaryFormSubmit"]:hover *,
        div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover * {
            color: #ffffff !important;
            fill: #ffffff !important;
        }

        /* ── Tabs in Dark Mode ─────────────────────────────────────── */
        div[data-testid="stTabs"] button[role="tab"] {
            color: #94a3b8 !important;
            background-color: transparent !important;
            border: none !important;
        }

        div[data-testid="stTabs"] button[role="tab"] * {
            color: #94a3b8 !important;
        }

        div[data-testid="stTabs"] button[role="tab"]:hover {
            color: #f1f5f9 !important;
        }

        div[data-testid="stTabs"] button[role="tab"]:hover * {
            color: #f1f5f9 !important;
        }

        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: #38bdf8 !important;
            border-bottom: 2px solid #38bdf8 !important;
        }

        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] * {
            color: #38bdf8 !important;
            font-weight: 700 !important;
        }

        /* ── Active Pills & Segmented Controls in Dark Mode ────────── */
        div[data-testid="stPills"] button[aria-selected="true"],
        div[data-testid="stSegmentedControl"] button[aria-selected="true"] {
            background-color: #2563eb !important;
            border-color: #3b82f6 !important;
            color: #ffffff !important;
        }

        div[data-testid="stPills"] button[aria-selected="true"] *,
        div[data-testid="stSegmentedControl"] button[aria-selected="true"] * {
            color: #ffffff !important;
            font-weight: 600 !important;
        }

        /* ── Tables & DataFrames in Dark Mode (No White Flash) ─────── */
        div[data-testid="stDataFrame"],
        div[data-testid="stDataFrame"] > div,
        div[data-testid="stDataFrameRoot"],
        div[data-testid="stDataFrameResizable"],
        div[class*="glideDataGrid"],
        div[data-testid="stDataFrame"] iframe {
            background-color: #141c2e !important;
            border: 1px solid #1e2d45 !important;
            border-radius: 8px !important;
            color: #f1f5f9 !important;
        }

        div[data-testid="stDataFrame"] canvas {
            filter: invert(0.92) hue-rotate(180deg) brightness(0.95) contrast(1.05);
            border-radius: 6px !important;
        }

        div[data-testid="stDataFrame"] div[data-testid="stDataFrameResizable"] {
            background-color: #141c2e !important;
        }

        div[data-testid="stDataFrame"] [data-testid="StyledFullScreenButton"],
        div[data-testid="stDataFrame"] [data-testid="stDataFrameToolbar"] button,
        div[data-testid="stDataFrame"] button {
            background-color: #182234 !important;
            color: #f1f5f9 !important;
            border: 1px solid #334155 !important;
            border-radius: 4px !important;
        }

        div[data-testid="stDataFrame"] [data-testid="StyledFullScreenButton"]:hover,
        div[data-testid="stDataFrame"] [data-testid="stDataFrameToolbar"] button:hover,
        div[data-testid="stDataFrame"] button:hover {
            background-color: #243048 !important;
            color: #38bdf8 !important;
            border-color: #38bdf8 !important;
        }

        div[data-testid="stDataFrame"] [data-testid="stDataFrameToolbar"] svg,
        div[data-testid="stDataFrame"] [data-testid="stDataFrameToolbar"] button * {
            color: #f1f5f9 !important;
            fill: #f1f5f9 !important;
        }

        div[data-testid="stDataFrame"] input {
            background-color: #182234 !important;
            color: #f1f5f9 !important;
            border: 1px solid #334155 !important;
        }

        /* Custom and HTML Tables in Dark Mode */
        .stitch-table-container,
        div[data-testid="stTable"],
        div[data-testid="stTable"] > div,
        table.dataframe,
        .dataframe {
            background-color: #141c2e !important;
            border: 1px solid #1e2d45 !important;
            border-radius: 8px !important;
            color: #f1f5f9 !important;
        }

        .stitch-table,
        div[data-testid="stTable"] table,
        table.dataframe,
        .dataframe {
            background-color: #141c2e !important;
            color: #f1f5f9 !important;
            width: 100% !important;
            border-collapse: collapse !important;
        }

        .stitch-table th,
        div[data-testid="stTable"] th,
        table.dataframe th,
        .dataframe th,
        table th {
            background-color: #182234 !important;
            color: #f8fafc !important;
            border-bottom: 1px solid #1e2d45 !important;
            font-weight: 700 !important;
        }

        .stitch-table td,
        div[data-testid="stTable"] td,
        table.dataframe td,
        .dataframe td,
        table td {
            background-color: #141c2e !important;
            color: #cbd5e1 !important;
            border-bottom: 1px solid #1e2d45 !important;
        }

        .stitch-table tr:nth-child(even) td,
        div[data-testid="stTable"] tr:nth-child(even) td,
        table.dataframe tr:nth-child(even) td {
            background-color: #162032 !important;
        }

        .stitch-table tr:nth-child(odd) td,
        div[data-testid="stTable"] tr:nth-child(odd) td,
        table.dataframe tr:nth-child(odd) td {
            background-color: #141c2e !important;
        }

        .stitch-table tr:hover td,
        div[data-testid="stTable"] tr:hover td,
        table.dataframe tr:hover td {
            background-color: #1e2d45 !important;
            color: #ffffff !important;
        }

        .stitch-table .null-val {
            color: #64748b !important;
        }

        .stitch-table-footer {
            color: #94a3b8 !important;
        }

        /* ── Inputs, Selectboxes, Dropdowns & Popovers in Dark Mode ── */
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
        div[data-baseweb="select"] > div,
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stDateInput"] input,
        div[data-testid="stTimeInput"] input {
            background-color: #141c2e !important;
            color: #f1f5f9 !important;
            border: 1px solid #1e2d45 !important;
            border-radius: 6px !important;
        }

        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div *,
        div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div *,
        div[data-baseweb="select"] > div *,
        div[data-testid="stTextInput"] input *,
        div[data-testid="stNumberInput"] input *,
        div[data-testid="stTextArea"] textarea * {
            color: #f1f5f9 !important;
        }

        div[data-baseweb="select"] input {
            color: #f1f5f9 !important;
            background-color: transparent !important;
        }

        div[data-baseweb="select"] svg {
            fill: #94a3b8 !important;
            color: #94a3b8 !important;
        }

        /* Multiselect Tags (Pills) */
        span[data-baseweb="tag"],
        div[data-testid="stMultiSelect"] span[data-baseweb="tag"],
        div[data-baseweb="tag"] {
            background-color: #1e293b !important;
            color: #f1f5f9 !important;
            border: 1px solid #334155 !important;
            border-radius: 4px !important;
        }

        span[data-baseweb="tag"] *,
        div[data-baseweb="tag"] * {
            color: #f1f5f9 !important;
        }

        span[data-baseweb="tag"] [role="presentation"],
        span[data-baseweb="tag"] svg,
        div[data-baseweb="tag"] svg {
            fill: #94a3b8 !important;
            color: #94a3b8 !important;
        }

        span[data-baseweb="tag"] [role="presentation"]:hover svg,
        div[data-baseweb="tag"] svg:hover {
            fill: #ef4444 !important;
            color: #ef4444 !important;
        }

        /* ── Complete Dropdown Popovers, Virtual Menus & Listboxes in Dark Mode ── */
        div[data-baseweb="popover"],
        div[data-baseweb="popover"] > div,
        div[data-baseweb="popover"] ul,
        div[data-baseweb="popover"] div,
        div[data-baseweb="menu"],
        div[data-baseweb="menu"] > ul,
        ul[data-baseweb="menu"],
        ul[role="listbox"],
        div[role="listbox"],
        div[data-testid*="VirtualDropdown"],
        div[data-testid*="virtualDropdown"],
        div[data-testid="stSelectboxVirtualDropdown"],
        div[data-testid="stMultiSelectVirtualDropdown"],
        div[data-testid="stPopoverBody"] {
            background-color: #141c2e !important;
            color: #f1f5f9 !important;
            border: 1px solid #1e2d45 !important;
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.65) !important;
        }

        div[data-baseweb="popover"] *,
        div[data-baseweb="menu"] *,
        ul[role="listbox"] *,
        div[data-testid*="VirtualDropdown"] *,
        div[data-testid="stPopoverBody"] * {
            color: #f1f5f9 !important;
            background-color: transparent !important;
        }

        /* Menu / Listbox Items */
        li[data-baseweb="menu-item"],
        li[role="option"],
        div[role="option"],
        div[data-baseweb="option"] {
            background-color: #141c2e !important;
            color: #f1f5f9 !important;
            padding: 8px 14px !important;
            cursor: pointer !important;
            border-bottom: 1px solid rgba(30, 45, 69, 0.5) !important;
        }

        li[data-baseweb="menu-item"]:hover,
        li[role="option"]:hover,
        div[role="option"]:hover,
        div[data-baseweb="option"]:hover,
        li[data-baseweb="menu-item"][aria-selected="true"],
        li[role="option"][aria-selected="true"],
        div[role="option"][aria-selected="true"] {
            background-color: #1e293b !important;
            color: #38bdf8 !important;
        }

        li[data-baseweb="menu-item"]:hover *,
        li[role="option"]:hover *,
        div[role="option"]:hover *,
        div[data-baseweb="option"]:hover *,
        li[data-baseweb="menu-item"][aria-selected="true"] *,
        li[role="option"][aria-selected="true"] * {
            color: #38bdf8 !important;
        }

        /* ── Disabled Buttons & Popover Buttons ── */
        .stButton > button:disabled,
        div[data-testid="stButton"] button:disabled,
        button:disabled {
            background-color: #111827 !important;
            color: #475569 !important;
            border: 1px solid #1e293b !important;
            cursor: not-allowed !important;
            opacity: 0.65 !important;
            box-shadow: none !important;
        }

        .stButton > button:disabled *,
        div[data-testid="stButton"] button:disabled *,
        button:disabled * {
            color: #475569 !important;
            fill: #475569 !important;
        }

        div[data-testid="stPopover"] button {
            background-color: #182234 !important;
            color: #f8fafc !important;
            border: 1px solid #334155 !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
        }

        div[data-testid="stPopover"] button * {
            color: #f8fafc !important;
            fill: #f8fafc !important;
            font-weight: 600 !important;
        }

        div[data-testid="stPopover"] button:hover {
            background-color: #243048 !important;
            border-color: #38bdf8 !important;
            color: #38bdf8 !important;
        }

        div[data-testid="stPopover"] button:hover * {
            color: #38bdf8 !important;
            fill: #38bdf8 !important;
        }

        /* ── Expanders, Accordions & Summaries in Dark Mode ──────── */
        div[data-testid="stExpander"],
        div[data-testid="stExpander"] details,
        details[data-testid="stExpander"] {
            background-color: #141c2e !important;
            border: 1px solid #1e2d45 !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25) !important;
            overflow: hidden !important;
        }

        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] details > summary,
        details[data-testid="stExpander"] > summary,
        [data-testid="stExpander"] summary {
            background-color: #141c2e !important;
            color: #f1f5f9 !important;
            border: none !important;
            border-bottom: 1px solid #1e2d45 !important;
            padding: 11px 16px !important;
            cursor: pointer !important;
        }

        div[data-testid="stExpander"] summary:hover,
        div[data-testid="stExpander"] details > summary:hover,
        details[data-testid="stExpander"] > summary:hover {
            background-color: #182234 !important;
            color: #38bdf8 !important;
        }

        div[data-testid="stExpander"] summary *,
        div[data-testid="stExpander"] details > summary *,
        details[data-testid="stExpander"] > summary * {
            color: #f1f5f9 !important;
            font-weight: 600 !important;
            font-size: 14px !important;
        }

        div[data-testid="stExpander"] summary:hover *,
        div[data-testid="stExpander"] details > summary:hover *,
        details[data-testid="stExpander"] > summary:hover * {
            color: #38bdf8 !important;
        }

        div[data-testid="stExpander"] summary svg,
        div[data-testid="stExpander"] [data-testid="stExpanderToggleIcon"] {
            color: #94a3b8 !important;
            fill: #94a3b8 !important;
        }

        div[data-testid="stExpanderDetails"],
        div[data-testid="stExpander"] details > div,
        div[data-testid="stExpander"] details > div:last-child {
            background-color: #141c2e !important;
            color: #f1f5f9 !important;
            padding: 14px 16px !important;
        }

        /* ── Headings and Markdown in Dark Mode ─────────────────────── */
        h1, h2, h3, h4, h5, h6,
        div[data-testid="stHeadingWithActionElements"] h1,
        div[data-testid="stHeadingWithActionElements"] h2,
        div[data-testid="stHeadingWithActionElements"] h3,
        div[data-testid="stHeadingWithActionElements"] *,
        div[data-testid="stMarkdownContainer"] h1,
        div[data-testid="stMarkdownContainer"] h2,
        div[data-testid="stMarkdownContainer"] h3,
        div[data-testid="stMarkdownContainer"] h4 {
            color: #f1f5f9 !important;
        }

        div[data-testid="stCaptionContainer"],
        div[data-testid="stCaptionContainer"] * {
            color: #94a3b8 !important;
        }

        /* ── Radio & Checkbox Labels in Dark Mode ──────────────────── */
        div[data-testid="stRadio"] label,
        div[data-testid="stCheckbox"] label,
        div[data-testid="stToggle"] label {
            color: #cbd5e1 !important;
        }

        div[data-testid="stRadio"] label *,
        div[data-testid="stCheckbox"] label *,
        div[data-testid="stToggle"] label * {
            color: #cbd5e1 !important;
        }

        /* ── All Cards and Containers in Dark Mode ──────────────────── */
        .stitch-bento-box,
        .stitch-health-card,
        .stitch-sidebar-card,
        .stitch-active-card,
        .stitch-upload-card,
        .ds-metric-card,
        .ds-action-card,
        .ds-insight-card,
        .ds-wf-card,
        .ds-ai-answer-card,
        .ds-ai-suggested-card,
        .pbi-chart-card,
        .ds-context-bar {
            background-color: #141c2e !important;
            border-color: #1e2d45 !important;
            color: #f1f5f9 !important;
        }

        .stitch-health-title,
        .stitch-bento-val,
        .stitch-sidebar-title,
        .stitch-col-name,
        .stitch-dataset-name,
        .ds-context-bar-name {
            color: #f1f5f9 !important;
        }

        .stitch-health-desc,
        .stitch-bento-label,
        .stitch-bento-sub,
        .stitch-dataset-meta,
        .ds-context-bar-meta {
            color: #94a3b8 !important;
        }

        .stitch-pill {
            background-color: #1e293b !important;
            color: #94a3b8 !important;
            border-color: #334155 !important;
        }
        """
    else:
        theme_block = """
        /* ══════════════════════════════════════════════════════════════════════
           LIGHT THEME EXPLICIT REINFORCEMENTS
           ══════════════════════════════════════════════════════════════════════ */
        .stApp, .main, body, section[data-testid="stMain"],
        div[data-testid="stAppViewContainer"],
        div[data-testid="stAppViewBlockContainer"],
        div[data-testid="stMainBlockContainer"] {
            background-color: #f4f7fb !important;
            color: #0f172a !important;
        }

        /* Secondary buttons in Light Mode */
        .stButton > button,
        div[data-testid="stButton"] button,
        button[data-testid="stBaseButton-secondary"],
        button[data-testid="baseButton-secondary"],
        button[data-testid="stBaseButton-minimal"],
        button[data-testid="stBaseButton-tertiary"],
        button[data-testid="stBaseButton-header"],
        button[data-testid="stBaseButton-icon"],
        .stButton > button[kind="secondary"],
        .stButton > button:not([kind="primary"]),
        div[data-testid="stDownloadButton"] button,
        div[data-testid="stFormSubmitButton"] button:not([kind="primary"]),
        div[data-testid="stFileUploader"] section button,
        div[data-testid="stFileUploader"] button,
        div[data-testid="stPills"] button:not([aria-selected="true"]),
        div[data-testid="stSegmentedControl"] button:not([aria-selected="true"]),
        div[data-testid="stPopover"] button,
        div[data-testid="stButtonGroup"] button,
        button[kind="secondary"],
        button[kind="secondaryFormSubmit"],
        div[data-testid="stLinkButton"] a {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05) !important;
        }

        .stButton > button *,
        div[data-testid="stButton"] button *,
        button[data-testid="stBaseButton-secondary"] *,
        button[data-testid="baseButton-secondary"] *,
        button[data-testid="stBaseButton-minimal"] *,
        button[data-testid="stBaseButton-tertiary"] *,
        button[data-testid="stBaseButton-header"] *,
        button[data-testid="stBaseButton-icon"] *,
        .stButton > button[kind="secondary"] *,
        .stButton > button:not([kind="primary"]) *,
        div[data-testid="stDownloadButton"] button *,
        div[data-testid="stFormSubmitButton"] button:not([kind="primary"]) *,
        div[data-testid="stFileUploader"] section button *,
        div[data-testid="stFileUploader"] button *,
        div[data-testid="stPills"] button:not([aria-selected="true"]) *,
        div[data-testid="stSegmentedControl"] button:not([aria-selected="true"]) *,
        div[data-testid="stPopover"] button *,
        div[data-testid="stButtonGroup"] button *,
        button[kind="secondary"] *,
        button[kind="secondaryFormSubmit"] *,
        div[data-testid="stLinkButton"] a * {
            color: #0f172a !important;
            fill: #0f172a !important;
            font-weight: 600 !important;
        }

        .stButton > button:hover,
        div[data-testid="stButton"] button:hover,
        button[data-testid="stBaseButton-secondary"]:hover,
        button[data-testid="baseButton-secondary"]:hover,
        .stButton > button:not([kind="primary"]):hover,
        div[data-testid="stDownloadButton"] button:hover,
        div[data-testid="stFormSubmitButton"] button:not([kind="primary"]):hover {
            background-color: #f1f5f9 !important;
            border-color: #2563eb !important;
            color: #2563eb !important;
        }

        .stButton > button:hover *,
        div[data-testid="stButton"] button:hover *,
        button[data-testid="stBaseButton-secondary"]:hover *,
        button[data-testid="baseButton-secondary"]:hover *,
        .stButton > button:not([kind="primary"]):hover * {
            color: #2563eb !important;
            fill: #2563eb !important;
        }

        /* Primary buttons in Light Mode */
        .stButton > button[kind="primary"],
        div[data-testid="stButton"] button[kind="primary"],
        button[data-testid="stBaseButton-primary"],
        button[data-testid="baseButton-primary"],
        button[kind="primary"],
        button[kind="primaryFormSubmit"] {
            background-color: #2563eb !important;
            border: 1px solid #1d4ed8 !important;
            color: #ffffff !important;
        }

        .stButton > button[kind="primary"] *,
        div[data-testid="stButton"] button[kind="primary"] *,
        button[data-testid="stBaseButton-primary"] *,
        button[data-testid="baseButton-primary"] *,
        button[kind="primary"] * {
            color: #ffffff !important;
            fill: #ffffff !important;
            font-weight: 600 !important;
        }

        /* Tables & DataFrames in Light Mode */
        div[data-testid="stDataFrame"],
        div[data-testid="stTable"],
        .stitch-table-container {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 8px !important;
        }

        .stitch-table th,
        div[data-testid="stTable"] th {
            background-color: #f8fafc !important;
            color: #0f172a !important;
            border-bottom: 1px solid #cbd5e1 !important;
        }

        .stitch-table td,
        div[data-testid="stTable"] td {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border-bottom: 1px solid #e2e8f0 !important;
        }

        /* Expanders in Light Mode */
        div[data-testid="stExpander"],
        div[data-testid="stExpander"] details,
        details[data-testid="stExpander"] {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 8px !important;
        }

        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] details > summary,
        details[data-testid="stExpander"] > summary {
            background-color: #f8fafc !important;
            color: #0f172a !important;
            border-bottom: 1px solid #cbd5e1 !important;
        }

        div[data-testid="stExpander"] summary *,
        div[data-testid="stExpander"] details > summary *,
        details[data-testid="stExpander"] > summary * {
            color: #0f172a !important;
            font-weight: 600 !important;
        }

        div[data-testid="stExpander"] summary:hover,
        div[data-testid="stExpander"] details > summary:hover {
            background-color: #f1f5f9 !important;
            color: #2563eb !important;
        }

        .stitch-table tr:nth-child(even) td {
            background-color: #f8fafc !important;
        }

        /* ── Inputs, Selectboxes, Dropdowns & Popovers in Light Mode ── */
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
        div[data-baseweb="select"] > div,
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stDateInput"] input,
        div[data-testid="stTimeInput"] input {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
        }

        span[data-baseweb="tag"],
        div[data-testid="stMultiSelect"] span[data-baseweb="tag"],
        div[data-baseweb="tag"] {
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 4px !important;
        }

        span[data-baseweb="tag"] * {
            color: #0f172a !important;
        }

        div[data-baseweb="popover"],
        div[data-baseweb="popover"] > div,
        div[data-baseweb="popover"] ul,
        div[data-baseweb="popover"] div,
        div[data-baseweb="menu"],
        div[data-baseweb="menu"] > ul,
        ul[data-baseweb="menu"],
        ul[role="listbox"],
        div[role="listbox"],
        div[data-testid*="VirtualDropdown"],
        div[data-testid*="virtualDropdown"],
        div[data-testid="stSelectboxVirtualDropdown"],
        div[data-testid="stMultiSelectVirtualDropdown"],
        div[data-testid="stPopoverBody"] {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 10px 25px rgba(15, 23, 42, 0.12) !important;
        }

        div[data-baseweb="popover"] *,
        div[data-baseweb="menu"] *,
        ul[role="listbox"] *,
        div[data-testid*="VirtualDropdown"] *,
        div[data-testid="stPopoverBody"] * {
            color: #0f172a !important;
            background-color: transparent !important;
        }

        li[data-baseweb="menu-item"],
        li[role="option"],
        div[role="option"],
        div[data-baseweb="option"] {
            background-color: #ffffff !important;
            color: #0f172a !important;
            padding: 8px 14px !important;
            cursor: pointer !important;
            border-bottom: 1px solid #f1f5f9 !important;
        }

        li[data-baseweb="menu-item"]:hover,
        li[role="option"]:hover,
        div[role="option"]:hover,
        div[data-baseweb="option"]:hover,
        li[data-baseweb="menu-item"][aria-selected="true"],
        li[role="option"][aria-selected="true"],
        div[role="option"][aria-selected="true"] {
            background-color: #f1f5f9 !important;
            color: #2563eb !important;
        }

        li[data-baseweb="menu-item"]:hover *,
        li[role="option"]:hover *,
        div[role="option"]:hover *,
        div[data-baseweb="option"]:hover *,
        li[data-baseweb="menu-item"][aria-selected="true"] *,
        li[role="option"][aria-selected="true"] * {
            color: #2563eb !important;
        }
        """

    full_css = f"<style>\n{css_content}\n{theme_block}\n</style>"
    st.markdown(full_css, unsafe_allow_html=True)


# ============================================================================
# COMPACT TOP HEADER COMPONENT (56-64px SaaS Context & Action Bar)
# ============================================================================

def render_top_header(
    page_title: str,
    page_icon: Optional[str] = None,
    dataset_name: Optional[str] = None,
    df: Optional[Any] = None,
    user: Optional[Dict[str, Any]] = None,
    is_admin: bool = False
) -> None:
    """
    Render the compact 56–64px Top Header for dataset context and global actions.
    """
    import html as html_lib

    # Left: Page title & icon
    icon_svg = get_icon_svg(page_icon or "layout-dashboard", 16)

    # Center: Dataset context
    if df is not None:
        rows, cols = df.shape
        ds_display_name = html_lib.escape(dataset_name or "Active Dataset")
        context_html = (
            f'<div class="ds-top-header-context ds-context-loaded">'
            f'<span class="ds-status-dot">●</span>'
            f'<span class="ds-context-name">{ds_display_name}</span>'
            f'<span class="ds-context-divider">·</span>'
            f'<span class="ds-context-stats">{rows:,} rows &times; {cols} cols</span>'
            f'</div>'
        )
    else:
        context_html = (
            f'<div class="ds-top-header-context ds-context-empty">'
            f'<span class="ds-context-empty-icon">{get_icon_svg("database", 12)}</span>'
            f'<span class="ds-context-muted">No dataset loaded</span>'
            f'</div>'
        )

    # Right: User & Role
    user_info = user or {}
    user_name = html_lib.escape(user_info.get("full_name", "User"))
    is_guest = user_info.get("is_guest", False)

    if is_admin:
        role_label = "ADMIN"
        role_class = "ds-role-admin"
    elif is_guest:
        role_label = "GUEST"
        role_class = "ds-role-guest"
    else:
        role_label = "MEMBER"
        role_class = "ds-role-member"

    html = (
        f'<header class="ds-top-header">'
        f'<div class="ds-top-header-left">'
        f'<div class="ds-top-header-title-wrap">'
        f'<span class="ds-top-header-icon">{icon_svg}</span>'
        f'<span class="ds-top-header-title">{html_lib.escape(page_title)}</span>'
        f'</div>'
        f'</div>'
        f'<div class="ds-top-header-center">'
        f'{context_html}'
        f'</div>'
        f'<div class="ds-top-header-right">'
        f'<div class="ds-top-header-user">'
        f'<span class="ds-user-name">{user_name}</span>'
        f'<span class="ds-role-badge {role_class}">{role_label}</span>'
        f'</div>'
        f'</div>'
        f'</header>'
    )
    st.markdown(html, unsafe_allow_html=True)


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
# WORKFLOW TIMELINE COMPONENT
# ============================================================================

def render_workflow_timeline(interactive: bool = True) -> None:
    """
    Render a professional analytics progress timeline with 6 workflow steps:
    1. Upload Dataset -> 2. Check Quality -> 3. Prepare Data -> 4. Analyze Data -> 5. Visualize Data -> 6. Build Dashboard
    Three professional states:
      - Completed: subtle checkmark (✓)
      - Current: application accent color
      - Upcoming: neutral styling
    """
    from modules.config import WORKFLOW_STEPS, is_workflow_step_completed, is_dataset_loaded, get_current_workflow_stage
    
    current_page = st.session_state.get("current_page", "Overview")
    stage_info = get_current_workflow_stage()
    current_step_num = stage_info["current_step_num"]

    steps_html = []
    for step in WORKFLOW_STEPS:
        s_num = step["step_num"]
        s_key = step["key"]
        s_name = step["name"]
        s_short = step.get("short_name", s_name)
        s_page = step["page"]
        
        is_comp = is_workflow_step_completed(s_key)
        is_curr = (s_num == current_step_num) and is_dataset_loaded()
        is_page_active = (current_page == s_page)
        
        if is_comp:
            state_class = "ds-timeline-step-completed"
            icon_badge = '<span class="ds-timeline-badge ds-badge-completed">✓</span>'
            status_text = "Completed"
        elif is_curr or (s_num == 1 and not is_dataset_loaded()):
            state_class = "ds-timeline-step-current"
            icon_badge = f'<span class="ds-timeline-badge ds-badge-current">{s_num}</span>'
            status_text = "Current Step"
        else:
            state_class = "ds-timeline-step-upcoming"
            icon_badge = f'<span class="ds-timeline-badge ds-badge-upcoming">{s_num}</span>'
            status_text = "Upcoming"

        step_card = (
            f'<div class="ds-timeline-step {state_class}">'
            f'<div class="ds-timeline-step-header">'
            f'{icon_badge}'
            f'<span class="ds-timeline-step-num">STEP 0{s_num}</span>'
            f'</div>'
            f'<div class="ds-timeline-step-title">{s_name}</div>'
            f'<div class="ds-timeline-step-status">{status_text}</div>'
            f'</div>'
        )
        steps_html.append(step_card)

    timeline_container_html = (
        f'<div class="ds-timeline-wrapper">'
        f'<div class="ds-timeline-track"></div>'
        f'<div class="ds-timeline-steps">{"".join(steps_html)}</div>'
        f'</div>'
    )
    st.markdown(timeline_container_html, unsafe_allow_html=True)

    # 1-Click interactive navigation buttons below timeline if requested
    if interactive:
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        nav_cols = st.columns(len(WORKFLOW_STEPS))
        for idx, step in enumerate(WORKFLOW_STEPS):
            with nav_cols[idx]:
                s_key = step["key"]
                s_page = step["page"]
                s_name = step["short_name"]
                is_comp = is_workflow_step_completed(s_key)
                is_curr = (step["step_num"] == current_step_num)
                btn_label = f"✓ {s_name}" if is_comp else (f"● {s_name}" if is_curr else s_name)
                
                if st.button(
                    btn_label,
                    key=f"tl_btn_{s_key}",
                    use_container_width=True,
                    type="primary" if is_curr else "secondary"
                ):
                    st.session_state["current_page"] = s_page
                    st.rerun()


# ============================================================================
# INTELLIGENT NEXT-STEP GUIDANCE BANNER
# ============================================================================

def render_next_step_banner(
    title: str,
    recommendation: str,
    primary_action_label: str,
    target_page: str,
    key_prefix: str = "next_step",
    suggested_actions: Optional[List[Dict[str, str]]] = None
) -> None:
    """
    Render a high-visibility, professional next-step guidance callout card.
    Dynamically guides the user from their current completed task to the next logical workflow phase.
    """
    banner_icon = get_icon_svg("arrow-right", 18)
    banner_html = (
        f'<div class="ds-next-step-banner">'
        f'<div class="ds-next-step-content">'
        f'<div class="ds-next-step-header">'
        f'<span class="ds-next-step-badge">RECOMMENDED NEXT STEP</span>'
        f'</div>'
        f'<div class="ds-next-step-title">{title}</div>'
        f'<div class="ds-next-step-desc">{recommendation}</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(banner_html, unsafe_allow_html=True)

    # Action buttons
    if suggested_actions:
        btn_cols = st.columns(len(suggested_actions) + 1)
        with btn_cols[0]:
            if st.button(
                primary_action_label,
                key=f"{key_prefix}_primary_btn",
                type="primary",
                use_container_width=True
            ):
                st.session_state["current_page"] = target_page
                st.rerun()
        for i, act in enumerate(suggested_actions):
            with btn_cols[i + 1]:
                if st.button(
                    act.get("label", "Action"),
                    key=f"{key_prefix}_extra_{i}",
                    use_container_width=True
                ):
                    st.session_state["current_page"] = act.get("page", "Overview")
                    st.rerun()
    else:
        c1, c2 = st.columns([7, 5])
        with c2:
            if st.button(
                primary_action_label,
                key=f"{key_prefix}_primary_btn",
                type="primary",
                use_container_width=True
            ):
                st.session_state["current_page"] = target_page
                st.rerun()


# ============================================================================
# CONTEXTUAL AI TRIGGER
# ============================================================================

def render_ai_context_trigger(
    label: str = "Ask AI about this data",
    intent: str = "general",
    key: str = "ai_trigger"
) -> None:
    """
    Render a clean, contextual AI Analyst trigger button without interrupting the workflow.
    """
    ai_icon = get_icon_svg("sparkles", 14)
    if st.button(
        f"✦ {label}",
        key=key,
        use_container_width=False,
        help="Consult AI Analyst for natural language queries and automated observations."
    ):
        st.session_state["ai_analyst_intent"] = intent
        st.session_state["current_page"] = "AI Analyst"
        st.rerun()


# ============================================================================
# STANDARDIZED DYNAMIC BOTTOM WORKFLOW STEPS COMPONENT
# ============================================================================

ANALYTICAL_WORKFLOW_STEPS = [
    {
        "page_key": "Overview",
        "name": "Overview",
        "description": "Executive dashboard and data health summary.",
        "icon": "layout-dashboard"
    },
    {
        "page_key": "Dataset",
        "name": "Dataset",
        "description": "Upload, inspect, and manage dataset schema.",
        "icon": "database"
    },
    {
        "page_key": "Data Quality",
        "name": "Data Quality",
        "description": "Review missing values, duplicates, and data health metrics.",
        "icon": "shield-check"
    },
    {
        "page_key": "Data Preparation",
        "name": "Data Preparation",
        "description": "Clean, transform, filter, and prepare your dataset.",
        "icon": "wrench"
    },
    {
        "page_key": "EDA",
        "name": "Analyze",
        "description": "Explore statistical distributions, correlations, and patterns.",
        "icon": "search"
    },
    {
        "page_key": "Visualization",
        "name": "Visualization",
        "description": "Create charts, visual rankings, and interactive graphics.",
        "icon": "bar-chart-3"
    },
    {
        "page_key": "Dashboard",
        "name": "Dashboard",
        "description": "Combine key insights and charts into an executive dashboard.",
        "icon": "layout-dashboard"
    },
    {
        "page_key": "AI Analyst",
        "name": "AI Analyst",
        "description": "Ask questions, investigate anomalies, and generate AI insights.",
        "icon": "sparkles"
    },
    {
        "page_key": "Settings",
        "name": "Settings",
        "description": "Configure preferences, appearance, and manage workspace state.",
        "icon": "settings"
    }
]


def render_next_workflow_steps(current_page: Optional[str] = None) -> None:
    """
    Render the standardized bottom 'Next Workflow Steps' section across all modules.
    Guarantees a consistent structure across every single page:
      - Button 1: Previous Module (if any)
      - Button 2: Immediate Next Module (Recommended, primary visual emphasis)
      - Button 3: Subsequent Next Module (if any)
    """
    if not current_page:
        current_page = st.session_state.get("current_page", "Overview")

    # Handle Admin Analytics special route
    if current_page == "Admin Analytics":
        cards = [
            {
                "step": ANALYTICAL_WORKFLOW_STEPS[0],  # Overview
                "role_badge": "PRIMARY WORKSPACE",
                "btn_label": "← Return to Overview",
                "is_recommended": True,
                "btn_type": "primary"
            },
            {
                "step": ANALYTICAL_WORKFLOW_STEPS[-1],  # Settings
                "role_badge": "SYSTEM PREFERENCES",
                "btn_label": "Go to Settings →",
                "is_recommended": False,
                "btn_type": "secondary"
            }
        ]
    else:
        # Resolve index in analytical workflow
        curr_idx = -1
        for idx, step in enumerate(ANALYTICAL_WORKFLOW_STEPS):
            if current_page == step["page_key"] or current_page.lower() == step["name"].lower():
                curr_idx = idx
                break

        if curr_idx == -1:
            return

        # Compute up to 3 buttons dynamically
        cards = []

        # 1. Previous Module (if exists)
        if curr_idx > 0:
            cards.append({
                "step": ANALYTICAL_WORKFLOW_STEPS[curr_idx - 1],
                "role_badge": "PREVIOUS STEP",
                "btn_label": f"← Return to {ANALYTICAL_WORKFLOW_STEPS[curr_idx - 1]['name']}",
                "is_recommended": False,
                "btn_type": "secondary"
            })

        # 2. Immediate Next Module (if exists - Recommended with primary emphasis)
        if curr_idx < len(ANALYTICAL_WORKFLOW_STEPS) - 1:
            cards.append({
                "step": ANALYTICAL_WORKFLOW_STEPS[curr_idx + 1],
                "role_badge": "RECOMMENDED NEXT",
                "btn_label": f"Continue to {ANALYTICAL_WORKFLOW_STEPS[curr_idx + 1]['name']} →",
                "is_recommended": True,
                "btn_type": "primary"
            })

        # 3. Second Next Module (if exists)
        if curr_idx < len(ANALYTICAL_WORKFLOW_STEPS) - 2:
            cards.append({
                "step": ANALYTICAL_WORKFLOW_STEPS[curr_idx + 2],
                "role_badge": "SUBSEQUENT STEP",
                "btn_label": f"Jump to {ANALYTICAL_WORKFLOW_STEPS[curr_idx + 2]['name']} →",
                "is_recommended": False,
                "btn_type": "secondary"
            })
        elif curr_idx == len(ANALYTICAL_WORKFLOW_STEPS) - 1 and len(ANALYTICAL_WORKFLOW_STEPS) > 2:
            # On last step (Settings), offer quick return to Overview
            cards.append({
                "step": ANALYTICAL_WORKFLOW_STEPS[0],
                "role_badge": "RETURN HOME",
                "btn_label": "Restart from Overview →",
                "is_recommended": True,
                "btn_type": "primary"
            })

    if not cards:
        return

    st.markdown("<div class='ds-wf-steps-container'>", unsafe_allow_html=True)

    render_section_header(
        title="Next Workflow Steps",
        subtitle="Continue your analytical journey through subsequent modules or review previous steps."
    )

    cols = st.columns(len(cards), gap="medium")

    for i, item in enumerate(cards):
        step_data = item["step"]
        is_rec = item["is_recommended"]
        role_badge = item["role_badge"]
        btn_label = item["btn_label"]
        btn_type = item["btn_type"]

        card_class = "ds-wf-card ds-wf-card-recommended" if is_rec else "ds-wf-card"
        badge_class = "ds-wf-badge ds-wf-badge-recommended" if is_rec else "ds-wf-badge"
        icon_svg = get_icon_svg(step_data["icon"], 16)

        with cols[i]:
            card_html = (
                f'<div class="{card_class}">'
                f'<div>'
                f'<span class="{badge_class}">{role_badge}</span>'
                f'<div class="ds-wf-card-title">{icon_svg} {step_data["name"]}</div>'
                f'<div class="ds-wf-card-desc">{step_data["description"]}</div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

            target_page_key = step_data["page_key"]
            if st.button(
                btn_label,
                key=f"wf_nav_{current_page.replace(' ', '_')}_{target_page_key}_{i}",
                type=btn_type,
                use_container_width=True
            ):
                st.session_state["current_page"] = target_page_key
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)



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

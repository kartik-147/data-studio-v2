"""
DATA STUDIO v2 — Configuration and Session State Architecture
"""
from typing import Dict, List, Any
import streamlit as st

# Application Branding
APP_NAME = "Data Studio"
APP_SUBTITLE = "Data Analytics Platform"
APP_VERSION = "v2.0"

# Icon mapping for navigation items
NAV_PAGE_ICONS: Dict[str, str] = {
    "Overview": "home",
    "Dashboard": "layout-dashboard",
    "Dataset": "database",
    "Data Quality": "shield-check",
    "Data Preparation": "wrench",
    "EDA": "search",
    "Visualization": "bar-chart-3",
    "AI Analyst": "sparkles",
    "Settings": "settings",
    "Admin Analytics": "layers",
    "Activity": "activity",
}

# Canonical Navigation Groups and Pages
NAV_GROUPS: Dict[str, List[str]] = {
    "WORKSPACE": [
        "Overview",
    ],
    "DATA PIPELINE": [
        "Dataset",
        "Data Preparation",
        "EDA",
    ],
    "ANALYTICS": [
        "Visualization",
        "Dashboard",
        "Data Quality",
    ],
    "INTELLIGENCE": [
        "AI Analyst",
    ],
    "SYSTEM": [
        "Settings"
    ]
}

ALL_PAGES: List[str] = [
    page for group in NAV_GROUPS.values() for page in group
]

PAGE_METADATA: Dict[str, Dict[str, str]] = {
    "Overview": {
        "title": "Overview",
        "subtitle": "Workspace home, onboarding, and platform summary.",
        "icon": "home",
        "group": "WORKSPACE"
    },
    "Dashboard": {
        "title": "Dashboard",
        "subtitle": "Automatically generated insights and KPIs from your active dataset.",
        "icon": "layout-dashboard",
        "group": "ANALYTICS"
    },
    "Dataset": {
        "title": "Dataset",
        "subtitle": "Upload, inspect, and profile your data before analysis.",
        "icon": "database",
        "group": "DATA PIPELINE"
    },
    "Data Quality": {
        "title": "Data Quality",
        "subtitle": "Understand the health, completeness, and reliability of your dataset.",
        "icon": "shield-check",
        "group": "ANALYTICS"
    },
    "Data Preparation": {
        "title": "Data Preparation",
        "subtitle": "Interactive cleaning, type conversions, missing value handling, and export.",
        "icon": "wrench",
        "group": "DATA PIPELINE"
    },
    "EDA": {
        "title": "Exploratory Data Analysis",
        "subtitle": "Descriptive statistics, skewness, kurtosis, correlation matrices, and outlier detection.",
        "icon": "search",
        "group": "DATA PIPELINE"
    },
    "Visualization": {
        "title": "Visualization Studio",
        "subtitle": "Interactive multi-dimensional chart builder with smart visual recommendations.",
        "icon": "bar-chart-3",
        "group": "ANALYTICS"
    },
    "AI Analyst": {
        "title": "AI Analyst",
        "subtitle": "Natural language data exploration, automated insights, and question answering.",
        "icon": "sparkles",
        "group": "INTELLIGENCE"
    },
    "Settings": {
        "title": "Settings",
        "subtitle": "Workspace configuration, appearance preferences, and session management.",
        "icon": "settings",
        "group": "SYSTEM"
    }
}

def init_session_state() -> None:
    """Initialize default session state keys for the application foundation."""
    defaults: Dict[str, Any] = {
        "current_page": "Overview",
        "theme": "Light",           # Light is the new default
        "sidebar_collapsed": False,  # Sidebar state
        # Authentication State
        "authenticated": False,
        "auth_provider": None,
        "user_info": None,
        "is_guest": False,
        # Centralized Dataset State Architecture
        "dataset": None,
        "original_dataset": None,
        "cleaned_dataset": None,
        "dataset_name": None,
        "dataset_metadata": None,
        "dataset_file_type": None,
        # Activity log
        "activity_log": [],
    }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def is_dataset_loaded() -> bool:
    """Check if an active dataset is loaded in memory."""
    return st.session_state.get("dataset") is not None

def log_activity(event: str, icon: str = "activity") -> None:
    """Append an activity event to the session activity log."""
    import datetime
    log: list = st.session_state.get("activity_log", [])
    log.append({
        "event": event,
        "icon": icon,
        "timestamp": datetime.datetime.now().strftime("%I:%M %p"),
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
    })
    # Keep last 20 events only
    st.session_state["activity_log"] = log[-20:]

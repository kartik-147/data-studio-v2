"""
DATA STUDIO v2 — Configuration and Session State Architecture
"""
from typing import Dict, List, Any
import streamlit as st

# Application Branding
APP_NAME = "Data Studio"
APP_SUBTITLE = "Data Analytics Platform"
APP_VERSION = "v2.0"

# Canonical Navigation Groups and Pages
NAV_GROUPS: Dict[str, List[str]] = {
    "ANALYZE": [
        "Overview",
        "Dashboard",
        "Dataset"
    ],
    "EXPLORE": [
        "Data Quality",
        "Data Preparation",
        "EDA",
        "Visualization"
    ],
    "INTELLIGENCE": [
        "AI Analyst"
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
        "subtitle": "Workspace onboarding, data workflow, and system summary.",
        "icon": "home",
        "group": "ANALYZE"
    },
    "Dashboard": {
        "title": "Dashboard",
        "subtitle": "Automatically generated insights from your active dataset.",
        "icon": "layout-dashboard",
        "group": "ANALYZE"
    },
    "Dataset": {
        "title": "Dataset",
        "subtitle": "Upload and inspect your data before starting the analysis.",
        "icon": "database",
        "group": "ANALYZE"
    },
    "Data Quality": {
        "title": "Data Quality",
        "subtitle": "Understand the health, completeness, and reliability of your dataset.",
        "icon": "shield-check",
        "group": "EXPLORE"
    },
    "Data Preparation": {
        "title": "Data Preparation",
        "subtitle": "Interactive cleaning, type conversions, missing value handling, and data export.",
        "icon": "wrench",
        "group": "EXPLORE"
    },
    "EDA": {
        "title": "Exploratory Data Analysis",
        "subtitle": "Descriptive statistics, skewness, kurtosis, correlation matrices, and outlier detection.",
        "icon": "search",
        "group": "EXPLORE"
    },
    "Visualization": {
        "title": "Visualization Builder",
        "subtitle": "Interactive multi-dimensional chart builder with smart visual recommendations.",
        "icon": "bar-chart-3",
        "group": "EXPLORE"
    },
    "AI Analyst": {
        "title": "AI Analyst Assistant",
        "subtitle": "Natural language data exploration, automated insights, and question answering.",
        "icon": "sparkles",
        "group": "INTELLIGENCE"
    },
    "Settings": {
        "title": "Settings & Preferences",
        "subtitle": "Workspace configuration, appearance preferences, and session management.",
        "icon": "settings",
        "group": "SYSTEM"
    }
}

def init_session_state() -> None:
    """Initialize default session state keys for the application foundation."""
    defaults: Dict[str, Any] = {
        "current_page": "Overview",
        "theme": "Dark",
        # Authentication State (Module 5)
        "authenticated": False,
        "auth_provider": None,
        "user_info": None,
        "is_guest": False,
        # Centralized Dataset State Architecture (Module 2)
        "dataset": None,
        "original_dataset": None,
        "cleaned_dataset": None,
        "dataset_name": None,
        "dataset_metadata": None,
        "dataset_file_type": None
    }
    
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def is_dataset_loaded() -> bool:
    """Check if an active dataset is loaded in memory."""
    return st.session_state.get("dataset") is not None

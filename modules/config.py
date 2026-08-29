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
    "Dataset": "database",
    "Overview": "layout-dashboard",
    "Data Preparation": "wrench",
    "Data Quality": "shield-check",
    "Analyze": "activity",
    "EDA": "activity",
    "Visualization": "bar-chart-3",
    "Dashboard": "panels-top-left",
    "AI Analyst": "sparkles",
    "Data Story": "book-open",
    "Settings": "settings",
    "Admin Analytics": "shield",
    "Activity": "activity",
}

# Canonical Navigation Groups and Pages (Organized by Professional Hierarchy)
NAV_GROUPS: Dict[str, List[str]] = {
    "WORKSPACE": [
        "Dataset",
        "Overview",
        "Data Preparation",
        "Data Quality",
        "Analyze",
        "Visualization",
        "Dashboard",
    ],
    "INTELLIGENCE": [
        "AI Analyst",
        "Data Story",
    ],
    "SYSTEM": [
        "Settings",
    ],
    "ADMINISTRATION": [
        "Admin Analytics"
    ]
}

FUNCTIONAL_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "WORKSPACE": {
        "title": "Analytical Workspace",
        "description": "Dataset management, data preparation, quality audit, exploratory analysis, visualization, and dashboards.",
        "icon": "database",
        "badge": "WORKSPACE",
        "pages": ["Dataset", "Overview", "Data Preparation", "Data Quality", "Analyze", "Visualization", "Dashboard"]
    },
    "INTELLIGENCE": {
        "title": "Intelligence & Insights",
        "description": "Conversational AI Analyst and multi-chapter executive data storytelling.",
        "icon": "sparkles",
        "badge": "INTELLIGENCE",
        "pages": ["AI Analyst", "Data Story"]
    },
    "SYSTEM": {
        "title": "System Preferences",
        "description": "Platform settings, theme management, and configurations.",
        "icon": "settings",
        "badge": "SYSTEM",
        "pages": ["Settings"]
    },
    "ADMINISTRATION": {
        "title": "Administration",
        "description": "System telemetry, user audit trails, and platform analytics.",
        "icon": "shield",
        "badge": "ADMIN",
        "pages": ["Admin Analytics"]
    }
}

ALL_PAGES: List[str] = [
    page for group in NAV_GROUPS.values() for page in group
]

PAGE_METADATA: Dict[str, Dict[str, str]] = {
    "Dataset": {
        "title": "Dataset",
        "subtitle": "Ingest, inspect, profile, and manage active datasets.",
        "icon": "database",
        "group": "WORKSPACE",
        "category_badge": "WORKSPACE"
    },
    "Overview": {
        "title": "Overview",
        "subtitle": "Intelligent control center, workspace summary, and workflow progress.",
        "icon": "layout-dashboard",
        "group": "WORKSPACE",
        "category_badge": "WORKSPACE"
    },
    "Data Preparation": {
        "title": "Data Preparation",
        "subtitle": "Interactive cleaning, type conversions, missing value handling, and transformation.",
        "icon": "wrench",
        "group": "WORKSPACE",
        "category_badge": "WORKSPACE"
    },
    "Data Quality": {
        "title": "Data Quality",
        "subtitle": "Assess completeness, consistency, and reliability of your dataset.",
        "icon": "shield-check",
        "group": "WORKSPACE",
        "category_badge": "WORKSPACE"
    },
    "Analyze": {
        "title": "Analyze",
        "subtitle": "Statistical distributions, correlation matrices, skewness, and outlier detection.",
        "icon": "activity",
        "group": "WORKSPACE",
        "category_badge": "WORKSPACE"
    },
    "EDA": {
        "title": "Analyze",
        "subtitle": "Statistical distributions, correlation matrices, skewness, and outlier detection.",
        "icon": "activity",
        "group": "WORKSPACE",
        "category_badge": "WORKSPACE"
    },
    "Visualization": {
        "title": "Visualization",
        "subtitle": "Interactive BI visualization studio with 25+ chart types and vector exports.",
        "icon": "bar-chart-3",
        "group": "WORKSPACE",
        "category_badge": "WORKSPACE"
    },
    "Dashboard": {
        "title": "Dashboard",
        "subtitle": "Interactive executive KPI summaries and multi-metric analytical views.",
        "icon": "panels-top-left",
        "group": "WORKSPACE",
        "category_badge": "WORKSPACE"
    },
    "AI Analyst": {
        "title": "AI Analyst",
        "subtitle": "Conversational data exploration, root-cause investigation, and Q&A.",
        "icon": "sparkles",
        "group": "INTELLIGENCE",
        "category_badge": "INTELLIGENCE"
    },
    "Data Story": {
        "title": "Data Story",
        "subtitle": "Transform complex analytics into an automated, executive-ready narrative briefing.",
        "icon": "book-open",
        "group": "INTELLIGENCE",
        "category_badge": "INTELLIGENCE"
    },
    "Settings": {
        "title": "Settings",
        "subtitle": "Application configuration, appearance themes, and performance preferences.",
        "icon": "settings",
        "group": "SYSTEM",
        "category_badge": "SYSTEM"
    },
    "Admin Analytics": {
        "title": "Admin Analytics",
        "subtitle": "Platform telemetry, real-time Firestore activity, and user analytics.",
        "icon": "shield",
        "group": "ADMINISTRATION",
        "category_badge": "ADMIN"
    }
}

# =============================================================================
# WORKFLOW TIMELINE CONSTANTS & PROGRESS TRACKING
# =============================================================================

WORKFLOW_STEPS = [
    {
        "key": "upload",
        "step_num": 1,
        "name": "Upload Dataset",
        "short_name": "Upload",
        "page": "Dataset",
        "desc": "Connect CSV or Excel files with automated schema detection."
    },
    {
        "key": "quality",
        "step_num": 2,
        "name": "Check Quality",
        "short_name": "Quality",
        "page": "Data Quality",
        "desc": "Audit dataset health, missing values, duplicates, and validity."
    },
    {
        "key": "prep",
        "step_num": 3,
        "name": "Prepare Data",
        "short_name": "Prepare",
        "page": "Data Preparation",
        "desc": "Clean missing values, drop duplicates, filter rows, and cast types."
    },
    {
        "key": "analyze",
        "step_num": 4,
        "name": "Analyze Data",
        "short_name": "Analyze",
        "page": "EDA",
        "desc": "Explore summary statistics, distributions, correlations, and outliers."
    },
    {
        "key": "visualize",
        "step_num": 5,
        "name": "Visualize Data",
        "short_name": "Visualize",
        "page": "Visualization",
        "desc": "Create interactive charts and communicate analytical findings."
    },
    {
        "key": "dashboard",
        "step_num": 6,
        "name": "Build Dashboard",
        "short_name": "Dashboard",
        "page": "Dashboard",
        "desc": "Synthesize key metrics, trends, and KPIs into an analytics dashboard."
    }
]


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
        # Workflow progress milestones (tracked by meaningful user actions)
        "workflow_quality_completed": False,
        "workflow_prep_completed": False,
        "workflow_analyze_completed": False,
        "workflow_visualize_completed": False,
        "workflow_dashboard_completed": False,
        # Saved items
        "saved_visualizations": [],
        # Activity log
        "activity_log": [],
        # AI Analyst mode (ask | investigate | story)
        "ai_analyst_mode": "ask",
        # Cross-module deep-link hint: set by Data Quality to pre-select a tool in Data Preparation
        # Values: None | "missing" | "duplicates" | "outliers" | "types"
        "prep_suggested_action": None,
        # Data Story narrative cache (None = not yet generated)
        "ai_story_cache": None,
    }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def is_dataset_loaded() -> bool:
    """Check if an active dataset is loaded in memory."""
    return st.session_state.get("dataset") is not None


def is_workflow_step_completed(step_key: str) -> bool:
    """
    Check if a specific analytical workflow step has been meaningfully completed.
    Never marks a step complete simply by opening a page.
    """
    if step_key == "upload":
        return is_dataset_loaded()
    elif step_key == "quality":
        return is_dataset_loaded() and bool(st.session_state.get("workflow_quality_completed", False))
    elif step_key == "prep":
        return is_dataset_loaded() and (
            st.session_state.get("cleaned_dataset") is not None or
            bool(st.session_state.get("workflow_prep_completed", False)) or
            len(st.session_state.get("prep_history", [])) > 0
        )
    elif step_key == "analyze":
        return is_dataset_loaded() and bool(st.session_state.get("workflow_analyze_completed", False))
    elif step_key == "visualize":
        return is_dataset_loaded() and (
            len(st.session_state.get("saved_visualizations", [])) > 0 or
            bool(st.session_state.get("workflow_visualize_completed", False))
        )
    elif step_key == "dashboard":
        return is_dataset_loaded() and bool(st.session_state.get("workflow_dashboard_completed", False))
    return False


def mark_workflow_step(step_key: str, completed: bool = True) -> None:
    """Record that a user has meaningfully completed an analytical workflow step."""
    flag_map = {
        "quality": "workflow_quality_completed",
        "prep": "workflow_prep_completed",
        "analyze": "workflow_analyze_completed",
        "visualize": "workflow_visualize_completed",
        "dashboard": "workflow_dashboard_completed"
    }
    if step_key in flag_map:
        st.session_state[flag_map[step_key]] = completed


def get_current_workflow_stage() -> Dict[str, Any]:
    """
    Evaluate the user's current position in the analytical workflow journey.
    Returns status, active step, next recommended action, and completion metrics.
    """
    if not is_dataset_loaded():
        return {
            "current_step_key": "upload",
            "current_step_num": 1,
            "current_step_name": "Upload Dataset",
            "progress_percent": 0,
            "completed_count": 0,
            "total_steps": 6,
            "status_label": "No Dataset Loaded",
            "recommended_title": "Upload a dataset to begin your analysis.",
            "recommended_desc": "Connect a CSV or Excel file to unlock quality audits, transformations, deep EDA, and dashboards.",
            "recommended_action_label": "UPLOAD DATASET →",
            "recommended_page": "Dataset"
        }

    completed_flags = [is_workflow_step_completed(s["key"]) for s in WORKFLOW_STEPS]
    completed_count = sum(1 for c in completed_flags if c)
    progress_pct = int((completed_count / len(WORKFLOW_STEPS)) * 100)

    # Determine current step (first incomplete step, or last step if all complete)
    current_idx = 0
    for idx, is_comp in enumerate(completed_flags):
        if not is_comp:
            current_idx = idx
            break
    else:
        current_idx = len(WORKFLOW_STEPS) - 1

    current_step = WORKFLOW_STEPS[current_idx]

    # Dynamic recommendation mapping based on current stage
    if not completed_flags[0]:  # Upload incomplete
        rec_title = "Upload a dataset to begin your analysis."
        rec_desc = "Upload a CSV or Excel file to start your analytics workflow."
        rec_btn = "UPLOAD DATASET →"
        rec_page = "Dataset"
    elif not completed_flags[1]:  # Quality incomplete
        rec_title = "Check your dataset quality for missing values, duplicates, and potential issues."
        rec_desc = "Evaluate health scores, completeness, and anomalous values before proceeding to preparation."
        rec_btn = "CONTINUE TO DATA QUALITY →"
        rec_page = "Data Quality"
    elif not completed_flags[2]:  # Prep incomplete
        rec_title = "Prepare your dataset and resolve identified issues."
        rec_desc = "Handle missing values, cast data types, deduplicate rows, and configure cleaned tables for analysis."
        rec_btn = "CONTINUE TO DATA PREPARATION →"
        rec_page = "Data Preparation"
    elif not completed_flags[3]:  # Analyze incomplete
        rec_title = "Explore patterns, distributions, correlations, and statistical summaries."
        rec_desc = "Run comprehensive exploratory data analysis (EDA), check correlations, and inspect distributions."
        rec_btn = "CONTINUE TO ANALYZE →"
        rec_page = "EDA"
    elif not completed_flags[4]:  # Visualize incomplete
        rec_title = "Create visualizations to communicate your findings."
        rec_desc = "Build interactive charts across comparison, trend, composition, and relationship families."
        rec_btn = "CONTINUE TO VISUALIZE →"
        rec_page = "Visualization"
    elif not completed_flags[5]:  # Dashboard incomplete
        rec_title = "Build a dashboard using your key metrics and charts."
        rec_desc = "Synthesize key metrics, trends, and executive insights into an interactive analytics dashboard."
        rec_btn = "OPEN DASHBOARD →"
        rec_page = "Dashboard"
    else:  # All complete
        rec_title = "Your analytics dashboard is ready."
        rec_desc = "Explore your complete analytics suite, consult the AI Analyst, or continue your deep-dive exploration."
        rec_btn = "ASK AI ANALYST →"
        rec_page = "AI Analyst"

    return {
        "current_step_key": current_step["key"],
        "current_step_num": current_step["step_num"],
        "current_step_name": current_step["name"],
        "progress_percent": progress_pct,
        "completed_count": completed_count,
        "total_steps": len(WORKFLOW_STEPS),
        "status_label": f"Step {current_step['step_num']} of {len(WORKFLOW_STEPS)}: {current_step['name']}",
        "recommended_title": rec_title,
        "recommended_desc": rec_desc,
        "recommended_action_label": rec_btn,
        "recommended_page": rec_page
    }


def reset_workflow_progress() -> None:
    """Reset workflow tracking flags when clearing or changing active dataset."""
    st.session_state["workflow_quality_completed"] = False
    st.session_state["workflow_prep_completed"] = False
    st.session_state["workflow_analyze_completed"] = False
    st.session_state["workflow_visualize_completed"] = False
    st.session_state["workflow_dashboard_completed"] = False
    st.session_state["saved_visualizations"] = []


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


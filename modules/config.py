"""
DATA STUDIO v2 — Configuration and Session State Architecture
"""
from typing import Dict, List, Any
import streamlit as st

# Application Branding
APP_NAME = "Data Studio"
APP_SUBTITLE = "Data Analytics Platform"
APP_VERSION = "v2.0"

# Icon mapping for navigation items (Lucide-style icon keys)
NAV_PAGE_ICONS: Dict[str, str] = {
    "Dataset": "database",
    "Overview": "layout-dashboard",
    "Data Quality": "shield-check",
    "Data Preparation": "sliders-horizontal",
    "Analyze": "chart-no-axes-combined",
    "EDA": "chart-no-axes-combined",
    "Visualization": "chart-column",
    "Dashboard": "panels-top-left",
    "AI Analyst": "brain-circuit",
    "Data Story": "book-open",
    "Settings": "settings",
    "Admin Analytics": "shield-check",
    "Activity": "activity",
}

# Canonical Navigation Groups and Pages (Organized by Professional Hierarchy)
NAV_GROUPS: Dict[str, List[str]] = {
    "WORKSPACE": [
        "Dataset",
        "Overview",
        "Data Quality",
        "Data Preparation",
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
        "description": "Dataset management, overview, data quality audit, interactive preparation, statistical analysis, visualization studio, and executive dashboard.",
        "icon": "database",
        "badge": "WORKSPACE",
        "pages": ["Dataset", "Overview", "Data Quality", "Data Preparation", "Analyze", "Visualization", "Dashboard"]
    },
    "INTELLIGENCE": {
        "title": "Intelligence & Insights",
        "description": "Conversational AI Analyst and multi-chapter executive data storytelling.",
        "icon": "brain-circuit",
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
        "icon": "shield-check",
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
    "Data Quality": {
        "title": "Data Quality",
        "subtitle": "Assess completeness, consistency, and reliability of your dataset.",
        "icon": "shield-check",
        "group": "WORKSPACE",
        "category_badge": "WORKSPACE"
    },
    "Data Preparation": {
        "title": "Data Preparation",
        "subtitle": "Interactive cleaning, type conversions, missing value handling, and transformation.",
        "icon": "sliders-horizontal",
        "group": "WORKSPACE",
        "category_badge": "WORKSPACE"
    },
    "Analyze": {
        "title": "Analyze",
        "subtitle": "Statistical distributions, correlation matrices, skewness, and outlier detection.",
        "icon": "chart-no-axes-combined",
        "group": "WORKSPACE",
        "category_badge": "WORKSPACE"
    },
    "EDA": {
        "title": "Analyze",
        "subtitle": "Statistical distributions, correlation matrices, skewness, and outlier detection.",
        "icon": "chart-no-axes-combined",
        "group": "WORKSPACE",
        "category_badge": "WORKSPACE"
    },
    "Visualization": {
        "title": "Visualization",
        "subtitle": "Interactive BI visualization studio with 25+ chart types and vector exports.",
        "icon": "chart-column",
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
        "icon": "brain-circuit",
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
        "icon": "shield-check",
        "group": "ADMINISTRATION",
        "category_badge": "ADMIN"
    }
}

# =============================================================================
# WORKFLOW TIMELINE CONSTANTS & PROGRESS TRACKING
# =============================================================================

WORKFLOW_STEPS = [
    {
        "key": "dataset",
        "step_num": 1,
        "name": "Dataset",
        "short_name": "Dataset",
        "page": "Dataset",
        "desc": "Upload and manage your active dataset with schema detection."
    },
    {
        "key": "overview",
        "step_num": 2,
        "name": "Overview",
        "short_name": "Overview",
        "page": "Overview",
        "desc": "Understand dataset structure and workspace summary."
    },
    {
        "key": "quality",
        "step_num": 3,
        "name": "Data Quality",
        "short_name": "Quality",
        "page": "Data Quality",
        "desc": "Audit dataset health, detect issues, and recommend remediation."
    },
    {
        "key": "prep",
        "step_num": 4,
        "name": "Data Preparation",
        "short_name": "Preparation",
        "page": "Data Preparation",
        "desc": "Apply corrections, clean missing values, and cast types."
    },
    {
        "key": "analyze",
        "step_num": 5,
        "name": "Analyze",
        "short_name": "Analyze",
        "page": "Analyze",
        "desc": "Discover patterns, statistical distributions, and correlations."
    },
    {
        "key": "visualize",
        "step_num": 6,
        "name": "Visualization",
        "short_name": "Visualization",
        "page": "Visualization",
        "desc": "Create interactive charts and explore findings visually."
    },
    {
        "key": "dashboard",
        "step_num": 7,
        "name": "Dashboard",
        "short_name": "Dashboard",
        "page": "Dashboard",
        "desc": "Combine important findings into an interactive dashboard."
    },
    {
        "key": "ai_analyst",
        "step_num": 8,
        "name": "AI Analyst",
        "short_name": "AI Analyst",
        "page": "AI Analyst",
        "desc": "Ask questions and receive AI-powered analysis."
    },
    {
        "key": "story",
        "step_num": 9,
        "name": "Data Story",
        "short_name": "Data Story",
        "page": "Data Story",
        "desc": "Convert the analysis into a complete understandable story."
    }
]


def init_session_state() -> None:
    """Initialize default session state keys for the application foundation."""
    defaults: Dict[str, Any] = {
        "current_page": "Overview",
        "theme": "Light",           # Light is the default
        "sidebar_collapsed": False,  # Sidebar state (expanded / collapsed)
        "mobile_drawer_open": False, # Mobile drawer state
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
        "workflow_dataset_completed": False,
        "workflow_overview_completed": False,
        "workflow_quality_completed": False,
        "workflow_prep_completed": False,
        "workflow_analyze_completed": False,
        "workflow_visualize_completed": False,
        "workflow_dashboard_completed": False,
        "workflow_ai_completed": False,
        "workflow_story_completed": False,
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
    if step_key == "dataset" or step_key == "upload":
        return is_dataset_loaded()
    elif step_key == "overview":
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
    elif step_key == "ai_analyst":
        return is_dataset_loaded() and bool(st.session_state.get("workflow_ai_completed", False))
    elif step_key == "story":
        return is_dataset_loaded() and bool(st.session_state.get("workflow_story_completed", False))
    return False


def mark_workflow_step(step_key: str, completed: bool = True) -> None:
    """Record that a user has meaningfully completed an analytical workflow step."""
    flag_map = {
        "dataset": "workflow_dataset_completed",
        "overview": "workflow_overview_completed",
        "quality": "workflow_quality_completed",
        "prep": "workflow_prep_completed",
        "analyze": "workflow_analyze_completed",
        "visualize": "workflow_visualize_completed",
        "dashboard": "workflow_dashboard_completed",
        "ai_analyst": "workflow_ai_completed",
        "story": "workflow_story_completed"
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
            "current_step_key": "dataset",
            "current_step_num": 1,
            "current_step_name": "Dataset",
            "progress_percent": 0,
            "completed_count": 0,
            "total_steps": len(WORKFLOW_STEPS),
            "status_label": "No Dataset Loaded",
            "recommended_title": "Upload a dataset to begin your analysis.",
            "recommended_desc": "Upload a CSV or Excel file to begin exploring data structure, quality, and patterns.",
            "recommended_action_label": "Upload Dataset →",
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
    if not completed_flags[0]:  # Dataset incomplete
        rec_title = "Upload a dataset to begin your analysis."
        rec_desc = "Upload a CSV or Excel file to start your analytics workflow."
        rec_btn = "Upload Dataset →"
        rec_page = "Dataset"
    elif not completed_flags[2]:  # Quality incomplete
        rec_title = "Check your dataset quality for missing values, duplicates, and anomalies."
        rec_desc = "Determine whether the dataset can be trusted before applying preparation transformations."
        rec_btn = "Continue to Data Quality →"
        rec_page = "Data Quality"
    elif not completed_flags[3]:  # Prep incomplete
        rec_title = "Apply recommended corrections and prepare your dataset."
        rec_desc = "Handle missing values, cast data types, deduplicate rows, and configure cleaned tables."
        rec_btn = "Continue to Data Preparation →"
        rec_page = "Data Preparation"
    elif not completed_flags[4]:  # Analyze incomplete
        rec_title = "Discover patterns, distributions, and statistical relationships."
        rec_desc = "Run comprehensive exploratory data analysis, inspect distributions, and check correlations."
        rec_btn = "Continue to Analyze →"
        rec_page = "Analyze"
    elif not completed_flags[5]:  # Visualize incomplete
        rec_title = "Explore your findings visually."
        rec_desc = "Build interactive charts across comparison, trend, composition, and relationship families."
        rec_btn = "Continue to Visualization →"
        rec_page = "Visualization"
    elif not completed_flags[6]:  # Dashboard incomplete
        rec_title = "Combine important findings into an interactive dashboard."
        rec_desc = "Synthesize key metrics, trends, and executive insights into an analytics dashboard."
        rec_btn = "Open Dashboard →"
        rec_page = "Dashboard"
    elif not completed_flags[7]:  # AI Analyst incomplete
        rec_title = "Ask questions and receive AI-powered analysis."
        rec_desc = "Explore natural language queries, root-cause investigations, and automated insights."
        rec_btn = "Open AI Analyst →"
        rec_page = "AI Analyst"
    elif not completed_flags[8]:  # Story incomplete
        rec_title = "Convert the analysis into a complete understandable story."
        rec_desc = "Generate an executive narrative briefing synthesizing all your findings."
        rec_btn = "Generate Data Story →"
        rec_page = "Data Story"
    else:  # All complete
        rec_title = "Your analytical workflow is complete."
        rec_desc = "Revisit your dashboard, ask further questions to the AI Analyst, or export your story."
        rec_btn = "Open Dashboard →"
        rec_page = "Dashboard"

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
    st.session_state["workflow_dataset_completed"] = False
    st.session_state["workflow_overview_completed"] = False
    st.session_state["workflow_quality_completed"] = False
    st.session_state["workflow_prep_completed"] = False
    st.session_state["workflow_analyze_completed"] = False
    st.session_state["workflow_visualize_completed"] = False
    st.session_state["workflow_dashboard_completed"] = False
    st.session_state["workflow_ai_completed"] = False
    st.session_state["workflow_story_completed"] = False
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



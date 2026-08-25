"""
DATA STUDIO v2 — Overview Landing Module (Premium UI v2)
=============================================================================
Personalized workspace home with greeting, KPI summary, quick action grid,
workflow steps, and contextual insight cards.
"""
import datetime
import streamlit as st
from modules.ui_components import (
    render_page_header,
    render_empty_state,
    render_section_header,
    render_metric_card,
    render_insight_card,
    render_activity_list,
    get_icon_svg,
)
from modules.config import is_dataset_loaded
from modules.auth import get_current_user


def _get_greeting() -> str:
    """Return a time-of-day greeting string."""
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    return "Good evening"


def render_overview_page() -> None:
    """Render the premium Overview landing view."""
    user = get_current_user()
    first_name = user.get("full_name", "").split()[0] if user.get("full_name") else "there"
    greeting = _get_greeting()
    dataset_loaded = is_dataset_loaded()

    render_page_header(
        title="Overview",
        subtitle="Your Data Studio workspace home.",
        icon="home"
    )

    # ── Welcome Hero ───────────────────────────────────────────────────────────
    greet_icon = get_icon_svg("zap", 18)
    welcome_html = (
        f'<div class="ds-welcome-hero">'
        f'<div class="ds-welcome-greeting">'
        f'{greeting}, {first_name}. 👋'
        f'</div>'
        f'<div class="ds-welcome-subtitle">'
        + (
            "A dataset is loaded and ready for exploration. Dive into any module below."
            if dataset_loaded else
            "Upload a dataset to unlock the full analytics suite — dashboards, EDA, "
            "data quality scoring, visualization studio, and AI-powered insights."
        ) +
        f'</div>'
        f'</div>'
    )
    st.markdown(welcome_html, unsafe_allow_html=True)

    # ── KPI Cards (when dataset is loaded) ────────────────────────────────────
    if dataset_loaded:
        df = st.session_state.get("dataset")
        name = st.session_state.get("dataset_name", "dataset.csv")
        meta = st.session_state.get("dataset_metadata") or {}
        rows = meta.get("total_rows", df.shape[0] if df is not None else 0)
        cols = meta.get("total_columns", df.shape[1] if df is not None else 0)
        missing_rate = meta.get("missing_percentage", None)
        quality_score = meta.get("quality_score", None)
        is_prepared = st.session_state.get("cleaned_dataset") is not None

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric_card(
                label="Active Dataset",
                value=name.split(".")[0].replace("_", " ").title()[:14],
                description=f".{name.split('.')[-1].upper()}",
                status="Loaded",
                icon="database"
            )
        with c2:
            render_metric_card(
                label="Dataset Size",
                value=f"{rows:,}",
                description=f"{cols} columns",
                status="Rows",
                icon="table"
            )
        with c3:
            render_metric_card(
                label="Data Quality",
                value=f"{int(quality_score)}%" if quality_score is not None else "—",
                change_type="success" if (quality_score or 0) >= 80 else "warning",
                description="Health score",
                icon="shield-check"
            )
        with c4:
            render_metric_card(
                label="Dataset State",
                value="Prepared" if is_prepared else "Original",
                description="Active version",
                status="Clean" if is_prepared else "Raw",
                icon="check-circle" if is_prepared else "wrench",
                change_type="success" if is_prepared else "neutral"
            )

        st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

    # ── Quick Actions ──────────────────────────────────────────────────────────
    render_section_header(
        title="Quick Actions",
        subtitle="Jump to any workflow step directly."
    )

    if not dataset_loaded:
        # Pre-dataset actions
        qa_col1, qa_col2, qa_col3, qa_col4 = st.columns(4)

        with qa_col1:
            upload_icon = get_icon_svg("upload", 22)
            card_html = (
                f'<div class="ds-action-card">'
                f'<div class="ds-action-icon">{upload_icon}</div>'
                f'<div class="ds-action-title">Upload Dataset</div>'
                f'<div class="ds-action-desc">Load CSV or Excel for instant analysis.</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button("Upload", key="qa_upload", use_container_width=True, type="primary"):
                st.session_state["current_page"] = "Dataset"
                st.rerun()

        with qa_col2:
            icon = get_icon_svg("layout-dashboard", 22)
            card_html = (
                f'<div class="ds-action-card">'
                f'<div class="ds-action-icon" style="background:rgba(124,58,237,0.08);color:#7c3aed;">{icon}</div>'
                f'<div class="ds-action-title">View Dashboard</div>'
                f'<div class="ds-action-desc">Auto-generated KPIs and insight charts.</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button("Dashboard", key="qa_dash", use_container_width=True):
                st.session_state["current_page"] = "Dashboard"
                st.rerun()

        with qa_col3:
            icon = get_icon_svg("bar-chart-3", 22)
            card_html = (
                f'<div class="ds-action-card">'
                f'<div class="ds-action-icon" style="background:rgba(5,150,105,0.08);color:#059669;">{icon}</div>'
                f'<div class="ds-action-title">Visualization</div>'
                f'<div class="ds-action-desc">Build custom interactive charts.</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button("Visualize", key="qa_viz", use_container_width=True):
                st.session_state["current_page"] = "Visualization"
                st.rerun()

        with qa_col4:
            icon = get_icon_svg("sparkles", 22)
            card_html = (
                f'<div class="ds-action-card">'
                f'<div class="ds-action-icon" style="background:rgba(217,119,6,0.08);color:#d97706;">{icon}</div>'
                f'<div class="ds-action-title">AI Analyst</div>'
                f'<div class="ds-action-desc">Natural language data exploration.</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button("Ask AI", key="qa_ai", use_container_width=True):
                st.session_state["current_page"] = "AI Analyst"
                st.rerun()

    else:
        # Post-dataset actions
        qa_col1, qa_col2, qa_col3, qa_col4 = st.columns(4)

        with qa_col1:
            icon = get_icon_svg("search", 22)
            card_html = (
                f'<div class="ds-action-card">'
                f'<div class="ds-action-icon">{icon}</div>'
                f'<div class="ds-action-title">Run EDA</div>'
                f'<div class="ds-action-desc">Distributions, correlations, and outlier detection.</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button("Open EDA", key="qa_eda", use_container_width=True, type="primary"):
                st.session_state["current_page"] = "EDA"
                st.rerun()

        with qa_col2:
            icon = get_icon_svg("shield-check", 22)
            card_html = (
                f'<div class="ds-action-card">'
                f'<div class="ds-action-icon" style="background:rgba(5,150,105,0.08);color:#059669;">{icon}</div>'
                f'<div class="ds-action-title">Data Quality</div>'
                f'<div class="ds-action-desc">Health scoring, completeness, and validity.</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button("Check Quality", key="qa_quality", use_container_width=True):
                st.session_state["current_page"] = "Data Quality"
                st.rerun()

        with qa_col3:
            icon = get_icon_svg("bar-chart-3", 22)
            card_html = (
                f'<div class="ds-action-card">'
                f'<div class="ds-action-icon" style="background:rgba(124,58,237,0.08);color:#7c3aed;">{icon}</div>'
                f'<div class="ds-action-title">Visualization</div>'
                f'<div class="ds-action-desc">Build interactive charts without code.</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button("Visualize", key="qa_viz_loaded", use_container_width=True):
                st.session_state["current_page"] = "Visualization"
                st.rerun()

        with qa_col4:
            icon = get_icon_svg("layout-dashboard", 22)
            card_html = (
                f'<div class="ds-action-card">'
                f'<div class="ds-action-icon" style="background:rgba(217,119,6,0.08);color:#d97706;">{icon}</div>'
                f'<div class="ds-action-title">Dashboard</div>'
                f'<div class="ds-action-desc">Auto-generated KPI cards and insights.</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button("Dashboard", key="qa_dash_loaded", use_container_width=True):
                st.session_state["current_page"] = "Dashboard"
                st.rerun()

    st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

    # ── Main content split: Workflow + Activity ────────────────────────────────
    left_col, right_col = st.columns([6, 4], gap="large")

    with left_col:
        # Workflow Steps
        render_section_header(
            title="Analytics Workflow",
            subtitle="How Data Studio transforms raw data into actionable intelligence."
        )
        st.markdown("""
<div class="ds-workflow-container">
    <div class="ds-workflow-step">
        <span class="ds-step-num">STEP 01</span>
        <span class="ds-step-title">Upload Dataset</span>
        <span class="ds-step-desc">Connect CSV or Excel files with automated schema and encoding detection.</span>
    </div>
    <div class="ds-workflow-step">
        <span class="ds-step-num">STEP 02</span>
        <span class="ds-step-title">Prepare & Profile</span>
        <span class="ds-step-desc">Clean data types, fill missing values, and score dataset health.</span>
    </div>
    <div class="ds-workflow-step">
        <span class="ds-step-num">STEP 03</span>
        <span class="ds-step-title">Build Dashboard</span>
        <span class="ds-step-desc">Auto-generate executive KPIs and high-priority insight charts.</span>
    </div>
    <div class="ds-workflow-step">
        <span class="ds-step-num">STEP 04</span>
        <span class="ds-step-title">Explore & Analyze</span>
        <span class="ds-step-desc">Deep-dive EDA, interactive visualizations, and AI-powered queries.</span>
    </div>
</div>
""", unsafe_allow_html=True)

        # Contextual insight cards (when dataset loaded)
        if dataset_loaded:
            meta = st.session_state.get("dataset_metadata") or {}
            missing_rate = meta.get("missing_percentage", 0) or 0
            dup_rate = meta.get("duplicate_percentage", 0) or 0
            quality_score = meta.get("quality_score", 100) or 100

            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
            render_section_header(
                title="Data Insights",
                subtitle="Automatic observations from your active dataset."
            )

            # Missing values insight
            if missing_rate > 5:
                render_insight_card(
                    title=f"{missing_rate:.1f}% Missing Values Detected",
                    description=(
                        f"Your dataset has cells with missing data. Use Data Preparation "
                        f"to fill, interpolate, or drop incomplete rows."
                    ),
                    priority="warning",
                    actions=[{"label": "Fix in Data Prep", "page": "Data Preparation"}]
                )
            else:
                render_insight_card(
                    title="Completeness Looks Healthy",
                    description=(
                        f"Only {missing_rate:.1f}% missing values found. Your dataset "
                        f"has good overall completeness."
                    ),
                    priority="healthy",
                    actions=[{"label": "View Quality Report", "page": "Data Quality"}]
                )

            # Duplicate rows insight
            if dup_rate > 1:
                render_insight_card(
                    title=f"{dup_rate:.1f}% Duplicate Rows",
                    description=(
                        "Duplicate records can distort aggregations and model training. "
                        "Consider deduplication in the Data Preparation module."
                    ),
                    priority="warning" if dup_rate > 5 else "info",
                    actions=[{"label": "Deduplicate", "page": "Data Preparation"}]
                )

            # Quality score insight
            if quality_score < 70:
                render_insight_card(
                    title=f"Quality Score {int(quality_score)}% — Needs Attention",
                    description=(
                        "Your dataset has significant quality issues. Check the Data Quality "
                        "report for a detailed breakdown and recommended actions."
                    ),
                    priority="critical",
                    actions=[{"label": "View Quality Report", "page": "Data Quality"}]
                )

    with right_col:
        render_section_header(
            title="Recent Activity",
            subtitle="Your session events and actions."
        )
        render_activity_list(max_items=8)

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

        if not dataset_loaded:
            # First-time user: platform capabilities
            render_section_header(
                title="Platform Capabilities",
                subtitle="What you can do with Data Studio."
            )
            caps = [
                ("database", "Dataset Workspace", "CSV & Excel upload with schema profiling"),
                ("layout-dashboard", "Auto Dashboards", "KPIs, charts, and data summaries"),
                ("shield-check", "Data Quality Engine", "0–100 health scoring system"),
                ("wrench", "Data Preparation", "Missing values, encoding, transformations"),
                ("search", "Exploratory Analysis", "Distributions, correlation, outliers"),
                ("bar-chart-3", "Visualization Studio", "Interactive chart builder"),
                ("sparkles", "AI Analyst", "Natural language data queries"),
            ]
            for icon_name, cap_title, cap_desc in caps:
                icon_svg = get_icon_svg(icon_name, 13)
                st.markdown(
                    f'<div class="ds-activity-item">'
                    f'<div style="color:var(--accent);display:flex;align-items:center;">{icon_svg}</div>'
                    f'<div class="ds-activity-text"><strong>{cap_title}</strong> — {cap_desc}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

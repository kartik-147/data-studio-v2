"""
DATA STUDIO v2 — Intelligent Overview & Control Center Module
=============================================================================
Workspace home providing dynamic greetings, dataset dimensions, progress timeline,
intelligent next-step recommendations, and compact administrative summaries.
"""
import datetime
import html
import streamlit as st
from modules.ui_components import (
    render_page_header,
    render_section_header,
    render_metric_card,
    render_insight_card,
    render_activity_list,
    render_workflow_timeline,
    render_next_step_banner,
    render_next_workflow_steps,
    get_icon_svg,
)
from modules.config import (
    is_dataset_loaded,
    get_current_workflow_stage,
    WORKFLOW_STEPS,
    is_workflow_step_completed
)
from modules.auth import get_current_user
from modules.firebase_service import is_admin_user, fetch_admin_analytics
from modules.data_loader import (
    get_available_sample_datasets,
    load_sample_dataset_by_key,
    set_active_dataset
)


def _get_greeting() -> str:
    """Return a time-of-day greeting string adjusted to local timezone (IST UTC+5:30)."""
    tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now = datetime.datetime.now(tz)
    hour = now.hour
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 17:
        return "Good afternoon"
    elif 17 <= hour < 22:
        return "Good evening"
    return "Good night"


def render_overview_page() -> None:
    """Render the intelligent Overview Control Center."""
    user = get_current_user()
    is_admin = is_admin_user(user)
    first_name = user.get("full_name", "").split()[0] if user.get("full_name") else "there"
    greeting = _get_greeting()
    dataset_loaded = is_dataset_loaded()
    stage_info = get_current_workflow_stage()

    render_page_header(
        title="Overview",
        subtitle="Intelligent control center, workflow progress, and dataset summary.",
        icon="layout-dashboard"
    )

    # ── Admin Welcome Banner & Compact Summary (Admin Only) ──────────────────
    if is_admin:
        _render_admin_welcome_summary()

    # ── Welcome Hero ─────────────────────────────────────────────────────────
    if not is_admin:
        if dataset_loaded:
            welcome_subtitle = f"Active dataset loaded ({stage_info['status_label']}). Continue your analysis workflow below."
            greeting_title = f"{greeting}, {first_name}."
        else:
            greeting_title = "Welcome to Data Studio."
            welcome_subtitle = "Upload a dataset to begin your analysis."

        welcome_html = (
            f'<div class="ds-welcome-hero">'
            f'<div class="ds-welcome-greeting">{greeting_title}</div>'
            f'<div class="ds-welcome-subtitle">{welcome_subtitle}</div>'
            f'</div>'
        )
        st.markdown(welcome_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════════
    # STATE A: WHEN NO DATASET IS LOADED
    # ═════════════════════════════════════════════════════════════════════════
    if not dataset_loaded:
        _render_no_dataset_state()
        return

    # ═════════════════════════════════════════════════════════════════════════
    # STATE B: WHEN A DATASET IS LOADED
    # ═════════════════════════════════════════════════════════════════════════
    _render_active_dataset_state(stage_info)


# =============================================================================
# ADMIN OVERVIEW SUMMARY
# =============================================================================

def _render_admin_welcome_summary() -> None:
    """Render a clean, compact administrative summary for the verified admin."""
    st.markdown(
        f"""
        <div style="background: var(--surface); border: 1px solid var(--border); border-left: 4px solid var(--accent); border-radius: var(--radius-md); padding: 14px 18px; margin-bottom: 16px; box-shadow: var(--shadow-xs);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px; font-weight: 700; color: var(--text-primary);">Welcome back, Admin.</span>
                    <span style="font-size: 10px; font-weight: 700; text-transform: uppercase; padding: 2px 7px; border-radius: 3px; background: rgba(37, 99, 235, 0.12); color: #2563eb; border: 1px solid rgba(37, 99, 235, 0.3); letter-spacing: 0.04em;">ADMIN</span>
                </div>
                <div style="font-size: 12px; color: var(--text-muted);">Administrative Workspace View</div>
            </div>
            <div style="font-size: 13px; color: var(--text-secondary); line-height: 1.45;">
                You have full access to both the normal dataset analysis workflow and platform administrative analytics.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Fetch real-time quick admin metrics
    admin_data = fetch_admin_analytics(date_filter="All Time")
    if admin_data.get("configured") and "kpis" in admin_data:
        kpis = admin_data["kpis"]
        ac1, ac2, ac3, ac4 = st.columns(4)
        with ac1:
            render_metric_card(label="Registered Users", value=f"{kpis.get('total_registered_users', 0):,}", status="Users", icon="users")
        with ac2:
            render_metric_card(label="Recent Logins", value=f"{kpis.get('total_login_events', 0):,}", status="Sessions", icon="activity")
        with ac3:
            render_metric_card(label="Dataset Uploads", value=f"{kpis.get('total_dataset_uploads', 0):,}", status="Uploads", icon="database")
        with ac4:
            render_metric_card(label="Active Users", value=f"{kpis.get('unique_active_users', 0):,}", status="Unique", icon="shield-check")

        col_admin_link, col_space = st.columns([3, 7])
        with col_admin_link:
            if st.button("Open Admin Analytics Dashboard →", key="ov_open_admin_btn", use_container_width=True):
                st.session_state["current_page"] = "Admin Analytics"
                st.rerun()

        st.markdown("<hr style='border:none; border-top: 1px solid var(--border); margin: 16px 0;'>", unsafe_allow_html=True)


# =============================================================================
# EMPTY STATE (NO DATASET LOADED)
# =============================================================================

def _render_no_dataset_state() -> None:
    """Render a clean, focused control center when no dataset is loaded."""
    col_main, col_preview = st.columns([6, 4], gap="large")

    with col_main:
        st.markdown(
            f"""
            <div style="background: var(--surface); border: 1.5px dashed var(--border-dashed); border-radius: var(--radius-md); padding: 36px 28px; text-align: center; margin-bottom: 20px;">
                <div style="display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; border-radius: 50%; background: var(--accent-subtle); color: var(--accent); margin-bottom: 16px;">
                    {get_icon_svg("upload", 26)}
                </div>
                <h3 style="font-size: 20px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; font-family: var(--font-sans);">
                    Upload a dataset to begin your analysis
                </h3>
                <p style="font-size: 14px; color: var(--text-secondary); max-width: 440px; margin: 0 auto 20px auto; line-height: 1.5;">
                    Connect a CSV or Excel file to unlock automated health audits, interactive cleaning, deep exploratory data analysis, and instant dashboards.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if st.button(
                "UPLOAD DATASET →",
                key="ov_empty_upload_btn",
                type="primary",
                use_container_width=True
            ):
                st.session_state["current_page"] = "Dataset"
                st.rerun()

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        render_section_header(
            title="Analysis Workflow Roadmap",
            subtitle="The standard enterprise path from raw data to actionable intelligence."
        )

        # Clean 6-step workflow preview roadmap
        render_workflow_timeline(interactive=False)

    with col_preview:
        render_section_header(
            title="Functional Architecture",
            subtitle="Three unified analytical pillars from ingestion to intelligence."
        )

        pillars = [
            (
                "database",
                "1. DATA FOUNDATION & HEALTH",
                "Dataset Workspace & Data Quality",
                "Multi-encoding parser, 5-type semantic classification, memory profiling, and deterministic 0–100 quality scoring.",
                "ds-badge-neutral"
            ),
            (
                "wrench",
                "2. TRANSFORM & EXPLORE",
                "Data Preparation & EDA Studio",
                "Interactive missing value imputation, outlier clipping, type casting, normality tests, and PCA dimensionality reduction.",
                "ds-badge-numeric"
            ),
            (
                "sparkles",
                "3. VISUALS & AI INTELLIGENCE",
                "25-Chart Studio, Dashboard & AI Analyst",
                "25 vector chart types, auto-generated executive KPI dashboards, multi-turn AI chat, and root-cause driver investigations.",
                "ds-badge-categorical"
            )
        ]

        for icon_name, p_tag, p_title, p_desc, badge_cls in pillars:
            icon_svg = get_icon_svg(icon_name, 15)
            st.markdown(
                f"""
                <div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 12px 16px; margin-bottom: 10px; box-shadow: var(--shadow-xs);">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                        <span class="ds-badge {badge_cls}" style="font-size: 9.5px; font-weight: 700; letter-spacing: 0.5px;">{p_tag}</span>
                        <div style="color: var(--accent);">{icon_svg}</div>
                    </div>
                    <div style="font-size: 13.5px; font-weight: 700; color: var(--text-primary); margin-bottom: 3px;">{p_title}</div>
                    <div style="font-size: 12px; color: var(--text-secondary); line-height: 1.45;">{p_desc}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # ── Quick Start with Sample Data ─────────────────────────────────────────
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    render_section_header(
        title="Quick Start with Sample Data",
        subtitle="Select a pre-loaded business dataset to immediately explore the entire Data Studio platform."
    )

    sample_catalog = get_available_sample_datasets()
    cols = st.columns(len(sample_catalog) if sample_catalog else 1)
    for idx, (key, info) in enumerate(sample_catalog.items()):
        with cols[idx]:
            st.markdown(f"**{info['name']}**")
            st.caption(info["description"])
            if st.button(f"Load {info['name']}", key=f"ov_sample_load_{key}", type="primary", use_container_width=True):
                with st.spinner(f"Loading {info['name']}..."):
                    s_df, s_err, s_file_type = load_sample_dataset_by_key(key)
                    if not s_err and s_df is not None:
                        set_active_dataset(s_df, info["filename"], s_file_type)
                        st.toast(f"{info['name']} loaded successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to load sample dataset: {s_err}")


# =============================================================================
# ACTIVE DATASET STATE (INTELLIGENT CONTROL CENTER)
# =============================================================================

def _render_active_dataset_state(stage_info: dict) -> None:
    """Render the active dataset control center answering the 3 core questions."""
    df = st.session_state.get("dataset")
    name = st.session_state.get("dataset_name", "dataset.csv")
    file_type = st.session_state.get("dataset_file_type", "CSV") or "CSV"
    meta = st.session_state.get("dataset_metadata") or {}
    rows = meta.get("total_rows", df.shape[0] if df is not None else 0)
    cols = meta.get("total_columns", df.shape[1] if df is not None else 0)
    quality_score = meta.get("quality_score", None)
    is_prepared = st.session_state.get("cleaned_dataset") is not None

    # 1. Answer: "What data am I working with?"
    render_section_header(
        title="Active Dataset Summary",
        subtitle=f"Currently loaded: {html.escape(name)} ({file_type.upper()})"
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card(
            label="Dataset Name",
            value=name.split(".")[0].replace("_", " ").title()[:14],
            description=f"Format: {file_type.upper()}",
            status="Active",
            icon="database"
        )
    with c2:
        render_metric_card(
            label="Dataset Dimensions",
            value=f"{rows:,}",
            description=f"{cols} total columns",
            status="Rows",
            icon="table"
        )
    with c3:
        render_metric_card(
            label="Data Quality Score",
            value=f"{int(quality_score)}%" if quality_score is not None else "—",
            change_type="success" if (quality_score or 0) >= 80 else "warning",
            description="Overall health",
            icon="shield-check"
        )
    with c4:
        render_metric_card(
            label="Workflow Status",
            value=f"{stage_info['progress_percent']}%",
            description=f"{stage_info['completed_count']}/{len(WORKFLOW_STEPS)} steps done",
            status="In Progress" if stage_info['progress_percent'] < 100 else "Completed",
            icon="activity",
            change_type="success" if stage_info['progress_percent'] >= 50 else "neutral"
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 2. Answer: "Where am I in the workflow?"
    render_section_header(
        title="Workflow Timeline",
        subtitle="Track your journey from raw dataset to executive dashboard."
    )
    render_workflow_timeline(interactive=True)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 3. Answer: "What should I do next?"
    render_next_step_banner(
        title=stage_info["recommended_title"],
        recommendation=stage_info["recommended_desc"],
        primary_action_label=stage_info["recommended_action_label"],
        target_page=stage_info["recommended_page"],
        key_prefix="ov_rec"
    )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # ── Main Content Split: Quick Actions & Contextual Insights ──────────────
    col_left, col_right = st.columns([6, 4], gap="large")

    with col_left:
        render_section_header(
            title="Functional Workspace Hub",
            subtitle="Jump directly to any specialized analysis module."
        )

        qa_col1, qa_col2, qa_col3 = st.columns(3, gap="small")
        with qa_col1:
            st.markdown("<div style='font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px;'>Workspace</div>", unsafe_allow_html=True)
            if st.button("Dataset", key="ov_qa_ds", use_container_width=True):
                st.session_state["current_page"] = "Dataset"
                st.rerun()
            if st.button("Data Quality", key="ov_qa_qual", use_container_width=True):
                st.session_state["current_page"] = "Data Quality"
                st.rerun()

        with qa_col2:
            st.markdown("<div style='font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px;'>Transform & Analyze</div>", unsafe_allow_html=True)
            if st.button("Data Preparation", key="ov_qa_prep", use_container_width=True):
                st.session_state["current_page"] = "Data Preparation"
                st.rerun()
            if st.button("Analyze", key="ov_qa_eda", use_container_width=True):
                st.session_state["current_page"] = "Analyze"
                st.rerun()

        with qa_col3:
            st.markdown("<div style='font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px;'>Visuals & Intelligence</div>", unsafe_allow_html=True)
            if st.button("Visualization", key="ov_qa_viz", use_container_width=True):
                st.session_state["current_page"] = "Visualization"
                st.rerun()
            if st.button("Dashboard", key="ov_qa_dash", use_container_width=True):
                st.session_state["current_page"] = "Dashboard"
                st.rerun()
            if st.button("AI Analyst", key="ov_qa_ai", use_container_width=True):
                st.session_state["current_page"] = "AI Analyst"
                st.rerun()
            if st.button("Data Story", key="ov_qa_story", use_container_width=True):
                st.session_state["current_page"] = "Data Story"
                st.rerun()

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Contextual Observations
        render_section_header(
            title="Automated Data Observations",
            subtitle="Immediate diagnostic highlights from your active dataset."
        )

        missing_rate = meta.get("missing_percentage", 0.0) or 0.0
        dup_rate = meta.get("duplicate_percentage", 0.0) or 0.0

        if missing_rate > 0:
            render_insight_card(
                title=f"{missing_rate:.1f}% Missing Values Detected",
                description="Your dataset contains incomplete fields. Use Data Preparation to impute, filter, or clean missing values.",
                priority="warning" if missing_rate > 5 else "info",
                actions=[{"label": "Clean in Data Prep", "page": "Data Preparation"}]
            )
        else:
            render_insight_card(
                title="100% Data Completeness",
                description="Zero missing values detected across all columns. Dataset integrity is high.",
                priority="healthy"
            )

        if dup_rate > 0:
            render_insight_card(
                title=f"{dup_rate:.1f}% Duplicate Rows Found",
                description="Duplicate records can bias statistical aggregations. Consider deduplication in Data Preparation.",
                priority="warning" if dup_rate > 3 else "info",
                actions=[{"label": "Deduplicate in Data Prep", "page": "Data Preparation"}]
            )

    with col_right:
        render_section_header(
            title="Session Activity",
            subtitle="Recent analytical events and operations."
        )
        render_activity_list(max_items=8)

    # ── Standardized Bottom Next Workflow Steps Section ──────────────────
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    render_next_workflow_steps("Overview")


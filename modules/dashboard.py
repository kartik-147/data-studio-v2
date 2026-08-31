"""
DATA STUDIO v2 — Power BI & Tableau Style AI Executive Dashboard
=============================================================================
Unified single-screen analytical cockpit providing:
  - Multi-perspective AI synthesis (rotates on [⚡ Refresh AI Dashboard])
  - Interactive Power BI style Category / Segment Slicers with instant chart sync
  - High-density executive KPI scorecard band
  - 2x2 responsive chart grid with interactive Plotly visuals
  - Executive AI Insights & Anomaly briefing card
  - One-Screen Download: Standalone offline HTML report & 1-page PDF print layout
  - Standardized bottom workflow navigation
"""
from __future__ import annotations
import html
import datetime
from typing import Optional, Dict, Any, List

import pandas as pd
import streamlit as st

from modules.config import is_dataset_loaded, mark_workflow_step, log_activity
from modules.ui_components import (
    render_page_header,
    render_section_header,
    render_empty_state,
    render_next_workflow_steps,
    render_notification,
    get_icon_svg,
)
from modules.data_loader import (
    get_available_sample_datasets,
    load_sample_dataset_by_key,
    set_active_dataset
)
from modules.dashboard_engine import (
    select_analytical_columns,
    prioritize_numeric_columns,
    prioritize_categorical_columns,
    generate_ai_dashboard_perspective,
    export_dashboard_to_standalone_html,
    PERSPECTIVE_DEFINITIONS,
)


# ─────────────────────────────────────────────────────────────────────────────
# STATE MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

def _init_dashboard_state() -> None:
    """Ensure dashboard session state variables are initialized."""
    if "dashboard_perspective_idx" not in st.session_state:
        st.session_state["dashboard_perspective_idx"] = 0
    if "dashboard_category_filter" not in st.session_state:
        st.session_state["dashboard_category_filter"] = "All"
    if "dashboard_filter_col" not in st.session_state:
        st.session_state["dashboard_filter_col"] = None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PAGE ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def render_dashboard_page() -> None:
    """Render the Power BI / Tableau AI Executive Dashboard."""
    _init_dashboard_state()

    # 1. Empty State Check
    if not is_dataset_loaded():
        render_page_header(
            title="Dashboard",
            subtitle="AI-powered executive dashboard and multi-perspective visual cockpit.",
            icon="layout-dashboard",
        )
        render_empty_state(
            title="No dataset loaded for Dashboard",
            description="Upload a CSV or Excel dataset or load a sample dataset to automatically generate your interactive Power BI / Tableau style AI dashboard.",
            icon="layout-dashboard",
        )

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        render_section_header(
            title="Quick Start with Sample Data",
            subtitle="Select a pre-loaded business dataset to immediately explore the Executive Dashboard."
        )

        sample_catalog = get_available_sample_datasets()
        cols = st.columns(len(sample_catalog) if sample_catalog else 1)
        for idx, (key, info) in enumerate(sample_catalog.items()):
            with cols[idx]:
                st.markdown(f"**{info['name']}**")
                st.caption(info["description"])
                if st.button(f"Load {info['name']}", key=f"dash_sample_load_{key}", type="primary", use_container_width=True):
                    with st.spinner(f"Loading {info['name']}..."):
                        s_df, s_err, s_file_type = load_sample_dataset_by_key(key)
                        if not s_err and s_df is not None:
                            set_active_dataset(s_df, info["filename"], s_file_type)
                            st.toast(f"{info['name']} loaded successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to load sample dataset: {s_err}")

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        btn_c1, btn_c2, btn_c3 = st.columns([1, 2, 1])
        with btn_c2:
            if st.button("Upload Custom Dataset", key="dash_goto_dataset_btn", use_container_width=True):
                st.session_state["current_page"] = "Dataset"
                st.rerun()
        return

    # 2. Extract Active Dataset & Metadata
    df: pd.DataFrame = st.session_state.get("dataset")
    metadata: Dict[str, Any] = st.session_state.get("dataset_metadata") or {}
    dataset_name = st.session_state.get("dataset_name", "dataset.csv")
    file_type = st.session_state.get("dataset_file_type", "CSV")
    current_theme = st.session_state.get("theme", "Light")

    if df is None or df.empty:
        render_notification(
            title="Dataset Empty",
            message="Active dataset contains no records to analyze.",
            variant="error"
        )
        return

    mark_workflow_step("dashboard", True)

    # 3. Analyze Column Candidates for Slicers
    analytical_cols = select_analytical_columns(df, metadata)
    ranked_cat = prioritize_categorical_columns(df, analytical_cols["categorical"])

    # 4. Standard Page Header
    render_page_header(
        title="Dashboard",
        subtitle=f"Interactive multi-perspective executive cockpit · {dataset_name} ({len(df):,} rows × {len(df.columns)} cols)",
        icon="panels-top-left",
    )

    # 5. Top Slicer Bar & Dynamic Perspective Control
    filtered_df, active_p_idx = _render_slicer_and_control_bar(df, ranked_cat, dataset_name, metadata, current_theme)

    # 6. Generate Multi-Perspective AI Layout
    perspective_data = generate_ai_dashboard_perspective(
        df=df,
        metadata=metadata,
        perspective_idx=active_p_idx,
        filtered_df=filtered_df,
        theme=current_theme
    )

    # 7. Render Perspective Banner
    _render_perspective_header_banner(perspective_data)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 8. Render 4 KPI Scorecard Tiles
    _render_kpi_scorecard_grid(perspective_data.get("kpi_cards", []))

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 9. Render 2x2 Interactive Power BI Chart Grid
    _render_2x2_chart_grid(perspective_data.get("charts", []))

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 10. Render Executive AI Briefing
    _render_executive_briefing(perspective_data.get("briefing", []))

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # 11. Standardized Universal Bottom Workflow Navigation
    render_next_workflow_steps("Dashboard")


# =============================================================================
# SLICER & CONTROL BAR
# =============================================================================

def _render_slicer_and_control_bar(
    df: pd.DataFrame,
    ranked_cat: List[str],
    dataset_name: str,
    metadata: Dict[str, Any],
    theme: str
) -> tuple[pd.DataFrame, int]:
    """
    Renders top horizontal control bar with:
      - Slicer dropdown (Filter by Category)
      - [⚡ Refresh AI Dashboard] button (rotates perspective)
      - [📥 Export Single-Screen Dashboard] popover with standalone HTML & print advice
    """
    col_slicer1, col_slicer2, col_refresh, col_export = st.columns([3, 3, 3, 3], gap="small")

    filtered_df = df

    # Slicer Column Selector
    with col_slicer1:
        if ranked_cat:
            filter_col = st.selectbox(
                "Slicer Dimension",
                options=ranked_cat,
                key="dash_slicer_col_sel",
                label_visibility="collapsed",
                help="Select category dimension to slice the dashboard"
            )
        else:
            filter_col = None
            st.markdown("<div style='font-size:12px; color:var(--text-muted); padding-top:8px;'>No category slicer available</div>", unsafe_allow_html=True)

    # Slicer Value Selector
    with col_slicer2:
        if filter_col and filter_col in df.columns:
            unique_vals = ["All"] + sorted([str(v) for v in df[filter_col].dropna().unique()][:40])
            selected_val = st.selectbox(
                "Filter Value",
                options=unique_vals,
                key="dash_slicer_val_sel",
                label_visibility="collapsed",
                help=f"Filter entire dashboard by {filter_col}"
            )
            if selected_val != "All":
                filtered_df = df[df[filter_col].astype(str) == selected_val]
        else:
            st.markdown("<div style='font-size:12px; color:var(--text-muted); padding-top:8px;'>Dataset unfiltered</div>", unsafe_allow_html=True)

    # Refresh AI Dashboard Button
    with col_refresh:
        if st.button(
            "⚡ Refresh Dashboard",
            key="dash_refresh_ai_btn",
            type="primary",
            use_container_width=True,
            help="Rotate perspective: generates alternative AI layout, charts, KPIs and smart insights!"
        ):
            st.session_state["dashboard_perspective_idx"] = (st.session_state.get("dashboard_perspective_idx", 0) + 1) % len(PERSPECTIVE_DEFINITIONS)
            new_p = PERSPECTIVE_DEFINITIONS[st.session_state["dashboard_perspective_idx"]]
            log_activity(f"Dashboard: Refreshed to {new_p['name']}", "layout-dashboard")
            st.toast(f"Switched to: {new_p['name']} ✓")
            st.rerun()

    # Export Single-Screen Dashboard Popover
    with col_export:
        with st.popover("📥 Export 1-Screen", help="Download self-contained offline dashboard or print 1-page PDF"):
            st.markdown("<div style='font-size:13px; font-weight:700; color:var(--text-primary); margin-bottom:8px;'>Export Options</div>", unsafe_allow_html=True)
            st.caption("Download a standalone single-screen dashboard with embedded interactive Plotly charts, or save as PDF.")

            active_idx = st.session_state.get("dashboard_perspective_idx", 0)
            current_p_data = generate_ai_dashboard_perspective(
                df=df,
                metadata=metadata,
                perspective_idx=active_idx,
                filtered_df=filtered_df,
                theme=theme
            )
            html_export_content = export_dashboard_to_standalone_html(
                dataset_name=dataset_name,
                metadata=metadata,
                perspective_data=current_p_data,
                theme=theme
            )

            st.download_button(
                label="Download Standalone HTML (.html)",
                data=html_export_content.encode("utf-8"),
                file_name=f"{dataset_name.replace('.csv','')}_dashboard_report.html",
                mime="text/html",
                key="dash_export_html_dl_btn",
                use_container_width=True,
                type="primary"
            )

            st.markdown(
                """
                <div style="font-size:11.5px; color:var(--text-secondary); margin-top:10px; padding:8px; background:var(--surface-container-low); border:1px solid var(--border); border-radius:6px;">
                    💡 <strong>Print / 1-Page PDF</strong>: Open the downloaded HTML file in Chrome/Edge and press <code>Ctrl + P</code> (Print to PDF) for a single-page executive briefing.
                </div>
                """,
                unsafe_allow_html=True
            )

    curr_p_idx = st.session_state.get("dashboard_perspective_idx", 0)
    return filtered_df, curr_p_idx


# =============================================================================
# PERSPECTIVE HEADER BANNER
# =============================================================================

def _render_perspective_header_banner(perspective_data: Dict[str, Any]) -> None:
    """Render perspective badge and narrative focus subtitle."""
    p_tag = perspective_data.get("perspective_tag", "PERSPECTIVE")
    p_name = perspective_data.get("perspective_name", "Executive Cockpit")
    p_desc = perspective_data.get("perspective_desc", "")

    st.markdown(
        f'<div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; margin-top:4px; margin-bottom:8px;">'
        f'<div style="display:flex; align-items:center; gap:8px;">'
        f'<span class="pbi-perspective-badge">{p_tag}</span>'
        f'<strong style="font-size:14.5px; color:var(--text-primary);">{html.escape(p_name)}</strong>'
        f'</div>'
        f'<div style="font-size:12px; color:var(--text-secondary); font-style:italic;">'
        f'{html.escape(p_desc)}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )


# =============================================================================
# KPI SCORECARD GRID
# =============================================================================

def _render_kpi_scorecard_grid(kpi_cards: List[Dict[str, Any]]) -> None:
    """Render 4 high-density KPI scorecards."""
    if not kpi_cards:
        return

    cols = st.columns(len(kpi_cards), gap="small")
    for i, kpi in enumerate(kpi_cards):
        with cols[i]:
            tile_cls = kpi.get("tile_class", "")
            badge_cls = kpi.get("badge_class", "pbi-badge-neutral")
            badge_text = kpi.get("badge", "")

            st.markdown(
                f'<div class="pbi-kpi-tile {tile_cls}">'
                f'<div class="pbi-kpi-label">{html.escape(kpi.get("label", "Metric"))}</div>'
                f'<div class="pbi-kpi-value">{html.escape(str(kpi.get("value", "0")))}</div>'
                f'<div class="pbi-kpi-meta">'
                f'<span class="pbi-kpi-badge {badge_cls}">{html.escape(badge_text)}</span>'
                f'<span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{html.escape(kpi.get("meta", ""))}</span>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )


# =============================================================================
# 2X2 INTERACTIVE CHART GRID
# =============================================================================

def _render_2x2_chart_grid(charts: List[Dict[str, Any]]) -> None:
    """Render 4 complementary charts in a clean 2x2 Power BI layout grid."""
    if not charts:
        st.info("No visual charts could be computed for the active perspective.")
        return

    # Row 1: Chart 0 and Chart 1
    if len(charts) >= 1:
        row1_c1, row1_c2 = st.columns(2, gap="medium")
        with row1_c1:
            _render_single_chart_card(charts[0], chart_idx=0)
        with row1_c2:
            if len(charts) >= 2:
                _render_single_chart_card(charts[1], chart_idx=1)

    # Row 2: Chart 2 and Chart 3
    if len(charts) >= 3:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        row2_c1, row2_c2 = st.columns(2, gap="medium")
        with row2_c1:
            _render_single_chart_card(charts[2], chart_idx=2)
        with row2_c2:
            if len(charts) >= 4:
                _render_single_chart_card(charts[3], chart_idx=3)


def _render_single_chart_card(chart_item: Dict[str, Any], chart_idx: int = 0) -> None:
    """Render an individual card container for a Plotly chart with unique element keys."""
    title = chart_item.get("title", "Visual Component")
    badge = chart_item.get("badge", "CHART")
    fig = chart_item.get("fig")

    st.markdown(
        f'<div class="pbi-chart-card-header">'
        f'<span class="pbi-chart-title">{html.escape(title)}</span>'
        f'<span class="pbi-chart-badge">{html.escape(badge)}</span>'
        f'</div>',
        unsafe_allow_html=True
    )

    if fig is not None:
        chart_key = f"pbi_cockpit_chart_{chart_idx}_{abs(hash(title)) % 1000000}"
        st.plotly_chart(
            fig,
            use_container_width=True,
            key=chart_key,
            config={"displayModeBar": False, "responsive": True}
        )
    else:
        st.markdown(
            '<div style="height:300px; display:flex; align-items:center; justify-content:center; background:var(--surface-container-low); border-radius:6px; color:var(--text-muted); font-size:13px;">'
            'Chart data unavailable for this selection'
            '</div>',
            unsafe_allow_html=True
        )


# =============================================================================
# EXECUTIVE AI BRIEFING
# =============================================================================

def _render_executive_briefing(briefing_items: List[Dict[str, Any]]) -> None:
    """Render executive summary takeaway bullet points."""
    if not briefing_items:
        return

    brief_html_list = []
    for b in briefing_items:
        title = html.escape(b.get("title", "Observation"))
        text = html.escape(b.get("text", ""))
        brief_html_list.append(
            f'<div class="pbi-insight-row">'
            f'<span class="pbi-insight-bullet">✦</span>'
            f'<div><strong style="color:var(--text-primary);">{title}</strong>: {text}</div>'
            f'</div>'
        )

    icon_svg = get_icon_svg("sparkles", 15)
    st.markdown(
        f'<div class="pbi-executive-brief">'
        f'<div class="pbi-brief-title">'
        f'{icon_svg} &nbsp;Executive AI Takeaways & Perspective Briefing'
        f'</div>'
        f'{"".join(brief_html_list)}'
        f'</div>',
        unsafe_allow_html=True
    )


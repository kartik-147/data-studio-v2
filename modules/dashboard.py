"""
DATA STUDIO v2 — Automatic Dataset Dashboard Module (Module 3)
=============================================================================
Dynamically profiles the active dataset to generate automated KPI metrics,
distribution charts, categorical comparisons, time trends, correlation matrices,
and deterministic factual insights.
"""
from typing import Optional, Dict, Any, List
import pandas as pd
import streamlit as st

from modules.config import is_dataset_loaded, mark_workflow_step
from modules.ui_components import (
    render_page_header,
    render_section_header,
    render_metric_card,
    render_notification,
    render_empty_state,
    render_next_step_banner,
    render_ai_context_trigger,
    get_icon_svg
)

from modules.dashboard_engine import (
    select_analytical_columns,
    prioritize_numeric_columns,
    prioritize_categorical_columns,
    select_primary_kpi_metric,
    generate_smart_insights,
    generate_composition_chart,
    generate_numeric_distribution_chart,
    generate_categorical_bar_chart,
    generate_time_trend_chart,
    generate_correlation_heatmap
)


def render_dashboard_page() -> None:
    """Main entry point for Automatic Dataset Dashboard (Module 3)."""
    # 1. Empty State Check
    if not is_dataset_loaded():
        render_page_header(
            title="Dashboard",
            subtitle="Automatically generated insights from your active dataset.",
            icon="layout-dashboard"
        )
        render_empty_state(
            title="No dataset loaded",
            description="Upload a dataset to automatically generate your analytics dashboard.",
            icon="layout-dashboard"
        )
        
        btn_c1, btn_c2, btn_c3 = st.columns([1, 2, 1])
        with btn_c2:
            if st.button("Go to Dataset", key="dashboard_goto_dataset_btn", type="primary", use_container_width=True):
                st.session_state["current_page"] = "Dataset"
                st.rerun()
        return

    # 2. Extract Active Dataset & Metadata
    df: pd.DataFrame = st.session_state.get("dataset")
    metadata: Dict[str, Any] = st.session_state.get("dataset_metadata")
    dataset_name = st.session_state.get("dataset_name", "dataset.csv")
    file_type = st.session_state.get("dataset_file_type", "CSV")
    current_theme = st.session_state.get("theme", "Dark")

    if df is None or metadata is None or df.empty:
        render_page_header(
            title="Dashboard",
            subtitle="Automatically generated insights from your active dataset.",
            icon="layout-dashboard"
        )
        render_notification(
            title="Dataset Unavailable",
            message="Active dataset could not be loaded into memory. Please re-select or upload your data.",
            variant="error"
        )
        if st.button("Return to Dataset", key="err_return_dataset_btn"):
            st.session_state["current_page"] = "Dataset"
            st.rerun()
        return

    # 3. Analyze Columns & Prioritize Features
    analytical_cols = select_analytical_columns(df, metadata)
    ranked_numeric = prioritize_numeric_columns(df, analytical_cols["numeric"])
    ranked_cat = prioritize_categorical_columns(df, analytical_cols["categorical"])
    dt_cols = analytical_cols["datetime"]

    # 4. Page Header
    render_page_header(
        title="Executive Dashboard",
        subtitle=f"Automatically generated executive overview and analytical breakdown for {dataset_name}",
        icon="layout-dashboard"
    )
    mark_workflow_step("dashboard", True)


    # 5. Dataset Context Bar
    _render_dataset_context_bar(dataset_name, file_type, metadata)

    # 6. KPI Overview Row
    _render_kpi_overview_row(df, metadata, ranked_numeric)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 7. Dataset Summary & Schema Composition
    _render_summary_and_composition_section(metadata, current_theme)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 8. Automatic Visual Insights (Distributions, Categories, Trends)
    _render_visual_insights_grid(df, ranked_numeric, ranked_cat, dt_cols, current_theme)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 9. Correlation Snapshot (if >= 2 numeric features)
    if len(ranked_numeric) >= 2:
        _render_correlation_section(df, ranked_numeric, current_theme)
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 10. Smart Insights Engine Output
    _render_smart_insights_section(df, metadata, analytical_cols)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # 11. Next-Step Navigation Actions
    _render_navigation_actions()


# =============================================================================
# SECTION RENDERERS
# =============================================================================

def _render_dataset_context_bar(name: str, file_type: str, metadata: Dict[str, Any]) -> None:
    """Render subtle context banner with quick actions."""
    col_info, col_actions = st.columns([7, 5])
    
    with col_info:
        banner_html = (
            f'<div class="ds-active-banner" style="margin-bottom: 12px; padding: 10px 16px;">'
            f'<div class="ds-active-banner-left">'
            f'<div class="ds-brand-badge" style="background: var(--accent);">{file_type[0]}</div>'
            f'<div>'
            f'<div class="ds-active-banner-name" style="font-size: 15px;">{name}</div>'
            f'<div class="ds-active-banner-meta" style="font-size: 12px;">'
            f'{metadata["total_rows"]:,} rows · {metadata["total_columns"]} columns · {file_type} · {metadata["memory_formatted"]}'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(banner_html, unsafe_allow_html=True)

    with col_actions:
        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
        ac1, ac2 = st.columns(2)
        with ac1:
            if st.button("Refresh Dashboard", key="dash_refresh_btn", use_container_width=True):
                st.toast("Dashboard analytics refreshed from active dataset.")
                st.rerun()
        with ac2:
            if st.button("View Dataset", key="dash_view_dataset_btn", use_container_width=True):
                st.session_state["current_page"] = "Dataset"
                st.rerun()



def _render_kpi_overview_row(
    df: pd.DataFrame,
    metadata: Dict[str, Any],
    ranked_numeric: List[str]
) -> None:
    """Generate dynamic top-level KPI cards tailored to dataset features."""
    render_section_header(
        title="Executive Metrics",
        subtitle="High-level indicators and primary aggregate statistics."
    )

    primary_kpi = select_primary_kpi_metric(df, ranked_numeric)
    
    # 5 columns if primary numeric KPI exists, else 4
    if primary_kpi:
        c1, c2, c3, c4, c5 = st.columns(5)
        
        with c1:
            render_metric_card(
                label="Total Records",
                value=f"{metadata['total_rows']:,}",
                description=f"{metadata['total_columns']} Columns",
                status="Size"
            )
        with c2:
            render_metric_card(
                label=primary_kpi["label"],
                value=primary_kpi["value"],
                description=f"Median: {primary_kpi['median']:,.1f}" if isinstance(primary_kpi['median'], (int, float)) else "Calculated",
                status=primary_kpi["agg_type"]
            )
        with c3:
            render_metric_card(
                label="Total Data Cells",
                value=f"{metadata['total_cells']:,}",
                description=metadata["memory_formatted"],
                status="Volume"
            )
        with c4:
            miss_cnt = metadata["missing_cells"]
            miss_pct = metadata["missing_percentage"]
            render_metric_card(
                label="Missing Values",
                value=f"{miss_cnt:,}",
                change=f"{miss_pct:.1f}% rate",
                change_type="positive" if miss_cnt == 0 else "neutral",
                description="Complete" if miss_cnt == 0 else f"{metadata['columns_with_missing']} cols affected",
                status="Health"
            )
        with c5:
            dup_cnt = metadata["duplicate_rows"]
            dup_pct = metadata["duplicate_percentage"]
            render_metric_card(
                label="Duplicate Rows",
                value=f"{dup_cnt:,}",
                change=f"{dup_pct:.1f}% rate",
                change_type="positive" if dup_cnt == 0 else "negative",
                description="Unique" if dup_cnt == 0 else f"{dup_cnt} duplicates",
                status="Integrity"
            )
    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric_card(
                label="Total Records",
                value=f"{metadata['total_rows']:,}",
                description="Sample Size",
                status="Rows"
            )
        with c2:
            render_metric_card(
                label="Total Features",
                value=f"{metadata['total_columns']:,}",
                description=metadata["memory_formatted"],
                status="Columns"
            )
        with c3:
            miss_cnt = metadata["missing_cells"]
            miss_pct = metadata["missing_percentage"]
            render_metric_card(
                label="Missing Values",
                value=f"{miss_cnt:,}",
                change=f"{miss_pct:.1f}% rate",
                change_type="positive" if miss_cnt == 0 else "neutral",
                status="Health"
            )
        with c4:
            dup_cnt = metadata["duplicate_rows"]
            dup_pct = metadata["duplicate_percentage"]
            render_metric_card(
                label="Duplicate Rows",
                value=f"{dup_cnt:,}",
                change=f"{dup_pct:.1f}% rate",
                change_type="positive" if dup_cnt == 0 else "negative",
                status="Integrity"
            )


def _render_summary_and_composition_section(
    metadata: Dict[str, Any],
    theme: str
) -> None:
    """Render dataset structural summary side-by-side with schema donut chart."""
    counts = metadata.get("type_counts", {})
    col_summary, col_donut = st.columns([5, 5], gap="large")

    with col_summary:
        render_section_header(
            title="Dataset Profile",
            subtitle="Structural breakdown and storage properties."
        )
        
        profile_html = (
            f'<div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: var(--space-4);">'
            f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">'
            f'<div>'
            f'<div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Dimensions</div>'
            f'<div style="font-size: 15px; font-weight: 600; color: var(--text-primary);">{metadata["total_rows"]:,} × {metadata["total_columns"]}</div>'
            f'</div>'
            f'<div>'
            f'<div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Memory Footprint</div>'
            f'<div style="font-size: 15px; font-weight: 600; color: var(--text-primary);">{metadata["memory_formatted"]}</div>'
            f'</div>'
            f'<div>'
            f'<div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Numeric Metrics</div>'
            f'<div style="font-size: 15px; font-weight: 600; color: #60a5fa;">{counts.get("Numeric", 0)} column(s)</div>'
            f'</div>'
            f'<div>'
            f'<div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Categorical Features</div>'
            f'<div style="font-size: 15px; font-weight: 600; color: #c084fc;">{counts.get("Categorical", 0)} column(s)</div>'
            f'</div>'
            f'<div>'
            f'<div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Date / Time Series</div>'
            f'<div style="font-size: 15px; font-weight: 600; color: #34d399;">{counts.get("Date/Time", 0)} column(s)</div>'
            f'</div>'
            f'<div>'
            f'<div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Data Health Status</div>'
            f'<div style="font-size: 15px; font-weight: 600; color: var(--color-success);">{100 - metadata["missing_percentage"]:.1f}% Complete</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(profile_html, unsafe_allow_html=True)

    with col_donut:
        render_section_header(
            title="Schema Composition",
            subtitle="Distribution of semantic column types."
        )
        donut_fig = generate_composition_chart(metadata, theme=theme)
        if donut_fig:
            st.plotly_chart(donut_fig, use_container_width=True, config={"displayModeBar": False})


def _render_visual_insights_grid(
    df: pd.DataFrame,
    ranked_numeric: List[str],
    ranked_cat: List[str],
    dt_cols: List[str],
    theme: str
) -> None:
    """Render balanced 2x2 grid of automatic distribution and trend visualizations."""
    render_section_header(
        title="Visual Insights",
        subtitle="Automated distributions, category proportions, and time-series trends."
    )

    charts_to_display = []

    # 1. Primary Numeric Distribution
    if ranked_numeric:
        num_fig = generate_numeric_distribution_chart(df, ranked_numeric[0], theme=theme)
        if num_fig:
            charts_to_display.append(num_fig)

    # 2. Primary Categorical Breakdown
    if ranked_cat:
        cat_fig = generate_categorical_bar_chart(df, ranked_cat[0], theme=theme)
        if cat_fig:
            charts_to_display.append(cat_fig)

    # 3. Time Trend (if date column exists) or Secondary Numeric Distribution
    if dt_cols:
        time_metric = ranked_numeric[0] if ranked_numeric else None
        trend_fig = generate_time_trend_chart(df, dt_cols[0], metric_col=time_metric, theme=theme)
        if trend_fig:
            charts_to_display.append(trend_fig)
    elif len(ranked_numeric) >= 2:
        num2_fig = generate_numeric_distribution_chart(df, ranked_numeric[1], theme=theme)
        if num2_fig:
            charts_to_display.append(num2_fig)

    # 4. Secondary Category or Third Numeric
    if len(ranked_cat) >= 2 and len(charts_to_display) < 4:
        cat2_fig = generate_categorical_bar_chart(df, ranked_cat[1], theme=theme)
        if cat2_fig:
            charts_to_display.append(cat2_fig)
    elif len(ranked_numeric) >= 3 and len(charts_to_display) < 4:
        num3_fig = generate_numeric_distribution_chart(df, ranked_numeric[2], theme=theme)
        if num3_fig:
            charts_to_display.append(num3_fig)

    if not charts_to_display:
        st.info("No standard numerical or categorical charts could be extracted from this dataset.")
        return

    # Render in 2-column rows
    for i in range(0, len(charts_to_display), 2):
        pair = charts_to_display[i:i+2]
        if len(pair) == 2:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(pair[0], use_container_width=True, config={"displayModeBar": False})
            with col2:
                st.plotly_chart(pair[1], use_container_width=True, config={"displayModeBar": False})
        else:
            st.plotly_chart(pair[0], use_container_width=True, config={"displayModeBar": False})


def _render_correlation_section(
    df: pd.DataFrame,
    ranked_numeric: List[str],
    theme: str
) -> None:
    """Render correlation heatmap snapshot and highlight top relationship."""
    render_section_header(
        title="Feature Relationships",
        subtitle="Pearson correlation snapshot across key numeric features."
    )

    col_map, col_info = st.columns([7, 5], gap="large")

    corr_fig, top_pair = generate_correlation_heatmap(df, ranked_numeric, theme=theme)

    with col_map:
        if corr_fig:
            st.plotly_chart(corr_fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Insufficient numeric variance to calculate correlation matrix.")

    with col_info:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        if top_pair:
            r = top_pair["r"]
            r_str = f"{r:+.2f}"
            c1_name = top_pair["col1"].replace("_", " ").title()
            c2_name = top_pair["col2"].replace("_", " ").title()
            
            if abs(r) >= 0.7:
                desc = "demonstrate a strong linear relationship"
                callout_variant = "success" if r > 0 else "info"
            elif abs(r) >= 0.4:
                desc = "demonstrate a moderate linear association"
                callout_variant = "info"
            else:
                desc = "demonstrate low linear correlation"
                callout_variant = "info"

            render_notification(
                title="Strongest Feature Pair",
                message=f"<b>{c1_name}</b> and <b>{c2_name}</b> {desc} (Pearson correlation coefficient: <b>{r_str}</b>).",
                variant=callout_variant
            )
        
        st.markdown("""
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: var(--space-4); margin-top: 12px;">
            <div style="font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">Correlation Interpretation</div>
            <div style="font-size: 12px; color: var(--text-secondary); line-height: 1.5;">
                • <b>+1.00</b>: Perfect positive linear correlation<br>
                • <b> 0.00</b>: No linear correlation<br>
                • <b>-1.00</b>: Perfect inverse linear correlation<br>
                Deep multi-variate and non-linear associations are analyzed in the upcoming EDA module.
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_smart_insights_section(
    df: pd.DataFrame,
    metadata: Dict[str, Any],
    analytical_cols: Dict[str, List[str]]
) -> None:
    """Render deterministic calculated insights cards."""
    render_section_header(
        title="Smart Dataset Insights",
        subtitle="Automated factual observations calculated directly from your dataset."
    )

    insights = generate_smart_insights(df, metadata, analytical_cols)
    
    if not insights:
        st.info("No notable data patterns detected.")
        return

    # Render in 2-column grid
    for i in range(0, len(insights), 2):
        chunk = insights[i:i+2]
        if len(chunk) == 2:
            c1, c2 = st.columns(2)
            with c1:
                render_notification(
                    title=chunk[0]["title"],
                    message=chunk[0]["text"],
                    variant=chunk[0]["variant"]
                )
            with c2:
                render_notification(
                    title=chunk[1]["title"],
                    message=chunk[1]["text"],
                    variant=chunk[1]["variant"]
                )
        else:
            render_notification(
                title=chunk[0]["title"],
                message=chunk[0]["text"],
                variant=chunk[0]["variant"]
            )


def _render_navigation_actions() -> None:
    """Render quick links to next exploratory phases and completion actions."""
    render_section_header(
        title="Workflow Completion & Next Steps",
        subtitle="Your analytics dashboard is ready. Continue exploring with AI, refine visualizations, or load a new dataset."
    )

    render_next_step_banner(
        title="Your analytics dashboard is ready.",
        recommendation="You have completed the automated workflow. Engage the AI Analyst for natural language queries, create custom visualizations, or upload a new dataset.",
        primary_action_label="✦ ASK AI ANALYST →",
        target_page="AI Analyst",
        key_prefix="dash_next_step",
        suggested_actions=[
            {"label": "🔍 Continue Analysis (EDA)", "page": "EDA"},
            {"label": "📊 Custom Visualizations", "page": "Visualization"},
            {"label": "📁 Upload New Dataset", "page": "Dataset"}
        ]
    )

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    render_ai_context_trigger("Explain this dashboard with AI", intent="dashboard_summary", key="dash_ai_btn")


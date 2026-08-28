"""
DATA STUDIO v2 — Data Quality Workspace Module (Module 4)
=============================================================================
Professional Data Quality Workspace analyzing completeness, uniqueness,
consistency, validity, outliers, and composite health scores.
Read-only analysis: NEVER mutates the underlying dataset.
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
    render_next_workflow_steps,
    get_icon_svg
)


from modules.data_quality_engine import (
    analyze_data_quality,
    generate_missing_bar_chart,
    generate_outlier_bar_chart
)


def render_data_quality_page() -> None:
    """Main entry point for Data Quality Module (Module 4)."""
    # 1. Empty State Check
    if not is_dataset_loaded():
        render_page_header(
            title="Data Quality",
            subtitle="Understand the health, completeness, and reliability of your dataset.",
            icon="shield-check"
        )
        render_empty_state(
            title="No dataset available",
            description="Upload a dataset to analyze its quality, completeness, and consistency.",
            icon="shield-check"
        )
        
        btn_c1, btn_c2, btn_c3 = st.columns([1, 2, 1])
        with btn_c2:
            if st.button("Go to Dataset", key="quality_goto_dataset_btn", type="primary", use_container_width=True):
                st.session_state["current_page"] = "Dataset"
                st.rerun()
        return

    # 2. Extract Active Dataset & Metadata
    df: pd.DataFrame = st.session_state.get("dataset")
    metadata: Dict[str, Any] = st.session_state.get("dataset_metadata")
    dataset_name = st.session_state.get("dataset_name", "dataset.csv")
    file_type = st.session_state.get("dataset_file_type", "CSV")
    current_theme = st.session_state.get("theme", "Light")

    if df is None or metadata is None or df.empty:
        render_page_header(
            title="Data Quality",
            subtitle="Understand the health, completeness, and reliability of your dataset.",
            icon="shield-check"
        )
        render_notification(
            title="Dataset State Error",
            message="Active dataset could not be accessed. Please upload or reload your data.",
            variant="error"
        )
        if st.button("Return to Dataset", key="err_return_quality_btn"):
            st.session_state["current_page"] = "Dataset"
            st.rerun()
        return

    # 3. Perform Comprehensive Quality Audit
    audit_report = analyze_data_quality(df, metadata)
    mark_workflow_step("quality", True)

    # 4. Standardized Page Header

    render_page_header(
        title="Data Quality",
        subtitle="Understand the health, completeness, and reliability of your dataset.",
        icon="shield-check"
    )

    # 5. Dataset Context Bar
    _render_context_bar(dataset_name, file_type, metadata)

    # 6. Hero Quality Score & Breakdown Card
    _render_quality_hero(audit_report)

    # 7. Quality KPI Summary Row
    _render_quality_kpis(audit_report, metadata)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 8. Internal Data Quality Tabs
    tab_overview, tab_missing, tab_duplicates, tab_consistency, tab_validity, tab_outliers = st.tabs([
        "OVERVIEW",
        "MISSING VALUES",
        "DUPLICATES",
        "DATA CONSISTENCY",
        "VALIDITY",
        "OUTLIERS"
    ])

    with tab_overview:
        _render_tab_overview(audit_report)

    with tab_missing:
        _render_tab_missing(audit_report, current_theme)

    with tab_duplicates:
        _render_tab_duplicates(audit_report)

    with tab_consistency:
        _render_tab_consistency(audit_report)

    with tab_validity:
        _render_tab_validity(audit_report)

    with tab_outliers:
        _render_tab_outliers(audit_report, current_theme)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # 9. Next Steps Navigation
    _render_next_actions(audit_report)


# =============================================================================
# CONTEXT & HERO RENDERERS
# =============================================================================

def _render_context_bar(name: str, file_type: str, metadata: Dict[str, Any]) -> None:
    """Render compact context bar with refresh action."""
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
            if st.button("Refresh Quality Analysis", key="quality_refresh_btn", use_container_width=True):
                st.toast("Data quality audit recalculated.")
                st.rerun()
        with ac2:
            if st.button("View Dataset", key="quality_view_dataset_btn", use_container_width=True):
                st.session_state["current_page"] = "Dataset"
                st.rerun()


def _render_quality_hero(report: Dict[str, Any]) -> None:
    """Render prominent Quality Score gauge and 5-dimension breakdown bars."""
    score = report["overall_score"]
    status = report["status"]
    status_color = report["status_color"]
    breakdown = report["breakdown"]

    # Build Breakdown Bar Rows
    breakdown_html_rows = []
    dim_colors = {
        "Completeness": "#3b82f6",
        "Uniqueness": "#10b981",
        "Consistency": "#8b5cf6",
        "Validity": "#f59e0b",
        "Outlier Health": "#06b6d4"
    }

    for dim_name, dim_val in breakdown.items():
        bar_color = dim_colors.get(dim_name, "#3b82f6")
        row_html = (
            f'<div class="ds-breakdown-item">'
            f'<span class="ds-breakdown-label">{dim_name}</span>'
            f'<div class="ds-breakdown-track">'
            f'<div class="ds-breakdown-fill" style="width: {dim_val}%; background: {bar_color};"></div>'
            f'</div>'
            f'<span class="ds-breakdown-score">{dim_val:.1f} / 100</span>'
            f'</div>'
        )
        breakdown_html_rows.append(row_html)

    breakdown_combined = "".join(breakdown_html_rows)

    hero_html = (
        f'<div class="ds-quality-hero">'
        f'<div class="ds-quality-score-circle">'
        f'<div class="ds-quality-score-num" style="color: {status_color};">{score:.1f}</div>'
        f'<div class="ds-quality-score-label" style="color: {status_color};">{status}</div>'
        f'<div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Quality Index / 100</div>'
        f'</div>'
        f'<div class="ds-breakdown-bar-container">'
        f'<div style="font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 2px;">Quality Score Breakdown</div>'
        f'{breakdown_combined}'
        f'</div>'
        f'</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)


def _render_quality_kpis(report: Dict[str, Any], metadata: Dict[str, Any]) -> None:
    """Render top quality metric cards."""
    missing = report["missing_analysis"]
    duplicates = report["duplicate_analysis"]
    outliers = report["outlier_analysis"]
    problem_cols = [c for c in report["column_quality_scores"] if c["quality_score"] < 80.0]

    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        render_metric_card(
            label="Overall Score",
            value=f"{report['overall_score']:.1f}",
            status=report["status"]
        )
    with c2:
        miss_cnt = missing["total_missing_cells"]
        miss_pct = missing["missing_percentage"]
        render_metric_card(
            label="Missing Values",
            value=f"{miss_cnt:,}",
            change=f"{miss_pct:.1f}% rate",
            change_type="positive" if miss_cnt == 0 else "neutral",
            description=f"{missing['columns_affected_count']} col(s) affected",
            status="Health"
        )
    with c3:
        dup_cnt = duplicates["duplicate_rows"]
        dup_pct = duplicates["duplicate_percentage"]
        render_metric_card(
            label="Duplicate Records",
            value=f"{dup_cnt:,}",
            change=f"{dup_pct:.1f}% rate",
            change_type="positive" if dup_cnt == 0 else "negative",
            description="Unique" if dup_cnt == 0 else f"{dup_cnt} duplicates",
            status="Uniqueness"
        )
    with c4:
        render_metric_card(
            label="Problematic Columns",
            value=f"{len(problem_cols)}",
            description=f"of {metadata['total_columns']} total columns",
            status="Attention" if len(problem_cols) > 0 else "Clean"
        )


# =============================================================================
# TABS IMPLEMENTATION
# =============================================================================

def _render_tab_overview(report: Dict[str, Any]) -> None:
    """Render Overview Tab: main issues, problematic column ranking, recommendations."""
    col_issues, col_rankings = st.columns([6, 4], gap="large")

    with col_issues:
        render_section_header(
            title="Consolidated Quality Issues",
            subtitle="Prioritized list of detected data defects and structural warnings."
        )
        
        issues = report.get("issues", [])
        if not issues:
            render_notification(
                title="Zero Quality Issues Detected",
                message="Your dataset passed all completeness, consistency, and validity checks with full marks.",
                variant="success"
            )
        else:
            # Issue cards & summary table
            for iss in issues[:4]:
                sev = iss["severity"]
                variant = "error" if sev == "CRITICAL" else ("warning" if sev in ["HIGH", "MEDIUM"] else "info")
                render_notification(
                    title=f"[{sev}] {iss['column']}: {iss['issue']}",
                    message=iss["details"],
                    variant=variant
                )

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            # Full table view
            issue_df = pd.DataFrame([
                {
                    "Severity": i["severity"],
                    "Category": i["category"],
                    "Column": i["column"],
                    "Issue": i["issue"],
                    "Details": i["details"]
                }
                for i in issues
            ])
            st.dataframe(issue_df, use_container_width=True, hide_index=True)

    with col_rankings:
        render_section_header(
            title="Problematic Columns",
            subtitle="Columns ranked by cumulative quality penalty."
        )
        
        col_scores = report.get("column_quality_scores", [])
        if col_scores:
            rank_df = pd.DataFrame([
                {
                    "Column": c["column"],
                    "Score": f"{c['quality_score']:.1f}",
                    "Severity": c["severity"],
                    "Primary Issue": c["main_issue"]
                }
                for c in col_scores[:8]
            ])
            st.dataframe(rank_df, use_container_width=True, hide_index=True)


def _render_tab_missing(report: Dict[str, Any], theme: str) -> None:
    """Render Missing Values Tab with charts, filters, and 'Fix in Data Preparation' action."""
    missing = report["missing_analysis"]

    render_section_header(
        title="Missing Values Profiling",
        subtitle="Detailed analysis of null and empty records across dataset features."
    )

    m1, m2, m3 = st.columns(3)
    with m1:
        render_metric_card(
            label="Total Missing Cells",
            value=f"{missing['total_missing_cells']:,}",
            status="Cells"
        )
    with m2:
        render_metric_card(
            label="Overall Missing Rate",
            value=f"{missing['missing_percentage']:.2f}%",
            status="Rate"
        )
    with m3:
        render_metric_card(
            label="Affected Columns",
            value=f"{missing['columns_affected_count']}",
            status="Columns"
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Missing Bar Chart
    chart = generate_missing_bar_chart(missing["column_missing_details"], theme=theme)
    if chart:
        st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})
    else:
        render_notification(
            title="100% Complete Data",
            message="No missing values were detected in any feature of this dataset.",
            variant="success"
        )

    # ── Severity filter + Fix action ──────────────────────────────────────────
    col_details = missing["column_missing_details"]
    affected = [c for c in col_details if c["missing_count"] > 0]

    if affected:
        filter_col, _, action_col = st.columns([3, 3, 4], gap="small")
        with filter_col:
            severity_opts = ["All"] + sorted({c["severity"] for c in affected if c["severity"] != "Healthy"})
            selected_sev = st.selectbox(
                "Filter by severity",
                options=severity_opts,
                key="miss_severity_filter",
                label_visibility="collapsed",
            )
        with action_col:
            if st.button(
                "Fix Missing Values in Data Preparation →",
                key="miss_fix_prep_btn",
                type="primary",
                use_container_width=True,
            ):
                st.session_state["prep_suggested_action"] = "missing"
                st.session_state["current_page"] = "Data Preparation"
                st.rerun()

        # Apply filter
        filtered = affected if selected_sev == "All" else [c for c in affected if c["severity"] == selected_sev]

        if filtered:
            st.markdown("##### Column Missing Breakdown")
            table_data = pd.DataFrame([
                {
                    "Column Name": c["column_name"],
                    "Missing Count": f"{c['missing_count']:,}",
                    "Missing %": f"{c['missing_percentage']:.2f}%",
                    "Non-Missing Count": f"{c['non_missing_count']:,}",
                    "Severity": c["severity"]
                }
                for c in filtered
            ])
            st.dataframe(table_data, use_container_width=True, hide_index=True)
        else:
            st.info(f"No columns match severity '{selected_sev}'.")
    else:
        render_notification(
            title="100% Complete Data",
            message="No columns have missing values.",
            variant="success"
        )


def _render_tab_duplicates(report: Dict[str, Any]) -> None:
    """Render Duplicates Tab: duplicate rows, identical columns, and samples."""
    dup = report["duplicate_analysis"]

    render_section_header(
        title="Duplicate Analysis",
        subtitle="Row-level redundancy and column-level identical value checks."
    )

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        render_metric_card(label="Total Records", value=f"{dup['total_rows']:,}", status="Rows")
    with d2:
        render_metric_card(label="Duplicate Rows", value=f"{dup['duplicate_rows']:,}", status="Duplicates")
    with d3:
        render_metric_card(label="Unique Records", value=f"{dup['unique_rows']:,}", status="Unique")
    with d4:
        render_metric_card(label="Duplication Rate", value=f"{dup['duplicate_percentage']:.2f}%", status="Rate")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Duplicate Columns Check
    dup_cols = dup.get("duplicate_columns", [])
    if dup_cols:
        render_notification(
            title=f"{len(dup_cols)} Duplicate Column Pair(s) Detected",
            message="Identical values found across: " + ", ".join([f"'{c1}' ↔ '{c2}'" for c1, c2 in dup_cols]),
            variant="warning"
        )
    else:
        render_notification(
            title="No Duplicate Columns",
            message="All features contain distinct data distributions.",
            variant="success"
        )

    # Duplicate Row Samples
    samples = dup.get("duplicate_samples")
    if samples is not None and len(samples) > 0:
        st.markdown(f"##### Duplicate Rows Preview ({len(samples):,} occurrences)")
        st.dataframe(samples, use_container_width=True, hide_index=False)

    # ── Fix action ────────────────────────────────────────────────────────────
    if dup.get("duplicate_rows", 0) > 0:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        _, fix_col = st.columns([6, 4], gap="small")
        with fix_col:
            if st.button(
                "Remove Duplicates in Data Preparation →",
                key="dup_fix_prep_btn",
                type="primary",
                use_container_width=True,
            ):
                st.session_state["prep_suggested_action"] = "duplicates"
                st.session_state["current_page"] = "Data Preparation"
                st.rerun()


def _render_tab_consistency(report: Dict[str, Any]) -> None:
    """Render Consistency Tab: empty columns, constant values, type anomalies."""
    cons = report["consistency_analysis"]

    render_section_header(
        title="Data Consistency & Structure",
        subtitle="Verification of schema uniformity, variance, and data type integrity."
    )

    # 1. Empty Columns
    empty_cols = cons.get("empty_columns", [])
    if empty_cols:
        render_notification(
            title=f"{len(empty_cols)} Completely Empty Column(s)",
            message="The following columns contain zero non-null records: " + ", ".join(empty_cols),
            variant="error"
        )

    # 2. Constant Columns
    const_cols = cons.get("constant_columns", [])
    if const_cols:
        render_notification(
            title=f"{len(const_cols)} Constant Single-Value Column(s)",
            message="Features with zero variance provide no statistical predictive value.",
            variant="warning"
        )
        const_df = pd.DataFrame([
            {
                "Column": c["column"],
                "Constant Value": c["constant_value"],
                "Non-Null Count": f"{c['non_null_count']:,}"
            }
            for c in const_cols
        ])
        st.dataframe(const_df, use_container_width=True, hide_index=True)

    # 3. Type Inconsistencies
    incons = cons.get("type_inconsistencies", [])
    if incons:
        render_notification(
            title=f"{len(incons)} Type Inconsistency Anomaly Detected",
            message="Columns contain mixed numbers, text strings, or unparseable formats.",
            variant="warning"
        )
        inc_df = pd.DataFrame([
            {
                "Column": i["column"],
                "Issue": i["issue"],
                "Inconsistent Count": f"{i['inconsistent_count']:,}",
                "Inconsistent %": f"{i['inconsistent_percentage']:.1f}%",
                "Sample Values": i["sample_values"]
            }
            for i in incons
        ])
        st.dataframe(inc_df, use_container_width=True, hide_index=True)

    if not empty_cols and not const_cols and not incons:
        render_notification(
            title="Consistent Schema Architecture",
            message="All columns exhibit expected variance, valid non-null contents, and homogeneous data types.",
            variant="success"
        )


def _render_tab_validity(report: Dict[str, Any]) -> None:
    """Render Validity Tab: whitespace strings, infinities, out-of-bounds metrics."""
    val = report["validity_analysis"]
    findings = val.get("invalid_findings", [])

    render_section_header(
        title="Validity & Value Sanity Checks",
        subtitle="Conservative checks for whitespace strings, infinite values, and unexpected negative measurements."
    )

    if not findings:
        render_notification(
            title="All Sanity Checks Passed",
            message="No infinite floats, blank whitespace strings, or out-of-bound values were detected.",
            variant="success"
        )
    else:
        for f in findings:
            sev = f.get("severity", "MEDIUM")
            variant = "error" if sev == "HIGH" else ("warning" if sev == "MEDIUM" else "info")
            render_notification(
                title=f"[{sev}] {f['column']}: {f['issue_type']}",
                message=f["description"],
                variant=variant
            )

        val_df = pd.DataFrame([
            {
                "Column": f["column"],
                "Issue": f["issue_type"],
                "Affected Count": f"{f['count']:,}",
                "Affected %": f"{f['percentage']:.2f}%",
                "Severity": f["severity"],
                "Details": f["description"]
            }
            for f in findings
        ])
        st.dataframe(val_df, use_container_width=True, hide_index=True)


def _render_tab_outliers(report: Dict[str, Any], theme: str) -> None:
    """Render Outliers Tab: IQR-based bounds, outlier counts, and rankings."""
    out = report["outlier_analysis"]
    col_outliers = out.get("column_outliers", [])

    render_section_header(
        title="Outlier Detection (IQR Method)",
        subtitle="Identification of extreme numeric values located outside [Q1 - 1.5×IQR, Q3 + 1.5×IQR]."
    )

    o1, o2 = st.columns(2)
    with o1:
        render_metric_card(
            label="Total Potential Outliers",
            value=f"{out['total_outliers']:,}",
            status="Count"
        )
    with o2:
        render_metric_card(
            label="Overall Outlier Rate",
            value=f"{out['outlier_rate']:.2f}%",
            status="Rate"
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    chart = generate_outlier_bar_chart(col_outliers, theme=theme)
    if chart:
        st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})

    if col_outliers:
        # ── Column selector filter ────────────────────────────────────────────
        filter_c1, _, action_c = st.columns([3, 3, 4], gap="small")
        col_names = [o["column"] for o in col_outliers]
        with filter_c1:
            selected_col = st.selectbox(
                "Filter by column",
                options=["All Columns"] + col_names,
                key="out_col_filter",
                label_visibility="collapsed",
            )
        with action_c:
            if st.button(
                "Handle Outliers in Data Preparation →",
                key="out_fix_prep_btn",
                type="primary",
                use_container_width=True,
            ):
                st.session_state["prep_suggested_action"] = "outliers"
                st.session_state["current_page"] = "Data Preparation"
                st.rerun()

        filtered_out = col_outliers if selected_col == "All Columns" else [o for o in col_outliers if o["column"] == selected_col]

        st.markdown("##### Outlier Bounds & Feature Breakdown")
        out_df = pd.DataFrame([
            {
                "Column Name": o["column"],
                "Outlier Count": f"{o['outlier_count']:,}",
                "Outlier %": f"{o['outlier_percentage']:.2f}%",
                "Lower Bound": f"{o['lower_bound']:,}",
                "Upper Bound": f"{o['upper_bound']:,}",
                "Min Value": f"{o['min_value']:,}",
                "Max Value": f"{o['max_value']:,}"
            }
            for o in filtered_out
        ])
        st.dataframe(out_df, use_container_width=True, hide_index=True)
    else:
        render_notification(
            title="Zero Extreme Outliers",
            message="All numeric features fall cleanly within standard interquartile bounds.",
            variant="success"
        )


def _render_next_actions(report: Dict[str, Any]) -> None:
    """Render recommended next action callouts and dynamic workflow navigation."""
    recommendations = report.get("recommendations", [])
    if recommendations:
        render_section_header(
            title="Audit Remediation Insights",
            subtitle="Suggested preparation steps based on audit findings."
        )
        for rec in recommendations:
            render_notification(
                title=rec["title"],
                message=rec["text"],
                variant=rec.get("variant", "info")
            )

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    render_ai_context_trigger("Explain quality results with AI", intent="quality_results", key="qual_ai_btn")

    # Dynamic Bottom Next Workflow Steps Section
    render_next_workflow_steps("Data Quality")



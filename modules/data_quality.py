"""
DATA STUDIO v2 — Data Quality Audit & Diagnostics (Module 4)
=============================================================================
Purpose: DETECT → MEASURE → EXPLAIN
Answers: "What problems exist in my dataset?"

Audits and summarizes:
- Missing values and completeness
- Duplicate rows and uniqueness
- Outliers and distribution health
- Invalid values and domain validity
- Type inconsistencies and structural anomalies

Decision-making, previews, and remediation workflows live inside Data Preparation.
"""
from typing import Optional, Dict, Any, List
import html
import pandas as pd
import streamlit as st

from modules.config import is_dataset_loaded, mark_workflow_step, log_activity
from modules.ui_components import (
    render_page_header,
    render_section_header,
    render_metric_card,
    render_notification,
    render_empty_state,
    render_ai_context_trigger,
    render_next_workflow_steps,
    get_icon_svg
)

from modules.data_quality_engine import (
    analyze_data_quality,
    generate_missing_bar_chart,
    generate_outlier_bar_chart
)

from modules.data_loader import (
    get_available_sample_datasets,
    load_sample_dataset_by_key,
    set_active_dataset
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
            description="Upload a CSV or Excel dataset or load a sample dataset to analyze its quality, completeness, and consistency.",
            icon="shield-check"
        )

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        render_section_header(
            title="Quick Start with Sample Data",
            subtitle="Select a pre-loaded business dataset to immediately explore the Data Quality workspace."
        )

        sample_catalog = get_available_sample_datasets()
        cols = st.columns(len(sample_catalog) if sample_catalog else 1)
        for idx, (key, info) in enumerate(sample_catalog.items()):
            with cols[idx]:
                st.markdown(f"**{info['name']}**")
                st.caption(info["description"])
                if st.button(f"Load {info['name']}", key=f"quality_sample_load_{key}", type="primary", use_container_width=True):
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
            if st.button("Upload Custom Dataset", key="quality_goto_dataset_btn", use_container_width=True):
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
    sig = f"{id(df)}_{len(df)}_{len(df.columns)}_{metadata.get('upload_timestamp', '')}"
    if st.session_state.get("_cached_quality_sig") == sig and st.session_state.get("_cached_quality_audit"):
        audit_report = st.session_state["_cached_quality_audit"]
    else:
        audit_report = analyze_data_quality(df, metadata)
        st.session_state["_cached_quality_sig"] = sig
        st.session_state["_cached_quality_audit"] = audit_report
    mark_workflow_step("quality", True)

    # 4. Standardized Page Subtitle
    render_page_header(
        title="Data Quality",
        subtitle="Multi-dimensional health audit, statistical anomaly detection, and issue diagnostics.",
        icon="shield-check"
    )

    # 5. Dataset Context Bar
    _render_context_bar(dataset_name, file_type, metadata)

    # 6. Hero Quality Score & Breakdown Card
    _render_quality_hero(audit_report)

    # 7. Quality KPI Summary Row
    _render_quality_kpis(audit_report, metadata)

    # 8. Detected Issues Summary & Data Preparation Handoff Banner
    _render_issues_summary_and_handoff(audit_report)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 9. Clean Diagnostic Data Quality Tabs (No Decision Queue tab)
    tab_overview, tab_missing, tab_duplicates, tab_outliers_validity = st.tabs([
        "OVERVIEW",
        "MISSING VALUES",
        "DUPLICATES",
        "OUTLIERS & VALIDITY"
    ])

    with tab_overview:
        _render_tab_overview(df, audit_report)

    with tab_missing:
        _render_tab_missing(df, audit_report, current_theme)

    with tab_duplicates:
        _render_tab_duplicates(df, audit_report)

    with tab_outliers_validity:
        _render_tab_outliers_and_validity(df, audit_report, current_theme)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # 10. Next Steps Navigation
    _render_next_actions(audit_report)


# =============================================================================
# CONTEXT & HERO RENDERERS
# =============================================================================

def _render_context_bar(name: str, file_type: str, metadata: Dict[str, Any]) -> None:
    """Render compact context bar with refresh and navigation actions."""
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
            if st.button("Refresh Audit", key="quality_refresh_btn", use_container_width=True):
                st.session_state["_cached_quality_sig"] = None
                st.session_state["_cached_quality_audit"] = None
                st.toast("Data quality audit recalculated.")
                st.rerun()
        with ac2:
            if st.button("Open Preparation", key="quality_goto_prep_btn", type="primary", use_container_width=True):
                st.session_state["current_page"] = "Data Preparation"
                st.rerun()


def _render_quality_hero(report: Dict[str, Any]) -> None:
    """Render prominent Quality Score gauge and 5-dimension breakdown bars."""
    score = report["overall_score"]
    status = report["status"]
    status_color = report["status_color"]
    breakdown = report["breakdown"]

    dim_colors = {
        "Completeness": "#3b82f6",
        "Uniqueness": "#10b981",
        "Consistency": "#8b5cf6",
        "Validity": "#f59e0b",
        "Outlier Health": "#06b6d4"
    }

    breakdown_html_rows = []
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
    problem_cols = [c for c in report["column_quality_scores"] if c["quality_score"] < 80.0]

    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        render_metric_card(
            label="Overall Score",
            value=f"{report['overall_score']:.1f}",
            description=f"Health Grade: {report['grade']}",
            status=report["status"]
        )
    with c2:
        miss_cnt = missing["total_missing_cells"]
        miss_pct = missing["missing_percentage"]
        human_miss = f"About {max(1, round(miss_pct))} in 100 cells empty" if miss_pct >= 1 else (f"{miss_cnt} empty cells" if miss_cnt > 0 else "100% complete")
        render_metric_card(
            label="Empty Values",
            value=f"{miss_cnt:,}",
            change=f"{miss_pct:.1f}% rate",
            change_type="positive" if miss_cnt == 0 else "neutral",
            description=human_miss,
            status="Health"
        )
    with c3:
        dup_cnt = duplicates["duplicate_rows"]
        dup_pct = duplicates["duplicate_percentage"]
        human_dup = f"About {max(1, round(dup_pct))} in 100 rows repeated" if dup_pct >= 1 else ("Zero repeated rows" if dup_cnt == 0 else f"{dup_cnt} repeated rows")
        render_metric_card(
            label="Repeated Records",
            value=f"{dup_cnt:,}",
            change=f"{dup_pct:.1f}% rate",
            change_type="positive" if dup_cnt == 0 else "negative",
            description=human_dup,
            status="Uniqueness"
        )
    with c4:
        render_metric_card(
            label="Problematic Columns",
            value=f"{len(problem_cols)}",
            description=f"of {metadata['total_columns']} total columns",
            status="Attention" if len(problem_cols) > 0 else "Clean"
        )


def _render_issues_summary_and_handoff(report: Dict[str, Any]) -> None:
    """Render structured issue count summary with clear handoff into Data Preparation."""
    missing = report["missing_analysis"]
    duplicates = report["duplicate_analysis"]
    outliers = report["outlier_analysis"]
    validity = report["validity_analysis"]

    miss_cnt = missing.get("total_missing_cells", 0)
    dup_cnt = duplicates.get("duplicate_rows", 0)
    out_cnt = outliers.get("total_outliers", 0)
    inv_cnt = validity.get("total_invalid_cells", 0)
    total_defects = miss_cnt + dup_cnt + out_cnt + inv_cnt

    st.markdown(
        f"""
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 18px; margin-top: 12px; margin-bottom: 8px; box-shadow: var(--shadow-xs);">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                <div>
                    <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--accent);">
                        Quality Audit Findings
                    </div>
                    <div style="font-size: 14px; font-weight: 600; color: var(--text-primary); margin-top: 2px;">
                        <b>{miss_cnt:,}</b> missing cells · <b>{dup_cnt:,}</b> duplicate rows · <b>{out_cnt:,}</b> outliers · <b>{inv_cnt:,}</b> invalid values
                    </div>
                </div>
                <div>
                    <span style="font-size: 12px; color: var(--text-secondary); margin-right: 8px;">
                        {f'⚡ {total_defects:,} total quality defects detected.' if total_defects > 0 else '✓ No critical defects found.'}
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if total_defects > 0:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if miss_cnt > 0 and st.button(f"Fix Missing Values ({miss_cnt:,}) →", key="btn_ho_missing", use_container_width=True):
                st.session_state["prep_active_tab"] = "Missing Values"
                st.session_state["current_page"] = "Data Preparation"
                st.rerun()
        with c2:
            if dup_cnt > 0 and st.button(f"Review Duplicates ({dup_cnt:,}) →", key="btn_ho_dups", use_container_width=True):
                st.session_state["prep_active_tab"] = "Duplicate Rows"
                st.session_state["current_page"] = "Data Preparation"
                st.rerun()
        with c3:
            if (out_cnt > 0 or inv_cnt > 0) and st.button(f"Investigate Outliers ({out_cnt:,}) →", key="btn_ho_outliers", use_container_width=True):
                st.session_state["prep_active_tab"] = "Outliers & Validity"
                st.session_state["current_page"] = "Data Preparation"
                st.rerun()
        with c4:
            if st.button("Review & Fix All Issues →", key="btn_ho_all", type="primary", use_container_width=True):
                st.session_state["prep_active_tab"] = "Missing Values" if miss_cnt > 0 else ("Duplicate Rows" if dup_cnt > 0 else "Outliers & Validity")
                st.session_state["current_page"] = "Data Preparation"
                st.rerun()


# =============================================================================
# TAB 1: OVERVIEW & COLUMN QUALITY RANKINGS
# =============================================================================

def _render_tab_overview(df: pd.DataFrame, report: Dict[str, Any]) -> None:
    """Render overall quality findings, column health rankings, and recommendations summary."""
    render_section_header(
        title="Column Quality Health Rankings",
        subtitle="Ranked assessment of each column's completeness, uniqueness, validity, and consistency."
    )

    col_scores = report.get("column_quality_scores", [])
    if col_scores:
        cols_df = pd.DataFrame([
            {
                "Column Name": c["column"],
                "Quality Score": f"{c['quality_score']:.1f} / 100",
                "Health Tier": c["severity"],
                "Primary Finding": c["main_issue"]
            }
            for c in col_scores
        ])
        st.dataframe(cols_df, use_container_width=True, hide_index=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Key Quality Findings & Recommendations")

    recs = report.get("recommendations", [])
    if recs:
        for idx, rec in enumerate(recs):
            rec_c1, rec_c2 = st.columns([8, 4])
            with rec_c1:
                st.markdown(
                    f"""
                    <div style="background: var(--surface-secondary); border-left: 3px solid var(--accent); padding: 10px 14px; border-radius: 4px; margin-bottom: 8px;">
                        <div style="font-weight: 700; font-size: 13.5px; color: var(--text-primary);">{rec.get('title', '')}</div>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">{rec.get('text', '')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with rec_c2:
                st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                target = rec.get("target_page", "Data Preparation")
                if target == "Data Preparation":
                    btn_txt = "Review in Data Preparation →"
                    if st.button(btn_txt, key=f"rec_goto_prep_{idx}", use_container_width=True):
                        # Route smartly based on recommendation title
                        t_lower = rec.get("title", "").lower()
                        if "missing" in t_lower:
                            st.session_state["prep_active_tab"] = "Missing Values"
                        elif "deduplicate" in t_lower or "duplicate" in t_lower:
                            st.session_state["prep_active_tab"] = "Duplicate Rows"
                        elif "outlier" in t_lower:
                            st.session_state["prep_active_tab"] = "Outliers & Validity"
                        st.session_state["current_page"] = "Data Preparation"
                        st.rerun()
    else:
        render_notification(
            title="Pristine Quality Status",
            message="No significant data defects were detected. Dataset is ready for exploration and analysis.",
            variant="success"
        )


# =============================================================================
# TAB 2: MISSING VALUES
# =============================================================================

def _render_tab_missing(df: pd.DataFrame, report: Dict[str, Any], theme: str) -> None:
    """Render Missing Values Tab with charts, column-level profiling, and handoff action."""
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

    # Missing breakdown table
    col_details = missing["column_missing_details"]
    affected = [c for c in col_details if c["missing_count"] > 0]

    if affected:
        st.markdown("##### Column Missing Breakdown")
        table_data = pd.DataFrame([
            {
                "Column Name": c["column_name"],
                "Missing Count": f"{c['missing_count']:,}",
                "Missing %": f"{c['missing_percentage']:.2f}%",
                "Non-Missing Count": f"{c['non_missing_count']:,}",
                "Severity": c["severity"]
            }
            for c in affected
        ])
        st.dataframe(table_data, use_container_width=True, hide_index=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        ho_c1, ho_c2, _ = st.columns([4, 4, 4])
        with ho_c1:
            if st.button("Fix Missing Values in Data Preparation →", key="btn_fix_missing_tab_ho", type="primary", use_container_width=True):
                st.session_state["prep_active_tab"] = "Missing Values"
                st.session_state["current_page"] = "Data Preparation"
                st.rerun()


# =============================================================================
# TAB 3: DUPLICATES
# =============================================================================

def _render_tab_duplicates(df: pd.DataFrame, report: Dict[str, Any]) -> None:
    """Render Duplicates Tab: row-level duplicate analysis, key inspection, and handoff action."""
    dup = report["duplicate_analysis"]

    render_section_header(
        title="Duplicate & Key Analysis",
        subtitle="Row-level exact redundancy and entity identifier distinction."
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

    if dup["duplicate_rows"] > 0:
        render_notification(
            title=f"{dup['duplicate_rows']:,} Exact Duplicate Rows Detected ({dup['duplicate_percentage']:.2f}%)",
            message="These records are identical across all available columns and therefore do not provide additional information.",
            variant="warning"
        )
        if dup.get("duplicate_samples") is not None:
            st.markdown("##### Sample Duplicate Records")
            st.dataframe(dup["duplicate_samples"].head(8), use_container_width=True, hide_index=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        ho_c1, ho_c2, _ = st.columns([4, 4, 4])
        with ho_c1:
            if st.button("Review Duplicates in Data Preparation →", key="btn_fix_dup_tab_ho", type="primary", use_container_width=True):
                st.session_state["prep_active_tab"] = "Duplicate Rows"
                st.session_state["current_page"] = "Data Preparation"
                st.rerun()
    else:
        render_notification(
            title="Zero Duplicate Records",
            message="Every row in the dataset represents a unique observation.",
            variant="success"
        )


# =============================================================================
# TAB 4: OUTLIERS & VALIDITY
# =============================================================================

def _render_tab_outliers_and_validity(df: pd.DataFrame, report: Dict[str, Any], theme: str) -> None:
    """Render Outliers, Validity, and Type Inconsistencies."""
    outlier_analysis = report["outlier_analysis"]
    validity = report["validity_analysis"]

    render_section_header(
        title="Outlier Health & Value Validity",
        subtitle="Distribution tail anomalies, negative values, and mixed-type formatting checks."
    )

    o1, o2, o3 = st.columns(3)
    with o1:
        render_metric_card(label="Outlier Health Score", value=f"{report['breakdown'].get('Outlier Health', 100):.1f}", status="Score")
    with o2:
        render_metric_card(label="Total Outlier Cells", value=f"{outlier_analysis.get('total_outliers', 0):,}", status="Outliers")
    with o3:
        render_metric_card(label="Invalid Cells", value=f"{validity.get('total_invalid_cells', 0):,}", status="Invalid")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Outliers Chart
    out_chart = generate_outlier_bar_chart(outlier_analysis.get("column_outliers", []), theme=theme)
    if out_chart:
        st.plotly_chart(out_chart, use_container_width=True, config={"displayModeBar": False})

    # Validity Findings
    inv_findings = validity.get("invalid_findings", [])
    if inv_findings:
        st.markdown("##### Value Validity Findings")
        st.dataframe(pd.DataFrame(inv_findings), use_container_width=True, hide_index=True)

    out_cnt = outlier_analysis.get("total_outliers", 0)
    inv_cnt = validity.get("total_invalid_cells", 0)
    if out_cnt > 0 or inv_cnt > 0:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        ho_c1, ho_c2, _ = st.columns([4, 4, 4])
        with ho_c1:
            if st.button("Investigate in Data Preparation →", key="btn_fix_outlier_tab_ho", type="primary", use_container_width=True):
                st.session_state["prep_active_tab"] = "Outliers & Validity"
                st.session_state["current_page"] = "Data Preparation"
                st.rerun()


# =============================================================================
# NEXT WORKFLOW NAVIGATION
# =============================================================================

def _render_next_actions(report: Dict[str, Any]) -> None:
    """Render contextual AI trigger and standardized bottom workflow navigation."""
    render_ai_context_trigger("Explain quality results with AI", intent="quality_results", key="qual_ai_btn")
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    render_next_workflow_steps("Data Quality")

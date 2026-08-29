"""
DATA STUDIO v2 — Intelligent Data Quality Decision Engine (Module 4)
=============================================================================
Transform passive problem detection into an intelligent decision advisor:
- Statistical profiling (skewness, distribution shape, outliers, mode dominance)
- Deterministic decision logic (answers What, Why, Severity, Action, Alternatives, Impact)
- Confidence, Risk, and Expected Impact assessments
- Interactive before/after preview before applying transformations
- Safe non-destructive execution with pristine original preservation
- Automated post-transformation verification check and quality score improvement
- Complete transformation history and audit trail with 1-click revert
"""
from typing import Optional, Dict, Any, List
import datetime
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
    render_next_step_banner,
    render_ai_context_trigger,
    render_next_workflow_steps,
    get_icon_svg
)

from modules.data_quality_engine import (
    analyze_data_quality,
    generate_missing_bar_chart,
    generate_outlier_bar_chart,
    generate_quality_decision_plan,
    preview_decision_transformation,
    apply_decision_transformation,
    verify_decision_impact
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
    sig = f"{id(df)}_{len(df)}_{len(df.columns)}_{metadata.get('upload_timestamp', '')}"
    if st.session_state.get("_cached_quality_sig") == sig and st.session_state.get("_cached_quality_audit"):
        audit_report = st.session_state["_cached_quality_audit"]
    else:
        audit_report = analyze_data_quality(df, metadata)
        st.session_state["_cached_quality_sig"] = sig
        st.session_state["_cached_quality_audit"] = audit_report
    mark_workflow_step("quality", True)

    # 4. Standardized Page Subtitle (beneath the compact Top Header)
    render_page_header(
        title="Data Quality",
        subtitle="Intelligent Data Quality Advisor — statistical anomaly investigation, decision reasoning, and verified remediation.",
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
    tab_decisions, tab_missing, tab_duplicates, tab_outliers_validity, tab_history = st.tabs([
        "⚡ DECISION QUEUE",
        "MISSING VALUES",
        "DUPLICATES",
        "OUTLIERS & VALIDITY",
        "TRANSFORMATION HISTORY"
    ])

    with tab_decisions:
        _render_tab_decision_queue(df, audit_report)

    with tab_missing:
        _render_tab_missing(df, audit_report, current_theme)

    with tab_duplicates:
        _render_tab_duplicates(df, audit_report)

    with tab_outliers_validity:
        _render_tab_outliers_and_validity(df, audit_report, current_theme)

    with tab_history:
        _render_tab_transformation_history(df, audit_report)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # 9. Next Steps Navigation
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
            if st.button("Open Preparation", key="quality_goto_prep_btn", use_container_width=True):
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
# TAB 1: INTELLIGENT DECISION QUEUE (THE CORE ADVISOR)
# =============================================================================

def _render_tab_decision_queue(df: pd.DataFrame, report: Dict[str, Any]) -> None:
    """Render Prioritized Intelligent Decision Queue with interactive cards and preview modals."""
    render_section_header(
        title="Intelligent Decision Queue",
        subtitle="Statistical investigation, deterministic decision logic, ranked alternatives, and 1-click remediation."
    )

    decisions: List[Dict[str, Any]] = report.get("decision_plan", [])

    if not decisions:
        render_notification(
            title="Zero Quality Defects Found",
            message="Your dataset is in pristine analytical condition. No missing values, exact duplicates, or structural anomalies were detected.",
            variant="success"
        )
        return

    # ── Filter Bar ───────────────────────────────────────────────────────────
    sev_counts = {
        "CRITICAL": sum(1 for d in decisions if d["severity"] == "CRITICAL"),
        "HIGH": sum(1 for d in decisions if d["severity"] == "HIGH"),
        "MEDIUM": sum(1 for d in decisions if d["severity"] == "MEDIUM"),
        "LOW": sum(1 for d in decisions if d["severity"] in ["LOW", "INFO"])
    }

    f1, f2 = st.columns([6, 4])
    with f1:
        filter_opts = [
            f"All Decisions ({len(decisions)})",
            f"Critical ({sev_counts['CRITICAL']})",
            f"High ({sev_counts['HIGH']})",
            f"Medium ({sev_counts['MEDIUM']})",
            f"Low & Review ({sev_counts['LOW']})"
        ]
        selected_filter = st.selectbox(
            "Filter decisions by priority",
            options=filter_opts,
            key="decision_queue_filter",
            label_visibility="collapsed"
        )

    with f2:
        search_query = st.text_input(
            "Search column or issue",
            placeholder="Search column (e.g. Age, Income)...",
            key="decision_search_input",
            label_visibility="collapsed"
        )

    # Filter decision list
    filtered_decisions = decisions
    if "Critical (" in selected_filter:
        filtered_decisions = [d for d in decisions if d["severity"] == "CRITICAL"]
    elif "High (" in selected_filter:
        filtered_decisions = [d for d in decisions if d["severity"] == "HIGH"]
    elif "Medium (" in selected_filter:
        filtered_decisions = [d for d in decisions if d["severity"] == "MEDIUM"]
    elif "Low & Review" in selected_filter:
        filtered_decisions = [d for d in decisions if d["severity"] in ["LOW", "INFO"]]

    if search_query.strip():
        q = search_query.lower().strip()
        filtered_decisions = [d for d in filtered_decisions if q in d.get("column", "").lower() or q in d.get("title", "").lower() or q in d.get("recommended_action", "").lower()]

    st.markdown(f"<div style='font-size: 12px; color: var(--text-muted); margin-bottom: 12px;'>Showing <b>{len(filtered_decisions)}</b> prioritized decision items</div>", unsafe_allow_html=True)

    # ── Active Preview Drawer (if user clicked preview on any item) ───────────
    active_preview_id = st.session_state.get("_active_preview_decision_id")
    if active_preview_id:
        target_dec = next((d for d in decisions if d["id"] == active_preview_id), None)
        if target_dec:
            _render_decision_preview_modal(df, target_dec)

    # ── Decision Cards ───────────────────────────────────────────────────────
    for idx, dec in enumerate(filtered_decisions):
        _render_decision_card(df, dec, idx)


def _render_decision_card(df: pd.DataFrame, dec: Dict[str, Any], idx: int) -> None:
    """Render a single intelligent decision card with why-explanation and actions."""
    sev = dec.get("severity", "MEDIUM")
    sev_class = f"sev-{sev.lower()}"
    badge_class = f"ds-sev-{sev.lower()}"

    card_html = (
        f'<div class="ds-decision-card {sev_class}">'
        f'<div class="ds-decision-header">'
        f'<div class="ds-decision-title-group">'
        f'<span class="ds-sev-badge {badge_class}">{sev}</span>'
        f'<h4 class="ds-decision-title">{html.escape(dec.get("title", ""))}</h4>'
        f'</div>'
        f'<span class="ds-affected-badge">{dec.get("affected_label", "")}</span>'
        f'</div>'
        f'<div class="ds-recommendation-box">'
        f'<div class="ds-rec-top-row">'
        f'<span class="ds-rec-label">Recommended Action</span>'
        f'<div class="ds-rec-meta-badges">'
        f'<span class="ds-conf-badge">Confidence: <b>{dec.get("confidence", "HIGH")}</b></span>'
        f'<span class="ds-risk-badge">Risk: <b>{dec.get("risk", "LOW")}</b></span>'
        f'</div>'
        f'</div>'
        f'<div class="ds-rec-action-name">⚡ {html.escape(dec.get("recommended_action", ""))}</div>'
        f'<div class="ds-decision-why"><b>Why:</b> {html.escape(dec.get("why_reason", ""))}</div>'
        f'<div class="ds-decision-impact"><span>📊</span><span><b>Expected Impact:</b> {html.escape(dec.get("expected_impact", ""))}</span></div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    # Expanders for Alternatives and Evidence
    exp_col1, exp_col2 = st.columns(2)
    
    with exp_col1:
        with st.expander("Show Alternative Strategies", expanded=False):
            alts = dec.get("alternatives", [])
            if alts:
                alt_rows = []
                for a in alts:
                    rec_tag = " (Recommended)" if a.get("is_recommended") else ""
                    alt_rows.append(
                        f"<tr>"
                        f"<td class='ds-alt-rating'>{a.get('rating', '★★★☆☆')}</td>"
                        f"<td><b>{html.escape(a.get('label', ''))}{rec_tag}</b><br><span style='color:var(--text-muted);font-size:11px;'>{html.escape(a.get('why', ''))}</span></td>"
                        f"<td style='font-size:11px;color:var(--text-muted);'>{html.escape(a.get('trade_off', ''))}</td>"
                        f"</tr>"
                    )
                table_html = (
                    f"<table class='ds-alt-table'>"
                    f"<thead><tr><th>Rating</th><th>Strategy</th><th>Trade-Off</th></tr></thead>"
                    f"<tbody>{''.join(alt_rows)}</tbody>"
                    f"</table>"
                )
                st.markdown(table_html, unsafe_allow_html=True)

    with exp_col2:
        with st.expander("Technical Distribution Evidence", expanded=False):
            ev = dec.get("evidence", {})
            if ev:
                ev_items = []
                for k, v in ev.items():
                    if isinstance(v, (int, float)):
                        ev_items.append({"Metric": k.replace("_", " ").title(), "Value": f"{v:,.2f}" if isinstance(v, float) else f"{v:,}"})
                    elif isinstance(v, str):
                        ev_items.append({"Metric": k.replace("_", " ").title(), "Value": v})
                if ev_items:
                    st.dataframe(pd.DataFrame(ev_items), use_container_width=True, hide_index=True)
                else:
                    st.caption("Standard profile evidence captured.")

    # Action Triggers
    act_c1, act_c2, _ = st.columns([3, 3, 6], gap="small")
    
    with act_c1:
        is_previewing = (st.session_state.get("_active_preview_decision_id") == dec["id"])
        btn_label = "✕ Close Preview" if is_previewing else "👁️ Preview Fix"
        if st.button(btn_label, key=f"preview_btn_{dec['id']}_{idx}", use_container_width=True):
            if is_previewing:
                st.session_state["_active_preview_decision_id"] = None
            else:
                st.session_state["_active_preview_decision_id"] = dec["id"]
            st.rerun()

    with act_c2:
        if st.button("⚡ Apply Fix", key=f"apply_btn_{dec['id']}_{idx}", type="primary", use_container_width=True):
            _execute_transformation(df, dec)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)


def _render_decision_preview_modal(df: pd.DataFrame, dec: Dict[str, Any]) -> None:
    """Render interactive before/after impact comparison drawer."""
    preview = preview_decision_transformation(df, dec)
    if not preview:
        return

    st.markdown(
        f"""
        <div class="ds-preview-modal-box">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                <div style="font-size: 14px; font-weight: 700; color: var(--accent);">
                    👁️ Transformation Preview: {html.escape(dec.get("title", ""))}
                </div>
                <span style="font-size: 11px; color: var(--text-muted); background: var(--surface-container-low); padding: 2px 8px; border-radius: 4px; border: 1px solid var(--border-light);">
                    Simulation Mode (Raw Dataset Untouched)
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 4 KPI comparison cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        r_delta = preview["row_delta"]
        delta_str = f"({r_delta:+d} rows)" if r_delta != 0 else "(Unchanged)"
        render_metric_card(
            label="Dataset Rows",
            value=f"{preview['rows_after']:,}",
            description=f"Before: {preview['rows_before']:,} {delta_str}",
            status="Rows"
        )
    with k2:
        m_delta = preview["missing_delta"]
        render_metric_card(
            label="Total Missing Cells",
            value=f"{preview['missing_after']:,}",
            change=f"{m_delta:+d} cells",
            change_type="positive" if m_delta < 0 else "neutral",
            description=f"Before: {preview['missing_before']:,}",
            status="Cells"
        )
    with k3:
        c_delta = preview["completeness_delta"]
        render_metric_card(
            label="Completeness",
            value=f"{preview['completeness_after']:.1f}%",
            change=f"{c_delta:+.1f}%",
            change_type="positive" if c_delta > 0 else "neutral",
            description=f"Before: {preview['completeness_before']:.1f}%",
            status="Health"
        )
    with k4:
        col_name = dec.get("column")
        s_after = preview.get("stat_after", {})
        s_before = preview.get("stat_before", {})
        if s_after and "median" in s_after:
            render_metric_card(
                label=f"{col_name} Median",
                value=f"{s_after['median']:,.2f}",
                description=f"Before: {s_before.get('median', 0.0):,.2f}",
                status="Metric"
            )
        else:
            render_metric_card(
                label="Columns",
                value=f"{preview['cols_after']}",
                description=f"Before: {preview['cols_before']}",
                status="Structure"
            )

    # Sample rows preview
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.markdown("##### Sample Transformed Data Preview")
    st.dataframe(preview["sample_after"].head(4), use_container_width=True, hide_index=True)

    # Approval Actions
    conf_c1, conf_c2, _ = st.columns([3, 3, 6])
    with conf_c1:
        if st.button("✓ Confirm & Apply Transformation", key="confirm_preview_apply_btn", type="primary", use_container_width=True):
            st.session_state["_active_preview_decision_id"] = None
            _execute_transformation(df, dec)
    with conf_c2:
        if st.button("✕ Dismiss Preview", key="dismiss_preview_btn", use_container_width=True):
            st.session_state["_active_preview_decision_id"] = None
            st.rerun()

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)


def _execute_transformation(df: pd.DataFrame, dec: Dict[str, Any], custom_strategy: Optional[str] = None) -> None:
    """Execute quality fix non-destructively, verify impact, and record in audit log."""
    transformed_df, meta = apply_decision_transformation(df, dec, custom_strategy=custom_strategy)

    # Verify quality impact
    impact = verify_decision_impact(df, transformed_df, dec)

    # Update session state working dataset
    st.session_state["dataset"] = transformed_df
    st.session_state["prep_working_df"] = transformed_df.copy(deep=True)
    
    # Invalidate cached quality audit so it re-audits immediately
    st.session_state["_cached_quality_sig"] = None
    st.session_state["_cached_quality_audit"] = None

    # Append to transformation history
    if "quality_audit_history" not in st.session_state:
        st.session_state["quality_audit_history"] = []
    
    audit_entry = {
        **meta,
        "score_before": impact["score_before"],
        "score_after": impact["score_after"],
        "score_delta": impact["score_delta"],
        "warnings": impact["warnings"]
    }
    st.session_state["quality_audit_history"].insert(0, audit_entry)

    # Also log to central activity
    log_activity(f"Data Quality Fix: {meta['description']}", "shield-check")

    st.toast(f"Transformation applied! Quality score: {impact['score_before']} → {impact['score_after']} (+{impact['score_delta']} pts)")
    st.rerun()


# =============================================================================
# TAB 2: MISSING VALUES
# =============================================================================

def _render_tab_missing(df: pd.DataFrame, report: Dict[str, Any], theme: str) -> None:
    """Render Missing Values Tab with charts and column-level profiling."""
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


# =============================================================================
# TAB 3: DUPLICATES
# =============================================================================

def _render_tab_duplicates(df: pd.DataFrame, report: Dict[str, Any]) -> None:
    """Render Duplicates Tab: row-level duplicate analysis and key inspection."""
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
            title=f"{dup['duplicate_rows']:,} Exact Duplicate Rows Found",
            message="These rows are 100% identical across all columns. You can remove them in the Decision Queue.",
            variant="warning"
        )
        if dup.get("duplicate_samples") is not None:
            st.markdown("##### Sample Duplicate Records")
            st.dataframe(dup["duplicate_samples"].head(8), use_container_width=True, hide_index=True)
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
    consistency = report["consistency_analysis"]

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


# =============================================================================
# TAB 5: TRANSFORMATION HISTORY & AUDIT TRAIL
# =============================================================================

def _render_tab_transformation_history(df: pd.DataFrame, report: Dict[str, Any]) -> None:
    """Render persistent transformation audit log with score deltas and 1-click revert."""
    render_section_header(
        title="Transformation Audit Trail",
        subtitle="Chronological record of verified data quality fixes applied to the active dataset."
    )

    history = st.session_state.get("quality_audit_history", [])

    if not history:
        render_empty_state(
            title="No Transformations Applied Yet",
            description="Apply recommended actions from the Decision Queue to see verified quality score improvements and audit logs here.",
            icon="shield-check"
        )
        return

    # Export actions
    exp_c1, exp_c2, _ = st.columns([3, 3, 6])
    with exp_c1:
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Export Prepared CSV",
            data=csv_bytes,
            file_name="prepared_dataset.csv",
            mime="text/csv",
            key="export_prepared_csv_btn",
            use_container_width=True
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    for idx, item in enumerate(history):
        delta = item.get("score_delta", 0.0)
        delta_tag = f"<span class='ds-preview-delta-positive'>+{delta:.1f} Quality Score</span>" if delta > 0 else ""
        
        entry_html = (
            f"<div class='ds-audit-entry'>"
            f"<div class='ds-audit-entry-left'>"
            f"<div class='ds-audit-entry-title'>⚡ {html.escape(item.get('description', 'Remediation Applied'))} {delta_tag}</div>"
            f"<div class='ds-audit-entry-meta'>{item.get('timestamp', '')} · Column: <b>{html.escape(item.get('column', 'Dataset'))}</b> · Strategy: {item.get('strategy', '')}</div>"
            f"<div style='font-size: 11.5px; color: var(--text-secondary); margin-top: 2px;'>{html.escape(item.get('reason', ''))}</div>"
            f"</div>"
            f"</div>"
        )
        st.markdown(entry_html, unsafe_allow_html=True)
        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)


# =============================================================================
# NEXT WORKFLOW NAVIGATION
# =============================================================================

def _render_next_actions(report: Dict[str, Any]) -> None:
    """Render contextual workflow next actions."""
    score = report["overall_score"]
    
    if score >= 85.0:
        title = "Quality Validated — Ready for Exploratory Analysis"
        primary_page = "EDA"
        secondary_page = "Visualization"
        desc = "Your dataset quality is solid (Quality Score ≥ 85). Proceed to Exploratory Data Analysis or build visualizations."
    else:
        title = "Quality Remediation Recommended"
        primary_page = "Data Preparation"
        secondary_page = "EDA"
        desc = "Apply prioritized recommendations from the Decision Queue or use Data Preparation to clean anomalies."

    render_next_step_banner(
        title=title,
        recommendation=desc,
        primary_action_label=f"Open {primary_page} →",
        target_page=primary_page,
        key_prefix="quality_next_step",
        suggested_actions=[{"label": f"Explore {secondary_page}", "page": secondary_page}]
    )


    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    render_ai_context_trigger("Explain quality results with AI", intent="quality_results", key="qual_ai_btn")

    # Dynamic Bottom Next Workflow Steps Section
    render_next_workflow_steps("Data Quality")




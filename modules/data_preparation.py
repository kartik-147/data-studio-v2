"""
DATA STUDIO v2 — Interactive Data Preparation & Remediation Studio (Module 5)
=============================================================================
Purpose: INVESTIGATE → RECOMMEND → DECIDE → PREVIEW → APPLY → VERIFY
The central intelligent remediation and decision-making workspace.

Sections:
1. Missing Values (Intelligent Decision Cards, Alternatives, Simulation Preview, Imputation)
2. Duplicate Rows (Deduplication Decision, Alternatives, Simulation Preview, Removal)
3. Outliers & Validity (Domain-aware Outlier Review, Winsorizing/Capping, Value Validity)
4. Transformations (Columns, Filters, Sorting, Text Cleaning, Dates & Math Derivations)
5. Preparation History (Audit Timeline, Verified Quality Improvement, 1-Click Undo, Export)
"""
from typing import Optional, Dict, Any, List, Tuple
import datetime
import html
import pandas as pd
import numpy as np
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
    get_icon_svg,
    get_type_badge_html
)

from modules.data_loader import (
    create_dataset_metadata,
    get_available_sample_datasets,
    load_sample_dataset_by_key,
    set_active_dataset,
    detect_column_type
)

from modules.data_preparation_engine import (
    get_missing_values_summary,
    handle_missing_values,
    get_duplicates_info,
    remove_duplicates,
    rename_column,
    drop_columns,
    reorder_columns,
    cast_column_type,
    apply_filters,
    sort_dataset,
    get_outliers_profile,
    handle_outliers,
    clean_text_column,
    extract_date_components,
    derive_column_arithmetic,
    export_prepared_csv,
    export_prepared_excel
)

from modules.data_quality_engine import (
    investigate_column_distribution,
    generate_missing_value_decision,
    generate_duplicate_decision,
    generate_outlier_decision,
    generate_invalid_and_type_decisions,
    preview_decision_transformation,
    apply_decision_transformation,
    verify_decision_impact,
    analyze_data_quality
)


# =============================================================================
# SESSION STATE INITIALIZATION & HISTORY MANAGEMENT
# =============================================================================

def _init_prep_state() -> None:
    """Initialize Data Preparation session state variables."""
    if "prep_working_df" not in st.session_state or st.session_state["prep_working_df"] is None:
        source_df = st.session_state.get("original_dataset")
        if source_df is None:
            source_df = st.session_state.get("dataset")
        st.session_state["prep_working_df"] = source_df.copy(deep=True) if source_df is not None else None

    if "prep_history" not in st.session_state:
        st.session_state["prep_history"] = []

    if "prep_undo_stack" not in st.session_state:
        st.session_state["prep_undo_stack"] = []

    if "prep_active_dataset_mode" not in st.session_state:
        st.session_state["prep_active_dataset_mode"] = "Original"

    if "prep_active_filters" not in st.session_state:
        st.session_state["prep_active_filters"] = []

    if "prep_active_tab" not in st.session_state:
        st.session_state["prep_active_tab"] = "Missing Values"

    if "quality_audit_history" not in st.session_state:
        st.session_state["quality_audit_history"] = []


def _record_transformation(
    new_df: pd.DataFrame,
    trans_type: str,
    description: str,
    before_rows: int,
    before_cols: int,
    score_delta: float = 0.0,
    column: str = "Dataset",
    strategy: str = "",
    reason: str = ""
) -> None:
    """Snapshot previous state to undo stack and record transformation in history logs."""
    current_working = st.session_state.get("prep_working_df")
    if current_working is not None:
        undo_stack: List[pd.DataFrame] = st.session_state.get("prep_undo_stack", [])
        undo_stack.append(current_working.copy(deep=True))
        if len(undo_stack) > 10:
            undo_stack.pop(0)
        st.session_state["prep_undo_stack"] = undo_stack

    st.session_state["prep_working_df"] = new_df.copy(deep=True)

    after_rows = len(new_df)
    after_cols = len(new_df.columns)
    hist_entry = {
        "id": f"tx_{len(st.session_state.get('prep_history', [])) + 1}",
        "type": trans_type,
        "description": description,
        "timestamp": datetime.datetime.now().strftime("%I:%M:%S %p"),
        "rows_before": before_rows,
        "rows_after": after_rows,
        "cols_before": before_cols,
        "cols_after": after_cols,
        "score_delta": score_delta,
        "column": column,
        "strategy": strategy,
        "reason": reason
    }

    st.session_state["prep_history"].insert(0, hist_entry)

    # Invalidate cached quality audit so any re-audits reflect the latest transformation
    st.session_state["_cached_quality_sig"] = None
    st.session_state["_cached_quality_audit"] = None

    # Central activity log
    log_activity(f"Data Prep: {description}", "sliders-horizontal")
    st.toast(f"Transformation applied: {description}")


def _undo_last_change() -> None:
    """Pop previous DataFrame state from undo stack."""
    undo_stack: List[pd.DataFrame] = st.session_state.get("prep_undo_stack", [])
    if undo_stack:
        prev_df = undo_stack.pop()
        st.session_state["prep_undo_stack"] = undo_stack
        st.session_state["prep_working_df"] = prev_df
        history = st.session_state.get("prep_history", [])
        if history:
            undone = history.pop(0)
            st.session_state["prep_history"] = history
            st.toast(f"Undone: {undone['description']}")
        # Invalidate quality cache
        st.session_state["_cached_quality_sig"] = None
        st.session_state["_cached_quality_audit"] = None
        st.rerun()


def _reset_all_changes() -> None:
    """Revert working DataFrame and active dataset to pristine original copy."""
    orig_df = st.session_state.get("original_dataset")
    if orig_df is not None:
        st.session_state["prep_working_df"] = orig_df.copy(deep=True)
        st.session_state["prep_history"] = []
        st.session_state["prep_undo_stack"] = []
        st.session_state["prep_active_filters"] = []
        st.session_state["dataset"] = orig_df.copy(deep=True)
        st.session_state["cleaned_dataset"] = None
        st.session_state["dataset_metadata"] = create_dataset_metadata(
            st.session_state["dataset"],
            st.session_state.get("dataset_name", "dataset.csv"),
            st.session_state.get("dataset_file_type", "CSV")
        )
        st.session_state["prep_active_dataset_mode"] = "Original"
        st.session_state["_cached_quality_sig"] = None
        st.session_state["_cached_quality_audit"] = None
        st.toast("Reset all changes! Restored original dataset.")
        st.rerun()


def _apply_prepared_to_analysis() -> None:
    """Promote prepared working dataset to active session dataset for all downstream modules."""
    working_df = st.session_state.get("prep_working_df")
    if working_df is not None:
        st.session_state["dataset"] = working_df.copy(deep=True)
        st.session_state["cleaned_dataset"] = working_df.copy(deep=True)
        st.session_state["dataset_metadata"] = create_dataset_metadata(
            working_df,
            st.session_state.get("dataset_name", "dataset.csv"),
            st.session_state.get("dataset_file_type", "CSV")
        )
        st.session_state["prep_active_dataset_mode"] = "Prepared"
        st.session_state["_cached_quality_sig"] = None
        st.session_state["_cached_quality_audit"] = None
        mark_workflow_step("prep", True)
        log_activity(f"Promoted prepared dataset ({len(working_df):,} rows × {len(working_df.columns)} cols) to active session", "sliders-horizontal")
        st.toast("Prepared dataset is now active across all Data Studio modules! ✓")
        st.rerun()


def _execute_decision_fix(
    df: pd.DataFrame,
    decision: Dict[str, Any],
    custom_strategy: Optional[str] = None
) -> None:
    """Execute decision remediation transformation, verify quality impact, and log."""
    b_rows = len(df)
    b_cols = len(df.columns)
    
    transformed_df, meta = apply_decision_transformation(df, decision, custom_strategy=custom_strategy)
    impact = verify_decision_impact(df, transformed_df, decision)
    
    _record_transformation(
        new_df=transformed_df,
        trans_type=decision.get("type", "remediation"),
        description=meta.get("description", "Quality fix applied"),
        before_rows=b_rows,
        before_cols=b_cols,
        score_delta=impact.get("score_delta", 0.0),
        column=meta.get("column", "Dataset"),
        strategy=meta.get("strategy", ""),
        reason=meta.get("reason", "")
    )
    st.session_state["_active_preview_decision_id"] = None
    st.rerun()


# =============================================================================
# MAIN PAGE ROUTER
# =============================================================================

def render_data_preparation_page() -> None:
    """Main entry point for Data Preparation (Module 5)."""
    # 1. Empty State Check
    if not is_dataset_loaded():
        render_page_header(
            title="Data Preparation",
            subtitle="Remediate missing values, remove duplicates, cap outliers, and prepare your dataset for analysis.",
            icon="sliders-horizontal"
        )
        render_empty_state(
            title="No dataset ready for preparation",
            description="Upload a CSV or Excel dataset to begin cleaning, filtering, and transforming your data.",
            icon="sliders-horizontal"
        )

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        render_section_header(
            title="Quick Start with Sample Data",
            subtitle="Select a pre-loaded business dataset to immediately explore the Data Preparation workspace."
        )

        sample_catalog = get_available_sample_datasets()
        cols = st.columns(len(sample_catalog) if sample_catalog else 1)
        for idx, (key, info) in enumerate(sample_catalog.items()):
            with cols[idx]:
                st.markdown(f"**{info['name']}**")
                st.caption(info["description"])
                if st.button(f"Load {info['name']}", key=f"prep_sample_load_{key}", type="primary", use_container_width=True):
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
            if st.button("Upload Custom Dataset", key="prep_goto_dataset_btn", use_container_width=True):
                st.session_state["current_page"] = "Dataset"
                st.rerun()
        return

    _init_prep_state()

    # ── Consume deep-link hint if set ────────────────────────────────────────
    prep_hint = st.session_state.get("prep_suggested_action")
    if prep_hint:
        if prep_hint == "missing":
            st.session_state["prep_active_tab"] = "Missing Values"
        elif prep_hint == "duplicates":
            st.session_state["prep_active_tab"] = "Duplicate Rows"
        elif prep_hint == "outliers":
            st.session_state["prep_active_tab"] = "Outliers & Validity"
        elif prep_hint == "types":
            st.session_state["prep_active_tab"] = "Transformations"
        st.session_state["prep_suggested_action"] = None

    orig_df: pd.DataFrame = st.session_state.get("original_dataset")
    working_df: pd.DataFrame = st.session_state.get("prep_working_df")
    dataset_name = st.session_state.get("dataset_name", "dataset.csv")
    file_type = st.session_state.get("dataset_file_type", "CSV")

    if working_df is None or orig_df is None:
        _init_prep_state()
        working_df = st.session_state.get("prep_working_df")
        orig_df = st.session_state.get("original_dataset")

    # 2. Standardized Page Header
    render_page_header(
        title="Data Preparation",
        subtitle="Remediate missing values, remove duplicates, investigate outliers, and execute verified transformations.",
        icon="sliders-horizontal"
    )

    # 3. Preparation Status Summary & Dataset Promotion Bar
    _render_preparation_summary_bar(orig_df, working_df, dataset_name, file_type)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 4. Standardized Analytical Tabs
    tab_missing, tab_dups, tab_outliers, tab_trans, tab_history = st.tabs([
        "MISSING VALUES",
        "DUPLICATE ROWS",
        "OUTLIERS & VALIDITY",
        "TRANSFORMATIONS",
        "PREPARATION HISTORY"
    ])

    with tab_missing:
        _render_section_missing_values(working_df)

    with tab_dups:
        _render_section_duplicates(working_df)

    with tab_outliers:
        _render_section_outliers_and_validity(working_df)

    with tab_trans:
        _render_section_transformations(working_df, dataset_name)

    with tab_history:
        _render_section_preparation_history(orig_df, working_df, dataset_name)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 5. Contextual AI & Bottom Workflow Navigation
    render_ai_context_trigger("Suggest cleaning transformations with AI", intent="data_prep_cleaning", key="prep_ai_btn")
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    render_next_workflow_steps("Data Preparation")


# =============================================================================
# SUMMARY BAR & ACTIVE DATASET PROMOTION
# =============================================================================

def _render_preparation_summary_bar(
    orig_df: pd.DataFrame,
    working_df: pd.DataFrame,
    dataset_name: str,
    file_type: str
) -> None:
    """Render top Preparation Status summary comparing original vs working dataset with promotion action."""
    orig_rows = len(orig_df) if orig_df is not None else 0
    orig_cols = len(orig_df.columns) if orig_df is not None else 0
    curr_rows = len(working_df) if working_df is not None else 0
    curr_cols = len(working_df.columns) if working_df is not None else 0

    history_len = len(st.session_state.get("prep_history", []))
    
    # Missing cells & Completeness
    orig_missing = int(orig_df.isna().sum().sum()) if orig_df is not None else 0
    orig_total_cells = orig_rows * orig_cols
    orig_completeness = float((1.0 - (orig_missing / orig_total_cells)) * 100) if orig_total_cells > 0 else 100.0

    curr_missing = int(working_df.isna().sum().sum()) if working_df is not None else 0
    curr_total_cells = curr_rows * curr_cols
    curr_completeness = float((1.0 - (curr_missing / curr_total_cells)) * 100) if curr_total_cells > 0 else 100.0

    # Duplicates
    orig_dups = int(orig_df.duplicated().sum()) if orig_df is not None else 0
    curr_dups = int(working_df.duplicated().sum()) if working_df is not None else 0

    # Initial detected vs resolved issues count
    initial_issues = orig_missing + orig_dups
    resolved_issues = max(0, initial_issues - (curr_missing + curr_dups))
    pending_review = curr_missing + curr_dups

    active_mode = st.session_state.get("prep_active_dataset_mode", "Original")

    # Banner with Status and Promote Action
    col_status, col_action = st.columns([7, 5])
    with col_status:
        badge_cls = "ds-badge-numeric" if active_mode == "Prepared" else "ds-badge-neutral"
        banner_html = (
            f'<div class="ds-active-banner" style="margin-bottom: 12px; padding: 10px 16px;">'
            f'<div class="ds-active-banner-left">'
            f'<div class="ds-brand-badge" style="background: var(--accent);">{file_type[0] if file_type else "P"}</div>'
            f'<div>'
            f'<div class="ds-active-banner-name" style="font-size: 15px;">{html.escape(dataset_name)}</div>'
            f'<div class="ds-active-banner-meta" style="font-size: 12px;">'
            f'{curr_rows:,} rows · {curr_cols} columns · <span class="ds-badge {badge_cls}" style="font-size: 11px;">{active_mode} Dataset</span> · {history_len} transformations applied'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(banner_html, unsafe_allow_html=True)

    with col_action:
        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
        ac1, ac2 = st.columns(2)
        with ac1:
            if st.button("Reset Changes", key="prep_reset_btn", disabled=(history_len == 0), use_container_width=True, help="Revert all transformations and restore original dataset"):
                st.session_state["prepared_dataset"] = orig_df.copy(deep=True)
                st.session_state["prep_history"] = []
                st.session_state["prep_active_dataset_mode"] = "Original"
                st.toast("Reverted all transformations. Original dataset restored.")
                st.rerun()
        with ac2:
            if st.button("Apply to Analysis", key="btn_apply_prepared_analysis", type="primary", use_container_width=True, help="Promote prepared dataset to all analysis modules"):
                _apply_prepared_to_analysis()

    # 4 Preparation Status KPI Summary Cards
    kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
    with kpi_c1:
        render_metric_card(
            label="Preparation Status",
            value=f"{resolved_issues:,} Resolved",
            change=f"{pending_review:,} Pending" if pending_review > 0 else "All Clean",
            change_type="neutral" if pending_review > 0 else "positive",
            description=f"Detected: {initial_issues:,} issues",
            status="Status"
        )
    with kpi_c2:
        row_delta = curr_rows - orig_rows
        render_metric_card(
            label="Dataset Rows",
            value=f"{curr_rows:,}",
            change=f"{row_delta:+,} rows" if row_delta != 0 else "Unchanged",
            change_type="positive" if row_delta >= 0 else "neutral",
            description=f"Original: {orig_rows:,}",
            status="Rows"
        )
    with kpi_c3:
        comp_delta = curr_completeness - orig_completeness
        render_metric_card(
            label="Completeness",
            value=f"{curr_completeness:.1f}%",
            change=f"{comp_delta:+.1f}%" if comp_delta != 0 else "Unchanged",
            change_type="positive" if comp_delta > 0 else "neutral",
            description=f"Before: {orig_completeness:.1f}%",
            status="Completeness"
        )
    with kpi_c4:
        render_metric_card(
            label="Duplicate Rows",
            value=f"{curr_dups:,}",
            change="Clean" if curr_dups == 0 else f"{curr_dups} remaining",
            change_type="positive" if curr_dups == 0 else "negative",
            description=f"Original: {orig_dups:,}",
            status="Uniqueness"
        )


# =============================================================================
# REUSABLE DECISION CARD & PREVIEW MODAL RENDERERS
# =============================================================================

def _render_explanation_level_selector() -> None:
    """Render the AI Explanation Level selector control (Beginner, Standard, Technical)."""
    if "ai_explanation_level" not in st.session_state:
        st.session_state["ai_explanation_level"] = "Beginner"

    lvl_c1, lvl_c2 = st.columns([5, 7])
    with lvl_c1:
        st.markdown(
            "<div style='font-size: 13px; font-weight: 600; color: var(--text-secondary); padding-top: 6px;'>"
            "<b>AI Data Mentor Mode:</b>"
            "</div>",
            unsafe_allow_html=True
        )
    with lvl_c2:
        current_lvl = st.session_state["ai_explanation_level"]
        opts = ["Beginner", "Standard", "Technical"]
        idx = opts.index(current_lvl) if current_lvl in opts else 0
        new_lvl = st.radio(
            "AI Explanation Level",
            options=opts,
            index=idx,
            horizontal=True,
            key="ai_explanation_level_radio",
            label_visibility="collapsed",
            help="Beginner uses simple language with no jargon; Standard provides analyst summaries; Technical includes full statistical metrics."
        )
        if new_lvl != current_lvl:
            st.session_state["ai_explanation_level"] = new_lvl
            st.rerun()


def _render_decision_card(
    df: pd.DataFrame,
    dec: Dict[str, Any],
    key_prefix: str,
    resolved_message: Optional[str] = None
) -> None:
    """Render a beginner-friendly AI Data Mentor decision card with adaptive explanation levels."""
    level = st.session_state.get("ai_explanation_level", "Beginner")
    sev = dec.get("severity", "MEDIUM")
    sev_class = f"sev-{sev.lower()}"
    badge_class = f"ds-sev-{sev.lower()}"

    # 1. Determine Title & Why based on Explanation Level
    if level == "Beginner":
        rec_action = dec.get("recommended_action_friendly") or dec.get("recommended_action", "")
        why_text = dec.get("why_beginner") or dec.get("why_reason", "")
    elif level == "Technical":
        rec_action = dec.get("recommended_action_technical") or dec.get("recommended_action", "")
        why_text = dec.get("why_technical") or dec.get("why_reason", "")
    else:  # Standard
        rec_action = dec.get("recommended_action_friendly") or dec.get("recommended_action", "")
        why_text = dec.get("why_standard") or dec.get("why_reason", "")

    # What We Found block
    found = dec.get("what_we_found", {})
    found_badge = found.get("badge", f"{sev} PRIORITY")
    found_primary = found.get("primary_text", dec.get("title", ""))
    found_secondary = found.get("secondary_text", dec.get("affected_label", ""))
    human_summary = found.get("human_summary", "")

    # What Will Happen items
    happen_items = dec.get("what_will_happen", [])
    if not happen_items and dec.get("expected_impact"):
        happen_items = [dec.get("expected_impact")]

    happen_html_list = "".join([
        f'<div class="ds-happen-item"><span class="ds-happen-check">✓</span><span>{html.escape(item)}</span></div>'
        for item in happen_items
    ])

    card_html = (
        f'<div class="ds-decision-card {sev_class}">'
        f'<div class="ds-mentor-found-box">'
        f'<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">'
        f'<span class="ds-mentor-found-badge">WHAT WE FOUND</span>'
        f'<span class="ds-sev-badge {badge_class}">{found_badge}</span>'
        f'</div>'
        f'<div class="ds-mentor-found-primary">{html.escape(found_primary)}</div>'
        f'<div class="ds-mentor-found-desc">'
        f'{html.escape(found_secondary)}'
        f'{f" · <b>{html.escape(human_summary)}</b>" if human_summary else ""}'
        f'</div>'
        f'</div>'
        f'<div class="ds-recommendation-box">'
        f'<div class="ds-rec-top-row">'
        f'<span class="ds-rec-label">OUR RECOMMENDATION</span>'
        f'<div class="ds-rec-meta-badges">'
        f'<span class="ds-conf-badge">Confidence: <b>{dec.get("confidence", "HIGH")}</b></span>'
        f'<span class="ds-risk-badge">Risk: <b>{dec.get("risk", "LOW")}</b></span>'
        f'</div>'
        f'</div>'
        f'<div class="ds-rec-action-name">{html.escape(rec_action)}</div>'
        f'<div class="ds-mentor-section-label" style="margin-top:10px;">WHY ARE WE RECOMMENDING THIS?</div>'
        f'<div class="ds-decision-why">{html.escape(why_text)}</div>'
        f'<div class="ds-mentor-section-label" style="margin-top:12px;">WHAT WILL HAPPEN?</div>'
        f'<div class="ds-mentor-happen-box" style="margin-top:4px; margin-bottom:4px;">'
        f'{happen_html_list}'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    # Action Triggers: Preview Fix vs Apply Fix
    act_c1, act_c2, _ = st.columns([3.5, 3.5, 5], gap="small")
    
    is_previewing = (st.session_state.get("_active_preview_decision_id") == dec["id"])
    with act_c1:
        btn_label = "Close Preview" if is_previewing else "Preview This Change"
        if st.button(btn_label, key=f"preview_btn_{key_prefix}_{dec['id']}", use_container_width=True):
            if is_previewing:
                st.session_state["_active_preview_decision_id"] = None
            else:
                st.session_state["_active_preview_decision_id"] = dec["id"]
            st.rerun()

    with act_c2:
        if st.button("Apply Recommendation", key=f"apply_btn_{key_prefix}_{dec['id']}", type="primary", use_container_width=True):
            _execute_decision_fix(df, dec)

    # Active Preview Drawer
    if is_previewing:
        _render_decision_preview_drawer(df, dec, key_prefix)

    # Collapsible 1: Why did AI choose this?
    ai_reason = dec.get("ai_reasoning_beginner") or "AI analyzed statistical distributions and edge boundaries to select this strategy."
    with st.expander("Why did AI choose this?", expanded=(level == "Beginner")):
        st.markdown(
            f"<div style='font-size: 13px; color: var(--text-secondary); line-height: 1.5; padding: 4px 0;'>"
            f"<b>AI Mentor Insight:</b> {html.escape(ai_reason)}"
            f"</div>",
            unsafe_allow_html=True
        )

    # Collapsible 2: Alternative Strategies
    with st.expander("Alternative Strategies", expanded=False):
        alts = dec.get("alternatives", [])
        if alts:
            alt_rows = []
            for a in alts:
                friendly_n = a.get("friendly_name") or a.get("label", "")
                tech_n = a.get("technical_name", "")
                tech_display = f" <span style='color:var(--text-muted); font-size:11px;'>({html.escape(tech_n)})</span>" if tech_n else ""
                rec_tag = " <span class='ds-sev-badge ds-sev-low' style='font-size:9px;'>RECOMMENDED</span>" if a.get("is_recommended") else ""
                desc = a.get("description") or a.get("why", "")
                
                alt_rows.append(
                    f"<tr>"
                    f"<td class='ds-alt-rating' style='width:90px;'>{a.get('rating', '★★★☆☆')}</td>"
                    f"<td><b>{html.escape(friendly_n)}</b>{tech_display}{rec_tag}<br><span style='color:var(--text-secondary);font-size:12px;'>{html.escape(desc)}</span></td>"
                    f"<td style='font-size:11.5px;color:var(--text-muted);width:200px;'>{html.escape(a.get('trade_off', 'None'))}</td>"
                    f"</tr>"
                )
            table_html = (
                f"<table class='ds-alt-table'>"
                f"<thead><tr><th>Rating</th><th>Strategy</th><th>Trade-Off</th></tr></thead>"
                f"<tbody>{''.join(alt_rows)}</tbody>"
                f"</table>"
            )
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.caption("No alternative strategies recorded for this recommendation.")

    # Collapsible 3: Technical details & evidence
    with st.expander("Technical details & evidence", expanded=(level == "Technical")):
        tech_ev = dec.get("technical_evidence") or {}
        if not tech_ev:
            ev = dec.get("evidence", {})
            tech_ev = {k.replace("_", " ").title(): f"{v:,.2f}" if isinstance(v, float) else str(v) for k, v in ev.items() if not isinstance(v, (pd.DataFrame, list))}
        
        if tech_ev:
            ev_df = pd.DataFrame([{"Metric": k, "Value": str(v)} for k, v in tech_ev.items()])
            st.dataframe(ev_df, use_container_width=True, hide_index=True)
        else:
            st.caption("Standard feature distribution profile recorded.")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)


def _render_decision_preview_drawer(df: pd.DataFrame, dec: Dict[str, Any], key_prefix: str) -> None:
    """Render interactive simulation preview comparing before vs after states."""
    preview = preview_decision_transformation(df, dec)
    if not preview:
        return

    st.markdown(
        f'<div class="ds-preview-modal-box">'
        f'<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">'
        f'<div style="font-size: 14px; font-weight: 700; color: var(--accent);">'
        f'Transformation Preview: {html.escape(dec.get("title", ""))}'
        f'</div>'
        f'<span style="font-size: 11px; color: var(--text-muted); background: var(--surface-container-low); padding: 2px 8px; border-radius: 4px; border: 1px solid var(--border-light);">'
        f'Simulation Mode (Raw Dataset Untouched)'
        f'</span>'
        f'</div>'
        f'</div>',
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
        elif s_after and "mean" in s_after:
            render_metric_card(
                label=f"{col_name} Mean",
                value=f"{s_after['mean']:,.2f}",
                description=f"Before: {s_before.get('mean', 0.0):,.2f}",
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
        if st.button("Confirm & Apply Fix", key=f"confirm_preview_apply_{key_prefix}_{dec['id']}", type="primary", use_container_width=True):
            _execute_decision_fix(df, dec)
    with conf_c2:
        if st.button("Dismiss Preview", key=f"dismiss_preview_{key_prefix}_{dec['id']}", use_container_width=True):
            st.session_state["_active_preview_decision_id"] = None
            st.rerun()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)


# =============================================================================
# SECTION 1: MISSING VALUES
# =============================================================================

def _render_section_missing_values(working_df: pd.DataFrame) -> None:
    """Render Missing Values section with manual controls first, followed by intelligent AI decision cards."""
    render_section_header(
        title="Manual Missing Value Imputation",
        subtitle="Directly apply batch imputations, custom override values, or removal strategies across selected columns."
    )

    missing_summary = get_missing_values_summary(working_df)
    affected_cols_df = missing_summary[missing_summary["Missing Count"] > 0]
    total_missing_cells = int(working_df.isna().sum().sum())

    # ── 1. MANUAL MISSING VALUE CONTROLS (COMES FIRST) ───────────────────────
    all_cols = list(working_df.columns)
    affected_col_names = list(affected_cols_df["Column"]) if not affected_cols_df.empty else all_cols
    default_selected = [affected_col_names[0]] if affected_col_names else []

    c1, c2, c3 = st.columns(3)
    with c1:
        target_cols = st.multiselect(
            "Target Column(s)",
            options=all_cols,
            default=default_selected,
            key="man_miss_cols",
            help="Select one or more columns to apply manual imputation or removal."
        )
    with c2:
        is_all_numeric = all(pd.api.types.is_numeric_dtype(working_df[c]) for c in target_cols) if target_cols else False
        strat_opts = [
            ("mean", "Mean Imputation"),
            ("median", "Median Imputation"),
            ("mode", "Mode Imputation"),
            ("zero", "Fill with 0 (Zero)"),
            ("unknown", "Fill with 'Unknown'"),
            ("ffill", "Forward Fill (ffill)"),
            ("bfill", "Backward Fill (bfill)"),
            ("custom", "Custom Fill Value"),
            ("drop_rows", "Drop Rows with Missing Values"),
            ("drop_cols", "Drop Selected Columns Entirely")
        ] if is_all_numeric else [
            ("mode", "Mode Imputation"),
            ("unknown", "Fill with 'Unknown'"),
            ("zero", "Fill with 0 (Zero)"),
            ("ffill", "Forward Fill (ffill)"),
            ("bfill", "Backward Fill (bfill)"),
            ("custom", "Custom Fill Value"),
            ("drop_rows", "Drop Rows with Missing Values"),
            ("drop_cols", "Drop Selected Columns Entirely")
        ]
        man_strat = st.selectbox(
            "Strategy",
            options=[s[0] for s in strat_opts],
            format_func=lambda k: dict(strat_opts).get(k, k),
            key="man_miss_strat"
        )
    with c3:
        custom_val = None
        if man_strat == "custom":
            custom_val = st.text_input("Custom Fill Value", value="0" if is_all_numeric else "Unknown", key="man_miss_custom_val")
        else:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    if target_cols:
        btn_col1, btn_col2 = st.columns([3, 7])
        with btn_col1:
            if st.button("Apply Manual Transformation", key="btn_apply_manual_missing", type="primary", use_container_width=True):
                b_rows = len(working_df)
                b_cols = len(working_df.columns)
                new_df, info = handle_missing_values(working_df, target_cols, man_strat, custom_value=custom_val)
                desc = f"Manual Fix: Resolved missing values in {', '.join(target_cols)} using {man_strat.replace('_', ' ').title()}"
                _record_transformation(new_df, "missing_values", desc, b_rows, b_cols, column=", ".join(target_cols), strategy=man_strat)
                st.rerun()

    st.markdown("<div style='height: 18px; border-bottom: 1px solid var(--border-light); margin-bottom: 18px;'></div>", unsafe_allow_html=True)

    # ── 2. AI SUGGESTIONS & INTELLIGENT DECISION CARDS (COMES AFTER) ────────
    render_section_header(
        title="AI-Powered Missing Value Suggestions",
        subtitle="Statistical recommendations and automated remediation decisions tailored to feature distributions."
    )

    _render_explanation_level_selector()

    if total_missing_cells == 0 or affected_cols_df.empty:
        render_notification(
            title="100% Complete Data",
            message="All columns in the prepared dataset are complete with zero missing values remaining.",
            variant="success"
        )
        return

    # Generate Decision Engine Recommendations for affected columns
    decisions = []
    for col in affected_cols_df["Column"]:
        miss_count = int(working_df[col].isna().sum())
        if miss_count > 0:
            prof = investigate_column_distribution(working_df[col], col, working_df)
            dec = generate_missing_value_decision(col, prof, working_df)
            if dec:
                decisions.append(dec)

    if decisions:
        for idx, dec in enumerate(decisions):
            _render_decision_card(working_df, dec, key_prefix=f"miss_{idx}")
    else:
        render_notification(
            title="No Pending Missing Value Actions",
            message="All columns meet high completeness standards.",
            variant="info"
        )


# =============================================================================
# SECTION 2: DUPLICATE ROWS
# =============================================================================

def _render_section_duplicates(working_df: pd.DataFrame) -> None:
    """Render Duplicate Rows section with manual tools first, followed by AI decision cards."""
    render_section_header(
        title="Manual Duplicate Rows Handling",
        subtitle="Manually configure deduplication across all columns or specific key identifiers, set retention rules, and preview duplicate records."
    )

    dup_info = get_duplicates_info(working_df)
    dup_cnt = dup_info["duplicate_count"]
    dup_pct = dup_info["duplicate_pct"]
    all_cols = list(working_df.columns)

    # ── 1. MANUAL DUPLICATE CONTROLS (COMES FIRST) ───────────────────────────
    c_scope, c_keep, c_action = st.columns([4, 4, 4])
    with c_scope:
        dedup_scope = st.radio(
            "Deduplication Scope",
            options=["All Columns (Exact Duplicate Rows)", "Specific Column Subset (Key Identifiers)"],
            key="man_dup_scope"
        )
    with c_keep:
        keep_choice = st.selectbox(
            "Retention Strategy",
            options=[("first", "Keep First Occurrence"), ("last", "Keep Last Occurrence")],
            format_func=lambda x: x[1],
            key="man_dup_keep"
        )
        keep_val = keep_choice[0]

    subset_selected = None
    if dedup_scope == "Specific Column Subset (Key Identifiers)":
        subset_selected = st.multiselect(
            "Select Key Identifier Columns",
            options=all_cols,
            default=[all_cols[0]] if all_cols else [],
            key="man_dup_subset_cols"
        )
        sub_info = get_duplicates_info(working_df, subset_cols=subset_selected) if subset_selected else dup_info
        active_dup_cnt = sub_info["duplicate_count"]
        active_dup_pct = sub_info["duplicate_pct"]
        active_dup_df = sub_info["duplicate_df"]
    else:
        active_dup_cnt = dup_cnt
        active_dup_pct = dup_pct
        active_dup_df = dup_info["duplicate_df"]

    with c_action:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        btn_label = f"Remove {active_dup_cnt:,} Duplicates" if active_dup_cnt > 0 else "Remove Duplicates"
        if st.button(btn_label, key="btn_apply_manual_dup", type="primary", disabled=(active_dup_cnt == 0), use_container_width=True):
            b_rows = len(working_df)
            b_cols = len(working_df.columns)
            new_df, info = remove_duplicates(working_df, subset_cols=subset_selected, keep=keep_val)
            col_desc = f"[{', '.join(subset_selected)}]" if subset_selected else "all columns"
            desc = f"Manual Fix: Removed {info['removed_count']:,} duplicate rows ({col_desc}, keep='{keep_val}')"
            _record_transformation(new_df, "duplicates", desc, b_rows, b_cols, column=", ".join(subset_selected) if subset_selected else "Dataset", strategy=f"dedup_{keep_val}")
            st.rerun()

    # Duplicate Records Preview
    if active_dup_cnt > 0:
        st.markdown(f"##### Duplicate Observations Preview ({active_dup_cnt:,} rows · {active_dup_pct:.1f}%)")
        st.dataframe(active_dup_df.head(15), use_container_width=True, hide_index=False)
    else:
        render_notification(
            title="Zero Duplicate Rows Detected",
            message="Every row in the dataset represents a unique observation under the current scope.",
            variant="success"
        )

    st.markdown("<div style='height: 18px; border-bottom: 1px solid var(--border-light); margin-bottom: 18px;'></div>", unsafe_allow_html=True)

    # ── 2. AI DEDUPLICATION SUGGESTIONS (COMES AFTER) ────────────────────────
    render_section_header(
        title="AI Deduplication Recommendation",
        subtitle="Automated uniqueness assessment and intelligent deduplication strategy."
    )

    _render_explanation_level_selector()

    if dup_cnt > 0:
        dup_dec = generate_duplicate_decision(dup_info, working_df)
        if dup_dec:
            _render_decision_card(working_df, dup_dec, key_prefix="dup_main")
    else:
        render_notification(
            title="Clean Uniqueness Health",
            message="No AI deduplication intervention required. All records are unique.",
            variant="success"
        )


# =============================================================================
# SECTION 3: OUTLIERS & VALIDITY
# =============================================================================

def _render_section_outliers_and_validity(working_df: pd.DataFrame) -> None:
    """Render Outliers & Validity section with manual tools first, followed by AI decision cards."""
    render_section_header(
        title="Manual Outlier Remediation",
        subtitle="Select a numeric feature to inspect its IQR distribution bounds, and apply Winsorization, trimming, or custom clipping."
    )

    numeric_cols = [c for c in working_df.columns if pd.api.types.is_numeric_dtype(working_df[c])]

    # ── 1. MANUAL OUTLIER CONTROLS (COMES FIRST) ─────────────────────────────
    if numeric_cols:
        c1, c2, c3 = st.columns(3)
        with c1:
            target_outlier_col = st.selectbox("Target Numeric Column", options=numeric_cols, key="man_outlier_col")

        prof = get_outliers_profile(working_df, target_outlier_col)
        out_cnt = prof["outlier_count"]
        lower_b = prof["lower_bound"]
        upper_b = prof["upper_bound"]

        with c2:
            out_strat = st.selectbox(
                "Remediation Method",
                options=[
                    ("cap_boundaries", "Cap at 1.5×IQR Boundaries (Winsorize)"),
                    ("remove_rows", "Drop Outlier Rows (Remove extremes)"),
                    ("custom_clip", "Custom Min / Max Range Clipping")
                ],
                format_func=lambda x: x[1],
                key="man_outlier_strat"
            )
            strat_val = out_strat[0]

        custom_min, custom_max = None, None
        with c3:
            if strat_val == "custom_clip":
                sub_c1, sub_c2 = st.columns(2)
                with sub_c1:
                    custom_min = st.number_input("Lower Cap (Min)", value=float(lower_b), key="man_outlier_custom_min")
                with sub_c2:
                    custom_max = st.number_input("Upper Cap (Max)", value=float(upper_b), key="man_outlier_custom_max")
            else:
                st.markdown(
                    f"<div style='font-size:12px; color:var(--text-secondary); padding-top:28px;'>"
                    f"1.5×IQR Bounds: <b>[{lower_b:,.2f}, {upper_b:,.2f}]</b> ({out_cnt:,} outliers)"
                    f"</div>",
                    unsafe_allow_html=True
                )

        btn_c1, btn_c2 = st.columns([3, 7])
        with btn_c1:
            if st.button("Apply Manual Outlier Fix", key="btn_apply_manual_outlier", type="primary", use_container_width=True):
                b_rows = len(working_df)
                b_cols = len(working_df.columns)
                if strat_val == "custom_clip":
                    new_df = working_df.copy(deep=True)
                    new_df[target_outlier_col] = new_df[target_outlier_col].clip(lower=custom_min, upper=custom_max)
                    desc = f"Manual Fix: Clipped '{target_outlier_col}' to custom range [{custom_min:,.2f}, {custom_max:,.2f}]"
                    _record_transformation(new_df, "outliers", desc, b_rows, b_cols, column=target_outlier_col, strategy="custom_clip")
                else:
                    new_df, info = handle_outliers(working_df, target_outlier_col, action=strat_val)
                    action_name = "Capped at IQR boundaries" if strat_val == "cap_boundaries" else "Removed outlier rows"
                    desc = f"Manual Fix: {action_name} in '{target_outlier_col}' ({info.get('affected', 0):,} outliers affected)"
                    _record_transformation(new_df, "outliers", desc, b_rows, b_cols, column=target_outlier_col, strategy=strat_val)
                st.rerun()

        if out_cnt > 0:
            with st.expander(f"Inspect Outlier Records in '{target_outlier_col}' ({out_cnt:,} rows)", expanded=False):
                st.dataframe(prof["outlier_df"].head(10), use_container_width=True)
    else:
        render_notification(
            title="No Numeric Columns",
            message="Outlier remediation tools apply only to numeric columns.",
            variant="info"
        )

    st.markdown("<div style='height: 18px; border-bottom: 1px solid var(--border-light); margin-bottom: 18px;'></div>", unsafe_allow_html=True)

    # ── 2. AI OUTLIER & VALIDITY RECOMMENDATIONS (COMES AFTER) ───────────────
    render_section_header(
        title="AI Outlier Recommendations",
        subtitle="Domain-aware AI reasoning based on distribution shape and statistical outlier severity."
    )

    _render_explanation_level_selector()

    outlier_decisions = []
    for col in numeric_cols:
        prof = investigate_column_distribution(working_df[col], col, working_df)
        o_dec = generate_outlier_decision(col, prof, working_df)
        if o_dec:
            outlier_decisions.append(o_dec)

    if outlier_decisions:
        for idx, o_dec in enumerate(outlier_decisions):
            _render_decision_card(working_df, o_dec, key_prefix=f"outlier_{idx}")
    else:
        render_notification(
            title="Clean Distribution Tails",
            message="No extreme statistical outliers detected across numeric features based on the 1.5×IQR boundary.",
            variant="success"
        )

    # 3. Value Validity Findings (Negative values, whitespace strings, mixed types)
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    render_section_header(
        title="AI Value Validity & Format Sanity Decisions",
        subtitle="Automated checks for negative quantities, unexpected whitespace, and mixed data types."
    )

    audit = analyze_data_quality(working_df)
    validity_decisions = generate_invalid_and_type_decisions(
        validity=audit.get("validity_analysis", {}),
        consistency=audit.get("consistency_analysis", {}),
        df=working_df
    )

    if validity_decisions:
        for idx, v_dec in enumerate(validity_decisions):
            _render_decision_card(working_df, v_dec, key_prefix=f"val_{idx}")
    else:
        render_notification(
            title="Value Validity Verified",
            message="All values adhere to semantic domain rules (e.g. non-negative quantities, clean strings, consistent data types).",
            variant="success"
        )


# =============================================================================
# SECTION 4: TRANSFORMATIONS
# =============================================================================

def _render_section_transformations(working_df: pd.DataFrame, dataset_name: str = "dataset.csv") -> None:
    """Render functional data transformation tools organized by sub-categories."""
    render_section_header(
        title="Transformations & Schema Operations",
        subtitle="Manage column names and data types, build visual filters, apply sorting, clean text, and derive new features."
    )

    sub_cols, sub_filters, sub_sort, sub_text, sub_dates, sub_preview = st.tabs([
        "COLUMNS & TYPES",
        "VISUAL FILTERS",
        "PERSISTENT SORTING",
        "TEXT CLEANING",
        "DATES & ARITHMETIC",
        "PREVIEW & EXPORT"
    ])

    all_cols = list(working_df.columns)
    numeric_cols = [c for c in working_df.columns if pd.api.types.is_numeric_dtype(working_df[c])]

    # ── Subtab 1: Columns & Types ────────────────────────────────────────────
    with sub_cols:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("##### Rename Column")
            col_to_rename = st.selectbox("Select Column", options=all_cols, key="trans_col_rename_sel")
            new_col_name = st.text_input("New Name", value=col_to_rename, key="trans_col_rename_val")
            if st.button("Apply Rename", key="btn_apply_rename_trans", type="primary"):
                b_rows = len(working_df)
                b_cols = len(working_df.columns)
                new_df, ok, msg = rename_column(working_df, col_to_rename, new_col_name)
                if ok:
                    _record_transformation(new_df, "rename_column", msg, b_rows, b_cols, column=col_to_rename, strategy="rename")
                    st.rerun()
                else:
                    st.error(msg)

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            st.markdown("##### Drop Column(s)")
            cols_to_drop = st.multiselect("Select Column(s) to Drop", options=all_cols, key="trans_col_drop_sel")
            if cols_to_drop and st.button(f"Confirm Drop {len(cols_to_drop)} Column(s)", key="btn_apply_drop_trans", type="primary"):
                b_rows = len(working_df)
                b_cols = len(working_df.columns)
                new_df, dropped = drop_columns(working_df, cols_to_drop)
                desc = f"Dropped column(s): {', '.join(dropped)}"
                _record_transformation(new_df, "drop_columns", desc, b_rows, b_cols, column=", ".join(dropped), strategy="drop")
                st.rerun()

        with col_c2:
            st.markdown("##### Safe Data Type Casting")
            col_to_cast = st.selectbox("Select Column to Cast", options=all_cols, key="trans_col_cast_sel")
            curr_type = str(working_df[col_to_cast].dtype)
            st.caption(f"Current Pandas Dtype: `{curr_type}`")
            target_type = st.selectbox("Target Data Type", options=["Numeric", "Integer", "Float", "String", "Category", "Boolean", "Datetime"], key="trans_col_cast_target")
            
            if st.button("Apply Type Conversion", key="btn_apply_cast_trans", type="primary"):
                b_rows = len(working_df)
                b_cols = len(working_df.columns)
                new_df, result = cast_column_type(working_df, col_to_cast, target_type)
                if result.get("success"):
                    desc = f"Cast column '{col_to_cast}' from {curr_type} to {target_type} ({result['converted']} converted, {result['coerced_na']} NA)"
                    _record_transformation(new_df, "cast_type", desc, b_rows, b_cols, column=col_to_cast, strategy=f"cast_{target_type}")
                    st.rerun()
                else:
                    st.error(f"Type conversion failed: {result.get('error')}")

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            st.markdown("##### Reorder Columns")
            new_order = st.multiselect("Set Display Order", options=all_cols, default=all_cols, key="trans_col_reorder_sel")
            if st.button("Apply Column Order", key="btn_apply_reorder_trans"):
                b_rows = len(working_df)
                b_cols = len(working_df.columns)
                new_df, ok = reorder_columns(working_df, new_order)
                if ok:
                    _record_transformation(new_df, "reorder_columns", "Reordered columns", b_rows, b_cols, strategy="reorder")
                    st.rerun()

    # ── Subtab 2: Visual Filters ─────────────────────────────────────────────
    with sub_filters:
        st.markdown("##### Rule-Based Visual Filter Builder")
        c1, c2, c3, c4 = st.columns([3, 3, 3, 3])
        with c1:
            f_col = st.selectbox("Filter Column", options=all_cols, key="trans_f_col")
        series = working_df[f_col]
        if pd.api.types.is_numeric_dtype(series):
            ops = ["Equals (=)", "Not Equals (!=)", "Greater Than (>)", "Greater or Equal (>=)", "Less Than (<)", "Less or Equal (<=)", "Between", "Is Null / Missing", "Is Not Null"]
        elif pd.api.types.is_datetime64_any_dtype(series):
            ops = ["Before (<)", "After (>)", "Equals", "Between", "Is Null / Missing", "Is Not Null"]
        else:
            ops = ["Equals", "Not Equals", "Contains", "Starts with", "Ends with", "Is one of", "Is Null / Missing", "Is Not Null"]

        with c2:
            f_op = st.selectbox("Operator", options=ops, key="trans_f_op")
        with c3:
            if f_op not in ["Is Null / Missing", "Is Not Null"]:
                if f_op == "Is one of":
                    f_val = st.text_input("Values (comma-separated)", key="trans_f_val_multi")
                elif pd.api.types.is_numeric_dtype(series):
                    min_v = float(series.dropna().min()) if not series.dropna().empty else 0.0
                    f_val = st.number_input("Value", value=min_v, key="trans_f_val_num")
                else:
                    f_val = st.text_input("Comparison Value", key="trans_f_val_str")
            else:
                f_val = None
        with c4:
            if f_op == "Between":
                if pd.api.types.is_numeric_dtype(series):
                    max_v = float(series.dropna().max()) if not series.dropna().empty else 100.0
                    f_val_end = st.number_input("End Value", value=max_v, key="trans_f_val_end_num")
                else:
                    f_val_end = st.text_input("End Value", key="trans_f_val_end_str")
            else:
                f_val_end = None

        if st.button("Apply Filter Rule", key="btn_apply_filter_trans", type="primary"):
            rule = {"column": f_col, "operator": f_op, "value": f_val, "value_end": f_val_end}
            b_rows = len(working_df)
            b_cols = len(working_df.columns)
            new_df, info = apply_filters(working_df, [rule])
            desc = f"Filtered '{f_col}' ({f_op} {f_val or ''}): kept {info['rows_after']:,} of {b_rows:,} rows"
            _record_transformation(new_df, "filter", desc, b_rows, b_cols, column=f_col, strategy="filter")
            st.rerun()

    # ── Subtab 3: Sorting ────────────────────────────────────────────────────
    with sub_sort:
        st.markdown("##### Multi-Column Persistent Sorting")
        sc1, sc2 = st.columns(2)
        with sc1:
            sort_cols = st.multiselect("Sort Columns (in priority order)", options=all_cols, default=[all_cols[0]] if all_cols else [], key="trans_sort_cols")
        with sc2:
            order_choice = st.radio("Direction", options=["Ascending (Low to High / A-Z)", "Descending (High to Low / Z-A)"], key="trans_sort_dir")
            is_asc = "Ascending" in order_choice

        if sort_cols and st.button("Apply Sort", key="btn_apply_sort_trans", type="primary"):
            b_rows = len(working_df)
            b_cols = len(working_df.columns)
            new_df, ok = sort_dataset(working_df, sort_cols, [is_asc] * len(sort_cols))
            if ok:
                desc = f"Sorted by {', '.join(sort_cols)} ({'Ascending' if is_asc else 'Descending'})"
                _record_transformation(new_df, "sort", desc, b_rows, b_cols, column=", ".join(sort_cols), strategy="sort")
                st.rerun()

    # ── Subtab 4: Text Cleaning ──────────────────────────────────────────────
    with sub_text:
        st.markdown("##### Text Case & String Cleaning")
        str_cols = [c for c in working_df.columns if not pd.api.types.is_numeric_dtype(working_df[c])]
        if str_cols:
            tc1, tc2 = st.columns(2)
            with tc1:
                target_str_col = st.selectbox("Select Text Column", options=str_cols, key="trans_text_col")
            with tc2:
                text_ops = st.multiselect(
                    "Operations",
                    options=["trim", "lower", "upper", "title", "remove_empty", "find_replace"],
                    default=["trim"],
                    format_func=lambda x: {
                        "trim": "Trim Whitespace",
                        "lower": "Lowercase",
                        "upper": "Uppercase",
                        "title": "Title Case",
                        "remove_empty": "Blank Strings to NA",
                        "find_replace": "Find and Replace"
                    }.get(x, x),
                    key="trans_text_ops"
                )

            find_val, replace_val = None, None
            if "find_replace" in text_ops:
                fr1, fr2 = st.columns(2)
                with fr1:
                    find_val = st.text_input("Find Substring", key="trans_text_find")
                with fr2:
                    replace_val = st.text_input("Replace With", key="trans_text_replace")

            if text_ops and st.button("Apply Text Cleaning", key="btn_apply_text_trans", type="primary"):
                b_rows = len(working_df)
                b_cols = len(working_df.columns)
                new_df, affected = clean_text_column(working_df, target_str_col, text_ops, find_str=find_val, replace_str=replace_val)
                desc = f"Cleaned text in '{target_str_col}' ({', '.join(text_ops)})"
                _record_transformation(new_df, "text_clean", desc, b_rows, b_cols, column=target_str_col, strategy="text_clean")
                st.rerun()
        else:
            render_notification(title="No Text Columns", message="Text operations apply to string and categorical columns.", variant="info")

    # ── Subtab 5: Dates & Arithmetic ─────────────────────────────────────────
    with sub_dates:
        st.markdown("##### Extract Date Components")
        dc1, dc2 = st.columns(2)
        with dc1:
            date_target = st.selectbox("Date Column", options=all_cols, key="trans_date_col")
        with dc2:
            comp_choices = st.multiselect(
                "Components",
                options=["year", "month", "day", "day_of_week", "quarter"],
                default=["year", "month"],
                format_func=lambda x: x.replace("_", " ").title(),
                key="trans_date_comps"
            )
        if comp_choices and st.button("Extract Components", key="btn_apply_date_trans", type="primary"):
            b_rows = len(working_df)
            b_cols = len(working_df.columns)
            new_df, created = extract_date_components(working_df, date_target, comp_choices)
            if created:
                desc = f"Extracted date components from '{date_target}': {', '.join(created)}"
                _record_transformation(new_df, "date_extraction", desc, b_rows, b_cols, column=date_target, strategy="date_extract")
                st.rerun()

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        st.markdown("##### Safe Mathematical Column Derivation")
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            new_col_name = st.text_input("New Column Name", placeholder="e.g. Total_Value", key="trans_derive_name")
        with d2:
            col_a = st.selectbox("Primary Column (A)", options=numeric_cols if numeric_cols else all_cols, key="trans_derive_col_a")
        with d3:
            op_choices = [("add", "A + B"), ("subtract", "A - B"), ("multiply", "A * B"), ("divide", "A / B"), ("percentage", "A / B * 100")]
            op = st.selectbox("Operation", options=[o[0] for o in op_choices], format_func=lambda k: dict(op_choices).get(k, k), key="trans_derive_op")
        with d4:
            operand_type = st.radio("Second Operand", options=["Another Column", "Constant Value"], key="trans_derive_op_type")

        col_b = None
        const_val = None
        if operand_type == "Another Column":
            col_b = st.selectbox("Second Column (B)", options=numeric_cols if numeric_cols else all_cols, key="trans_derive_col_b")
        else:
            const_val = st.number_input("Constant Value (B)", value=1.0, key="trans_derive_const_val")

        if new_col_name and st.button("Compute Derived Column", key="btn_apply_derive_trans", type="primary"):
            b_rows = len(working_df)
            b_cols = len(working_df.columns)
            new_df, ok, msg = derive_column_arithmetic(working_df, new_col_name, col_a, op, col_b=col_b, constant_val=const_val)
            if ok:
                _record_transformation(new_df, "derive_column", msg, b_rows, b_cols, column=new_col_name, strategy="arithmetic")
                st.rerun()
            else:
                st.error(msg)

    # ── Subtab 6: Preview & Export ───────────────────────────────────────────
    with sub_preview:
        st.markdown(f"##### Prepared Dataset Table ({len(working_df):,} rows × {len(working_df.columns)} columns)")
        st.dataframe(working_df.head(100), use_container_width=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        exp_c1, exp_c2 = st.columns(2)
        base_name = dataset_name.rsplit(".", 1)[0] if "." in dataset_name else dataset_name
        with exp_c1:
            csv_bytes = export_prepared_csv(working_df)
            st.download_button(
                label="📥 Download Prepared CSV",
                data=csv_bytes,
                file_name=f"{base_name}_prepared.csv",
                mime="text/csv",
                key="trans_dl_csv",
                type="primary",
                use_container_width=True
            )
        with exp_c2:
            xlsx_bytes = export_prepared_excel(working_df, sheet_name="Prepared_Data")
            st.download_button(
                label="📥 Download Prepared Excel (XLSX)",
                data=xlsx_bytes,
                file_name=f"{base_name}_prepared.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="trans_dl_xlsx",
                use_container_width=True
            )


# =============================================================================
# SECTION 5: PREPARATION HISTORY & AUDIT TRAIL
# =============================================================================

def _render_section_preparation_history(
    orig_df: pd.DataFrame,
    working_df: pd.DataFrame,
    dataset_name: str
) -> None:
    """Render audit timeline of applied transformations, verified quality improvements, and 1-click revert."""
    render_section_header(
        title="Preparation History & Audit Trail",
        subtitle="Chronological audit timeline of verified transformations, quality improvements, and 1-click undo."
    )

    history = st.session_state.get("prep_history", [])
    undo_stack = st.session_state.get("prep_undo_stack", [])

    # History Toolbar
    t1, t2, t3 = st.columns([6, 3, 3])
    with t1:
        st.markdown(
            f'<div style="font-weight: 600; font-size: 13.5px; color: var(--text-primary); padding-top: 6px;">'
            f'Recorded Audit Trail ({len(history)} Modifications)'
            f'</div>',
            unsafe_allow_html=True
        )
    with t2:
        can_undo = len(undo_stack) > 0
        if st.button("↩ Undo Last Change", key="hist_undo_btn", disabled=not can_undo, use_container_width=True):
            _undo_last_change()
    with t3:
        with st.popover("Reset All Changes", use_container_width=True):
            st.markdown("**Confirm Full Reset**")
            st.caption("Revert working dataset back to the pristine uploaded copy. All transformation history will be cleared.")
            if st.button("Yes, Reset to Original", key="confirm_reset_hist_btn", type="primary", use_container_width=True):
                _reset_all_changes()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    if not history:
        render_empty_state(
            title="No Transformations Recorded Yet",
            description="Apply recommended fixes or custom transformations from the sections above to see verified audit entries here.",
            icon="sliders-horizontal"
        )
        return

    # Render Audit Timeline Items
    for idx, item in enumerate(history):
        delta = item.get("score_delta", 0.0)
        delta_tag = f"<span class='ds-preview-delta-positive'>+{delta:.1f} Quality Score</span>" if delta > 0 else ""
        col_tag = f"Column: <b>{html.escape(item.get('column', 'Dataset'))}</b>"
        strat_tag = f"Method: <b>{html.escape(item.get('strategy', 'Applied'))}</b>" if item.get('strategy') else ""
        dim_tag = f"Dataset: {item.get('rows_before', 0):,} → {item.get('rows_after', 0):,} rows"

        reason_text = item.get("reason", "")
        reason_html = f"<div style='font-size: 11.5px; color: var(--text-secondary); margin-top: 2px;'>{html.escape(reason_text)}</div>" if reason_text else ""

        entry_html = (
            f"<div class='ds-audit-entry' style='margin-bottom: 8px;'>"
            f"<div class='ds-audit-entry-left'>"
            f"<div class='ds-audit-entry-title'>⚡ {html.escape(item.get('description', 'Transformation Applied'))} {delta_tag}</div>"
            f"<div class='ds-audit-entry-meta'>{item.get('timestamp', '')} · {col_tag} · {strat_tag} · {dim_tag}</div>"
            f"{reason_html}"
            f"</div>"
            f"</div>"
        )
        st.markdown(entry_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    st.markdown("##### Export Prepared Dataset")
    exp_c1, exp_c2 = st.columns(2)
    base_name = dataset_name.rsplit(".", 1)[0] if "." in dataset_name else dataset_name
    with exp_c1:
        csv_bytes = export_prepared_csv(working_df)
        st.download_button(
            label="📥 Download Prepared Dataset (CSV)",
            data=csv_bytes,
            file_name=f"{base_name}_prepared.csv",
            mime="text/csv",
            key="hist_dl_csv",
            type="primary",
            use_container_width=True
        )
    with exp_c2:
        xlsx_bytes = export_prepared_excel(working_df, sheet_name="Prepared_Data")
        st.download_button(
            label="📥 Download Prepared Dataset (Excel XLSX)",
            data=xlsx_bytes,
            file_name=f"{base_name}_prepared.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="hist_dl_xlsx",
            use_container_width=True
        )

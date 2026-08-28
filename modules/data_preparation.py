"""
DATA STUDIO v2 — Interactive Data Preparation & Transformation Studio (Module 5)
=============================================================================
Professional, non-destructive data preparation workspace delivering:
- Dual-State Dataset Architecture (Immutable original vs Interactive working copy)
- Dynamic Preparation Summary & Real-Time Transformation KPIs
- Transformation History Logging with 1-Click Undo and Reset All Changes
- Missing Value Imputation (Mean, Median, Zero, Mode, Unknown, Custom, Drop)
- Whole-Row and Column-Subset Duplicate Removal
- Column Management (Rename with validation, Drop, Reorder, Safe Type Casting)
- Type-Aware Visual Filter Builder with Compound Conditions
- Persistent Single and Multi-Column Sorting
- IQR Outlier Inspection, Boundary Capping, and Row Removal
- Text & String Cleaning (Trim, Case conversions, Find/Replace, Empty handling)
- Date Parsing and Temporal Component Extraction (Year, Month, Day, DayOfWeek, Quarter)
- Safe Controlled Column Arithmetic Derivation (Strictly no eval/exec)
- Side-by-Side Before/After Data Preview and CSV / Excel Exports
- "Use Prepared Dataset for Analysis" Integration with All Downstream Modules
"""
from typing import Optional, Dict, Any, List, Tuple
import datetime
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
    render_next_step_banner,
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


# =============================================================================
# SESSION STATE INITIALIZATION & HISTORY MANAGEMENT
# =============================================================================

def _init_prep_state() -> None:
    """Initialize Data Preparation session state variables."""
    # If working copy doesn't exist, initialize from original_dataset or dataset
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


def _record_transformation(
    new_df: pd.DataFrame,
    trans_type: str,
    description: str,
    before_rows: int,
    before_cols: int
) -> None:
    """Snapshot previous state to undo stack and record transformation in history log."""
    # Push snapshot to undo stack (limit stack size to 10 to protect memory)
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
        "cols_after": after_cols
    }

    st.session_state["prep_history"].append(hist_entry)
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
            undone = history.pop()
            st.session_state["prep_history"] = history
            st.toast(f"Undone: {undone['description']}")
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
        mark_workflow_step("prep", True)
        log_activity(f"Applied prepared dataset ({len(working_df):,} rows × {len(working_df.columns)} cols) to active session", "wrench")
        st.toast("Prepared dataset is now active across all Data Studio modules!")
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
            subtitle="Clean missing values, drop duplicates, cast types, and prepare your dataset for analysis.",
            icon="wrench"
        )
        render_empty_state(
            title="No dataset ready for preparation",
            description="Upload a CSV or Excel dataset to begin cleaning, filtering, and transforming your data.",
            icon="wrench"
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

    # ── Consume deep-link hint from Data Quality ────────────────────────────────────
    prep_hint = st.session_state.get("prep_suggested_action")
    if prep_hint:
        hint_messages = {
            "missing": ("Missing Values", "Use the **MISSING VALUES** tab below to impute, fill, or drop columns with null values."),
            "duplicates": ("Duplicate Rows", "Use the **DUPLICATES** tab below to remove identical rows from your dataset."),
            "outliers": ("Outlier Treatment", "Use the **OUTLIERS** tab below to cap, remove, or inspect extreme values."),
            "types": ("Column Types", "Use the **COLUMNS** tab below to rename, reorder, or cast data types."),
        }
        if prep_hint in hint_messages:
            tab_label, hint_msg = hint_messages[prep_hint]
            render_notification(
                title=f"→ Jump to: {tab_label}",
                message=hint_msg,
                variant="info"
            )
        # Clear hint after consuming it
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
        subtitle="Clean missing values, drop duplicates, filter rows, cast types, and prepare your dataset for analysis.",
        icon="wrench"
    )

    # 3. Preparation Summary KPI Cards & Active Dataset Switcher
    _render_preparation_summary_bar(orig_df, working_df, dataset_name, file_type)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 4. Transformation History & Undo / Reset Toolbar
    _render_history_and_undo_toolbar()

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 5. Functional Preparation Tabs
    tab_overview, tab_missing, tab_dups, tab_cols, tab_filter, tab_sort, tab_outliers, tab_text, tab_dates, tab_preview = st.tabs([
        "OVERVIEW",
        "MISSING VALUES",
        "DUPLICATES",
        "COLUMNS",
        "FILTERS",
        "SORTING",
        "OUTLIERS",
        "TEXT CLEANING",
        "DATES & DERIVATIONS",
        "PREVIEW & EXPORT"
    ])

    with tab_overview:
        _render_tab_overview(orig_df, working_df)

    with tab_missing:
        _render_tab_missing_values(working_df)

    with tab_dups:
        _render_tab_duplicates(working_df)

    with tab_cols:
        _render_tab_columns(working_df)

    with tab_filter:
        _render_tab_filters(working_df)

    with tab_sort:
        _render_tab_sorting(working_df)

    with tab_outliers:
        _render_tab_outliers(working_df)

    with tab_text:
        _render_tab_text_cleaning(working_df)

    with tab_dates:
        _render_tab_dates_and_derivations(working_df)

    with tab_preview:
        _render_tab_preview_and_export(orig_df, working_df, dataset_name)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    render_ai_context_trigger("Suggest cleaning transformations with AI", intent="data_prep_cleaning", key="prep_ai_btn")

    # Dynamic Bottom Next Workflow Steps Section
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
    """Render top metrics comparing original vs working dataset and promotion button."""
    orig_rows = len(orig_df) if orig_df is not None else 0
    orig_cols = len(orig_df.columns) if orig_df is not None else 0
    curr_rows = len(working_df) if working_df is not None else 0
    curr_cols = len(working_df.columns) if working_df is not None else 0

    history_len = len(st.session_state.get("prep_history", []))
    missing_cells = int(working_df.isna().sum().sum()) if working_df is not None else 0
    total_cells = curr_rows * curr_cols
    missing_pct = (missing_cells / total_cells * 100) if total_cells > 0 else 0.0
    dup_rows = int(working_df.duplicated().sum()) if working_df is not None else 0

    active_mode = st.session_state.get("prep_active_dataset_mode", "Original")

    # Banner with Status and Promote Action
    col_status, col_action = st.columns([7, 5])
    with col_status:
        badge_cls = "ds-badge-numeric" if active_mode == "Prepared" else "ds-badge-neutral"
        banner_html = (
            f'<div class="ds-active-banner" style="margin-bottom: 10px; padding: 10px 16px;">'
            f'<div class="ds-active-banner-left">'
            f'<div class="ds-brand-badge" style="background: var(--accent);">P</div>'
            f'<div>'
            f'<div class="ds-active-banner-name" style="font-size: 15px;">{dataset_name}</div>'
            f'<div class="ds-active-banner-meta" style="font-size: 12px;">'
            f'Active in Analysis: <span class="ds-badge {badge_cls}" style="font-size: 11px;">{active_mode} Dataset</span> · {history_len} transformations applied'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(banner_html, unsafe_allow_html=True)

    with col_action:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        if st.button("Use Prepared Dataset for Analysis", key="btn_apply_prepared_analysis", type="primary", use_container_width=True):
            _apply_prepared_to_analysis()

    # 4 KPI Summary Cards
    kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
    with kpi_c1:
        row_delta = curr_rows - orig_rows
        render_metric_card(
            label="Dataset Rows",
            value=f"{curr_rows:,}",
            change=f"{row_delta:+,} rows" if row_delta != 0 else "Unchanged",
            change_type="success" if row_delta >= 0 else "neutral",
            description=f"Original: {orig_rows:,}"
        )
    with kpi_c2:
        col_delta = curr_cols - orig_cols
        render_metric_card(
            label="Dataset Columns",
            value=f"{curr_cols}",
            change=f"{col_delta:+} cols" if col_delta != 0 else "Unchanged",
            change_type="success" if col_delta >= 0 else "neutral",
            description=f"Original: {orig_cols}"
        )
    with kpi_c3:
        render_metric_card(
            label="Missing Values",
            value=f"{missing_cells:,} ({missing_pct:.1f}%)",
            change=f"{missing_cells} cells",
            change_type="warning" if missing_cells > 0 else "success",
            description="Remaining null cells"
        )
    with kpi_c4:
        render_metric_card(
            label="Duplicate Rows",
            value=f"{dup_rows:,}",
            change="Clean" if dup_rows == 0 else f"{dup_rows} duplicates",
            change_type="success" if dup_rows == 0 else "warning",
            description="Remaining duplicated rows"
        )


# =============================================================================
# HISTORY & UNDO / RESET TOOLBAR
# =============================================================================

def _render_history_and_undo_toolbar() -> None:
    """Render undo, reset all changes, and transformation history log."""
    history = st.session_state.get("prep_history", [])
    undo_stack = st.session_state.get("prep_undo_stack", [])

    toolbar_c1, toolbar_c2, toolbar_c3 = st.columns([6, 3, 3])

    with toolbar_c1:
        st.markdown(
            f'<div style="font-weight: 600; font-size: 13px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; padding-top: 6px;">'
            f'Transformation Actions ({len(history)} Changes Recorded)'
            f'</div>',
            unsafe_allow_html=True
        )

    with toolbar_c2:
        can_undo = len(undo_stack) > 0
        if st.button("Undo Last Change", key="prep_undo_btn", disabled=not can_undo, use_container_width=True):
            _undo_last_change()

    with toolbar_c3:
        with st.popover("Reset All Changes", use_container_width=True):
            st.markdown("**Confirm Full Reset**")
            st.caption("Revert working dataset back to the pristine original uploaded file. All transformation history will be cleared.")
            if st.button("Yes, Reset to Original", key="confirm_reset_all_btn", type="primary", use_container_width=True):
                _reset_all_changes()

    if history:
        with st.expander(f"View Transformation History Log ({len(history)} entries)", expanded=False):
            hist_df = pd.DataFrame(history)[["id", "timestamp", "description", "rows_before", "rows_after", "cols_before", "cols_after"]]
            hist_df.columns = ["Step", "Time", "Operation Description", "Rows Before", "Rows After", "Cols Before", "Cols After"]
            st.dataframe(hist_df, use_container_width=True, hide_index=True)


# =============================================================================
# TAB 1: OVERVIEW
# =============================================================================

def _render_tab_overview(orig_df: pd.DataFrame, working_df: pd.DataFrame) -> None:
    """Render high-level dataset health comparison and quick fix suggestions."""
    render_section_header(
        title="Preparation Workspace Overview",
        subtitle="Compare original uploaded state vs current prepared working state."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Original Dataset State")
        orig_missing = int(orig_df.isna().sum().sum())
        orig_dups = int(orig_df.duplicated().sum())
        st.write(f"- **Total Rows:** {len(orig_df):,}")
        st.write(f"- **Total Columns:** {len(orig_df.columns)}")
        st.write(f"- **Missing Cells:** {orig_missing:,}")
        st.write(f"- **Duplicate Rows:** {orig_dups:,}")

    with col2:
        st.markdown("#### Current Prepared State")
        curr_missing = int(working_df.isna().sum().sum())
        curr_dups = int(working_df.duplicated().sum())
        st.write(f"- **Total Rows:** {len(working_df):,}")
        st.write(f"- **Total Columns:** {len(working_df.columns)}")
        st.write(f"- **Missing Cells:** {curr_missing:,}")
        st.write(f"- **Duplicate Rows:** {curr_dups:,}")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Quick Cleaning Recommendations")

    recs = []
    if curr_dups > 0:
        recs.append(f"Remove **{curr_dups} duplicate rows** in the **Duplicates** tab.")
    if curr_missing > 0:
        recs.append(f"Resolve **{curr_missing} missing values** across columns in the **Missing Values** tab.")
    
    # Check for whitespace in text columns
    text_cols = [c for c in working_df.columns if pd.api.types.is_object_dtype(working_df[c])]
    if text_cols:
        recs.append("Standardize text formatting (trim whitespace, lower/upper) in the **Text Cleaning** tab.")

    if recs:
        for r in recs:
            st.info(r)
    else:
        render_notification(
            title="Clean Dataset Status",
            message="No critical duplicates or missing values detected in the current prepared state.",
            variant="success"
        )


# =============================================================================
# TAB 2: MISSING VALUE HANDLING
# =============================================================================

def _render_tab_missing_values(working_df: pd.DataFrame) -> None:
    """Render interactive missing value profile table and imputation tools."""
    render_section_header(
        title="Missing Value Handling",
        subtitle="Review column completeness and apply precision imputation or removal strategies."
    )

    summary_df = get_missing_values_summary(working_df)
    missing_cols_df = summary_df[summary_df["Missing Count"] > 0]

    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    if missing_cols_df.empty:
        render_notification(
            title="Zero Missing Values",
            message="All columns in the prepared dataset are 100% complete.",
            variant="success"
        )
        return

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Apply Missing Value Strategy")

    col_options = list(missing_cols_df["Column"])
    ctrl1, ctrl2, ctrl3 = st.columns([4, 4, 4])

    with ctrl1:
        target_cols = st.multiselect(
            "Target Columns",
            options=col_options,
            default=[col_options[0]] if col_options else [],
            key="prep_missing_target_cols"
        )

    with ctrl2:
        # Check if selected columns are numeric or categorical
        is_all_numeric = all(pd.api.types.is_numeric_dtype(working_df[c]) for c in target_cols) if target_cols else False
        
        if is_all_numeric:
            strategies = [
                ("mean", "Fill with Column Mean"),
                ("median", "Fill with Column Median"),
                ("zero", "Fill with 0 (Zero)"),
                ("mode", "Fill with Mode (Most Frequent)"),
                ("custom", "Fill with Custom Value"),
                ("ffill", "Forward Fill (Previous Value)"),
                ("drop_rows", "Drop Rows with Missing Values"),
                ("drop_cols", "Drop Selected Columns Entirely")
            ]
        else:
            strategies = [
                ("mode", "Fill with Mode (Most Frequent)"),
                ("unknown", "Fill with 'Unknown'"),
                ("custom", "Fill with Custom Text/Value"),
                ("ffill", "Forward Fill (Previous Value)"),
                ("drop_rows", "Drop Rows with Missing Values"),
                ("drop_cols", "Drop Selected Columns Entirely")
            ]

        strat_keys = [s[0] for s in strategies]
        strategy = st.selectbox(
            "Imputation Strategy",
            options=strat_keys,
            format_func=lambda k: dict(strategies).get(k, k),
            key="prep_missing_strategy"
        )

    custom_val = None
    with ctrl3:
        if strategy == "custom":
            custom_val = st.text_input("Custom Fill Value", value="0" if is_all_numeric else "Unknown", key="prep_missing_custom_val")
        else:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    if target_cols:
        # Pre-apply impact calculation
        est_missing_before = int(working_df[target_cols].isna().sum().sum())
        if strategy == "drop_rows":
            est_rows_dropped = int(working_df[target_cols].isna().any(axis=1).sum())
            impact_msg = f"Applying **Drop Rows** will remove **{est_rows_dropped:,} rows**."
        elif strategy == "drop_cols":
            impact_msg = f"Applying **Drop Columns** will remove columns: **{', '.join(target_cols)}**."
        else:
            impact_msg = f"Applying strategy will impute **{est_missing_before:,} missing values**."

        st.caption(f"Estimated Impact: {impact_msg}")

        if st.button("Apply Missing Value Transformation", key="btn_apply_missing", type="primary"):
            b_rows = len(working_df)
            b_cols = len(working_df.columns)
            new_df, info = handle_missing_values(working_df, target_cols, strategy, custom_value=custom_val)
            desc = f"Resolved missing values in {', '.join(target_cols)} using {strategy.replace('_', ' ').title()}"
            _record_transformation(new_df, "missing_values", desc, b_rows, b_cols)
            st.rerun()


# =============================================================================
# TAB 3: DUPLICATE HANDLING
# =============================================================================

def _render_tab_duplicates(working_df: pd.DataFrame) -> None:
    """Render duplicate row inspector and subset removal."""
    render_section_header(
        title="Duplicate Row Handling",
        subtitle="Detect and remove identical or subset-duplicated records."
    )

    all_cols = list(working_df.columns)
    subset_selection = st.multiselect(
        "Evaluate Duplicates on Specific Column Subset (Leave empty to evaluate all columns)",
        options=all_cols,
        default=[],
        key="prep_dup_subset_cols"
    )

    dup_info = get_duplicates_info(working_df, subset_cols=subset_selection if subset_selection else None)
    dup_cnt = dup_info["duplicate_count"]
    dup_pct = dup_info["duplicate_pct"]

    c1, c2 = st.columns(2)
    with c1:
        render_metric_card(
            label="Duplicate Rows Detected",
            value=f"{dup_cnt:,}",
            change=f"{dup_pct:.1f}% of dataset",
            change_type="warning" if dup_cnt > 0 else "success"
        )
    with c2:
        keep_opt = st.selectbox("Duplicate Retention Rule", options=["first", "last"], format_func=lambda x: f"Keep {x.capitalize()} Occurrence", key="prep_dup_keep")

    if dup_cnt > 0:
        st.markdown("#### Duplicate Records Preview")
        st.dataframe(dup_info["duplicate_df"], use_container_width=True)

        if st.button(f"Remove {dup_cnt:,} Duplicate Rows", key="btn_remove_dups", type="primary"):
            b_rows = len(working_df)
            b_cols = len(working_df.columns)
            new_df, info = remove_duplicates(working_df, subset_cols=subset_selection if subset_selection else None, keep=keep_opt)
            desc = f"Removed {info['removed_count']:,} duplicate rows"
            _record_transformation(new_df, "duplicates", desc, b_rows, b_cols)
            st.rerun()
    else:
        render_notification(
            title="Zero Duplicate Records",
            message="No duplicate records detected based on current column selection.",
            variant="success"
        )


# =============================================================================
# TAB 4: COLUMN MANAGEMENT (Rename, Drop, Reorder, Cast Type)
# =============================================================================

def _render_tab_columns(working_df: pd.DataFrame) -> None:
    """Render column operations: Rename, Drop, Reorder, and Cast Data Type."""
    render_section_header(
        title="Column Management",
        subtitle="Rename columns, drop unnecessary features, reorder columns, or cast data types safely."
    )

    subtab_rename, subtab_drop, subtab_reorder, subtab_cast = st.tabs([
        "RENAME COLUMN",
        "DROP COLUMNS",
        "REORDER COLUMNS",
        "CHANGE DATA TYPE"
    ])

    all_cols = list(working_df.columns)

    # 1. Rename Column
    with subtab_rename:
        st.markdown("#### Rename Column")
        c1, c2 = st.columns(2)
        with c1:
            col_to_rename = st.selectbox("Select Column to Rename", options=all_cols, key="prep_col_rename_sel")
        with c2:
            new_col_name = st.text_input("New Column Name", value=col_to_rename, key="prep_col_rename_val")

        if st.button("Apply Rename", key="btn_apply_rename", type="primary"):
            b_rows = len(working_df)
            b_cols = len(working_df.columns)
            new_df, ok, msg = rename_column(working_df, col_to_rename, new_col_name)
            if ok:
                _record_transformation(new_df, "rename_column", msg, b_rows, b_cols)
                st.rerun()
            else:
                st.error(msg)

    # 2. Drop Columns
    with subtab_drop:
        st.markdown("#### Drop Column(s)")
        cols_to_drop = st.multiselect("Select Column(s) to Drop", options=all_cols, key="prep_col_drop_sel")

        if cols_to_drop:
            st.warning(f"Dropping {len(cols_to_drop)} columns: {', '.join(cols_to_drop)}")
            if st.button(f"Confirm Drop {len(cols_to_drop)} Column(s)", key="btn_apply_drop_cols", type="primary"):
                b_rows = len(working_df)
                b_cols = len(working_df.columns)
                new_df, dropped = drop_columns(working_df, cols_to_drop)
                desc = f"Dropped column(s): {', '.join(dropped)}"
                _record_transformation(new_df, "drop_columns", desc, b_rows, b_cols)
                st.rerun()

    # 3. Reorder Columns
    with subtab_reorder:
        st.markdown("#### Reorder Columns")
        st.caption("Select columns in the desired display order:")
        new_order = st.multiselect("Column Ordering", options=all_cols, default=all_cols, key="prep_col_reorder_sel")

        if st.button("Apply Column Order", key="btn_apply_reorder", type="primary"):
            b_rows = len(working_df)
            b_cols = len(working_df.columns)
            new_df, ok = reorder_columns(working_df, new_order)
            if ok:
                _record_transformation(new_df, "reorder_columns", "Reordered dataset columns", b_rows, b_cols)
                st.rerun()

    # 4. Change Data Type
    with subtab_cast:
        st.markdown("#### Safe Data Type Casting")
        c1, c2 = st.columns(2)
        with c1:
            col_to_cast = st.selectbox("Select Column to Cast", options=all_cols, key="prep_col_cast_sel")
            curr_type = str(working_df[col_to_cast].dtype)
            st.caption(f"Current Pandas Dtype: `{curr_type}`")

        with c2:
            type_options = ["Numeric", "Integer", "Float", "String", "Category", "Boolean", "Datetime"]
            target_type = st.selectbox("Target Data Type", options=type_options, key="prep_col_cast_target")

        if st.button("Apply Type Conversion", key="btn_apply_cast", type="primary"):
            b_rows = len(working_df)
            b_cols = len(working_df.columns)
            new_df, result = cast_column_type(working_df, col_to_cast, target_type)
            if result.get("success"):
                desc = f"Cast column '{col_to_cast}' from {curr_type} to {target_type} ({result['converted']} values converted, {result['coerced_na']} coerced to NA)"
                _record_transformation(new_df, "cast_type", desc, b_rows, b_cols)
                st.rerun()
            else:
                st.error(f"Type conversion failed: {result.get('error')}")


# =============================================================================
# TAB 5: VISUAL FILTER BUILDER
# =============================================================================

def _render_tab_filters(working_df: pd.DataFrame) -> None:
    """Render visual rule-based filter builder with compound conditions."""
    render_section_header(
        title="Visual Filter Builder",
        subtitle="Build non-destructive filters adapting to numeric, text, and datetime column types."
    )

    all_cols = list(working_df.columns)
    c1, c2, c3, c4 = st.columns([3, 3, 3, 3])

    with c1:
        f_col = st.selectbox("Filter Column", options=all_cols, key="prep_filter_col")

    # Select operators according to column data type
    series = working_df[f_col]
    if pd.api.types.is_numeric_dtype(series):
        ops = ["Equals (=)", "Not Equals (!=)", "Greater Than (>)", "Greater or Equal (>=)", "Less Than (<)", "Less or Equal (<=)", "Between", "Is Null / Missing", "Is Not Null"]
    elif pd.api.types.is_datetime64_any_dtype(series):
        ops = ["Before (<)", "After (>)", "Equals", "Between", "Is Null / Missing", "Is Not Null"]
    else:
        ops = ["Equals", "Not Equals", "Contains", "Starts with", "Ends with", "Is one of", "Is Null / Missing", "Is Not Null"]

    with c2:
        f_op = st.selectbox("Condition Operator", options=ops, key="prep_filter_op")

    with c3:
        if f_op not in ["Is Null / Missing", "Is Not Null"]:
            if f_op == "Is one of":
                f_val = st.text_input("Values (comma-separated)", key="prep_filter_val_multi")
            elif pd.api.types.is_numeric_dtype(series):
                min_v = float(series.dropna().min()) if not series.dropna().empty else 0.0
                f_val = st.number_input("Value", value=min_v, key="prep_filter_val_num")
            else:
                f_val = st.text_input("Comparison Value", key="prep_filter_val_str")
        else:
            f_val = None

    with c4:
        if f_op == "Between":
            if pd.api.types.is_numeric_dtype(series):
                max_v = float(series.dropna().max()) if not series.dropna().empty else 100.0
                f_val_end = st.number_input("End Value (Between)", value=max_v, key="prep_filter_val_end_num")
            else:
                f_val_end = st.text_input("End Value", key="prep_filter_val_end_str")
        else:
            f_val_end = None

    if st.button("Apply Filter", key="btn_apply_single_filter", type="primary"):
        rule = {"column": f_col, "operator": f_op, "value": f_val, "value_end": f_val_end}
        b_rows = len(working_df)
        b_cols = len(working_df.columns)
        new_df, info = apply_filters(working_df, [rule])
        desc = f"Filtered '{f_col}' with {f_op} {f_val or ''} (Kept {info['rows_after']:,} of {b_rows:,} rows)"
        _record_transformation(new_df, "filter", desc, b_rows, b_cols)
        st.rerun()


# =============================================================================
# TAB 6: SORTING
# =============================================================================

def _render_tab_sorting(working_df: pd.DataFrame) -> None:
    """Render single and multi-column persistent sorting builder."""
    render_section_header(
        title="Persistent Sorting",
        subtitle="Reorder dataset records by primary and secondary columns."
    )

    all_cols = list(working_df.columns)
    c1, c2 = st.columns(2)
    with c1:
        sort_cols = st.multiselect("Sort Columns (in priority order)", options=all_cols, default=[all_cols[0]] if all_cols else [], key="prep_sort_cols")
    with c2:
        order_choice = st.radio("Sort Direction", options=["Ascending (Low to High / A-Z)", "Descending (High to Low / Z-A)"], key="prep_sort_dir")
        is_asc = "Ascending" in order_choice

    if sort_cols and st.button("Apply Persistent Sort", key="btn_apply_sort", type="primary"):
        b_rows = len(working_df)
        b_cols = len(working_df.columns)
        new_df, ok = sort_dataset(working_df, sort_cols, [is_asc] * len(sort_cols))
        if ok:
            desc = f"Sorted dataset by {', '.join(sort_cols)} ({'Ascending' if is_asc else 'Descending'})"
            _record_transformation(new_df, "sort", desc, b_rows, b_cols)
            st.rerun()


# =============================================================================
# TAB 7: OUTLIER HANDLING (IQR)
# =============================================================================

def _render_tab_outliers(working_df: pd.DataFrame) -> None:
    """Render IQR outlier detection, affected row preview, capping, and removal."""
    render_section_header(
        title="IQR Outlier Handling",
        subtitle="Detect and handle statistical outliers using the Interquartile Range (IQR) method."
    )

    numeric_cols = [c for c in working_df.columns if pd.api.types.is_numeric_dtype(working_df[c])]
    if not numeric_cols:
        render_notification(title="No Numeric Columns", message="Outlier detection requires at least one numeric column.", variant="info")
        return

    c1, c2 = st.columns([5, 7])
    with c1:
        target_num_col = st.selectbox("Select Numeric Column", options=numeric_cols, key="prep_outlier_col")

    prof = get_outliers_profile(working_df, target_num_col)
    outlier_cnt = prof["outlier_count"]
    lower = prof["lower_bound"]
    upper = prof["upper_bound"]

    with c2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        st.caption(f"IQR Boundary: [{lower:,.2f}, {upper:,.2f}] · Detected Outliers: **{outlier_cnt:,} records**")

    if outlier_cnt > 0:
        st.markdown("#### Outlier Records Review")
        st.dataframe(prof["outlier_df"].head(30), use_container_width=True)

        action_c1, action_c2 = st.columns(2)
        with action_c1:
            if st.button(f"Cap Outliers to Boundaries [{lower:,.1f}, {upper:,.1f}]", key="btn_cap_outliers", type="primary", use_container_width=True):
                b_rows = len(working_df)
                b_cols = len(working_df.columns)
                new_df, info = handle_outliers(working_df, target_num_col, action="cap_boundaries")
                desc = f"Capped {outlier_cnt:,} outliers in '{target_num_col}' to [{lower:,.2f}, {upper:,.2f}]"
                _record_transformation(new_df, "outliers_cap", desc, b_rows, b_cols)
                st.rerun()

        with action_c2:
            if st.button(f"Remove {outlier_cnt:,} Outlier Rows", key="btn_remove_outliers", use_container_width=True):
                b_rows = len(working_df)
                b_cols = len(working_df.columns)
                new_df, info = handle_outliers(working_df, target_num_col, action="remove_rows")
                desc = f"Removed {outlier_cnt:,} outlier rows in '{target_num_col}'"
                _record_transformation(new_df, "outliers_remove", desc, b_rows, b_cols)
                st.rerun()
    else:
        render_notification(
            title="Clean Column Distribution",
            message=f"No statistical outliers detected in '{target_num_col}' based on 1.5×IQR boundary.",
            variant="success"
        )


# =============================================================================
# TAB 8: TEXT CLEANING
# =============================================================================

def _render_tab_text_cleaning(working_df: pd.DataFrame) -> None:
    """Render text and categorical string cleaning operations."""
    render_section_header(
        title="Text & String Cleaning",
        subtitle="Standardize text case, trim whitespace, find and replace values, or clean empty strings."
    )

    str_cols = [c for c in working_df.columns if not pd.api.types.is_numeric_dtype(working_df[c])]
    if not str_cols:
        render_notification(title="No Text Columns", message="Text cleaning applies to string or categorical columns.", variant="info")
        return

    c1, c2 = st.columns(2)
    with c1:
        target_str_col = st.selectbox("Select Text Column", options=str_cols, key="prep_text_col")

    with c2:
        text_ops = st.multiselect(
            "Select Cleaning Operations",
            options=["trim", "lower", "upper", "title", "remove_empty", "find_replace"],
            default=["trim"],
            format_func=lambda x: {
                "trim": "Trim Leading/Trailing Whitespace",
                "lower": "Convert to Lowercase",
                "upper": "Convert to Uppercase",
                "title": "Convert to Title Case",
                "remove_empty": "Convert Blank/Empty Strings to NA",
                "find_replace": "Find and Replace Text"
            }.get(x, x),
            key="prep_text_ops"
        )

    find_val = None
    replace_val = None
    if "find_replace" in text_ops:
        fr1, fr2 = st.columns(2)
        with fr1:
            find_val = st.text_input("Find Substring / Value", key="prep_text_find")
        with fr2:
            replace_val = st.text_input("Replace With", key="prep_text_replace")

    if text_ops and st.button("Apply Text Cleaning", key="btn_apply_text_clean", type="primary"):
        b_rows = len(working_df)
        b_cols = len(working_df.columns)
        new_df, affected = clean_text_column(working_df, target_str_col, text_ops, find_str=find_val, replace_str=replace_val)
        desc = f"Cleaned text in '{target_str_col}' ({', '.join(text_ops)})"
        _record_transformation(new_df, "text_clean", desc, b_rows, b_cols)
        st.rerun()


# =============================================================================
# TAB 9: DATES & COLUMN DERIVATIONS
# =============================================================================

def _render_tab_dates_and_derivations(working_df: pd.DataFrame) -> None:
    """Render temporal component extractors and safe column arithmetic derivations."""
    render_section_header(
        title="Dates & Column Derivations",
        subtitle="Extract temporal features or derive new columns using safe mathematical calculations."
    )

    subtab_dates, subtab_arith = st.tabs(["DATE COMPONENT EXTRACTION", "SAFE COLUMN ARITHMETIC"])

    all_cols = list(working_df.columns)
    numeric_cols = [c for c in working_df.columns if pd.api.types.is_numeric_dtype(working_df[c])]

    # 1. Date Component Extraction
    with subtab_dates:
        st.markdown("#### Extract Date Components")
        c1, c2 = st.columns(2)
        with c1:
            date_target = st.selectbox("Date / Timestamp Column", options=all_cols, key="prep_date_extract_col")
        with c2:
            comp_choices = st.multiselect(
                "Components to Extract",
                options=["year", "month", "day", "day_of_week", "quarter"],
                default=["year", "month"],
                format_func=lambda x: x.replace("_", " ").title(),
                key="prep_date_comps"
            )

        if comp_choices and st.button("Extract Date Features", key="btn_apply_date_extract", type="primary"):
            b_rows = len(working_df)
            b_cols = len(working_df.columns)
            new_df, created = extract_date_components(working_df, date_target, comp_choices)
            if created:
                desc = f"Extracted temporal components from '{date_target}': {', '.join(created)}"
                _record_transformation(new_df, "date_extraction", desc, b_rows, b_cols)
                st.rerun()

    # 2. Safe Column Arithmetic
    with subtab_arith:
        st.markdown("#### Safe Mathematical Derivation (Strictly No eval/exec)")
        st.caption("Calculate new columns from arithmetic operations between features.")

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            new_col_name = st.text_input("New Column Name", placeholder="e.g. Net_Revenue", key="prep_derive_name")
        with d2:
            col_a = st.selectbox("Primary Column (A)", options=numeric_cols if numeric_cols else all_cols, key="prep_derive_col_a")
        with d3:
            op_choices = [
                ("add", "Add (A + B)"),
                ("subtract", "Subtract (A - B)"),
                ("multiply", "Multiply (A * B)"),
                ("divide", "Divide (A / B)"),
                ("percentage", "Percentage Share (A / B * 100)")
            ]
            op_keys = [o[0] for o in op_choices]
            op = st.selectbox("Operation", options=op_keys, format_func=lambda k: dict(op_choices).get(k, k), key="prep_derive_op")
        with d4:
            operand_type = st.radio("Second Operand (B)", options=["Another Column", "Constant Value"], key="prep_derive_operand_type")

        col_b = None
        const_val = None
        if operand_type == "Another Column":
            col_b = st.selectbox("Second Column (B)", options=numeric_cols if numeric_cols else all_cols, key="prep_derive_col_b")
        else:
            const_val = st.number_input("Constant Numeric Value (B)", value=1.0, key="prep_derive_const_val")

        if new_col_name and st.button("Compute Derived Column", key="btn_apply_derive", type="primary"):
            b_rows = len(working_df)
            b_cols = len(working_df.columns)
            new_df, ok, msg = derive_column_arithmetic(working_df, new_col_name, col_a, op, col_b=col_b, constant_val=const_val)
            if ok:
                _record_transformation(new_df, "derive_column", msg, b_rows, b_cols)
                st.rerun()
            else:
                st.error(msg)


# =============================================================================
# TAB 10: PREVIEW & EXPORT
# =============================================================================

def _render_tab_preview_and_export(
    orig_df: pd.DataFrame,
    working_df: pd.DataFrame,
    dataset_name: str
) -> None:
    """Render side-by-side / toggleable dataset preview and export options."""
    render_section_header(
        title="Prepared Dataset Preview & Export",
        subtitle="Inspect clean data tables and export the prepared dataset to CSV or Excel."
    )

    prev_mode = st.radio(
        "Preview Mode",
        options=["Prepared Working Dataset", "Original Uploaded Dataset", "Side-by-Side Comparison"],
        horizontal=True,
        key="prep_preview_mode_choice"
    )

    if prev_mode == "Prepared Working Dataset":
        st.markdown(f"**Prepared Dataset Preview** ({len(working_df):,} rows × {len(working_df.columns)} columns)")
        st.dataframe(working_df, use_container_width=True)

    elif prev_mode == "Original Uploaded Dataset":
        st.markdown(f"**Original Dataset Preview** ({len(orig_df):,} rows × {len(orig_df.columns)} columns)")
        st.dataframe(orig_df, use_container_width=True)

    else:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Original** ({len(orig_df):,} × {len(orig_df.columns)})")
            st.dataframe(orig_df.head(50), use_container_width=True)
        with c2:
            st.markdown(f"**Prepared** ({len(working_df):,} × {len(working_df.columns)})")
            st.dataframe(working_df.head(50), use_container_width=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Export Prepared Dataset")

    base_name = dataset_name.rsplit(".", 1)[0] if "." in dataset_name else dataset_name
    exp_c1, exp_c2 = st.columns(2)

    with exp_c1:
        csv_bytes = export_prepared_csv(working_df)
        st.download_button(
            label="Download Prepared Dataset (CSV)",
            data=csv_bytes,
            file_name=f"{base_name}_prepared.csv",
            mime="text/csv",
            key="prep_dl_csv",
            type="primary",
            use_container_width=True
        )

    with exp_c2:
        xlsx_bytes = export_prepared_excel(working_df, sheet_name="Prepared_Data")
        st.download_button(
            label="Download Prepared Dataset (Excel XLSX)",
            data=xlsx_bytes,
            file_name=f"{base_name}_prepared.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="prep_dl_xlsx",
            use_container_width=True
        )

"""
DATA STUDIO v2 — Dataset Upload and Dataset Workspace Module (Unified Redesign)
=============================================================================
Professional Dataset Workspace providing visual, structural, and behavioral
consistency with Data Quality, Data Preparation, EDA, and Visualization modules:
- Standardized Page Header & Top Context Action Bar
- 4-Card Horizontal Metric Summary Row (Rows, Columns, Completeness, Memory)
- 5 Structured Analytical Tabs:
    1. DATA PREVIEW & EXPLORER (Search, column subset selector, row slices, interactive table)
    2. COLUMN SCHEMA & ATTRIBUTES (Semantic badges, nulls, distinct counts, sample previews)
    3. STATISTICAL PROFILES (Numeric stats matrix, categorical breakdown, datetime ranges)
    4. HEALTH & INTEGRITY (Completeness audit, duplicate inspection, quick repair routing)
    5. UPLOAD & SAMPLE DATASETS (CSV/Excel upload, multi-sheet parser, sample datasets library)
- Universal Standardized Bottom Next Workflow Steps
- Full preservation of CSV/Excel parsing, session state, and Firebase logging
"""
from typing import Optional, Dict, Any, List
import html
import textwrap
import pandas as pd
import numpy as np
import streamlit as st

from modules.config import is_dataset_loaded, mark_workflow_step
from modules.auth import get_current_user
from modules.firebase_service import log_dataset_upload
from modules.ui_components import (
    render_page_header,
    render_section_header,
    render_metric_card,
    render_notification,
    render_empty_state,
    render_next_step_banner,
    render_ai_context_trigger,
    render_next_workflow_steps,
    get_type_badge_html
)
from modules.data_loader import (
    load_csv,
    load_excel,
    get_excel_sheet_names,
    load_dataset_file,
    get_available_sample_datasets,
    load_sample_dataset_by_key,
    set_active_dataset,
    clear_dataset_state,
    create_dataset_metadata
)


def render_dataset_page() -> None:
    """Main entry point for Dataset Workspace."""
    df: Optional[pd.DataFrame] = st.session_state.get("dataset")
    metadata: Optional[Dict[str, Any]] = st.session_state.get("dataset_metadata")
    dataset_name: Optional[str] = st.session_state.get("dataset_name")
    file_type: str = st.session_state.get("dataset_file_type", "CSV") or "CSV"

    # 1. Standardized Page Header
    render_page_header(
        title="Dataset",
        subtitle="Upload, inspect schema, explore statistical profiles, and manage active datasets.",
        icon="database"
    )

    # 2. Empty State: If no dataset is loaded, show dedicated Upload & Sample Data screen
    if df is None or metadata is None or not dataset_name or df.empty:
        _render_empty_upload_workspace()
        return

    # 3. Session Guard: Log dataset upload metadata once per dataset signature
    mark_workflow_step("dataset", True)
    current_sig = f"{dataset_name}_{metadata.get('total_rows', 0)}_{metadata.get('total_columns', 0)}_{metadata.get('memory_bytes', 0)}"
    if st.session_state.get("logged_dataset_signature") != current_sig:
        user_info = get_current_user()
        log_dataset_upload(user_info, metadata, file_type=file_type)
        st.session_state["logged_dataset_signature"] = current_sig

    # 4. Standardized Top Context Bar
    _render_dataset_context_bar(df, dataset_name, file_type, metadata)

    # 5. Horizontal 4-Card Metric Summary Row (Exact match to Quality & Prep)
    _render_dataset_kpis(df, metadata)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 6. Main Unified 5-Tab System
    tab_preview, tab_schema, tab_stats, tab_health, tab_upload = st.tabs([
        "DATA PREVIEW & EXPLORER",
        "COLUMN SCHEMA & ATTRIBUTES",
        "STATISTICAL PROFILES",
        "HEALTH & INTEGRITY",
        "UPLOAD & SAMPLE DATASETS"
    ])

    with tab_preview:
        _render_tab_preview(df, metadata, dataset_name)

    with tab_schema:
        _render_tab_schema(metadata)

    with tab_stats:
        _render_tab_stats(df, metadata)

    with tab_health:
        _render_tab_health(df, metadata)

    with tab_upload:
        _render_tab_upload(has_active_dataset=True)

    # 7. Standardized Bottom Workflow Steps
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    render_next_workflow_steps("Dataset")


# =============================================================================
# CONTEXT BAR & KPI METRIC CARDS
# =============================================================================

def _render_dataset_context_bar(
    df: pd.DataFrame,
    dataset_name: str,
    file_type: str,
    metadata: Dict[str, Any]
) -> None:
    """Render compact top context bar with quick dataset actions."""
    col_info, col_actions = st.columns([7, 5])

    total_rows = metadata.get("total_rows", len(df))
    total_cols = metadata.get("total_columns", len(df.columns))
    mem_str = metadata.get("memory_formatted", "0 KB")

    with col_info:
        banner_html = (
            f'<div class="ds-active-banner" style="margin-bottom: 12px; padding: 10px 16px;">'
            f'<div class="ds-active-banner-left">'
            f'<div class="ds-brand-badge" style="background: var(--accent);">{file_type[0]}</div>'
            f'<div>'
            f'<div class="ds-active-banner-name" style="font-size: 15px;">{html.escape(dataset_name)}</div>'
            f'<div class="ds-active-banner-meta" style="font-size: 12px;">'
            f'{total_rows:,} rows · {total_cols} columns · {file_type} · {mem_str} · '
            f'<span class="ds-badge ds-badge-numeric" style="font-size: 11px;">Active Dataset</span>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(banner_html, unsafe_allow_html=True)

    with col_actions:
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        ac1, ac2, ac3 = st.columns([4, 4, 4])
        with ac1:
            with st.popover("Switch Data", use_container_width=True):
                st.markdown("<span style='font-weight: 600; font-size: 13px;'>Switch Active Dataset</span>", unsafe_allow_html=True)
                sample_catalog = get_available_sample_datasets()
                if sample_catalog:
                    sample_keys = list(sample_catalog.keys())
                    sample_names = [sample_catalog[k]["name"] for k in sample_keys]
                    sel_name = st.selectbox("Select Sample Dataset", options=sample_names, key="ctx_sample_sel")
                    sel_key = next((k for k in sample_keys if sample_catalog[k]["name"] == sel_name), sample_keys[0])
                    if st.button("Load Sample", key="ctx_load_sample_btn", type="primary", use_container_width=True):
                        with st.spinner(f"Loading {sel_name}..."):
                            s_df, s_err, s_type = load_sample_dataset_by_key(sel_key)
                            if s_err:
                                st.error(s_err)
                            elif s_df is not None:
                                set_active_dataset(s_df, sample_catalog[sel_key]["filename"], file_type=s_type)
                                st.rerun()
        with ac2:
            with st.popover("Export / Clear", use_container_width=True):
                st.markdown("<span style='font-weight: 600; font-size: 13px;'>Dataset Management</span>", unsafe_allow_html=True)
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download CSV",
                    data=csv_data,
                    file_name=dataset_name if dataset_name.endswith(".csv") else f"{dataset_name}.csv",
                    mime="text/csv",
                    key="ctx_download_csv_btn",
                    use_container_width=True
                )
                if st.button("Clear Dataset", key="ctx_clear_active_btn", use_container_width=True):
                    clear_dataset_state()
                    st.rerun()
        with ac3:
            if st.button("Audit Quality →", key="ctx_goto_quality_btn", use_container_width=True):
                st.session_state["current_page"] = "Data Quality"
                st.rerun()


def _render_dataset_kpis(df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Render 4-card metric row matching Data Quality and Data Preparation."""
    total_rows = metadata.get("total_rows", len(df))
    total_cols = metadata.get("total_columns", len(df.columns))
    by_type = metadata.get("columns_by_type", {})
    num_count = len(by_type.get("Numeric", []))
    cat_count = len(by_type.get("Categorical", [])) + len(by_type.get("Text", []))
    date_count = len(by_type.get("Date/Time", []))
    bool_count = len(by_type.get("Boolean", []))

    missing_cells = metadata.get("missing_cells", 0)
    missing_pct = metadata.get("missing_percentage", 0.0)
    completeness_pct = max(0.0, 100.0 - missing_pct)
    mem_str = metadata.get("memory_formatted", "0 KB")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_metric_card(
            label="Total Records",
            value=f"{total_rows:,}",
            change="Full Row Count",
            change_type="positive",
            description="Active dataset observations",
            status="Rows"
        )
    with c2:
        breakdown_str = f"{num_count} Num · {cat_count} Cat"
        if date_count > 0:
            breakdown_str += f" · {date_count} Date"
        render_metric_card(
            label="Total Features",
            value=f"{total_cols}",
            change=breakdown_str,
            change_type="neutral",
            description="Schema dimensions",
            status="Columns"
        )
    with c3:
        comp_type = "positive" if missing_cells == 0 else ("neutral" if missing_pct < 5.0 else "negative")
        render_metric_card(
            label="Completeness Rate",
            value=f"{completeness_pct:.1f}%",
            change="Zero missing cells" if missing_cells == 0 else f"{missing_cells:,} null cells ({missing_pct:.1f}%)",
            change_type=comp_type,
            description="Data integrity index",
            status="Completeness"
        )
    with c4:
        render_metric_card(
            label="Memory Footprint",
            value=mem_str,
            change="In-Memory RAM",
            change_type="neutral",
            description=f"{file_type_label(metadata)} loaded",
            status="Storage"
        )


def file_type_label(metadata: Dict[str, Any]) -> str:
    """Return formatted file type label."""
    return st.session_state.get("dataset_file_type", "CSV")


# =============================================================================
# TAB 1: DATA PREVIEW & EXPLORER
# =============================================================================

def _render_tab_preview(df: pd.DataFrame, metadata: Dict[str, Any], dataset_name: str) -> None:
    """Render full-width searchable, filterable interactive dataframe preview."""
    all_columns = list(df.columns)

    # Control Toolbar: Search, Column Filter, Row Limits
    tool_c1, tool_c2, tool_c3 = st.columns([5, 5, 2], gap="small")

    with tool_c1:
        search_query = st.text_input(
            "Search rows...",
            placeholder="Type keyword to filter records across all columns...",
            key="tab_prev_search_input",
            label_visibility="collapsed"
        )

    with tool_c2:
        selected_cols = st.multiselect(
            "Select Columns to View",
            options=all_columns,
            default=all_columns,
            key="tab_prev_col_filter",
            label_visibility="collapsed",
            placeholder="Filter visible columns..."
        )

    with tool_c3:
        row_limit = st.selectbox(
            "Rows to Display",
            options=[15, 25, 50, 100, 250, "All"],
            index=0,
            key="tab_prev_row_limit",
            label_visibility="collapsed"
        )

    # Apply column subsetting
    display_cols = selected_cols if selected_cols else all_columns
    filtered_df = df[display_cols]

    # Apply text search filter
    if search_query and search_query.strip():
        query_str = search_query.strip().lower()
        if not filtered_df.empty and len(filtered_df.columns) > 0:
            mask = pd.Series(False, index=filtered_df.index, dtype=bool)
            for i in range(len(filtered_df.columns)):
                col_series = filtered_df.iloc[:, i]
                col_mask = col_series.astype(str).str.lower().str.contains(query_str, regex=False, na=False)
                col_mask = col_mask & (~col_series.isna())
                mask = mask | col_mask
            filtered_df = filtered_df[mask]
        else:
            filtered_df = filtered_df.iloc[0:0]

    # Apply row limits
    total_matching = len(filtered_df)
    if row_limit != "All":
        preview_df = filtered_df.head(int(row_limit))
    else:
        preview_df = filtered_df

    # Render Interactive DataFrame with full container width
    st.dataframe(
        preview_df,
        use_container_width=True,
        hide_index=False,
        height=450
    )

    # Footer Slice Information Bar
    f_c1, f_c2 = st.columns([8, 4])
    with f_c1:
        st.markdown(
            f"<span class='font-mono-data' style='color: var(--text-muted); font-size: 12px;'>"
            f"Displaying <strong>{len(preview_df):,}</strong> of <strong>{total_matching:,}</strong> matching rows · "
            f"<strong>{len(display_cols)}</strong> of <strong>{len(all_columns)}</strong> columns visible"
            f"</span>",
            unsafe_allow_html=True
        )
    with f_c2:
        st.markdown(
            f"<div style='text-align: right;' class='font-mono-data'>"
            f"<span style='color: var(--text-muted); font-size: 12px;'>Source: {html.escape(dataset_name)}</span>"
            f"</div>",
            unsafe_allow_html=True
        )


# =============================================================================
# TAB 2: COLUMN SCHEMA & ATTRIBUTES
# =============================================================================

def _render_tab_schema(metadata: Dict[str, Any]) -> None:
    """Render comprehensive tabular schema with data types, nulls, and sample previews."""
    details = metadata.get("column_details", [])
    if not details:
        st.info("No column schema details available.")
        return

    # Column type summary header pills
    by_type = metadata.get("columns_by_type", {})
    type_pills = []
    type_colors = {
        "Numeric": "ds-badge-numeric",
        "Categorical": "ds-badge-string",
        "Date/Time": "ds-badge-datetime",
        "Boolean": "ds-badge-boolean",
        "Text": "ds-badge-string"
    }
    for tname, tcols in by_type.items():
        if tcols:
            badge_cls = type_colors.get(tname, "ds-badge-neutral")
            type_pills.append(f'<span class="ds-badge {badge_cls}">{len(tcols)} {tname}</span>')

    st.markdown(
        f'<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px;">'
        f'{"".join(type_pills)}'
        f'</div>',
        unsafe_allow_html=True
    )

    # Search filter for schema columns
    s_col1, s_col2 = st.columns([6, 6])
    with s_col1:
        col_search = st.text_input(
            "Filter schema columns...",
            placeholder="Search column names or data types...",
            key="schema_col_search_input"
        )
    with s_col2:
        type_filter = st.selectbox(
            "Filter by Data Type",
            options=["All Types", "Numeric", "Categorical", "Date/Time", "Boolean", "Text"],
            key="schema_type_filter_sel"
        )

    # Build schema rows
    filtered_details = details
    if col_search and col_search.strip():
        q = col_search.strip().lower()
        filtered_details = [c for c in filtered_details if q in c["column_name"].lower() or q in c["detected_type"].lower()]

    if type_filter != "All Types":
        filtered_details = [c for c in filtered_details if c["detected_type"] == type_filter]

    table_data = []
    for c in filtered_details:
        table_data.append({
            "Column Name": c["column_name"],
            "Semantic Type": c["detected_type"],
            "Pandas Dtype": c["pandas_dtype"],
            "Non-Null Count": f"{c['non_null_count']:,}",
            "Missing Count": f"{c['missing_count']:,}",
            "Missing %": f"{c['missing_percentage']:.2f}%",
            "Unique Count": f"{c['unique_count']:,}",
            "Sample Values": c["sample_preview"]
        })

    st.dataframe(
        pd.DataFrame(table_data),
        use_container_width=True,
        hide_index=True,
        height=400
    )


# =============================================================================
# TAB 3: STATISTICAL PROFILES
# =============================================================================

def _render_tab_stats(df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Render numeric descriptive statistics and categorical frequency breakdowns."""
    numeric_cols = metadata.get("columns_by_type", {}).get("Numeric", [])
    cat_cols = metadata.get("columns_by_type", {}).get("Categorical", []) + metadata.get("columns_by_type", {}).get("Text", [])
    date_cols = metadata.get("columns_by_type", {}).get("Date/Time", [])

    # 1. Numeric Summary Statistics Matrix
    st.markdown("#### Numeric Summary Statistics")
    if numeric_cols:
        num_df = df[numeric_cols]
        desc_df = num_df.describe().T
        # Calculate extra statistical dimensions: Median, Skewness, Zeros Count
        desc_df["median"] = num_df.median()
        desc_df["skew"] = num_df.skew()
        desc_df["zeros_count"] = (num_df == 0).sum()

        formatted_stats = []
        for col_name, row in desc_df.iterrows():
            formatted_stats.append({
                "Column": col_name,
                "Count": f"{int(row['count']):,}",
                "Mean": f"{row['mean']:.2f}",
                "Std Dev": f"{row['std']:.2f}" if not pd.isna(row['std']) else "—",
                "Min": f"{row['min']:.2f}",
                "25%": f"{row['25%']:.2f}",
                "Median (50%)": f"{row['median']:.2f}",
                "75%": f"{row['75%']:.2f}",
                "Max": f"{row['max']:.2f}",
                "Skewness": f"{row['skew']:.2f}" if not pd.isna(row['skew']) else "—",
                "Zeros": f"{int(row['zeros_count']):,}"
            })

        st.dataframe(pd.DataFrame(formatted_stats), use_container_width=True, hide_index=True)
    else:
        st.info("No numerical columns detected in this dataset.")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 2. Categorical & Text Frequency Breakdown
    st.markdown("#### Categorical & Text Cardinality")
    if cat_cols:
        cat_stats = []
        for col_name in cat_cols:
            series = df[col_name].dropna()
            total_cnt = len(series)
            uniq_cnt = series.nunique()
            if total_cnt > 0:
                top_val = str(series.mode().iloc[0]) if not series.empty else "—"
                top_freq = int(series.value_counts().iloc[0]) if not series.empty else 0
                top_pct = (top_freq / total_cnt * 100) if total_cnt > 0 else 0.0
                uniq_ratio = (uniq_cnt / total_cnt * 100) if total_cnt > 0 else 0.0
            else:
                top_val = "—"
                top_freq = 0
                top_pct = 0.0
                uniq_ratio = 0.0

            cat_stats.append({
                "Column": col_name,
                "Total Values": f"{total_cnt:,}",
                "Distinct Categories": f"{uniq_cnt:,}",
                "Uniqueness Ratio": f"{uniq_ratio:.1f}%",
                "Top (Most Frequent)": top_val,
                "Top Frequency": f"{top_freq:,} ({top_pct:.1f}%)"
            })

        st.dataframe(pd.DataFrame(cat_stats), use_container_width=True, hide_index=True)
    else:
        st.info("No categorical or text columns detected.")

    # 3. Date / Time Temporal Ranges
    if date_cols:
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("#### Temporal & Date Ranges")
        date_stats = []
        for col_name in date_cols:
            try:
                parsed_dates = pd.to_datetime(df[col_name], errors='coerce').dropna()
                if not parsed_dates.empty:
                    min_date = parsed_dates.min().strftime('%Y-%m-%d')
                    max_date = parsed_dates.max().strftime('%Y-%m-%d')
                    span_days = (parsed_dates.max() - parsed_dates.min()).days
                    date_stats.append({
                        "Column": col_name,
                        "Valid Dates Count": f"{len(parsed_dates):,}",
                        "Earliest Date": min_date,
                        "Latest Date": max_date,
                        "Date Span": f"{span_days:,} days"
                    })
            except Exception:
                pass

        if date_stats:
            st.dataframe(pd.DataFrame(date_stats), use_container_width=True, hide_index=True)


# =============================================================================
# TAB 4: HEALTH & INTEGRITY
# =============================================================================

def _render_tab_health(df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Render missing data summary, duplicate row audit, and direct repair links."""
    h_col1, h_col2 = st.columns(2, gap="large")

    missing_cnt = metadata.get("missing_cells", 0)
    missing_pct = metadata.get("missing_percentage", 0.0)
    missing_cols = [c for c in metadata.get("column_details", []) if c["missing_count"] > 0]

    dup_cnt = metadata.get("duplicate_rows", 0)
    dup_pct = metadata.get("duplicate_percentage", 0.0)

    with h_col1:
        st.markdown("#### Missing Values Audit")
        if missing_cnt == 0:
            st.success("✅ **100% Complete**: Zero missing values detected across all columns.")
        else:
            st.warning(f"⚠️ **{missing_cnt:,} missing cells** detected ({missing_pct:.2f}% of total data cells).")
            st.markdown(f"**{len(missing_cols)} column(s)** contain missing values:")
            st.dataframe(pd.DataFrame([
                {
                    "Column": c["column_name"],
                    "Missing Count": f"{c['missing_count']:,}",
                    "Missing %": f"{c['missing_percentage']:.2f}%",
                    "Semantic Type": c["detected_type"]
                }
                for c in missing_cols
            ]), use_container_width=True, hide_index=True)

            if st.button("Impute in Data Preparation →", key="hlth_goto_prep_missing_btn", type="primary", use_container_width=True):
                st.session_state["prep_suggested_action"] = "missing"
                st.session_state["current_page"] = "Data Preparation"
                st.rerun()

    with h_col2:
        st.markdown("#### Duplicate Records Audit")
        if dup_cnt == 0:
            st.success("✅ **100% Unique**: Every record in the dataset is unique.")
        else:
            st.warning(f"⚠️ **{dup_cnt:,} duplicate rows** found ({dup_pct:.2f}% of dataset).")
            dup_mask = df.duplicated(keep=False)
            dup_df = df[dup_mask]
            if not dup_df.empty:
                st.markdown(f"**Duplicate Records Preview ({len(dup_df):,} occurrences):**")
                st.dataframe(dup_df.head(20), use_container_width=True, hide_index=False)

            if st.button("Deduplicate in Data Preparation →", key="hlth_goto_prep_dup_btn", type="primary", use_container_width=True):
                st.session_state["prep_suggested_action"] = "duplicates"
                st.session_state["current_page"] = "Data Preparation"
                st.rerun()

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Comprehensive Audit Jump Banner
    act_c1, act_c2 = st.columns([8, 4])
    with act_c1:
        st.markdown(
            "**Need an in-depth 6-dimension data quality audit?**<br>"
            "<span style='color: var(--text-secondary); font-size: 13px;'>"
            "Inspect completeness, uniqueness, consistency, validity, and outlier distribution in the Data Quality module."
            "</span>",
            unsafe_allow_html=True
        )
    with act_c2:
        if st.button("Open Full Data Quality Audit →", key="hlth_open_quality_module_btn", use_container_width=True):
            st.session_state["current_page"] = "Data Quality"
            st.rerun()


# =============================================================================
# TAB 5 / EMPTY STATE: UPLOAD & SAMPLE DATASETS
# =============================================================================

def _render_tab_upload(has_active_dataset: bool = True) -> None:
    """Render upload file dropzone and sample datasets catalog."""
    if has_active_dataset:
        st.info("💡 Uploading or selecting a new dataset will replace the currently active workspace dataset.")

    u_col1, u_col2 = st.columns([6, 6], gap="large")

    with u_col1:
        st.markdown("#### Upload Dataset File")
        uploaded_file = st.file_uploader(
            "Upload CSV or Excel file",
            type=["csv", "xlsx", "xls"],
            key="tab_upload_file_picker",
            help="Drag and drop CSV or Excel files up to 200 MB"
        )

        if uploaded_file is not None:
            filename = uploaded_file.name
            ext = filename.split(".")[-1].lower()

            if ext in ["xlsx", "xls"]:
                sheet_names, sheet_err = get_excel_sheet_names(uploaded_file)
                if sheet_err:
                    render_notification(title="Excel Inspection Failed", message=sheet_err, variant="error")
                elif len(sheet_names) > 1:
                    st.info(f"Excel workbook contains {len(sheet_names)} worksheets:")
                    selected_sheet = st.selectbox("Select Worksheet", options=sheet_names, key="tab_excel_sheet_sel")
                    if st.button("Load Selected Worksheet", key="tab_load_sheet_btn", type="primary", use_container_width=True):
                        with st.spinner("Parsing Excel worksheet..."):
                            parsed_df, err, ftype = load_dataset_file(uploaded_file, filename, sheet_name=selected_sheet)
                            if err:
                                st.error(err)
                            elif parsed_df is not None:
                                set_active_dataset(parsed_df, f"{filename} ({selected_sheet})", file_type="Excel")
                                st.success("Dataset loaded successfully!")
                                st.rerun()
                else:
                    sheet_to_load = sheet_names[0] if sheet_names else None
                    if st.button("Load Excel Dataset", key="tab_load_single_excel_btn", type="primary", use_container_width=True):
                        with st.spinner("Parsing Excel file..."):
                            parsed_df, err, ftype = load_dataset_file(uploaded_file, filename, sheet_name=sheet_to_load)
                            if err:
                                st.error(err)
                            elif parsed_df is not None:
                                set_active_dataset(parsed_df, filename, file_type="Excel")
                                st.success("Dataset loaded successfully!")
                                st.rerun()
            else:
                if st.button("Load Uploaded CSV", key="tab_load_csv_btn", type="primary", use_container_width=True):
                    with st.spinner("Decoding CSV dataset..."):
                        parsed_df, err, ftype = load_dataset_file(uploaded_file, filename)
                        if err:
                            st.error(err)
                        elif parsed_df is not None:
                            set_active_dataset(parsed_df, filename, file_type="CSV")
                            st.success("Dataset loaded successfully!")
                            st.rerun()

    with u_col2:
        st.markdown("#### Sample Datasets Library")
        st.markdown(
            "<span style='color: var(--text-secondary); font-size: 13px;'>"
            "Select from pre-configured sample datasets to explore Data Studio instantly."
            "</span>",
            unsafe_allow_html=True
        )

        sample_catalog = get_available_sample_datasets()
        if sample_catalog:
            sample_keys = list(sample_catalog.keys())
            sample_names = [sample_catalog[k]["name"] for k in sample_keys]

            selected_sample_name = st.selectbox(
                "Choose Sample Dataset",
                options=sample_names,
                key="tab_sample_dataset_sel"
            )
            selected_sample_key = next((k for k in sample_keys if sample_catalog[k]["name"] == selected_sample_name), sample_keys[0])
            selected_info = sample_catalog[selected_sample_key]

            st.markdown(
                f"<div style='background: var(--surface-container); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px; margin: 12px 0;'>"
                f"<div style='font-weight: 600; color: var(--text-primary); font-size: 14px;'>{selected_info['name']}</div>"
                f"<div style='color: var(--text-secondary); font-size: 12.5px; margin-top: 4px;'>{selected_info.get('description', 'Pre-configured business intelligence dataset.')}</div>"
                f"<div style='color: var(--text-muted); font-size: 11.5px; margin-top: 6px;' class='font-mono-data'>File: {selected_info['filename']}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

            if st.button("Load This Sample Dataset", key="tab_load_sample_btn", type="primary", use_container_width=True):
                with st.spinner(f"Loading {selected_sample_name}..."):
                    s_df, s_err, s_type = load_sample_dataset_by_key(selected_sample_key)
                    if s_err:
                        st.error(s_err)
                    elif s_df is not None:
                        set_active_dataset(s_df, selected_info["filename"], file_type=s_type)
                        st.success(f"{selected_sample_name} loaded successfully!")
                        st.rerun()


def _render_empty_upload_workspace() -> None:
    """Render full empty state screen when no dataset is loaded."""
    render_empty_state(
        title="No Dataset Loaded",
        description="Upload a CSV or Excel file, or choose from our sample dataset library to begin your analytical workflow.",
        icon="database"
    )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    _render_tab_upload(has_active_dataset=False)

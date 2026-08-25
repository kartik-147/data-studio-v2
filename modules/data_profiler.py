"""
DATA STUDIO v2 — Dataset Upload and Dataset Workspace Module (Module 2)
=============================================================================
Professional Dataset Workspace providing file uploading (CSV, XLSX, XLS),
sample dataset loading, schema profiling, semantic type classification,
and interactive dataset inspection.
"""
from typing import Optional, Dict, Any, List
import pandas as pd
import streamlit as st

from modules.config import is_dataset_loaded
from modules.auth import get_current_user
from modules.firebase_service import log_dataset_upload
from modules.ui_components import (
    render_page_header,
    render_section_header,
    render_metric_card,
    render_notification,
    render_empty_state,
    get_icon_svg,
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
    clear_dataset_state
)


def render_dataset_page() -> None:
    """Main entry point for Dataset Upload and Dataset Workspace (Module 2)."""
    # Standardized Page Header
    render_page_header(
        title="Dataset",
        subtitle="Upload and inspect your data before starting the analysis.",
        icon="database"
    )

    if not is_dataset_loaded():
        _render_upload_experience()
    else:
        _render_dataset_workspace()


# =============================================================================
# UPLOAD EXPERIENCE & EMPTY STATE
# =============================================================================

def _render_upload_experience() -> None:
    """Render the primary upload interface and sample data selection when no dataset is active."""
    render_empty_state(
        title="Upload a dataset to start your analysis",
        description="Upload your CSV or Excel file to inspect records, detect schema types, and unlock analytical modules.",
        icon="upload"
    )

    col_upload, col_sample = st.columns([6, 5], gap="large")

    with col_upload:
        st.markdown("#### Upload Data File")
        st.caption("Supported file formats: **CSV, XLSX, XLS** (Max file size: 200 MB)")
        
        uploaded_file = st.file_uploader(
            "Upload file",
            type=["csv", "xlsx", "xls"],
            key="dataset_file_uploader",
            label_visibility="collapsed"
        )

        if uploaded_file is not None:
            filename = uploaded_file.name
            ext = filename.split(".")[-1].lower()

            if ext in ["xlsx", "xls"]:
                # Multi-sheet Excel inspection
                sheet_names, sheet_err = get_excel_sheet_names(uploaded_file)
                if sheet_err:
                    render_notification(
                        title="Excel Inspection Failed",
                        message=sheet_err,
                        variant="error"
                    )
                elif len(sheet_names) > 1:
                    st.info(f"Excel workbook contains {len(sheet_names)} worksheets. Please select a sheet:")
                    selected_sheet = st.selectbox(
                        "Worksheet",
                        options=sheet_names,
                        key="excel_sheet_selector"
                    )
                    if st.button("Load Worksheet", key="load_excel_sheet_btn", type="primary", use_container_width=True):
                        with st.spinner("Parsing Excel worksheet..."):
                            df, err, file_type = load_dataset_file(uploaded_file, filename, sheet_name=selected_sheet)
                            if err:
                                render_notification(title="Upload Failed", message=err, variant="error")
                            elif df is not None:
                                set_active_dataset(df, f"{filename} ({selected_sheet})", file_type="Excel")
                                st.rerun()
                else:
                    # Single sheet Excel
                    sheet_to_load = sheet_names[0] if sheet_names else None
                    if st.button("Load Excel Dataset", key="load_single_excel_btn", type="primary", use_container_width=True):
                        with st.spinner("Parsing Excel file..."):
                            df, err, file_type = load_dataset_file(uploaded_file, filename, sheet_name=sheet_to_load)
                            if err:
                                render_notification(title="Upload Failed", message=err, variant="error")
                            elif df is not None:
                                set_active_dataset(df, filename, file_type="Excel")
                                st.rerun()
            else:
                # CSV File
                if st.button("Load CSV Dataset", key="load_csv_file_btn", type="primary", use_container_width=True):
                    with st.spinner("Decoding and validating CSV file..."):
                        df, err, file_type = load_dataset_file(uploaded_file, filename)
                        if err:
                            render_notification(title="Upload Failed", message=err, variant="error")
                        elif df is not None:
                            set_active_dataset(df, filename, file_type="CSV")
                            st.rerun()

    with col_sample:
        st.markdown("#### Load Sample Dataset")
        st.caption("Quickly test Data Studio with curated real-world analytics datasets.")
        
        sample_catalog = get_available_sample_datasets()
        if sample_catalog:
            sample_keys = list(sample_catalog.keys())
            sample_options = [sample_catalog[k]["name"] for k in sample_keys]
            
            selected_name = st.selectbox(
                "Select Sample Dataset",
                options=sample_options,
                key="sample_dataset_selector"
            )
            
            # Find selected catalog entry
            selected_key = next((k for k in sample_keys if sample_catalog[k]["name"] == selected_name), sample_keys[0])
            sample_info = sample_catalog[selected_key]
            
            sample_html = (
                f'<div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: var(--space-4); margin-bottom: var(--space-4);">'
                f'<div style="font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px;">{sample_info["name"]}</div>'
                f'<div style="font-size: 12px; color: var(--text-secondary); line-height: 1.4;">{sample_info["description"]}</div>'
                f'<div style="margin-top: 8px; font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">Format: {sample_info["file_type"]} • Source: sample_data/{sample_info["filename"]}</div>'
                f'</div>'
            )
            st.markdown(sample_html, unsafe_allow_html=True)
            
            if st.button("Load Sample Dataset", key="load_sample_btn", use_container_width=True):
                with st.spinner(f"Loading {sample_info['name']}..."):
                    df, err, file_type = load_sample_dataset_by_key(selected_key)
                    if err:
                        render_notification(title="Sample Load Failed", message=err, variant="error")
                    elif df is not None:
                        set_active_dataset(df, sample_info["filename"], file_type=file_type)
                        st.rerun()
        else:
            st.info("No sample datasets currently detected in the sample_data/ directory.")


# =============================================================================
# ACTIVE DATASET WORKSPACE
# =============================================================================

def _render_dataset_workspace() -> None:
    """Render the active Dataset Workspace with summary metrics, preview, schema, and type tabs."""
    df: pd.DataFrame = st.session_state.get("dataset")
    metadata: Dict[str, Any] = st.session_state.get("dataset_metadata")
    dataset_name = st.session_state.get("dataset_name", "dataset.csv")
    file_type = st.session_state.get("dataset_file_type", "CSV")

    if df is None or metadata is None:
        render_notification(
            title="Dataset State Error",
            message="Active dataset data was not found in session state. Please reload your dataset.",
            variant="error"
        )
        if st.button("Return to Upload", key="err_return_upload_btn"):
            clear_dataset_state()
            st.rerun()
        return

    # Top Workspace Controls: Active Dataset Indicator & Replacement Options
    _render_workspace_action_bar(dataset_name, file_type, metadata)

    # Session Guard: Log dataset upload metadata once per dataset signature
    current_sig = f"{dataset_name}_{metadata.get('total_rows', 0)}_{metadata.get('total_columns', 0)}_{metadata.get('memory_bytes', 0)}"
    if st.session_state.get("logged_dataset_signature") != current_sig:
        user_info = get_current_user()
        log_dataset_upload(user_info, metadata, file_type=file_type)
        st.session_state["logged_dataset_signature"] = current_sig

    # 4 Key Summary Metric Cards
    _render_metric_summary_grid(metadata)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Dataset Workspace Tabs
    tab_overview, tab_preview, tab_columns, tab_datatypes = st.tabs([
        "OVERVIEW",
        "PREVIEW",
        "COLUMNS",
        "DATA TYPES"
    ])

    with tab_overview:
        _render_tab_overview(df, metadata)

    with tab_preview:
        _render_tab_preview(df, metadata)

    with tab_columns:
        _render_tab_columns(metadata)

    with tab_datatypes:
        _render_tab_datatypes(df, metadata)


# =============================================================================
# WORKSPACE COMPONENTS & TABS
# =============================================================================

def _render_workspace_action_bar(name: str, file_type: str, metadata: Dict[str, Any]) -> None:
    """Render the active dataset header and management actions."""
    col_info, col_actions = st.columns([7, 5])
    
    with col_info:
        banner_html = (
            f'<div class="ds-active-banner" style="margin-bottom: 12px; padding: 12px 16px;">'
            f'<div class="ds-active-banner-left">'
            f'<div class="ds-brand-badge" style="background: var(--accent);">{file_type[0]}</div>'
            f'<div>'
            f'<div class="ds-active-banner-name">{name}</div>'
            f'<div class="ds-active-banner-meta">'
            f'{metadata["total_rows"]:,} rows • {metadata["total_columns"]} columns • {metadata["memory_formatted"]} • {file_type}'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(banner_html, unsafe_allow_html=True)

    with col_actions:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        act_c1, act_c2 = st.columns(2)
        with act_c1:
            with st.popover("Replace Dataset", use_container_width=True):
                st.markdown("##### Replace Active Dataset")
                st.caption("Replacing the dataset will reset current analysis.")
                
                new_file = st.file_uploader(
                    "Upload new file",
                    type=["csv", "xlsx", "xls"],
                    key="replace_file_uploader"
                )
                if new_file is not None:
                    if st.button("Confirm & Replace", key="confirm_replace_btn", type="primary", use_container_width=True):
                        with st.spinner("Loading new dataset..."):
                            new_df, err, new_type = load_dataset_file(new_file, new_file.name)
                            if err:
                                st.error(err)
                            elif new_df is not None:
                                clear_dataset_state()
                                set_active_dataset(new_df, new_file.name, file_type=new_type)
                                st.rerun()
                                
                st.divider()
                st.markdown("###### Or select a sample dataset:")
                sample_cat = get_available_sample_datasets()
                sample_opts = [sample_cat[k]["name"] for k in sample_cat]
                chosen_sample = st.selectbox("Sample Data", sample_opts, key="replace_sample_select")
                if st.button("Load Sample", key="replace_sample_confirm_btn", use_container_width=True):
                    chosen_key = next((k for k in sample_cat if sample_cat[k]["name"] == chosen_sample), list(sample_cat.keys())[0])
                    s_df, s_err, s_type = load_sample_dataset_by_key(chosen_key)
                    if s_df is not None:
                        clear_dataset_state()
                        set_active_dataset(s_df, sample_cat[chosen_key]["filename"], file_type=s_type)
                        st.rerun()

        with act_c2:
            if st.button("Clear Dataset", key="workspace_clear_dataset_btn", use_container_width=True):
                clear_dataset_state()
                st.rerun()


def _render_metric_summary_grid(metadata: Dict[str, Any]) -> None:
    """Render balanced 4-column summary metric cards."""
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_metric_card(
            label="Total Records",
            value=f"{metadata['total_rows']:,}",
            description=f"{metadata['total_columns']} Columns",
            status="Dimensions"
        )

    with c2:
        render_metric_card(
            label="Total Data Cells",
            value=f"{metadata['total_cells']:,}",
            description=f"{metadata['memory_formatted']} memory",
            status="Storage"
        )

    with c3:
        missing_cnt = metadata["missing_cells"]
        missing_pct = metadata["missing_percentage"]
        change_type = "positive" if missing_cnt == 0 else ("neutral" if missing_pct < 5 else "negative")
        status_txt = "Clean" if missing_cnt == 0 else "Missing"
        
        render_metric_card(
            label="Missing Values",
            value=f"{missing_cnt:,}",
            change=f"{missing_pct:.2f}%" if missing_cnt > 0 else "0.00%",
            change_type=change_type,
            description="Complete" if missing_cnt == 0 else f"{metadata['columns_with_missing']} column(s) affected",
            status=status_txt
        )

    with c4:
        dup_cnt = metadata["duplicate_rows"]
        dup_pct = metadata["duplicate_percentage"]
        dup_change_type = "positive" if dup_cnt == 0 else "negative"
        dup_status = "Unique" if dup_cnt == 0 else "Duplicates"
        
        render_metric_card(
            label="Duplicate Rows",
            value=f"{dup_cnt:,}",
            change=f"{dup_pct:.2f}%" if dup_cnt > 0 else "0.00%",
            change_type=dup_change_type,
            description="All records unique" if dup_cnt == 0 else f"{dup_cnt} duplicate rows",
            status=dup_status
        )


def _render_tab_overview(df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Render the Overview Tab: type distribution chips, missing summary, duplicate health."""
    render_section_header(
        title="Column Type Distribution",
        subtitle="Semantic classification breakdown across the dataset schema."
    )

    # 5 Semantic Type Summary Cards
    counts = metadata["column_types_count"]
    t1, t2, t3, t4, t5 = st.columns(5)
    
    with t1:
        st.markdown(
            f'<div class="ds-type-box">'
            f'<div class="ds-type-box-label">Numeric</div>'
            f'<div class="ds-type-box-val">{counts.get("Numeric", 0)}</div>'
            f'<div style="font-size: 11px; color: #60a5fa;">Quantitative metrics</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with t2:
        st.markdown(
            f'<div class="ds-type-box">'
            f'<div class="ds-type-box-label">Categorical</div>'
            f'<div class="ds-type-box-val">{counts.get("Categorical", 0)}</div>'
            f'<div style="font-size: 11px; color: #c084fc;">Discrete groups</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with t3:
        st.markdown(
            f'<div class="ds-type-box">'
            f'<div class="ds-type-box-label">Date / Time</div>'
            f'<div class="ds-type-box-val">{counts.get("Date/Time", 0)}</div>'
            f'<div style="font-size: 11px; color: #34d399;">Temporal series</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with t4:
        st.markdown(
            f'<div class="ds-type-box">'
            f'<div class="ds-type-box-label">Text</div>'
            f'<div class="ds-type-box-val">{counts.get("Text", 0)}</div>'
            f'<div style="font-size: 11px; color: #fbbf24;">Strings & Identifiers</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with t5:
        st.markdown(
            f'<div class="ds-type-box">'
            f'<div class="ds-type-box-label">Boolean</div>'
            f'<div class="ds-type-box-val">{counts.get("Boolean", 0)}</div>'
            f'<div style="font-size: 11px; color: #f472b6;">Binary flags</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Missing Values and Duplicates Summary
    col_missing, col_dup = st.columns(2, gap="medium")
    
    with col_missing:
        render_section_header(
            title="Missing Values Summary",
            subtitle="Data completeness across features."
        )
        if metadata["missing_cells"] == 0:
            render_notification(
                title="100% Complete Dataset",
                message="Zero missing or null values were detected across all rows and columns.",
                variant="success"
            )
        else:
            render_notification(
                title=f"{metadata['missing_cells']:,} Missing Values ({metadata['missing_percentage']:.2f}%)",
                message=f"{metadata['columns_with_missing']} of {metadata['total_columns']} columns contain missing data.",
                variant="warning"
            )
            # Show list of columns with missing values
            missing_cols = [
                c for c in metadata["column_details"] if c["missing_count"] > 0
            ]
            if missing_cols:
                missing_df = pd.DataFrame([
                    {
                        "Column": c["column_name"],
                        "Type": c["detected_type"],
                        "Missing": c["missing_count"],
                        "Missing %": f"{c['missing_percentage']:.2f}%"
                    }
                    for c in missing_cols
                ])
                st.dataframe(missing_df, use_container_width=True, hide_index=True)

    with col_dup:
        render_section_header(
            title="Duplicate Rows Summary",
            subtitle="Record-level redundancy check."
        )
        if metadata["duplicate_rows"] == 0:
            render_notification(
                title="No Duplicate Rows",
                message="Every row in this dataset represents a distinct unique record.",
                variant="success"
            )
        else:
            render_notification(
                title=f"{metadata['duplicate_rows']:,} Duplicate Rows Detected ({metadata['duplicate_percentage']:.2f}%)",
                message="Duplicate rows can be audited in Data Quality and deduplicated in Data Preparation.",
                variant="warning"
            )


def _render_tab_preview(df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Render the Preview Tab with customizable row count and interactive table."""
    render_section_header(
        title="Dataset Record Preview",
        subtitle="Explore raw tabular data records and schema alignments."
    )

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([3, 3, 4])
    
    with ctrl_col1:
        row_limit = st.selectbox(
            "Show rows",
            options=[25, 50, 100, "All"],
            index=0,
            key="preview_row_limit_select"
        )
        
    with ctrl_col2:
        view_mode = st.selectbox(
            "View slice",
            options=["First N rows", "Last N rows", "Random sample"],
            index=0,
            key="preview_view_mode_select"
        )

    with ctrl_col3:
        column_filter = st.multiselect(
            "Filter visible columns",
            options=list(df.columns),
            default=[],
            placeholder="All columns displayed",
            key="preview_col_filter_select"
        )

    # Slice dataframe
    display_df = df[column_filter] if column_filter else df
    total_len = len(display_df)

    if row_limit == "All":
        n_rows = total_len
    else:
        n_rows = min(int(row_limit), total_len)

    if view_mode == "First N rows":
        preview_slice = display_df.head(n_rows)
    elif view_mode == "Last N rows":
        preview_slice = display_df.tail(n_rows)
    else:
        preview_slice = display_df.sample(n=n_rows, random_state=42) if total_len > 0 else display_df

    # Render styled preview table
    st.dataframe(
        preview_slice,
        use_container_width=True,
        hide_index=False
    )
    
    st.caption(f"Showing **{len(preview_slice):,}** of **{total_len:,}** records • **{len(display_df.columns)}** visible columns")


def _render_tab_columns(metadata: Dict[str, Any]) -> None:
    """Render the Columns Tab: detailed column profiling, null count, and missing rates."""
    render_section_header(
        title="Column Schema & Profile",
        subtitle="Comprehensive breakdown of data types, completeness, and cardinality."
    )

    search_col, sort_col = st.columns([6, 4])
    with search_col:
        search_query = st.text_input(
            "Search columns",
            placeholder="Type column name to filter...",
            key="col_search_input",
            label_visibility="collapsed"
        )
    with sort_col:
        sort_by = st.selectbox(
            "Sort by",
            options=["Original Order", "Missing % (High to Low)", "Unique Values (High to Low)", "Column Name (A-Z)"],
            index=0,
            key="col_sort_select",
            label_visibility="collapsed"
        )

    details = metadata["column_details"]
    
    # Filter by search
    if search_query:
        details = [c for c in details if search_query.lower() in c["column_name"].lower()]

    # Sort
    if sort_by == "Missing % (High to Low)":
        details = sorted(details, key=lambda x: x["missing_percentage"], reverse=True)
    elif sort_by == "Unique Values (High to Low)":
        details = sorted(details, key=lambda x: x["unique_count"], reverse=True)
    elif sort_by == "Column Name (A-Z)":
        details = sorted(details, key=lambda x: x["column_name"].lower())

    # Build clean formatted DataFrame
    col_table_data = []
    for c in details:
        col_table_data.append({
            "Column Name": c["column_name"],
            "Detected Type": c["detected_type"],
            "Pandas Dtype": c["pandas_dtype"],
            "Non-Null Count": f"{c['non_null_count']:,}",
            "Missing Count": f"{c['missing_count']:,}",
            "Missing %": f"{c['missing_percentage']:.2f}%",
            "Unique Count": f"{c['unique_count']:,}",
            "Sample Values": c["sample_preview"]
        })

    if col_table_data:
        col_summary_df = pd.DataFrame(col_table_data)
        st.dataframe(
            col_summary_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No columns match the search query.")


def _render_tab_datatypes(df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Render the Data Types Tab: grouped column listings and semantic classification rationale."""
    render_section_header(
        title="Semantic Data Types",
        subtitle="Columns grouped by their detected analytical classification."
    )

    by_type = metadata["columns_by_type"]
    
    type_descriptions = {
        "Numeric": "Continuous or discrete numerical measurements suitable for aggregation, mathematical transformations, and statistical modeling.",
        "Categorical": "Discrete labels or categories with bounded cardinality, suitable for grouping, filtering, and cross-tabulation.",
        "Date/Time": "Temporal features (dates, timestamps, periods) suitable for chronological sorting, trend analysis, and time-series decomposition.",
        "Text": "Free-form strings or high-cardinality alphanumeric identifiers (e.g. Customer ID, Order ID, UUIDs, descriptions).",
        "Boolean": "Binary logical values (True/False, 1/0, Yes/No) representing states or flags."
    }

    for type_name in ["Numeric", "Categorical", "Date/Time", "Text", "Boolean"]:
        cols = by_type.get(type_name, [])
        badge_html = get_type_badge_html(type_name)
        
        with st.expander(f"{type_name} Columns ({len(cols)})", expanded=len(cols) > 0):
            st.caption(type_descriptions.get(type_name, ""))
            
            if cols:
                # Show cards/table of columns with sample values
                items = []
                for c in cols:
                    sample_vals = df[c].dropna().head(3).tolist()
                    sample_str = ", ".join([str(v) for v in sample_vals]) if sample_vals else "—"
                    items.append({
                        "Column": c,
                        "Pandas Dtype": str(df[c].dtype),
                        "Unique Values": f"{df[c].nunique():,}",
                        "Sample Preview": sample_str
                    })
                
                st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)
            else:
                st.caption(f"No {type_name.lower()} columns detected in this dataset.")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Classification Guide
    render_notification(
        title="Intelligent Classification Engine",
        message="Data Studio evaluates Pandas dtypes, cardinality ratios, date patterns, and identifier naming conventions (e.g. preserving Customer_ID and Order_ID as Text identifiers rather than aggregatable numbers).",
        variant="info"
    )

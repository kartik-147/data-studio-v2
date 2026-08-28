"""
DATA STUDIO v2 — Dataset Upload and Dataset Workspace Module (Stitch Redesign)
=============================================================================
Professional Dataset Workspace implementing the Stitch Design System:
- 12-column analytical grid layout (8 cols left, 4 cols right)
- High-density data table with zebra striping, sticky headers, and tabular figures
- 2x2 Bento KPI grid for core dataset dimensions
- Column Summary with semantic iconography and data type badges
- Dataset Health and Next Steps action cards
- Full preservation of CSV/Excel parsing, session state, and Firebase logging
"""
from typing import Optional, Dict, Any, List
import html
import textwrap
import pandas as pd
import numpy as np
import streamlit as st

from modules.config import is_dataset_loaded
from modules.auth import get_current_user
from modules.firebase_service import log_dataset_upload
from modules.ui_components import (
    render_notification,
    get_type_badge_html,
    render_next_step_banner,
    render_ai_context_trigger,
    render_next_workflow_steps
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
    """Main entry point for Dataset Workspace (Stitch Design System)."""
    # ── Page Header ─────────────────────────────────────────────────────────
    st.markdown(
        textwrap.dedent("""
        <div class="stitch-page-header">
            <h1 class="stitch-page-title font-headline-md">Dataset</h1>
            <p class="stitch-page-subtitle font-body-lg">Upload, inspect, and manage the dataset used across your workspace.</p>
        </div>
        """),
        unsafe_allow_html=True
    )

    df: Optional[pd.DataFrame] = st.session_state.get("dataset")
    metadata: Optional[Dict[str, Any]] = st.session_state.get("dataset_metadata")
    dataset_name: Optional[str] = st.session_state.get("dataset_name")
    file_type: str = st.session_state.get("dataset_file_type", "CSV") or "CSV"

    # 12-Column Responsive Grid (8 col left, 4 col right)
    col_left, col_right = st.columns([8, 4], gap="medium")

    with col_left:
        if df is None or metadata is None or not dataset_name:
            # Upload box is shown only when no dataset is currently active
            _render_upload_section(has_active_dataset=False)
        else:
            # When active dataset exists, show the full preview card and management tools
            _render_active_dataset_preview_card(df, metadata, dataset_name, file_type)

    with col_right:
        if df is not None and metadata is not None:
            _render_dataset_health_card(metadata)
            _render_bento_kpis(metadata)
            _render_column_summary_card(metadata)
        else:
            _render_empty_sidebar_guide()

    # ── Deep-Dive Technical Tabs (Retains 100% full profiling power) ─────────
    if df is not None and metadata is not None:
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        with st.expander("Detailed Schema & Semantic Profiling (Advanced Inspection)", expanded=False):
            tab_cols, tab_types, tab_missing = st.tabs([
                "FULL COLUMN SCHEMA",
                "SEMANTIC DATA TYPES",
                "COMPLETENESS & DUPLICATES"
            ])
            with tab_cols:
                _render_full_column_schema(metadata)
            with tab_types:
                _render_semantic_datatypes_tab(df, metadata)
            with tab_missing:
                _render_missing_and_duplicates_tab(df, metadata)

        # ── Standardized Bottom Next Workflow Steps Section ──────────────────
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        render_next_workflow_steps("Dataset")



# =============================================================================
# LEFT COLUMN: UPLOAD & ACTIVE DATASET PREVIEW
# =============================================================================

def _render_upload_section(has_active_dataset: bool = False) -> None:
    """Render the Stitch dashed upload dropzone with CSV/Excel parsing and sample datasets."""
    st.markdown(
        textwrap.dedent("""
        <div class="stitch-upload-card">
            <div class="stitch-upload-icon-circle">
                <span class="mat-icon" style="font-size: 26px;">cloud_upload</span>
            </div>
            <h2 class="stitch-upload-title font-headline-sm">Upload Dataset</h2>
            <p class="stitch-upload-desc font-body-md">Drag and drop your CSV or Excel file here</p>
        </div>
        """),
        unsafe_allow_html=True
    )

    # Streamlit native file uploader placed cleanly below or inside controls
    u_col1, u_col2 = st.columns([7, 5], gap="small")
    
    with u_col1:
        uploaded_file = st.file_uploader(
            "Browse Files (CSV • XLSX • XLS)",
            type=["csv", "xlsx", "xls"],
            key="stitch_dataset_file_uploader",
            help="Upload CSV or Excel files up to 200 MB"
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
                    selected_sheet = st.selectbox("Select Worksheet", options=sheet_names, key="stitch_excel_sheet_sel")
                    if st.button("Load Selected Sheet", key="stitch_load_sheet_btn", type="primary", use_container_width=True):
                        with st.spinner("Parsing Excel worksheet..."):
                            parsed_df, err, ftype = load_dataset_file(uploaded_file, filename, sheet_name=selected_sheet)
                            if err:
                                st.error(err)
                            elif parsed_df is not None:
                                set_active_dataset(parsed_df, f"{filename} ({selected_sheet})", file_type="Excel")
                                st.rerun()
                else:
                    sheet_to_load = sheet_names[0] if sheet_names else None
                    if st.button("Load Excel Dataset", key="stitch_load_single_excel_btn", type="primary", use_container_width=True):
                        with st.spinner("Parsing Excel file..."):
                            parsed_df, err, ftype = load_dataset_file(uploaded_file, filename, sheet_name=sheet_to_load)
                            if err:
                                st.error(err)
                            elif parsed_df is not None:
                                set_active_dataset(parsed_df, filename, file_type="Excel")
                                st.rerun()
            else:
                # CSV
                if st.button("Load Uploaded CSV", key="stitch_load_csv_btn", type="primary", use_container_width=True):
                    with st.spinner("Decoding CSV dataset..."):
                        parsed_df, err, ftype = load_dataset_file(uploaded_file, filename)
                        if err:
                            st.error(err)
                        elif parsed_df is not None:
                            set_active_dataset(parsed_df, filename, file_type="CSV")
                            st.rerun()

    with u_col2:
        # Sample dataset quick loader
        sample_catalog = get_available_sample_datasets()
        if sample_catalog:
            sample_keys = list(sample_catalog.keys())
            sample_names = [sample_catalog[k]["name"] for k in sample_keys]
            
            selected_sample_name = st.selectbox(
                "Or load sample data",
                options=sample_names,
                key="stitch_sample_dataset_sel"
            )
            selected_sample_key = next((k for k in sample_keys if sample_catalog[k]["name"] == selected_sample_name), sample_keys[0])
            
            if st.button("Load Sample Dataset", key="stitch_load_sample_btn", use_container_width=True):
                with st.spinner(f"Loading {selected_sample_name}..."):
                    s_df, s_err, s_type = load_sample_dataset_by_key(selected_sample_key)
                    if s_err:
                        st.error(s_err)
                    elif s_df is not None:
                        set_active_dataset(s_df, sample_catalog[selected_sample_key]["filename"], file_type=s_type)
                        st.rerun()

    st.markdown("<p class='font-mono-data' style='text-align: center; color: var(--text-muted); margin-top: 4px; margin-bottom: 24px;'>CSV • XLSX • XLS supported</p>", unsafe_allow_html=True)


def _render_active_dataset_preview_card(
    df: pd.DataFrame,
    metadata: Dict[str, Any],
    dataset_name: str,
    file_type: str
) -> None:
    """Render the active dataset overview card with live search and high-density tabular preview."""
    # Session Guard: Log dataset upload metadata once per dataset signature
    current_sig = f"{dataset_name}_{metadata.get('total_rows', 0)}_{metadata.get('total_columns', 0)}_{metadata.get('memory_bytes', 0)}"
    if st.session_state.get("logged_dataset_signature") != current_sig:
        user_info = get_current_user()
        log_dataset_upload(user_info, metadata, file_type=file_type)
        st.session_state["logged_dataset_signature"] = current_sig

    rows_cnt = metadata.get("total_rows", len(df))
    cols_cnt = metadata.get("total_columns", len(df.columns))
    mem_str = metadata.get("memory_formatted", "0 KB")
    meta_str = f"{rows_cnt:,} rows &nbsp;|&nbsp; {cols_cnt} columns &nbsp;|&nbsp; {mem_str} &nbsp;|&nbsp; Active Dataset"
    footer_total_str = f"{rows_cnt:,}"

    # Card Top Header Row
    top_c1, top_c2 = st.columns([10, 2])
    with top_c1:
        st.markdown(
            textwrap.dedent(f"""
            <div class="stitch-dataset-title-row">
                <span class="mat-icon" style="color: var(--accent); font-size: 22px;">table_chart</span>
                <h2 class="stitch-dataset-name font-headline-sm">{html.escape(dataset_name)}</h2>
                <span class="stitch-badge-active font-mono-data">
                    <span style="font-size: 8px;">●</span> Active Dataset
                </span>
            </div>
            <div class="stitch-dataset-meta font-mono-data">
                {meta_str}
            </div>
            """),
            unsafe_allow_html=True
        )

    with top_c2:
        with st.popover("⋮", help="Dataset options"):
            st.markdown("<span class='font-label-md'>Dataset Options</span>", unsafe_allow_html=True)
            if st.button("Clear Dataset", key="stitch_clear_active_ds_btn", use_container_width=True):
                clear_dataset_state()
                st.rerun()
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Export CSV",
                data=csv_data,
                file_name=dataset_name if dataset_name.endswith(".csv") else f"{dataset_name}.csv",
                mime="text/csv",
                key="stitch_download_csv_btn",
                use_container_width=True
            )

    st.markdown("<hr style='border:none; border-top: 1px solid var(--border); margin: 12px 0 16px 0;'>", unsafe_allow_html=True)

    # Sub-header: DATASET PREVIEW & Search rows input
    prev_hdr_col, search_col = st.columns([6, 6])
    with prev_hdr_col:
        st.markdown(
            "<h3 class='font-label-md' style='color: var(--text-primary); margin: 8px 0 0 0;'>DATASET PREVIEW</h3>",
            unsafe_allow_html=True
        )
    with search_col:
        search_query = st.text_input(
            "Search rows...",
            placeholder="Search rows...",
            key="stitch_row_search_input",
            label_visibility="collapsed"
        )

    # Filter rows based on search query
    filtered_df = df
    if search_query:
        query_str = search_query.strip().lower()
        mask = filtered_df.astype(str).apply(lambda row: query_str in " ".join(row).lower(), axis=1)
        filtered_df = filtered_df[mask]

    # Display Top Rows in High-Density Table
    preview_limit = 5
    preview_slice = filtered_df.head(preview_limit)

    # Construct HTML Table matching Stitch CSS
    headers = list(preview_slice.columns)
    table_rows_html = []

    for _, row in preview_slice.iterrows():
        cells_html = []
        for col_name in headers:
            val = row[col_name]
            if pd.isna(val) or val is None or str(val).strip() == "":
                formatted_val = '<span class="null-val">null</span>'
            else:
                if isinstance(val, float) and val.is_integer():
                    val_str = str(int(val))
                else:
                    val_str = str(val)
                # Check if numerical/currency for right alignment
                is_num = isinstance(val, (int, float, np.number)) or val_str.startswith("$") or val_str.replace(",", "").replace(".", "").isdigit()
                align_style = "text-align: right;" if is_num else "text-align: left;"
                formatted_val = f'<span style="{align_style}">{html.escape(val_str)}</span>'
            cells_html.append(f"<td>{formatted_val}</td>")
        
        table_rows_html.append(f"<tr>{''.join(cells_html)}</tr>")

    headers_th = "".join([f"<th>{html.escape(str(h))}</th>" for h in headers])
    tbody_content = "".join(table_rows_html)

    footer_display_total = f"{len(filtered_df):,}" if search_query else f"{rows_cnt:,}"

    table_markup = (
        f'<div class="stitch-table-container">'
        f'<table class="stitch-table">'
        f'<thead><tr>{headers_th}</tr></thead>'
        f'<tbody>{tbody_content}</tbody>'
        f'</table>'
        f'</div>'
        f'<div class="stitch-table-footer font-mono-data">'
        f'Showing 1-{len(preview_slice)} of {footer_display_total} rows'
        f'</div>'
    )
    st.markdown(table_markup, unsafe_allow_html=True)


# =============================================================================
# RIGHT COLUMN: HEALTH, BENTO KPIS, COLUMN SUMMARY & NEXT STEPS
# =============================================================================

def _render_dataset_health_card(metadata: Dict[str, Any]) -> None:
    """Render the Dataset Health status card with direct navigation link."""
    missing_cells = metadata.get("missing_cells", 0)
    has_issues = missing_cells > 0

    if has_issues:
        status_title = "Needs attention"
        status_desc = f"{missing_cells:,} missing cells detected. Review quality report."
        icon_name = "error_outline"
        icon_color = "#ef4444"
        icon_bg = "rgba(239, 68, 68, 0.10)"
    else:
        status_title = "Ready for analysis"
        status_desc = "Dataset integrity checks passed. Schema matches expected format."
        icon_name = "task_alt"
        icon_color = "#10b981"
        icon_bg = "rgba(16, 185, 129, 0.10)"

    st.markdown(
        textwrap.dedent(f"""
        <div class="stitch-health-card">
            <div class="stitch-health-icon-circle" style="background: {icon_bg}; color: {icon_color};">
                <span class="mat-icon" style="font-size: 22px;">{icon_name}</span>
            </div>
            <div style="flex: 1;">
                <h3 class="stitch-health-title font-headline-sm">{status_title}</h3>
                <p class="stitch-health-desc font-body-md">{status_desc}</p>
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )

    if st.button("VIEW FULL DATA QUALITY →", key="stitch_goto_quality_btn", use_container_width=True):
        st.session_state["current_page"] = "Data Quality"
        st.rerun()


def _render_bento_kpis(metadata: Dict[str, Any]) -> None:
    """Render 2x2 Bento Grid KPIs: Rows, Columns, Numeric, Missing Values."""
    total_rows = metadata.get("total_rows", 0)
    total_cols = metadata.get("total_columns", 0)
    numeric_count = len(metadata.get("columns_by_type", {}).get("Numeric", []))
    missing_cnt = metadata.get("missing_cells", 0)
    missing_pct = metadata.get("missing_percentage", 0.0)
    rows_val = f"{total_rows:,}"
    cols_val = str(total_cols)
    num_val = str(numeric_count)
    miss_val = f"{missing_cnt:,}"
    miss_sub = f"({missing_pct:.1f}%)"
    miss_class = "error" if missing_cnt > 0 else ""

    st.markdown(
        textwrap.dedent(f"""
        <div class="stitch-bento-grid">
            <div class="stitch-bento-box">
                <span class="stitch-bento-label font-label-md">Rows</span>
                <span class="stitch-bento-val font-headline-lg">{rows_val}</span>
            </div>
            <div class="stitch-bento-box">
                <span class="stitch-bento-label font-label-md">Columns</span>
                <span class="stitch-bento-val font-headline-lg">{cols_val}</span>
            </div>
            <div class="stitch-bento-box">
                <span class="stitch-bento-label font-label-md">Numeric</span>
                <span class="stitch-bento-val font-headline-lg">{num_val}</span>
            </div>
            <div class="stitch-bento-box">
                <span class="stitch-bento-label font-label-md">Missing Values</span>
                <div style="display: flex; align-items: baseline; gap: 4px;">
                    <span class="stitch-bento-val {miss_class} font-headline-lg">{miss_val}</span>
                    <span class="stitch-bento-sub font-mono-data">{miss_sub}</span>
                </div>
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )


def _get_column_icon_name(col_name: str, detected_type: str) -> str:
    """Return appropriate Material Symbol icon name for a given column name and type."""
    col_lower = col_name.lower()
    if "id" in col_lower or "key" in col_lower or "code" in col_lower:
        return "key"
    if "age" in col_lower or "count" in col_lower or "qty" in col_lower or "num" in col_lower:
        return "tag"
    if "income" in col_lower or "price" in col_lower or "salary" in col_lower or "sales" in col_lower or "revenue" in col_lower:
        return "payments"
    if "gender" in col_lower or "category" in col_lower or "type" in col_lower:
        return "category"
    if "date" in col_lower or "time" in col_lower or "year" in col_lower:
        return "calendar_today"
    if "loc" in col_lower or "city" in col_lower or "state" in col_lower or "country" in col_lower:
        return "location_on"
    
    # Fallback by detected semantic type
    if detected_type == "Numeric":
        return "tag"
    elif detected_type == "Date/Time":
        return "calendar_today"
    elif detected_type == "Boolean":
        return "check_box"
    return "key"


def _render_column_summary_card(metadata: Dict[str, Any]) -> None:
    """Render the Column Summary card with semantic type pills, icons, and null indicators."""
    details = metadata.get("column_details", [])
    
    # Header with title and view all toggle
    hdr_c1, hdr_c2 = st.columns([7, 5])
    with hdr_c1:
        st.markdown(
            "<h3 class='stitch-sidebar-title font-label-md' style='margin-top: 6px;'>COLUMN SUMMARY</h3>",
            unsafe_allow_html=True
        )
    with hdr_c2:
        show_all = st.checkbox("View All", key="stitch_toggle_all_cols", value=False)

    display_cols = details if show_all else details[:4]
    items_html = []
    for col in display_cols:
        col_name = col["column_name"]
        detected_type = col["detected_type"]
        missing_count = col["missing_count"]
        icon_name = _get_column_icon_name(col_name, detected_type)
        if detected_type == "Numeric":
            pill_type = "INTEGER" if "int" in col["pandas_dtype"].lower() else "FLOAT"
            pill_class = "stitch-pill-numeric"
        elif detected_type == "Date/Time":
            pill_type = "DATETIME"
            pill_class = "stitch-pill-datetime"
        elif detected_type == "Boolean":
            pill_type = "BOOLEAN"
            pill_class = "stitch-pill-boolean"
        else:
            pill_type = "STRING"
            pill_class = "stitch-pill-string"

        nulls_class = "has-nulls" if missing_count > 0 else ""

        item_row = (
            f'<div class="stitch-col-item">'
            f'<div class="stitch-col-left">'
            f'<span class="mat-icon stitch-step-icon" style="font-size: 16px;">{icon_name}</span>'
            f'<span class="stitch-col-name font-mono-data" title="{html.escape(col_name)}">{html.escape(col_name)}</span>'
            f'</div>'
            f'<span class="stitch-pill {pill_class} font-mono-data">{pill_type}</span>'
            f'<span class="stitch-col-nulls {nulls_class} font-mono-data">{missing_count}</span>'
            f'</div>'
        )
        items_html.append(item_row)

    legend_html = (
        '<div style="display: flex; justify-content: space-between; margin-top: 10px; padding-top: 8px; border-top: 1px solid var(--border);" class="font-mono-data">'
        '<span style="color: var(--text-muted); font-size: 11px;">Name</span>'
        '<div style="display: flex; gap: 28px; color: var(--text-muted); font-size: 11px;">'
        '<span>Type</span>'
        '<span style="width: 24px; text-align: right;">Nulls</span>'
        '</div>'
        '</div>'
    )

    card_content = (
        f'<div class="stitch-sidebar-card">'
        f'{"".join(items_html)}'
        f'{legend_html}'
        f'</div>'
    )
    st.markdown(card_content, unsafe_allow_html=True)


def _render_next_steps_card() -> None:
    """Render the Next Steps workflow guidance card with 1-click navigation."""
    st.markdown(
        textwrap.dedent("""
        <div class="stitch-sidebar-card">
            <h3 class="stitch-sidebar-title font-label-md" style="border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 10px;">
                WORKFLOW NEXT STEP
            </h3>
            <p style="font-size: 12.5px; color: var(--text-secondary); line-height: 1.45; margin-bottom: 12px;">
                Dataset uploaded successfully.<br>
                <strong style="color: var(--text-primary);">Recommended next step:</strong><br>
                Check your dataset quality for missing values, duplicates, and potential issues.
            </p>
        </div>
        """),
        unsafe_allow_html=True
    )

    if st.button("CONTINUE TO DATA QUALITY →", key="stitch_step_quality_primary_btn", type="primary", use_container_width=True):
        st.session_state["current_page"] = "Data Quality"
        st.rerun()

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    render_ai_context_trigger("Ask AI about this data", intent="dataset_profile", key="ds_ai_ask_btn")



def _render_empty_sidebar_guide() -> None:
    """Render helpful starting guide on right column when no dataset is loaded."""
    st.markdown(
        textwrap.dedent("""
        <div class="stitch-sidebar-card">
            <h3 class="stitch-sidebar-title font-label-md" style="margin-bottom: 8px;">GETTING STARTED</h3>
            <p class="font-body-md" style="color: var(--text-secondary); margin-bottom: 12px;">
                Upload a CSV or Excel file on the left or select a sample dataset to unlock Data Studio's analytics suite.
            </p>
            <ul style="padding-left: 18px; color: var(--text-secondary); font-size: 13px; line-height: 1.6;">
                <li>Automatic schema and type detection</li>
                <li>Missing value & duplicate audits</li>
                <li>Exploratory data analysis & charting</li>
                <li>AI-powered natural language insights</li>
            </ul>
        </div>
        """),
        unsafe_allow_html=True
    )


# =============================================================================
# DEEP DIVE TECHNICAL TABS
# =============================================================================

def _render_full_column_schema(metadata: Dict[str, Any]) -> None:
    """Render comprehensive tabular breakdown of all columns, types, and stats."""
    details = metadata.get("column_details", [])
    if not details:
        st.info("No column schema details available.")
        return

    table_data = []
    for c in details:
        table_data.append({
            "Column": c["column_name"],
            "Semantic Type": c["detected_type"],
            "Dtype": c["pandas_dtype"],
            "Non-Null Count": f"{c['non_null_count']:,}",
            "Missing Count": f"{c['missing_count']:,}",
            "Missing %": f"{c['missing_percentage']:.2f}%",
            "Unique Count": f"{c['unique_count']:,}",
            "Sample Preview": c["sample_preview"]
        })

    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)


def _render_semantic_datatypes_tab(df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Render classification breakdown across all columns."""
    by_type = metadata.get("columns_by_type", {})
    for type_name in ["Numeric", "Categorical", "Date/Time", "Text", "Boolean"]:
        cols = by_type.get(type_name, [])
        with st.expander(f"{type_name} Columns ({len(cols)})", expanded=len(cols) > 0):
            if cols:
                items = []
                for c in cols:
                    sample_vals = df[c].dropna().head(3).tolist()
                    sample_str = ", ".join([str(v) for v in sample_vals]) if sample_vals else "—"
                    items.append({
                        "Column": c,
                        "Pandas Dtype": str(df[c].dtype),
                        "Unique Values": f"{df[c].nunique():,}",
                        "Sample Values": sample_str
                    })
                st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)
            else:
                st.caption(f"No {type_name.lower()} columns detected.")


def _render_missing_and_duplicates_tab(df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Render missing data summary and duplicate row analysis."""
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown("#### Missing Values Breakdown")
        missing_cnt = metadata.get("missing_cells", 0)
        missing_pct = metadata.get("missing_percentage", 0.0)
        if missing_cnt == 0:
            st.success("Zero missing values detected across all columns.")
        else:
            st.warning(f"{missing_cnt:,} missing cells ({missing_pct:.2f}% of dataset).")
            missing_cols = [c for c in metadata.get("column_details", []) if c["missing_count"] > 0]
            if missing_cols:
                st.dataframe(pd.DataFrame([
                    {"Column": c["column_name"], "Missing": c["missing_count"], "Missing %": f"{c['missing_percentage']:.2f}%"}
                    for c in missing_cols
                ]), use_container_width=True, hide_index=True)

    with c2:
        st.markdown("#### Duplicate Rows Check")
        dup_cnt = metadata.get("duplicate_rows", 0)
        dup_pct = metadata.get("duplicate_percentage", 0.0)
        if dup_cnt == 0:
            st.success("No duplicate rows found. Every record is unique.")
        else:
            st.warning(f"{dup_cnt:,} duplicate rows detected ({dup_pct:.2f}%).")
            if df is not None:
                dup_mask = df.duplicated(keep=False)
                dup_df = df[dup_mask]
                if not dup_df.empty:
                    st.markdown(f"**Duplicate Records Preview ({len(dup_df):,} occurrences):**")
                    st.dataframe(dup_df, use_container_width=True, hide_index=False)
                    if st.button("Deduplicate in Data Preparation →", key="prof_dup_prep_action_btn", type="primary", use_container_width=True):
                        st.session_state["prep_suggested_action"] = "duplicates"
                        st.session_state["current_page"] = "Data Preparation"
                        st.rerun()

"""
DATA STUDIO v2 — Advanced EDA & Insights Workspace (Module 6)
=============================================================================
Professional analytics workspace delivering exploratory data analysis:
- Dataset Overview & KPIs
- Summary Statistics (Mean, Median, Std Dev, Min, Quantiles, Max, Skewness, Kurtosis)
- Correlation Heatmaps & Matrix Rankings (Pearson & Spearman)
- Distribution Profiling & Statistical Interpretations
- IQR-based Outlier Diagnostics & Inspector
- Universal Column Deep Dives across all semantic types
- Deterministic Rule-Based Automated Insights
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
    render_ai_context_trigger,
    render_next_workflow_steps,
    get_icon_svg,
    get_type_badge_html
)


from modules.eda_engine import (
    compute_summary_statistics,
    compute_correlation_matrix,
    extract_strongest_correlations,
    compute_iqr_outliers,
    analyze_column_deep_dive,
    generate_eda_insights,
    generate_correlation_heatmap,
    generate_distribution_histogram,
    generate_distribution_boxplot,
    generate_outlier_inspector_chart,
    generate_categorical_barchart,
    generate_datetime_timeline_chart,
    interpret_skewness,
    interpret_kurtosis
)


from modules.data_loader import (
    get_available_sample_datasets,
    load_sample_dataset_by_key,
    set_active_dataset
)


def render_eda_page() -> None:
    """Main entry point for Advanced Exploratory Data Analysis & Insights (Module 6)."""
    # 1. Empty State Check
    if not is_dataset_loaded():
        render_page_header(
            title="EDA & Insights",
            subtitle="Descriptive summaries, distributions, skewness, kurtosis, correlation matrices, and outlier detection.",
            icon="search"
        )
        render_empty_state(
            title="No dataset loaded for analysis",
            description="Upload a CSV or Excel file to explore summary statistics, distributions, correlations, outliers, and automated insights.",
            icon="search"
        )
        
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        render_section_header(
            title="Quick Start with Sample Data",
            subtitle="Select a pre-loaded business dataset to immediately explore the EDA workspace."
        )
        
        sample_catalog = get_available_sample_datasets()
        cols = st.columns(len(sample_catalog) if sample_catalog else 1)
        for idx, (key, info) in enumerate(sample_catalog.items()):
            with cols[idx]:
                st.markdown(f"**{info['name']}**")
                st.caption(info["description"])
                if st.button(f"Load {info['name']}", key=f"eda_sample_load_{key}", type="primary", use_container_width=True):
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
            if st.button("Upload Custom Dataset", key="eda_goto_dataset_btn", use_container_width=True):
                st.session_state["current_page"] = "Dataset"
                st.rerun()
        return

    # 2. Extract Active Dataset & Metadata from Session State
    df: pd.DataFrame = st.session_state.get("dataset")
    metadata: Dict[str, Any] = st.session_state.get("dataset_metadata", {})
    dataset_name = st.session_state.get("dataset_name", "dataset.csv")
    file_type = st.session_state.get("dataset_file_type", "CSV")
    current_theme = st.session_state.get("theme", "Light")

    if df is None or df.empty:
        render_page_header(
            title="EDA & Insights",
            subtitle="Descriptive summaries, distributions, skewness, kurtosis, correlation matrices, and outlier detection.",
            icon="search"
        )
        render_notification(
            title="Dataset State Error",
            message="Active dataset could not be accessed. Please upload or reload your data.",
            variant="error"
        )
        if st.button("Return to Dataset", key="err_return_eda_btn"):
            st.session_state["current_page"] = "Dataset"
            st.rerun()
        return

    # 3. Standardized Page Header
    render_page_header(
        title="Analyze",
        subtitle="Descriptive statistics, skewness, kurtosis, correlation matrices, outlier detection, and column deep dives.",
        icon="chart-no-axes-combined"
    )
    mark_workflow_step("analyze", True)

    # 4. Dataset Context Banner
    _render_context_bar(dataset_name, file_type, metadata)


    # 5. Section 1: Dataset Overview KPI Cards
    _render_dataset_overview_kpis(df, metadata)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 6. Internal Module Tabs
    tab_summary, tab_corr, tab_dist, tab_outliers, tab_deepdive, tab_insights = st.tabs([
        "SUMMARY STATISTICS",
        "CORRELATION ANALYSIS",
        "DISTRIBUTION ANALYSIS",
        "OUTLIER DETECTION",
        "COLUMN DEEP DIVE",
        "AUTOMATED INSIGHTS"
    ])

    with tab_summary:
        _render_tab_summary_statistics(df, metadata)

    with tab_corr:
        _render_tab_correlation(df, metadata, current_theme)

    with tab_dist:
        _render_tab_distribution(df, metadata, current_theme)

    with tab_outliers:
        _render_tab_outliers(df, metadata, current_theme)

    with tab_deepdive:
        _render_tab_deep_dive(df, metadata, current_theme)

    with tab_insights:
        _render_tab_automated_insights(df, metadata)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # 7. Next Actions Navigation
    _render_next_actions()


# =============================================================================
# CONTEXT BANNER & DATASET OVERVIEW KPIS
# =============================================================================

def _render_context_bar(name: str, file_type: str, metadata: Dict[str, Any]) -> None:
    """Render compact context bar with quick action buttons."""
    col_info, col_actions = st.columns([7, 5])
    
    total_rows = metadata.get("total_rows", 0)
    total_cols = metadata.get("total_columns", 0)
    memory_formatted = metadata.get("memory_formatted", "")

    with col_info:
        banner_html = (
            f'<div class="ds-active-banner" style="margin-bottom: 12px; padding: 10px 16px;">'
            f'<div class="ds-active-banner-left">'
            f'<div class="ds-brand-badge" style="background: var(--accent);">{file_type[0] if file_type else "D"}</div>'
            f'<div>'
            f'<div class="ds-active-banner-name" style="font-size: 15px;">{name}</div>'
            f'<div class="ds-active-banner-meta" style="font-size: 12px;">'
            f'{total_rows:,} rows · {total_cols} columns · {file_type} · {memory_formatted}'
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
            if st.button("Refresh EDA", key="eda_refresh_btn", use_container_width=True):
                st.toast("Exploratory Data Analysis metrics updated.")
                st.rerun()
        with ac2:
            if st.button("View Dataset", key="eda_view_dataset_btn", use_container_width=True):
                st.session_state["current_page"] = "Dataset"
                st.rerun()


def _render_dataset_overview_kpis(df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Render the 7 primary dataset overview metric cards required by Module 6."""
    total_rows = len(df)
    total_cols = len(df.columns)
    
    # Column counts by type
    cols_by_type = metadata.get("columns_by_type", {})
    numeric_count = len(cols_by_type.get("Numeric", [])) if cols_by_type else sum(1 for c in df.columns if pd.api.types.is_numeric_dtype(df[c]))
    categorical_count = len(cols_by_type.get("Categorical", [])) if cols_by_type else sum(1 for c in df.columns if not pd.api.types.is_numeric_dtype(df[c]))
    
    # Missing & duplicate stats
    total_cells = total_rows * total_cols
    missing_cells = int(df.isna().sum().sum())
    missing_pct = (missing_cells / total_cells * 100) if total_cells > 0 else 0.0
    duplicate_rows = int(df.duplicated().sum())
    duplicate_pct = (duplicate_rows / total_rows * 100) if total_rows > 0 else 0.0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    with c1:
        render_metric_card(
            label="Total Records",
            value=f"{total_rows:,}",
            description="Active data rows",
            status="Rows"
        )
    with c2:
        render_metric_card(
            label="Total Features",
            value=f"{total_cols:,}",
            description="Dataset columns",
            status="Columns"
        )
    with c3:
        render_metric_card(
            label="Numeric Columns",
            value=f"{numeric_count}",
            description=f"{numeric_count/total_cols*100:.0f}% of features" if total_cols > 0 else "0%",
            status="Numeric"
        )
    with c4:
        render_metric_card(
            label="Categorical Columns",
            value=f"{categorical_count}",
            description=f"{categorical_count/total_cols*100:.0f}% of features" if total_cols > 0 else "0%",
            status="Categorical"
        )
    with c5:
        render_metric_card(
            label="Missing Values",
            value=f"{missing_pct:.1f}%",
            change="Clean" if missing_cells == 0 else f"{missing_cells:,} cells",
            change_type="positive" if missing_cells == 0 else ("negative" if missing_pct > 10 else "neutral"),
            description="Completeness",
            status="Health"
        )
    with c6:
        render_metric_card(
            label="Duplicate Rows",
            value=f"{duplicate_rows:,}",
            change=f"{duplicate_pct:.1f}% rate",
            change_type="positive" if duplicate_rows == 0 else "negative",
            description="Zero duplicates" if duplicate_rows == 0 else "Redundant",
            status="Uniqueness"
        )


def _get_cached_summary_stats(df: pd.DataFrame, numeric_cols: List[str]) -> pd.DataFrame:
    """Retrieve cached summary statistics or compute deterministically."""
    sig = f"{id(df)}_{len(df)}_{len(df.columns)}_stats"
    if st.session_state.get("_eda_stats_sig") == sig and st.session_state.get("_eda_stats_df") is not None:
        return st.session_state["_eda_stats_df"]
    res = compute_summary_statistics(df, numeric_cols)
    st.session_state["_eda_stats_sig"] = sig
    st.session_state["_eda_stats_df"] = res
    return res


def _get_cached_correlation_matrix(df: pd.DataFrame, numeric_cols: List[str], method: str = "pearson") -> pd.DataFrame:
    """Retrieve cached correlation matrix or compute deterministically."""
    sig = f"{id(df)}_{len(df)}_{len(df.columns)}_corr_{method}"
    if st.session_state.get("_eda_corr_sig") == sig and st.session_state.get("_eda_corr_df") is not None:
        return st.session_state["_eda_corr_df"]
    res = compute_correlation_matrix(df, numeric_cols, method=method)
    st.session_state["_eda_corr_sig"] = sig
    st.session_state["_eda_corr_df"] = res
    return res


# =============================================================================
# TAB 1: SUMMARY STATISTICS
# =============================================================================

def _render_tab_summary_statistics(df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Render comprehensive summary statistics table for numeric features with highlights."""
    render_section_header(
        title="Numeric Summary Statistics",
        subtitle="Central tendency, dispersion, quantiles, skewness, and Fisher excess kurtosis."
    )

    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    if not numeric_cols:
        render_notification(
            title="No Numeric Features Found",
            message="This dataset does not contain numeric columns. Summary statistics require quantitative numerical data.",
            variant="warning"
        )
        return

    # Compute stats (Session-Cached)
    summary_df = _get_cached_summary_stats(df, numeric_cols)

    # Highlight metrics row
    h1, h2, h3, h4 = st.columns(4)
    with h1:
        render_metric_card(
            label="Numeric Features",
            value=f"{len(numeric_cols)}",
            description="Quantitatively analyzed",
            status="Metrics"
        )
    with h2:
        # Highest mean column
        if not summary_df.empty:
            valid_means = summary_df.dropna(subset=["Mean"])
            if not valid_means.empty:
                max_mean_row = valid_means.sort_values(by="Mean", ascending=False).iloc[0]
                render_metric_card(
                    label="Highest Mean",
                    value=f"{max_mean_row['Mean']:,.1f}",
                    description=f"Feature: {max_mean_row['Column']}",
                    status="Average"
                )
    with h3:
        # Highest variance / std dev column
        if not summary_df.empty:
            valid_stds = summary_df.dropna(subset=["Std Dev"])
            if not valid_stds.empty:
                max_std_row = valid_stds.sort_values(by="Std Dev", ascending=False).iloc[0]
                render_metric_card(
                    label="Highest Std Dev",
                    value=f"{max_std_row['Std Dev']:,.1f}",
                    description=f"Feature: {max_std_row['Column']}",
                    status="Dispersion"
                )
    with h4:
        # Most skewed column
        if not summary_df.empty:
            valid_skews = summary_df.dropna(subset=["Skewness"])
            if not valid_skews.empty:
                max_skew_row = valid_skews.iloc[valid_skews["Skewness"].abs().argmax()]
                render_metric_card(
                    label="Max Abs Skewness",
                    value=f"{max_skew_row['Skewness']:.2f}",
                    description=f"Feature: {max_skew_row['Column']}",
                    status="Asymmetry"
                )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Search / Filter Bar
    filter_col, sort_col, export_col = st.columns([5, 4, 3])
    with filter_col:
        search_query = st.text_input(
            "Filter numeric columns",
            placeholder="Search column names...",
            key="summary_stats_search",
            label_visibility="collapsed"
        )
    with sort_col:
        sort_by = st.selectbox(
            "Sort By",
            options=["Column", "Mean", "Std Dev", "Skewness", "Kurtosis", "Min", "Max", "Missing %"],
            key="summary_stats_sort",
            label_visibility="collapsed"
        )
    with export_col:
        csv_data = summary_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="summary_statistics.csv",
            mime="text/csv",
            key="summary_stats_download_btn",
            use_container_width=True
        )

    # Apply search and sort
    filtered_df = summary_df.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df["Column"].str.contains(search_query, case=False, na=False)]
    
    if sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=(sort_by == "Column")).reset_index(drop=True)

    # Format numeric values cleanly
    column_config = {
        "Column": st.column_config.TextColumn("Column Name", width="medium"),
        "Count": st.column_config.NumberColumn("Count", format="%d"),
        "Mean": st.column_config.NumberColumn("Mean", format="%.2f"),
        "Median": st.column_config.NumberColumn("Median", format="%.2f"),
        "Std Dev": st.column_config.NumberColumn("Std Dev", format="%.2f"),
        "Min": st.column_config.NumberColumn("Min", format="%.2f"),
        "25% (Q1)": st.column_config.NumberColumn("25% (Q1)", format="%.2f"),
        "50% (Q2)": st.column_config.NumberColumn("50% (Q2)", format="%.2f"),
        "75% (Q3)": st.column_config.NumberColumn("75% (Q3)", format="%.2f"),
        "Max": st.column_config.NumberColumn("Max", format="%.2f"),
        "Skewness": st.column_config.NumberColumn("Skewness", format="%.2f"),
        "Kurtosis": st.column_config.NumberColumn("Kurtosis", format="%.2f"),
        "Missing %": st.column_config.NumberColumn("Missing %", format="%.1f%%")
    }

    st.dataframe(
        filtered_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True
    )


# =============================================================================
# TAB 2: CORRELATION ANALYSIS
# =============================================================================

def _render_tab_correlation(df: pd.DataFrame, metadata: Dict[str, Any], theme: str) -> None:
    """Render interactive correlation heatmap, correlation matrix table, and strongest correlation rankings."""
    render_section_header(
        title="Feature Correlation Analysis",
        subtitle="Evaluate pairwise linear (Pearson) and monotonic rank (Spearman) relationships between numeric features."
    )

    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    if len(numeric_cols) < 2:
        render_notification(
            title="Insufficient Numeric Columns",
            message=f"Correlation analysis requires at least 2 numeric features. Found {len(numeric_cols)} numeric column(s).",
            variant="warning"
        )
        return

    # Method Selector & Controls
    c_method, c_thresh, c_view = st.columns([4, 4, 4])
    with c_method:
        corr_method = st.selectbox(
            "Correlation Method",
            options=["Pearson", "Spearman"],
            index=0,
            key="corr_method_selector",
            help="Pearson measures linear relationships. Spearman measures monotonic rank relationships."
        )
    with c_thresh:
        min_threshold = st.slider(
            "Highlight Correlation Threshold (|r| ≥)",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05,
            key="corr_thresh_slider"
        )
    with c_view:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        show_matrix_table = st.checkbox("Show Correlation Matrix Table", value=False, key="corr_show_table_toggle")

    # Compute correlation matrix (Session-Cached)
    corr_matrix = _get_cached_correlation_matrix(df, numeric_cols, method=corr_method.lower())

    if corr_matrix.empty or len(corr_matrix.columns) < 2:
        render_notification(
            title="Correlation Matrix Could Not Be Calculated",
            message="Numeric columns in this dataset contain zero variance or insufficient non-null observations.",
            variant="warning"
        )
        return

    # Plotly Interactive Heatmap
    heatmap_fig = generate_correlation_heatmap(corr_matrix, method=corr_method, theme=theme, height=450)
    if heatmap_fig:
        st.plotly_chart(heatmap_fig, use_container_width=True, config={"displayModeBar": True})

    # Strongest Correlations Rankings
    pos_pairs, neg_pairs = extract_strongest_correlations(corr_matrix, top_n=8)

    col_pos, col_neg = st.columns(2, gap="large")

    with col_pos:
        render_section_header(
            title="Top Positive Correlations (+r)",
            subtitle="Features that tend to increase together."
        )
        filtered_pos = [p for p in pos_pairs if p["Correlation (r)"] >= min_threshold]
        if not filtered_pos:
            render_notification(
                title="No Strong Positive Correlations",
                message=f"No feature pairs with positive correlation r ≥ {min_threshold:.2f}.",
                variant="info"
            )
        else:
            pos_df = pd.DataFrame([
                {
                    "Feature A": p["Variable 1"],
                    "Feature B": p["Variable 2"],
                    "Correlation (r)": f"+{p['Correlation (r)']:.3f}",
                    "Strength": p["Strength"]
                }
                for p in filtered_pos
            ])
            st.dataframe(pos_df, use_container_width=True, hide_index=True)

    with col_neg:
        render_section_header(
            title="Top Negative Correlations (-r)",
            subtitle="Features that move in opposite directions."
        )
        filtered_neg = [p for p in neg_pairs if abs(p["Correlation (r)"]) >= min_threshold]
        if not filtered_neg:
            render_notification(
                title="No Strong Negative Correlations",
                message=f"No feature pairs with negative correlation |r| ≥ {min_threshold:.2f}.",
                variant="info"
            )
        else:
            neg_df = pd.DataFrame([
                {
                    "Feature A": p["Variable 1"],
                    "Feature B": p["Variable 2"],
                    "Correlation (r)": f"{p['Correlation (r)']:.3f}",
                    "Strength": p["Strength"]
                }
                for p in filtered_neg
            ])
            st.dataframe(neg_df, use_container_width=True, hide_index=True)

    # Optional Matrix Table
    if show_matrix_table:
        st.markdown("##### Full Correlation Matrix")
        st.dataframe(corr_matrix.style.format("{:.3f}"), use_container_width=True)


# =============================================================================
# TAB 3: DISTRIBUTION ANALYSIS
# =============================================================================

def _render_tab_distribution(df: pd.DataFrame, metadata: Dict[str, Any], theme: str) -> None:
    """Render numeric column distribution analysis with automatic skewness/kurtosis interpretations."""
    render_section_header(
        title="Distribution & Symmetry Profiling",
        subtitle="Examine data spread, central tendencies, shape symmetry, and tail characteristics."
    )

    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    if not numeric_cols:
        render_notification(
            title="No Numeric Columns Available",
            message="Distribution analysis requires numeric features.",
            variant="warning"
        )
        return

    # Column Selector & Chart Controls
    col_sel, col_bins, col_lines = st.columns([5, 4, 3])
    with col_sel:
        selected_col = st.selectbox(
            "Select Numeric Column",
            options=numeric_cols,
            key="dist_column_selector"
        )
    with col_bins:
        bin_count = st.slider("Histogram Bins", min_value=5, max_value=60, value=25, step=5, key="dist_bin_slider")
    with col_lines:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        show_ref_lines = st.checkbox("Show Mean / Median Lines", value=True, key="dist_ref_lines_toggle")

    series = df[selected_col].dropna()
    if series.empty:
        render_notification(
            title="Empty Feature",
            message=f"Feature '{selected_col}' contains only null values.",
            variant="warning"
        )
        return

    # Calculate key metrics
    mean_val = float(series.mean())
    median_val = float(series.median())
    std_val = float(series.std()) if len(series) > 1 else 0.0
    skew_val = float(series.skew()) if len(series) >= 3 and std_val > 0 else 0.0
    kurt_val = float(series.kurtosis()) if len(series) >= 4 and std_val > 0 else 0.0
    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr_val = q3 - q1

    # Distribution Summary KPI Row
    d1, d2, d3, d4, d5, d6 = st.columns(6)
    with d1:
        render_metric_card(label="Mean", value=f"{mean_val:,.2f}", status="Average")
    with d2:
        render_metric_card(label="Median", value=f"{median_val:,.2f}", status="50th %ile")
    with d3:
        render_metric_card(label="Std Dev", value=f"{std_val:,.2f}", status="Spread")
    with d4:
        render_metric_card(label="IQR", value=f"{iqr_val:,.2f}", status="Middle 50%")
    with d5:
        render_metric_card(
            label="Skewness",
            value=f"{skew_val:+.2f}",
            description="Symmetric" if abs(skew_val) <= 0.5 else ("Right-skewed" if skew_val > 0 else "Left-skewed"),
            status="Shape"
        )
    with d6:
        render_metric_card(
            label="Kurtosis",
            value=f"{kurt_val:+.2f}",
            description="Excess kurtosis",
            status="Tails"
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Automatic Statistical Interpretations
    skew_info = interpret_skewness(skew_val)
    kurt_info = interpret_kurtosis(kurt_val)

    int_col1, int_col2 = st.columns(2)
    with int_col1:
        render_notification(
            title=f"Symmetry: {skew_info['label']}",
            message=f"Skewness = {skew_val:.2f}. {skew_info['description']}",
            variant="info" if skew_info["category"] == "symmetric" else "warning"
        )
    with int_col2:
        render_notification(
            title=f"Tail Weight: {kurt_info['label']}",
            message=f"Excess Kurtosis = {kurt_val:.2f}. {kurt_info['description']}",
            variant="info" if kurt_info["category"] == "mesokurtic" else "warning"
        )

    # Distribution Visualizations
    chart_col1, chart_col2 = st.columns([6, 4], gap="large")

    with chart_col1:
        hist_fig = generate_distribution_histogram(
            series,
            col_name=selected_col,
            nbins=bin_count,
            show_mean_median=show_ref_lines,
            theme=theme,
            height=360
        )
        st.plotly_chart(hist_fig, use_container_width=True, config={"displayModeBar": False})

    with chart_col2:
        box_fig = generate_distribution_boxplot(
            series,
            col_name=selected_col,
            theme=theme,
            height=360
        )
        st.plotly_chart(box_fig, use_container_width=True, config={"displayModeBar": False})


# =============================================================================
# TAB 4: OUTLIER DETECTION
# =============================================================================

def _render_tab_outliers(df: pd.DataFrame, metadata: Dict[str, Any], theme: str) -> None:
    """Render IQR-based outlier detection, summary table, and single-column inspector."""
    render_section_header(
        title="Outlier Detection (IQR Method)",
        subtitle="Detect extreme values outside the 1.5×IQR boundary: [Q1 - 1.5×IQR, Q3 + 1.5×IQR]. Read-only analysis."
    )

    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    if not numeric_cols:
        render_notification(
            title="No Numeric Features",
            message="Outlier detection requires quantitative numeric features.",
            variant="warning"
        )
        return

    # Compute IQR outliers across all numeric columns
    outlier_results = compute_iqr_outliers(df, numeric_cols)
    summary_df = outlier_results["summary_df"]
    total_outliers = outlier_results["total_outliers"]
    overall_rate = outlier_results["overall_outlier_rate"]
    affected_cols = outlier_results["affected_columns_count"]
    col_outliers_map = outlier_results["column_outliers"]

    # KPI Summary Row
    o1, o2, o3, o4 = st.columns(4)
    with o1:
        render_metric_card(
            label="Total Outliers",
            value=f"{total_outliers:,}",
            description="Across all numeric features",
            status="Count"
        )
    with o2:
        render_metric_card(
            label="Overall Outlier Rate",
            value=f"{overall_rate:.2f}%",
            change="Clean" if total_outliers == 0 else f"{overall_rate:.1f}% rate",
            change_type="positive" if total_outliers == 0 else "neutral",
            description="Evaluated numeric cells",
            status="Rate"
        )
    with o3:
        render_metric_card(
            label="Affected Columns",
            value=f"{affected_cols}",
            description=f"of {len(numeric_cols)} numeric columns",
            status="Columns"
        )
    with o4:
        top_col = summary_df.iloc[0]["Column"] if not summary_df.empty and total_outliers > 0 else "None"
        top_pct = summary_df.iloc[0]["Outlier %"] if not summary_df.empty and total_outliers > 0 else 0.0
        render_metric_card(
            label="Highest Outlier Feature",
            value=top_col,
            description=f"{top_pct:.1f}% outlier rate" if total_outliers > 0 else "Zero outliers",
            status="Burden"
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Outlier Summary Table
    if not summary_df.empty:
        st.markdown("##### Outlier Summary Table")
        
        column_config = {
            "Column": st.column_config.TextColumn("Column Name", width="medium"),
            "Non-Null Count": st.column_config.NumberColumn("Non-Null Count", format="%d"),
            "Q1 (25%)": st.column_config.NumberColumn("Q1", format="%.2f"),
            "Q3 (75%)": st.column_config.NumberColumn("Q3", format="%.2f"),
            "IQR": st.column_config.NumberColumn("IQR", format="%.2f"),
            "Lower Bound": st.column_config.NumberColumn("Lower Bound", format="%.2f"),
            "Upper Bound": st.column_config.NumberColumn("Upper Bound", format="%.2f"),
            "Outlier Count": st.column_config.NumberColumn("Outliers", format="%d"),
            "Outlier %": st.column_config.NumberColumn("Outlier %", format="%.2f%%"),
            "Status": st.column_config.TextColumn("Health Status", width="small")
        }

        st.dataframe(
            summary_df[["Column", "Non-Null Count", "Q1 (25%)", "Q3 (75%)", "IQR", "Lower Bound", "Upper Bound", "Outlier Count", "Outlier %", "Status"]],
            column_config=column_config,
            use_container_width=True,
            hide_index=True
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Interactive Single-Column Outlier Inspector
    render_section_header(
        title="Single-Column Outlier Inspector",
        subtitle="Inspect threshold bounds and outlier points for a selected feature."
    )

    inspector_col = st.selectbox(
        "Select Column to Inspect Outliers",
        options=numeric_cols,
        key="outlier_inspector_selector"
    )

    if inspector_col in col_outliers_map:
        col_meta = col_outliers_map[inspector_col]
        series = df[inspector_col].dropna()

        chart_col, data_col = st.columns([6, 4], gap="large")

        with chart_col:
            outlier_fig = generate_outlier_inspector_chart(
                series,
                col_name=inspector_col,
                lower_bound=col_meta["lower_bound"],
                upper_bound=col_meta["upper_bound"],
                theme=theme,
                height=380
            )
            st.plotly_chart(outlier_fig, use_container_width=True, config={"displayModeBar": False})

        with data_col:
            st.markdown(f"**Inspection Bounds for '{inspector_col}'**")
            b_info = pd.DataFrame([
                {"Metric": "Lower Bound (Q1 - 1.5×IQR)", "Value": f"{col_meta['lower_bound']:,.2f}"},
                {"Metric": "Upper Bound (Q3 + 1.5×IQR)", "Value": f"{col_meta['upper_bound']:,.2f}"},
                {"Metric": "Outlier Count", "Value": f"{col_meta['outlier_count']:,} records"},
                {"Metric": "Outlier Rate", "Value": f"{col_meta['outlier_pct']:.2f}%"}
            ])
            st.dataframe(b_info, use_container_width=True, hide_index=True)

            if col_meta["outlier_count"] > 0:
                st.markdown(f"**Sample Outlier Records ({len(col_meta['outlier_values'])} total)**")
                sample_outlier_df = pd.DataFrame({
                    "Row Index": col_meta["outlier_indices"][:10],
                    "Outlier Value": col_meta["outlier_values"][:10]
                })
                st.dataframe(sample_outlier_df, use_container_width=True, hide_index=True)
            else:
                render_notification(
                    title="No Outliers in this Feature",
                    message=f"All records for '{inspector_col}' fall within standard bounds.",
                    variant="success"
                )


# =============================================================================
# TAB 5: COLUMN DEEP DIVE
# =============================================================================

def _render_tab_deep_dive(df: pd.DataFrame, metadata: Dict[str, Any], theme: str) -> None:
    """Render universal single-column deep dive supporting Numeric, Categorical, Datetime, and Text types."""
    render_section_header(
        title="Column Deep Dive",
        subtitle="Focused analysis panel providing fine-grained statistical inspection for any dataset feature."
    )

    all_cols = list(df.columns)
    if not all_cols:
        return

    # Universal Column Selector
    selected_col = st.selectbox(
        "Select Dataset Feature to Deep Dive",
        options=all_cols,
        key="deep_dive_col_selector"
    )

    # Perform Deep Dive Profile
    profile = analyze_column_deep_dive(df, selected_col)
    if not profile:
        return

    det_type = profile.get("detected_type", "Text")

    # Column Meta Banner
    type_badge_html = get_type_badge_html(det_type)
    meta_banner_html = (
        f'<div class="ds-active-banner" style="margin-bottom: 14px; padding: 12px 18px;">'
        f'<div class="ds-active-banner-left">'
        f'{type_badge_html}'
        f'<div>'
        f'<div class="ds-active-banner-name" style="font-size: 16px;">{selected_col}</div>'
        f'<div class="ds-active-banner-meta" style="font-size: 12px;">'
        f'{profile["total_rows"]:,} total rows · {profile["non_null_count"]:,} non-null · {profile["missing_percentage"]:.1f}% missing'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(meta_banner_html, unsafe_allow_html=True)

    # Common KPIs across all types
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_metric_card(label="Data Type", value=det_type, status="Semantic Type")
    with k2:
        render_metric_card(label="Non-Null Records", value=f"{profile['non_null_count']:,}", status="Count")
    with k3:
        render_metric_card(
            label="Missing Values",
            value=f"{profile['missing_percentage']:.1f}%",
            change=f"{profile['missing_count']:,} missing" if profile['missing_count'] > 0 else "0 missing",
            change_type="positive" if profile['missing_count'] == 0 else "neutral",
            status="Completeness"
        )
    with k4:
        render_metric_card(
            label="Unique Values",
            value=f"{profile['unique_count']:,}",
            description=f"{profile['unique_percentage']:.1f}% unique",
            status="Cardinality"
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 1. NUMERIC DEEP DIVE
    if det_type == "Numeric" and "mean" in profile:
        st.markdown("##### Numeric Descriptive Profile")
        
        n_col1, n_col2 = st.columns(2)
        with n_col1:
            render_notification(
                title=f"Symmetry: {profile['skew_interpretation']['label']}",
                message=f"Skewness = {profile['skewness']:.2f}. {profile['skew_interpretation']['description']}",
                variant="info" if profile["skew_interpretation"]["category"] == "symmetric" else "warning"
            )
        with n_col2:
            render_notification(
                title=f"Tail Weight: {profile['kurt_interpretation']['label']}",
                message=f"Excess Kurtosis = {profile['kurtosis']:.2f}. {profile['kurt_interpretation']['description']}",
                variant="info" if profile["kurt_interpretation"]["category"] == "mesokurtic" else "warning"
            )

        # Quantiles & Distribution Table
        q_col, stats_col = st.columns([5, 5], gap="large")
        with q_col:
            st.markdown("**Quantiles Breakdown**")
            q_df = pd.DataFrame([
                {"Percentile": k, "Value": f"{v:,.2f}"}
                for k, v in profile.get("quantiles", {}).items()
            ])
            st.dataframe(q_df, use_container_width=True, hide_index=True)

        with stats_col:
            st.markdown("**Spread & Boundary Metrics**")
            s_df = pd.DataFrame([
                {"Metric": "Mean", "Value": f"{profile['mean']:,.2f}"},
                {"Metric": "Standard Deviation", "Value": f"{profile['std']:,.2f}"},
                {"Metric": "Variance", "Value": f"{profile['variance']:,.2f}"},
                {"Metric": "Min / Max", "Value": f"{profile['min']:,.2f} / {profile['max']:,.2f}"},
                {"Metric": "IQR [Q1 - Q3]", "Value": f"{profile['iqr']:,.2f} [{profile['q1']:,.2f} – {profile['q3']:,.2f}]"},
                {"Metric": "IQR Outlier Count", "Value": f"{profile['outlier_count']:,} records"}
            ])
            st.dataframe(s_df, use_container_width=True, hide_index=True)

        # Charts
        series = df[selected_col].dropna()
        c_h, c_b = st.columns([6, 4], gap="large")
        with c_h:
            hist_fig = generate_distribution_histogram(series, selected_col, theme=theme, height=320)
            st.plotly_chart(hist_fig, use_container_width=True, config={"displayModeBar": False})
        with c_b:
            box_fig = generate_distribution_boxplot(series, selected_col, theme=theme, height=320)
            st.plotly_chart(box_fig, use_container_width=True, config={"displayModeBar": False})

    # 2. CATEGORICAL / BOOLEAN / TEXT DEEP DIVE
    elif det_type in ["Categorical", "Boolean", "Text"]:
        st.markdown("##### Categorical Frequency & Value Distribution")
        
        freq_table = profile.get("frequency_table", pd.DataFrame())
        
        f_table_col, f_chart_col = st.columns([5, 7], gap="large")
        with f_table_col:
            st.markdown("**Top Category Frequencies**")
            st.dataframe(freq_table, use_container_width=True, hide_index=True)

        with f_chart_col:
            if not freq_table.empty:
                bar_fig = generate_categorical_barchart(freq_table, selected_col, theme=theme, height=360)
                if bar_fig:
                    st.plotly_chart(bar_fig, use_container_width=True, config={"displayModeBar": False})

    # 3. DATE/TIME DEEP DIVE
    elif det_type == "Date/Time":
        st.markdown("##### Temporal Span & Timeline Profiling")

        t1, t2, t3 = st.columns(3)
        with t1:
            render_metric_card(label="Earliest Date (Min)", value=profile.get("min_date", "N/A"), status="Start")
        with t2:
            render_metric_card(label="Latest Date (Max)", value=profile.get("max_date", "N/A"), status="End")
        with t3:
            render_metric_card(label="Date Span", value=profile.get("date_span_formatted", "N/A"), status="Duration")

        dt_series = profile.get("dt_series")
        if dt_series is not None and not dt_series.empty:
            tl_fig = generate_datetime_timeline_chart(dt_series, selected_col, theme=theme, height=360)
            if tl_fig:
                st.plotly_chart(tl_fig, use_container_width=True, config={"displayModeBar": False})


# =============================================================================
# TAB 6: AUTOMATED EDA INSIGHTS
# =============================================================================

def _render_tab_automated_insights(df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Render deterministic, rule-based EDA insights without fake/AI text."""
    render_section_header(
        title="Automated Analytics Observations",
        subtitle="Deterministic insights computed directly from dataset statistics, distributions, and correlations."
    )

    insights = generate_eda_insights(df, metadata)

    if not insights:
        render_notification(
            title="Zero Critical Anomalies Detected",
            message="Your dataset exhibits clean distributions, complete records, and balanced feature distributions.",
            variant="success"
        )
        return

    # Filter by category if multiple
    categories = sorted(list(set(i["category"] for i in insights)))
    
    cat_filter = st.selectbox(
        "Filter Insights by Category",
        options=["All Categories"] + categories,
        key="insights_category_filter"
    )

    filtered_insights = insights if cat_filter == "All Categories" else [i for i in insights if i["category"] == cat_filter]

    for item in filtered_insights:
        render_notification(
            title=f"[{item['category']}] {item['title']}",
            message=item["observation"],
            variant=item.get("variant", "info")
        )


# =============================================================================
# NEXT ACTIONS NAVIGATION
# =============================================================================

def _render_next_actions() -> None:
    """Render contextual AI trigger and standardized bottom workflow navigation."""
    render_ai_context_trigger("Generate AI Insights for this analysis", intent="eda_insights", key="eda_ai_btn")
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    render_next_workflow_steps("Analyze")



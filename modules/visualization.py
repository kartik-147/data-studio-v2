"""
DATA STUDIO v2 — Interactive Visualization Studio (Module 8)
=============================================================================
Professional, self-service chart-building workspace delivering:
- 12 Supported Chart Types across 6 Families (Comparison, Trends, Relationships,
  Distribution, Composition, Advanced)
- Smart Dynamic Configuration Controls (X, Y, Color, Size, Aggregation, Sorting, Bins, Top N)
- Deterministic Smart Chart Recommendations with 1-Click Application
- Large Responsive Theme-Aware Interactive Plotly Preview (Dark / Light)
- Deterministic Calculated Analytical Chart Insights
- Active Session-Level Chart Saving & Workspace Reloading
- Multi-Format Export Options (High-Res PNG, Standalone HTML, Configuration JSON)
- Robust Data Validation & Graceful Handling of Edge Cases
"""
from typing import Optional, Dict, Any, List
import json
import datetime
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
    get_icon_svg,
    get_type_badge_html
)

from modules.data_loader import (
    get_available_sample_datasets,
    load_sample_dataset_by_key,
    set_active_dataset
)
from modules.visualization_engine import (
    CHART_FAMILIES,
    CHART_METADATA,
    AGGREGATION_OPTIONS,
    SORT_OPTIONS,
    get_dataset_column_types,
    is_chart_compatible,
    get_compatible_chart_types,
    build_chart,
    generate_chart_recommendations,
    generate_chart_insights,
    export_chart_png,
    export_chart_html,
    export_chart_config_json
)


def _init_viz_state() -> None:
    """Initialize Visualization Studio session state variables."""
    if "viz_selected_family" not in st.session_state:
        st.session_state["viz_selected_family"] = "Comparison"
    if "viz_selected_chart" not in st.session_state:
        st.session_state["viz_selected_chart"] = "bar"
    if "viz_config" not in st.session_state:
        st.session_state["viz_config"] = {}
    if "saved_visualizations" not in st.session_state:
        st.session_state["saved_visualizations"] = []


def render_visualization_page() -> None:
    """Main entry point for the Visualization Studio workspace."""
    _init_viz_state()

    # 1. Empty State Check
    if not is_dataset_loaded():
        render_page_header(
            title="Visualization",
            subtitle="Interactive multi-dimensional chart builder with smart visual recommendations.",
            icon="bar-chart-3"
        )
        render_empty_state(
            title="No dataset loaded for visualization",
            description="Upload a CSV or Excel file to start building interactive charts and exploring visual insights.",
            icon="bar-chart-3"
        )

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        render_section_header(
            title="Quick Start with Sample Data",
            subtitle="Select a pre-loaded business dataset to immediately explore the Visualization Studio."
        )

        sample_catalog = get_available_sample_datasets()
        cols = st.columns(len(sample_catalog) if sample_catalog else 1)
        for idx, (key, info) in enumerate(sample_catalog.items()):
            with cols[idx]:
                st.markdown(f"**{info['name']}**")
                st.caption(info["description"])
                if st.button(f"Load {info['name']}", key=f"viz_sample_load_{key}", type="primary", use_container_width=True):
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
            if st.button("Upload Custom Dataset", key="viz_goto_dataset_btn", use_container_width=True):
                st.session_state["current_page"] = "Dataset"
                st.rerun()
        return

    # 2. Extract Active Dataset and Theme
    df: pd.DataFrame = st.session_state.get("dataset")
    metadata: Dict[str, Any] = st.session_state.get("dataset_metadata", {})
    dataset_name = st.session_state.get("dataset_name", "dataset.csv")
    file_type = st.session_state.get("dataset_file_type", "CSV")
    current_theme = st.session_state.get("theme", "Dark")

    if df is None or df.empty:
        render_page_header(
            title="Visualization",
            subtitle="Interactive multi-dimensional chart builder with smart visual recommendations.",
            icon="bar-chart-3"
        )
        render_notification(
            title="Dataset State Error",
            message="Active dataset contains no rows. Please upload or reload your data.",
            variant="error"
        )
        return

    col_types = get_dataset_column_types(df)
    compat_types_by_family = get_compatible_chart_types(df, col_types)

    # 3. Standard Page Header
    render_page_header(
        title="Visualize Data",
        subtitle="Interactive multi-dimensional chart builder with smart visual recommendations.",
        icon="bar-chart-3"
    )
    mark_workflow_step("visualize", True)

    # 4. Context Bar
    _render_context_bar(dataset_name, file_type, metadata)

    # 5. Smart Recommendations Bar
    _render_recommendations_section(df, metadata)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 6. Main Chart Studio (Builder Controls + Interactive Canvas)
    _render_chart_studio(df, col_types, compat_types_by_family, current_theme)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # 7. Saved Visualizations Gallery
    _render_saved_visualizations_section(df, current_theme)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 8. Workflow Next Step Guidance Banner
    render_next_step_banner(
        title="Visualizations are ready.",
        recommendation="Build an executive dashboard combining your key metrics, trend distributions, and charts.",
        primary_action_label="OPEN DASHBOARD →",
        target_page="Dashboard",
        key_prefix="viz_next_step"
    )

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    c_ai, c_nav = st.columns([4, 6])
    with c_ai:
        render_ai_context_trigger("Suggest chart recommendations with AI", intent="viz_recommend", key="viz_ai_btn")
    with c_nav:
        st.markdown("<div style='display:flex; justify-content:flex-end; gap:8px;'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Analyze Data (EDA)", key="viz_nav_eda_btn", use_container_width=True):
                st.session_state["current_page"] = "EDA"
                st.rerun()
        with col2:
            if st.button("Dataset Overview", key="viz_nav_ov_btn", use_container_width=True):
                st.session_state["current_page"] = "Overview"
                st.rerun()



# =============================================================================
# CONTEXT BAR
# =============================================================================

def _render_context_bar(name: str, file_type: str, metadata: Dict[str, Any]) -> None:
    """Render compact context bar with active dataset metadata."""
    total_rows = metadata.get("total_rows", 0)
    total_cols = metadata.get("total_columns", 0)
    memory_formatted = metadata.get("memory_formatted", "")

    col_info, col_btn = st.columns([8, 4])
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

    with col_btn:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        if st.button("Change Dataset", key="viz_change_dataset_btn", use_container_width=True):
            st.session_state["current_page"] = "Dataset"
            st.rerun()


# =============================================================================
# RECOMMENDED VISUALIZATIONS SECTION
# =============================================================================

def _render_recommendations_section(df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Render deterministic smart recommendation cards with 1-click apply."""
    recommendations = generate_chart_recommendations(df, metadata)
    if not recommendations:
        return

    with st.expander("✨ Recommended Visualizations (Auto-Generated)", expanded=True):
        st.caption("Intelligent chart recommendations based on column data types and business heuristics. Click 'Apply' to instantly load any configuration.")
        
        cols = st.columns(min(len(recommendations), 3))
        for i, rec in enumerate(recommendations):
            col_idx = i % 3
            with cols[col_idx]:
                chart_meta = CHART_METADATA.get(rec["chart_type"], {})
                badge_html = f'<span class="ds-badge ds-badge-numeric" style="margin-bottom: 6px;">{rec.get("badge", "Insight")}</span>'
                
                card_html = (
                    f'<div class="ds-metric-card" style="padding: 14px; margin-bottom: 8px; min-height: 120px;">'
                    f'{badge_html}'
                    f'<div style="font-weight: 600; font-size: 13px; color: var(--text-primary); margin-top: 4px;">{rec["title"]}</div>'
                    f'<div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px; line-height: 1.4;">{rec["description"]}</div>'
                    f'</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

                if st.button(f"Apply {chart_meta.get('name', 'Chart')}", key=f"apply_rec_{rec['id']}", use_container_width=True):
                    st.session_state["viz_selected_family"] = rec["family"]
                    st.session_state["viz_selected_chart"] = rec["chart_type"]
                    st.session_state["viz_config"] = rec["config"]
                    st.toast(f"Applied {rec['title']} to chart builder!")
                    st.rerun()


# =============================================================================
# MAIN CHART STUDIO WORKSPACE
# =============================================================================

def _render_chart_studio(
    df: pd.DataFrame,
    col_types: Dict[str, List[str]],
    compat_families: Dict[str, List[str]],
    theme: str
) -> None:
    """Render the chart family/type selectors, dynamic config controls, and preview canvas."""
    render_section_header(
        title="Visualization Workspace",
        subtitle="Select a chart family, configure dimensions and metrics, and explore the interactive preview."
    )

    numeric_cols = col_types["Numeric"]
    categorical_cols = col_types["Categorical"] + col_types["Boolean"]
    datetime_cols = col_types["Date/Time"]
    all_cols = col_types["All"]

    # 1. Chart Family Selector
    active_family = st.session_state.get("viz_selected_family", "Comparison")
    available_families = [f for f in CHART_FAMILIES.keys() if f in compat_families]
    if active_family not in available_families and available_families:
        active_family = available_families[0]
        st.session_state["viz_selected_family"] = active_family

    fam_cols = st.columns(len(available_families) if available_families else 1)
    for idx, fam_name in enumerate(available_families):
        with fam_cols[idx]:
            is_active = (fam_name == active_family)
            btn_type = "primary" if is_active else "secondary"
            if st.button(fam_name, key=f"fam_btn_{fam_name}", type=btn_type, use_container_width=True):
                st.session_state["viz_selected_family"] = fam_name
                # Set default chart in family
                if compat_families.get(fam_name):
                    st.session_state["viz_selected_chart"] = compat_families[fam_name][0]
                st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 2. Specific Chart Type Selector within Selected Family
    compatible_charts = compat_families.get(active_family, [])
    active_chart = st.session_state.get("viz_selected_chart", "bar")
    if active_chart not in compatible_charts and compatible_charts:
        active_chart = compatible_charts[0]
        st.session_state["viz_selected_chart"] = active_chart

    c_cols = st.columns(len(compatible_charts) if compatible_charts else 1)
    for idx, c_type in enumerate(compatible_charts):
        meta = CHART_METADATA.get(c_type, {})
        with c_cols[idx]:
            is_active = (c_type == active_chart)
            btn_type = "primary" if is_active else "secondary"
            btn_label = meta.get("name", c_type.replace("_", " ").title())
            if st.button(btn_label, key=f"chart_btn_{c_type}", type=btn_type, use_container_width=True):
                st.session_state["viz_selected_chart"] = c_type
                st.rerun()

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 3. Dynamic Configuration Controls
    active_meta = CHART_METADATA.get(active_chart, {})
    current_config = st.session_state.get("viz_config", {})

    with st.container():
        st.markdown(
            f'<div class="ds-section-header" style="margin-bottom: 8px;">'
            f'<div style="font-weight: 600; font-size: 13px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em;">'
            f'Configuration Controls — {active_meta.get("name", active_chart)}'
            f'</div>'
            f'<div style="font-size: 12px; color: var(--text-muted);">{active_meta.get("description", "")}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        config = _render_dynamic_controls(active_chart, df, col_types, current_config)
        st.session_state["viz_config"] = config

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 4. Large Interactive Chart Preview Area
    _render_chart_preview_canvas(active_chart, df, config, theme)


# =============================================================================
# DYNAMIC CONFIGURATION CONTROLS PANEL
# =============================================================================

def _render_dynamic_controls(
    chart_type: str,
    df: pd.DataFrame,
    col_types: Dict[str, List[str]],
    saved_cfg: Dict[str, Any]
) -> Dict[str, Any]:
    """Dynamically render only relevant input controls for the chosen chart type."""
    numeric_cols = col_types["Numeric"]
    categorical_cols = col_types["Categorical"] + col_types["Boolean"] + col_types["Text"]
    datetime_cols = col_types["Date/Time"]
    all_cols = col_types["All"]

    config: Dict[str, Any] = dict(saved_cfg)

    # -------------------------------------------------------------------------
    # Correlation Heatmap Controls
    # -------------------------------------------------------------------------
    if chart_type == "heatmap":
        col1, col2 = st.columns([8, 4])
        with col1:
            default_cols = config.get("columns", numeric_cols[:10])
            valid_defaults = [c for c in default_cols if c in numeric_cols]
            selected_cols = st.multiselect(
                "Numeric Columns for Correlation Matrix",
                options=numeric_cols,
                default=valid_defaults if valid_defaults else numeric_cols[:8],
                key="viz_ctrl_heatmap_cols"
            )
            config["columns"] = selected_cols
        with col2:
            method_opts = ["pearson", "spearman"]
            saved_m = config.get("method", "pearson")
            method_idx = method_opts.index(saved_m) if saved_m in method_opts else 0
            method = st.selectbox("Correlation Method", options=method_opts, index=method_idx, format_func=str.capitalize, key="viz_ctrl_heatmap_method")
            config["method"] = method

        config["title"] = f"Pairwise Feature Correlation Matrix ({config['method'].capitalize()})"
        config["height"] = 480
        return config

    # -------------------------------------------------------------------------
    # Standard 1D / 2D / 3D Chart Controls
    # -------------------------------------------------------------------------
    ctrl_row1 = st.columns(3)
    
    # Control 1: X-Axis / Primary Category / Names
    with ctrl_row1[0]:
        if chart_type in ["bar", "grouped_bar", "pie", "donut"]:
            label = "Category / Dimension (X-Axis)" if chart_type != "pie" and chart_type != "donut" else "Slices / Category"
            options = categorical_cols + datetime_cols + numeric_cols
            saved_val = config.get("x")
            idx = options.index(saved_val) if saved_val in options else 0
            x_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_x")
            config["x"] = x_col

        elif chart_type == "horizontal_bar":
            label = "Category / Ranking (Y-Axis)"
            options = categorical_cols + datetime_cols + numeric_cols
            saved_val = config.get("y")
            idx = options.index(saved_val) if saved_val in options else 0
            y_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_y")
            config["y"] = y_col

        elif chart_type in ["line", "area"]:
            label = "Time / Sequence (X-Axis)"
            options = datetime_cols + numeric_cols + categorical_cols
            saved_val = config.get("x")
            idx = options.index(saved_val) if saved_val in options else 0
            x_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_x")
            config["x"] = x_col

        elif chart_type in ["scatter", "bubble"]:
            label = "X-Axis Column (Numeric)"
            options = numeric_cols if numeric_cols else all_cols
            saved_val = config.get("x")
            idx = options.index(saved_val) if saved_val in options else 0
            x_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_x")
            config["x"] = x_col

        elif chart_type == "histogram":
            label = "Distribution Column (Numeric)"
            options = numeric_cols if numeric_cols else all_cols
            saved_val = config.get("x")
            idx = options.index(saved_val) if saved_val in options else 0
            x_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_x")
            config["x"] = x_col

        elif chart_type in ["box", "violin"]:
            label = "Metric Column (Numeric Y-Axis)"
            options = numeric_cols if numeric_cols else all_cols
            saved_val = config.get("y")
            idx = options.index(saved_val) if saved_val in options else 0
            y_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_y")
            config["y"] = y_col

    # Control 2: Y-Axis / Metric / Values
    with ctrl_row1[1]:
        if chart_type in ["bar", "grouped_bar", "pie", "donut"]:
            label = "Metric / Value Column" if chart_type != "pie" and chart_type != "donut" else "Values / Metric"
            options = ["(Count Records)"] + numeric_cols
            saved_val = config.get("y")
            idx = options.index(saved_val) if saved_val in options else (1 if len(options) > 1 else 0)
            y_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_y")
            config["y"] = None if y_col == "(Count Records)" else y_col

        elif chart_type == "horizontal_bar":
            label = "Metric / Value Column"
            options = ["(Count Records)"] + numeric_cols
            saved_val = config.get("x")
            idx = options.index(saved_val) if saved_val in options else (1 if len(options) > 1 else 0)
            x_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_x")
            config["x"] = None if x_col == "(Count Records)" else x_col

        elif chart_type in ["line", "area"]:
            label = "Metric Column (Numeric Y-Axis)"
            options = numeric_cols if numeric_cols else all_cols
            saved_val = config.get("y")
            idx = options.index(saved_val) if saved_val in options else 0
            y_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_y")
            config["y"] = y_col

        elif chart_type in ["scatter", "bubble"]:
            label = "Y-Axis Column (Numeric)"
            options = numeric_cols if numeric_cols else all_cols
            saved_val = config.get("y")
            idx = options.index(saved_val) if saved_val in options else (1 if len(options) > 1 else 0)
            y_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_y")
            config["y"] = y_col

        elif chart_type == "histogram":
            bins_val = config.get("nbins", 30)
            nbins = st.slider("Number of Bins", min_value=5, max_value=80, value=bins_val, step=5, key="viz_ctrl_bins")
            config["nbins"] = nbins

        elif chart_type in ["box", "violin"]:
            label = "Group Dimension (Optional X-Axis)"
            options = ["(None)"] + categorical_cols + datetime_cols
            saved_val = config.get("x")
            idx = options.index(saved_val) if saved_val in options else 0
            x_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_box_x")
            config["x"] = None if x_col == "(None)" else x_col

    # Control 3: Aggregation Function or Bubble Size
    with ctrl_row1[2]:
        if chart_type in ["bar", "horizontal_bar", "grouped_bar", "line", "area", "pie", "donut"]:
            saved_agg = config.get("agg", "Sum")
            # If (Count Records) is active, fix to Count
            val_selection = config.get("y") if chart_type != "horizontal_bar" else config.get("x")
            if val_selection is None:
                agg_opts = ["Count"]
            else:
                agg_opts = AGGREGATION_OPTIONS

            idx = agg_opts.index(saved_agg) if saved_agg in agg_opts else 0
            agg = st.selectbox("Aggregation", options=agg_opts, index=idx, key="viz_ctrl_agg")
            config["agg"] = agg

        elif chart_type == "bubble":
            label = "Bubble Size Column (Numeric)"
            options = numeric_cols if numeric_cols else all_cols
            saved_val = config.get("size")
            idx = options.index(saved_val) if saved_val in options else (2 if len(options) > 2 else 0)
            size_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_size")
            config["size"] = size_col

        elif chart_type == "scatter":
            show_t = config.get("show_trendline", False)
            trend = st.checkbox("Show Trendline (OLS Regression)", value=show_t, key="viz_ctrl_trend")
            config["show_trendline"] = trend

        elif chart_type == "histogram":
            marginal_opts = ["box", "rug", "none"]
            saved_m = config.get("marginal", "box")
            idx = marginal_opts.index(saved_m) if saved_m in marginal_opts else 0
            marginal = st.selectbox("Marginal Distribution Plot", options=marginal_opts, index=idx, format_func=str.capitalize, key="viz_ctrl_marginal")
            config["marginal"] = marginal

        elif chart_type in ["box", "violin"]:
            point_opts = ["outliers", "all", "none"]
            saved_p = config.get("points", "outliers")
            idx = point_opts.index(saved_p) if saved_p in point_opts else 0
            points = st.selectbox("Point Display", options=point_opts, index=idx, format_func=str.capitalize, key="viz_ctrl_points")
            config["points"] = points

    # -------------------------------------------------------------------------
    # Secondary Controls Row (Color/Group, Sorting, Top N, Slices)
    # -------------------------------------------------------------------------
    ctrl_row2 = st.columns(3)

    with ctrl_row2[0]:
        # Color / Group Dimension
        if chart_type in ["bar", "horizontal_bar", "line", "area", "scatter", "bubble", "histogram"]:
            color_opts = ["(None)"] + categorical_cols
            saved_c = config.get("color")
            idx = color_opts.index(saved_c) if saved_c in color_opts else 0
            color = st.selectbox("Color / Group Segment (Optional)", options=color_opts, index=idx, key="viz_ctrl_color")
            config["color"] = None if color == "(None)" else color

        elif chart_type == "grouped_bar":
            color_opts = categorical_cols if categorical_cols else all_cols
            saved_c = config.get("color")
            idx = color_opts.index(saved_c) if saved_c in color_opts else (1 if len(color_opts) > 1 else 0)
            color = st.selectbox("Group / Stack Dimension (Color)", options=color_opts, index=idx, key="viz_ctrl_grouped_color")
            config["color"] = color

        elif chart_type in ["pie", "donut"]:
            saved_n = config.get("top_n", 8)
            top_n = st.slider("Max Slices (Top N Categories)", min_value=3, max_value=20, value=saved_n, step=1, key="viz_ctrl_topn_pie")
            config["top_n"] = top_n

        elif chart_type in ["box", "violin"]:
            color_opts = ["(None)"] + categorical_cols
            saved_c = config.get("color")
            idx = color_opts.index(saved_c) if saved_c in color_opts else 0
            color = st.selectbox("Color Segment (Optional)", options=color_opts, index=idx, key="viz_ctrl_box_color")
            config["color"] = None if color == "(None)" else color

    with ctrl_row2[1]:
        # Sorting or Barmode
        if chart_type in ["bar", "horizontal_bar"]:
            sort_keys = [opt[0] for opt in SORT_OPTIONS]
            sort_labels = [opt[1] for opt in SORT_OPTIONS]
            saved_s = config.get("sort", "value_desc")
            idx = sort_keys.index(saved_s) if saved_s in sort_keys else 0
            sort_by = st.selectbox("Sort Order", options=sort_keys, index=idx, format_func=lambda k: dict(SORT_OPTIONS).get(k, k), key="viz_ctrl_sort")
            config["sort"] = sort_by

        elif chart_type == "grouped_bar":
            barmodes = ["group", "stack"]
            saved_bm = config.get("barmode", "group")
            idx = barmodes.index(saved_bm) if saved_bm in barmodes else 0
            barmode = st.selectbox("Bar Display Mode", options=barmodes, index=idx, format_func=str.capitalize, key="viz_ctrl_barmode")
            config["barmode"] = barmode

        elif chart_type in ["line", "area"]:
            show_m = config.get("show_markers", True)
            markers = st.checkbox("Show Data Point Markers", value=show_m, key="viz_ctrl_markers")
            config["show_markers"] = markers

        elif chart_type in ["scatter", "bubble"]:
            color_opts = ["(None)"] + categorical_cols + numeric_cols
            saved_c = config.get("color")
            idx = color_opts.index(saved_c) if saved_c in color_opts else 0
            color = st.selectbox("Color Attribute (Optional)", options=color_opts, index=idx, key="viz_ctrl_scatter_color")
            config["color"] = None if color == "(None)" else color

        elif chart_type == "violin":
            show_b = config.get("show_box", True)
            box_toggle = st.checkbox("Show Inner Box Plot", value=show_b, key="viz_ctrl_violin_box")
            config["show_box"] = box_toggle

    with ctrl_row2[2]:
        # Top N Filter for Bar / Horizontal Bar
        if chart_type in ["bar", "horizontal_bar", "grouped_bar"]:
            saved_n = config.get("top_n", 15)
            top_n = st.slider("Limit Categories (Top N)", min_value=5, max_value=40, value=saved_n, step=5, key="viz_ctrl_topn_bar")
            config["top_n"] = top_n

        elif chart_type in ["scatter", "bubble", "line", "area", "histogram", "box", "pie", "donut", "violin"]:
            chart_height = st.slider("Chart Canvas Height", min_value=350, max_value=700, value=config.get("height", 460), step=20, key="viz_ctrl_height")
            config["height"] = chart_height

    # Auto-generate dynamic default title
    if "title" not in config or not config["title"]:
        val_name = config.get("y") or config.get("x") or "Records"
        dim_name = config.get("x") or config.get("y") or "Dimension"
        agg_name = config.get("agg", "Total")
        config["title"] = f"{agg_name} of {val_name} by {dim_name}"

    return config


# =============================================================================
# CHART PREVIEW CANVAS & ACTIONS
# =============================================================================

def _render_chart_preview_canvas(
    chart_type: str,
    df: pd.DataFrame,
    config: Dict[str, Any],
    theme: str
) -> None:
    """Render the Plotly chart figure, action toolbar, insights, and exports."""
    # Build chart figure
    fig, data_df, err = build_chart(chart_type, df, config, theme=theme)

    if err or fig is None:
        render_notification(
            title="Chart Generation Issue",
            message=f"Unable to render visualization: {err}",
            variant="warning"
        )
        return

    # 1. Preview Header & Action Toolbar
    toolbar_col1, toolbar_col2 = st.columns([7, 5])
    with toolbar_col1:
        st.markdown(
            f'<div style="font-weight: 600; font-size: 15px; color: var(--text-primary); padding-top: 4px;">'
            f'{config.get("title", "Interactive Preview")}'
            f'</div>',
            unsafe_allow_html=True
        )

    with toolbar_col2:
        btn_save, btn_export = st.columns([1, 1])
        with btn_save:
            if st.button("Save to Session", key="viz_save_btn", type="primary", use_container_width=True):
                saved_list = st.session_state.get("saved_visualizations", [])
                saved_item = {
                    "id": f"saved_{len(saved_list) + 1}_{int(datetime.datetime.now().timestamp())}",
                    "chart_type": chart_type,
                    "title": config.get("title", f"{chart_type.title()} Chart"),
                    "config": dict(config),
                    "created_at": datetime.datetime.now().strftime("%I:%M %p")
                }
                saved_list.append(saved_item)
                st.session_state["saved_visualizations"] = saved_list
                st.toast("Chart saved to active session!")
                st.rerun()

        with btn_export:
            # Multi-format export expander / popover
            with st.popover("Export Chart", use_container_width=True):
                st.markdown("<div style='font-weight: 600; font-size: 13px; margin-bottom: 6px;'>Export Options</div>", unsafe_allow_html=True)
                
                # 1. High-Res PNG Download
                png_bytes, png_err = export_chart_png(fig)
                if png_bytes:
                    st.download_button(
                        label="Download PNG Image",
                        data=png_bytes,
                        file_name=f"{config.get('title', 'chart').replace(' ', '_').lower()}.png",
                        mime="image/png",
                        key="viz_dl_png",
                        use_container_width=True
                    )
                else:
                    st.caption("PNG export requires Kaleido.")

                # 2. Interactive Standalone HTML Download
                html_str = export_chart_html(fig, title=config.get("title", "Visualization"))
                st.download_button(
                    label="Download Interactive HTML",
                    data=html_str,
                    file_name=f"{config.get('title', 'chart').replace(' ', '_').lower()}.html",
                    mime="text/html",
                    key="viz_dl_html",
                    use_container_width=True
                )

                # 3. Chart Configuration JSON Download
                json_str = export_chart_config_json(config, chart_type)
                st.download_button(
                    label="Download Config JSON",
                    data=json_str,
                    file_name=f"{config.get('title', 'chart').replace(' ', '_').lower()}_config.json",
                    mime="application/json",
                    key="viz_dl_json",
                    use_container_width=True
                )

    # 2. Plotly Interactive Chart Display
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "responsive": True,
            "displaylogo": False,
            "toImageButtonOptions": {
                "format": "png",
                "filename": config.get("title", "chart").replace(" ", "_").lower(),
                "height": 650,
                "width": 1200,
                "scale": 2
            }
        }
    )

    # 3. Deterministic Chart Insights Panel
    insights = generate_chart_insights(chart_type, df, config, data_df=data_df)
    if insights:
        st.markdown(
            '<div style="font-weight: 600; font-size: 13px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 12px; margin-bottom: 8px;">'
            'Analytical Observations & Highlights'
            '</div>',
            unsafe_allow_html=True
        )

        ins_cols = st.columns(len(insights))
        for idx, ins in enumerate(insights):
            with ins_cols[idx]:
                render_metric_card(
                    label=ins["label"],
                    value=ins["value"],
                    description=ins["detail"],
                    change_type=ins.get("type", "neutral")
                )


# =============================================================================
# SAVED VISUALIZATIONS GALLERY SECTION
# =============================================================================

def _render_saved_visualizations_section(df: pd.DataFrame, theme: str) -> None:
    """Render active session saved charts shelf with 1-click reload and delete."""
    saved_list: List[Dict[str, Any]] = st.session_state.get("saved_visualizations", [])

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    header_col, action_col = st.columns([9, 3])
    with header_col:
        render_section_header(
            title="Saved Visualizations",
            subtitle="Access, reload, or remove charts saved during your current session."
        )
    with action_col:
        if saved_list:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            if st.button("Clear All Saved", key="viz_clear_saved_btn", use_container_width=True):
                st.session_state["saved_visualizations"] = []
                st.toast("Saved visualizations cleared.")
                st.rerun()

    if not saved_list:
        render_notification(
            title="No Saved Visualizations",
            message="Configure any chart above and click 'Save to Session' to pin it here for quick access.",
            variant="info"
        )
        return

    # Render saved cards grid
    grid_cols = st.columns(min(len(saved_list), 3))
    for idx, item in enumerate(saved_list):
        col_idx = idx % 3
        with grid_cols[col_idx]:
            c_type = item["chart_type"]
            meta = CHART_METADATA.get(c_type, {})
            c_name = meta.get("name", c_type.title())
            cfg = item["config"]
            
            card_html = (
                f'<div class="ds-metric-card" style="padding: 14px; margin-bottom: 8px;">'
                f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">'
                f'<span class="ds-badge ds-badge-numeric">{c_name}</span>'
                f'<span style="font-size: 11px; color: var(--text-muted);">{item.get("created_at", "")}</span>'
                f'</div>'
                f'<div style="font-weight: 600; font-size: 13px; color: var(--text-primary); margin-top: 4px;">{item["title"]}</div>'
                f'<div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">'
                f'X: {cfg.get("x") or "(Default)"} · Y: {cfg.get("y") or "(Count)"} · Agg: {cfg.get("agg", "Sum")}'
                f'</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

            btn_load, btn_del = st.columns([2, 1])
            with btn_load:
                if st.button("Load Chart", key=f"load_saved_{item['id']}", type="primary", use_container_width=True):
                    st.session_state["viz_selected_family"] = meta.get("family", "Comparison")
                    st.session_state["viz_selected_chart"] = c_type
                    st.session_state["viz_config"] = cfg
                    st.toast(f"Loaded '{item['title']}' into workspace!")
                    st.rerun()

            with btn_del:
                if st.button("Delete", key=f"del_saved_{item['id']}", use_container_width=True):
                    saved_list = [s for s in saved_list if s["id"] != item["id"]]
                    st.session_state["saved_visualizations"] = saved_list
                    st.toast("Chart deleted from session.")
                    st.rerun()

            # Expandable quick inline preview
            with st.expander("Quick Preview"):
                preview_fig, _, p_err = build_chart(c_type, df, cfg, theme=theme)
                if preview_fig and not p_err:
                    preview_fig.update_layout(height=260, margin=dict(l=20, r=20, t=30, b=20))
                    st.plotly_chart(preview_fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.caption("Preview unavailable.")

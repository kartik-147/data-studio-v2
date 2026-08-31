"""
DATA STUDIO v2 — Interactive Visualization Studio (Module 8)
=============================================================================
Professional, systematic self-service chart-building workspace delivering:
- 25 Supported Chart Types across 6 Families (Comparison, Trends, Relationships,
  Distribution, Composition, Advanced & KPIs)
- Systematic Split Studio Layout (Left Configuration Console + Right Live Canvas)
- Theme-Aware Custom Palettes (Sapphire, Emerald, Sunset, Cyber Neon, Autumn, Titanium)
- Deterministic Smart Recommendations & 1-Click Quick Preset Templates
- Large Responsive Theme-Aware Interactive Plotly Canvas (Dark / Light)
- Real-Time Deterministic Analytical Chart Insights & Data Inspector
- Active Session-Level Chart Saving & Workspace Reloading Shelf
- Multi-Format Export Options (High-Res PNG, Standalone HTML, Config JSON, Transformed CSV)
- Universal Standardized Bottom Workflow Navigation
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
    render_ai_context_trigger,
    render_next_workflow_steps,
    get_icon_svg
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
    COLOR_PALETTES,
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
            title="Visualization Studio",
            subtitle="Interactive multi-dimensional chart builder with real-time visual analytics.",
            icon="bar-chart-3"
        )
        render_empty_state(
            title="No dataset loaded for visualization",
            description="Upload a CSV or Excel file or pick a pre-loaded sample dataset to start building interactive charts.",
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
    current_theme = st.session_state.get("theme", "Light")

    if df is None or df.empty:
        render_page_header(
            title="Visualization Studio",
            subtitle="Interactive multi-dimensional chart builder with real-time visual analytics.",
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
        title="Visualization Studio",
        subtitle="Systematic BI visual builder with 25+ chart types, dynamic dimensions, and analytical insights.",
        icon="bar-chart-3"
    )
    mark_workflow_step("visualize", True)

    # 4. Context Bar & Quick Presets
    _render_context_and_presets_bar(df, dataset_name, file_type, metadata, col_types)

    # 5. Smart Recommendations Shelf
    _render_recommendations_section(df, metadata)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 6. Main Split Studio (Left Config Console + Right Live Canvas)
    _render_split_studio(df, col_types, compat_types_by_family, current_theme)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 7. Saved Visualizations Gallery Shelf
    _render_saved_visualizations_section(df, current_theme)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    render_ai_context_trigger("Ask AI Analyst about this Visualization", intent="viz_recommend", key="viz_ai_btn")
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 8. Standardized Universal Bottom Workflow Navigation
    render_next_workflow_steps("Visualization")


# =============================================================================
# CONTEXT & QUICK PRESET BAR
# =============================================================================

def _render_context_and_presets_bar(
    df: pd.DataFrame,
    name: str,
    file_type: str,
    metadata: Dict[str, Any],
    col_types: Dict[str, List[str]]
) -> None:
    """Render compact context bar with active dataset metadata and 1-click preset templates."""
    total_rows = metadata.get("total_rows", len(df))
    total_cols = metadata.get("total_columns", len(df.columns))
    memory_formatted = metadata.get("memory_formatted", "")

    col_info, col_btn = st.columns([8.2, 3.8])
    with col_info:
        banner_html = (
            f'<div class="ds-active-banner" style="margin-bottom: 8px; padding: 8px 14px;">'
            f'<div class="ds-active-banner-left">'
            f'<div class="ds-brand-badge" style="background: var(--accent);">{file_type[0] if file_type else "D"}</div>'
            f'<div>'
            f'<div class="ds-active-banner-name" style="font-size: 14px; font-weight: 700;">{name}</div>'
            f'<div class="ds-active-banner-meta" style="font-size: 11.5px;">'
            f'{total_rows:,} rows · {total_cols} columns · {len(col_types["Numeric"])} numeric · {len(col_types["Categorical"])} categorical · {memory_formatted}'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(banner_html, unsafe_allow_html=True)

    with col_btn:
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
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

    with st.expander("Smart Visual Recommendations & Insights (Auto-Generated)", expanded=False):
        st.caption("Heuristic recommendations tailored to your dataset schema. Click 'Apply' to load any chart configuration instantly.")
        
        cols = st.columns(min(len(recommendations), 3))
        for i, rec in enumerate(recommendations):
            col_idx = i % 3
            with cols[col_idx]:
                chart_meta = CHART_METADATA.get(rec["chart_type"], {})
                badge_html = f'<span class="ds-badge ds-badge-numeric" style="margin-bottom: 4px;">{rec.get("badge", "Insight")}</span>'
                
                card_html = (
                    f'<div class="ds-metric-card" style="padding: 12px; margin-bottom: 6px; min-height: 110px;">'
                    f'{badge_html}'
                    f'<div style="font-weight: 600; font-size: 12.5px; color: var(--text-primary); margin-top: 2px;">{rec["title"]}</div>'
                    f'<div style="font-size: 11px; color: var(--text-secondary); margin-top: 2px; line-height: 1.35;">{rec["description"]}</div>'
                    f'</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

                if st.button(f"Apply {chart_meta.get('name', 'Chart')}", key=f"apply_rec_{rec['id']}", use_container_width=True):
                    st.session_state["viz_selected_family"] = rec["family"]
                    st.session_state["viz_selected_chart"] = rec["chart_type"]
                    st.session_state["viz_config"] = rec["config"]
                    st.toast(f"Applied '{rec['title']}' to workspace!")
                    st.rerun()


# =============================================================================
# SYSTEMATIC 2-COLUMN SPLIT STUDIO WORKSPACE
# =============================================================================

def _render_split_studio(
    df: pd.DataFrame,
    col_types: Dict[str, List[str]],
    compat_families: Dict[str, List[str]],
    theme: str
) -> None:
    """Render systematic 2-column BI Studio: Left Configuration Console + Right Live Canvas."""
    col_controls, col_canvas = st.columns([3.8, 8.2], gap="medium")

    # ── Left Column: Configuration Deck ───────────────────────────────────────
    with col_controls:
        st.markdown(
            '<div style="font-weight: 700; font-size: 13.5px; color: var(--text-primary); text-transform: uppercase; letter-spacing: 0.05em; padding-bottom: 6px; border-bottom: 2px solid var(--accent); margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">'
            '<span>⚙ Configuration Console</span>'
            '</div>',
            unsafe_allow_html=True
        )

        # 1. Family Navigation Pills
        active_family = st.session_state.get("viz_selected_family", "Comparison")
        available_families = [f for f in CHART_FAMILIES.keys() if f in compat_families]
        if active_family not in available_families and available_families:
            active_family = available_families[0]
            st.session_state["viz_selected_family"] = active_family

        fam_cols = st.columns(3)
        fam_list = list(CHART_FAMILIES.keys())
        for idx, fam_name in enumerate(fam_list):
            c_idx = idx % 3
            with fam_cols[c_idx]:
                is_active = (fam_name == active_family)
                btn_type = "primary" if is_active else "secondary"
                if st.button(fam_name, key=f"fam_btn_{fam_name}", type=btn_type, use_container_width=True):
                    st.session_state["viz_selected_family"] = fam_name
                    if compat_families.get(fam_name):
                        st.session_state["viz_selected_chart"] = compat_families[fam_name][0]
                    st.rerun()

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # 2. Chart Type Picker Grid for Active Family
        compatible_charts = compat_families.get(active_family, CHART_FAMILIES.get(active_family, []))
        active_chart = st.session_state.get("viz_selected_chart", "bar")
        if active_chart not in compatible_charts and compatible_charts:
            active_chart = compatible_charts[0]
            st.session_state["viz_selected_chart"] = active_chart

        st.markdown(
            f'<div style="font-size: 11.5px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">'
            f'Chart Type ({len(compatible_charts)} Available in {active_family})'
            f'</div>',
            unsafe_allow_html=True
        )

        type_cols = st.columns(2)
        for idx, c_type in enumerate(compatible_charts):
            meta = CHART_METADATA.get(c_type, {})
            c_idx = idx % 2
            with type_cols[c_idx]:
                is_active = (c_type == active_chart)
                btn_type = "primary" if is_active else "secondary"
                btn_label = meta.get("name", c_type.replace("_", " ").title())
                if st.button(btn_label, key=f"chart_btn_{c_type}", type=btn_type, use_container_width=True):
                    st.session_state["viz_selected_chart"] = c_type
                    st.rerun()

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # 3. Dynamic Configuration Parameters (Tabbed Sections)
        active_meta = CHART_METADATA.get(active_chart, {})
        current_config = st.session_state.get("viz_config", {})

        st.caption(f"ℹ {active_meta.get('description', '')}")

        tab_encoding, tab_grouping, tab_styling = st.tabs([
            "DIMENSIONS",
            "CHANNELS & GROUP",
            "STYLING & THEME"
        ])

        with tab_encoding:
            config = _render_encoding_controls(active_chart, df, col_types, current_config)

        with tab_grouping:
            config = _render_grouping_controls(active_chart, df, col_types, config)

        with tab_styling:
            config = _render_styling_controls(active_chart, df, col_types, config)

        st.session_state["viz_config"] = config

    # ── Right Column: High-Definition Interactive Canvas & Intelligence ─────────
    with col_canvas:
        _render_canvas_intelligence_hub(active_chart, df, config, theme)


# =============================================================================
# DYNAMIC ENCODING & CONTROL TAB RENDERERS
# =============================================================================

def _render_encoding_controls(
    chart_type: str,
    df: pd.DataFrame,
    col_types: Dict[str, List[str]],
    saved_cfg: Dict[str, Any]
) -> Dict[str, Any]:
    """Render primary X/Y axis, multi-metrics, and aggregation controls."""
    numeric_cols = col_types["Numeric"]
    categorical_cols = col_types["Categorical"] + col_types["Boolean"] + col_types["Text"]
    datetime_cols = col_types["Date/Time"]
    all_cols = col_types["All"]

    config: Dict[str, Any] = dict(saved_cfg)

    # 1. Correlation Heatmap Special Encoding
    if chart_type == "heatmap":
        default_cols = config.get("columns", numeric_cols[:10])
        valid_defaults = [c for c in default_cols if c in numeric_cols]
        selected_cols = st.multiselect(
            "Matrix Columns (Numeric)",
            options=numeric_cols,
            default=valid_defaults if valid_defaults else numeric_cols[:8],
            key="viz_ctrl_heatmap_cols"
        )
        config["columns"] = selected_cols
        config["title"] = f"Pairwise Feature Correlation Matrix ({config.get('method', 'pearson').capitalize()})"
        return config

    # 2. Multi-Metric Trend / Radar Special Encoding
    if chart_type in ["multi_line", "radar"]:
        if chart_type == "multi_line":
            dt_options = datetime_cols + numeric_cols + categorical_cols
            saved_x = config.get("x")
            idx_x = dt_options.index(saved_x) if saved_x in dt_options else 0
            x_col = st.selectbox("Timeline / Sequence Axis (X)", options=dt_options, index=idx_x, key="viz_ctrl_multiline_x")
            config["x"] = x_col

        elif chart_type == "radar":
            cat_options = ["(Dataset Overall)"] + categorical_cols
            saved_x = config.get("x")
            idx_x = cat_options.index(saved_x) if saved_x in cat_options else 0
            x_col = st.selectbox("Category Grouping (Optional)", options=cat_options, index=idx_x, key="viz_ctrl_radar_x")
            config["x"] = None if x_col == "(Dataset Overall)" else x_col

        saved_metrics = config.get("metrics", numeric_cols[:3])
        valid_metrics = [m for m in saved_metrics if m in numeric_cols]
        metrics = st.multiselect(
            "Numeric Metric Columns",
            options=numeric_cols,
            default=valid_metrics if valid_metrics else numeric_cols[:min(len(numeric_cols), 4)],
            key="viz_ctrl_multi_metrics"
        )
        config["metrics"] = metrics

        saved_agg = config.get("agg", "Mean" if chart_type == "radar" else "Sum")
        agg_opts = AGGREGATION_OPTIONS
        idx_agg = agg_opts.index(saved_agg) if saved_agg in agg_opts else 0
        agg = st.selectbox("Metric Aggregation", options=agg_opts, index=idx_agg, key="viz_ctrl_multi_agg")
        config["agg"] = agg
        return config

    # 3. KPI Gauge Special Encoding
    if chart_type == "gauge":
        saved_y = config.get("y")
        idx_y = numeric_cols.index(saved_y) if saved_y in numeric_cols else 0
        y_col = st.selectbox("Target Numeric Metric", options=numeric_cols if numeric_cols else all_cols, index=idx_y, key="viz_ctrl_gauge_y")
        config["y"] = y_col

        saved_agg = config.get("agg", "Mean")
        agg_opts = ["Mean", "Sum", "Median", "Maximum", "Minimum"]
        idx_agg = agg_opts.index(saved_agg) if saved_agg in agg_opts else 0
        agg = st.selectbox("Calculation Aggregation", options=agg_opts, index=idx_agg, key="viz_ctrl_gauge_agg")
        config["agg"] = agg
        return config

    # 4. Standard 1D / 2D / 3D Dimensions
    # Primary Category / X-Axis
    if chart_type in ["bar", "grouped_bar", "lollipop", "waterfall", "pie", "donut", "treemap", "sunburst", "funnel"]:
        label = "Category / Dimension (X-Axis)" if chart_type not in ["pie", "donut", "treemap", "sunburst", "funnel"] else "Category / Slices"
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

    elif chart_type in ["line", "area", "stepline"]:
        label = "Time / Sequence (X-Axis)"
        options = datetime_cols + numeric_cols + categorical_cols
        saved_val = config.get("x")
        idx = options.index(saved_val) if saved_val in options else 0
        x_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_x")
        config["x"] = x_col

    elif chart_type in ["scatter", "bubble", "scatter_3d", "density_contour", "histogram", "ecdf"]:
        label = "X-Axis Column (Numeric)"
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

    # Secondary Metric / Y-Axis
    if chart_type in ["bar", "grouped_bar", "lollipop", "pie", "donut", "treemap", "sunburst", "funnel"]:
        label = "Metric / Value Column" if chart_type not in ["pie", "donut"] else "Values / Metric"
        options = ["(Count Records)"] + numeric_cols
        saved_val = config.get("y")
        idx = options.index(saved_val) if saved_val in options else (1 if len(options) > 1 else 0)
        y_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_y")
        config["y"] = None if y_col == "(Count Records)" else y_col

    elif chart_type == "waterfall":
        label = "Variance / Value Column (Numeric)"
        options = numeric_cols if numeric_cols else all_cols
        saved_val = config.get("y")
        idx = options.index(saved_val) if saved_val in options else 0
        y_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_y")
        config["y"] = y_col

    elif chart_type == "horizontal_bar":
        label = "Metric / Value Column"
        options = ["(Count Records)"] + numeric_cols
        saved_val = config.get("x")
        idx = options.index(saved_val) if saved_val in options else (1 if len(options) > 1 else 0)
        x_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_x")
        config["x"] = None if x_col == "(Count Records)" else x_col

    elif chart_type in ["line", "area", "stepline", "scatter", "bubble", "scatter_3d", "density_contour"]:
        label = "Y-Axis Column (Numeric)"
        options = numeric_cols if numeric_cols else all_cols
        saved_val = config.get("y")
        idx = options.index(saved_val) if saved_val in options else (1 if len(options) > 1 else 0)
        y_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_y")
        config["y"] = y_col

    elif chart_type in ["box", "violin"]:
        label = "Group Dimension (Optional X-Axis)"
        options = ["(None)"] + categorical_cols + datetime_cols
        saved_val = config.get("x")
        idx = options.index(saved_val) if saved_val in options else 0
        x_col = st.selectbox(label, options=options, index=idx, key="viz_ctrl_box_x")
        config["x"] = None if x_col == "(None)" else x_col

    # Aggregation Function
    if chart_type in ["bar", "horizontal_bar", "grouped_bar", "lollipop", "waterfall", "line", "area", "stepline", "pie", "donut", "treemap", "sunburst", "funnel"]:
        saved_agg = config.get("agg", "Sum")
        val_selection = config.get("y") if chart_type != "horizontal_bar" else config.get("x")
        if val_selection is None:
            agg_opts = ["Count"]
        else:
            agg_opts = AGGREGATION_OPTIONS

        idx = agg_opts.index(saved_agg) if saved_agg in agg_opts else 0
        agg = st.selectbox("Aggregation Function", options=agg_opts, index=idx, key="viz_ctrl_agg")
        config["agg"] = agg

    return config


def _render_grouping_controls(
    chart_type: str,
    df: pd.DataFrame,
    col_types: Dict[str, List[str]],
    saved_cfg: Dict[str, Any]
) -> Dict[str, Any]:
    """Render color grouping, secondary dimensions, size, 3D Z, and sorting."""
    numeric_cols = col_types["Numeric"]
    categorical_cols = col_types["Categorical"] + col_types["Boolean"] + col_types["Text"]
    datetime_cols = col_types["Date/Time"]
    all_cols = col_types["All"]

    config: Dict[str, Any] = dict(saved_cfg)

    # 1. Treemap & Sunburst Sub-Category Hierarchy
    if chart_type in ["treemap", "sunburst"]:
        sub_opts = ["(None)"] + [c for c in categorical_cols if c != config.get("x")]
        saved_sub = config.get("sub_category")
        idx_sub = sub_opts.index(saved_sub) if saved_sub in sub_opts else (1 if len(sub_opts) > 1 else 0)
        sub_cat = st.selectbox("Sub-Hierarchy Dimension", options=sub_opts, index=idx_sub, key="viz_ctrl_subcat")
        config["sub_category"] = None if sub_cat == "(None)" else sub_cat

    # 2. 3D Scatter Z-Axis
    if chart_type == "scatter_3d":
        saved_z = config.get("z")
        remaining_nums = [c for c in numeric_cols if c not in [config.get("x"), config.get("y")]]
        options_z = remaining_nums if remaining_nums else numeric_cols
        idx_z = options_z.index(saved_z) if saved_z in options_z else 0
        z_col = st.selectbox("Z-Axis Column (Numeric)", options=options_z, index=idx_z, key="viz_ctrl_z")
        config["z"] = z_col

    # 3. Bubble Size Attribute
    if chart_type in ["bubble", "scatter", "scatter_3d"]:
        if chart_type == "bubble":
            saved_sz = config.get("size")
            idx_sz = numeric_cols.index(saved_sz) if saved_sz in numeric_cols else (2 if len(numeric_cols) > 2 else 0)
            sz_col = st.selectbox("Bubble Size Column (Numeric)", options=numeric_cols if numeric_cols else all_cols, index=idx_sz, key="viz_ctrl_bubble_size")
            config["size"] = sz_col
        else:
            sz_opts = ["(None)"] + numeric_cols
            saved_sz = config.get("size")
            idx_sz = sz_opts.index(saved_sz) if saved_sz in sz_opts else 0
            sz_col = st.selectbox("Marker Size Attribute (Optional)", options=sz_opts, index=idx_sz, key="viz_ctrl_scatter_size")
            config["size"] = None if sz_col == "(None)" else sz_col

    # 4. Color / Group Segment
    if chart_type in ["bar", "horizontal_bar", "lollipop", "line", "area", "stepline", "scatter", "bubble", "scatter_3d", "density_contour", "histogram", "ecdf"]:
        color_opts = ["(None)"] + categorical_cols + (numeric_cols if chart_type in ["scatter", "scatter_3d"] else [])
        saved_c = config.get("color")
        idx_c = color_opts.index(saved_c) if saved_c in color_opts else 0
        color = st.selectbox("Color / Group Segment", options=color_opts, index=idx_c, key="viz_ctrl_color")
        config["color"] = None if color == "(None)" else color

    elif chart_type == "grouped_bar":
        color_opts = categorical_cols if categorical_cols else all_cols
        saved_c = config.get("color")
        idx_c = color_opts.index(saved_c) if saved_c in color_opts else (1 if len(color_opts) > 1 else 0)
        color = st.selectbox("Group / Stack Dimension (Color)", options=color_opts, index=idx_c, key="viz_ctrl_grouped_color")
        config["color"] = color

        barmodes = ["group", "stack"]
        saved_bm = config.get("barmode", "group")
        idx_bm = barmodes.index(saved_bm) if saved_bm in barmodes else 0
        barmode = st.selectbox("Bar Display Mode", options=barmodes, index=idx_bm, format_func=str.capitalize, key="viz_ctrl_barmode")
        config["barmode"] = barmode

    elif chart_type in ["box", "violin"]:
        color_opts = ["(None)"] + categorical_cols
        saved_c = config.get("color")
        idx_c = color_opts.index(saved_c) if saved_c in color_opts else 0
        color = st.selectbox("Color Segment", options=color_opts, index=idx_c, key="viz_ctrl_box_color")
        config["color"] = None if color == "(None)" else color

    # 5. Sorting Controls
    if chart_type in ["bar", "horizontal_bar", "lollipop"]:
        sort_keys = [opt[0] for opt in SORT_OPTIONS]
        saved_s = config.get("sort", "value_desc" if chart_type != "horizontal_bar" else "value_asc")
        idx_s = sort_keys.index(saved_s) if saved_s in sort_keys else 0
        sort_by = st.selectbox("Sort Order", options=sort_keys, index=idx_s, format_func=lambda k: dict(SORT_OPTIONS).get(k, k), key="viz_ctrl_sort")
        config["sort"] = sort_by

    # 6. Slices & Top N Limiter
    if chart_type in ["bar", "horizontal_bar", "grouped_bar", "lollipop", "waterfall", "pie", "donut", "funnel"]:
        max_limit = 20 if chart_type in ["pie", "donut", "funnel"] else 40
        saved_n = config.get("top_n", 10 if chart_type in ["pie", "donut", "funnel"] else 15)
        top_n = st.slider("Limit Categories (Top N)", min_value=3, max_value=max_limit, value=min(saved_n, max_limit), step=1 if max_limit <= 20 else 5, key="viz_ctrl_topn")
        config["top_n"] = top_n

    elif chart_type == "histogram":
        bins_val = config.get("nbins", 30)
        nbins = st.slider("Number of Bins", min_value=5, max_value=80, value=bins_val, step=5, key="viz_ctrl_bins")
        config["nbins"] = nbins

        marginal_opts = ["box", "rug", "none"]
        saved_m = config.get("marginal", "box")
        idx_m = marginal_opts.index(saved_m) if saved_m in marginal_opts else 0
        marginal = st.selectbox("Marginal Plot", options=marginal_opts, index=idx_m, format_func=str.capitalize, key="viz_ctrl_marginal")
        config["marginal"] = marginal

    elif chart_type == "scatter":
        show_t = config.get("show_trendline", False)
        trend = st.checkbox("Show OLS Trendline", value=show_t, key="viz_ctrl_trend")
        config["show_trendline"] = trend

    elif chart_type == "heatmap":
        method_opts = ["pearson", "spearman"]
        saved_m = config.get("method", "pearson")
        idx_m = method_opts.index(saved_m) if saved_m in method_opts else 0
        method = st.selectbox("Correlation Method", options=method_opts, index=idx_m, format_func=str.capitalize, key="viz_ctrl_heatmap_method")
        config["method"] = method

    return config


def _render_styling_controls(
    chart_type: str,
    df: pd.DataFrame,
    col_types: Dict[str, List[str]],
    saved_cfg: Dict[str, Any]
) -> Dict[str, Any]:
    """Render color palette, height slider, and custom chart title."""
    config: Dict[str, Any] = dict(saved_cfg)

    # 1. Color Palette Selector
    pal_opts = list(COLOR_PALETTES.keys())
    saved_pal = config.get("palette", "Classic SaaS")
    idx_pal = pal_opts.index(saved_pal) if saved_pal in pal_opts else 0
    palette = st.selectbox("Color Palette", options=pal_opts, index=idx_pal, key="viz_ctrl_palette")
    config["palette"] = palette

    # 2. Chart Canvas Height
    saved_h = config.get("height", 460)
    chart_height = st.slider("Canvas Height (px)", min_value=360, max_value=720, value=saved_h, step=20, key="viz_ctrl_height")
    config["height"] = chart_height

    # 3. Chart Title Customization
    default_title = config.get("title", "")
    if not default_title:
        val_name = config.get("y") or config.get("x") or "Records"
        dim_name = config.get("x") or config.get("y") or "Dimension"
        agg_name = config.get("agg", "Total")
        default_title = f"{agg_name} of {val_name} by {dim_name}"

    title_input = st.text_input("Chart Title", value=default_title, key="viz_ctrl_custom_title")
    config["title"] = title_input

    return config


# =============================================================================
# LIVE CANVAS & INTELLIGENCE HUB
# =============================================================================

def _render_canvas_intelligence_hub(
    chart_type: str,
    df: pd.DataFrame,
    config: Dict[str, Any],
    theme: str
) -> None:
    """Render interactive Plotly canvas, live toolbar, deterministic insights, and data drawer."""
    # Build chart figure
    fig, data_df, err = build_chart(chart_type, df, config, theme=theme)

    if err or fig is None:
        render_notification(
            title="Chart Generation Warning",
            message=f"Unable to render visualization: {err}. Try adjusting dimension or metric selections.",
            variant="warning"
        )
        return

    # 1. Top Action Toolbar
    toolbar_col1, toolbar_col2 = st.columns([7, 5])
    with toolbar_col1:
        st.markdown(
            f'<div style="font-weight: 700; font-size: 15px; color: var(--text-primary); padding-top: 4px;">'
            f'{config.get("title", "Interactive Preview")}'
            f'</div>',
            unsafe_allow_html=True
        )

    with toolbar_col2:
        btn_save, btn_export = st.columns([1, 1])
        with btn_save:
            if st.button("Save Chart", key="viz_save_btn", type="primary", use_container_width=True):
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
                st.toast("Saved to active session gallery! ✓")
                st.rerun()

        with btn_export:
            with st.popover("Export", use_container_width=True):
                st.markdown("<div style='font-weight: 600; font-size: 13px; margin-bottom: 6px;'>Export Options</div>", unsafe_allow_html=True)
                
                # 1. PNG Image Export
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

                # 2. Interactive Standalone HTML Export
                html_str = export_chart_html(fig, title=config.get("title", "Visualization"))
                st.download_button(
                    label="Download Interactive HTML",
                    data=html_str,
                    file_name=f"{config.get('title', 'chart').replace(' ', '_').lower()}.html",
                    mime="text/html",
                    key="viz_dl_html",
                    use_container_width=True
                )

                # 3. Configuration JSON Export
                json_str = export_chart_config_json(config, chart_type)
                st.download_button(
                    label="Download Config JSON",
                    data=json_str,
                    file_name=f"{config.get('title', 'chart').replace(' ', '_').lower()}_config.json",
                    mime="application/json",
                    key="viz_dl_json",
                    use_container_width=True
                )

                # 4. Transformed CSV Dataset Export
                if data_df is not None and not data_df.empty:
                    csv_data = data_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="Download Transformed CSV",
                        data=csv_data,
                        file_name=f"{config.get('title', 'data').replace(' ', '_').lower()}_aggregated.csv",
                        mime="text/csv",
                        key="viz_dl_csv",
                        use_container_width=True
                    )

    # 2. Interactive Plotly Figure Display
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

    # 3. Deterministic Analytical Highlights Panel
    insights = generate_chart_insights(chart_type, df, config, data_df=data_df)
    if insights:
        st.markdown(
            '<div style="font-weight: 700; font-size: 12px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 8px; margin-bottom: 6px;">'
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

    # 4. Transformed Data Table Inspector Drawer
    if data_df is not None and not data_df.empty:
        with st.expander(f"Transformed Data Inspector ({len(data_df):,} rows feeding active chart)", expanded=False):
            st.dataframe(data_df, use_container_width=True, height=220)


# =============================================================================
# SAVED VISUALIZATIONS GALLERY SECTION
# =============================================================================

def _render_saved_visualizations_section(df: pd.DataFrame, theme: str) -> None:
    """Render active session saved charts shelf with 1-click reload, preview, and delete."""
    saved_list: List[Dict[str, Any]] = st.session_state.get("saved_visualizations", [])

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    header_col, action_col = st.columns([9, 3])
    with header_col:
        render_section_header(
            title="Saved Visualizations Gallery",
            subtitle="Access, reload, inspect, or manage charts pinned during your current session."
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
            title="No Saved Visualizations in Session",
            message="Configure any chart above and click 'Save Chart' to pin it here for quick multi-chart review.",
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
                f'<div class="ds-metric-card" style="padding: 12px; margin-bottom: 6px;">'
                f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">'
                f'<span class="ds-badge ds-badge-numeric">{c_name}</span>'
                f'<span style="font-size: 11px; color: var(--text-muted);">{item.get("created_at", "")}</span>'
                f'</div>'
                f'<div style="font-weight: 600; font-size: 13px; color: var(--text-primary); margin-top: 2px;">{item["title"]}</div>'
                f'<div style="font-size: 11px; color: var(--text-secondary); margin-top: 2px;">'
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

            with st.expander("Thumbnail Preview"):
                preview_fig, _, p_err = build_chart(c_type, df, cfg, theme=theme)
                if preview_fig and not p_err:
                    preview_fig.update_layout(height=240, margin=dict(l=15, r=15, t=25, b=15))
                    st.plotly_chart(preview_fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.caption("Preview unavailable.")

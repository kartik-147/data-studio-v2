"""
DATA STUDIO v2 — Visualization Studio Analytics & Rendering Engine
=============================================================================
Modular, decoupled engine for:
- Supported Chart Types (Comparison, Trends, Relationships, Distribution, Composition, Advanced)
- Dataset Schema & Chart Compatibility Profiling
- Robust Data Transformations & Multi-Dimensional Aggregations
- Design System-Aware Plotly Visualizations (Dark/Light themes)
- Deterministic Smart Recommendations Engine
- Deterministic Analytical Chart Insights Engine
- Multi-Format Chart Export (PNG, Interactive HTML, Configuration JSON)
"""
from typing import Optional, Dict, Any, List, Tuple
import json
import re
import io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from modules.data_loader import detect_column_type


# =============================================================================
# CHART TAXONOMY & SPECIFICATIONS (12 Chart Types across 6 Families)
# =============================================================================

CHART_FAMILIES: Dict[str, List[str]] = {
    "Comparison": ["bar", "horizontal_bar", "grouped_bar"],
    "Trends": ["line", "area"],
    "Relationships": ["scatter", "bubble"],
    "Distribution": ["histogram", "box"],
    "Composition": ["pie", "donut"],
    "Advanced": ["heatmap", "violin"]
}

CHART_METADATA: Dict[str, Dict[str, Any]] = {
    "bar": {
        "name": "Bar Chart",
        "family": "Comparison",
        "icon": "bar-chart-3",
        "description": "Compare metrics across distinct categorical groups with vertical bars.",
        "requires_x": True,
        "requires_y": False,  # If no Y, counts records
        "supports_color": True,
        "supports_agg": True,
        "supports_top_n": True
    },
    "horizontal_bar": {
        "name": "Horizontal Bar Chart",
        "family": "Comparison",
        "icon": "bar-chart-3",
        "description": "Ideal for ranking categories with long labels or displaying leaderboards.",
        "requires_x": False,  # If no X, counts records
        "requires_y": True,
        "supports_color": True,
        "supports_agg": True,
        "supports_top_n": True
    },
    "grouped_bar": {
        "name": "Grouped / Stacked Bar",
        "family": "Comparison",
        "icon": "layers",
        "description": "Multi-dimensional category comparison grouped or stacked by a secondary attribute.",
        "requires_x": True,
        "requires_y": False,
        "requires_color": True,
        "supports_agg": True,
        "supports_barmode": True
    },
    "line": {
        "name": "Line Chart",
        "family": "Trends",
        "icon": "bar-chart-3",
        "description": "Track changes, progressions, and continuous trends over time or sequence.",
        "requires_x": True,
        "requires_y": True,
        "supports_color": True,
        "supports_agg": True
    },
    "area": {
        "name": "Area Chart",
        "family": "Trends",
        "icon": "layers",
        "description": "Visualize volume and continuous cumulative trends over time.",
        "requires_x": True,
        "requires_y": True,
        "supports_color": True,
        "supports_agg": True
    },
    "scatter": {
        "name": "Scatter Plot",
        "family": "Relationships",
        "icon": "sparkles",
        "description": "Examine correlation, clustering, and relationships between two numeric variables.",
        "requires_x": True,
        "requires_y": True,
        "supports_color": True,
        "supports_size": True,
        "supports_trendline": True
    },
    "bubble": {
        "name": "Bubble Chart",
        "family": "Relationships",
        "icon": "sparkles",
        "description": "Three-variable relationship plot using X, Y positions and marker circle size.",
        "requires_x": True,
        "requires_y": True,
        "requires_size": True,
        "supports_color": True
    },
    "histogram": {
        "name": "Histogram",
        "family": "Distribution",
        "icon": "bar-chart-3",
        "description": "Display frequency distribution, spread, and skewness of a numeric column.",
        "requires_x": True,
        "requires_y": False,
        "supports_color": True,
        "supports_bins": True
    },
    "box": {
        "name": "Box Plot",
        "family": "Distribution",
        "icon": "layers",
        "description": "Summarize statistical medians, quartiles, and detect potential outliers.",
        "requires_y": True,
        "supports_x": True,
        "supports_color": True
    },
    "pie": {
        "name": "Pie Chart",
        "family": "Composition",
        "icon": "bar-chart-3",
        "description": "Display proportional breakdown and component shares of a whole.",
        "requires_x": True,  # Names/Labels
        "requires_y": False,  # Values (count or numeric sum)
        "supports_agg": True,
        "supports_top_n": True
    },
    "donut": {
        "name": "Donut Chart",
        "family": "Composition",
        "icon": "bar-chart-3",
        "description": "Modern ring chart showing proportional categorical composition.",
        "requires_x": True,  # Names/Labels
        "requires_y": False,  # Values (count or numeric sum)
        "supports_agg": True,
        "supports_top_n": True
    },
    "heatmap": {
        "name": "Correlation Heatmap",
        "family": "Advanced",
        "icon": "layout-dashboard",
        "description": "Matrix of pairwise statistical correlation coefficients across numeric variables.",
        "requires_multi_numeric": True,
        "supports_method": True
    },
    "violin": {
        "name": "Violin Plot",
        "family": "Advanced",
        "icon": "layers",
        "description": "Combines box plot summary with kernel density distribution curves.",
        "requires_y": True,
        "supports_x": True,
        "supports_color": True
    }
}

AGGREGATION_OPTIONS = [
    "Count",
    "Sum",
    "Mean",
    "Median",
    "Minimum",
    "Maximum"
]

SORT_OPTIONS = [
    ("value_desc", "Value: High to Low"),
    ("value_asc", "Value: Low to High"),
    ("alpha_asc", "Category: A to Z"),
    ("alpha_desc", "Category: Z to A"),
    ("default", "Default / Original Order")
]


# =============================================================================
# THEME PALETTES & PLOTLY STYLING
# =============================================================================

THEME_CONFIGS = {
    "Dark": {
        "bg": "rgba(0,0,0,0)",
        "paper_bg": "rgba(0,0,0,0)",
        "plot_bg": "rgba(0,0,0,0)",
        "text": "#f8fafc",
        "subtext": "#94a3b8",
        "grid": "#1e293b",
        "zero_line": "#3b82f6",
        "primary": "#3b82f6",
        "palette": ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ec4899", "#06b6d4", "#6366f1", "#14b8a6"],
        "sequential": "Blues",
        "diverging": "RdBu",
        "tooltip_bg": "#141b2d",
        "tooltip_border": "#3b82f6",
        "tooltip_text": "#f8fafc"
    },
    "Light": {
        "bg": "rgba(0,0,0,0)",
        "paper_bg": "rgba(0,0,0,0)",
        "plot_bg": "rgba(0,0,0,0)",
        "text": "#0f172a",
        "subtext": "#475569",
        "grid": "#e2e8f0",
        "zero_line": "#2563eb",
        "primary": "#2563eb",
        "palette": ["#2563eb", "#7c3aed", "#059669", "#d97706", "#db2777", "#0891b2", "#4f46e5", "#0d9488"],
        "sequential": "Blues",
        "diverging": "RdBu",
        "tooltip_bg": "#ffffff",
        "tooltip_border": "#2563eb",
        "tooltip_text": "#0f172a"
    }
}


def apply_chart_theme(
    fig: go.Figure,
    theme: str = "Dark",
    title: Optional[str] = None,
    height: int = 460,
    show_legend: bool = True,
    x_title: Optional[str] = None,
    y_title: Optional[str] = None
) -> go.Figure:
    """Apply consistent design system typography, colors, borders, and margins."""
    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
    
    layout_update: Dict[str, Any] = {
        "paper_bgcolor": cfg["paper_bg"],
        "plot_bgcolor": cfg["plot_bg"],
        "font": {
            "family": "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
            "color": cfg["text"],
            "size": 12
        },
        "margin": dict(l=50, r=30, t=55 if title else 25, b=50),
        "height": height,
        "showlegend": show_legend,
        "hoverlabel": {
            "bgcolor": cfg["tooltip_bg"],
            "bordercolor": cfg["tooltip_border"],
            "font": {"color": cfg["tooltip_text"], "size": 12}
        },
        "colorway": cfg["palette"]
    }

    if title:
        layout_update["title"] = {
            "text": f"<b>{title}</b>",
            "font": {
                "size": 14,
                "color": cfg["text"],
                "family": "Inter, sans-serif"
            },
            "x": 0.0,
            "xanchor": "left",
            "y": 0.98,
            "yanchor": "top"
        }

    if show_legend:
        layout_update["legend"] = dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            font=dict(size=11, color=cfg["subtext"])
        )

    fig.update_layout(**layout_update)

    # Standardize Cartesian Axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor=cfg["grid"],
        showline=True,
        linewidth=1,
        linecolor=cfg["grid"],
        tickfont=dict(color=cfg["subtext"], size=11),
        title_font=dict(color=cfg["text"], size=12)
    )
    if x_title is not None:
        fig.update_xaxes(title_text=x_title)

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor=cfg["grid"],
        showline=True,
        linewidth=1,
        linecolor=cfg["grid"],
        tickfont=dict(color=cfg["subtext"], size=11),
        title_font=dict(color=cfg["text"], size=12)
    )
    if y_title is not None:
        fig.update_yaxes(title_text=y_title)

    return fig


# =============================================================================
# COLUMN CLASSIFICATION & COMPATIBILITY HELPERS
# =============================================================================

def get_dataset_column_types(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Profile DataFrame columns into semantic lists:
    - Numeric
    - Categorical
    - Date/Time
    - Text
    - Boolean
    - All
    """
    if df is None or df.empty:
        return {
            "Numeric": [],
            "Categorical": [],
            "Date/Time": [],
            "Text": [],
            "Boolean": [],
            "All": []
        }
        
    total_rows = len(df)
    cols_by_type: Dict[str, List[str]] = {
        "Numeric": [],
        "Categorical": [],
        "Date/Time": [],
        "Text": [],
        "Boolean": [],
        "All": list(df.columns)
    }
    
    for col in df.columns:
        series = df[col]
        detected = detect_column_type(series, str(col), total_rows)
        if detected in cols_by_type:
            cols_by_type[detected].append(col)
        else:
            cols_by_type["Text"].append(col)
            
    return cols_by_type


def is_chart_compatible(chart_type: str, df: pd.DataFrame, col_types: Optional[Dict[str, List[str]]] = None) -> Tuple[bool, str]:
    """
    Check if a chart type is compatible with the current dataset columns.
    Returns (is_compatible, reason).
    """
    if df is None or df.empty:
        return False, "No active dataset available."
        
    if col_types is None:
        col_types = get_dataset_column_types(df)
        
    num_cols = len(col_types["Numeric"])
    total_cols = len(df.columns)

    if chart_type in ["bar", "horizontal_bar", "pie", "donut"]:
        if total_cols >= 1:
            return True, "Compatible"
        return False, "Requires at least 1 column in the dataset."

    elif chart_type == "grouped_bar":
        if total_cols >= 2:
            return True, "Compatible"
        return False, "Requires at least 2 columns to group dimensions."

    elif chart_type in ["line", "area"]:
        if num_cols >= 1 and total_cols >= 2:
            return True, "Compatible"
        elif num_cols >= 1 and total_cols >= 1:
            return True, "Compatible (using index for trend)"
        return False, "Requires at least 1 numeric column to plot trend magnitude."

    elif chart_type == "scatter":
        if num_cols >= 2:
            return True, "Compatible"
        elif num_cols >= 1 and total_cols >= 2:
            return True, "Compatible (numeric vs category/sequence)"
        return False, "Requires at least 2 columns (preferably numeric) to analyze relationship."

    elif chart_type == "bubble":
        if num_cols >= 2 and total_cols >= 3:
            return True, "Compatible"
        elif num_cols >= 2:
            return True, "Compatible"
        return False, "Requires at least 2-3 columns with numeric attributes for sizing."

    elif chart_type in ["histogram", "box"]:
        if num_cols >= 1:
            return True, "Compatible"
        return False, "Requires at least 1 numeric column to compute distributions."

    elif chart_type == "heatmap":
        if num_cols >= 2:
            return True, "Compatible"
        return False, "Requires at least 2 numeric columns to compute correlation matrix."

    elif chart_type == "violin":
        if num_cols >= 1:
            return True, "Compatible"
        return False, "Requires at least 1 numeric column to compute violin density."

    return False, "Unknown chart type."


def get_compatible_chart_types(df: pd.DataFrame, col_types: Optional[Dict[str, List[str]]] = None) -> Dict[str, List[str]]:
    """Return dictionary mapping chart families to compatible chart type keys."""
    if col_types is None:
        col_types = get_dataset_column_types(df)
        
    result: Dict[str, List[str]] = {}
    for family, types in CHART_FAMILIES.items():
        compat_in_family = [t for t in types if is_chart_compatible(t, df, col_types)[0]]
        if compat_in_family:
            result[family] = compat_in_family
    return result


# =============================================================================
# DATA AGGREGATION & TRANSFORMATION ENGINE
# =============================================================================

def aggregate_data(
    df: pd.DataFrame,
    x_col: Optional[str] = None,
    y_col: Optional[str] = None,
    agg_func: str = "Sum",
    color_col: Optional[str] = None,
    sort_by: str = "default",
    top_n: Optional[int] = 15,
    orientation: str = "vertical"
) -> Tuple[pd.DataFrame, str, str]:
    """
    Safely transform and aggregate data for chart rendering.
    Returns (aggregated_df, effective_x_col, effective_y_col).
    """
    if df is None or df.empty:
        return pd.DataFrame(), "", ""

    is_horizontal = (orientation == "horizontal")
    dim_col = y_col if is_horizontal else x_col
    val_col = x_col if is_horizontal else y_col

    # Validate column presence in DataFrame
    if dim_col and dim_col not in df.columns:
        dim_col = None
    if val_col and val_col != "(Count Records)" and val_col not in df.columns:
        val_col = None
    if color_col and (color_col == "(None)" or color_col not in df.columns):
        color_col = None

    # Handle scenario: Record count if no metric column is chosen or explicit Count
    if val_col is None or val_col == "(Count Records)" or agg_func == "Count":
        metric_name = "Record Count"
        group_keys = [dim_col] if dim_col else []
        if color_col and color_col != "(None)" and color_col != dim_col:
            group_keys.append(color_col)

        if group_keys:
            clean_df = df.dropna(subset=group_keys)
            grouped = clean_df.groupby(group_keys, as_index=False, observed=False).size()
            grouped.rename(columns={"size": metric_name}, inplace=True)
            res_df = grouped
        else:
            res_df = pd.DataFrame({metric_name: [len(df)]})

        metric_col = metric_name

    else:
        metric_col = f"{agg_func} of {val_col}"
        group_keys = [dim_col] if dim_col else []
        if color_col and color_col != "(None)" and color_col != dim_col:
            group_keys.append(color_col)

        agg_map = {
            "Sum": "sum",
            "Mean": "mean",
            "Median": "median",
            "Minimum": "min",
            "Maximum": "max"
        }
        pd_func = agg_map.get(agg_func, "sum")

        if group_keys:
            clean_df = df.dropna(subset=group_keys).copy()
            clean_df[val_col] = pd.to_numeric(clean_df[val_col], errors="coerce")
            clean_df = clean_df.dropna(subset=[val_col])

            grouped = clean_df.groupby(group_keys, as_index=False, observed=False)[val_col].agg(pd_func)
            grouped.rename(columns={val_col: metric_col}, inplace=True)
            res_df = grouped
        else:
            clean_series = pd.to_numeric(df[val_col], errors="coerce").dropna()
            val_result = getattr(clean_series, pd_func)() if not clean_series.empty else 0
            res_df = pd.DataFrame({metric_col: [val_result]})

    # Top N limiting for primary dimension if cardinality is high
    if dim_col and top_n and top_n > 0 and len(res_df) > 0:
        unique_dims = res_df[dim_col].nunique()
        if unique_dims > top_n:
            dim_totals = res_df.groupby(dim_col, observed=False)[metric_col].sum()
            top_keys = dim_totals.nlargest(top_n).index
            res_df = res_df[res_df[dim_col].isin(top_keys)].copy()

    # Sorting
    if not res_df.empty:
        if sort_by == "value_desc":
            res_df = res_df.sort_values(by=metric_col, ascending=False)
        elif sort_by == "value_asc":
            res_df = res_df.sort_values(by=metric_col, ascending=True)
        elif sort_by == "alpha_asc" and dim_col:
            res_df = res_df.sort_values(by=dim_col, ascending=True)
        elif sort_by == "alpha_desc" and dim_col:
            res_df = res_df.sort_values(by=dim_col, ascending=False)

    if is_horizontal:
        return res_df, metric_col, dim_col
    else:
        return res_df, dim_col, metric_col


# =============================================================================
# PLOTLY CHART GENERATORS (12 Types)
# =============================================================================

def generate_bar_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate professional vertical bar chart."""
    x_col = config.get("x")
    y_col = config.get("y")
    color_col = config.get("color")
    agg_func = config.get("agg", "Sum")
    sort_by = config.get("sort", "value_desc")
    top_n = config.get("top_n", 15)
    title = config.get("title", f"{agg_func} of {y_col or 'Records'} by {x_col}")
    height = config.get("height", 460)

    color_arg = color_col if (color_col and color_col != "(None)" and color_col != x_col) else None
    agg_df, eff_x, eff_y = aggregate_data(
        df, x_col=x_col, y_col=y_col, agg_func=agg_func,
        color_col=color_arg, sort_by=sort_by, top_n=top_n, orientation="vertical"
    )

    if agg_df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), agg_df

    fig = px.bar(
        agg_df,
        x=eff_x,
        y=eff_y,
        color=color_arg,
        barmode="group",
        text_auto=".2s" if len(agg_df) <= 20 else False
    )

    fig.update_traces(
        marker_line_width=0,
        opacity=0.92,
        hovertemplate="<b>%{x}</b><br>" + f"{eff_y}: %{{y:,.2f}}<extra></extra>"
    )

    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=bool(color_arg), x_title=str(eff_x), y_title=str(eff_y)
    )
    return fig, agg_df


def generate_horizontal_bar_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate professional horizontal bar chart."""
    x_col = config.get("x")
    y_col = config.get("y")
    color_col = config.get("color")
    agg_func = config.get("agg", "Sum")
    sort_by = config.get("sort", "value_asc")
    top_n = config.get("top_n", 15)
    title = config.get("title", f"{agg_func} of {x_col or 'Records'} by {y_col}")
    height = config.get("height", 460)

    color_arg = color_col if (color_col and color_col != "(None)" and color_col != y_col) else None
    agg_df, eff_x, eff_y = aggregate_data(
        df, x_col=x_col, y_col=y_col, agg_func=agg_func,
        color_col=color_arg, sort_by=sort_by, top_n=top_n, orientation="horizontal"
    )

    if agg_df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), agg_df

    fig = px.bar(
        agg_df,
        x=eff_x,
        y=eff_y,
        color=color_arg,
        orientation="h",
        text_auto=".2s" if len(agg_df) <= 20 else False
    )

    fig.update_traces(
        marker_line_width=0,
        opacity=0.92,
        hovertemplate="<b>%{y}</b><br>" + f"{eff_x}: %{{x:,.2f}}<extra></extra>"
    )

    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=bool(color_arg), x_title=str(eff_x), y_title=str(eff_y)
    )
    return fig, agg_df


def generate_grouped_bar_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate multi-dimensional grouped or stacked bar chart."""
    x_col = config.get("x")
    y_col = config.get("y")
    color_col = config.get("color")
    barmode = config.get("barmode", "group")
    agg_func = config.get("agg", "Sum")
    sort_by = config.get("sort", "value_desc")
    top_n = config.get("top_n", 12)
    title = config.get("title", f"{agg_func} of {y_col or 'Records'} by {x_col} and {color_col}")
    height = config.get("height", 460)

    color_arg = color_col if (color_col and color_col != "(None)") else None
    agg_df, eff_x, eff_y = aggregate_data(
        df, x_col=x_col, y_col=y_col, agg_func=agg_func,
        color_col=color_arg, sort_by=sort_by, top_n=top_n, orientation="vertical"
    )

    if agg_df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), agg_df

    fig = px.bar(
        agg_df,
        x=eff_x,
        y=eff_y,
        color=color_arg,
        barmode=barmode
    )

    fig.update_traces(
        marker_line_width=0,
        opacity=0.92,
        hovertemplate="<b>%{x}</b><br>" + f"{eff_y}: %{{y:,.2f}}<extra></extra>"
    )

    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=True, x_title=str(eff_x), y_title=str(eff_y)
    )
    return fig, agg_df


def generate_line_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate clean trend line chart with optional grouping and aggregation."""
    x_col = config.get("x")
    y_col = config.get("y")
    color_col = config.get("color")
    agg_func = config.get("agg", "Sum")
    show_markers = config.get("show_markers", True)
    title = config.get("title", f"{agg_func} of {y_col} across {x_col}")
    height = config.get("height", 460)

    color_arg = color_col if (color_col and color_col != "(None)" and color_col != x_col) else None

    agg_df, eff_x, eff_y = aggregate_data(
        df, x_col=x_col, y_col=y_col, agg_func=agg_func,
        color_col=color_arg, sort_by="alpha_asc", top_n=None, orientation="vertical"
    )

    if agg_df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), agg_df

    fig = px.line(
        agg_df,
        x=eff_x,
        y=eff_y,
        color=color_arg,
        markers=show_markers
    )

    fig.update_traces(
        line=dict(width=2.5),
        marker=dict(size=6),
        hovertemplate="<b>%{x}</b><br>" + f"{eff_y}: %{{y:,.2f}}<extra></extra>"
    )

    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=bool(color_arg), x_title=str(eff_x), y_title=str(eff_y)
    )
    return fig, agg_df


def generate_area_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate volume and cumulative trend area chart."""
    x_col = config.get("x")
    y_col = config.get("y")
    color_col = config.get("color")
    agg_func = config.get("agg", "Sum")
    title = config.get("title", f"{agg_func} of {y_col} Volume Trend across {x_col}")
    height = config.get("height", 460)

    color_arg = color_col if (color_col and color_col != "(None)" and color_col != x_col) else None

    agg_df, eff_x, eff_y = aggregate_data(
        df, x_col=x_col, y_col=y_col, agg_func=agg_func,
        color_col=color_arg, sort_by="alpha_asc", top_n=None, orientation="vertical"
    )

    if agg_df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), agg_df

    fig = px.area(
        agg_df,
        x=eff_x,
        y=eff_y,
        color=color_arg
    )

    fig.update_traces(
        line=dict(width=2),
        opacity=0.65,
        hovertemplate="<b>%{x}</b><br>" + f"{eff_y}: %{{y:,.2f}}<extra></extra>"
    )

    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=bool(color_arg), x_title=str(eff_x), y_title=str(eff_y)
    )
    return fig, agg_df


def generate_scatter_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate scatter plot with correlation and optional OLS regression trendline."""
    x_col = config.get("x")
    y_col = config.get("y")
    color_col = config.get("color")
    size_col = config.get("size")
    show_trendline = config.get("show_trendline", False)
    title = config.get("title", f"{y_col} vs {x_col} Relationship")
    height = config.get("height", 460)

    if df is None or df.empty or not x_col or not y_col:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), pd.DataFrame()

    subset_cols = [x_col, y_col]
    color_arg = color_col if (color_col and color_col != "(None)") else None
    if color_arg:
        subset_cols.append(color_arg)
    size_arg = size_col if (size_col and size_col != "(None)") else None
    if size_arg:
        subset_cols.append(size_arg)

    clean_df = df[subset_cols].dropna().copy()
    clean_df[x_col] = pd.to_numeric(clean_df[x_col], errors="coerce")
    clean_df[y_col] = pd.to_numeric(clean_df[y_col], errors="coerce")
    clean_df = clean_df.dropna(subset=[x_col, y_col])

    if size_arg:
        clean_df[size_arg] = pd.to_numeric(clean_df[size_arg], errors="coerce").fillna(1)
        clean_df[size_arg] = np.maximum(clean_df[size_arg], 0.1)

    if clean_df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), clean_df

    trend_mode = "ols" if show_trendline and len(clean_df) >= 3 else None
    try:
        fig = px.scatter(
            clean_df,
            x=x_col,
            y=y_col,
            color=color_arg,
            size=size_arg,
            trendline=trend_mode,
            trendline_color_override="#ef4444" if trend_mode else None
        )
    except Exception:
        fig = px.scatter(
            clean_df,
            x=x_col,
            y=y_col,
            color=color_arg,
            size=size_arg
        )

    fig.update_traces(
        marker=dict(opacity=0.8, line=dict(width=0.5, color="#1e293b"))
    )

    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=bool(color_arg), x_title=str(x_col), y_title=str(y_col)
    )
    return fig, clean_df


def generate_bubble_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate 3-variable bubble chart."""
    x_col = config.get("x")
    y_col = config.get("y")
    size_col = config.get("size")
    title = config.get("title", f"{y_col} vs {x_col} (Sized by {size_col})")
    height = config.get("height", 460)

    cfg = dict(config)
    cfg["size"] = size_col
    cfg["title"] = title
    cfg["height"] = height
    return generate_scatter_chart(df, cfg, theme=theme)


def generate_histogram_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate distribution histogram with customizable bin count and marginals."""
    x_col = config.get("x")
    color_col = config.get("color")
    nbins = config.get("nbins", 30)
    marginal = config.get("marginal", "box")
    title = config.get("title", f"Distribution of {x_col}")
    height = config.get("height", 460)

    if df is None or df.empty or not x_col:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), pd.DataFrame()

    subset_cols = [x_col]
    color_arg = color_col if (color_col and color_col != "(None)" and color_col != x_col) else None
    if color_arg:
        subset_cols.append(color_arg)

    clean_df = df[subset_cols].dropna().copy()
    clean_df[x_col] = pd.to_numeric(clean_df[x_col], errors="coerce")
    clean_df = clean_df.dropna(subset=[x_col])

    if clean_df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), clean_df

    marginal_opt = marginal if marginal in ["box", "rug"] else None

    fig = px.histogram(
        clean_df,
        x=x_col,
        color=color_arg,
        nbins=nbins,
        marginal=marginal_opt,
        opacity=0.85
    )

    fig.update_traces(
        marker_line_width=0.5,
        marker_line_color="#1e293b"
    )

    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=bool(color_arg), x_title=str(x_col), y_title="Frequency Count"
    )
    return fig, clean_df


def generate_box_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate statistical box plot with quartile markers and outlier points."""
    y_col = config.get("y")
    x_col = config.get("x")
    color_col = config.get("color")
    points = config.get("points", "outliers")
    title = config.get("title", f"Box Plot of {y_col}" + (f" by {x_col}" if x_col and x_col != "(None)" else ""))
    height = config.get("height", 460)

    if df is None or df.empty or not y_col:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), pd.DataFrame()

    subset_cols = [y_col]
    x_arg = x_col if (x_col and x_col != "(None)" and x_col != y_col) else None
    if x_arg:
        subset_cols.append(x_arg)
    color_arg = color_col if (color_col and color_col != "(None)" and color_col != y_col) else None
    if color_arg and color_arg not in subset_cols:
        subset_cols.append(color_arg)

    clean_df = df[subset_cols].dropna().copy()
    clean_df[y_col] = pd.to_numeric(clean_df[y_col], errors="coerce")
    clean_df = clean_df.dropna(subset=[y_col])

    if clean_df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), clean_df

    points_opt = points if points in ["outliers", "all"] else False

    fig = px.box(
        clean_df,
        x=x_arg,
        y=y_col,
        color=color_arg or x_arg,
        points=points_opt,
        notched=False
    )

    fig.update_traces(
        marker=dict(size=4, opacity=0.7),
        boxmean=True
    )

    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=bool(color_arg and color_arg != x_arg),
        x_title=str(x_arg) if x_arg else None,
        y_title=str(y_col)
    )
    return fig, clean_df


def generate_pie_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate proportional pie chart with top-slice limiting."""
    names_col = config.get("x")
    values_col = config.get("y")
    agg_func = config.get("agg", "Sum")
    top_n = config.get("top_n", 8)
    title = config.get("title", f"Proportion of {values_col or 'Records'} by {names_col}")
    height = config.get("height", 460)

    agg_df, eff_names, eff_vals = aggregate_data(
        df, x_col=names_col, y_col=values_col, agg_func=agg_func,
        sort_by="value_desc", top_n=top_n, orientation="vertical"
    )

    if agg_df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), agg_df

    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])

    fig = go.Figure(
        data=[
            go.Pie(
                labels=agg_df[eff_names],
                values=agg_df[eff_vals],
                hole=0.0,
                textinfo="label+percent",
                textposition="inside",
                insidetextorientation="radial",
                marker=dict(colors=cfg["palette"] * 4, line=dict(color=cfg["paper_bg"], width=1.5)),
                hovertemplate="<b>%{label}</b><br>" + f"{eff_vals}: %{{value:,.2f}}<br>Share: %{{percent}}<extra></extra>"
            )
        ]
    )

    apply_chart_theme(fig, theme=theme, title=title, height=height, show_legend=True)
    return fig, agg_df


def generate_donut_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate sleek donut chart with center hole and clean percentage hover."""
    names_col = config.get("x")
    values_col = config.get("y")
    agg_func = config.get("agg", "Sum")
    top_n = config.get("top_n", 8)
    title = config.get("title", f"Composition of {values_col or 'Records'} by {names_col}")
    height = config.get("height", 460)

    agg_df, eff_names, eff_vals = aggregate_data(
        df, x_col=names_col, y_col=values_col, agg_func=agg_func,
        sort_by="value_desc", top_n=top_n, orientation="vertical"
    )

    if agg_df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), agg_df

    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
    total_metric = agg_df[eff_vals].sum()

    if total_metric >= 1_000_000:
        center_text = f"${total_metric/1_000_000:.1f}M" if "sales" in str(values_col).lower() or "revenue" in str(values_col).lower() else f"{total_metric/1_000_000:.1f}M"
    elif total_metric >= 1_000:
        center_text = f"${total_metric/1_000:.1f}K" if "sales" in str(values_col).lower() or "revenue" in str(values_col).lower() else f"{total_metric/1_000:.1f}K"
    else:
        center_text = f"{total_metric:,.0f}"

    fig = go.Figure(
        data=[
            go.Pie(
                labels=agg_df[eff_names],
                values=agg_df[eff_vals],
                hole=0.55,
                textinfo="percent",
                textposition="inside",
                marker=dict(colors=cfg["palette"] * 4, line=dict(color=cfg["paper_bg"], width=2)),
                hovertemplate="<b>%{label}</b><br>" + f"{eff_vals}: %{{value:,.2f}}<br>Share: %{{percent}}<extra></extra>"
            )
        ]
    )

    fig.add_annotation(
        text=f"<b>{center_text}</b><br><span style='font-size: 10px; color: {cfg['subtext']};'>Total</span>",
        x=0.5, y=0.5,
        font=dict(size=14, color=cfg["text"]),
        showarrow=False
    )

    apply_chart_theme(fig, theme=theme, title=title, height=height, show_legend=True)
    return fig, agg_df


def generate_correlation_heatmap(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate pairwise correlation heatmap matrix with annotated coefficients."""
    selected_cols = config.get("columns")
    method = config.get("method", "pearson")
    title = config.get("title", f"Pairwise Feature Correlation Matrix ({method.capitalize()})")
    height = config.get("height", 460)

    if df is None or df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), pd.DataFrame()

    col_types = get_dataset_column_types(df)
    numeric_cols = col_types["Numeric"]

    if selected_cols and isinstance(selected_cols, list):
        target_cols = [c for c in selected_cols if c in numeric_cols]
    else:
        target_cols = numeric_cols[:12]

    if len(target_cols) < 2:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), pd.DataFrame()

    clean_df = df[target_cols].apply(pd.to_numeric, errors="coerce")
    corr_matrix = clean_df.corr(method=method).round(2)

    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])

    fig = go.Figure(
        data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale="RdBu",
            zmin=-1.0,
            zmax=1.0,
            colorbar=dict(
                title=dict(text="r", font=dict(color=cfg["text"], size=12)),
                tickfont=dict(color=cfg["subtext"], size=10),
                len=0.85
            ),
            hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.2f}<extra></extra>"
        )
    )

    annotations = []
    for i, row in enumerate(corr_matrix.index):
        for j, col in enumerate(corr_matrix.columns):
            val = corr_matrix.iloc[i, j]
            val_str = f"{val:.2f}" if not np.isnan(val) else "—"
            txt_color = "#ffffff" if abs(val) > 0.4 else cfg["text"]
            annotations.append(
                dict(
                    x=col,
                    y=row,
                    text=val_str,
                    font=dict(color=txt_color, size=11, family="JetBrains Mono, monospace"),
                    showarrow=False
                )
            )

    fig.update_layout(annotations=annotations)
    apply_chart_theme(fig, theme=theme, title=title, height=height, show_legend=False)
    return fig, corr_matrix


def generate_violin_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate distribution violin plot with embedded box markers."""
    y_col = config.get("y")
    x_col = config.get("x")
    color_col = config.get("color")
    show_box = config.get("show_box", True)
    points = config.get("points", "outliers")
    title = config.get("title", f"Violin Density Plot of {y_col}" + (f" by {x_col}" if x_col and x_col != "(None)" else ""))
    height = config.get("height", 460)

    if df is None or df.empty or not y_col:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), pd.DataFrame()

    subset_cols = [y_col]
    x_arg = x_col if (x_col and x_col != "(None)" and x_col != y_col) else None
    if x_arg:
        subset_cols.append(x_arg)
    color_arg = color_col if (color_col and color_col != "(None)" and color_col != y_col) else None
    if color_arg and color_arg not in subset_cols:
        subset_cols.append(color_arg)

    clean_df = df[subset_cols].dropna().copy()
    clean_df[y_col] = pd.to_numeric(clean_df[y_col], errors="coerce")
    clean_df = clean_df.dropna(subset=[y_col])

    if clean_df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), clean_df

    points_opt = points if points in ["outliers", "all"] else False

    fig = px.violin(
        clean_df,
        x=x_arg,
        y=y_col,
        color=color_arg or x_arg,
        box=show_box,
        points=points_opt
    )

    fig.update_traces(
        opacity=0.85,
        marker=dict(size=4)
    )

    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=bool(color_arg and color_arg != x_arg),
        x_title=str(x_arg) if x_arg else None,
        y_title=str(y_col)
    )
    return fig, clean_df


# Dispatcher map
CHART_BUILDERS = {
    "bar": generate_bar_chart,
    "horizontal_bar": generate_horizontal_bar_chart,
    "grouped_bar": generate_grouped_bar_chart,
    "line": generate_line_chart,
    "area": generate_area_chart,
    "scatter": generate_scatter_chart,
    "bubble": generate_bubble_chart,
    "histogram": generate_histogram_chart,
    "box": generate_box_chart,
    "pie": generate_pie_chart,
    "donut": generate_donut_chart,
    "heatmap": generate_correlation_heatmap,
    "violin": generate_violin_chart
}


def build_chart(
    chart_type: str,
    df: pd.DataFrame,
    config: Dict[str, Any],
    theme: str = "Dark"
) -> Tuple[Optional[go.Figure], Optional[pd.DataFrame], Optional[str]]:
    """
    Main chart builder entry point.
    Returns (plotly_fig, processed_data_df, error_string).
    """
    if df is None or df.empty:
        return None, None, "Dataset is empty or not loaded."

    builder = CHART_BUILDERS.get(chart_type)
    if not builder:
        return None, None, f"Unsupported chart type: {chart_type}"

    try:
        fig, data_df = builder(df, config, theme=theme)
        return fig, data_df, None
    except Exception as e:
        return None, None, f"Failed to build {chart_type} chart: {str(e)}"


# =============================================================================
# DETERMINISTIC SMART RECOMMENDATIONS ENGINE
# =============================================================================

BIZ_METRICS_REGEX = re.compile(
    r"(?:^|_)(?:sales|revenue|profit|price|cost|amount|mrr|arr|income|expense|total|spend|value|rating|score|salary|budget|margin|discount|quantity|volume)$",
    re.IGNORECASE
)

CATEGORIES_REGEX = re.compile(
    r"(?:^|_)(?:category|sub_category|status|region|segment|tier|plan|type|group|channel|country|state|city|department|division|role|industry|stage|brand)$",
    re.IGNORECASE
)

DATETIME_REGEX = re.compile(
    r"(?:^|_)(?:date|time|timestamp|datetime|year|month|day|created_at|period|quarter|order_date)$",
    re.IGNORECASE
)


def generate_chart_recommendations(df: pd.DataFrame, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Deterministically analyze dataset column types and business heuristics
    to provide 4-6 smart pre-configured chart recommendations.
    """
    if df is None or df.empty:
        return []

    col_types = get_dataset_column_types(df)
    numeric_cols = col_types["Numeric"]
    cat_cols = col_types["Categorical"] + col_types["Boolean"]
    dt_cols = col_types["Date/Time"]

    recommendations: List[Dict[str, Any]] = []

    def score_col(name: str, regex: re.Pattern) -> int:
        return 10 if bool(regex.search(name)) else 1

    ranked_num = sorted(numeric_cols, key=lambda c: score_col(c, BIZ_METRICS_REGEX), reverse=True)
    ranked_cat = sorted(cat_cols, key=lambda c: score_col(c, CATEGORIES_REGEX), reverse=True)
    ranked_dt = sorted(dt_cols, key=lambda c: score_col(c, DATETIME_REGEX), reverse=True)

    # 1. Recommendation: Time Trend (Date + Primary Numeric) -> Line Chart
    if ranked_dt and ranked_num:
        best_dt = ranked_dt[0]
        best_num = ranked_num[0]
        recommendations.append({
            "id": "rec_trend_line",
            "chart_type": "line",
            "title": f"{best_num} Trend over {best_dt}",
            "family": "Trends",
            "badge": "Trend Analysis",
            "description": f"Track temporal progression and seasonality of {best_num} across {best_dt}.",
            "config": {
                "x": best_dt,
                "y": best_num,
                "color": "(None)",
                "agg": "Sum",
                "show_markers": True,
                "title": f"Total {best_num} Trend over {best_dt}"
            }
        })

    # 2. Recommendation: Category Comparison (Primary Cat + Primary Numeric) -> Bar Chart
    if ranked_cat and ranked_num:
        best_cat = ranked_cat[0]
        best_num = ranked_num[0]
        recommendations.append({
            "id": "rec_category_bar",
            "chart_type": "bar",
            "title": f"{best_num} by {best_cat}",
            "family": "Comparison",
            "badge": "Top Comparison",
            "description": f"Compare total {best_num} breakdown across {best_cat} segments.",
            "config": {
                "x": best_cat,
                "y": best_num,
                "color": "(None)",
                "agg": "Sum",
                "sort": "value_desc",
                "top_n": 12,
                "title": f"{best_num} by {best_cat}"
            }
        })

    # 3. Recommendation: Composition / Share -> Donut Chart
    if ranked_cat and (ranked_num or len(ranked_cat) >= 1):
        target_cat = ranked_cat[1] if len(ranked_cat) > 1 else ranked_cat[0]
        target_num = ranked_num[0] if ranked_num else "(Count Records)"
        recommendations.append({
            "id": "rec_composition_donut",
            "chart_type": "donut",
            "title": f"{target_cat} Share Breakdown",
            "family": "Composition",
            "badge": "Share Composition",
            "description": f"Examine proportional distribution of {target_cat} across the dataset.",
            "config": {
                "x": target_cat,
                "y": target_num,
                "agg": "Sum" if target_num != "(Count Records)" else "Count",
                "top_n": 8,
                "title": f"Proportional {target_cat} Composition"
            }
        })

    # 4. Recommendation: Bivariate Correlation (Two Numerics) -> Scatter Plot
    if len(ranked_num) >= 2:
        num_x = ranked_num[1]
        num_y = ranked_num[0]
        color_dim = ranked_cat[0] if ranked_cat else "(None)"
        recommendations.append({
            "id": "rec_bivariate_scatter",
            "chart_type": "scatter",
            "title": f"{num_y} vs {num_x}",
            "family": "Relationships",
            "badge": "Correlation",
            "description": f"Identify correlations, clusters, and regression trends between {num_y} and {num_x}.",
            "config": {
                "x": num_x,
                "y": num_y,
                "color": color_dim,
                "show_trendline": True,
                "title": f"{num_y} vs {num_x} Correlation"
            }
        })

    # 5. Recommendation: Numeric Distribution -> Histogram
    if ranked_num:
        dist_num = ranked_num[0]
        recommendations.append({
            "id": "rec_distribution_hist",
            "chart_type": "histogram",
            "title": f"{dist_num} Distribution Profile",
            "family": "Distribution",
            "badge": "Distribution",
            "description": f"Evaluate data skewness, concentration, and spread for {dist_num}.",
            "config": {
                "x": dist_num,
                "color": "(None)",
                "nbins": 25,
                "marginal": "box",
                "title": f"Frequency Distribution of {dist_num}"
            }
        })

    # 6. Recommendation: Advanced Correlation Matrix (if >= 3 numerics) -> Heatmap
    if len(ranked_num) >= 3:
        recommendations.append({
            "id": "rec_corr_heatmap",
            "chart_type": "heatmap",
            "title": "Global Feature Correlation Matrix",
            "family": "Advanced",
            "badge": "Multi-Variable",
            "description": "Examine pairwise Pearson correlation coefficients across all numeric attributes.",
            "config": {
                "columns": ranked_num[:10],
                "method": "pearson",
                "title": "Feature Correlation Matrix (Pearson)"
            }
        })

    # Fallback if only categorical columns exist
    if not recommendations and ranked_cat:
        cat_single = ranked_cat[0]
        recommendations.append({
            "id": "rec_cat_count",
            "chart_type": "bar",
            "title": f"Record Counts by {cat_single}",
            "family": "Comparison",
            "badge": "Frequency",
            "description": f"Display frequency distribution of records across {cat_single}.",
            "config": {
                "x": cat_single,
                "y": "(Count Records)",
                "color": "(None)",
                "agg": "Count",
                "sort": "value_desc",
                "top_n": 15,
                "title": f"Record Count by {cat_single}"
            }
        })

    return recommendations[:6]


# =============================================================================
# DETERMINISTIC ANALYTICAL CHART INSIGHTS ENGINE
# =============================================================================

def generate_chart_insights(
    chart_type: str,
    df: pd.DataFrame,
    config: Dict[str, Any],
    data_df: Optional[pd.DataFrame] = None
) -> List[Dict[str, str]]:
    """
    Calculate deterministic, verifiable analytical observations directly
    from the active chart configuration and dataset.
    Returns a list of structured insight dicts: {"label": ..., "value": ..., "detail": ..., "type": ...}
    """
    if df is None or df.empty:
        return []

    insights: List[Dict[str, str]] = []

    try:
        # 1. Categorical Comparison Insights (Bar, Horizontal Bar, Grouped Bar, Pie, Donut)
        if chart_type in ["bar", "horizontal_bar", "grouped_bar", "pie", "donut"] and data_df is not None and not data_df.empty:
            numeric_cols_in_data = [c for c in data_df.columns if pd.api.types.is_numeric_dtype(data_df[c])]
            cat_cols_in_data = [c for c in data_df.columns if c not in numeric_cols_in_data]

            if numeric_cols_in_data and cat_cols_in_data:
                val_col = numeric_cols_in_data[0]
                dim_col = cat_cols_in_data[0]

                dim_summary = data_df.groupby(dim_col, observed=False)[val_col].sum().sort_values(ascending=False)
                total_val = float(dim_summary.sum())

                if not dim_summary.empty and total_val > 0:
                    top_cat = str(dim_summary.index[0])
                    top_val = float(dim_summary.iloc[0])
                    top_pct = (top_val / total_val) * 100

                    insights.append({
                        "label": "Dominant Category",
                        "value": top_cat,
                        "detail": f"Accounts for {top_val:,.2f} ({top_pct:.1f}% of total {val_col}).",
                        "type": "success"
                    })

                    if len(dim_summary) > 1:
                        lowest_cat = str(dim_summary.index[-1])
                        lowest_val = float(dim_summary.iloc[-1])
                        lowest_pct = (lowest_val / total_val) * 100

                        insights.append({
                            "label": "Lowest Category",
                            "value": lowest_cat,
                            "detail": f"Represents {lowest_val:,.2f} ({lowest_pct:.1f}% of total).",
                            "type": "neutral"
                        })

                    if len(dim_summary) >= 3:
                        top3_val = float(dim_summary.head(3).sum())
                        top3_pct = (top3_val / total_val) * 100
                        insights.append({
                            "label": "Top 3 Concentration",
                            "value": f"{top3_pct:.1f}%",
                            "detail": f"The top 3 categories comprise {top3_val:,.2f} of total value.",
                            "type": "info"
                        })

        # 2. Trend Analysis Insights (Line, Area)
        elif chart_type in ["line", "area"] and data_df is not None and not data_df.empty:
            numeric_cols_in_data = [c for c in data_df.columns if pd.api.types.is_numeric_dtype(data_df[c])]
            cat_cols_in_data = [c for c in data_df.columns if c not in numeric_cols_in_data]

            if numeric_cols_in_data and cat_cols_in_data:
                val_col = numeric_cols_in_data[0]
                dim_col = cat_cols_in_data[0]

                series = data_df[val_col].dropna()
                if len(series) >= 2:
                    start_val = float(series.iloc[0])
                    end_val = float(series.iloc[-1])
                    diff_pct = ((end_val - start_val) / abs(start_val) * 100) if start_val != 0 else 0.0

                    direction = "Upward Growth" if diff_pct > 2.0 else ("Downward Decline" if diff_pct < -2.0 else "Stable / Flat")
                    dir_type = "success" if diff_pct > 2.0 else ("warning" if diff_pct < -2.0 else "neutral")

                    insights.append({
                        "label": "Overall Trend Direction",
                        "value": f"{direction} ({diff_pct:+.1f}%)",
                        "detail": f"Moved from {start_val:,.2f} at start to {end_val:,.2f} at period end.",
                        "type": dir_type
                    })

                    max_idx = series.idxmax()
                    min_idx = series.idxmin()
                    peak_x = str(data_df.loc[max_idx, dim_col]) if max_idx in data_df.index else "Peak"
                    peak_val = float(series.loc[max_idx])
                    trough_x = str(data_df.loc[min_idx, dim_col]) if min_idx in data_df.index else "Trough"
                    trough_val = float(series.loc[min_idx])

                    insights.append({
                        "label": "Peak Point",
                        "value": f"{peak_val:,.2f}",
                        "detail": f"Highest recorded value occurred at {peak_x}.",
                        "type": "info"
                    })

                    insights.append({
                        "label": "Trough Point",
                        "value": f"{trough_val:,.2f}",
                        "detail": f"Lowest recorded value occurred at {trough_x}.",
                        "type": "neutral"
                    })

        # 3. Relationship Insights (Scatter, Bubble)
        elif chart_type in ["scatter", "bubble"]:
            x_col = config.get("x")
            y_col = config.get("y")
            if x_col and y_col and x_col in df.columns and y_col in df.columns:
                s_x = pd.to_numeric(df[x_col], errors="coerce")
                s_y = pd.to_numeric(df[y_col], errors="coerce")
                valid_mask = s_x.notna() & s_y.notna()
                if valid_mask.sum() >= 3:
                    clean_x = s_x[valid_mask]
                    clean_y = s_y[valid_mask]
                    r = float(clean_x.corr(clean_y))

                    if abs(r) >= 0.7:
                        strength = "Strong Positive" if r > 0 else "Strong Negative"
                        r_type = "success" if r > 0 else "warning"
                    elif abs(r) >= 0.4:
                        strength = "Moderate Positive" if r > 0 else "Moderate Negative"
                        r_type = "info"
                    elif abs(r) >= 0.15:
                        strength = "Weak Positive" if r > 0 else "Weak Negative"
                        r_type = "neutral"
                    else:
                        strength = "Negligible / Uncorrelated"
                        r_type = "neutral"

                    insights.append({
                        "label": "Pearson Correlation (r)",
                        "value": f"{r:+.3f}",
                        "detail": f"Exhibits a {strength.lower()} statistical relationship.",
                        "type": r_type
                    })

                    insights.append({
                        "label": "Sample Size",
                        "value": f"{len(clean_x):,} records",
                        "detail": f"Calculated across non-null paired observations.",
                        "type": "neutral"
                    })

        # 4. Distribution Insights (Histogram, Box, Violin)
        elif chart_type in ["histogram", "box", "violin"]:
            target_col = config.get("x") if chart_type == "histogram" else config.get("y")
            if target_col and target_col in df.columns:
                series = pd.to_numeric(df[target_col], errors="coerce").dropna()
                if len(series) >= 4:
                    mean_val = float(series.mean())
                    median_val = float(series.median())
                    std_val = float(series.std())
                    q25 = float(series.quantile(0.25))
                    q75 = float(series.quantile(0.75))
                    iqr = q75 - q25

                    lower_bound = q25 - 1.5 * iqr
                    upper_bound = q75 + 1.5 * iqr
                    outliers_count = int(((series < lower_bound) | (series > upper_bound)).sum())

                    skew = float(series.skew())
                    if skew > 1.0:
                        skew_desc = "Highly Right-Skewed (Long positive tail)"
                    elif skew > 0.5:
                        skew_desc = "Moderately Right-Skewed"
                    elif skew < -1.0:
                        skew_desc = "Highly Left-Skewed (Long negative tail)"
                    elif skew < -0.5:
                        skew_desc = "Moderately Left-Skewed"
                    else:
                        skew_desc = "Approximately Symmetric"

                    insights.append({
                        "label": "Distribution Symmetry",
                        "value": skew_desc,
                        "detail": f"Skewness score = {skew:.2f} (Mean = {mean_val:,.2f}, Median = {median_val:,.2f}).",
                        "type": "info"
                    })

                    insights.append({
                        "label": "Interquartile Range (IQR)",
                        "value": f"{iqr:,.2f}",
                        "detail": f"50% of records fall between {q25:,.2f} and {q75:,.2f}.",
                        "type": "neutral"
                    })

                    insights.append({
                        "label": "Statistical Outliers",
                        "value": f"{outliers_count} ({outliers_count/len(series)*100:.1f}%)",
                        "detail": f"Values falling outside 1.5×IQR boundary [{lower_bound:,.1f}, {upper_bound:,.1f}].",
                        "type": "warning" if outliers_count > 0 else "success"
                    })

        # 5. Correlation Heatmap Insights
        elif chart_type == "heatmap" and data_df is not None and not data_df.empty:
            corr_matrix = data_df.copy()
            pairs = []
            cols = list(corr_matrix.columns)
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    c1, c2 = cols[i], cols[j]
                    val = float(corr_matrix.loc[c1, c2])
                    if not np.isnan(val):
                        pairs.append((c1, c2, val))

            if pairs:
                pairs_sorted = sorted(pairs, key=lambda p: abs(p[2]), reverse=True)
                strongest = pairs_sorted[0]
                insights.append({
                    "label": "Strongest Correlation",
                    "value": f"r = {strongest[2]:+.2f}",
                    "detail": f"Between '{strongest[0]}' and '{strongest[1]}'.",
                    "type": "success" if strongest[2] > 0 else "warning"
                })

                pos_count = sum(1 for p in pairs if p[2] > 0.3)
                neg_count = sum(1 for p in pairs if p[2] < -0.3)
                insights.append({
                    "label": "Significant Pairs (|r| > 0.3)",
                    "value": f"{pos_count} Positive / {neg_count} Negative",
                    "detail": f"Out of {len(pairs)} total pairwise combinations evaluated.",
                    "type": "info"
                })

    except Exception:
        pass

    return insights


# =============================================================================
# EXPORT UTILITIES (PNG, Standalone HTML, Configuration JSON)
# =============================================================================

def export_chart_png(fig: go.Figure, width: int = 1200, height: int = 650, scale: int = 2) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Export Plotly chart as high-resolution PNG bytes using Kaleido.
    Returns (png_bytes, error_message).
    """
    if fig is None:
        return None, "No active chart figure to export."

    try:
        png_bytes = fig.to_image(format="png", width=width, height=height, scale=scale)
        return png_bytes, None
    except Exception as e:
        return None, f"PNG export failed: {str(e)}"


def export_chart_html(fig: go.Figure, title: str = "Data Studio Visualization") -> str:
    """
    Export standalone interactive Plotly HTML file string.
    Includes Plotly JS from CDN for lightweight export.
    """
    if fig is None:
        return "<html><body><p>No visualization available.</p></body></html>"

    try:
        html_str = fig.to_html(
            include_plotlyjs="cdn",
            full_html=True,
            default_width="100%",
            default_height="650px",
            config={"responsive": True, "displayModeBar": True}
        )
        return html_str
    except Exception as e:
        return f"<html><body><p>Error generating HTML: {str(e)}</p></body></html>"


def export_chart_config_json(config: Dict[str, Any], chart_type: str) -> str:
    """Export chart parameters configuration as formatted JSON string."""
    payload = {
        "app": "Data Studio v2",
        "module": "Visualization Studio",
        "chart_type": chart_type,
        "configuration": config
    }
    return json.dumps(payload, indent=2)

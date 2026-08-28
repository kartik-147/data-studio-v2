"""
DATA STUDIO v2 — Visualization Studio Analytics & Rendering Engine
=============================================================================
Modular, decoupled engine providing:
- 25 Supported Chart Types across 6 Families (Comparison, Trends, Relationships,
  Distribution, Composition, Advanced & KPIs)
- Dataset Schema & Chart Compatibility Profiling
- Robust Data Transformations & Multi-Dimensional Aggregations
- Design System-Aware Plotly Visualizations (Dark / Light themes & Custom Palettes)
- Deterministic Smart Recommendations Engine
- Deterministic Analytical Chart Insights Engine
- Multi-Format Chart Export (High-Res PNG, Interactive HTML, Config JSON)
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
# CHART TAXONOMY & SPECIFICATIONS (25 Chart Types across 6 Families)
# =============================================================================

CHART_FAMILIES: Dict[str, List[str]] = {
    "Comparison": ["bar", "horizontal_bar", "grouped_bar", "lollipop", "waterfall", "radar"],
    "Trends": ["line", "area", "stepline", "multi_line"],
    "Relationships": ["scatter", "bubble", "scatter_3d", "density_contour"],
    "Distribution": ["histogram", "box", "violin", "ecdf"],
    "Composition": ["pie", "donut", "treemap", "sunburst", "funnel"],
    "Advanced": ["heatmap", "gauge"]
}

CHART_METADATA: Dict[str, Dict[str, Any]] = {
    # ── 1. Comparison Family ────────────────────────────────────────────────
    "bar": {
        "name": "Column Bar Chart",
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
    "lollipop": {
        "name": "Lollipop Chart",
        "family": "Comparison",
        "icon": "bar-chart-3",
        "description": "Sleek, minimalist alternative to bar charts using thin stems and circular metric nodes.",
        "requires_x": True,
        "requires_y": False,
        "supports_color": True,
        "supports_agg": True,
        "supports_top_n": True
    },
    "waterfall": {
        "name": "Waterfall Chart",
        "family": "Comparison",
        "icon": "trending-up",
        "description": "Visualize sequential positive & negative variance contributions and cumulative totals.",
        "requires_x": True,
        "requires_y": True,
        "supports_agg": True,
        "supports_top_n": True
    },
    "radar": {
        "name": "Radar / Spider Chart",
        "family": "Comparison",
        "icon": "sparkles",
        "description": "Evaluate multi-attribute performance scores and multi-variate metrics across categories.",
        "requires_x": True,  # Dimension or Feature axis
        "requires_y": False,  # Metrics
        "supports_multi_metric": True,
        "supports_agg": True
    },

    # ── 2. Trends Family ────────────────────────────────────────────────────
    "line": {
        "name": "Line Chart",
        "family": "Trends",
        "icon": "trending-up",
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
    "stepline": {
        "name": "Step Line Chart",
        "family": "Trends",
        "icon": "trending-up",
        "description": "Show discrete stage transitions and step-wise rate changes across intervals.",
        "requires_x": True,
        "requires_y": True,
        "supports_color": True,
        "supports_agg": True
    },
    "multi_line": {
        "name": "Multi-Metric Trend",
        "family": "Trends",
        "icon": "trending-up",
        "description": "Compare multiple numeric metrics simultaneously across the same temporal axis.",
        "requires_x": True,
        "requires_multi_y": True,
        "supports_agg": True
    },

    # ── 3. Relationships Family ─────────────────────────────────────────────
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
    "scatter_3d": {
        "name": "3D Scatter Plot",
        "family": "Relationships",
        "icon": "sparkles",
        "description": "Interactive orbital 3D spatial visualization analyzing 3 numeric axes simultaneously.",
        "requires_x": True,
        "requires_y": True,
        "requires_z": True,
        "supports_color": True,
        "supports_size": True
    },
    "density_contour": {
        "name": "2D Density Contour",
        "family": "Relationships",
        "icon": "layers",
        "description": "Smooth bivariate density contour surfaces identifying high concentration clusters.",
        "requires_x": True,
        "requires_y": True,
        "supports_color": True
    },

    # ── 4. Distribution Family ──────────────────────────────────────────────
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
    "violin": {
        "name": "Violin Plot",
        "family": "Distribution",
        "icon": "layers",
        "description": "Combines box plot summary with kernel density distribution curves.",
        "requires_y": True,
        "supports_x": True,
        "supports_color": True
    },
    "ecdf": {
        "name": "Empirical CDF (ECDF)",
        "family": "Distribution",
        "icon": "trending-up",
        "description": "Empirical Cumulative Distribution Function showing percentile coverage from 0% to 100%.",
        "requires_x": True,
        "supports_color": True
    },

    # ── 5. Composition Family ───────────────────────────────────────────────
    "pie": {
        "name": "Pie Chart",
        "family": "Composition",
        "icon": "pie-chart",
        "description": "Display proportional breakdown and component shares of a whole.",
        "requires_x": True,  # Names/Labels
        "requires_y": False,  # Values (count or numeric sum)
        "supports_agg": True,
        "supports_top_n": True
    },
    "donut": {
        "name": "Donut Chart",
        "family": "Composition",
        "icon": "pie-chart",
        "description": "Modern ring chart with center total KPI showing categorical composition.",
        "requires_x": True,  # Names/Labels
        "requires_y": False,  # Values (count or numeric sum)
        "supports_agg": True,
        "supports_top_n": True
    },
    "treemap": {
        "name": "Treemap Hierarchy",
        "family": "Composition",
        "icon": "layout-dashboard",
        "description": "Nested rectangular tiles displaying proportional share and nested hierarchies.",
        "requires_x": True,  # Primary Category / Hierarchy Path
        "requires_y": False,
        "supports_color": True,
        "supports_agg": True
    },
    "sunburst": {
        "name": "Sunburst Chart",
        "family": "Composition",
        "icon": "pie-chart",
        "description": "Concentric radial multi-level rings displaying hierarchical structure.",
        "requires_x": True,  # Hierarchy Path
        "requires_y": False,
        "supports_agg": True
    },
    "funnel": {
        "name": "Funnel Chart",
        "family": "Composition",
        "icon": "filter",
        "description": "Conversion stage pipeline showing volume progressions and drop-off rates.",
        "requires_x": True,  # Stage Dimension
        "requires_y": False, # Values / Metric
        "supports_agg": True
    },

    # ── 6. Advanced & KPIs Family ───────────────────────────────────────────
    "heatmap": {
        "name": "Correlation Heatmap",
        "family": "Advanced",
        "icon": "layout-dashboard",
        "description": "Matrix of pairwise statistical correlation coefficients across numeric variables.",
        "requires_multi_numeric": True,
        "supports_method": True
    },
    "gauge": {
        "name": "KPI Gauge Dial",
        "family": "Advanced",
        "icon": "zap",
        "description": "Speedometer performance dial displaying current value against targets and warning thresholds.",
        "requires_y": True, # Metric to gauge
        "supports_agg": True
    }
}

AGGREGATION_OPTIONS = [
    "Sum",
    "Mean",
    "Median",
    "Count",
    "Minimum",
    "Maximum",
    "Standard Deviation"
]

SORT_OPTIONS = [
    ("value_desc", "Value: High to Low"),
    ("value_asc", "Value: Low to High"),
    ("alpha_asc", "Category: A to Z"),
    ("alpha_desc", "Category: Z to A"),
    ("default", "Default / Original Order")
]

COLOR_PALETTES: Dict[str, List[str]] = {
    "Classic SaaS": ["#2563eb", "#7c3aed", "#059669", "#d97706", "#db2777", "#0891b2", "#4f46e5", "#0d9488"],
    "Sapphire Modern": ["#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#1d4ed8", "#1e40af", "#38bdf8", "#0284c7"],
    "Emerald Energy": ["#059669", "#10b981", "#34d399", "#6ee7b7", "#047857", "#065f46", "#14b8a6", "#0d9488"],
    "Sunset Glow": ["#db2777", "#f59e0b", "#8b5cf6", "#ec4899", "#f97316", "#6366f1", "#ef4444", "#fbbf24"],
    "Cyber Neon": ["#06b6d4", "#8b5cf6", "#10b981", "#f43f5e", "#eab308", "#3b82f6", "#a855f7", "#14b8a6"],
    "Warm Autumn": ["#d97706", "#dc2626", "#ea580c", "#b45309", "#78350f", "#f59e0b", "#c2410c", "#9a3412"],
    "Titanium Steel": ["#475569", "#64748b", "#94a3b8", "#cbd5e1", "#334155", "#1e293b", "#0f172a", "#64748b"]
}


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
    y_title: Optional[str] = None,
    palette_name: Optional[str] = None
) -> go.Figure:
    """Apply consistent design system typography, colors, borders, and margins."""
    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
    palette = COLOR_PALETTES.get(palette_name, cfg["palette"])
    
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
        "colorway": palette
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

    # Standardize Cartesian Axes if applicable
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
    """Profile DataFrame columns into semantic lists."""
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
    """Check if a chart type is compatible with the current dataset columns."""
    if df is None or df.empty:
        return False, "No active dataset available."
        
    if col_types is None:
        col_types = get_dataset_column_types(df)
        
    num_cols = len(col_types["Numeric"])
    cat_cols = len(col_types["Categorical"]) + len(col_types["Boolean"]) + len(col_types["Text"])
    dt_cols = len(col_types["Date/Time"])
    total_cols = len(df.columns)

    if chart_type in ["bar", "horizontal_bar", "lollipop", "pie", "donut", "treemap", "sunburst", "funnel"]:
        if total_cols >= 1:
            return True, "Compatible"
        return False, "Requires at least 1 column."

    elif chart_type == "grouped_bar":
        if total_cols >= 2:
            return True, "Compatible"
        return False, "Requires at least 2 columns."

    elif chart_type == "waterfall":
        if num_cols >= 1 and total_cols >= 2:
            return True, "Compatible"
        return False, "Requires 1 dimension and 1 numeric metric."

    elif chart_type == "radar":
        if num_cols >= 2:
            return True, "Compatible"
        elif total_cols >= 2:
            return True, "Compatible"
        return False, "Requires multiple numeric columns or category + metric."

    elif chart_type in ["line", "area", "stepline"]:
        if num_cols >= 1 and total_cols >= 2:
            return True, "Compatible"
        elif num_cols >= 1:
            return True, "Compatible (using index)"
        return False, "Requires at least 1 numeric column."

    elif chart_type == "multi_line":
        if num_cols >= 2 and total_cols >= 2:
            return True, "Compatible"
        return False, "Requires at least 2 numeric metrics and 1 timeline column."

    elif chart_type == "scatter":
        if num_cols >= 2:
            return True, "Compatible"
        elif num_cols >= 1 and total_cols >= 2:
            return True, "Compatible"
        return False, "Requires at least 2 columns (numeric vs numeric/category)."

    elif chart_type == "bubble":
        if num_cols >= 2 and total_cols >= 3:
            return True, "Compatible"
        elif num_cols >= 2:
            return True, "Compatible"
        return False, "Requires at least 2 numeric columns + size attribute."

    elif chart_type == "scatter_3d":
        if num_cols >= 3:
            return True, "Compatible"
        elif num_cols >= 2 and total_cols >= 3:
            return True, "Compatible"
        return False, "Requires at least 3 columns (3 numeric axes recommended)."

    elif chart_type == "density_contour":
        if num_cols >= 2:
            return True, "Compatible"
        return False, "Requires at least 2 numeric columns to build density contours."

    elif chart_type in ["histogram", "box", "violin", "ecdf"]:
        if num_cols >= 1:
            return True, "Compatible"
        return False, "Requires at least 1 numeric column."

    elif chart_type == "heatmap":
        if num_cols >= 2:
            return True, "Compatible"
        return False, "Requires at least 2 numeric columns for pairwise correlation matrix."

    elif chart_type == "gauge":
        if num_cols >= 1:
            return True, "Compatible"
        return False, "Requires at least 1 numeric metric column."

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
    """Safely transform and aggregate data for chart rendering."""
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

    # Handle Record Count
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
            "Maximum": "max",
            "Standard Deviation": "std"
        }
        pd_func = agg_map.get(agg_func, "sum")

        clean_cols = group_keys + [val_col]
        clean_df = df[clean_cols].dropna().copy()
        clean_df[val_col] = pd.to_numeric(clean_df[val_col], errors="coerce")
        clean_df = clean_df.dropna(subset=[val_col])

        if group_keys:
            grouped = clean_df.groupby(group_keys, as_index=False, observed=False)[val_col].agg(pd_func)
            grouped.rename(columns={val_col: metric_col}, inplace=True)
            res_df = grouped
        else:
            agg_val = getattr(clean_df[val_col], pd_func)()
            res_df = pd.DataFrame({metric_col: [agg_val]})

    # Sorting logic
    if dim_col and dim_col in res_df.columns and metric_col in res_df.columns:
        if sort_by == "value_desc":
            res_df = res_df.sort_values(by=metric_col, ascending=False)
        elif sort_by == "value_asc":
            res_df = res_df.sort_values(by=metric_col, ascending=True)
        elif sort_by == "alpha_asc":
            res_df = res_df.sort_values(by=dim_col, ascending=True)
        elif sort_by == "alpha_desc":
            res_df = res_df.sort_values(by=dim_col, ascending=False)

    # Top N Filtering
    if top_n and top_n > 0 and dim_col and dim_col in res_df.columns:
        top_dims = res_df[dim_col].drop_duplicates().head(top_n)
        res_df = res_df[res_df[dim_col].isin(top_dims)]

    eff_x = metric_col if is_horizontal else (dim_col or metric_col)
    eff_y = (dim_col or metric_col) if is_horizontal else metric_col

    return res_df, eff_x, eff_y


# =============================================================================
# 25 INDIVIDUAL CHART GENERATOR IMPLEMENTATIONS
# =============================================================================

# ── 1. COMPARISON FAMILY ─────────────────────────────────────────────────────

def generate_bar_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate vertical bar / column chart."""
    x_col = config.get("x")
    y_col = config.get("y")
    color_col = config.get("color")
    agg_func = config.get("agg", "Sum")
    sort_by = config.get("sort", "value_desc")
    top_n = config.get("top_n", 15)
    palette = config.get("palette", "Classic SaaS")
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
        text_auto=".2s" if len(agg_df) <= 20 else False
    )
    fig.update_traces(
        marker_line_width=0,
        opacity=0.92,
        hovertemplate="<b>%{x}</b><br>" + f"{eff_y}: %{{y:,.2f}}<extra></extra>"
    )
    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=bool(color_arg), x_title=str(eff_x), y_title=str(eff_y), palette_name=palette
    )
    return fig, agg_df


def generate_horizontal_bar_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate horizontal bar leaderboard chart."""
    y_col = config.get("y")
    x_col = config.get("x")
    color_col = config.get("color")
    agg_func = config.get("agg", "Sum")
    sort_by = config.get("sort", "value_asc")  # asc shows highest bar at top in horizontal
    top_n = config.get("top_n", 15)
    palette = config.get("palette", "Classic SaaS")
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
        show_legend=bool(color_arg), x_title=str(eff_x), y_title=str(eff_y), palette_name=palette
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
    palette = config.get("palette", "Classic SaaS")
    title = config.get("title", f"{agg_func} of {y_col or 'Records'} by {x_col} & {color_col}")
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
        show_legend=True, x_title=str(eff_x), y_title=str(eff_y), palette_name=palette
    )
    return fig, agg_df


def generate_lollipop_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate modern lollipop chart (thin stems + circular dots)."""
    x_col = config.get("x")
    y_col = config.get("y")
    agg_func = config.get("agg", "Sum")
    sort_by = config.get("sort", "value_desc")
    top_n = config.get("top_n", 15)
    palette = config.get("palette", "Classic SaaS")
    title = config.get("title", f"Lollipop Ranking: {agg_func} of {y_col or 'Records'} by {x_col}")
    height = config.get("height", 460)

    agg_df, eff_x, eff_y = aggregate_data(
        df, x_col=x_col, y_col=y_col, agg_func=agg_func,
        sort_by=sort_by, top_n=top_n, orientation="vertical"
    )

    if agg_df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), agg_df

    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
    pal = COLOR_PALETTES.get(palette, cfg["palette"])
    dot_color = pal[0]
    stem_color = pal[1] if len(pal) > 1 else cfg["grid"]

    fig = go.Figure()

    # Add vertical line stems
    for _, row in agg_df.iterrows():
        fig.add_shape(
            type="line",
            x0=row[eff_x], y0=0,
            x1=row[eff_x], y1=row[eff_y],
            line=dict(color=stem_color, width=2.5)
        )

    # Add circle markers
    fig.add_trace(
        go.Scatter(
            x=agg_df[eff_x],
            y=agg_df[eff_y],
            mode="markers",
            marker=dict(size=12, color=dot_color, line=dict(color=cfg["text"], width=1.5)),
            hovertemplate="<b>%{x}</b><br>" + f"{eff_y}: %{{y:,.2f}}<extra></extra>"
        )
    )

    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=False, x_title=str(eff_x), y_title=str(eff_y), palette_name=palette
    )
    return fig, agg_df


def generate_waterfall_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate financial / variance waterfall chart."""
    x_col = config.get("x")
    y_col = config.get("y")
    agg_func = config.get("agg", "Sum")
    top_n = config.get("top_n", 10)
    palette = config.get("palette", "Classic SaaS")
    title = config.get("title", f"Waterfall Variance: {agg_func} of {y_col} across {x_col}")
    height = config.get("height", 460)

    agg_df, eff_x, eff_y = aggregate_data(
        df, x_col=x_col, y_col=y_col, agg_func=agg_func,
        sort_by="default", top_n=top_n, orientation="vertical"
    )

    if agg_df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), agg_df

    x_vals = list(agg_df[eff_x]) + ["Net Total"]
    y_vals = list(agg_df[eff_y]) + [0]
    measures = ["relative"] * len(agg_df) + ["total"]

    fig = go.Figure(
        go.Waterfall(
            name="Variance",
            orientation="v",
            measure=measures,
            x=x_vals,
            y=y_vals,
            textposition="outside",
            text=[f"{v:,.1f}" for v in agg_df[eff_y]] + ["Total"],
            connector={"line": {"color": "#94a3b8", "width": 1.5, "dash": "dot"}},
            decreasing={"marker": {"color": "#ef4444"}},
            increasing={"marker": {"color": "#10b981"}},
            totals={"marker": {"color": "#3b82f6"}}
        )
    )

    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=False, x_title=str(eff_x), y_title=str(eff_y), palette_name=palette
    )
    return fig, agg_df


def generate_radar_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate multi-attribute radar / spider web chart."""
    x_col = config.get("x")
    metrics = config.get("metrics")
    agg_func = config.get("agg", "Mean")
    palette = config.get("palette", "Classic SaaS")
    title = config.get("title", f"Radar Feature Profile ({agg_func})")
    height = config.get("height", 480)

    col_types = get_dataset_column_types(df)
    numeric_cols = col_types["Numeric"]

    if not metrics or not isinstance(metrics, list):
        metrics = numeric_cols[:6]

    valid_metrics = [m for m in metrics if m in numeric_cols]
    if len(valid_metrics) < 3:
        valid_metrics = numeric_cols[:5]

    if len(valid_metrics) < 3:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), pd.DataFrame()

    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
    pal = COLOR_PALETTES.get(palette, cfg["palette"])

    fig = go.Figure()

    if x_col and x_col in df.columns and x_col not in valid_metrics:
        # Multiple category slices
        top_cats = df[x_col].value_counts().head(4).index
        agg_map = {"Sum": "sum", "Mean": "mean", "Median": "median", "Maximum": "max", "Minimum": "min"}
        p_func = agg_map.get(agg_func, "mean")
        grouped = df[df[x_col].isin(top_cats)].groupby(x_col, as_index=False, observed=False)[valid_metrics].agg(p_func)

        for i, row in grouped.iterrows():
            r_vals = [row[m] for m in valid_metrics]
            r_vals.append(r_vals[0])  # Close polygon
            theta_vals = valid_metrics + [valid_metrics[0]]
            cat_name = str(row[x_col])
            color = pal[i % len(pal)]

            fig.add_trace(
                go.Scatterpolar(
                    r=r_vals,
                    theta=theta_vals,
                    fill="toself",
                    name=cat_name,
                    line=dict(color=color, width=2),
                    opacity=0.65
                )
            )
        ret_df = grouped
    else:
        # Overall dataset single profile
        agg_map = {"Sum": "sum", "Mean": "mean", "Median": "median", "Maximum": "max", "Minimum": "min"}
        p_func = agg_map.get(agg_func, "mean")
        agg_vals = getattr(df[valid_metrics], p_func)().to_dict()
        r_vals = [agg_vals[m] for m in valid_metrics]
        r_vals.append(r_vals[0])
        theta_vals = valid_metrics + [valid_metrics[0]]

        fig.add_trace(
            go.Scatterpolar(
                r=r_vals,
                theta=theta_vals,
                fill="toself",
                name="Aggregate Profile",
                line=dict(color=pal[0], width=2.5),
                opacity=0.7
            )
        )
        ret_df = pd.DataFrame([agg_vals])

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, showline=True, gridcolor=cfg["grid"], tickfont=dict(color=cfg["subtext"], size=10)),
            angularaxis=dict(gridcolor=cfg["grid"], tickfont=dict(color=cfg["text"], size=11))
        )
    )

    apply_chart_theme(fig, theme=theme, title=title, height=height, show_legend=True, palette_name=palette)
    return fig, ret_df


# ── 2. TRENDS FAMILY ─────────────────────────────────────────────────────────

def generate_line_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate continuous trend line chart."""
    x_col = config.get("x")
    y_col = config.get("y")
    color_col = config.get("color")
    agg_func = config.get("agg", "Sum")
    show_markers = config.get("show_markers", True)
    palette = config.get("palette", "Classic SaaS")
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
        show_legend=bool(color_arg), x_title=str(eff_x), y_title=str(eff_y), palette_name=palette
    )
    return fig, agg_df


def generate_area_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate volume and cumulative trend area chart."""
    x_col = config.get("x")
    y_col = config.get("y")
    color_col = config.get("color")
    agg_func = config.get("agg", "Sum")
    palette = config.get("palette", "Classic SaaS")
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
        show_legend=bool(color_arg), x_title=str(eff_x), y_title=str(eff_y), palette_name=palette
    )
    return fig, agg_df


def generate_stepline_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate discrete step line chart."""
    x_col = config.get("x")
    y_col = config.get("y")
    color_col = config.get("color")
    agg_func = config.get("agg", "Sum")
    palette = config.get("palette", "Classic SaaS")
    title = config.get("title", f"Step Transition: {agg_func} of {y_col} across {x_col}")
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
        line_shape="hv",
        markers=True
    )
    fig.update_traces(
        line=dict(width=2.5),
        marker=dict(size=6),
        hovertemplate="<b>%{x}</b><br>" + f"{eff_y}: %{{y:,.2f}}<extra></extra>"
    )
    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=bool(color_arg), x_title=str(eff_x), y_title=str(eff_y), palette_name=palette
    )
    return fig, agg_df


def generate_multi_line_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate comparison chart of multiple numeric metrics over the same timeline."""
    x_col = config.get("x")
    metrics = config.get("metrics")
    agg_func = config.get("agg", "Sum")
    palette = config.get("palette", "Classic SaaS")
    title = config.get("title", f"Multi-Metric Trend Comparison over {x_col}")
    height = config.get("height", 460)

    col_types = get_dataset_column_types(df)
    numeric_cols = col_types["Numeric"]

    if not metrics or not isinstance(metrics, list):
        metrics = numeric_cols[:3]

    valid_metrics = [m for m in metrics if m in numeric_cols]
    if not valid_metrics or not x_col or x_col not in df.columns:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), pd.DataFrame()

    agg_map = {"Sum": "sum", "Mean": "mean", "Median": "median", "Maximum": "max", "Minimum": "min"}
    p_func = agg_map.get(agg_func, "sum")

    clean_cols = [x_col] + valid_metrics
    clean_df = df[clean_cols].dropna(subset=[x_col]).copy()
    for m in valid_metrics:
        clean_df[m] = pd.to_numeric(clean_df[m], errors="coerce")

    grouped = clean_df.groupby(x_col, as_index=False, observed=False)[valid_metrics].agg(p_func)
    grouped = grouped.sort_values(by=x_col, ascending=True)

    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
    pal = COLOR_PALETTES.get(palette, cfg["palette"])

    fig = go.Figure()
    for i, m in enumerate(valid_metrics):
        fig.add_trace(
            go.Scatter(
                x=grouped[x_col],
                y=grouped[m],
                mode="lines+markers",
                name=m,
                line=dict(width=2.5, color=pal[i % len(pal)]),
                marker=dict(size=5),
                hovertemplate=f"<b>{m}</b>: %{{y:,.2f}}<br>Date: %{{x}}<extra></extra>"
            )
        )

    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=True, x_title=str(x_col), y_title=f"{agg_func} Magnitude", palette_name=palette
    )
    return fig, grouped


# ── 3. RELATIONSHIPS FAMILY ──────────────────────────────────────────────────

def generate_scatter_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate 2D scatter plot with optional regression trendline."""
    x_col = config.get("x")
    y_col = config.get("y")
    color_col = config.get("color")
    size_col = config.get("size")
    show_trendline = config.get("show_trendline", False)
    palette = config.get("palette", "Classic SaaS")
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
        show_legend=bool(color_arg), x_title=str(x_col), y_title=str(y_col), palette_name=palette
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


def generate_scatter_3d(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate interactive 3D XYZ spatial scatter plot."""
    x_col = config.get("x")
    y_col = config.get("y")
    z_col = config.get("z")
    color_col = config.get("color")
    size_col = config.get("size")
    palette = config.get("palette", "Classic SaaS")
    title = config.get("title", f"3D Relationship: {x_col} × {y_col} × {z_col}")
    height = config.get("height", 500)

    col_types = get_dataset_column_types(df)
    numeric_cols = col_types["Numeric"]

    if not z_col or z_col not in df.columns:
        remaining_nums = [c for c in numeric_cols if c not in [x_col, y_col]]
        z_col = remaining_nums[0] if remaining_nums else (numeric_cols[0] if numeric_cols else None)

    if not x_col or not y_col or not z_col:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), pd.DataFrame()

    subset_cols = [x_col, y_col, z_col]
    color_arg = color_col if (color_col and color_col != "(None)") else None
    if color_arg:
        subset_cols.append(color_arg)
    size_arg = size_col if (size_col and size_col != "(None)") else None
    if size_arg:
        subset_cols.append(size_arg)

    clean_df = df[subset_cols].dropna().copy()
    for col in [x_col, y_col, z_col]:
        clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce")
    clean_df = clean_df.dropna(subset=[x_col, y_col, z_col])

    if size_arg:
        clean_df[size_arg] = pd.to_numeric(clean_df[size_arg], errors="coerce").fillna(1)
        clean_df[size_arg] = np.maximum(clean_df[size_arg], 0.1)

    if clean_df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), clean_df

    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
    fig = px.scatter_3d(
        clean_df,
        x=x_col,
        y=y_col,
        z=z_col,
        color=color_arg,
        size=size_arg,
        opacity=0.85
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(gridcolor=cfg["grid"], backgroundcolor=cfg["plot_bg"], title=x_col),
            yaxis=dict(gridcolor=cfg["grid"], backgroundcolor=cfg["plot_bg"], title=y_col),
            zaxis=dict(gridcolor=cfg["grid"], backgroundcolor=cfg["plot_bg"], title=z_col),
        )
    )
    apply_chart_theme(fig, theme=theme, title=title, height=height, show_legend=bool(color_arg), palette_name=palette)
    return fig, clean_df


def generate_density_contour(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate 2D smooth density contour map."""
    x_col = config.get("x")
    y_col = config.get("y")
    color_col = config.get("color")
    palette = config.get("palette", "Classic SaaS")
    title = config.get("title", f"2D Density Contours: {y_col} vs {x_col}")
    height = config.get("height", 460)

    if not x_col or not y_col or df is None or df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), pd.DataFrame()

    subset_cols = [x_col, y_col]
    color_arg = color_col if (color_col and color_col != "(None)") else None
    if color_arg:
        subset_cols.append(color_arg)

    clean_df = df[subset_cols].dropna().copy()
    clean_df[x_col] = pd.to_numeric(clean_df[x_col], errors="coerce")
    clean_df[y_col] = pd.to_numeric(clean_df[y_col], errors="coerce")
    clean_df = clean_df.dropna(subset=[x_col, y_col])

    if clean_df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), clean_df

    fig = px.density_contour(
        clean_df,
        x=x_col,
        y=y_col,
        color=color_arg,
        marginal_x="histogram",
        marginal_y="histogram"
    )
    fig.update_traces(selector=dict(type="histogram2dcontour"), contours_coloring="fill", opacity=0.75)
    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=bool(color_arg), x_title=str(x_col), y_title=str(y_col), palette_name=palette
    )
    return fig, clean_df


# ── 4. DISTRIBUTION FAMILY ───────────────────────────────────────────────────

def generate_histogram_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate distribution histogram with customizable bin count and marginals."""
    x_col = config.get("x")
    color_col = config.get("color")
    nbins = config.get("nbins", 30)
    marginal = config.get("marginal", "box")
    palette = config.get("palette", "Classic SaaS")
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
    fig.update_traces(marker_line_width=0.5, marker_line_color="#1e293b")
    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=bool(color_arg), x_title=str(x_col), y_title="Frequency Count", palette_name=palette
    )
    return fig, clean_df


def generate_box_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate statistical box plot with quartile markers and outlier points."""
    y_col = config.get("y")
    x_col = config.get("x")
    color_col = config.get("color")
    points = config.get("points", "outliers")
    palette = config.get("palette", "Classic SaaS")
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
    fig.update_traces(marker=dict(size=4, opacity=0.7), boxmean=True)
    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=bool(color_arg and color_arg != x_arg),
        x_title=str(x_arg) if x_arg else None,
        y_title=str(y_col), palette_name=palette
    )
    return fig, clean_df


def generate_violin_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate distribution violin plot with embedded box markers."""
    y_col = config.get("y")
    x_col = config.get("x")
    color_col = config.get("color")
    show_box = config.get("show_box", True)
    points = config.get("points", "outliers")
    palette = config.get("palette", "Classic SaaS")
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
    fig.update_traces(opacity=0.85, marker=dict(size=4))
    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=bool(color_arg and color_arg != x_arg),
        x_title=str(x_arg) if x_arg else None,
        y_title=str(y_col), palette_name=palette
    )
    return fig, clean_df


def generate_ecdf_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate Empirical Cumulative Distribution Function (ECDF) plot."""
    x_col = config.get("x")
    color_col = config.get("color")
    palette = config.get("palette", "Classic SaaS")
    title = config.get("title", f"Cumulative Probability Distribution of {x_col}")
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

    fig = px.ecdf(
        clean_df,
        x=x_col,
        color=color_arg,
        markers=True,
        marginal="rug"
    )
    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=bool(color_arg), x_title=str(x_col), y_title="Cumulative Probability (0 to 1)", palette_name=palette
    )
    return fig, clean_df


# ── 5. COMPOSITION FAMILY ────────────────────────────────────────────────────

def generate_pie_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate proportional pie chart with top-slice limiting."""
    names_col = config.get("x")
    values_col = config.get("y")
    agg_func = config.get("agg", "Sum")
    top_n = config.get("top_n", 8)
    palette = config.get("palette", "Classic SaaS")
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
    pal = COLOR_PALETTES.get(palette, cfg["palette"])

    fig = go.Figure(
        data=[
            go.Pie(
                labels=agg_df[eff_names],
                values=agg_df[eff_vals],
                hole=0.0,
                textinfo="label+percent",
                textposition="inside",
                insidetextorientation="radial",
                marker=dict(colors=pal * 4, line=dict(color=cfg["paper_bg"], width=1.5)),
                hovertemplate="<b>%{label}</b><br>" + f"{eff_vals}: %{{value:,.2f}}<br>Share: %{{percent}}<extra></extra>"
            )
        ]
    )
    apply_chart_theme(fig, theme=theme, title=title, height=height, show_legend=True, palette_name=palette)
    return fig, agg_df


def generate_donut_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate sleek donut chart with center KPI total."""
    names_col = config.get("x")
    values_col = config.get("y")
    agg_func = config.get("agg", "Sum")
    top_n = config.get("top_n", 8)
    palette = config.get("palette", "Classic SaaS")
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
    pal = COLOR_PALETTES.get(palette, cfg["palette"])
    total_metric = agg_df[eff_vals].sum()

    if total_metric >= 1_000_000:
        center_text = f"{total_metric/1_000_000:.1f}M"
    elif total_metric >= 1_000:
        center_text = f"{total_metric/1_000:.1f}K"
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
                marker=dict(colors=pal * 4, line=dict(color=cfg["paper_bg"], width=2)),
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
    apply_chart_theme(fig, theme=theme, title=title, height=height, show_legend=True, palette_name=palette)
    return fig, agg_df


def generate_treemap_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate hierarchical nested treemap."""
    x_col = config.get("x")
    sub_cat = config.get("sub_category")
    y_col = config.get("y")
    agg_func = config.get("agg", "Sum")
    palette = config.get("palette", "Classic SaaS")
    title = config.get("title", f"Treemap Hierarchy: {y_col or 'Records'} by {x_col}")
    height = config.get("height", 480)

    if df is None or df.empty or not x_col or x_col not in df.columns:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), pd.DataFrame()

    path_cols = [x_col]
    if sub_cat and sub_cat != "(None)" and sub_cat in df.columns and sub_cat != x_col:
        path_cols.append(sub_cat)

    if y_col and y_col != "(Count Records)" and y_col in df.columns:
        agg_map = {"Sum": "sum", "Mean": "mean", "Median": "median", "Maximum": "max", "Minimum": "min"}
        p_func = agg_map.get(agg_func, "sum")
        clean_df = df[path_cols + [y_col]].dropna().copy()
        clean_df[y_col] = pd.to_numeric(clean_df[y_col], errors="coerce").fillna(0)
        grouped = clean_df.groupby(path_cols, as_index=False, observed=False)[y_col].agg(p_func)
        metric_col = y_col
    else:
        clean_df = df[path_cols].dropna().copy()
        grouped = clean_df.groupby(path_cols, as_index=False, observed=False).size()
        grouped.rename(columns={"size": "Record Count"}, inplace=True)
        metric_col = "Record Count"

    fig = px.treemap(
        grouped,
        path=path_cols,
        values=metric_col,
        color=path_cols[0]
    )
    fig.update_traces(
        marker=dict(cornerradius=4),
        hovertemplate="<b>%{label}</b><br>" + f"{metric_col}: %{{value:,.2f}}<br>Parent: %{{parent}}<extra></extra>"
    )
    apply_chart_theme(fig, theme=theme, title=title, height=height, show_legend=False, palette_name=palette)
    return fig, grouped


def generate_sunburst_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate concentric sunburst chart."""
    x_col = config.get("x")
    sub_cat = config.get("sub_category")
    y_col = config.get("y")
    agg_func = config.get("agg", "Sum")
    palette = config.get("palette", "Classic SaaS")
    title = config.get("title", f"Sunburst Breakdown: {y_col or 'Records'} across {x_col}")
    height = config.get("height", 480)

    if df is None or df.empty or not x_col or x_col not in df.columns:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), pd.DataFrame()

    path_cols = [x_col]
    if sub_cat and sub_cat != "(None)" and sub_cat in df.columns and sub_cat != x_col:
        path_cols.append(sub_cat)

    if y_col and y_col != "(Count Records)" and y_col in df.columns:
        agg_map = {"Sum": "sum", "Mean": "mean", "Median": "median", "Maximum": "max", "Minimum": "min"}
        p_func = agg_map.get(agg_func, "sum")
        clean_df = df[path_cols + [y_col]].dropna().copy()
        clean_df[y_col] = pd.to_numeric(clean_df[y_col], errors="coerce").fillna(0)
        grouped = clean_df.groupby(path_cols, as_index=False, observed=False)[y_col].agg(p_func)
        metric_col = y_col
    else:
        clean_df = df[path_cols].dropna().copy()
        grouped = clean_df.groupby(path_cols, as_index=False, observed=False).size()
        grouped.rename(columns={"size": "Record Count"}, inplace=True)
        metric_col = "Record Count"

    fig = px.sunburst(
        grouped,
        path=path_cols,
        values=metric_col,
        color=path_cols[0]
    )
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>" + f"{metric_col}: %{{value:,.2f}}<br>Share of parent: %{{percentParent:.1%}}<extra></extra>"
    )
    apply_chart_theme(fig, theme=theme, title=title, height=height, show_legend=False, palette_name=palette)
    return fig, grouped


def generate_funnel_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate pipeline / stage funnel chart."""
    x_col = config.get("x")  # Stage dimension
    y_col = config.get("y")  # Metric
    agg_func = config.get("agg", "Sum")
    top_n = config.get("top_n", 8)
    palette = config.get("palette", "Classic SaaS")
    title = config.get("title", f"Conversion Funnel: {y_col or 'Volume'} across {x_col}")
    height = config.get("height", 460)

    agg_df, eff_x, eff_y = aggregate_data(
        df, x_col=x_col, y_col=y_col, agg_func=agg_func,
        sort_by="value_desc", top_n=top_n, orientation="vertical"
    )

    if agg_df.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), agg_df

    fig = px.funnel(
        agg_df,
        x=eff_y,
        y=eff_x
    )
    fig.update_traces(
        opacity=0.9,
        textinfo="value+percent initial",
        hovertemplate="<b>%{y}</b><br>Stage Volume: %{x:,.2f}<br>Conversion: %{percentInitial:.1%}<extra></extra>"
    )
    apply_chart_theme(
        fig, theme=theme, title=title, height=height,
        show_legend=False, x_title=f"{eff_y} Volume", y_title="Funnel Stages", palette_name=palette
    )
    return fig, agg_df


# ── 6. ADVANCED & KPIS FAMILY ────────────────────────────────────────────────

def generate_correlation_heatmap(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate pairwise correlation heatmap matrix with annotated coefficients."""
    selected_cols = config.get("columns")
    method = config.get("method", "pearson")
    title = config.get("title", f"Pairwise Feature Correlation Matrix ({method.capitalize()})")
    height = config.get("height", 480)

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


def generate_gauge_chart(df: pd.DataFrame, config: Dict[str, Any], theme: str = "Dark") -> Tuple[go.Figure, pd.DataFrame]:
    """Generate KPI performance speedometer / gauge dial."""
    y_col = config.get("y")
    agg_func = config.get("agg", "Mean")
    palette = config.get("palette", "Classic SaaS")
    title = config.get("title", f"KPI Gauge: {agg_func} of {y_col}")
    height = config.get("height", 420)

    if df is None or df.empty or not y_col or y_col not in df.columns:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), pd.DataFrame()

    series = pd.to_numeric(df[y_col], errors="coerce").dropna()
    if series.empty:
        fig = go.Figure()
        return apply_chart_theme(fig, theme=theme, title=title, height=height), pd.DataFrame()

    agg_map = {"Sum": series.sum(), "Mean": series.mean(), "Median": series.median(), "Maximum": series.max(), "Minimum": series.min()}
    val = float(agg_map.get(agg_func, series.mean()))
    min_v = float(series.min())
    max_v = float(series.max()) if series.max() > min_v else min_v + 100.0
    target_v = float(val * 1.15) if val > 0 else 100.0

    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
    pal = COLOR_PALETTES.get(palette, cfg["palette"])
    primary_color = pal[0]

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=val,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": f"<b>{y_col}</b><br><span style='font-size:12px;color:{cfg['subtext']};'>{agg_func} Metric</span>"},
            delta={"reference": target_v, "increasing": {"color": "#10b981"}, "decreasing": {"color": "#ef4444"}},
            gauge={
                "axis": {"range": [min_v, max_v * 1.1], "tickcolor": cfg["subtext"]},
                "bar": {"color": primary_color, "thickness": 0.3},
                "bgcolor": cfg["plot_bg"],
                "borderwidth": 1,
                "bordercolor": cfg["grid"],
                "steps": [
                    {"range": [min_v, (min_v + max_v) / 2], "color": "rgba(239, 68, 68, 0.15)"},
                    {"range": [(min_v + max_v) / 2, max_v * 0.85], "color": "rgba(245, 158, 11, 0.15)"},
                    {"range": [max_v * 0.85, max_v * 1.1], "color": "rgba(16, 185, 129, 0.15)"}
                ],
                "threshold": {
                    "line": {"color": "#ef4444", "width": 3},
                    "thickness": 0.75,
                    "value": target_v
                }
            }
        )
    )

    data_df = pd.DataFrame([{"Metric": y_col, "Aggregation": agg_func, "Value": val, "Target": target_v, "Min": min_v, "Max": max_v}])
    apply_chart_theme(fig, theme=theme, title=title, height=height, show_legend=False, palette_name=palette)
    return fig, data_df


# =============================================================================
# CHART BUILDERS DISPATCHER MAP
# =============================================================================

CHART_BUILDERS = {
    # Comparison
    "bar": generate_bar_chart,
    "horizontal_bar": generate_horizontal_bar_chart,
    "grouped_bar": generate_grouped_bar_chart,
    "lollipop": generate_lollipop_chart,
    "waterfall": generate_waterfall_chart,
    "radar": generate_radar_chart,

    # Trends
    "line": generate_line_chart,
    "area": generate_area_chart,
    "stepline": generate_stepline_chart,
    "multi_line": generate_multi_line_chart,

    # Relationships
    "scatter": generate_scatter_chart,
    "bubble": generate_bubble_chart,
    "scatter_3d": generate_scatter_3d,
    "density_contour": generate_density_contour,

    # Distribution
    "histogram": generate_histogram_chart,
    "box": generate_box_chart,
    "violin": generate_violin_chart,
    "ecdf": generate_ecdf_chart,

    # Composition
    "pie": generate_pie_chart,
    "donut": generate_donut_chart,
    "treemap": generate_treemap_chart,
    "sunburst": generate_sunburst_chart,
    "funnel": generate_funnel_chart,

    # Advanced & KPIs
    "heatmap": generate_correlation_heatmap,
    "gauge": generate_gauge_chart
}


def build_chart(
    chart_type: str,
    df: pd.DataFrame,
    config: Dict[str, Any],
    theme: str = "Dark"
) -> Tuple[Optional[go.Figure], Optional[pd.DataFrame], Optional[str]]:
    """Main chart builder entry point. Returns (plotly_fig, processed_data_df, error_string)."""
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
    """Deterministically analyze dataset column types and provide smart chart recommendations."""
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

    # 1. Recommendation: Time Trend (Date + Numeric) -> Line Chart
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

    # 2. Recommendation: Category Comparison -> Horizontal Lollipop or Column Bar
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

    # 3. Recommendation: Proportional Composition -> Donut or Treemap
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

    # 4. Recommendation: Treemap Hierarchy (if >= 2 categories)
    if len(ranked_cat) >= 2 and ranked_num:
        recommendations.append({
            "id": "rec_treemap_hierarchy",
            "chart_type": "treemap",
            "title": f"Hierarchical Breakdown: {ranked_cat[0]} & {ranked_cat[1]}",
            "family": "Composition",
            "badge": "Hierarchy",
            "description": f"Visualize proportional size of {ranked_num[0]} nested within {ranked_cat[0]} and {ranked_cat[1]}.",
            "config": {
                "x": ranked_cat[0],
                "sub_category": ranked_cat[1],
                "y": ranked_num[0],
                "agg": "Sum",
                "title": f"{ranked_num[0]} Treemap Breakdown"
            }
        })

    # 5. Recommendation: Bivariate Correlation (Two Numerics) -> Scatter Plot
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

    # 6. Recommendation: Numeric Distribution Profile -> Histogram
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

    # 7. Recommendation: Global Feature Correlation Matrix (if >= 3 numerics) -> Heatmap
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
    """Calculate deterministic, verifiable analytical observations directly from active chart."""
    if df is None or df.empty:
        return []

    insights: List[Dict[str, str]] = []

    try:
        # 1. Categorical Comparison Insights (Bar, Horizontal Bar, Grouped Bar, Lollipop, Pie, Donut, Treemap, Funnel)
        if chart_type in ["bar", "horizontal_bar", "grouped_bar", "lollipop", "pie", "donut", "treemap", "sunburst", "funnel"] and data_df is not None and not data_df.empty:
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
                        "label": "Dominant Segment",
                        "value": top_cat,
                        "detail": f"Accounts for {top_val:,.2f} ({top_pct:.1f}% of total {val_col}).",
                        "type": "success"
                    })

                    if len(dim_summary) > 1:
                        lowest_cat = str(dim_summary.index[-1])
                        lowest_val = float(dim_summary.iloc[-1])
                        lowest_pct = (lowest_val / total_val) * 100

                        insights.append({
                            "label": "Lowest Segment",
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
                            "detail": f"The top 3 segments comprise {top3_val:,.2f} of total magnitude.",
                            "type": "info"
                        })

        # 2. Trend Analysis Insights (Line, Area, Stepline, Multi-Line)
        elif chart_type in ["line", "area", "stepline", "multi_line"] and data_df is not None and not data_df.empty:
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
                        "label": "Trend Direction",
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

        # 3. Relationship Insights (Scatter, Bubble, 3D Scatter, Density Contour)
        elif chart_type in ["scatter", "bubble", "scatter_3d", "density_contour"]:
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
                        "value": f"{len(clean_x):,} points",
                        "detail": "Evaluated across valid paired numeric rows.",
                        "type": "neutral"
                    })

        # 4. Distribution Insights (Histogram, Box, Violin, ECDF)
        elif chart_type in ["histogram", "box", "violin", "ecdf"]:
            target_col = config.get("x") if chart_type in ["histogram", "ecdf"] else config.get("y")
            if target_col and target_col in df.columns:
                series = pd.to_numeric(df[target_col], errors="coerce").dropna()
                if len(series) >= 4:
                    mean_val = float(series.mean())
                    median_val = float(series.median())
                    q25 = float(series.quantile(0.25))
                    q75 = float(series.quantile(0.75))
                    iqr = q75 - q25

                    lower_bound = q25 - 1.5 * iqr
                    upper_bound = q75 + 1.5 * iqr
                    outliers_count = int(((series < lower_bound) | (series > upper_bound)).sum())

                    skew = float(series.skew())
                    if skew > 0.8:
                        skew_desc = "Right-Skewed (Positive tail)"
                    elif skew < -0.8:
                        skew_desc = "Left-Skewed (Negative tail)"
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

        # 6. Waterfall Variance Insights
        elif chart_type == "waterfall" and data_df is not None and not data_df.empty:
            numeric_cols_in_data = [c for c in data_df.columns if pd.api.types.is_numeric_dtype(data_df[c])]
            cat_cols_in_data = [c for c in data_df.columns if c not in numeric_cols_in_data]
            if numeric_cols_in_data and cat_cols_in_data:
                val_col = numeric_cols_in_data[0]
                dim_col = cat_cols_in_data[0]
                total_delta = float(data_df[val_col].sum())
                pos_steps = data_df[data_df[val_col] > 0]
                neg_steps = data_df[data_df[val_col] < 0]

                insights.append({
                    "label": "Net Cumulative Delta",
                    "value": f"{total_delta:+,.2f}",
                    "detail": "Net total impact across all sequential steps.",
                    "type": "success" if total_delta >= 0 else "warning"
                })
                if not pos_steps.empty:
                    top_pos = pos_steps.sort_values(by=val_col, ascending=False).iloc[0]
                    insights.append({
                        "label": "Top Positive Driver",
                        "value": str(top_pos[dim_col]),
                        "detail": f"Contributed {float(top_pos[val_col]):+,.2f}.",
                        "type": "success"
                    })
                if not neg_steps.empty:
                    top_neg = neg_steps.sort_values(by=val_col, ascending=True).iloc[0]
                    insights.append({
                        "label": "Top Negative Drag",
                        "value": str(top_neg[dim_col]),
                        "detail": f"Reduced net total by {float(top_neg[val_col]):+,.2f}.",
                        "type": "warning"
                    })

        # 7. Radar Profile Insights
        elif chart_type == "radar" and data_df is not None and not data_df.empty:
            metric_cols = [c for c in data_df.columns if pd.api.types.is_numeric_dtype(data_df[c])]
            if metric_cols:
                mean_scores = data_df[metric_cols].mean()
                top_m = mean_scores.idxmax()
                top_score = float(mean_scores[top_m])
                low_m = mean_scores.idxmin()
                low_score = float(mean_scores[low_m])

                insights.append({
                    "label": "Highest Dimension",
                    "value": str(top_m),
                    "detail": f"Peak average score of {top_score:,.2f}.",
                    "type": "success"
                })
                insights.append({
                    "label": "Lowest Dimension",
                    "value": str(low_m),
                    "detail": f"Lowest average score of {low_score:,.2f}.",
                    "type": "neutral"
                })
                insights.append({
                    "label": "Metrics Evaluated",
                    "value": f"{len(metric_cols)} Dimensions",
                    "detail": "Spider chart radar profile span.",
                    "type": "info"
                })

        # 8. Gauge KPI Insights
        elif chart_type == "gauge" and data_df is not None and not data_df.empty:
            row = data_df.iloc[0]
            val = float(row["Value"])
            target = float(row["Target"])
            pct_target = (val / target * 100) if target > 0 else 100.0

            insights.append({
                "label": "Current Metric Value",
                "value": f"{val:,.2f}",
                "detail": f"{row['Aggregation']} of {row['Metric']}.",
                "type": "info"
            })
            insights.append({
                "label": "Target Achievement",
                "value": f"{pct_target:.1f}%",
                "detail": f"Reference target is set to {target:,.2f}.",
                "type": "success" if pct_target >= 100 else "warning"
            })

    except Exception:
        pass

    return insights


# =============================================================================
# EXPORT UTILITIES (PNG, Standalone HTML, Configuration JSON, CSV Extract)
# =============================================================================

def export_chart_png(fig: go.Figure, width: int = 1200, height: int = 650, scale: int = 2) -> Tuple[Optional[bytes], Optional[str]]:
    """Export Plotly chart as high-resolution PNG bytes using Kaleido."""
    if fig is None:
        return None, "No active chart figure to export."

    try:
        png_bytes = fig.to_image(format="png", width=width, height=height, scale=scale)
        return png_bytes, None
    except Exception as e:
        return None, f"PNG export failed: {str(e)}"


def export_chart_html(fig: go.Figure, title: str = "Data Studio Visualization") -> str:
    """Export standalone interactive Plotly HTML file string."""
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

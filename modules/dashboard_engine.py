"""
DATA STUDIO v2 — Dashboard Analytics Engine & Smart Insights
=============================================================================
Reusable, modular analytics engine for automatic dataset profiling,
intelligent column prioritization, deterministic insights, and theme-aware
Plotly visualizations.
"""
from typing import Optional, Dict, Any, List, Tuple
import re
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from modules.data_loader import detect_column_type


# =============================================================================
# KEYWORD PATTERNS & SCORING RULES
# =============================================================================

BUSINESS_METRIC_KEYWORDS = re.compile(
    r"(?:^|_)(?:sales|revenue|profit|price|cost|amount|mrr|arr|income|expense|total|fee|balance|spend|value|rating|score|salary|budget|margin|discount|quantity|volume|count|metric|target)$",
    re.IGNORECASE
)

CATEGORY_KEYWORDS = re.compile(
    r"(?:^|_)(?:category|sub_category|status|region|segment|tier|plan|type|group|channel|country|state|city|department|division|gender|role|industry|level|stage)$",
    re.IGNORECASE
)

ID_KEYWORDS = re.compile(
    r"(?:^|_)(?:id|key|code|sku|uuid|guid|ssn|ein|zip|postal|phone|isbn|account_no|order_id|customer_id|user_id|employee_id|item_id|product_id|trans_id|transaction_id)$",
    re.IGNORECASE
)


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
        "grid": "#1e2c47",
        "zero_line": "#3b82f6",
        "primary": "#3b82f6",
        "palette": ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ec4899", "#06b6d4", "#6366f1", "#14b8a6"],
        "color_scale": "Blues"
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
        "color_scale": "Blues"
    }
}


def apply_chart_theme(
    fig: go.Figure,
    theme: str = "Dark",
    title: Optional[str] = None,
    height: int = 340,
    show_legend: bool = False
) -> go.Figure:
    """Apply consistent design system typography, colors, and grid lines to Plotly charts."""
    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
    
    layout_update = {
        "paper_bgcolor": cfg["paper_bg"],
        "plot_bgcolor": cfg["plot_bg"],
        "font": {
            "family": "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
            "color": cfg["text"],
            "size": 12
        },
        "margin": dict(l=36, r=20, t=44 if title else 20, b=36),
        "height": height,
        "showlegend": show_legend,
        "hoverlabel": {
            "bgcolor": "#1e2c47" if theme == "Dark" else "#ffffff",
            "bordercolor": cfg["primary"],
            "font": {"color": "#f8fafc" if theme == "Dark" else "#0f172a", "size": 12}
        }
    }

    if title:
        layout_update["title"] = {
            "text": f"<b>{title}</b>",
            "font": {"size": 14, "color": cfg["text"]},
            "x": 0.01,
            "xanchor": "left"
        }

    fig.update_layout(**layout_update)

    # Update axis grids
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor=cfg["grid"],
        zeroline=False,
        tickfont=dict(color=cfg["subtext"], size=11),
        title_font=dict(color=cfg["subtext"], size=12)
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor=cfg["grid"],
        zeroline=False,
        tickfont=dict(color=cfg["subtext"], size=11),
        title_font=dict(color=cfg["subtext"], size=12)
    )

    return fig


# =============================================================================
# COLUMN SELECTION & INTELLIGENT PRIORITIZATION
# =============================================================================

def select_analytical_columns(df: pd.DataFrame, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
    """
    Classify and segregate columns into analytical categories, strictly
    filtering out high-cardinality IDs from numerical and categorical analysis.
    """
    total_rows = len(df)
    
    numeric_cols: List[str] = []
    categorical_cols: List[str] = []
    datetime_cols: List[str] = []
    text_cols: List[str] = []
    boolean_cols: List[str] = []

    for col in df.columns:
        series = df[col]
        col_str = str(col)
        detected_type = detect_column_type(series, col_str, total_rows)
        
        # Check if column is an identifier
        is_id_name = bool(ID_KEYWORDS.search(col_str)) or "index" in col_str.lower()
        unique_cnt = series.nunique(dropna=True)
        is_integer_seq = pd.api.types.is_integer_dtype(series) and unique_cnt == total_rows and total_rows > 30

        if detected_type == "Numeric":
            # Exclude IDs (columns named with ID patterns or integer sequential index)
            if is_id_name or is_integer_seq:
                text_cols.append(col)
            else:
                numeric_cols.append(col)
        elif detected_type == "Categorical":
            if is_id_name and unique_cnt == total_rows:
                text_cols.append(col)
            elif 2 <= unique_cnt <= 40:
                categorical_cols.append(col)
            else:
                text_cols.append(col)
        elif detected_type == "Date/Time":
            datetime_cols.append(col)
        elif detected_type == "Boolean":
            boolean_cols.append(col)
        else:
            text_cols.append(col)

    return {
        "numeric": numeric_cols,
        "categorical": categorical_cols,
        "datetime": datetime_cols,
        "text": text_cols,
        "boolean": boolean_cols
    }


def prioritize_numeric_columns(df: pd.DataFrame, numeric_cols: List[str]) -> List[str]:
    """Rank numeric columns by relevance for dashboard visual representation."""
    if not numeric_cols:
        return []

    scored_cols = []
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue

        score = 0.0
        col_lower = str(col).lower()

        # Business keyword match (+12)
        if BUSINESS_METRIC_KEYWORDS.search(col_lower):
            score += 12.0

        # Variance and spread (+4 if valid variance)
        var = series.var()
        if pd.notna(var) and var > 0:
            score += 4.0

        # Completeness (+3 for high data density)
        missing_rate = df[col].isna().mean()
        score += (1.0 - missing_rate) * 3.0

        # Distinct values count (+2 for continuous variation)
        if series.nunique() > 5:
            score += 2.0

        scored_cols.append((col, score))

    scored_cols.sort(key=lambda x: x[1], reverse=True)
    return [col for col, _ in scored_cols]


def prioritize_categorical_columns(df: pd.DataFrame, cat_cols: List[str]) -> List[str]:
    """Rank categorical columns by suitability for bar and comparison charts."""
    if not cat_cols:
        return []

    scored_cols = []
    for col in cat_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue

        score = 0.0
        col_lower = str(col).lower()
        unique_cnt = series.nunique()

        # Ideal cardinality for bar charts is 2 to 12 categories (+10)
        if 2 <= unique_cnt <= 12:
            score += 10.0
        elif 13 <= unique_cnt <= 25:
            score += 5.0

        # Business keyword match (+8)
        if CATEGORY_KEYWORDS.search(col_lower):
            score += 8.0

        # Completeness (+2)
        missing_rate = df[col].isna().mean()
        score += (1.0 - missing_rate) * 2.0

        scored_cols.append((col, score))

    scored_cols.sort(key=lambda x: x[1], reverse=True)
    return [col for col, _ in scored_cols]


# =============================================================================
# PRIMARY METRICS & KPI SELECTION
# =============================================================================

def select_primary_kpi_metric(df: pd.DataFrame, ranked_numeric_cols: List[str]) -> Optional[Dict[str, Any]]:
    """Select the most meaningful primary numeric metric for top-level KPI display."""
    if not ranked_numeric_cols:
        return None

    top_col = ranked_numeric_cols[0]
    series = df[top_col].dropna()
    if len(series) == 0:
        return None

    col_lower = str(top_col).lower()
    
    # Decide whether Sum or Mean makes more analytical sense
    is_sum_candidate = any(w in col_lower for w in ["sales", "revenue", "profit", "amount", "volume", "mrr", "arr", "spend", "cost", "total", "quantity"])
    
    if is_sum_candidate:
        agg_val = series.sum()
        agg_type = "Total"
    else:
        agg_val = series.mean()
        agg_type = "Average"

    # Format value
    if abs(agg_val) >= 1_000_000:
        formatted_val = f"{agg_val / 1_000_000:.2f}M"
    elif abs(agg_val) >= 1_000:
        formatted_val = f"{agg_val / 1_000:.1f}K"
    elif isinstance(agg_val, float):
        formatted_val = f"{agg_val:,.2f}"
    else:
        formatted_val = f"{agg_val:,}"

    return {
        "column": top_col,
        "label": f"{agg_type} {top_col.replace('_', ' ').title()}",
        "value": formatted_val,
        "agg_type": agg_type,
        "raw_value": agg_val,
        "median": series.median(),
        "std": series.std()
    }


# =============================================================================
# DETERMINISTIC SMART INSIGHTS ENGINE
# =============================================================================

def generate_smart_insights(
    df: pd.DataFrame,
    metadata: Dict[str, Any],
    analytical_cols: Dict[str, List[str]]
) -> List[Dict[str, str]]:
    """
    Generate 4 to 6 fact-based, deterministic analytical observations
    directly from dataset statistics without hallucinations or unsupported claims.
    """
    insights: List[Dict[str, str]] = []
    total_rows = len(df)
    total_cols = len(df.columns)
    
    # 1. Scale & Completeness Insight
    missing_cells = metadata.get("missing_cells", 0)
    missing_pct = metadata.get("missing_percentage", 0.0)
    if missing_cells == 0:
        insights.append({
            "title": "Data Completeness",
            "text": f"The dataset contains <b>{total_rows:,}</b> records across <b>{total_cols}</b> features with <b>100% data completeness</b> (zero null values detected).",
            "variant": "success"
        })
    else:
        cols_affected = metadata.get("columns_with_missing", 0)
        insights.append({
            "title": "Data Completeness Profile",
            "text": f"The dataset contains <b>{total_rows:,}</b> records with an overall missing rate of <b>{missing_pct:.2f}%</b> ({missing_cells:,} missing cells affecting {cols_affected} of {total_cols} columns).",
            "variant": "warning" if missing_pct > 5 else "info"
        })

    # 2. Dominant Category Insight
    cat_cols = analytical_cols.get("categorical", [])
    if cat_cols:
        top_cat_col = cat_cols[0]
        val_counts = df[top_cat_col].value_counts(dropna=True)
        if len(val_counts) > 0:
            top_cat_name = str(val_counts.index[0])
            top_cat_count = int(val_counts.iloc[0])
            top_cat_pct = (top_cat_count / total_rows) * 100
            insights.append({
                "title": f"Category Distribution ({top_cat_col})",
                "text": f"In <b>{top_cat_col}</b>, the leading segment is <b>'{top_cat_name}'</b>, comprising <b>{top_cat_pct:.1f}%</b> of total records ({top_cat_count:,} entries across {len(val_counts)} distinct groups).",
                "variant": "info"
            })

    # 3. Numeric Spread & Variability Insight
    num_cols = analytical_cols.get("numeric", [])
    if num_cols:
        # Find column with highest relative spread (coefficient of variation)
        cv_scores = []
        for col in num_cols:
            s = df[col].dropna()
            if len(s) > 1 and s.mean() != 0:
                cv = abs(s.std() / s.mean())
                cv_scores.append((col, cv, s.mean(), s.std(), s.min(), s.max()))

        if cv_scores:
            cv_scores.sort(key=lambda x: x[1], reverse=True)
            top_var_col, _, mean_val, std_val, min_val, max_val = cv_scores[0]
            insights.append({
                "title": f"Feature Variability ({top_var_col})",
                "text": f"<b>{top_var_col}</b> exhibits high relative dispersion (mean: <b>{mean_val:,.2f}</b>, std: <b>{std_val:,.2f}</b>, range: <b>{min_val:,.1f}</b> to <b>{max_val:,.1f}</b>).",
                "variant": "info"
            })

    # 4. Correlation Relationship Insight
    if len(num_cols) >= 2:
        valid_num_df = df[num_cols[:6]].dropna()
        if len(valid_num_df) > 5:
            corr_matrix = valid_num_df.corr(numeric_only=True)
            # Find strongest off-diagonal correlation
            pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    c1, c2 = corr_matrix.columns[i], corr_matrix.columns[j]
                    r = corr_matrix.iloc[i, j]
                    if pd.notna(r):
                        pairs.append((c1, c2, r, abs(r)))

            if pairs:
                pairs.sort(key=lambda x: x[3], reverse=True)
                c1, c2, r_val, abs_r = pairs[0]
                if abs_r >= 0.65:
                    rel_type = "strong positive" if r_val > 0 else "strong negative"
                    insights.append({
                        "title": "Strong Correlation Detected",
                        "text": f"A <b>{rel_type} relationship (Pearson r = {r_val:+.2f})</b> was detected between <b>{c1}</b> and <b>{c2}</b>.",
                        "variant": "success" if r_val > 0 else "info"
                    })
                elif abs_r >= 0.35:
                    rel_type = "moderate positive" if r_val > 0 else "moderate negative"
                    insights.append({
                        "title": "Moderate Relationship",
                        "text": f"A <b>{rel_type} correlation (Pearson r = {r_val:+.2f})</b> exists between <b>{c1}</b> and <b>{c2}</b>.",
                        "variant": "info"
                    })

    # 5. Temporal Span Insight
    dt_cols = analytical_cols.get("datetime", [])
    if dt_cols:
        time_col = dt_cols[0]
        parsed_dates = pd.to_datetime(df[time_col], errors="coerce").dropna()
        if len(parsed_dates) > 0:
            min_d = parsed_dates.min().strftime("%Y-%m-%d")
            max_d = parsed_dates.max().strftime("%Y-%m-%d")
            delta_days = (parsed_dates.max() - parsed_dates.min()).days
            insights.append({
                "title": f"Temporal Coverage ({time_col})",
                "text": f"Time-series records span <b>{delta_days:,} days</b> from <b>{min_d}</b> through <b>{max_d}</b>.",
                "variant": "info"
            })

    # 6. Duplication & Integrity Insight
    dup_rows = metadata.get("duplicate_rows", 0)
    dup_pct = metadata.get("duplicate_percentage", 0.0)
    if dup_rows > 0:
        insights.append({
            "title": "Record Redundancy",
            "text": f"Detected <b>{dup_rows:,} duplicate records ({dup_pct:.1f}%)</b> that can be audited in Data Quality and resolved in Data Preparation.",
            "variant": "warning"
        })

    return insights


# =============================================================================
# AUTOMATIC CHART BUILDERS
# =============================================================================

def generate_composition_chart(metadata: Dict[str, Any], theme: str = "Dark") -> Optional[go.Figure]:
    """Generate donut chart of column type composition."""
    try:
        counts = metadata.get("column_types_count", {})
        labels = [k for k, v in counts.items() if v > 0]
        values = [counts[k] for k in labels]
        
        if not values or sum(values) == 0:
            return None

        cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
        color_map = {
            "Numeric": "#3b82f6",
            "Categorical": "#8b5cf6",
            "Date/Time": "#10b981",
            "Text": "#f59e0b",
            "Boolean": "#ec4899"
        }
        colors = [color_map.get(l, "#64748b") for l in labels]

        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.62,
                marker=dict(colors=colors, line=dict(color=cfg["grid"], width=1.5)),
                textinfo="label+value",
                textposition="outside",
                hoverinfo="label+value+percent",
                showlegend=False
            )
        ])

        fig.update_layout(
            annotations=[dict(
                text=f"<b>{sum(values)}</b><br><span style='font-size:10px; color:{cfg['subtext']};'>Columns</span>",
                x=0.5, y=0.5,
                font_size=16,
                font_color=cfg["text"],
                showarrow=False
            )]
        )

        return apply_chart_theme(fig, theme=theme, title="Dataset Schema Composition", height=280)
    except Exception:
        return None


def generate_numeric_distribution_chart(
    df: pd.DataFrame,
    col_name: str,
    theme: str = "Dark"
) -> Optional[go.Figure]:
    """Generate clean histogram / distribution curve for top numeric feature."""
    try:
        series = df[col_name].dropna()
        if len(series) == 0:
            return None

        cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=series,
            nbinsx=min(25, max(8, series.nunique())),
            marker=dict(
                color=cfg["primary"],
                line=dict(color=cfg["grid"], width=1)
            ),
            opacity=0.85,
            name=col_name,
            hovertemplate=f"<b>{col_name}</b>: %{{x}}<br>Count: %{{y}}<extra></extra>"
        ))

        title_str = f"Distribution: {col_name.replace('_', ' ').title()}"
        apply_chart_theme(fig, theme=theme, title=title_str, height=320)
        fig.update_xaxes(title_text=col_name)
        fig.update_yaxes(title_text="Frequency")
        return fig
    except Exception:
        return None


def generate_categorical_bar_chart(
    df: pd.DataFrame,
    col_name: str,
    theme: str = "Dark",
    top_n: int = 8
) -> Optional[go.Figure]:
    """Generate horizontal / vertical bar chart of category frequencies."""
    try:
        series = df[col_name].dropna()
        if len(series) == 0:
            return None

        val_counts = series.value_counts()
        if len(val_counts) > top_n:
            top_slice = val_counts.head(top_n)
            other_count = val_counts.iloc[top_n:].sum()
            labels = list(top_slice.index) + ["Other"]
            values = list(top_slice.values) + [other_count]
        else:
            labels = list(val_counts.index)
            values = list(val_counts.values)

        cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
        
        # Horizontal bar if label length is substantial or >= 5 categories
        fig = go.Figure(data=[
            go.Bar(
                x=values,
                y=[str(l) for l in labels],
                orientation="h",
                marker=dict(
                    color=cfg["palette"][1 % len(cfg["palette"])],
                    line=dict(color=cfg["grid"], width=1)
                ),
                hovertemplate="Category: <b>%{y}</b><br>Count: %{x}<extra></extra>"
            )
        ])

        title_str = f"Category Breakdown: {col_name.replace('_', ' ').title()}"
        apply_chart_theme(fig, theme=theme, title=title_str, height=320)
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(title_text="Record Count")
        return fig
    except Exception:
        return None


def generate_time_trend_chart(
    df: pd.DataFrame,
    time_col: str,
    metric_col: Optional[str] = None,
    theme: str = "Dark"
) -> Optional[go.Figure]:
    """Generate chronological time trend chart."""
    try:
        temp_df = df[[time_col] + ([metric_col] if metric_col else [])].copy()
        temp_df["_dt_parsed"] = pd.to_datetime(temp_df[time_col], errors="coerce")
        temp_df = temp_df.dropna(subset=["_dt_parsed"])
        
        if len(temp_df) < 2:
            return None

        temp_df = temp_df.sort_values("_dt_parsed")
        
        # Determine appropriate time bucket based on date range
        span_days = (temp_df["_dt_parsed"].max() - temp_df["_dt_parsed"].min()).days
        if span_days > 730:
            bucket = "ME" # Month End
        elif span_days > 60:
            bucket = "W" # Weekly
        else:
            bucket = "D" # Daily

        cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
        fig = go.Figure()

        if metric_col and pd.api.types.is_numeric_dtype(temp_df[metric_col]):
            grouped = temp_df.set_index("_dt_parsed")[metric_col].resample(bucket).sum().reset_index()
            y_col_title = f"Total {metric_col.replace('_', ' ').title()}"
            fig.add_trace(go.Scatter(
                x=grouped["_dt_parsed"],
                y=grouped[metric_col],
                mode="lines+markers",
                line=dict(color=cfg["palette"][2 % len(cfg["palette"])], width=2.5),
                marker=dict(size=6, color=cfg["palette"][2 % len(cfg["palette"])]),
                name=metric_col,
                hovertemplate=f"Date: %{{x|%Y-%m-%d}}<br>{metric_col}: %{{y:,.2f}}<extra></extra>"
            ))
            title_str = f"Trend Over Time: {metric_col.replace('_', ' ').title()}"
        else:
            grouped = temp_df.set_index("_dt_parsed").resample(bucket).size().reset_index(name="count")
            y_col_title = "Record Count"
            fig.add_trace(go.Scatter(
                x=grouped["_dt_parsed"],
                y=grouped["count"],
                mode="lines+markers",
                line=dict(color=cfg["palette"][2 % len(cfg["palette"])], width=2.5),
                marker=dict(size=6, color=cfg["palette"][2 % len(cfg["palette"])]),
                name="Records",
                hovertemplate="Date: %{x|%Y-%m-%d}<br>Records: %{y:,}<extra></extra>"
            ))
            title_str = f"Record Activity: {time_col.replace('_', ' ').title()}"

        apply_chart_theme(fig, theme=theme, title=title_str, height=320)
        fig.update_xaxes(title_text="Timeline")
        fig.update_yaxes(title_text=y_col_title)
        return fig
    except Exception:
        return None


def generate_correlation_heatmap(
    df: pd.DataFrame,
    numeric_cols: List[str],
    theme: str = "Dark"
) -> Tuple[Optional[go.Figure], Optional[Dict[str, Any]]]:
    """Generate compact correlation matrix heatmap and top correlated relationship pair."""
    try:
        if len(numeric_cols) < 2:
            return None, None

        # Pick top 3 to 6 columns
        target_cols = numeric_cols[:6]
        corr_df = df[target_cols].dropna().corr(numeric_only=True)
        
        if corr_df.empty or len(corr_df) < 2:
            return None, None

        # Clean display names
        display_names = [c.replace("_", " ").title() for c in target_cols]
        z_vals = corr_df.values.round(2)

        # Top correlation pair detection
        pairs = []
        for i in range(len(target_cols)):
            for j in range(i + 1, len(target_cols)):
                r = corr_df.iloc[i, j]
                if pd.notna(r):
                    pairs.append((target_cols[i], target_cols[j], float(r), abs(float(r))))

        top_pair = None
        if pairs:
            pairs.sort(key=lambda x: x[3], reverse=True)
            c1, c2, r_val, _ = pairs[0]
            top_pair = {"col1": c1, "col2": c2, "r": r_val}

        cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
        
        fig = go.Figure(data=go.Heatmap(
            z=z_vals,
            x=display_names,
            y=display_names,
            colorscale=[[0, "#ef4444"], [0.5, "#1e293b" if theme == "Dark" else "#e2e8f0"], [1, "#3b82f6"]],
            zmin=-1.0,
            zmax=1.0,
            text=z_vals,
            texttemplate="%{text:+.2f}",
            textfont=dict(size=11, color="#ffffff" if theme == "Dark" else "#0f172a"),
            hoverongaps=False,
            hovertemplate="<b>%{x}</b> ↔ <b>%{y}</b><br>Correlation: %{z:+.2f}<extra></extra>"
        ))

        apply_chart_theme(fig, theme=theme, title="Feature Correlation Snapshot", height=340)
        return fig, top_pair
    except Exception:
        return None, None

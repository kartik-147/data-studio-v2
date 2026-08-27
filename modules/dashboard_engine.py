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


def generate_scatter_relationship_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    theme: str = "Dark"
) -> Optional[go.Figure]:
    """Generate high-density scatter plot for correlation/driver analysis with trend line."""
    try:
        cols_to_use = [x_col, y_col] + ([color_col] if color_col and color_col in df.columns else [])
        temp_df = df[cols_to_use].dropna().head(1000) # sample to protect rendering speed
        
        if len(temp_df) < 5:
            return None

        cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
        
        if color_col and color_col in temp_df.columns:
            fig = px.scatter(
                temp_df,
                x=x_col,
                y=y_col,
                color=color_col,
                title=f"{y_col.replace('_', ' ').title()} vs {x_col.replace('_', ' ').title()}",
                color_discrete_sequence=cfg["palette"],
                opacity=0.75
            )
        else:
            fig = px.scatter(
                temp_df,
                x=x_col,
                y=y_col,
                title=f"{y_col.replace('_', ' ').title()} vs {x_col.replace('_', ' ').title()}",
                color_discrete_sequence=[cfg["primary"]],
                opacity=0.75
            )

        apply_chart_theme(fig, theme=theme, height=330, show_legend=bool(color_col))
        fig.update_traces(marker=dict(size=7, line=dict(width=0.5, color=cfg["grid"])))
        return fig
    except Exception:
        return None


# =============================================================================
# MULTI-PERSPECTIVE AI DASHBOARD SYNTHESIS
# =============================================================================

PERSPECTIVE_DEFINITIONS = [
    {
        "id": "executive",
        "name": "Executive & Core Performance",
        "tag": "PERSPECTIVE 1 OF 4",
        "icon": "trending-up",
        "desc": "High-level KPI scorecard, primary metric distribution, top category breakdown, and composition share."
    },
    {
        "id": "segment",
        "name": "Segment & Dimensional Slices",
        "tag": "PERSPECTIVE 2 OF 4",
        "icon": "layers",
        "desc": "Cross-categorical comparisons, multi-segment distributions, and categorical volume rankings."
    },
    {
        "id": "drivers",
        "name": "Driver & Correlation Radar",
        "tag": "PERSPECTIVE 3 OF 4",
        "icon": "activity",
        "desc": "Deep-dive relationship scatter, strongest correlation matrix, and multi-variable interaction patterns."
    },
    {
        "id": "anomalies",
        "name": "Anomaly & Data Health Matrix",
        "tag": "PERSPECTIVE 4 OF 4",
        "icon": "alert-triangle",
        "desc": "Outlier profiles, data completeness health, high-variance attributes, and risk distributions."
    }
]


def generate_ai_dashboard_perspective(
    df: pd.DataFrame,
    metadata: Dict[str, Any],
    perspective_idx: int = 0,
    filtered_df: Optional[pd.DataFrame] = None,
    theme: str = "Dark"
) -> Dict[str, Any]:
    """
    Synthesizes a complete Power BI / Tableau single-screen dashboard layout
    with 4 KPI cards, 4 complementary charts, and 3 executive insight bullets
    tailored dynamically based on the selected AI perspective.
    """
    active_df = filtered_df if filtered_df is not None and not filtered_df.empty else df
    active_idx = perspective_idx % len(PERSPECTIVE_DEFINITIONS)
    p_meta = PERSPECTIVE_DEFINITIONS[active_idx]

    analytical_cols = select_analytical_columns(active_df, metadata)
    ranked_num = prioritize_numeric_columns(active_df, analytical_cols["numeric"])
    ranked_cat = prioritize_categorical_columns(active_df, analytical_cols["categorical"])
    dt_cols = analytical_cols["datetime"]

    total_rows = len(active_df)
    total_cols = len(active_df.columns)

    # Build Perspective-Specific KPIs
    kpi_cards = []
    charts = []
    briefing = []

    # ─────────────────────────────────────────────────────────────────────────
    # PERSPECTIVE 0: Executive & Core Performance
    # ─────────────────────────────────────────────────────────────────────────
    if active_idx == 0:
        # KPI 1: Primary Metric
        primary_kpi = select_primary_kpi_metric(active_df, ranked_num)
        if primary_kpi:
            kpi_cards.append({
                "label": primary_kpi["label"],
                "value": primary_kpi["value"],
                "meta": f"Median: {primary_kpi['median']:,.1f} · Std: {primary_kpi['std']:,.1f}",
                "badge": "PRIMARY METRIC",
                "badge_class": "pbi-badge-up",
                "tile_class": "pbi-kpi-tile-success"
            })
        else:
            kpi_cards.append({
                "label": "Total Records",
                "value": f"{total_rows:,}",
                "meta": f"{total_cols} columns loaded",
                "badge": "VOLUME",
                "badge_class": "pbi-badge-neutral",
                "tile_class": ""
            })

        # KPI 2: Secondary Numeric or Average
        if len(ranked_num) >= 2:
            sec_col = ranked_num[1]
            s = active_df[sec_col].dropna()
            kpi_cards.append({
                "label": f"Avg {sec_col.replace('_', ' ').title()}",
                "value": f"{s.mean():,.2f}" if s.mean() < 1000 else f"{s.mean():,.1f}",
                "meta": f"Range: [{s.min():,.1f} – {s.max():,.1f}]",
                "badge": "BENCHMARK",
                "badge_class": "pbi-badge-neutral",
                "tile_class": "pbi-kpi-tile-info"
            })
        elif ranked_cat:
            top_cat = ranked_cat[0]
            kpi_cards.append({
                "label": f"Top {top_cat.replace('_', ' ').title()}",
                "value": str(active_df[top_cat].mode().iloc[0]) if not active_df[top_cat].dropna().empty else "N/A",
                "meta": f"{active_df[top_cat].nunique()} unique segments",
                "badge": "LEADER",
                "badge_class": "pbi-badge-up",
                "tile_class": "pbi-kpi-tile-purple"
            })

        # KPI 3: Dataset Quality Score
        qs = metadata.get("quality_score", 95.0)
        qs_status = "Optimal" if qs >= 85 else ("Acceptable" if qs >= 70 else "Attention")
        kpi_cards.append({
            "label": "Data Quality Index",
            "value": f"{qs:.1f}%",
            "meta": f"Missing: {metadata.get('missing_percentage', 0.0):.1f}% · Dups: {metadata.get('duplicate_percentage', 0.0):.1f}%",
            "badge": qs_status.upper(),
            "badge_class": "pbi-badge-up" if qs >= 80 else "pbi-badge-down",
            "tile_class": "pbi-kpi-tile-warning" if qs < 80 else ""
        })

        # KPI 4: Active Filter Scope
        pct_of_orig = (total_rows / len(df) * 100) if len(df) > 0 else 100
        kpi_cards.append({
            "label": "Active Data Scope",
            "value": f"{total_rows:,} rows",
            "meta": f"{pct_of_orig:.0f}% of full dataset",
            "badge": "FILTERED" if total_rows != len(df) else "100% INCLUDED",
            "badge_class": "pbi-badge-neutral",
            "tile_class": "pbi-kpi-tile-info"
        })

        # Chart 1: Time Trend or Numeric Distribution
        if dt_cols and ranked_num:
            c1_fig = generate_time_trend_chart(active_df, dt_cols[0], ranked_num[0], theme=theme)
            charts.append({"title": f"Timeline Trend: {ranked_num[0].title()}", "badge": "TIMELINE", "fig": c1_fig})
        elif ranked_num:
            c1_fig = generate_numeric_distribution_chart(active_df, ranked_num[0], theme=theme)
            charts.append({"title": f"Distribution: {ranked_num[0].title()}", "badge": "DISTRIBUTION", "fig": c1_fig})

        # Chart 2: Category Breakdown
        if ranked_cat:
            c2_fig = generate_categorical_bar_chart(active_df, ranked_cat[0], top_n=8, theme=theme)
            charts.append({"title": f"Volume by {ranked_cat[0].title()}", "badge": "CATEGORIES", "fig": c2_fig})

        # Chart 3: Composition Share
        c3_fig = generate_composition_chart(metadata, theme=theme)
        charts.append({"title": "Schema Data Type Breakdown", "badge": "COMPOSITION", "fig": c3_fig})

        # Chart 4: Correlation or Secondary Category/Numeric
        if len(ranked_num) >= 2:
            c4_fig, _ = generate_correlation_heatmap(active_df, ranked_num, theme=theme)
            charts.append({"title": "Correlation Matrix Snapshot", "badge": "CORRELATION", "fig": c4_fig})
        elif len(ranked_cat) >= 2:
            c4_fig = generate_categorical_bar_chart(active_df, ranked_cat[1], top_n=8, theme=theme)
            charts.append({"title": f"Breakdown: {ranked_cat[1].title()}", "badge": "CATEGORIES", "fig": c4_fig})

        # Executive Briefing
        briefing.append({
            "title": "Primary Driver Focus",
            "text": f"The primary operational feature is '{ranked_num[0] if ranked_num else 'N/A'}' across {total_rows:,} observed records."
        })
        if ranked_cat:
            briefing.append({
                "title": "Segment Distribution",
                "text": f"Categorical segment '{ranked_cat[0]}' accounts for dominant record volume across {active_df[ranked_cat[0]].nunique()} unique tiers."
            })
        briefing.append({
            "title": "Data Health Status",
            "text": f"Overall quality score is {qs:.1f}% with {metadata.get('missing_percentage', 0.0):.1f}% missing value rate."
        })

    # ─────────────────────────────────────────────────────────────────────────
    # PERSPECTIVE 1: Segment & Dimensional Slices
    # ─────────────────────────────────────────────────────────────────────────
    elif active_idx == 1:
        # Category-centric KPIs
        for i, c in enumerate(ranked_cat[:3]):
            s = active_df[c].dropna()
            top_val = s.mode().iloc[0] if not s.empty else "N/A"
            kpi_cards.append({
                "label": f"{c.replace('_', ' ').title()}",
                "value": f"{s.nunique()} Segments",
                "meta": f"Top: {str(top_val)[:18]} ({((s == top_val).sum() / len(s) * 100):.1f}%)" if len(s) > 0 else "N/A",
                "badge": "CARDINALITY",
                "badge_class": "pbi-badge-neutral",
                "tile_class": "pbi-kpi-tile-purple" if i == 0 else ""
            })

        while len(kpi_cards) < 4:
            kpi_cards.append({
                "label": "Total Categorical Fields",
                "value": f"{len(analytical_cols['categorical'])}",
                "meta": f"{total_rows:,} total rows",
                "badge": "DIMENSIONS",
                "badge_class": "pbi-badge-neutral",
                "tile_class": "pbi-kpi-tile-info"
            })

        # 4 Categorical & Comparative Charts
        for cat in ranked_cat[:3]:
            fig = generate_categorical_bar_chart(active_df, cat, top_n=10, theme=theme)
            if fig:
                charts.append({"title": f"Distribution by {cat.title()}", "badge": "SEGMENT", "fig": fig})

        if ranked_num and ranked_cat:
            # Scatter / Group comparison
            fig = generate_scatter_relationship_chart(active_df, ranked_num[0], ranked_num[1] if len(ranked_num) > 1 else ranked_num[0], color_col=ranked_cat[0], theme=theme)
            if fig:
                charts.append({"title": f"Segment Dispersion ({ranked_cat[0].title()})", "badge": "DISPERSION", "fig": fig})

        briefing.append({
            "title": "Dimensional Hierarchy",
            "text": f"Found {len(ranked_cat)} high-signal categorical dimensions suitable for slicing and grouping."
        })
        if ranked_cat:
            briefing.append({
                "title": "Concentration Analysis",
                "text": f"Dimension '{ranked_cat[0]}' shows concentrated activity in top-ranking groups."
            })
        briefing.append({
            "title": "Cross-Filtering Ready",
            "text": "Use the top slicer bar to dynamically filter the entire dashboard by category."
        })

    # ─────────────────────────────────────────────────────────────────────────
    # PERSPECTIVE 2: Driver & Correlation Radar
    # ─────────────────────────────────────────────────────────────────────────
    elif active_idx == 2:
        if len(ranked_num) >= 2:
            c_matrix = active_df[ranked_num[:6]].dropna().corr()
            # Find top correlation
            pairs = []
            for i in range(len(c_matrix.columns)):
                for j in range(i + 1, len(c_matrix.columns)):
                    r = c_matrix.iloc[i, j]
                    if pd.notna(r):
                        pairs.append((c_matrix.columns[i], c_matrix.columns[j], float(r)))
            pairs.sort(key=lambda x: abs(x[2]), reverse=True)

            if pairs:
                top_p = pairs[0]
                kpi_cards.append({
                    "label": "Strongest Correlation",
                    "value": f"r = {top_p[2]:+.2f}",
                    "meta": f"{top_p[0]} ↔ {top_p[1]}",
                    "badge": "COEFFICIENT",
                    "badge_class": "pbi-badge-up" if abs(top_p[2]) >= 0.7 else "pbi-badge-neutral",
                    "tile_class": "pbi-kpi-tile-success"
                })

        while len(kpi_cards) < 4:
            idx = len(kpi_cards)
            if idx < len(ranked_num):
                col = ranked_num[idx]
                s = active_df[col].dropna()
                kpi_cards.append({
                    "label": f"Variance: {col.title()}",
                    "value": f"{s.std():,.2f}" if s.std() < 1000 else f"{s.std():,.1f}",
                    "meta": f"Mean: {s.mean():,.2f}",
                    "badge": "SPREAD",
                    "badge_class": "pbi-badge-neutral",
                    "tile_class": ""
                })
            else:
                kpi_cards.append({
                    "label": "Analyzed Metrics",
                    "value": f"{len(ranked_num)}",
                    "meta": "Numeric variables evaluated",
                    "badge": "CORRELATION RADAR",
                    "badge_class": "pbi-badge-neutral",
                    "tile_class": "pbi-kpi-tile-info"
                })

        # Charts: Heatmap, Scatter 1, Scatter 2, Numeric Distribution
        if len(ranked_num) >= 2:
            h_fig, _ = generate_correlation_heatmap(active_df, ranked_num, theme=theme)
            if h_fig:
                charts.append({"title": "Pairwise Correlation Heatmap", "badge": "MATRIX", "fig": h_fig})

            sc_fig = generate_scatter_relationship_chart(active_df, ranked_num[0], ranked_num[1], color_col=ranked_cat[0] if ranked_cat else None, theme=theme)
            if sc_fig:
                charts.append({"title": f"Relationship: {ranked_num[0].title()} ↔ {ranked_num[1].title()}", "badge": "SCATTER", "fig": sc_fig})

        if len(ranked_num) >= 3:
            sc2_fig = generate_scatter_relationship_chart(active_df, ranked_num[0], ranked_num[2], theme=theme)
            if sc2_fig:
                charts.append({"title": f"Relationship: {ranked_num[0].title()} ↔ {ranked_num[2].title()}", "badge": "SCATTER", "fig": sc2_fig})

        if ranked_num:
            d_fig = generate_numeric_distribution_chart(active_df, ranked_num[0], theme=theme)
            if d_fig:
                charts.append({"title": f"Distribution: {ranked_num[0].title()}", "badge": "DISTRIBUTION", "fig": d_fig})

        briefing.append({
            "title": "Driver Interdependence",
            "text": f"Identified {len(ranked_num)} quantitative features with active variance and statistical correlation."
        })
        briefing.append({
            "title": "Predictive Indicators",
            "text": "Strong linear relationships indicate potential multicollinearity or shared underlying trends."
        })
        briefing.append({
            "title": "Scatter Patterns",
            "text": "Inspect scatter clusters to identify distinct operational customer/transaction subgroups."
        })

    # ─────────────────────────────────────────────────────────────────────────
    # PERSPECTIVE 3: Anomaly & Data Health Matrix
    # ─────────────────────────────────────────────────────────────────────────
    else:
        # Outlier count
        total_outliers = 0
        for col in ranked_num[:5]:
            s = active_df[col].dropna()
            if len(s) >= 4:
                q1, q3 = s.quantile(0.25), s.quantile(0.75)
                iqr = q3 - q1
                total_outliers += int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())

        kpi_cards.append({
            "label": "Total Potential Outliers",
            "value": f"{total_outliers:,}",
            "meta": "IQR 1.5× Boundary Method",
            "badge": "ANOMALY RADAR",
            "badge_class": "pbi-badge-down" if total_outliers > 0 else "pbi-badge-up",
            "tile_class": "pbi-kpi-tile-warning"
        })

        # Missing values
        missing_cnt = int(active_df.isna().sum().sum())
        kpi_cards.append({
            "label": "Missing Data Cells",
            "value": f"{missing_cnt:,}",
            "meta": f"{metadata.get('missing_percentage', 0.0):.2f}% of total cells",
            "badge": "COMPLETENESS",
            "badge_class": "pbi-badge-up" if missing_cnt == 0 else "pbi-badge-down",
            "tile_class": "pbi-kpi-tile-warning" if missing_cnt > 0 else "pbi-kpi-tile-success"
        })

        # Duplicate records
        dup_cnt = int(active_df.duplicated().sum())
        kpi_cards.append({
            "label": "Duplicate Rows",
            "value": f"{dup_cnt:,}",
            "meta": f"{metadata.get('duplicate_percentage', 0.0):.2f}% redundancy",
            "badge": "UNIQUENESS",
            "badge_class": "pbi-badge-up" if dup_cnt == 0 else "pbi-badge-down",
            "tile_class": "pbi-kpi-tile-warning" if dup_cnt > 0 else "pbi-kpi-tile-success"
        })

        # Quality Score
        qs = metadata.get("quality_score", 90.0)
        kpi_cards.append({
            "label": "Health Index",
            "value": f"{qs:.1f}/100",
            "meta": "Automated Quality Assessment",
            "badge": "AUDIT",
            "badge_class": "pbi-badge-up" if qs >= 80 else "pbi-badge-down",
            "tile_class": "pbi-kpi-tile-success" if qs >= 80 else "pbi-kpi-tile-warning"
        })

        # Charts: Distributions showing outlier tails
        for col in ranked_num[:3]:
            fig = generate_numeric_distribution_chart(active_df, col, theme=theme)
            if fig:
                charts.append({"title": f"Outlier Tail Inspection: {col.title()}", "badge": "ANOMALY", "fig": fig})

        c_comp = generate_composition_chart(metadata, theme=theme)
        if c_comp:
            charts.append({"title": "Schema Completeness Breakdown", "badge": "COMPOSITION", "fig": c_comp})

        briefing.append({
            "title": "Anomaly Landscape",
            "text": f"Found {total_outliers:,} potential outlier records across evaluated numeric attributes."
        })
        briefing.append({
            "title": "Completeness Profile",
            "text": f"Dataset completeness is at {100 - metadata.get('missing_percentage', 0.0):.1f}%."
        })
        briefing.append({
            "title": "Remediation Action",
            "text": "Navigate to Data Preparation if you wish to cap, winsorize, or filter extreme outlier values."
        })

    # Fallback to fill 4 charts if needed
    while len(charts) < 4:
        if ranked_cat and len(charts) < len(ranked_cat):
            fig = generate_categorical_bar_chart(active_df, ranked_cat[len(charts) % len(ranked_cat)], theme=theme)
            if fig:
                charts.append({"title": f"Category: {ranked_cat[len(charts) % len(ranked_cat)].title()}", "badge": "CATEGORIES", "fig": fig})
        elif ranked_num:
            fig = generate_numeric_distribution_chart(active_df, ranked_num[len(charts) % len(ranked_num)], theme=theme)
            if fig:
                charts.append({"title": f"Distribution: {ranked_num[len(charts) % len(ranked_num)].title()}", "badge": "DISTRIBUTION", "fig": fig})
        else:
            break

    return {
        "perspective_id": p_meta["id"],
        "perspective_name": p_meta["name"],
        "perspective_tag": p_meta["tag"],
        "perspective_icon": p_meta["icon"],
        "perspective_desc": p_meta["desc"],
        "kpi_cards": kpi_cards[:4],
        "charts": charts[:4],
        "briefing": briefing[:3]
    }


# =============================================================================
# STANDALONE SINGLE-SCREEN HTML EXPORT GENERATOR
# =============================================================================

def export_dashboard_to_standalone_html(
    dataset_name: str,
    metadata: Dict[str, Any],
    perspective_data: Dict[str, Any],
    theme: str = "Dark"
) -> str:
    """
    Generate a complete, self-contained single-screen executive dashboard in standalone HTML.
    Includes embedded Plotly CDN scripts, glassmorphic CSS tokens, KPI scorecards,
    and responsive 2x2 grid suitable for offline viewing, emailing, and 1-page PDF printing.
    """
    is_dark = theme == "Dark"
    bg_color = "#0b1329" if is_dark else "#f8fafc"
    surface_color = "#131e3a" if is_dark else "#ffffff"
    text_primary = "#f8fafc" if is_dark else "#0f172a"
    text_secondary = "#94a3b8" if is_dark else "#475569"
    border_color = "#1e2c47" if is_dark else "#e2e8f0"
    accent_color = "#3b82f6" if is_dark else "#2563eb"

    # Convert Plotly figures to embedded HTML snippets
    chart_divs = []
    for item in perspective_data.get("charts", []):
        fig = item.get("fig")
        if fig is not None:
            html_snippet = fig.to_html(full_html=False, include_plotlyjs="cdn", config={"displayModeBar": False, "responsive": True})
            chart_divs.append({
                "title": item.get("title", "Chart"),
                "badge": item.get("badge", "VISUALIZATION"),
                "html": html_snippet
            })

    # Build KPI tiles HTML
    kpi_html_list = []
    for kpi in perspective_data.get("kpi_cards", []):
        kpi_html = f"""
        <div class="kpi-card">
            <div class="kpi-label">{kpi.get('label', '')}</div>
            <div class="kpi-value">{kpi.get('value', '')}</div>
            <div class="kpi-meta">
                <span class="kpi-badge">{kpi.get('badge', '')}</span>
                <span>{kpi.get('meta', '')}</span>
            </div>
        </div>
        """
        kpi_html_list.append(kpi_html)

    # Build Briefing HTML
    brief_html_list = []
    for b in perspective_data.get("briefing", []):
        brief_html_list.append(f"""
        <div class="brief-item">
            <span class="brief-bullet">✦</span>
            <div><strong>{b.get('title', '')}</strong>: {b.get('text', '')}</div>
        </div>
        """)

    # Build Chart Grid HTML
    charts_html_list = []
    for c in chart_divs:
        charts_html_list.append(f"""
        <div class="chart-card">
            <div class="chart-header">
                <span class="chart-title">{c['title']}</span>
                <span class="chart-badge">{c['badge']}</span>
            </div>
            <div class="chart-body">
                {c['html']}
            </div>
        </div>
        """)

    # Build Compact Briefing Ticker HTML
    brief_items_html = " &nbsp;·&nbsp; ".join([
        f"<strong>{b.get('title', '')}</strong>: {b.get('text', '')}"
        for b in perspective_data.get("briefing", [])
    ])

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Studio — {dataset_name} Executive Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        @page {{
            size: A4 landscape;
            margin: 6mm;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        html, body {{
            height: 100%;
            width: 100%;
            overflow: hidden;
            background-color: {bg_color};
            color: {text_primary};
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 13px;
        }}
        .cockpit-canvas {{
            height: 100vh;
            width: 100vw;
            display: flex;
            flex-direction: column;
            padding: 10px 14px;
            gap: 8px;
            box-sizing: border-box;
        }}
        /* 1. Header Bar */
        .cockpit-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: {surface_color};
            border: 1px solid {border_color};
            border-radius: 8px;
            padding: 8px 16px;
            height: 48px;
            flex-shrink: 0;
        }}
        .brand-title {{
            font-size: 16px;
            font-weight: 900;
            letter-spacing: -0.01em;
            color: {text_primary};
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .brand-meta {{
            font-size: 11px;
            color: {text_secondary};
            font-weight: 500;
        }}
        .header-actions {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .perspective-pill {{
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            background: rgba(59, 130, 246, 0.15);
            color: {accent_color};
            border: 1px solid rgba(59, 130, 246, 0.3);
            padding: 3px 10px;
            border-radius: 12px;
        }}
        .print-btn {{
            background: {accent_color};
            color: #ffffff;
            border: none;
            padding: 4px 12px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 11px;
            cursor: pointer;
            transition: opacity 0.15s;
        }}
        .print-btn:hover {{
            opacity: 0.9;
        }}

        /* 2. Top KPI Scorecards */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            height: 72px;
            flex-shrink: 0;
        }}
        .kpi-card {{
            background: {surface_color};
            border: 1px solid {border_color};
            border-left: 4px solid {accent_color};
            border-radius: 6px;
            padding: 8px 12px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .kpi-label {{
            font-size: 9.5px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: {text_secondary};
            line-height: 1;
        }}
        .kpi-value {{
            font-size: 20px;
            font-weight: 800;
            color: {text_primary};
            line-height: 1.1;
        }}
        .kpi-meta {{
            font-size: 10px;
            color: {text_secondary};
            display: flex;
            align-items: center;
            gap: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .kpi-badge {{
            font-size: 8.5px;
            font-weight: 700;
            padding: 1px 4px;
            border-radius: 3px;
            background: rgba(59, 130, 246, 0.12);
            color: {accent_color};
        }}

        /* 3. 2x2 Interactive Chart Grid */
        .charts-grid {{
            flex: 1;
            min-height: 0;
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 8px;
        }}
        .chart-card {{
            background: {surface_color};
            border: 1px solid {border_color};
            border-radius: 6px;
            padding: 8px 10px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            min-height: 0;
        }}
        .chart-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 4px;
            border-bottom: 1px solid {border_color};
            height: 22px;
            flex-shrink: 0;
        }}
        .chart-title {{
            font-size: 11.5px;
            font-weight: 700;
            color: {text_primary};
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .chart-badge {{
            font-size: 8.5px;
            font-weight: 700;
            text-transform: uppercase;
            color: {text_secondary};
            background: rgba(255,255,255,0.05);
            padding: 1px 5px;
            border-radius: 3px;
            border: 1px solid {border_color};
        }}
        .chart-body {{
            flex: 1;
            min-height: 0;
            width: 100%;
            height: 100%;
            position: relative;
        }}
        .chart-body .plotly-graph-div {{
            height: 100% !important;
            width: 100% !important;
        }}

        /* 4. Bottom AI Takeaways Ticker */
        .brief-bar {{
            background: {surface_color};
            border: 1px solid {border_color};
            border-radius: 6px;
            padding: 6px 14px;
            height: 34px;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 11px;
            color: {text_secondary};
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
        }}
        .brief-tag {{
            font-weight: 800;
            color: {accent_color};
            text-transform: uppercase;
            letter-spacing: 0.05em;
            flex-shrink: 0;
        }}

        /* Single-Page Print Rules */
        @media print {{
            html, body {{
                height: 100% !important;
                width: 100% !important;
                overflow: hidden !important;
                background: #ffffff !important;
                color: #0f172a !important;
            }}
            .cockpit-canvas {{
                height: 100vh !important;
                width: 100vw !important;
                padding: 4mm !important;
                gap: 4mm !important;
            }}
            .print-btn {{
                display: none !important;
            }}
            .chart-card, .kpi-card, .brief-bar, .cockpit-header {{
                border-color: #cbd5e1 !important;
                background: #ffffff !important;
                box-shadow: none !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="cockpit-canvas">
        <div class="cockpit-header">
            <div class="brand-title">
                <span>⚡ DATA STUDIO</span>
                <span class="brand-meta">· {dataset_name} ({metadata.get('total_rows', 0):,} rows × {metadata.get('total_columns', 0)} cols)</span>
            </div>
            <div class="header-actions">
                <span class="perspective-pill">{perspective_data.get('perspective_name', 'Executive Perspective')}</span>
                <button class="print-btn" onclick="window.print()">🖨 Print / PDF</button>
            </div>
        </div>

        <div class="kpi-grid">
            {''.join(kpi_html_list)}
        </div>

        <div class="charts-grid">
            {''.join(charts_html_list)}
        </div>

        <div class="brief-bar">
            <span class="brief-tag">✦ AI Briefing:</span>
            <span>{brief_items_html}</span>
        </div>
    </div>

    <script>
        // Trigger auto-resize on Plotly graphs to fill 100% of grid cells seamlessly
        window.addEventListener('resize', function() {{
            var graphs = document.querySelectorAll('.plotly-graph-div');
            graphs.forEach(function(g) {{
                Plotly.Plots.resize(g);
            }});
        }});
        setTimeout(function() {{
            var graphs = document.querySelectorAll('.plotly-graph-div');
            graphs.forEach(function(g) {{
                Plotly.Plots.resize(g);
            }});
        }}, 300);
    </script>
</body>
</html>
"""
    return html_template



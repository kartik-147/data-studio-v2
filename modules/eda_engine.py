"""
DATA STUDIO v2 — EDA Analytics Engine & Plotly Visualizations (Module 6)
=============================================================================
Modular, reusable data-processing and statistical engine decoupled from UI presentation.
Provides descriptive statistics, skewness and kurtosis interpretation,
Pearson and Spearman correlation matrices, IQR outlier detection, column deep dives,
deterministic automated EDA insights, and theme-aware Plotly charts.
Read-only analysis: NEVER mutates the underlying dataset.
"""
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from modules.data_loader import detect_column_type
from modules.dashboard_engine import apply_chart_theme, THEME_CONFIGS


# =============================================================================
# STATISTICAL INTERPRETATION HELPERS
# =============================================================================

def interpret_skewness(skew_val: Optional[float]) -> Dict[str, str]:
    """
    Interpret skewness value into standard statistical categories.
    Rules:
    - Between -0.5 and 0.5: Approximately symmetric
    - Between 0.5 and 1.0: Moderately right-skewed (positive skew)
    - Greater than 1.0: Highly right-skewed (heavy right tail)
    - Between -1.0 and -0.5: Moderately left-skewed (negative skew)
    - Less than -1.0: Highly left-skewed (heavy left tail)
    """
    if skew_val is None or pd.isna(skew_val):
        return {
            "label": "Undefined",
            "category": "neutral",
            "description": "Insufficient variance or non-null data to determine distribution symmetry.",
            "badge_class": "ds-badge-neutral"
        }
    
    if abs(skew_val) <= 0.5:
        return {
            "label": "Approximately Symmetric",
            "category": "symmetric",
            "description": "Values are evenly balanced around the central mean with minimal directional tail pull.",
            "badge_class": "ds-badge-datetime"  # green tint
        }
    elif skew_val > 1.0:
        return {
            "label": "Highly Right-Skewed",
            "category": "right_high",
            "description": "Long right-side tail with extreme high values pulling the mean above the median. Consider log or power transformations.",
            "badge_class": "ds-badge-text"  # amber tint
        }
    elif 0.5 < skew_val <= 1.0:
        return {
            "label": "Moderately Right-Skewed",
            "category": "right_mod",
            "description": "Moderate positive tail pull towards higher values.",
            "badge_class": "ds-badge-text"
        }
    elif skew_val < -1.0:
        return {
            "label": "Highly Left-Skewed",
            "category": "left_high",
            "description": "Long left-side tail with extreme low values pulling the mean below the median.",
            "badge_class": "ds-badge-text"
        }
    else:  # -1.0 <= skew_val < -0.5
        return {
            "label": "Moderately Left-Skewed",
            "category": "left_mod",
            "description": "Moderate negative tail pull towards lower values.",
            "badge_class": "ds-badge-text"
        }


def interpret_kurtosis(kurt_val: Optional[float]) -> Dict[str, str]:
    """
    Interpret Fisher excess kurtosis (where Normal distribution kurtosis = 0).
    - Kurtosis > 0.5: Leptokurtic (heavy tails, sharper peak, outlier-prone)
    - Kurtosis < -0.5: Platykurtic (light tails, flatter peak, fewer outliers)
    - -0.5 <= Kurtosis <= 0.5: Mesokurtic (similar tail weight to normal distribution)
    """
    if kurt_val is None or pd.isna(kurt_val):
        return {
            "label": "Undefined",
            "category": "neutral",
            "description": "Insufficient variance to determine tail weight.",
            "badge_class": "ds-badge-neutral"
        }
        
    if kurt_val > 0.5:
        return {
            "label": "Leptokurtic (Heavy-Tailed)",
            "category": "leptokurtic",
            "description": "Higher concentration of values in tails and sharp peak; more prone to extreme outliers.",
            "badge_class": "ds-badge-text"
        }
    elif kurt_val < -0.5:
        return {
            "label": "Platykurtic (Light-Tailed)",
            "category": "platykurtic",
            "description": "Flatter peak with thinner tails and fewer extreme values than a normal distribution.",
            "badge_class": "ds-badge-numeric"
        }
    else:
        return {
            "label": "Mesokurtic (Normal Tails)",
            "category": "mesokurtic",
            "description": "Tail weight and peak sharpness are comparable to a standard normal distribution.",
            "badge_class": "ds-badge-datetime"
        }


# =============================================================================
# SUMMARY STATISTICS COMPUTATION
# =============================================================================

def compute_summary_statistics(df: pd.DataFrame, numeric_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Compute comprehensive descriptive statistics for numeric columns.
    Includes: Count, Mean, Median, Std Dev, Min, 25%, 50%, 75%, Max, Skewness, Kurtosis, Missing %.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    if numeric_cols is None:
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]

    if not numeric_cols:
        return pd.DataFrame()

    records = []
    for col in numeric_cols:
        s = df[col].dropna()
        total_len = len(df[col])
        valid_cnt = len(s)
        missing_cnt = total_len - valid_cnt
        missing_pct = (missing_cnt / total_len * 100) if total_len > 0 else 0.0

        if valid_cnt == 0:
            records.append({
                "Column": col,
                "Count": 0,
                "Mean": np.nan,
                "Median": np.nan,
                "Std Dev": np.nan,
                "Min": np.nan,
                "25% (Q1)": np.nan,
                "50% (Q2)": np.nan,
                "75% (Q3)": np.nan,
                "Max": np.nan,
                "Skewness": np.nan,
                "Kurtosis": np.nan,
                "Missing %": missing_pct
            })
            continue

        mean_val = float(s.mean())
        median_val = float(s.median())
        std_val = float(s.std()) if valid_cnt > 1 else 0.0
        min_val = float(s.min())
        q25 = float(s.quantile(0.25))
        q50 = median_val
        q75 = float(s.quantile(0.75))
        max_val = float(s.max())

        # Skewness & Fisher excess kurtosis
        skew_val = float(s.skew()) if valid_cnt >= 3 and std_val > 0 else 0.0
        kurt_val = float(s.kurtosis()) if valid_cnt >= 4 and std_val > 0 else 0.0

        records.append({
            "Column": col,
            "Count": valid_cnt,
            "Mean": mean_val,
            "Median": median_val,
            "Std Dev": std_val,
            "Min": min_val,
            "25% (Q1)": q25,
            "50% (Q2)": q50,
            "75% (Q3)": q75,
            "Max": max_val,
            "Skewness": skew_val,
            "Kurtosis": kurt_val,
            "Missing %": missing_pct
        })

    summary_df = pd.DataFrame(records)
    return summary_df


# =============================================================================
# CORRELATION ANALYSIS
# =============================================================================

def compute_correlation_matrix(
    df: pd.DataFrame,
    numeric_cols: Optional[List[str]] = None,
    method: str = "pearson"
) -> pd.DataFrame:
    """
    Compute pairwise correlation matrix for numeric columns using Pearson or Spearman.
    Safely ignores non-numeric columns and constant columns with zero variance.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    if numeric_cols is None:
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]

    if len(numeric_cols) < 2:
        return pd.DataFrame()

    # Filter out columns with zero variance or all nulls
    usable_cols = []
    for col in numeric_cols:
        s = df[col].dropna()
        if len(s) > 1 and s.nunique() > 1:
            usable_cols.append(col)

    if len(usable_cols) < 2:
        return pd.DataFrame()

    sub_df = df[usable_cols]
    corr = sub_df.corr(method=method.lower())
    return corr


def extract_strongest_correlations(
    corr_matrix: pd.DataFrame,
    top_n: int = 5
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Extract the strongest positive and strongest negative correlation pairs
    (excluding diagonal self-correlations r=1.0).
    """
    if corr_matrix.empty or len(corr_matrix.columns) < 2:
        return [], []

    cols = list(corr_matrix.columns)
    pairs = []
    seen = set()

    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            col1 = cols[i]
            col2 = cols[j]
            val = corr_matrix.loc[col1, col2]
            if pd.notna(val):
                pair_key = tuple(sorted([col1, col2]))
                if pair_key not in seen:
                    seen.add(pair_key)
                    pairs.append({
                        "Variable 1": col1,
                        "Variable 2": col2,
                        "Correlation (r)": float(val),
                        "Abs Correlation": abs(float(val)),
                        "Strength": _classify_correlation_strength(float(val))
                    })

    if not pairs:
        return [], []

    # Sort for positive correlations
    pos_pairs = sorted([p for p in pairs if p["Correlation (r)"] > 0], key=lambda x: x["Correlation (r)"], reverse=True)
    # Sort for negative correlations
    neg_pairs = sorted([p for p in pairs if p["Correlation (r)"] < 0], key=lambda x: x["Correlation (r)"])

    return pos_pairs[:top_n], neg_pairs[:top_n]


def _classify_correlation_strength(r_val: float) -> str:
    """Classify correlation strength coefficient into intuitive descriptive label."""
    abs_r = abs(r_val)
    if abs_r >= 0.85:
        return "Very Strong"
    elif abs_r >= 0.70:
        return "Strong"
    elif abs_r >= 0.50:
        return "Moderate"
    elif abs_r >= 0.30:
        return "Weak"
    else:
        return "Negligible"


# =============================================================================
# IQR OUTLIER DETECTION
# =============================================================================

def compute_iqr_outliers(
    df: pd.DataFrame,
    numeric_cols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Perform rigorous Interquartile Range (IQR) outlier detection across numeric features.
    Lower Bound = Q1 - 1.5 * IQR
    Upper Bound = Q3 + 1.5 * IQR
    """
    if df is None or df.empty:
        return {
            "summary_df": pd.DataFrame(),
            "total_outliers": 0,
            "overall_outlier_rate": 0.0,
            "affected_columns_count": 0,
            "column_outliers": {}
        }

    if numeric_cols is None:
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]

    summary_records = []
    column_outliers_map = {}
    total_outliers_count = 0
    total_evaluated_cells = 0

    for col in numeric_cols:
        series = df[col].dropna()
        n_valid = len(series)
        total_evaluated_cells += n_valid

        if n_valid < 4:
            continue

        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_mask = (series < lower_bound) | (series > upper_bound)
        outlier_series = series[outlier_mask]
        outlier_count = int(outlier_mask.sum())
        outlier_pct = float(outlier_count / n_valid * 100) if n_valid > 0 else 0.0

        total_outliers_count += outlier_count

        status = "Clean"
        if outlier_pct > 5.0:
            status = "High Outlier Burden"
        elif outlier_pct > 0.0:
            status = "Moderate Outliers"

        summary_records.append({
            "Column": col,
            "Non-Null Count": n_valid,
            "Q1 (25%)": q1,
            "Q3 (75%)": q3,
            "IQR": iqr,
            "Lower Bound": lower_bound,
            "Upper Bound": upper_bound,
            "Outlier Count": outlier_count,
            "Outlier %": outlier_pct,
            "Min Value": float(series.min()),
            "Max Value": float(series.max()),
            "Status": status
        })

        # Save details for single column inspector
        column_outliers_map[col] = {
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "outlier_count": outlier_count,
            "outlier_pct": outlier_pct,
            "outlier_indices": outlier_series.index.tolist(),
            "outlier_values": outlier_series.tolist(),
            "min": float(series.min()),
            "max": float(series.max())
        }

    summary_df = pd.DataFrame(summary_records)
    if not summary_df.empty:
        summary_df = summary_df.sort_values(by=["Outlier Count", "Outlier %"], ascending=False).reset_index(drop=True)

    affected_cols_count = sum(1 for c in column_outliers_map.values() if c["outlier_count"] > 0)
    overall_rate = (total_outliers_count / total_evaluated_cells * 100) if total_evaluated_cells > 0 else 0.0

    return {
        "summary_df": summary_df,
        "total_outliers": total_outliers_count,
        "overall_outlier_rate": overall_rate,
        "affected_columns_count": affected_cols_count,
        "column_outliers": column_outliers_map
    }


# =============================================================================
# COLUMN DEEP DIVE ANALYSIS
# =============================================================================

def analyze_column_deep_dive(
    df: pd.DataFrame,
    col_name: str,
    detected_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform deep statistical profiling for a single selected dataset column.
    Handles Numeric, Categorical, Date/Time, Boolean, and Text data types.
    """
    if df is None or df.empty or col_name not in df.columns:
        return {}

    series = df[col_name]
    total_rows = len(df)
    non_null_series = series.dropna()
    non_null_count = len(non_null_series)
    missing_count = total_rows - non_null_count
    missing_pct = (missing_count / total_rows * 100) if total_rows > 0 else 0.0

    unique_count = int(series.nunique(dropna=True))
    unique_pct = (unique_count / non_null_count * 100) if non_null_count > 0 else 0.0

    if detected_type is None:
        detected_type = detect_column_type(series, col_name, total_rows)

    base_profile = {
        "column_name": col_name,
        "detected_type": detected_type,
        "total_rows": total_rows,
        "non_null_count": non_null_count,
        "missing_count": missing_count,
        "missing_percentage": missing_pct,
        "unique_count": unique_count,
        "unique_percentage": unique_pct,
        "is_constant": unique_count == 1,
        "is_unique_identifier": unique_count == total_rows and total_rows > 1
    }

    # 1. Numeric Deep Dive
    if detected_type == "Numeric" or pd.api.types.is_numeric_dtype(series):
        if non_null_count > 0:
            num_s = pd.to_numeric(non_null_series, errors="coerce").dropna()
            mean_val = float(num_s.mean())
            median_val = float(num_s.median())
            std_val = float(num_s.std()) if len(num_s) > 1 else 0.0
            var_val = float(num_s.var()) if len(num_s) > 1 else 0.0
            min_val = float(num_s.min())
            max_val = float(num_s.max())
            val_range = max_val - min_val

            q1 = float(num_s.quantile(0.25))
            q3 = float(num_s.quantile(0.75))
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outlier_count = int(((num_s < lower_bound) | (num_s > upper_bound)).sum())

            skew_val = float(num_s.skew()) if len(num_s) >= 3 and std_val > 0 else 0.0
            kurt_val = float(num_s.kurtosis()) if len(num_s) >= 4 and std_val > 0 else 0.0

            quantiles = {
                "1%": float(num_s.quantile(0.01)),
                "5%": float(num_s.quantile(0.05)),
                "25% (Q1)": q1,
                "50% (Median)": median_val,
                "75% (Q3)": q3,
                "95%": float(num_s.quantile(0.95)),
                "99%": float(num_s.quantile(0.99))
            }

            base_profile.update({
                "mean": mean_val,
                "median": median_val,
                "std": std_val,
                "variance": var_val,
                "min": min_val,
                "max": max_val,
                "range": val_range,
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "outlier_count": outlier_count,
                "skewness": skew_val,
                "kurtosis": kurt_val,
                "quantiles": quantiles,
                "skew_interpretation": interpret_skewness(skew_val),
                "kurt_interpretation": interpret_kurtosis(kurt_val)
            })

    # 2. Categorical / Boolean / Text Deep Dive
    elif detected_type in ["Categorical", "Boolean", "Text"]:
        val_counts = non_null_series.astype(str).value_counts()
        top_counts = val_counts.head(15)
        
        freq_records = []
        for val, count in top_counts.items():
            pct = (count / non_null_count * 100) if non_null_count > 0 else 0.0
            freq_records.append({
                "Value": str(val),
                "Count": int(count),
                "Percentage (%)": float(pct)
            })
        
        base_profile.update({
            "frequency_table": pd.DataFrame(freq_records),
            "top_value": str(val_counts.index[0]) if len(val_counts) > 0 else None,
            "top_value_count": int(val_counts.iloc[0]) if len(val_counts) > 0 else 0,
            "top_value_pct": float(val_counts.iloc[0] / non_null_count * 100) if non_null_count > 0 and len(val_counts) > 0 else 0.0
        })

    # 3. Date/Time Deep Dive
    elif detected_type == "Date/Time":
        try:
            dt_series = pd.to_datetime(non_null_series, errors="coerce").dropna()
            if not dt_series.empty:
                min_date = dt_series.min()
                max_date = dt_series.max()
                date_span_days = (max_date - min_date).days

                base_profile.update({
                    "min_date": min_date.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(min_date) else "N/A",
                    "max_date": max_date.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(max_date) else "N/A",
                    "date_span_days": date_span_days,
                    "date_span_formatted": f"{date_span_days:,} days (~{date_span_days/365.25:.1f} years)" if date_span_days > 365 else f"{date_span_days:,} days",
                    "dt_series": dt_series
                })
        except Exception:
            pass

    return base_profile


# =============================================================================
# DETERMINISTIC AUTOMATED EDA INSIGHTS
# =============================================================================

def generate_eda_insights(df: pd.DataFrame, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Generate deterministic, rule-based analytics observations and actionable findings
    derived strictly from mathematical dataset statistics (zero hallucinated/fake AI text).
    """
    if df is None or df.empty:
        return []

    insights: List[Dict[str, Any]] = []
    total_rows = len(df)
    total_cols = len(df.columns)

    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]

    # 1. Missing Value Observations
    missing_series = df.isna().sum()
    high_missing = missing_series[missing_series / total_rows > 0.20]
    crit_missing = missing_series[missing_series / total_rows > 0.50]

    if len(crit_missing) > 0:
        col_names = ", ".join([f"'{c}' ({missing_series[c]/total_rows*100:.1f}%)" for c in crit_missing.index[:3]])
        insights.append({
            "category": "Missing Data",
            "severity": "CRITICAL",
            "variant": "error",
            "title": f"{len(crit_missing)} Column(s) Have Severe Missing Rates (>50%)",
            "observation": f"Features with severe null rates: {col_names}. Imputation may distort underlying patterns; consider feature removal or domain-specific default filling."
        })
    elif len(high_missing) > 0:
        col_names = ", ".join([f"'{c}' ({missing_series[c]/total_rows*100:.1f}%)" for c in high_missing.index[:3]])
        insights.append({
            "category": "Missing Data",
            "severity": "WARNING",
            "variant": "warning",
            "title": f"{len(high_missing)} Column(s) Have Elevated Missingness (>20%)",
            "observation": f"Features {col_names} contain notable missing values that should be handled during preparation."
        })
    else:
        insights.append({
            "category": "Completeness",
            "severity": "POSITIVE",
            "variant": "success",
            "title": "High Data Completeness",
            "observation": f"All {total_cols} columns have high data completeness (<20% missing values across all features)."
        })

    # 2. Correlation & Multicollinearity Observations
    if len(numeric_cols) >= 2:
        corr_matrix = compute_correlation_matrix(df, numeric_cols, method="pearson")
        pos_pairs, neg_pairs = extract_strongest_correlations(corr_matrix, top_n=5)

        high_pos = [p for p in pos_pairs if p["Correlation (r)"] >= 0.75]
        high_neg = [p for p in neg_pairs if p["Correlation (r)"] <= -0.75]

        if high_pos:
            top_pair = high_pos[0]
            insights.append({
                "category": "Correlation",
                "severity": "STRONG CORRELATION",
                "variant": "info",
                "title": f"Strong Positive Linear Relationship: {top_pair['Variable 1']} ↔ {top_pair['Variable 2']} (r = {top_pair['Correlation (r)']:.2f})",
                "observation": f"Variables '{top_pair['Variable 1']}' and '{top_pair['Variable 2']}' exhibit a {top_pair['Strength'].lower()} positive correlation. In regression modeling, verify whether one feature is redundant or causing multicollinearity."
            })

        if high_neg:
            top_neg = high_neg[0]
            insights.append({
                "category": "Correlation",
                "severity": "INVERSE CORRELATION",
                "variant": "info",
                "title": f"Strong Negative Relationship: {top_neg['Variable 1']} ↔ {top_neg['Variable 2']} (r = {top_neg['Correlation (r)']:.2f})",
                "observation": f"Variables '{top_neg['Variable 1']}' and '{top_neg['Variable 2']}' move inversely with a correlation coefficient of {top_neg['Correlation (r)']:.2f}."
            })

    # 3. Distribution & Skewness Observations
    skewed_cols = []
    for col in numeric_cols:
        s = df[col].dropna()
        if len(s) >= 4 and s.std() > 0:
            sk = s.skew()
            if abs(sk) > 1.5:
                skewed_cols.append((col, sk))

    if skewed_cols:
        skewed_cols.sort(key=lambda x: abs(x[1]), reverse=True)
        top_skew_col, top_skew_val = skewed_cols[0]
        direction = "right (positive)" if top_skew_val > 0 else "left (negative)"
        insights.append({
            "category": "Distribution",
            "severity": "HIGH SKEWNESS",
            "variant": "warning",
            "title": f"Highly Asymmetric Distribution in '{top_skew_col}' (Skewness = {top_skew_val:.2f})",
            "observation": f"Feature '{top_skew_col}' is heavily skewed towards the {direction}. Algorithms assuming normal distribution (e.g. Linear Models, PCA) will benefit from log, square-root, or Box-Cox transformation."
        })

    # 4. Outlier Burden Observations
    outliers_data = compute_iqr_outliers(df, numeric_cols)
    outlier_df = outliers_data["summary_df"]
    if not outlier_df.empty:
        high_outliers = outlier_df[outlier_df["Outlier %"] > 5.0]
        if not high_outliers.empty:
            top_outlier = high_outliers.iloc[0]
            insights.append({
                "category": "Outliers",
                "severity": "OUTLIER BURDEN",
                "variant": "warning",
                "title": f"Elevated Outlier Concentration in '{top_outlier['Column']}' ({top_outlier['Outlier Count']} records, {top_outlier['Outlier %']:.1f}%)",
                "observation": f"Column '{top_outlier['Column']}' contains {top_outlier['Outlier Count']} records outside the 1.5×IQR boundary [{top_outlier['Lower Bound']:.2f}, {top_outlier['Upper Bound']:.2f}]."
            })

    # 5. Cardinality & Single Constant Columns
    constant_cols = []
    high_cardinality_cols = []
    for col in df.columns:
        valid_s = df[col].dropna()
        n_valid = len(valid_s)
        if n_valid == 0:
            continue
        n_unique = valid_s.nunique()
        if n_unique == 1:
            constant_cols.append(col)
        elif n_valid > 30 and (n_unique / n_valid > 0.85) and not pd.api.types.is_numeric_dtype(df[col]):
            high_cardinality_cols.append(col)

    if constant_cols:
        insights.append({
            "category": "Schema Quality",
            "severity": "ZERO VARIANCE",
            "variant": "warning",
            "title": f"{len(constant_cols)} Constant Column(s) Detected",
            "observation": f"Columns {constant_cols} have identical single values across all rows, offering zero predictive variance."
        })

    if high_cardinality_cols:
        insights.append({
            "category": "Cardinality",
            "severity": "HIGH CARDINALITY",
            "variant": "info",
            "title": f"High Cardinality in {len(high_cardinality_cols)} Categorical Feature(s)",
            "observation": f"Features {high_cardinality_cols[:3]} exhibit near-unique values (>85% unique), indicating they likely represent IDs, transactional timestamps, or free text."
        })

    # 6. Duplication Check
    dup_rows = int(df.duplicated().sum())
    if dup_rows > 0:
        dup_pct = (dup_rows / total_rows * 100)
        insights.append({
            "category": "Uniqueness",
            "severity": "DUPLICATES",
            "variant": "warning" if dup_pct > 2.0 else "info",
            "title": f"{dup_rows:,} Duplicate Row(s) Detected ({dup_pct:.1f}%)",
            "observation": f"Identical records detected in the active dataset. Ensure these represent legitimate repeated transactions rather than accidental data collection duplicates."
        })

    return insights


# =============================================================================
# THEME-AWARE PLOTLY CHART BUILDERS
# =============================================================================

def generate_correlation_heatmap(
    corr_matrix: pd.DataFrame,
    method: str = "Pearson",
    theme: str = "Dark",
    height: int = 420
) -> Optional[go.Figure]:
    """
    Generate an interactive, theme-aligned correlation matrix heatmap with annotations.
    """
    if corr_matrix.empty or len(corr_matrix.columns) < 2:
        return None

    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
    cols = list(corr_matrix.columns)
    z_vals = corr_matrix.values

    # Clean text matrix for formatted annotations
    text_matrix = []
    for row in z_vals:
        text_row = []
        for v in row:
            if pd.isna(v):
                text_row.append("—")
            else:
                text_row.append(f"{v:.2f}")
        text_matrix.append(text_row)

    # Colorscale: Diverging blue-white-red or clean corporate blue-gray
    colorscale = [
        [0.0, "#ef4444" if theme == "Dark" else "#dc2626"],   # -1.0 (Strong Negative)
        [0.5, "#1e293b" if theme == "Dark" else "#f1f5f9"],   #  0.0 (No Correlation)
        [1.0, "#3b82f6" if theme == "Dark" else "#2563eb"]    # +1.0 (Strong Positive)
    ]

    fig = go.Figure(data=go.Heatmap(
        z=z_vals,
        x=cols,
        y=cols,
        text=text_matrix,
        texttemplate="%{text}",
        textfont={"size": 11, "family": "Inter, sans-serif", "color": "#f8fafc" if theme == "Dark" else "#0f172a"},
        colorscale=colorscale,
        zmin=-1.0,
        zmax=1.0,
        colorbar=dict(
            title=dict(text="r", font=dict(color=cfg["text"], size=12)),
            tickfont=dict(color=cfg["text"], size=10),
            len=0.9,
            thickness=14
        ),
        hovertemplate="<b>%{y}</b> ↔ <b>%{x}</b><br>Correlation (" + method + "): <b>%{z:.3f}</b><extra></extra>"
    ))

    fig = apply_chart_theme(fig, theme=theme, height=height, show_legend=False)
    fig.update_xaxes(side="bottom", tickangle=-35, tickfont=dict(size=11))
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=11))
    return fig


def generate_distribution_histogram(
    series: pd.Series,
    col_name: str,
    nbins: int = 30,
    show_mean_median: bool = True,
    theme: str = "Dark",
    height: int = 340
) -> go.Figure:
    """
    Generate an interactive histogram with kernel density estimation approximation
    and mean/median reference lines.
    """
    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
    clean_s = series.dropna()

    fig = go.Figure()

    if clean_s.empty:
        return fig

    # Histogram trace
    fig.add_trace(go.Histogram(
        x=clean_s,
        nbinsx=nbins,
        name="Frequency",
        marker=dict(
            color=cfg["primary"],
            line=dict(color="#1e293b" if theme == "Dark" else "#ffffff", width=1)
        ),
        opacity=0.85,
        hovertemplate="Range: <b>%{x}</b><br>Count: <b>%{y:,}</b><extra></extra>"
    ))

    # Mean and Median reference lines
    if show_mean_median and len(clean_s) > 0:
        mean_val = float(clean_s.mean())
        median_val = float(clean_s.median())

        fig.add_vline(
            x=mean_val,
            line_width=2,
            line_dash="dash",
            line_color="#f59e0b",
            annotation_text=f"Mean: {mean_val:.2f}",
            annotation_position="top right",
            annotation_font=dict(color="#f59e0b", size=11, family="Inter")
        )
        fig.add_vline(
            x=median_val,
            line_width=2,
            line_dash="dot",
            line_color="#10b981",
            annotation_text=f"Median: {median_val:.2f}",
            annotation_position="top left",
            annotation_font=dict(color="#10b981", size=11, family="Inter")
        )

    fig = apply_chart_theme(fig, theme=theme, title=f"Distribution of {col_name}", height=height, show_legend=False)
    fig.update_xaxes(title_text=col_name, gridcolor=cfg["grid"])
    fig.update_yaxes(title_text="Count", gridcolor=cfg["grid"])
    return fig


def generate_distribution_boxplot(
    series: pd.Series,
    col_name: str,
    theme: str = "Dark",
    height: int = 340
) -> go.Figure:
    """
    Generate an interactive Box and Whisker plot highlighting median, IQR, and outliers.
    """
    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
    clean_s = series.dropna()

    fig = go.Figure()

    if clean_s.empty:
        return fig

    fig.add_trace(go.Box(
        y=clean_s,
        name=col_name,
        boxpoints="outliers",
        jitter=0.25,
        pointpos=-1.8,
        marker=dict(
            color="#ec4899" if theme == "Dark" else "#db2777",
            size=5,
            opacity=0.75
        ),
        line=dict(color=cfg["primary"], width=2),
        fillcolor="rgba(59, 130, 246, 0.2)" if theme == "Dark" else "rgba(37, 99, 235, 0.15)",
        hovertemplate="Value: <b>%{y}</b><extra></extra>"
    ))

    fig = apply_chart_theme(fig, theme=theme, title=f"Box Plot: {col_name}", height=height, show_legend=False)
    fig.update_yaxes(title_text=col_name, gridcolor=cfg["grid"])
    return fig


def generate_outlier_inspector_chart(
    series: pd.Series,
    col_name: str,
    lower_bound: float,
    upper_bound: float,
    theme: str = "Dark",
    height: int = 360
) -> go.Figure:
    """
    Generate an annotated Box Plot with upper and lower IQR threshold boundary lines.
    """
    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
    clean_s = series.dropna()

    fig = go.Figure()

    if clean_s.empty:
        return fig

    # Box Plot trace
    fig.add_trace(go.Box(
        x=clean_s,
        name=col_name,
        boxpoints="all",
        jitter=0.3,
        pointpos=-1.5,
        marker=dict(
            color=cfg["palette"][1],
            size=5,
            opacity=0.6
        ),
        line=dict(color=cfg["primary"], width=2),
        fillcolor="rgba(59, 130, 246, 0.15)",
        hovertemplate="Value: <b>%{x}</b><extra></extra>"
    ))

    # Upper and Lower bound lines
    fig.add_vline(
        x=lower_bound,
        line_width=2,
        line_dash="dash",
        line_color="#ef4444",
        annotation_text=f"Lower Bound: {lower_bound:.2f}",
        annotation_position="top left",
        annotation_font=dict(color="#ef4444", size=10)
    )
    fig.add_vline(
        x=upper_bound,
        line_width=2,
        line_dash="dash",
        line_color="#ef4444",
        annotation_text=f"Upper Bound: {upper_bound:.2f}",
        annotation_position="top right",
        annotation_font=dict(color="#ef4444", size=10)
    )

    fig = apply_chart_theme(fig, theme=theme, title=f"Outlier Threshold Inspection: {col_name}", height=height, show_legend=False)
    fig.update_xaxes(title_text=col_name, gridcolor=cfg["grid"])
    return fig


def generate_categorical_barchart(
    freq_df: pd.DataFrame,
    col_name: str,
    theme: str = "Dark",
    height: int = 340
) -> Optional[go.Figure]:
    """
    Generate a clean horizontal bar chart for top categorical value frequencies.
    """
    if freq_df.empty:
        return None

    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
    df_sorted = freq_df.sort_values(by="Count", ascending=True)

    fig = go.Figure(data=go.Bar(
        x=df_sorted["Count"],
        y=df_sorted["Value"].astype(str),
        orientation="h",
        marker=dict(
            color=cfg["primary"],
            line=dict(color=cfg["primary"], width=1)
        ),
        text=df_sorted.apply(lambda r: f"{r['Count']:,} ({r['Percentage (%)']:.1f}%)", axis=1),
        textposition="auto",
        textfont=dict(size=11, color="#ffffff" if theme == "Dark" else "#0f172a"),
        hovertemplate="Category: <b>%{y}</b><br>Count: <b>%{x:,}</b><extra></extra>"
    ))

    fig = apply_chart_theme(fig, theme=theme, title=f"Frequency Breakdown: {col_name}", height=height, show_legend=False)
    fig.update_xaxes(title_text="Count", gridcolor=cfg["grid"])
    fig.update_yaxes(title_text="", gridcolor=cfg["grid"])
    return fig


def generate_datetime_timeline_chart(
    dt_series: pd.Series,
    col_name: str,
    theme: str = "Dark",
    height: int = 340
) -> Optional[go.Figure]:
    """
    Generate an aggregate frequency timeline for datetime features.
    """
    if dt_series.empty:
        return None

    cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
    
    # Resample frequency based on span
    span_days = (dt_series.max() - dt_series.min()).days
    if span_days > 730:
        freq_rule = "YE" if hasattr(pd, "Grouper") else "Y"
    elif span_days > 90:
        freq_rule = "ME" if hasattr(pd, "Grouper") else "M"
    else:
        freq_rule = "D"

    try:
        time_counts = dt_series.dt.to_period(freq_rule).value_counts().sort_index()
        x_dates = [str(p) for p in time_counts.index]
        y_counts = time_counts.values

        fig = go.Figure(data=go.Bar(
            x=x_dates,
            y=y_counts,
            marker=dict(color=cfg["primary"]),
            hovertemplate="Date Interval: <b>%{x}</b><br>Record Count: <b>%{y:,}</b><extra></extra>"
        ))

        fig = apply_chart_theme(fig, theme=theme, title=f"Temporal Event Distribution: {col_name}", height=height, show_legend=False)
        fig.update_xaxes(title_text="Time Period", tickangle=-35, gridcolor=cfg["grid"])
        fig.update_yaxes(title_text="Record Count", gridcolor=cfg["grid"])
        return fig
    except Exception:
        return None

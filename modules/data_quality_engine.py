"""
DATA STUDIO v2 — Data Quality Engine (Module 4)
=============================================================================
Comprehensive deterministic data health auditing, multi-dimensional quality
scoring, type consistency analysis, outlier detection, and actionable issue tracking.
Read-only analysis: NEVER mutates the underlying dataset.
"""
from typing import Optional, Dict, Any, List, Tuple
import re
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from modules.dashboard_engine import apply_chart_theme, THEME_CONFIGS
from modules.data_loader import detect_column_type

# Common ID and contextual keywords
ID_KEYWORDS = re.compile(
    r"(?:^|_)(?:id|key|code|sku|uuid|guid|ssn|ein|zip|postal|phone|isbn|account_no|order_id|customer_id|user_id|employee_id|item_id|product_id|trans_id|transaction_id)$",
    re.IGNORECASE
)

NON_NEGATIVE_KEYWORDS = re.compile(
    r"(?:^|_)(?:age|count|quantity|qty|volume|size|days|hours|minutes|seconds|inventory|stock|years|months)$",
    re.IGNORECASE
)

PERCENTAGE_KEYWORDS = re.compile(
    r"(?:^|_)(?:pct|percent|percentage|rate|discount_pct|share|ratio)$",
    re.IGNORECASE
)


# =============================================================================
# DATA QUALITY AUDITING & METRICS
# =============================================================================

def get_missing_severity(missing_pct: float) -> str:
    """Return categorical severity based on missing percentage."""
    if missing_pct == 0:
        return "Healthy"
    elif missing_pct <= 5.0:
        return "Low"
    elif missing_pct <= 20.0:
        return "Moderate"
    elif missing_pct <= 50.0:
        return "High"
    else:
        return "Critical"


def analyze_missing_values(df: pd.DataFrame) -> Dict[str, Any]:
    """Inspect missingness across all features and assign severity tiers."""
    total_rows = len(df)
    total_cols = len(df.columns)
    total_cells = total_rows * total_cols
    
    missing_series = df.isna().sum()
    total_missing_cells = int(missing_series.sum())
    overall_missing_pct = float((total_missing_cells / total_cells * 100)) if total_cells > 0 else 0.0
    cols_affected = int((missing_series > 0).sum())

    column_details = []
    for col in df.columns:
        cnt = int(missing_series[col])
        pct = float((cnt / total_rows * 100)) if total_rows > 0 else 0.0
        non_null_cnt = total_rows - cnt
        severity = get_missing_severity(pct)

        column_details.append({
            "column_name": str(col),
            "missing_count": cnt,
            "missing_percentage": pct,
            "non_missing_count": non_null_cnt,
            "severity": severity
        })

    # Sort so most affected columns appear first
    column_details.sort(key=lambda x: x["missing_percentage"], reverse=True)

    return {
        "total_missing_cells": total_missing_cells,
        "missing_percentage": overall_missing_pct,
        "columns_affected_count": cols_affected,
        "column_missing_details": column_details
    }


def analyze_duplicates(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect row-level exact duplicates and identical column pairs."""
    total_rows = len(df)
    duplicate_rows_count = int(df.duplicated().sum())
    dup_pct = float((duplicate_rows_count / total_rows * 100)) if total_rows > 0 else 0.0
    unique_rows_count = total_rows - duplicate_rows_count

    # Extract duplicate rows if present
    duplicate_samples = None
    if duplicate_rows_count > 0:
        duplicate_samples = df[df.duplicated(keep=False)]

    # Detect duplicate columns (identical values across distinct column headers)
    duplicate_columns = []
    cols = list(df.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            c1, c2 = cols[i], cols[j]
            try:
                if df[c1].equals(df[c2]):
                    duplicate_columns.append((str(c1), str(c2)))
            except Exception:
                pass

    return {
        "total_rows": total_rows,
        "duplicate_rows": duplicate_rows_count,
        "unique_rows": unique_rows_count,
        "duplicate_percentage": dup_pct,
        "duplicate_columns": duplicate_columns,
        "duplicate_samples": duplicate_samples
    }


def analyze_consistency_and_structure(df: pd.DataFrame) -> Dict[str, Any]:
    """Audit schema health: empty columns, constant features, type anomalies, and high cardinality."""
    total_rows = len(df)
    
    empty_columns = []
    constant_columns = []
    type_inconsistencies = []
    high_cardinality_columns = []

    for col in df.columns:
        series = df[col]
        col_str = str(col)
        non_null_series = series.dropna()
        non_null_cnt = len(non_null_series)
        unique_cnt = int(series.nunique(dropna=True))
        is_id = bool(ID_KEYWORDS.search(col_str))

        # 1. Empty Column
        if non_null_cnt == 0:
            empty_columns.append(col_str)
            continue

        # 2. Constant Column (only 1 distinct value)
        if unique_cnt == 1 and total_rows > 1:
            val_sample = str(non_null_series.iloc[0])
            constant_columns.append({
                "column": col_str,
                "constant_value": val_sample,
                "non_null_count": non_null_cnt
            })

        # 3. High Cardinality Check
        unique_pct = (unique_cnt / total_rows * 100) if total_rows > 0 else 0.0
        if unique_cnt > 50 and unique_pct >= 85.0 and not is_id:
            high_cardinality_columns.append({
                "column": col_str,
                "unique_count": unique_cnt,
                "unique_percentage": unique_pct,
                "is_id": is_id
            })

        # 4. Type Inconsistencies
        # If object column, check if contains mixed types (e.g. mix of numeric strings and text)
        if pd.api.types.is_object_dtype(series) and non_null_cnt > 0:
            str_series = non_null_series.astype(str).str.strip()
            
            # Check if largely numeric with some unparseable text
            numeric_parsed = pd.to_numeric(str_series, errors="coerce")
            num_valid_ratio = numeric_parsed.notna().mean()
            
            if 0.15 < num_valid_ratio < 0.98 and non_null_cnt >= 10:
                inconsistent_mask = numeric_parsed.isna()
                inconsistent_cnt = int(inconsistent_mask.sum())
                inconsistent_pct = float((inconsistent_cnt / non_null_cnt * 100))
                samples = str_series[inconsistent_mask].head(3).tolist()
                
                type_inconsistencies.append({
                    "column": col_str,
                    "issue": "Mixed Numeric & Text Values",
                    "inconsistent_count": inconsistent_cnt,
                    "inconsistent_percentage": inconsistent_pct,
                    "sample_values": ", ".join(samples) if samples else "—"
                })

    return {
        "empty_columns": empty_columns,
        "constant_columns": constant_columns,
        "type_inconsistencies": type_inconsistencies,
        "high_cardinality_columns": high_cardinality_columns
    }


def analyze_validity(df: pd.DataFrame) -> Dict[str, Any]:
    """Conservative detection of invalid or suspicious values."""
    total_rows = len(df)
    invalid_findings = []
    total_invalid_cells = 0

    for col in df.columns:
        series = df[col]
        col_str = str(col)
        col_lower = col_str.lower()
        non_null_series = series.dropna()

        if len(non_null_series) == 0:
            continue

        # 1. Empty or whitespace-only strings in object columns
        if pd.api.types.is_object_dtype(series):
            str_s = non_null_series.astype(str)
            whitespace_mask = (str_s == "") | (str_s.str.strip() == "")
            ws_cnt = int(whitespace_mask.sum())
            if ws_cnt > 0:
                ws_pct = (ws_cnt / total_rows) * 100
                invalid_findings.append({
                    "column": col_str,
                    "issue_type": "Whitespace / Blank Strings",
                    "count": ws_cnt,
                    "percentage": ws_pct,
                    "severity": "LOW" if ws_pct < 5 else "MEDIUM",
                    "description": f"{ws_cnt:,} blank or whitespace-only strings detected."
                })
                total_invalid_cells += ws_cnt

        # 2. Infinite numeric values
        if pd.api.types.is_numeric_dtype(series):
            inf_mask = np.isinf(non_null_series)
            inf_cnt = int(inf_mask.sum())
            if inf_cnt > 0:
                inf_pct = (inf_cnt / total_rows) * 100
                invalid_findings.append({
                    "column": col_str,
                    "issue_type": "Infinite Numeric Values",
                    "count": inf_cnt,
                    "percentage": inf_pct,
                    "severity": "HIGH",
                    "description": f"{inf_cnt:,} infinite values (+inf / -inf) found."
                })
                total_invalid_cells += inf_cnt

            # 3. Negative values in columns expected to be non-negative (e.g. Age, Quantity)
            if NON_NEGATIVE_KEYWORDS.search(col_lower) and not bool(ID_KEYWORDS.search(col_lower)):
                neg_mask = non_null_series < 0
                neg_cnt = int(neg_mask.sum())
                if neg_cnt > 0:
                    neg_pct = (neg_cnt / total_rows) * 100
                    invalid_findings.append({
                        "column": col_str,
                        "issue_type": "Unexpected Negative Values",
                        "count": neg_cnt,
                        "percentage": neg_pct,
                        "severity": "HIGH" if "age" in col_lower else "MEDIUM",
                        "description": f"{neg_cnt:,} negative values detected in '{col_str}'."
                    })
                    total_invalid_cells += neg_cnt

            # 4. Out-of-bounds percentages (> 100 or < 0 if 0-100 scale, or > 1.0 if 0-1 scale)
            if PERCENTAGE_KEYWORDS.search(col_lower) and not ("diff" in col_lower or "growth" in col_lower):
                max_v = non_null_series.max()
                min_v = non_null_series.min()
                if min_v < 0 or (max_v > 100.0 and max_v > 1.0):
                    oob_mask = (non_null_series < 0) | (non_null_series > 100)
                    oob_cnt = int(oob_mask.sum())
                    if oob_cnt > 0:
                        oob_pct = (oob_cnt / total_rows) * 100
                        invalid_findings.append({
                            "column": col_str,
                            "issue_type": "Out-of-Bounds Percentage",
                            "count": oob_cnt,
                            "percentage": oob_pct,
                            "severity": "MEDIUM",
                            "description": f"{oob_cnt:,} percentage values outside standard bounds [0, 100]."
                        })
                        total_invalid_cells += oob_cnt

    return {
        "invalid_findings": invalid_findings,
        "total_invalid_cells": total_invalid_cells
    }


def detect_outliers_iqr(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform IQR-based outlier detection on non-ID numeric analytical columns.
    Lower Bound = Q1 - 1.5 * IQR, Upper Bound = Q3 + 1.5 * IQR.
    """
    total_rows = len(df)
    column_outliers = []
    total_outliers = 0
    total_numeric_cells = 0

    for col in df.columns:
        series = df[col]
        col_str = str(col)
        
        # Skip ID columns or non-numeric
        if bool(ID_KEYWORDS.search(col_str)) or not pd.api.types.is_numeric_dtype(series):
            continue

        non_null_series = series.dropna()
        n_count = len(non_null_series)
        
        if n_count < 5 or non_null_series.nunique() <= 2:
            continue

        total_numeric_cells += n_count

        q1 = float(non_null_series.quantile(0.25))
        q3 = float(non_null_series.quantile(0.75))
        iqr = q3 - q1

        # If IQR is 0, skip to avoid flagging normal variation
        if iqr <= 0:
            continue

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_mask = (non_null_series < lower_bound) | (non_null_series > upper_bound)
        outlier_cnt = int(outlier_mask.sum())
        
        if outlier_cnt > 0:
            total_outliers += outlier_cnt
            outlier_pct = float((outlier_cnt / n_count * 100))
            
            column_outliers.append({
                "column": col_str,
                "outlier_count": outlier_cnt,
                "outlier_percentage": outlier_pct,
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
                "min_value": round(float(non_null_series.min()), 2),
                "max_value": round(float(non_null_series.max()), 2)
            })

    column_outliers.sort(key=lambda x: x["outlier_percentage"], reverse=True)
    overall_outlier_rate = (total_outliers / total_numeric_cells * 100) if total_numeric_cells > 0 else 0.0

    return {
        "total_outliers": total_outliers,
        "outlier_rate": overall_outlier_rate,
        "column_outliers": column_outliers
    }


# =============================================================================
# DATA QUALITY SCORE COMPUTATION
# =============================================================================

def calculate_data_quality_score(
    missing_analysis: Dict[str, Any],
    duplicate_analysis: Dict[str, Any],
    consistency_analysis: Dict[str, Any],
    validity_analysis: Dict[str, Any],
    outlier_analysis: Dict[str, Any],
    total_cells: int
) -> Tuple[float, Dict[str, float], str, str]:
    """
    Calculate transparent, deterministic 5-dimensional data quality scores.
    Weights:
      - Completeness: 30%
      - Uniqueness:   20%
      - Consistency:  20%
      - Validity:     15%
      - Outlier Health: 15%
    """
    # 1. Completeness Score (0-100)
    missing_pct = missing_analysis.get("missing_percentage", 0.0)
    empty_cols_cnt = len(consistency_analysis.get("empty_columns", []))
    completeness = max(0.0, min(100.0, 100.0 - missing_pct - (empty_cols_cnt * 10.0)))

    # 2. Uniqueness Score (0-100)
    dup_pct = duplicate_analysis.get("duplicate_percentage", 0.0)
    dup_cols_cnt = len(duplicate_analysis.get("duplicate_columns", []))
    uniqueness = max(0.0, min(100.0, 100.0 - (dup_pct * 2.5) - (dup_cols_cnt * 10.0)))

    # 3. Consistency Score (0-100)
    constant_cols_cnt = len(consistency_analysis.get("constant_columns", []))
    inconsistencies = consistency_analysis.get("type_inconsistencies", [])
    inconsistent_penalty = sum(inc.get("inconsistent_percentage", 0.0) * 0.5 for inc in inconsistencies)
    consistency = max(0.0, min(100.0, 100.0 - (constant_cols_cnt * 6.0) - inconsistent_penalty))

    # 4. Validity Score (0-100)
    invalid_cells = validity_analysis.get("total_invalid_cells", 0)
    invalid_pct = (invalid_cells / total_cells * 100) if total_cells > 0 else 0.0
    validity = max(0.0, min(100.0, 100.0 - (invalid_pct * 3.5)))

    # 5. Outlier Health Score (0-100)
    outlier_rate = outlier_analysis.get("outlier_rate", 0.0)
    outlier_health = max(0.0, min(100.0, 100.0 - (outlier_rate * 2.5)))

    # Weighted Composite
    overall_score = (
        (0.30 * completeness) +
        (0.20 * uniqueness) +
        (0.20 * consistency) +
        (0.15 * validity) +
        (0.15 * outlier_health)
    )
    overall_score = round(max(0.0, min(100.0, overall_score)), 1)

    breakdown = {
        "Completeness": round(completeness, 1),
        "Uniqueness": round(uniqueness, 1),
        "Consistency": round(consistency, 1),
        "Validity": round(validity, 1),
        "Outlier Health": round(outlier_health, 1)
    }

    # Status mapping
    if overall_score >= 90.0:
        status = "Excellent"
        status_color = "#10b981" # Green
    elif overall_score >= 75.0:
        status = "Good"
        status_color = "#3b82f6" # Blue
    elif overall_score >= 60.0:
        status = "Needs Attention"
        status_color = "#f59e0b" # Amber
    elif overall_score >= 40.0:
        status = "Poor"
        status_color = "#f97316" # Orange
    else:
        status = "Critical"
        status_color = "#ef4444" # Red

    return overall_score, breakdown, status, status_color


# =============================================================================
# CONSOLIDATED ISSUES & COLUMN RANKINGS
# =============================================================================

def generate_quality_issues_and_rankings(
    df: pd.DataFrame,
    missing_analysis: Dict[str, Any],
    duplicate_analysis: Dict[str, Any],
    consistency_analysis: Dict[str, Any],
    validity_analysis: Dict[str, Any],
    outlier_analysis: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, str]]]:
    """Consolidate quality issues, rank problematic columns, and build recommendations."""
    issues: List[Dict[str, Any]] = []
    col_penalties: Dict[str, float] = {str(c): 0.0 for c in df.columns}
    col_main_issue: Dict[str, str] = {str(c): "Clean" for c in df.columns}

    # 1. Empty Columns Issues (CRITICAL)
    for col in consistency_analysis.get("empty_columns", []):
        issues.append({
            "severity": "CRITICAL",
            "category": "Structure",
            "column": col,
            "issue": "Completely Empty Column",
            "details": "100% of rows contain missing null values.",
            "measured_value": 100.0
        })
        col_penalties[col] += 50.0
        col_main_issue[col] = "100% empty column"

    # 2. Missing Values Issues
    for c in missing_analysis.get("column_missing_details", []):
        pct = c["missing_percentage"]
        if pct > 0:
            if pct >= 50.0:
                sev = "CRITICAL"
                weight = 30.0
            elif pct >= 20.0:
                sev = "HIGH"
                weight = 20.0
            elif pct >= 5.0:
                sev = "MEDIUM"
                weight = 10.0
            else:
                sev = "LOW"
                weight = 4.0

            issues.append({
                "severity": sev,
                "category": "Missing Values",
                "column": c["column_name"],
                "issue": f"{pct:.1f}% Missing Values",
                "details": f"{c['missing_count']:,} null values across {c['non_missing_count']:,} total non-null records.",
                "measured_value": pct
            })
            col_penalties[c["column_name"]] += weight
            if col_main_issue[c["column_name"]] == "Clean" or weight >= 20.0:
                col_main_issue[c["column_name"]] = f"{pct:.1f}% missing values"

    # 3. Duplicate Rows Issue (Dataset-level)
    dup_cnt = duplicate_analysis.get("duplicate_rows", 0)
    dup_pct = duplicate_analysis.get("duplicate_percentage", 0.0)
    if dup_cnt > 0:
        dup_sev = "HIGH" if dup_pct >= 20.0 else ("MEDIUM" if dup_pct >= 5.0 else "LOW")
        issues.append({
            "severity": dup_sev,
            "category": "Duplicates",
            "column": "Dataset (All Rows)",
            "issue": f"{dup_cnt:,} Duplicate Records",
            "details": f"{dup_pct:.1f}% of records in the dataset are exact row duplicates.",
            "measured_value": dup_pct
        })

    # 4. Duplicate Columns Issue
    for c1, c2 in duplicate_analysis.get("duplicate_columns", []):
        issues.append({
            "severity": "HIGH",
            "category": "Duplicates",
            "column": f"{c1} ↔ {c2}",
            "issue": "Duplicate Column Content",
            "details": f"Columns '{c1}' and '{c2}' contain 100% identical values across all rows.",
            "measured_value": 100.0
        })
        col_penalties[c2] += 25.0

    # 5. Constant Columns Issue
    for c in consistency_analysis.get("constant_columns", []):
        issues.append({
            "severity": "MEDIUM",
            "category": "Consistency",
            "column": c["column"],
            "issue": "Constant Single Value",
            "details": f"Column has zero variance (constant value: '{c['constant_value']}').",
            "measured_value": 1.0
        })
        col_penalties[c["column"]] += 15.0
        if col_main_issue[c["column"]] == "Clean":
            col_main_issue[c["column"]] = f"Constant value ('{c['constant_value']}')"

    # 6. Type Inconsistencies
    for inc in consistency_analysis.get("type_inconsistencies", []):
        issues.append({
            "severity": "HIGH",
            "category": "Consistency",
            "column": inc["column"],
            "issue": inc["issue"],
            "details": f"{inc['inconsistent_percentage']:.1f}% inconsistent values (e.g. {inc['sample_values']}).",
            "measured_value": inc["inconsistent_percentage"]
        })
        col_penalties[inc["column"]] += 20.0
        col_main_issue[inc["column"]] = "Mixed data types"

    # 7. Validity Findings
    for v in validity_analysis.get("invalid_findings", []):
        issues.append({
            "severity": v["severity"],
            "category": "Validity",
            "column": v["column"],
            "issue": v["issue_type"],
            "details": v["description"],
            "measured_value": v["percentage"]
        })
        col_penalties[v["column"]] += 12.0

    # 8. Outlier Findings
    for o in outlier_analysis.get("column_outliers", []):
        if o["outlier_percentage"] >= 5.0:
            sev = "MEDIUM" if o["outlier_percentage"] < 15.0 else "HIGH"
            issues.append({
                "severity": sev,
                "category": "Outliers",
                "column": o["column"],
                "issue": f"{o['outlier_count']} Extreme Outliers",
                "details": f"{o['outlier_percentage']:.1f}% values outside bounds [{o['lower_bound']}, {o['upper_bound']}].",
                "measured_value": o["outlier_percentage"]
            })
            col_penalties[o["column"]] += 10.0

    # Sort issues by severity priority
    sev_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    issues.sort(key=lambda x: (sev_rank.get(x["severity"], 5), -x["measured_value"]))

    # Problematic Columns Ranking
    column_scores = []
    for col in df.columns:
        col_str = str(col)
        score = max(0.0, min(100.0, 100.0 - col_penalties[col_str]))
        main_iss = col_main_issue[col_str]
        
        if score >= 90:
            sev = "Healthy"
        elif score >= 75:
            sev = "Low"
        elif score >= 60:
            sev = "Moderate"
        elif score >= 40:
            sev = "High"
        else:
            sev = "Critical"

        column_scores.append({
            "column": col_str,
            "quality_score": round(score, 1),
            "main_issue": main_iss,
            "severity": sev
        })

    # Sort worst columns first
    column_scores.sort(key=lambda x: x["quality_score"])

    # Generate Deterministic Recommendations
    recommendations = []
    if missing_analysis["missing_percentage"] > 0:
        high_miss_cols = [c["column_name"] for c in missing_analysis["column_missing_details"] if c["missing_percentage"] >= 20.0]
        if high_miss_cols:
            recommendations.append({
                "title": "Resolve High Missing Rates",
                "text": f"Review missing value imputation or column pruning for <b>{', '.join(high_miss_cols[:3])}</b> before statistical modeling.",
                "target_page": "Data Preparation",
                "variant": "warning"
            })
        else:
            recommendations.append({
                "title": "Impute Missing Records",
                "text": f"Dataset has an overall missing rate of <b>{missing_analysis['missing_percentage']:.1f}%</b>. Consider filling strategies in Data Preparation.",
                "target_page": "Data Preparation",
                "variant": "info"
            })

    if dup_cnt > 0:
        recommendations.append({
            "title": "Deduplicate Dataset",
            "text": f"Remove <b>{dup_cnt:,} duplicate records ({dup_pct:.1f}%)</b> in Data Preparation to avoid skewed analytical weights.",
            "target_page": "Data Preparation",
            "variant": "warning" if dup_pct > 10 else "info"
        })

    if consistency_analysis["empty_columns"]:
        recommendations.append({
            "title": "Drop Empty Columns",
            "text": f"Columns <b>{', '.join(consistency_analysis['empty_columns'])}</b> contain 0 non-null values and should be removed.",
            "target_page": "Data Preparation",
            "variant": "warning"
        })

    if outlier_analysis["column_outliers"]:
        top_outliers = [o["column"] for o in outlier_analysis["column_outliers"][:2]]
        recommendations.append({
            "title": "Inspect Extreme Outliers",
            "text": f"Examine distribution tails and capping thresholds for <b>{', '.join(top_outliers)}</b> in Exploratory Data Analysis.",
            "target_page": "EDA",
            "variant": "info"
        })

    if not recommendations:
        recommendations.append({
            "title": "Dataset Health is Excellent",
            "text": "No critical quality defects or significant data anomalies were detected. Dataset is ready for exploration and visualization.",
            "target_page": "EDA",
            "variant": "success"
        })

    return issues, column_scores, recommendations


# =============================================================================
# MAIN DATA QUALITY ORCHESTRATOR
# =============================================================================

def analyze_data_quality(df: pd.DataFrame, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Main audit pipeline executing all diagnostic checks and composite scoring."""
    total_cells = len(df) * len(df.columns)
    
    missing = analyze_missing_values(df)
    duplicates = analyze_duplicates(df)
    consistency = analyze_consistency_and_structure(df)
    validity = analyze_validity(df)
    outliers = detect_outliers_iqr(df)

    score, breakdown, status, status_color = calculate_data_quality_score(
        missing_analysis=missing,
        duplicate_analysis=duplicates,
        consistency_analysis=consistency,
        validity_analysis=validity,
        outlier_analysis=outliers,
        total_cells=total_cells
    )

    issues, col_scores, recommendations = generate_quality_issues_and_rankings(
        df=df,
        missing_analysis=missing,
        duplicate_analysis=duplicates,
        consistency_analysis=consistency,
        validity_analysis=validity,
        outlier_analysis=outliers
    )

    return {
        "overall_score": score,
        "status": status,
        "status_color": status_color,
        "breakdown": breakdown,
        "missing_analysis": missing,
        "duplicate_analysis": duplicates,
        "consistency_analysis": consistency,
        "validity_analysis": validity,
        "outlier_analysis": outliers,
        "column_quality_scores": col_scores,
        "issues": issues,
        "recommendations": recommendations
    }


# =============================================================================
# DATA QUALITY PLOTLY VISUALIZATIONS
# =============================================================================

def generate_missing_bar_chart(
    missing_details: List[Dict[str, Any]],
    theme: str = "Dark"
) -> Optional[go.Figure]:
    """Generate horizontal bar chart ranking columns by missing percentage."""
    try:
        # Filter to affected columns
        affected = [c for c in missing_details if c["missing_percentage"] > 0]
        if not affected:
            return None

        # Show top 10 most missing
        top_affected = affected[:10]
        cols = [c["column_name"] for c in top_affected]
        pcts = [c["missing_percentage"] for c in top_affected]

        cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])
        
        # Dynamic color based on severity
        colors = []
        for p in pcts:
            if p >= 50:
                colors.append("#ef4444")
            elif p >= 20:
                colors.append("#f97316")
            elif p >= 5:
                colors.append("#f59e0b")
            else:
                colors.append("#3b82f6")

        fig = go.Figure(data=[
            go.Bar(
                x=pcts,
                y=cols,
                orientation="h",
                marker=dict(color=colors, line=dict(color=cfg["grid"], width=1)),
                text=[f"{p:.1f}%" for p in pcts],
                textposition="auto",
                hovertemplate="Column: <b>%{y}</b><br>Missing: %{x:.2f}%<extra></extra>"
            )
        ])

        apply_chart_theme(fig, theme=theme, title="Missing Value Rates (Top Affected Columns)", height=320)
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(title_text="Missing Percentage (%)", range=[0, max(100, max(pcts) * 1.15)])
        return fig
    except Exception:
        return None


def generate_outlier_bar_chart(
    outlier_details: List[Dict[str, Any]],
    theme: str = "Dark"
) -> Optional[go.Figure]:
    """Generate bar chart ranking columns by outlier rate."""
    try:
        if not outlier_details:
            return None

        top_outliers = outlier_details[:8]
        cols = [o["column"] for o in top_outliers]
        pcts = [o["outlier_percentage"] for o in top_outliers]

        cfg = THEME_CONFIGS.get(theme, THEME_CONFIGS["Dark"])

        fig = go.Figure(data=[
            go.Bar(
                x=pcts,
                y=cols,
                orientation="h",
                marker=dict(color="#8b5cf6", line=dict(color=cfg["grid"], width=1)),
                text=[f"{p:.1f}%" for p in pcts],
                textposition="auto",
                hovertemplate="Column: <b>%{y}</b><br>Outliers: %{x:.2f}%<extra></extra>"
            )
        ])

        apply_chart_theme(fig, theme=theme, title="Outlier Rate by Feature (IQR Method)", height=300)
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(title_text="Outlier Percentage (%)")
        return fig
    except Exception:
        return None

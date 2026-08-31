"""
DATA STUDIO v2 — Data Quality Engine (Module 4)
=============================================================================
Comprehensive deterministic data health auditing, multi-dimensional quality
scoring, type consistency analysis, outlier detection, and actionable issue tracking.
Read-only analysis: NEVER mutates the underlying dataset.
"""
from typing import Optional, Dict, Any, List, Tuple
import datetime
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

    report = {
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

    # Generate prioritized actionable intelligent decision plan
    report["decision_plan"] = generate_quality_decision_plan(df, report)

    return report


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


# =============================================================================
# INTELLIGENT DECISION ENGINE & STATISTICAL REASONER
# =============================================================================

def investigate_column_distribution(series: pd.Series, col_name: str, df: pd.DataFrame) -> Dict[str, Any]:
    """Deep statistical profiling of a column for data quality decision logic."""
    col_str = str(col_name)
    col_lower = col_str.lower()
    total_rows = len(df)
    non_null = series.dropna()
    non_null_cnt = len(non_null)
    missing_cnt = int(series.isna().sum())
    missing_pct = float(missing_cnt / total_rows * 100) if total_rows > 0 else 0.0

    is_id = bool(ID_KEYWORDS.search(col_str))
    is_numeric = pd.api.types.is_numeric_dtype(series) and not is_id
    is_datetime = pd.api.types.is_datetime64_any_dtype(series)
    is_categorical = (
        pd.api.types.is_object_dtype(series)
        or pd.api.types.is_string_dtype(series)
        or pd.api.types.is_bool_dtype(series)
        or isinstance(series.dtype, pd.CategoricalDtype)
        or (not is_numeric and not is_datetime and not is_id)
    )

    # Detect high-value analytical target names
    is_target = any(kw in col_lower for kw in ["revenue", "sales", "profit", "price", "amount", "target", "churn", "label", "income", "cost", "salary", "spend"])

    stats: Dict[str, Any] = {
        "column_name": col_str,
        "dtype": str(series.dtype),
        "total_rows": total_rows,
        "non_null_count": non_null_cnt,
        "missing_count": missing_cnt,
        "missing_percentage": missing_pct,
        "is_id": is_id,
        "is_numeric": is_numeric,
        "is_datetime": is_datetime,
        "is_categorical": is_categorical,
        "is_target": is_target,
        "unique_count": int(series.nunique(dropna=True)),
    }

    if is_numeric and non_null_cnt > 0:
        mean_val = float(non_null.mean())
        median_val = float(non_null.median())
        std_val = float(non_null.std(ddof=1)) if non_null_cnt > 1 else 0.0
        min_val = float(non_null.min())
        max_val = float(non_null.max())
        q25 = float(non_null.quantile(0.25))
        q75 = float(non_null.quantile(0.75))
        iqr = q75 - q25
        
        # Outlier counts
        lower_b = q25 - 1.5 * iqr
        upper_b = q75 + 1.5 * iqr
        outlier_mask = (non_null < lower_b) | (non_null > upper_b)
        outlier_cnt = int(outlier_mask.sum())
        outlier_pct = float(outlier_cnt / non_null_cnt * 100)

        skew_val = float(non_null.skew()) if non_null_cnt >= 3 else 0.0
        is_skewed = abs(skew_val) > 1.0
        is_heavily_skewed = abs(skew_val) > 2.0

        stats.update({
            "mean": mean_val,
            "median": median_val,
            "std": std_val,
            "min": min_val,
            "max": max_val,
            "q25": q25,
            "q75": q75,
            "iqr": iqr,
            "skewness": skew_val,
            "is_skewed": is_skewed,
            "is_heavily_skewed": is_heavily_skewed,
            "outliers_count": outlier_cnt,
            "outliers_percentage": outlier_pct,
            "lower_bound": lower_b,
            "upper_bound": upper_b
        })

    elif is_categorical and non_null_cnt > 0:
        top_cat = non_null.mode().iloc[0] if not non_null.empty else None
        top_freq = int((non_null == top_cat).sum()) if top_cat is not None else 0
        top_ratio = float(top_freq / non_null_cnt) if non_null_cnt > 0 else 0.0

        # Check for currency or percentage text patterns
        sample_texts = non_null.astype(str).head(30)
        has_currency = sample_texts.str.contains(r"[\$€£₹¥]", regex=True).mean() > 0.4
        has_percentage = sample_texts.str.contains(r"%", regex=True).mean() > 0.4
        is_numeric_str = pd.to_numeric(sample_texts.str.replace(r"[,\$€£₹\s%]", "", regex=True), errors="coerce").notna().mean() > 0.7

        stats.update({
            "top_category": str(top_cat) if top_cat is not None else "None",
            "top_frequency": top_freq,
            "top_ratio": top_ratio,
            "is_dominant_mode": top_ratio >= 0.40,
            "has_currency_symbols": has_currency,
            "has_percentage_symbols": has_percentage,
            "is_numeric_string": is_numeric_str
        })

    return stats


# =============================================================================
# AI DATA MENTOR DECISION GENERATION ENGINE
# =============================================================================

def _build_human_frequency_text(count: int, total: int, item_type: str = "cells") -> str:
    """Produce an intuitive, human-understandable ratio sentence for beginners."""
    if total <= 0 or count <= 0:
        return f"0 {item_type} affected."
    pct = (count / total) * 100
    if pct >= 95:
        return f"Nearly all {item_type} ({count:,} of {total:,}) are affected."
    elif 45 <= pct <= 55:
        return f"About half of the {item_type} ({count:,} of {total:,}) are affected."
    elif pct < 1:
        return f"Less than 1 out of every 100 {item_type} is affected ({count:,} total)."
    else:
        out_of_100 = max(1, round(pct))
        return f"About {out_of_100} out of every 100 {item_type} are empty." if "empty" in item_type or "cell" in item_type else f"About {out_of_100} out of every 100 {item_type} are affected."


def generate_missing_value_decision(col_name: str, prof: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate an intelligent, statistically reasoned remediation recommendation
    for a column with missing values following the AI Data Mentor structure.
    """
    missing_cnt = prof.get("missing_count", 0)
    missing_pct = prof.get("missing_percentage", 0.0)
    is_numeric = prof.get("is_numeric", False)
    is_categorical = prof.get("is_categorical", False)
    is_datetime = prof.get("is_datetime", False)
    is_id = prof.get("is_id", False)
    is_target = prof.get("is_target", False)
    total_rows = prof.get("total_rows", len(df))

    # ── Severity Assessment ──────────────────────────────────────────────────
    if missing_pct >= 60.0 or (missing_pct >= 30.0 and (is_id or is_target)):
        severity = "CRITICAL"
        priority_weight = 100 + missing_pct
    elif missing_pct >= 20.0 or (missing_pct >= 5.0 and (is_id or is_target)):
        severity = "HIGH"
        priority_weight = 70 + missing_pct
    elif missing_pct >= 5.0:
        severity = "MEDIUM"
        priority_weight = 40 + missing_pct
    else:
        severity = "LOW"
        priority_weight = 10 + missing_pct

    # Human frequency description
    human_freq = _build_human_frequency_text(missing_cnt, total_rows, "cells")

    # What We Found block
    what_we_found = {
        "badge": "EMPTY VALUES FOUND",
        "column": col_name,
        "primary_text": f"{missing_cnt:,} out of {total_rows:,} values are missing",
        "secondary_text": f"{missing_pct:.1f}% of this column is empty",
        "human_summary": human_freq
    }

    # ── Strategy Generation & Reasoning ──────────────────────────────────────
    if missing_pct >= 70.0:
        rec_friendly = f"Remove the '{col_name}' column from your analysis"
        rec_technical = "Drop Incomplete Column (>70% Missing)"
        action_key = "drop_cols"
        
        why_beginner = (
            f"Over {missing_pct:.0f}% of '{col_name}' is empty ({missing_cnt:,} missing entries). "
            f"Trying to guess this many missing values could give misleading results. "
            f"Removing this column is safer and keeps all other columns completely intact."
        )
        why_standard = (
            f"Over {missing_pct:.1f}% of observations in '{col_name}' are missing. "
            f"Imputing {missing_cnt:,} values would introduce artificial variance and bias. "
            f"Dropping this column prevents model degradation while retaining 100% of rows for other features."
        )
        why_technical = (
            f"Nullity rate ({missing_pct:.1f}%) exceeds safety tolerance for MCAR/MAR imputation. "
            f"Feature pruning eliminates pseudo-variance while preserving all {total_rows:,} sample records."
        )
        
        confidence = "HIGH"
        risk = "LOW"
        
        what_will_happen = [
            f"The '{col_name}' column will be removed from your dataset",
            "No customer or transaction rows will be deleted",
            f"Your dataset will keep all {total_rows:,} rows across {max(1, len(df.columns)-1)} columns"
        ]
        
        ai_reasoning_beginner = (
            "When more than half a column is missing, guessing the values is like flipping a coin. "
            "AI recommends dropping the column so your overall numbers remain trustworthy."
        )

        alternatives = [
            {
                "rating": "★★★★★",
                "friendly_name": "Remove this column",
                "technical_name": "Drop column",
                "strategy": "drop_cols",
                "is_recommended": True,
                "description": "Safest choice when most values are missing. Leaves all rows intact.",
                "why": "Prunes column with >70% nulls; avoids massive data fabrication.",
                "trade_off": "Removes the feature entirely from downstream analyses."
            },
            {
                "rating": "★★★☆☆",
                "friendly_name": "Fill with 'Unknown' / 0",
                "technical_name": "Categorical indicator",
                "strategy": "unknown" if is_categorical else "zero",
                "is_recommended": False,
                "description": "Keeps the column by labeling blanks as Unknown or Zero.",
                "why": "Retains the column by tagging missingness distinctly.",
                "trade_off": "High empty volume may dilute analytical signal."
            },
            {
                "rating": "★☆☆☆☆",
                "friendly_name": "Delete incomplete rows",
                "technical_name": "Listwise deletion",
                "strategy": "drop_rows",
                "is_recommended": False,
                "description": f"Removes all rows containing missing values in this column.",
                "why": "Removes any rows with missing values.",
                "trade_off": f"Destructive: would eliminate {missing_cnt:,} rows ({missing_pct:.1f}% of your data)."
            }
        ]

        technical_evidence = {
            "Total Missing Count": f"{missing_cnt:,} cells",
            "Missingness Rate": f"{missing_pct:.2f}%",
            "Column Classification": "Categorical" if is_categorical else ("Numeric" if is_numeric else "Text/General"),
            "Recommended Strategy": "Drop Column (Pruning)",
            "Preserved Records": f"{total_rows:,} rows (100%)"
        }

    elif is_numeric:
        is_skewed = prof.get("is_skewed", False)
        skew_val = prof.get("skewness", 0.0)
        mean_val = prof.get("mean", 0.0)
        median_val = prof.get("median", 0.0)
        outlier_cnt = prof.get("outliers_count", 0)

        fmt_median = f"{int(median_val)}" if float(median_val).is_integer() else f"{median_val:,.2f}"
        fmt_mean = f"{int(mean_val)}" if float(mean_val).is_integer() else f"{mean_val:,.2f}"

        if is_skewed or outlier_cnt > 0:
            rec_friendly = f"Fill the missing values with {fmt_median}"
            rec_technical = "Median Imputation (Robust to Outliers)"
            action_key = "median"
            
            why_beginner = (
                f"Some values in '{col_name}' are unusually high or low compared with the rest. "
                f"Because of this, using the simple average ({fmt_mean}) could give misleading replacement values. "
                f"{fmt_median} represents the middle of the existing values, making it a safer and more realistic choice."
            )
            why_standard = (
                f"The distribution of '{col_name}' is {'right' if skew_val > 0 else 'left'}-skewed (skewness: {skew_val:.2f}) "
                f"with {outlier_cnt:,} unusual values detected. The median ({fmt_median}) is mathematically robust to extreme values, "
                f"whereas the mean ({fmt_mean}) is pulled by the long tail."
            )
            why_technical = (
                f"Non-normal distribution with skewness={skew_val:.2f} and {outlier_cnt} IQR outliers. "
                f"Median estimator ({fmt_median}) minimizes L1 loss and protects parametric estimators against leverage distortion."
            )
            
            confidence = "HIGH"
            risk = "LOW"
            
            what_will_happen = [
                f"{missing_cnt:,} empty cells will be filled with {fmt_median}",
                "No rows will be deleted",
                f"Your dataset will remain at {total_rows:,} rows"
            ]
            
            ai_reasoning_beginner = (
                "AI compared the average value with the middle value and checked for unusually high or low entries. "
                "The data contains several unusual numbers, so the middle value is safer than the average."
            )

            alternatives = [
                {
                    "rating": "★★★★★",
                    "friendly_name": "Fill with the middle value",
                    "technical_name": "Median imputation",
                    "strategy": "median",
                    "is_recommended": True,
                    "description": "Best option for this dataset. Safe against unusual high or low values.",
                    "why": f"Preserves middle value ({fmt_median}) against {outlier_cnt:,} outliers.",
                    "trade_off": "Slightly reduces data spread near the middle."
                },
                {
                    "rating": "★★★★☆",
                    "friendly_name": "Fill with the average",
                    "technical_name": "Mean imputation",
                    "strategy": "mean",
                    "is_recommended": False,
                    "description": f"Uses the mathematical average ({fmt_mean}). Works best when values are evenly balanced.",
                    "why": "Standard mathematical average across available values.",
                    "trade_off": f"Biased by skewness ({skew_val:.2f}); pulls imputed values toward {fmt_mean}."
                },
                {
                    "rating": "★★☆☆☆" if missing_pct > 3.0 else "★★★☆☆",
                    "friendly_name": "Delete incomplete rows",
                    "technical_name": "Drop rows",
                    "strategy": "drop_rows",
                    "is_recommended": False,
                    "description": "Removes any row containing an empty value in this column.",
                    "why": "Ensures all analyzed records contain 100% measured data.",
                    "trade_off": f"Eliminates {missing_cnt:,} rows ({missing_pct:.1f}% sample loss)."
                },
                {
                    "rating": "★☆☆☆☆",
                    "friendly_name": "Keep values empty",
                    "technical_name": "Do nothing",
                    "strategy": "none",
                    "is_recommended": False,
                    "description": "Leave the empty cells as they are. Use only if blanks have a specific meaning.",
                    "why": "Leaves raw entries untouched.",
                    "trade_off": "May cause errors or exclusions in charts and calculations."
                }
            ]

            technical_evidence = {
                "Median (Middle Value)": fmt_median,
                "Mean (Average)": fmt_mean,
                "Skewness": f"{skew_val:.2f} ({'Right-skewed' if skew_val > 0 else 'Left-skewed'})",
                "Unusual Values (Outliers)": f"{outlier_cnt:,} detected",
                "Standard Deviation": f"{prof.get('std', 0.0):,.2f}",
                "Method": "Median Imputation"
            }
        else:
            rec_friendly = f"Fill the missing values with the average ({fmt_mean})"
            rec_technical = "Mean Imputation (Symmetric Distribution)"
            action_key = "mean"
            
            why_beginner = (
                f"The values in '{col_name}' are fairly evenly balanced without extreme unusual numbers. "
                f"Using the average ({fmt_mean}) is a safe, natural choice that keeps the overall dataset balanced."
            )
            why_standard = (
                f"'{col_name}' exhibits an approximately symmetric distribution (skewness: {skew_val:.2f}, "
                f"mean: {fmt_mean}, median: {fmt_median}). Mean imputation seamlessly preserves the expected value."
            )
            why_technical = (
                f"Symmetric distribution (skewness: {skew_val:.2f} ≈ 0, mean ≈ median). "
                f"Mean imputation unbiasedly preserves sample first moment E[X] without shifting location parameters."
            )
            
            confidence = "HIGH"
            risk = "LOW"
            
            what_will_happen = [
                f"{missing_cnt:,} empty cells will be filled with {fmt_mean}",
                "No rows will be deleted",
                f"Your dataset will remain at {total_rows:,} rows"
            ]
            
            ai_reasoning_beginner = (
                "AI checked whether the numbers were spread out evenly. Because there are no extreme outliers, "
                "the average value accurately reflects the typical observation in this column."
            )

            alternatives = [
                {
                    "rating": "★★★★★",
                    "friendly_name": "Fill with the average",
                    "technical_name": "Mean imputation",
                    "strategy": "mean",
                    "is_recommended": True,
                    "description": f"Best option for evenly balanced numbers. Fills with {fmt_mean}.",
                    "why": f"Matches symmetric distribution ({fmt_mean}); preserves expected value.",
                    "trade_off": "Mild variance reduction around the mean."
                },
                {
                    "rating": "★★★★☆",
                    "friendly_name": "Fill with the middle value",
                    "technical_name": "Median imputation",
                    "strategy": "median",
                    "is_recommended": False,
                    "description": f"Uses the middle value ({fmt_median}). Very close to average in this case.",
                    "why": f"Close to mean ({fmt_median} vs {fmt_mean}); safe alternative.",
                    "trade_off": "Equivalent to mean for symmetric distributions."
                },
                {
                    "rating": "★★☆☆☆",
                    "friendly_name": "Delete incomplete rows",
                    "technical_name": "Drop rows",
                    "strategy": "drop_rows",
                    "is_recommended": False,
                    "description": "Removes any row containing an empty value.",
                    "why": "Retains only strictly complete observations.",
                    "trade_off": f"Discards {missing_cnt:,} rows of valid measurements in other columns."
                }
            ]

            technical_evidence = {
                "Mean (Average)": fmt_mean,
                "Median (Middle Value)": fmt_median,
                "Skewness": f"{skew_val:.2f} (Symmetric)",
                "Outliers Detected": "0",
                "Standard Deviation": f"{prof.get('std', 0.0):,.2f}",
                "Method": "Mean Imputation"
            }

    elif is_categorical:
        top_cat = prof.get("top_category", "Unknown")
        top_ratio = prof.get("top_ratio", 0.0)
        is_dominant = prof.get("is_dominant_mode", False)

        if is_dominant and missing_pct <= 15.0:
            rec_friendly = f"Fill missing entries with the most common value ('{top_cat}')"
            rec_technical = f"Mode Imputation ('{top_cat}')"
            action_key = "mode"
            
            why_beginner = (
                f"'{top_cat}' is the most common value by far, appearing in {top_ratio*100:.0f}% of existing records. "
                f"Because only a small portion is empty ({missing_pct:.1f}%), filling empty cells with '{top_cat}' is the most natural match."
            )
            why_standard = (
                f"'{top_cat}' is the dominant category representing {top_ratio*100:.1f}% of known entries. "
                f"Because missingness is low ({missing_pct:.1f}%), mode imputation restores completeness with minimal class distortion."
            )
            why_technical = (
                f"Categorical distribution has dominant mode '{top_cat}' (frequency={top_ratio*100:.1f}%). "
                f"Low missingness rate ({missing_pct:.1f}%) ensures modal imputation does not induce significant categorical entropy shift."
            )
            
            confidence = "HIGH"
            risk = "LOW"
            
            what_will_happen = [
                f"{missing_cnt:,} empty cells will be filled with '{top_cat}'",
                "No rows will be deleted",
                f"Your dataset will remain at {total_rows:,} rows"
            ]
            
            ai_reasoning_beginner = (
                f"AI analyzed the frequency of all categories in '{col_name}'. "
                f"'{top_cat}' occurs much more often than any other option, making it the most probable replacement."
            )

            alternatives = [
                {
                    "rating": "★★★★★",
                    "friendly_name": "Fill with most common value",
                    "technical_name": "Mode imputation",
                    "strategy": "mode",
                    "is_recommended": True,
                    "description": f"Fills with '{top_cat}' (accounts for {top_ratio*100:.0f}% of known entries).",
                    "why": f"Most frequent state ({top_ratio*100:.1f}% prevalence); highly plausible.",
                    "trade_off": f"Slightly increases count of '{top_cat}' by +{missing_cnt:,}."
                },
                {
                    "rating": "★★★★☆",
                    "friendly_name": "Label as 'Unknown'",
                    "technical_name": "Missing value indicator",
                    "strategy": "unknown",
                    "is_recommended": False,
                    "description": "Explicitly preserves missing cells as a separate 'Unknown' group.",
                    "why": "Explicitly preserves the missing state as a distinct category.",
                    "trade_off": "Creates a new artificial category value."
                },
                {
                    "rating": "★★☆☆☆",
                    "friendly_name": "Delete incomplete rows",
                    "technical_name": "Drop rows",
                    "strategy": "drop_rows",
                    "is_recommended": False,
                    "description": "Removes any rows with missing text values.",
                    "why": "Avoids assumption of dominant category.",
                    "trade_off": f"Permanently drops {missing_cnt:,} rows."
                }
            ]

            technical_evidence = {
                "Most Common Category (Mode)": str(top_cat),
                "Mode Prevalence": f"{top_ratio*100:.1f}%",
                "Missing Cells": f"{missing_cnt:,} ({missing_pct:.1f}%)",
                "Total Categories": f"{prof.get('unique_count', 0):,}",
                "Method": "Mode Imputation"
            }
        else:
            rec_friendly = "Label missing entries as 'Unknown'"
            rec_technical = "Categorize as 'Unknown'"
            action_key = "unknown"
            
            why_beginner = (
                f"There is no single dominant value in '{col_name}' (the top value only appears in {top_ratio*100:.0f}% of entries). "
                f"Guessing a category could introduce bias. Labeling empty cells as 'Unknown' keeps your data honest without deleting records."
            )
            why_standard = (
                f"No single category dominates '{col_name}' (highest frequency is {top_ratio*100:.1f}%). "
                f"Imputing an arbitrary mode would introduce heavy bias. Labeling missing entries as 'Unknown' preserves data integrity."
            )
            why_technical = (
                f"High categorical entropy with no modal dominance (top ratio={top_ratio*100:.1f}%). "
                f"Explicit sentinel encoding ('Unknown') preserves informational missingness without corrupting probability distribution."
            )
            
            confidence = "MEDIUM"
            risk = "LOW"
            
            what_will_happen = [
                f"{missing_cnt:,} empty cells will be labeled as 'Unknown'",
                "No rows will be deleted",
                f"Your dataset will remain at {total_rows:,} rows"
            ]
            
            ai_reasoning_beginner = (
                "AI checked whether one category appeared significantly more than others. "
                "Since values are spread out, guessing could distort your results, so a neutral 'Unknown' label is recommended."
            )

            alternatives = [
                {
                    "rating": "★★★★★",
                    "friendly_name": "Label as 'Unknown'",
                    "technical_name": "Categorize as 'Unknown'",
                    "strategy": "unknown",
                    "is_recommended": True,
                    "description": "Safe and neutral. Does not guess or distort existing categories.",
                    "why": "Does not fabricate category assumptions; neutral to distribution.",
                    "trade_off": "Adds 'Unknown' as a distinct category."
                },
                {
                    "rating": "★★★☆☆",
                    "friendly_name": "Fill with most frequent value",
                    "technical_name": "Mode imputation",
                    "strategy": "mode",
                    "is_recommended": False,
                    "description": f"Uses '{top_cat}' even though it only represents {top_ratio*100:.0f}% of data.",
                    "why": "Uses most frequent observed value.",
                    "trade_off": f"May introduce artificial bias since mode is only {top_ratio*100:.1f}%."
                },
                {
                    "rating": "★★☆☆☆",
                    "friendly_name": "Delete incomplete rows",
                    "technical_name": "Drop rows",
                    "strategy": "drop_rows",
                    "is_recommended": False,
                    "description": "Removes any rows missing this information.",
                    "why": "Removes unclassified entries.",
                    "trade_off": f"Permanently drops {missing_cnt:,} rows."
                }
            ]

            technical_evidence = {
                "Top Category": str(top_cat),
                "Top Category Share": f"{top_ratio*100:.1f}%",
                "Unique Categories": f"{prof.get('unique_count', 0):,}",
                "Missing Cells": f"{missing_cnt:,} ({missing_pct:.1f}%)",
                "Method": "Explicit Sentinel Categorization"
            }

    elif is_datetime:
        rec_friendly = "Fill missing timestamps using the previous recorded time"
        rec_technical = "Forward Fill (Time Series Propagation)"
        action_key = "ffill"
        
        why_beginner = (
            f"'{col_name}' represents dates or times. When a date is missing in sequential records, "
            f"carrying forward the previous known date is a natural and standard way to fill the gap."
        )
        why_standard = (
            f"'{col_name}' is a temporal sequence. Forward filling propagates the last valid timestamp, "
            f"which is standard for sequential time-series observations without introducing future lookahead bias."
        )
        why_technical = (
            f"Temporal sequence indexed column. First-order forward sample-and-hold (ffill) maintains chronological "
            f"continuity while strictly adhering to non-anticipative causality (no future lookahead)."
        )
        
        confidence = "MEDIUM"
        risk = "LOW"
        
        what_will_happen = [
            f"{missing_cnt:,} missing timestamps will be filled from the preceding record",
            "No rows will be deleted",
            f"Your dataset will remain at {total_rows:,} rows"
        ]
        
        ai_reasoning_beginner = (
            "In timelines and dates, numbers usually move forward. AI recommends using the most recent known date to keep the timeline unbroken."
        )

        alternatives = [
            {
                "rating": "★★★★★",
                "friendly_name": "Fill from previous record",
                "technical_name": "Forward fill (ffill)",
                "strategy": "ffill",
                "is_recommended": True,
                "description": "Propagates the last known date forward. Ideal for sequential data.",
                "why": "Standard sequential propagation for time-indexed data.",
                "trade_off": "Cannot fill missing values at the very start of the series."
            },
            {
                "rating": "★★★☆☆",
                "friendly_name": "Delete rows with missing dates",
                "technical_name": "Drop rows",
                "strategy": "drop_rows",
                "is_recommended": False,
                "description": "Removes rows where the timestamp is unknown.",
                "why": "Ensures every analyzed row has an exact confirmed timestamp.",
                "trade_off": f"Deletes {missing_cnt:,} rows ({missing_pct:.1f}%)."
            }
        ]

        technical_evidence = {
            "Data Type": "Datetime / Timestamp",
            "Missing Timestamps": f"{missing_cnt:,} ({missing_pct:.1f}%)",
            "Method": "Forward Fill (ffill)",
            "Lookahead Bias": "None (Causal propagation)"
        }
    else:
        rec_friendly = "Fill missing values with 'Unknown'" if missing_pct > 1.0 else "Remove rows with missing values"
        rec_technical = "Categorize as 'Unknown'" if missing_pct > 1.0 else "Drop Incomplete Rows"
        action_key = "unknown" if missing_pct > 1.0 else "drop_rows"
        
        why_beginner = (
            f"Missingness is minor ({missing_pct:.1f}% / {missing_cnt:,} cells). "
            f"Filling with 'Unknown' preserves all records without causing calculation errors."
        )
        why_standard = (
            f"Missingness is minor ({missing_pct:.1f}% / {missing_cnt:,} cells). "
            f"Remediating prevents downstream null errors without significant data loss."
        )
        why_technical = (
            f"Low nullity proportion ({missing_pct:.1f}%). Remediating eliminates missingness indicator overhead."
        )
        
        confidence = "MEDIUM"
        risk = "LOW"
        
        what_will_happen = [
            f"{missing_cnt:,} empty cells will be resolved",
            "No rows will be deleted" if action_key == "unknown" else f"{missing_cnt:,} rows deleted",
            f"Your dataset will have {total_rows:,} rows"
        ]
        
        ai_reasoning_beginner = "AI identified a small number of empty cells and recommends safe replacement to avoid errors."

        alternatives = [
            {"rating": "★★★★☆", "friendly_name": "Fill with 'Unknown'", "technical_name": "Sentinel placeholder", "strategy": "unknown", "is_recommended": True, "description": "Safe placeholder.", "why": "Safe placeholder.", "trade_off": "None."},
            {"rating": "★★★☆☆", "friendly_name": "Delete incomplete rows", "technical_name": "Drop rows", "strategy": "drop_rows", "is_recommended": False, "description": "Removes incomplete rows.", "why": "Clean complete records.", "trade_off": f"Drops {missing_cnt:,} rows."}
        ]

        technical_evidence = {
            "Missing Cells": f"{missing_cnt:,}",
            "Missing Percentage": f"{missing_pct:.2f}%",
            "Method": "Fallback Safe Handler"
        }

    return {
        "id": f"missing_{col_name.replace(' ', '_')}",
        "type": "missing",
        "column": col_name,
        "title": f"Missing Values in '{col_name}'",
        "severity": severity,
        "priority_weight": priority_weight,
        "affected_count": missing_cnt,
        "affected_percentage": missing_pct,
        "affected_label": f"{missing_cnt:,} cells ({missing_pct:.1f}%)",
        
        # AI Data Mentor Structured Fields
        "what_we_found": what_we_found,
        "recommended_action": rec_friendly,
        "recommended_action_friendly": rec_friendly,
        "recommended_action_technical": rec_technical,
        "action_key": action_key,
        "why_reason": why_beginner,
        "why_beginner": why_beginner,
        "why_standard": why_standard,
        "why_technical": why_technical,
        "what_will_happen": what_will_happen,
        "ai_reasoning_beginner": ai_reasoning_beginner,
        "confidence": confidence,
        "risk": risk,
        "expected_impact": what_will_happen[0],
        "alternatives": alternatives,
        "technical_evidence": technical_evidence,
        "evidence": prof,
        "execution_payload": {
            "action_type": "missing",
            "column": col_name,
            "strategy": action_key,
            "custom_value": None
        }
    }


def generate_duplicate_decision(dup_analysis: Dict[str, Any], df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """Generate intelligent recommendations for row-level duplicates following AI Data Mentor structure."""
    dup_cnt = dup_analysis.get("duplicate_rows", 0)
    dup_pct = dup_analysis.get("duplicate_percentage", 0.0)
    total_rows = len(df)

    if dup_cnt == 0:
        return None

    # Check if there are identifier columns
    id_cols = [c for c in df.columns if bool(ID_KEYWORDS.search(str(c)))]

    if dup_pct >= 15.0:
        severity = "HIGH"
        priority_weight = 90 + dup_pct
    elif dup_pct >= 5.0:
        severity = "MEDIUM"
        priority_weight = 60 + dup_pct
    else:
        severity = "LOW"
        priority_weight = 30 + dup_pct

    human_freq = _build_human_frequency_text(dup_cnt, total_rows, "records")

    what_we_found = {
        "badge": "REPEATED RECORDS FOUND",
        "column": "Entire Dataset",
        "primary_text": f"{dup_cnt:,} records appear to be exact copies",
        "secondary_text": f"{dup_pct:.1f}% of your dataset is duplicated",
        "human_summary": human_freq
    }

    rec_friendly = "Remove the repeated records"
    rec_technical = "Exact Row Deduplication"
    action_key = "remove_exact"

    why_beginner = (
        f"These {dup_cnt:,} records contain the exact same information as other rows in your dataset. "
        f"Keeping them would count the same people, transactions, or items more than once, leading to inaccurate totals."
    )
    why_standard = (
        f"Detected {dup_cnt:,} completely identical rows ({dup_pct:.1f}% of the dataset) matching across all {len(df.columns)} columns. "
        f"Keeping identical duplicates artificially inflates record counts and distorts aggregate sums (e.g. Total Revenue)."
    )
    why_technical = (
        f"Exact feature vector duplication across {len(df.columns)} dimensions. "
        f"Pseudo-replication violates observational independence, deflates empirical variance, and biases estimator precision."
    )

    what_will_happen = [
        f"{dup_cnt:,} repeated records will be removed",
        f"Your dataset will go from {total_rows:,} rows → {total_rows - dup_cnt:,} rows",
        "Every remaining row will represent a unique observation"
    ]

    ai_reasoning_beginner = (
        "AI compared all columns across every row to check for identical matches. "
        "Because these rows are 100% duplicates, removing them ensures accurate analysis without losing unique information."
    )

    alternatives = [
        {
            "rating": "★★★★★",
            "friendly_name": "Remove repeated records",
            "technical_name": "Exact deduplication",
            "strategy": "remove_exact",
            "is_recommended": True,
            "description": "Best option. Eliminates identical copies so each observation is counted once.",
            "why": "Eliminates redundant identical records; restores genuine population metrics.",
            "trade_off": f"Reduces total row count from {total_rows:,} to {total_rows - dup_cnt:,}."
        },
        {
            "rating": "★★★☆☆",
            "friendly_name": "Keep all records",
            "technical_name": "Retain duplicates for audit",
            "strategy": "keep_all",
            "is_recommended": False,
            "description": "Leaves raw records untouched if multiple entries represent real simultaneous events.",
            "why": "Leaves raw records untouched if multiple entries represent simultaneous transactions.",
            "trade_off": "Risk of duplicate aggregation and skewed predictive weights."
        }
    ]

    technical_evidence = {
        "Duplicate Rows Count": f"{dup_cnt:,}",
        "Duplicate Proportion": f"{dup_pct:.2f}%",
        "Rows Before": f"{total_rows:,}",
        "Rows After Remediation": f"{total_rows - dup_cnt:,}",
        "Columns Compared": f"{len(df.columns)} columns (Full row)",
        "Detection Algorithm": "Exact multi-column tuple matching"
    }

    return {
        "id": "duplicates_dataset_exact",
        "type": "duplicates",
        "column": "All Columns (Row-Level)",
        "title": f"Exact Duplicate Rows ({dup_cnt:,} records)",
        "severity": severity,
        "priority_weight": priority_weight,
        "affected_count": dup_cnt,
        "affected_percentage": dup_pct,
        "affected_label": f"{dup_cnt:,} rows ({dup_pct:.1f}%)",
        
        # AI Data Mentor Fields
        "what_we_found": what_we_found,
        "recommended_action": rec_friendly,
        "recommended_action_friendly": rec_friendly,
        "recommended_action_technical": rec_technical,
        "action_key": action_key,
        "why_reason": why_beginner,
        "why_beginner": why_beginner,
        "why_standard": why_standard,
        "why_technical": why_technical,
        "what_will_happen": what_will_happen,
        "ai_reasoning_beginner": ai_reasoning_beginner,
        "confidence": "HIGH",
        "risk": "LOW",
        "expected_impact": what_will_happen[0],
        "alternatives": alternatives,
        "technical_evidence": technical_evidence,
        "evidence": {
            "duplicate_count": dup_cnt,
            "duplicate_percentage": dup_pct,
            "total_rows_before": total_rows,
            "total_rows_after": total_rows - dup_cnt,
            "id_columns_found": id_cols
        },
        "execution_payload": {
            "action_type": "duplicates",
            "strategy": "remove_exact",
            "subset": None
        }
    }


def generate_outlier_decision(col_name: str, prof: Dict[str, Any], df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """Generate domain-aware outlier management recommendations following AI Data Mentor structure."""
    outlier_cnt = prof.get("outliers_count", 0)
    outlier_pct = prof.get("outliers_percentage", 0.0)
    if outlier_cnt == 0:
        return None

    col_lower = str(col_name).lower()
    lower_b = prof.get("lower_bound", 0.0)
    upper_b = prof.get("upper_bound", 0.0)
    min_v = prof.get("min", 0.0)
    max_v = prof.get("max", 0.0)
    total_rows = len(df)

    # Check for known semantic fields (e.g. Age, Salary, Revenue)
    is_age = "age" in col_lower
    is_financial = any(k in col_lower for k in ["salary", "income", "revenue", "price", "amount", "cost", "spend"])

    human_freq = f"{outlier_cnt:,} values look unusual compared with the rest of the dataset."

    what_we_found = {
        "badge": "UNUSUAL VALUES FOUND",
        "column": col_name,
        "primary_text": f"{outlier_cnt:,} values in '{col_name}' are much higher or lower than most records",
        "secondary_text": f"{outlier_pct:.1f}% of observations fall outside the standard range",
        "human_summary": human_freq
    }

    if is_age and (max_v > 120 or min_v < 0):
        severity = "HIGH"
        priority_weight = 75.0
        rec_friendly = "Cap unusual age values between 0 and 100"
        rec_technical = "Domain Boundary Capping [0, 100]"
        action_key = "cap_bounds"
        
        why_beginner = (
            f"Some recorded ages in '{col_name}' are physically impossible (Min: {min_v}, Max: {max_v}). "
            f"Capping them to realistic human limits (0 to 100) fixes data-entry typos without deleting valuable rows."
        )
        why_standard = (
            f"Column '{col_name}' contains biologically implausible age values (Min: {min_v}, Max: {max_v}). "
            f"Capping extreme tails preserves valid records while eliminating severe entry distortions."
        )
        why_technical = (
            f"Domain constraint violation detected on age attribute. Hard-clipping to [0, 100] eliminates leverage "
            f"from corrupted outliers while retaining 100% degrees of freedom in downstream models."
        )
        
        what_will_happen = [
            f"Ages below 0 or above 100 will be brought into the safe range [0, 100]",
            "No rows will be deleted",
            f"Your dataset will remain at {total_rows:,} rows"
        ]
        confidence = "HIGH"
        risk = "LOW"
    elif is_financial:
        severity = "LOW"
        priority_weight = 25.0
        rec_friendly = "Review and keep these values (Do not delete)"
        rec_technical = "Retain for Deep Segmentation (Financial Extremes)"
        action_key = "retain_outliers"
        
        why_beginner = (
            f"'{col_name}' represents financial data with {outlier_cnt:,} very large values. "
            f"In business, extreme numbers often represent your highest-paying VIP customers or large bulk sales. "
            f"Deleting them would erase your most valuable real-world business insights."
        )
        why_standard = (
            f"'{col_name}' represents financial metrics with {outlier_cnt:,} extreme observations ({outlier_pct:.1f}%). "
            f"High financial values frequently represent legitimate VIP accounts or bulk transactions. "
            f"Deleting them would artificially underestimate total economic value."
        )
        why_technical = (
            f"Heavy-tailed Pareto/log-normal distribution typical of financial variables. "
            f"Trimming would introduce severe survivorship bias and truncate revenue integrals."
        )
        
        what_will_happen = [
            "All values and customer records will be preserved exactly as recorded",
            "No rows will be deleted",
            f"Your dataset will remain at {total_rows:,} rows"
        ]
        confidence = "HIGH"
        risk = "LOW"
    else:
        severity = "MEDIUM" if outlier_pct > 8.0 else "LOW"
        priority_weight = 35.0 + outlier_pct
        rec_friendly = f"Cap extreme values at natural bounds [{lower_b:,.1f}, {upper_b:,.1f}]"
        rec_technical = "Winsorize / Cap at 1.5×IQR Bounds"
        action_key = "cap_bounds"
        
        why_beginner = (
            f"'{col_name}' has {outlier_cnt:,} numbers that sit far outside the normal range. "
            f"Bringing these extreme numbers to the boundary [{lower_b:,.1f}, {upper_b:,.1f}] prevents them from "
            f"pulling your averages in the wrong direction while keeping all your records."
        )
        why_standard = (
            f"Detected {outlier_cnt:,} observations ({outlier_pct:.1f}%) outside the 1.5×IQR boundary [{lower_b:,.2f}, {upper_b:,.2f}]. "
            f"Capping values at the threshold limits statistical leverage on linear models while preserving sample size."
        )
        why_technical = (
            f"Tukey's 1.5×IQR fence identifies {outlier_cnt} observations beyond [Q1-1.5IQR, Q3+1.5IQR]. "
            f"Winsorization bounds extreme residual influence without reducing effective sample size N={total_rows}."
        )
        
        what_will_happen = [
            f"Adjusts {outlier_cnt:,} extreme values to the safe boundary [{lower_b:,.1f}, {upper_b:,.1f}]",
            "No rows will be deleted",
            f"Your dataset will remain at {total_rows:,} rows"
        ]
        confidence = "HIGH"
        risk = "LOW"

    ai_reasoning_beginner = (
        "AI analyzed the spread of numbers in this column to spot values that sit unusually far from the majority. "
        "Rather than blindly deleting them, AI recommends reviewing or capping them to protect your analysis."
    )

    alternatives = [
        {
            "rating": "★★★★★",
            "friendly_name": "Cap extreme values at boundary",
            "technical_name": "Winsorize at 1.5×IQR",
            "strategy": "cap_bounds",
            "is_recommended": action_key == "cap_bounds",
            "description": f"Brings extreme numbers to the nearest reasonable boundary [{lower_b:,.1f}, {upper_b:,.1f}] without deleting rows.",
            "why": "Optimal balance between model stability and data retention.",
            "trade_off": "Subtle boundary clipping."
        },
        {
            "rating": "★★★★☆",
            "friendly_name": "Keep all unusual values",
            "technical_name": "Retain as valid extremes",
            "strategy": "retain_outliers",
            "is_recommended": action_key == "retain_outliers",
            "description": "Leaves all numbers untouched. Best if extreme values represent real VIP customers or transactions.",
            "why": "Preserves genuine extreme business phenomena.",
            "trade_off": "May skew mean and variance calculations."
        },
        {
            "rating": "★★☆☆☆",
            "friendly_name": "Delete rows with unusual values",
            "technical_name": "Drop outlier rows",
            "strategy": "drop_outliers",
            "is_recommended": False,
            "description": f"Permanently deletes {outlier_cnt:,} rows from your dataset.",
            "why": "Restricts data to strictly normal core distribution.",
            "trade_off": f"Eliminates {outlier_cnt:,} rows ({outlier_pct:.1f}% sample loss)."
        }
    ]

    technical_evidence = {
        "Outlier Count": f"{outlier_cnt:,} observations",
        "Outlier Proportion": f"{outlier_pct:.2f}%",
        "Lower Fence (1.5×IQR)": f"{lower_b:,.2f}",
        "Upper Fence (1.5×IQR)": f"{upper_b:,.2f}",
        "Min Observed Value": f"{min_v:,.2f}",
        "Max Observed Value": f"{max_v:,.2f}",
        "Interquartile Range (IQR)": f"{prof.get('iqr', 0.0):,.2f}",
        "Remediation Strategy": rec_technical
    }

    return {
        "id": f"outliers_{col_name.replace(' ', '_')}",
        "type": "outliers",
        "column": col_name,
        "title": f"Extreme Values in '{col_name}' ({outlier_cnt:,} outliers)",
        "severity": severity,
        "priority_weight": priority_weight,
        "affected_count": outlier_cnt,
        "affected_percentage": outlier_pct,
        "affected_label": f"{outlier_cnt:,} observations ({outlier_pct:.1f}%)",
        
        # AI Data Mentor Fields
        "what_we_found": what_we_found,
        "recommended_action": rec_friendly,
        "recommended_action_friendly": rec_friendly,
        "recommended_action_technical": rec_technical,
        "action_key": action_key,
        "why_reason": why_beginner,
        "why_beginner": why_beginner,
        "why_standard": why_standard,
        "why_technical": why_technical,
        "what_will_happen": what_will_happen,
        "ai_reasoning_beginner": ai_reasoning_beginner,
        "confidence": confidence,
        "risk": risk,
        "expected_impact": what_will_happen[0],
        "alternatives": alternatives,
        "technical_evidence": technical_evidence,
        "evidence": prof,
        "execution_payload": {
            "action_type": "outliers",
            "column": col_name,
            "strategy": action_key,
            "lower_bound": lower_b,
            "upper_bound": upper_b
        }
    }


def generate_invalid_and_type_decisions(
    validity: Dict[str, Any],
    consistency: Dict[str, Any],
    df: pd.DataFrame
) -> List[Dict[str, Any]]:
    """Generate intelligent recommendations for invalid values, type anomalies, and formatting defects."""
    decisions = []
    total_rows = len(df)

    # 1. Invalid Values (e.g. Negative values in non-negative columns)
    for inv in validity.get("invalid_findings", []):
        col = inv["column"]
        cnt = inv["count"]
        pct = inv["percentage"]
        issue_type = inv["issue_type"]

        if "Negative" in issue_type:
            rec_friendly = f"Set negative values in '{col}' to 0 (Zero)"
            rec_technical = "Clip Non-Negative Lower Boundary (>= 0)"
            act_key = "clip_non_negative"
            why_b = f"'{col}' represents quantities or counts that cannot physically be negative. Setting them to 0 fixes data-entry typos."
            why_s = f"Column '{col}' represents physical quantities or counts that cannot be negative. Negative values ({cnt:,} cells) are likely entry errors."
            why_t = f"Physical domain invariant violation (X < 0). Lower boundary rectification at zero restores domain validity."
        elif "Whitespace" in issue_type:
            rec_friendly = f"Clean blank spaces and treat as empty cells in '{col}'"
            rec_technical = "Trim Whitespace & Normalize Empty Strings"
            act_key = "trim_whitespace"
            why_b = f"Found {cnt:,} cells that contain only empty spaces. Cleaning them ensures they are recognized consistently as empty cells."
            why_s = f"Detected {cnt:,} whitespace-only strings. Converting them to standard nulls ensures uniform missingness handling."
            why_t = f"String whitespace entropy anomaly. Trimming and null normalization ensures categorical integrity."
        else:
            rec_friendly = f"Clean invalid formatting in '{col}'"
            rec_technical = "Sanitize Domain Value Anomaly"
            act_key = "clean_invalid"
            why_b = f"Found {cnt:,} entries with invalid formatting or unexpected values in '{col}'."
            why_s = inv.get("description", "Anomalous values detected outside expected domain limits.")
            why_t = "Statistical/domain rule violation across column entries."

        what_we_found = {
            "badge": "INVALID VALUES FOUND",
            "column": col,
            "primary_text": f"{cnt:,} values in '{col}' have invalid formatting or values",
            "secondary_text": f"{pct:.1f}% of entries are affected ({issue_type})",
            "human_summary": f"{cnt:,} cells contain values that violate expected rules (e.g. negative numbers or blank spaces)."
        }

        what_will_happen = [
            f"Fixes {cnt:,} invalid values in '{col}'",
            "No rows will be deleted",
            f"Your dataset will remain at {total_rows:,} rows"
        ]

        decisions.append({
            "id": f"validity_{col.replace(' ', '_')}_{cnt}",
            "type": "validity",
            "column": col,
            "title": f"Invalid Values in '{col}' ({issue_type})",
            "severity": inv.get("severity", "MEDIUM"),
            "priority_weight": 50 + pct,
            "affected_count": cnt,
            "affected_percentage": pct,
            "affected_label": f"{cnt:,} cells ({pct:.1f}%)",
            "what_we_found": what_we_found,
            "recommended_action": rec_friendly,
            "recommended_action_friendly": rec_friendly,
            "recommended_action_technical": rec_technical,
            "action_key": act_key,
            "why_reason": why_b,
            "why_beginner": why_b,
            "why_standard": why_s,
            "why_technical": why_t,
            "what_will_happen": what_will_happen,
            "ai_reasoning_beginner": "AI identified values that do not match the expected real-world format and recommended a safe correction.",
            "confidence": "HIGH",
            "risk": "LOW",
            "expected_impact": what_will_happen[0],
            "alternatives": [
                {"rating": "★★★★★", "friendly_name": "Fix invalid values", "technical_name": rec_technical, "label": rec_friendly, "strategy": act_key, "is_recommended": True, "description": "Standard data hygiene.", "why": "Standard data hygiene.", "trade_off": "None."},
                {"rating": "★★☆☆☆", "friendly_name": "Delete affected rows", "technical_name": "Drop invalid rows", "label": "Drop Rows with Invalid Values", "strategy": "drop_invalid_rows", "is_recommended": False, "description": "Deletes rows with errors.", "why": "Strict complete data.", "trade_off": f"Discards {cnt:,} records."}
            ],
            "technical_evidence": {
                "Issue Type": issue_type,
                "Affected Cells": f"{cnt:,}",
                "Affected Percentage": f"{pct:.2f}%",
                "Column Name": col
            },
            "evidence": inv,
            "execution_payload": {
                "action_type": "validity",
                "column": col,
                "strategy": act_key
            }
        })

    # 2. Type Inconsistencies & Currency/Percentage Strings
    for inc in consistency.get("type_inconsistencies", []):
        col = inc["column"]
        cnt = inc["inconsistent_count"]
        pct = inc["inconsistent_percentage"]

        rec_friendly = f"Convert '{col}' into clean numbers"
        rec_technical = "Sanitize & Cast to Numeric"
        act_key = "cast_numeric_clean"

        what_we_found = {
            "badge": "MIXED DATA TYPES FOUND",
            "column": col,
            "primary_text": f"'{col}' has mixed text and numbers",
            "secondary_text": f"{cnt:,} entries contain symbols (like $ or %) preventing calculations",
            "human_summary": f"{cnt:,} values contain symbols or mixed formatting that prevent charts and sums."
        }

        why_b = f"'{col}' contains numbers mixed with text or currency symbols (like $ or %). Cleaning the symbols turns them into real numbers so you can calculate sums, averages, and build charts."
        why_s = f"Column '{col}' contains mixed text and numeric data. Mixed types prevent mathematical calculations and charts."
        why_t = f"Mixed dtype column. Stripping currency/percentage symbols and casting to float64 unlocks vectorized numerical operations."

        what_will_happen = [
            f"Cleans symbols and converts {cnt:,} entries into standard numbers",
            "No rows will be deleted",
            f"Your dataset will remain at {total_rows:,} rows"
        ]

        decisions.append({
            "id": f"type_inconsistency_{col.replace(' ', '_')}",
            "type": "consistency",
            "column": col,
            "title": f"Mixed Data Types in '{col}'",
            "severity": "HIGH",
            "priority_weight": 65 + pct,
            "affected_count": cnt,
            "affected_percentage": pct,
            "affected_label": f"{cnt:,} inconsistent values ({pct:.1f}%)",
            "what_we_found": what_we_found,
            "recommended_action": rec_friendly,
            "recommended_action_friendly": rec_friendly,
            "recommended_action_technical": rec_technical,
            "action_key": act_key,
            "why_reason": why_b,
            "why_beginner": why_b,
            "why_standard": why_s,
            "why_technical": why_t,
            "what_will_happen": what_will_happen,
            "ai_reasoning_beginner": "AI found currency or percentage symbols mixed into number columns and recommends standardizing them for calculations.",
            "confidence": "HIGH",
            "risk": "LOW",
            "expected_impact": what_will_happen[0],
            "alternatives": [
                {"rating": "★★★★★", "friendly_name": "Clean and convert to numbers", "technical_name": "Cast to numeric", "label": "Sanitize & Cast to Numeric", "strategy": "cast_numeric_clean", "is_recommended": True, "description": "Unlocks mathematical analysis and charting.", "why": "Unlocks full mathematical analysis.", "trade_off": "Unparseable text becomes null."},
                {"rating": "★★★☆☆", "friendly_name": "Keep as plain text", "technical_name": "Retain as string", "label": "Retain as String/Text", "strategy": "keep_string", "is_recommended": False, "description": "Leaves characters as text. Blocks math.", "why": "Preserves raw characters.", "trade_off": "Blocks mathematical aggregations."}
            ],
            "technical_evidence": {
                "Inconsistent Count": f"{cnt:,}",
                "Inconsistent Percentage": f"{pct:.2f}%",
                "Sample Text Values": str(inc.get("sample_values", []))[:80],
                "Target Dtype": "float64"
            },
            "evidence": inc,
            "execution_payload": {
                "action_type": "consistency",
                "column": col,
                "strategy": "cast_numeric_clean"
            }
        })

    # 3. Empty Columns (100% missing)
    for empty_col in consistency.get("empty_columns", []):
        decisions.append({
            "id": f"empty_col_{empty_col.replace(' ', '_')}",
            "type": "structure",
            "column": empty_col,
            "title": f"100% Empty Column: '{empty_col}'",
            "severity": "CRITICAL",
            "priority_weight": 120.0,
            "affected_count": len(df),
            "affected_percentage": 100.0,
            "affected_label": f"100% null cells ({len(df):,} rows)",
            "recommended_action": "Drop Empty Column",
            "action_key": "drop_cols",
            "why_reason": f"Column '{empty_col}' contains zero non-null values across the entire dataset. It provides zero analytical value.",
            "confidence": "HIGH",
            "risk": "LOW",
            "expected_impact": f"Removes '{empty_col}'. Reduces column count by 1.",
            "alternatives": [
                {"rating": "★★★★★", "label": "Drop Empty Column", "strategy": "drop_cols", "is_recommended": True, "why": "Eliminates dead feature.", "trade_off": "None."}
            ],
            "evidence": {"empty_column": empty_col},
            "execution_payload": {
                "action_type": "missing",
                "column": empty_col,
                "strategy": "drop_cols"
            }
        })

    return decisions


def generate_quality_decision_plan(df: pd.DataFrame, audit_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Consolidate all intelligent decision recommendations across missing values,
    duplicates, outliers, validity, and consistency, prioritized by severity.
    """
    decisions: List[Dict[str, Any]] = []

    # 1. Duplicates Decision
    dup_dec = generate_duplicate_decision(audit_report.get("duplicate_analysis", {}), df)
    if dup_dec:
        decisions.append(dup_dec)

    # 2. Missing Values Decisions
    missing_analysis = audit_report.get("missing_analysis", {})
    for item in missing_analysis.get("column_missing_details", []):
        if item["missing_count"] > 0:
            col_name = item["column_name"]
            if col_name in df.columns:
                prof = investigate_column_distribution(df[col_name], col_name, df)
                m_dec = generate_missing_value_decision(col_name, prof, df)
                decisions.append(m_dec)

    # 3. Outlier Decisions
    outlier_analysis = audit_report.get("outlier_analysis", {})
    for out in outlier_analysis.get("column_outliers", []):
        col_name = out["column"]
        if col_name in df.columns:
            prof = investigate_column_distribution(df[col_name], col_name, df)
            o_dec = generate_outlier_decision(col_name, prof, df)
            if o_dec:
                decisions.append(o_dec)

    # 4. Invalid & Type Inconsistencies Decisions
    inv_decisions = generate_invalid_and_type_decisions(
        validity=audit_report.get("validity_analysis", {}),
        consistency=audit_report.get("consistency_analysis", {}),
        df=df
    )
    decisions.extend(inv_decisions)

    # 5. Sort by Global Priority Weight (Highest severity first)
    sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    decisions.sort(key=lambda x: (sev_order.get(x.get("severity", "INFO"), 5), -x.get("priority_weight", 0.0)))

    return decisions


# =============================================================================
# DECISION PREVIEW, EXECUTION & IMPACT VERIFICATION
# =============================================================================

def preview_decision_transformation(
    df: pd.DataFrame,
    decision: Dict[str, Any],
    custom_strategy: Optional[str] = None
) -> Dict[str, Any]:
    """
    Simulate the execution of a decision recommendation on a copy of df
    to generate exact before/after metrics and sample data preview.
    """
    if df is None or df.empty:
        return {}

    strategy = custom_strategy or decision.get("action_key", "median")
    col = decision.get("column")
    action_type = decision.get("type", "missing")
    
    rows_before = len(df)
    cols_before = len(df.columns)
    missing_before = int(df.isna().sum().sum())
    completeness_before = float((1.0 - (missing_before / (rows_before * cols_before))) * 100) if (rows_before * cols_before) > 0 else 100.0

    stat_before = {}
    if col and col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
        s = df[col].dropna()
        if not s.empty:
            stat_before = {
                "mean": float(s.mean()),
                "median": float(s.median()),
                "std": float(s.std(ddof=1)) if len(s) > 1 else 0.0,
                "missing_in_col": int(df[col].isna().sum())
            }

    # Execute simulation
    sim_df, transform_meta = apply_decision_transformation(df, decision, custom_strategy=strategy)

    rows_after = len(sim_df)
    cols_after = len(sim_df.columns)
    missing_after = int(sim_df.isna().sum().sum())
    completeness_after = float((1.0 - (missing_after / (rows_after * cols_after))) * 100) if (rows_after * cols_after) > 0 else 100.0

    stat_after = {}
    if col and col in sim_df.columns and pd.api.types.is_numeric_dtype(sim_df[col]):
        s_after = sim_df[col].dropna()
        if not s_after.empty:
            stat_after = {
                "mean": float(s_after.mean()),
                "median": float(s_after.median()),
                "std": float(s_after.std(ddof=1)) if len(s_after) > 1 else 0.0,
                "missing_in_col": int(sim_df[col].isna().sum())
            }

    # Sample rows preview
    sample_before = df.head(5)
    sample_after = sim_df.head(5)

    return {
        "strategy_applied": strategy,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "row_delta": rows_after - rows_before,
        "cols_before": cols_before,
        "cols_after": cols_after,
        "col_delta": cols_after - cols_before,
        "missing_before": missing_before,
        "missing_after": missing_after,
        "missing_delta": missing_after - missing_before,
        "completeness_before": round(completeness_before, 1),
        "completeness_after": round(completeness_after, 1),
        "completeness_delta": round(completeness_after - completeness_before, 1),
        "stat_before": stat_before,
        "stat_after": stat_after,
        "sample_before": sample_before,
        "sample_after": sample_after,
        "affected_count": transform_meta.get("affected_count", 0),
        "description": transform_meta.get("description", "")
    }


def apply_decision_transformation(
    df: pd.DataFrame,
    decision: Dict[str, Any],
    custom_strategy: Optional[str] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Safely execute a quality remediation transformation on df.
    Returns (transformed_df, transformation_metadata).
    """
    if df is None or df.empty:
        return df, {"affected_count": 0, "description": "Empty dataset"}

    new_df = df.copy(deep=True)
    strategy = custom_strategy or decision.get("action_key", "median")
    col = decision.get("column")
    action_type = decision.get("type", "missing")
    affected_count = 0
    desc = ""

    # 1. Duplicates
    if action_type == "duplicates" or strategy == "remove_exact":
        before_cnt = len(new_df)
        new_df = new_df.drop_duplicates(keep="first").reset_index(drop=True)
        affected_count = before_cnt - len(new_df)
        desc = f"Removed {affected_count:,} exact duplicate rows"

    # 2. Missing Values Handling
    elif action_type == "missing" or strategy in ["median", "mean", "mode", "zero", "unknown", "ffill", "bfill", "drop_rows", "drop_cols"]:
        if strategy == "drop_cols" and col in new_df.columns:
            new_df = new_df.drop(columns=[col])
            affected_count = len(df)
            desc = f"Dropped column '{col}'"

        elif strategy == "drop_rows" and col in new_df.columns:
            before_cnt = len(new_df)
            new_df = new_df.dropna(subset=[col]).reset_index(drop=True)
            affected_count = before_cnt - len(new_df)
            desc = f"Dropped {affected_count:,} rows with missing '{col}'"

        elif col in new_df.columns:
            missing_mask = new_df[col].isna()
            affected_count = int(missing_mask.sum())
            
            if affected_count > 0:
                if strategy == "median" and pd.api.types.is_numeric_dtype(new_df[col]):
                    fill_val = new_df[col].median()
                    new_df[col] = new_df[col].fillna(fill_val)
                    desc = f"Imputed {affected_count:,} missing values in '{col}' with median ({fill_val:,.2f})"

                elif strategy == "mean" and pd.api.types.is_numeric_dtype(new_df[col]):
                    fill_val = new_df[col].mean()
                    new_df[col] = new_df[col].fillna(fill_val)
                    desc = f"Imputed {affected_count:,} missing values in '{col}' with mean ({fill_val:,.2f})"

                elif strategy == "mode":
                    mode_val = new_df[col].mode()
                    fill_val = mode_val.iloc[0] if not mode_val.empty else "Unknown"
                    new_df[col] = new_df[col].fillna(fill_val)
                    desc = f"Imputed {affected_count:,} missing values in '{col}' with mode ('{fill_val}')"

                elif strategy == "zero":
                    new_df[col] = new_df[col].fillna(0)
                    desc = f"Imputed {affected_count:,} missing values in '{col}' with 0"

                elif strategy == "unknown":
                    new_df[col] = new_df[col].fillna("Unknown")
                    desc = f"Replaced {affected_count:,} missing values in '{col}' with 'Unknown'"

                elif strategy == "ffill":
                    new_df[col] = new_df[col].ffill().bfill()
                    desc = f"Forward-filled {affected_count:,} missing values in '{col}'"

                elif strategy == "bfill":
                    new_df[col] = new_df[col].bfill().ffill()
                    desc = f"Backward-filled {affected_count:,} missing values in '{col}'"

    # 3. Outlier Capping
    elif action_type == "outliers" or strategy == "cap_bounds":
        if col in new_df.columns and pd.api.types.is_numeric_dtype(new_df[col]):
            payload = decision.get("execution_payload", {})
            lower_b = payload.get("lower_bound")
            upper_b = payload.get("upper_bound")
            
            if lower_b is None or upper_b is None:
                q25 = new_df[col].quantile(0.25)
                q75 = new_df[col].quantile(0.75)
                iqr = q75 - q25
                lower_b = q25 - 1.5 * iqr
                upper_b = q75 + 1.5 * iqr

            out_mask = (new_df[col] < lower_b) | (new_df[col] > upper_b)
            affected_count = int(out_mask.sum())
            new_df[col] = new_df[col].clip(lower=lower_b, upper=upper_b)
            desc = f"Capped {affected_count:,} outliers in '{col}' to bounds [{lower_b:,.2f}, {upper_b:,.2f}]"

    # 4. Validity & Type Cleansing
    elif strategy == "clip_non_negative" and col in new_df.columns:
        if pd.api.types.is_numeric_dtype(new_df[col]):
            neg_mask = new_df[col] < 0
            affected_count = int(neg_mask.sum())
            new_df[col] = new_df[col].clip(lower=0)
            desc = f"Clipped {affected_count:,} negative values in '{col}' to 0"

    elif strategy == "trim_whitespace" and col in new_df.columns:
        if pd.api.types.is_object_dtype(new_df[col]):
            s_str = new_df[col].astype(str).str.strip()
            blank_mask = (s_str == "") | (s_str == "nan") | (s_str == "None")
            affected_count = int(blank_mask.sum())
            new_df[col] = new_df[col].astype(str).str.strip().replace("", np.nan)
            desc = f"Trimmed whitespace and standardized {affected_count:,} blank cells in '{col}' to null"

    elif strategy == "cast_numeric_clean" and col in new_df.columns:
        s_clean = new_df[col].astype(str).str.replace(r"[,\$€£₹\s%]", "", regex=True)
        converted = pd.to_numeric(s_clean, errors="coerce")
        affected_count = int(converted.notna().sum())
        new_df[col] = converted
        desc = f"Cleaned symbols and cast column '{col}' to numeric ({affected_count:,} values parsed)"

    meta = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "operation": decision.get("recommended_action", "Quality Remediation"),
        "column": col or "Dataset",
        "strategy": strategy,
        "affected_count": affected_count,
        "description": desc,
        "reason": decision.get("why_reason", "")
    }

    return new_df, meta


def verify_decision_impact(
    df_before: pd.DataFrame,
    df_after: pd.DataFrame,
    decision: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute post-transformation verification check comparing before and after
    quality metrics, verifying improvement, and identifying potential side effects.
    """
    audit_before = analyze_data_quality(df_before)
    audit_after = analyze_data_quality(df_after)

    score_before = audit_before["overall_score"]
    score_after = audit_after["overall_score"]
    score_delta = round(score_after - score_before, 1)

    warnings = []
    col = decision.get("column")

    # Check for variance collapse side effect on numeric columns
    if col and col in df_before.columns and col in df_after.columns:
        if pd.api.types.is_numeric_dtype(df_before[col]) and pd.api.types.is_numeric_dtype(df_after[col]):
            std_b = df_before[col].std(ddof=1)
            std_a = df_after[col].std(ddof=1)
            if std_b > 0 and (std_a / std_b) < 0.60:
                warnings.append(
                    f"Standard deviation for '{col}' decreased by {((1 - std_a/std_b)*100):.1f}% "
                    f"due to central value replacement. Verify distribution before training sensitive ML models."
                )

    # Check for unexpected row reduction
    if len(df_after) < len(df_before) and decision.get("action_key") not in ["drop_rows", "remove_exact"]:
        warnings.append(f"Unexpected row count reduction ({len(df_before):,} → {len(df_after):,} rows).")

    return {
        "score_before": score_before,
        "score_after": score_after,
        "score_delta": score_delta,
        "improved": score_delta > 0,
        "breakdown_before": audit_before["breakdown"],
        "breakdown_after": audit_after["breakdown"],
        "warnings": warnings
    }


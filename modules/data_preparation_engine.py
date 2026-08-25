"""
DATA STUDIO v2 — Data Preparation & Transformation Engine
=============================================================================
Modular, decoupled engine for:
- Non-destructive DataFrame transformations
- Missing value imputation and row/column removal
- Whole-row and column-subset duplicate removal
- Column management (Rename with validation, Drop, Reorder, Safe Type Casting)
- Type-aware visual filtering and compound chaining
- Single and multi-column persistent sorting
- IQR-based outlier detection, row removal, and boundary capping
- Text & string cleaning (Trim, Lower, Upper, Title, Find/Replace, Empty handling)
- Date parsing and component extraction (Year, Month, Day, Day of Week, Quarter)
- Safe arithmetic and percentage column derivations (No eval/exec)
- Export to CSV and Excel (XLSX) bytes
"""
from typing import Optional, Dict, Any, List, Tuple, Union
import io
import re
import datetime
import pandas as pd
import numpy as np


# =============================================================================
# MISSING VALUE HANDLING
# =============================================================================

def get_missing_values_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Generate a detailed missing value profile table per column."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["Column", "Data Type", "Missing Count", "Missing %", "Recommended Action"])

    total_rows = len(df)
    records = []

    for col in df.columns:
        series = df[col]
        missing_count = int(series.isna().sum())
        missing_pct = (missing_count / total_rows * 100) if total_rows > 0 else 0.0
        dtype_str = str(series.dtype)

        # Determine recommendation
        if missing_count == 0:
            rec = "Complete (No Action Needed)"
        elif missing_pct > 70.0:
            rec = "Consider Dropping Column (>70% missing)"
        elif pd.api.types.is_numeric_dtype(series):
            if abs(series.skew()) > 1.0 if len(series.dropna()) >= 3 else False:
                rec = "Fill with Median (Skewed)"
            else:
                rec = "Fill with Mean or Median"
        elif pd.api.types.is_datetime64_any_dtype(series):
            rec = "Drop Rows or Forward Fill"
        else:
            rec = "Fill with Mode or 'Unknown'"

        records.append({
            "Column": str(col),
            "Data Type": dtype_str,
            "Missing Count": missing_count,
            "Missing %": round(missing_pct, 2),
            "Recommended Action": rec
        })

    return pd.DataFrame(records)


def handle_missing_values(
    df: pd.DataFrame,
    columns: List[str],
    strategy: str,
    custom_value: Optional[Any] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Handle missing values across selected columns.
    Strategies:
    - 'drop_rows': Drop any rows where specified columns are NA
    - 'drop_cols': Drop the specified columns entirely
    - 'mean': Fill with column mean (numeric only)
    - 'median': Fill with column median (numeric only)
    - 'zero': Fill with 0 (numeric)
    - 'mode': Fill with most frequent value
    - 'unknown': Fill with 'Unknown' string
    - 'custom': Fill with custom provided value
    - 'ffill': Forward fill previous valid value
    - 'bfill': Backward fill next valid value
    """
    if df is None or df.empty:
        return df, {"rows_before": 0, "rows_after": 0, "cols_before": 0, "cols_after": 0, "affected": 0}

    new_df = df.copy(deep=True)
    rows_before = len(new_df)
    cols_before = len(new_df.columns)
    valid_cols = [c for c in columns if c in new_df.columns]

    if not valid_cols:
        return new_df, {"rows_before": rows_before, "rows_after": rows_before, "cols_before": cols_before, "cols_after": cols_before, "affected": 0}

    affected_count = 0

    if strategy == "drop_rows":
        missing_mask = new_df[valid_cols].isna().any(axis=1)
        affected_count = int(missing_mask.sum())
        new_df = new_df[~missing_mask].reset_index(drop=True)

    elif strategy == "drop_cols":
        affected_count = len(valid_cols)
        new_df = new_df.drop(columns=valid_cols)

    elif strategy in ["mean", "median", "zero", "mode", "unknown", "custom", "ffill", "bfill"]:
        for col in valid_cols:
            col_missing = int(new_df[col].isna().sum())
            if col_missing == 0:
                continue

            if strategy == "mean" and pd.api.types.is_numeric_dtype(new_df[col]):
                fill_val = new_df[col].mean()
                if pd.notna(fill_val):
                    new_df[col] = new_df[col].fillna(fill_val)
                    affected_count += col_missing

            elif strategy == "median" and pd.api.types.is_numeric_dtype(new_df[col]):
                fill_val = new_df[col].median()
                if pd.notna(fill_val):
                    new_df[col] = new_df[col].fillna(fill_val)
                    affected_count += col_missing

            elif strategy == "zero":
                fill_val = 0 if pd.api.types.is_numeric_dtype(new_df[col]) else "0"
                new_df[col] = new_df[col].fillna(fill_val)
                affected_count += col_missing

            elif strategy == "mode":
                mode_series = new_df[col].mode(dropna=True)
                if not mode_series.empty:
                    fill_val = mode_series.iloc[0]
                    new_df[col] = new_df[col].fillna(fill_val)
                    affected_count += col_missing

            elif strategy == "unknown":
                new_df[col] = new_df[col].fillna("Unknown")
                affected_count += col_missing

            elif strategy == "custom":
                if custom_value is not None:
                    # Convert to numeric if column is numeric and custom_val is parsable
                    if pd.api.types.is_numeric_dtype(new_df[col]):
                        try:
                            c_val = float(custom_value)
                            if int(c_val) == c_val:
                                c_val = int(c_val)
                        except (ValueError, TypeError):
                            c_val = custom_value
                    else:
                        c_val = str(custom_value)
                    new_df[col] = new_df[col].fillna(c_val)
                    affected_count += col_missing

            elif strategy == "ffill":
                new_df[col] = new_df[col].ffill()
                affected_count += col_missing

            elif strategy == "bfill":
                new_df[col] = new_df[col].bfill()
                affected_count += col_missing

    rows_after = len(new_df)
    cols_after = len(new_df.columns)

    return new_df, {
        "rows_before": rows_before,
        "rows_after": rows_after,
        "cols_before": cols_before,
        "cols_after": cols_after,
        "affected": affected_count
    }


# =============================================================================
# DUPLICATE HANDLING
# =============================================================================

def get_duplicates_info(df: pd.DataFrame, subset_cols: Optional[List[str]] = None) -> Dict[str, Any]:
    """Inspect and return duplicate counts and duplicated row records."""
    if df is None or df.empty:
        return {"total_rows": 0, "duplicate_count": 0, "duplicate_pct": 0.0, "duplicate_df": pd.DataFrame()}

    cols = [c for c in subset_cols if c in df.columns] if subset_cols else None
    dup_mask = df.duplicated(subset=cols, keep=False)
    dup_count = int(df.duplicated(subset=cols, keep="first").sum())
    total_rows = len(df)
    dup_pct = (dup_count / total_rows * 100) if total_rows > 0 else 0.0
    dup_df = df[dup_mask].copy()

    return {
        "total_rows": total_rows,
        "duplicate_count": dup_count,
        "duplicate_pct": round(dup_pct, 2),
        "duplicate_df": dup_df
    }


def remove_duplicates(df: pd.DataFrame, subset_cols: Optional[List[str]] = None, keep: str = "first") -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Remove duplicate rows based on all or a subset of columns."""
    if df is None or df.empty:
        return df, {"rows_before": 0, "rows_after": 0, "removed_count": 0}

    rows_before = len(df)
    cols = [c for c in subset_cols if c in df.columns] if subset_cols else None
    new_df = df.drop_duplicates(subset=cols, keep=keep).reset_index(drop=True)
    rows_after = len(new_df)
    removed_count = rows_before - rows_after

    return new_df, {
        "rows_before": rows_before,
        "rows_after": rows_after,
        "removed_count": removed_count
    }


# =============================================================================
# COLUMN MANAGEMENT (Rename, Drop, Reorder, Cast Type)
# =============================================================================

def rename_column(df: pd.DataFrame, old_name: str, new_name: str) -> Tuple[pd.DataFrame, bool, str]:
    """Rename a single column with collision and validity checks."""
    if df is None or df.empty:
        return df, False, "Dataset is empty."

    if not old_name or old_name not in df.columns:
        return df, False, f"Source column '{old_name}' not found."

    clean_new = str(new_name).strip()
    if not clean_new:
        return df, False, "New column name cannot be blank."

    if clean_new in df.columns and clean_new != old_name:
        return df, False, f"A column named '{clean_new}' already exists."

    new_df = df.rename(columns={old_name: clean_new})
    return new_df, True, f"Renamed '{old_name}' to '{clean_new}'"


def drop_columns(df: pd.DataFrame, columns_to_drop: List[str]) -> Tuple[pd.DataFrame, List[str]]:
    """Drop specified columns safely."""
    if df is None or df.empty or not columns_to_drop:
        return df, []

    valid_drop = [c for c in columns_to_drop if c in df.columns]
    if not valid_drop:
        return df, []

    # Ensure we do not drop ALL columns
    if len(valid_drop) >= len(df.columns):
        return df, []

    new_df = df.drop(columns=valid_drop)
    return new_df, valid_drop


def reorder_columns(df: pd.DataFrame, ordered_columns: List[str]) -> Tuple[pd.DataFrame, bool]:
    """Reorder DataFrame columns safely."""
    if df is None or df.empty or not ordered_columns:
        return df, False

    # Keep all existing columns, placing requested ordered ones first
    existing_cols = list(df.columns)
    valid_ordered = [c for c in ordered_columns if c in existing_cols]
    remaining = [c for c in existing_cols if c not in valid_ordered]
    final_order = valid_ordered + remaining

    new_df = df[final_order].copy()
    return new_df, True


def cast_column_type(
    df: pd.DataFrame,
    column: str,
    target_type: str,
    datetime_format: Optional[str] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Safely cast column to target data type:
    - 'Numeric' (float or int)
    - 'Integer'
    - 'Float'
    - 'String'
    - 'Category'
    - 'Boolean'
    - 'Datetime'
    Tracks successful conversions vs coerced/invalid values without destroying data silently.
    """
    if df is None or df.empty or column not in df.columns:
        return df, {"success": False, "error": "Column not found", "converted": 0, "coerced_na": 0}

    new_df = df.copy(deep=True)
    orig_series = new_df[column]
    orig_na = int(orig_series.isna().sum())
    total_count = len(orig_series)

    converted_count = 0
    coerced_na_count = 0

    try:
        if target_type == "Numeric":
            res_series = pd.to_numeric(orig_series, errors="coerce")
            new_na = int(res_series.isna().sum())
            coerced_na_count = max(0, new_na - orig_na)
            converted_count = total_count - new_na
            new_df[column] = res_series

        elif target_type == "Integer":
            num_series = pd.to_numeric(orig_series, errors="coerce")
            # Using Int64 nullable integer
            res_series = num_series.round().astype("Int64")
            new_na = int(res_series.isna().sum())
            coerced_na_count = max(0, new_na - orig_na)
            converted_count = total_count - new_na
            new_df[column] = res_series

        elif target_type == "Float":
            res_series = pd.to_numeric(orig_series, errors="coerce").astype(float)
            new_na = int(res_series.isna().sum())
            coerced_na_count = max(0, new_na - orig_na)
            converted_count = total_count - new_na
            new_df[column] = res_series

        elif target_type == "String":
            new_df[column] = orig_series.astype(str).replace("nan", np.nan).replace("None", np.nan)
            converted_count = total_count - int(new_df[column].isna().sum())
            coerced_na_count = 0

        elif target_type == "Category":
            new_df[column] = orig_series.astype("category")
            converted_count = total_count - int(new_df[column].isna().sum())
            coerced_na_count = 0

        elif target_type == "Boolean":
            # Map standard truthy/falsy values
            bool_map = {
                "true": True, "1": True, "1.0": True, "yes": True, "y": True, "t": True, "active": True,
                "false": False, "0": False, "0.0": False, "no": False, "n": False, "f": False, "inactive": False
            }
            def parse_bool(v):
                if pd.isna(v):
                    return np.nan
                if isinstance(v, bool):
                    return v
                str_v = str(v).strip().lower()
                return bool_map.get(str_v, np.nan)

            res_series = orig_series.map(parse_bool).astype("boolean")
            new_na = int(res_series.isna().sum())
            coerced_na_count = max(0, new_na - orig_na)
            converted_count = total_count - new_na
            new_df[column] = res_series

        elif target_type == "Datetime":
            if datetime_format:
                res_series = pd.to_datetime(orig_series, format=datetime_format, errors="coerce")
            else:
                try:
                    res_series = pd.to_datetime(orig_series, errors="coerce", format="mixed")
                except TypeError:
                    res_series = pd.to_datetime(orig_series, errors="coerce")

            new_na = int(res_series.isna().sum())
            coerced_na_count = max(0, new_na - orig_na)
            converted_count = total_count - new_na
            new_df[column] = res_series

        else:
            return df, {"success": False, "error": f"Unknown target type: {target_type}"}

        return new_df, {
            "success": True,
            "converted": converted_count,
            "coerced_na": coerced_na_count,
            "prev_dtype": str(orig_series.dtype),
            "new_dtype": str(new_df[column].dtype)
        }

    except Exception as e:
        return df, {"success": False, "error": str(e), "converted": 0, "coerced_na": 0}


# =============================================================================
# VISUAL FILTER BUILDER
# =============================================================================

def apply_filters(df: pd.DataFrame, filter_rules: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Evaluate multiple filter rules safely without eval/exec.
    Each rule:
    {
        "column": str,
        "operator": str,
        "value": Any,
        "value_end": Optional[Any] (for 'between')
    }
    """
    if df is None or df.empty or not filter_rules:
        return df, {"rows_before": len(df) if df is not None else 0, "rows_after": len(df) if df is not None else 0, "removed": 0}

    rows_before = len(df)
    combined_mask = pd.Series(True, index=df.index)

    for rule in filter_rules:
        col = rule.get("column")
        op = rule.get("operator")
        val = rule.get("value")
        val_end = rule.get("value_end")

        if not col or col not in df.columns or not op:
            continue

        series = df[col]
        rule_mask = pd.Series(True, index=df.index)

        # 1. Numeric Operators
        if pd.api.types.is_numeric_dtype(series):
            num_series = pd.to_numeric(series, errors="coerce")
            try:
                num_val = float(val) if val is not None else 0.0
                if op == "Equals (=)":
                    rule_mask = (num_series == num_val)
                elif op == "Not Equals (!=)":
                    rule_mask = (num_series != num_val)
                elif op == "Greater Than (>)":
                    rule_mask = (num_series > num_val)
                elif op == "Greater or Equal (>=)":
                    rule_mask = (num_series >= num_val)
                elif op == "Less Than (<)":
                    rule_mask = (num_series < num_val)
                elif op == "Less or Equal (<=)":
                    rule_mask = (num_series <= num_val)
                elif op == "Between":
                    num_end = float(val_end) if val_end is not None else num_val
                    rule_mask = (num_series >= min(num_val, num_end)) & (num_series <= max(num_val, num_end))
                elif op == "Is Null / Missing":
                    rule_mask = num_series.isna()
                elif op == "Is Not Null":
                    rule_mask = num_series.notna()
            except (ValueError, TypeError):
                continue

        # 2. Datetime Operators
        elif pd.api.types.is_datetime64_any_dtype(series):
            dt_series = pd.to_datetime(series, errors="coerce")
            try:
                dt_val = pd.to_datetime(val) if val else None
                if op == "Before (<)":
                    rule_mask = (dt_series < dt_val)
                elif op == "After (>)":
                    rule_mask = (dt_series > dt_val)
                elif op == "Equals":
                    rule_mask = (dt_series.dt.date == dt_val.date()) if dt_val else pd.Series(True, index=df.index)
                elif op == "Between":
                    dt_end = pd.to_datetime(val_end) if val_end else dt_val
                    rule_mask = (dt_series >= dt_val) & (dt_series <= dt_end)
                elif op == "Is Null / Missing":
                    rule_mask = dt_series.isna()
                elif op == "Is Not Null":
                    rule_mask = dt_series.notna()
            except Exception:
                continue

        # 3. String / Categorical Operators
        else:
            str_series = series.astype(str).str.lower()
            str_val = str(val).lower() if val is not None else ""

            if op == "Equals":
                rule_mask = (str_series == str_val)
            elif op == "Not Equals":
                rule_mask = (str_series != str_val)
            elif op == "Contains":
                rule_mask = str_series.str.contains(re.escape(str_val), na=False)
            elif op == "Starts with":
                rule_mask = str_series.str.startswith(str_val, na=False)
            elif op == "Ends with":
                rule_mask = str_series.str.endswith(str_val, na=False)
            elif op == "Is one of":
                if isinstance(val, list):
                    items = [str(x).lower() for x in val]
                    rule_mask = str_series.isin(items)
                elif isinstance(val, str):
                    items = [x.strip().lower() for x in val.split(",") if x.strip()]
                    rule_mask = str_series.isin(items)
            elif op == "Is Null / Missing":
                rule_mask = series.isna() | (series.astype(str).str.strip() == "")
            elif op == "Is Not Null":
                rule_mask = series.notna() & (series.astype(str).str.strip() != "")

        combined_mask = combined_mask & rule_mask

    filtered_df = df[combined_mask].reset_index(drop=True)
    rows_after = len(filtered_df)

    return filtered_df, {
        "rows_before": rows_before,
        "rows_after": rows_after,
        "removed": rows_before - rows_after
    }


# =============================================================================
# PERSISTENT SORTING
# =============================================================================

def sort_dataset(df: pd.DataFrame, sort_columns: List[str], ascending_list: List[bool]) -> Tuple[pd.DataFrame, bool]:
    """Sort dataset by one or multiple columns."""
    if df is None or df.empty or not sort_columns:
        return df, False

    valid_cols = [c for c in sort_columns if c in df.columns]
    if not valid_cols:
        return df, False

    # Adjust ascending list length to match valid cols
    asc_flags = ascending_list[:len(valid_cols)]
    if len(asc_flags) < len(valid_cols):
        asc_flags += [True] * (len(valid_cols) - len(asc_flags))

    sorted_df = df.sort_values(by=valid_cols, ascending=asc_flags).reset_index(drop=True)
    return sorted_df, True


# =============================================================================
# IQR OUTLIER HANDLING (Cap, Remove, Review)
# =============================================================================

def get_outliers_profile(df: pd.DataFrame, column: str) -> Dict[str, Any]:
    """Detect IQR outliers and compute upper/lower bounds for a numeric column."""
    if df is None or df.empty or column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
        return {"outlier_count": 0, "lower_bound": 0, "upper_bound": 0, "q1": 0, "q3": 0, "iqr": 0, "outlier_df": pd.DataFrame()}

    series = pd.to_numeric(df[column], errors="coerce").dropna()
    if len(series) < 4:
        return {"outlier_count": 0, "lower_bound": 0, "upper_bound": 0, "q1": 0, "q3": 0, "iqr": 0, "outlier_df": pd.DataFrame()}

    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outlier_mask = (df[column] < lower_bound) | (df[column] > upper_bound)
    outlier_count = int(outlier_mask.sum())
    outlier_df = df[outlier_mask].copy()

    return {
        "outlier_count": outlier_count,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "outlier_df": outlier_df
    }


def handle_outliers(
    df: pd.DataFrame,
    column: str,
    action: str  # 'remove_rows', 'cap_boundaries'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Handle detected IQR outliers:
    - 'remove_rows': Drop rows with outlier values in the selected column
    - 'cap_boundaries': Clip outlier values to [Lower Bound, Upper Bound]
    """
    if df is None or df.empty or column not in df.columns:
        return df, {"affected": 0, "rows_before": len(df) if df is not None else 0, "rows_after": len(df) if df is not None else 0}

    prof = get_outliers_profile(df, column)
    outlier_cnt = prof["outlier_count"]
    rows_before = len(df)

    if outlier_cnt == 0:
        return df, {"affected": 0, "rows_before": rows_before, "rows_after": rows_before}

    new_df = df.copy(deep=True)
    lower = prof["lower_bound"]
    upper = prof["upper_bound"]

    if action == "remove_rows":
        mask = (new_df[column] >= lower) & (new_df[column] <= upper)
        # Keep NaNs if any so missing value handler can deal with them separately
        mask = mask | new_df[column].isna()
        new_df = new_df[mask].reset_index(drop=True)

    elif action == "cap_boundaries":
        new_df[column] = new_df[column].clip(lower=lower, upper=upper)

    rows_after = len(new_df)

    return new_df, {
        "affected": outlier_cnt,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "lower_bound": lower,
        "upper_bound": upper
    }


# =============================================================================
# TEXT CLEANING
# =============================================================================

def clean_text_column(
    df: pd.DataFrame,
    column: str,
    operations: List[str],
    find_str: Optional[str] = None,
    replace_str: Optional[str] = None
) -> Tuple[pd.DataFrame, int]:
    """
    Clean string/text column with operations:
    - 'trim': Strip leading and trailing whitespace
    - 'lower': Convert to lowercase
    - 'upper': Convert to uppercase
    - 'title': Convert to title case
    - 'find_replace': Replace find_str with replace_str
    - 'remove_empty': Convert empty/whitespace strings to NaN
    """
    if df is None or df.empty or column not in df.columns:
        return df, 0

    new_df = df.copy(deep=True)
    series = new_df[column].astype(str)
    affected = len(df)

    for op in operations:
        if op == "trim":
            series = series.str.strip()
        elif op == "lower":
            series = series.str.lower()
        elif op == "upper":
            series = series.str.upper()
        elif op == "title":
            series = series.str.title()
        elif op == "find_replace" and find_str is not None:
            series = series.str.replace(find_str, replace_str or "", regex=False)
        elif op == "remove_empty":
            series = series.replace(r"^\s*$", np.nan, regex=True)

    new_df[column] = series
    return new_df, affected


# =============================================================================
# DATE & DATETIME PREPARATION
# =============================================================================

def extract_date_components(
    df: pd.DataFrame,
    date_column: str,
    components: List[str],  # ['year', 'month', 'day', 'day_of_week', 'quarter']
    prefix: Optional[str] = None
) -> Tuple[pd.DataFrame, List[str]]:
    """Extract temporal components into new derived columns safely."""
    if df is None or df.empty or date_column not in df.columns:
        return df, []

    new_df = df.copy(deep=True)
    dt_series = pd.to_datetime(new_df[date_column], errors="coerce")
    created_cols = []
    pfx = prefix or date_column

    for comp in components:
        if comp == "year":
            col_name = f"{pfx}_Year"
            new_df[col_name] = dt_series.dt.year.astype("Int64")
            created_cols.append(col_name)
        elif comp == "month":
            col_name = f"{pfx}_Month"
            new_df[col_name] = dt_series.dt.month.astype("Int64")
            created_cols.append(col_name)
        elif comp == "day":
            col_name = f"{pfx}_Day"
            new_df[col_name] = dt_series.dt.day.astype("Int64")
            created_cols.append(col_name)
        elif comp == "day_of_week":
            col_name = f"{pfx}_DayOfWeek"
            new_df[col_name] = dt_series.dt.day_name()
            created_cols.append(col_name)
        elif comp == "quarter":
            col_name = f"{pfx}_Quarter"
            new_df[col_name] = dt_series.dt.quarter.astype("Int64")
            created_cols.append(col_name)

    return new_df, created_cols


# =============================================================================
# CONTROLLED COLUMN DERIVATION (No eval/exec)
# =============================================================================

def derive_column_arithmetic(
    df: pd.DataFrame,
    new_col_name: str,
    col_a: str,
    operation: str,  # 'add', 'subtract', 'multiply', 'divide', 'percentage'
    col_b: Optional[str] = None,
    constant_val: Optional[float] = None
) -> Tuple[pd.DataFrame, bool, str]:
    """
    Derive new column using safe mathematical arithmetic between columns or column and constant.
    Strictly NO eval() or exec()!
    """
    if df is None or df.empty:
        return df, False, "Dataset is empty."

    clean_name = str(new_col_name).strip()
    if not clean_name:
        return df, False, "Derived column name cannot be empty."

    if clean_name in df.columns:
        return df, False, f"A column named '{clean_name}' already exists."

    if col_a not in df.columns:
        return df, False, f"Primary column '{col_a}' not found."

    new_df = df.copy(deep=True)
    s_a = pd.to_numeric(new_df[col_a], errors="coerce")

    # Determine second operand
    if col_b and col_b != "(None)" and col_b in df.columns:
        s_b = pd.to_numeric(new_df[col_b], errors="coerce")
    elif constant_val is not None:
        s_b = float(constant_val)
    else:
        return df, False, "Second operand (column or constant value) is required."

    try:
        if operation == "add":
            res = s_a + s_b
        elif operation == "subtract":
            res = s_a - s_b
        elif operation == "multiply":
            res = s_a * s_b
        elif operation == "divide":
            # Handle division by zero safely
            if isinstance(s_b, (int, float)):
                res = s_a / s_b if s_b != 0 else np.nan
            else:
                res = s_a / s_b.replace(0, np.nan)
        elif operation == "percentage":
            if isinstance(s_b, (int, float)):
                res = (s_a / s_b * 100) if s_b != 0 else np.nan
            else:
                res = (s_a / s_b.replace(0, np.nan) * 100)
        else:
            return df, False, f"Unsupported operation: {operation}"

        new_df[clean_name] = res
        return new_df, True, f"Successfully created derived column '{clean_name}'"

    except Exception as e:
        return df, False, f"Derivation calculation failed: {str(e)}"


# =============================================================================
# EXPORT UTILITIES (CSV & Excel)
# =============================================================================

def export_prepared_csv(df: pd.DataFrame) -> bytes:
    """Export DataFrame as UTF-8 CSV bytes."""
    if df is None:
        return b""
    return df.to_csv(index=False, encoding="utf-8").encode("utf-8")


def export_prepared_excel(df: pd.DataFrame, sheet_name: str = "Cleaned_Data") -> bytes:
    """Export DataFrame as Excel .xlsx bytes."""
    if df is None or df.empty:
        return b""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return output.getvalue()

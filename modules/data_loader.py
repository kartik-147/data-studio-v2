"""
DATA STUDIO v2 — Dataset Loader, Parsing, Schema Detection & Metadata Engine
=============================================================================
Modular, reusable data-processing layer decoupled from UI presentation.
"""
from typing import Optional, Dict, Any, List, Tuple
import os
import io
import re
import pandas as pd
import numpy as np
import streamlit as st


# =============================================================================
# FILE PARSING & VALIDATION
# =============================================================================

def validate_dataset(df: Optional[pd.DataFrame]) -> Tuple[bool, Optional[str]]:
    """Validate that DataFrame exists and contains usable rows and columns."""
    if df is None:
        return False, "The file could not be parsed into a dataset."
    if not isinstance(df, pd.DataFrame):
        return False, "Invalid data structure encountered."
    if df.empty:
        return False, "The uploaded file is empty (contains no data rows)."
    if len(df.columns) == 0:
        return False, "The dataset contains no columns."
    if len(df) == 0:
        return False, "The dataset contains header columns but zero data records."
    return True, None


def load_csv(file_obj, filename: str = "dataset.csv") -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Parse a CSV file with automatic multi-encoding fallback and delimiter inference.
    Safe against corrupted streams and unsupported encodings.
    """
    # Read raw bytes if file_obj is an UploadedFile or file-like object
    if hasattr(file_obj, "read"):
        try:
            content_bytes = file_obj.read()
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
        except Exception as e:
            return None, f"Failed to read file buffer: {str(e)}"
    elif isinstance(file_obj, bytes):
        content_bytes = file_obj
    elif isinstance(file_obj, str) and os.path.exists(file_obj):
        try:
            with open(file_obj, "rb") as f:
                content_bytes = f.read()
        except Exception as e:
            return None, f"Failed to open local file: {str(e)}"
    else:
        return None, "Invalid file input provided."

    if len(content_bytes) == 0:
        return None, "The uploaded CSV file is empty (0 bytes)."

    # List of common encodings to attempt in priority order
    encodings_to_try = ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"]
    
    last_error = None
    for enc in encodings_to_try:
        try:
            # Try standard comma separator
            df = pd.read_csv(io.BytesIO(content_bytes), encoding=enc)
            # If 1 column and contains commas/semicolons, check if sep was semicolon/tab
            if len(df.columns) == 1 and len(df) > 0:
                first_col_name = str(df.columns[0])
                if ";" in first_col_name:
                    df = pd.read_csv(io.BytesIO(content_bytes), encoding=enc, sep=";")
                elif "\t" in first_col_name:
                    df = pd.read_csv(io.BytesIO(content_bytes), encoding=enc, sep="\t")

            # Clean column names (strip leading/trailing whitespace and ensure string type)
            df.columns = [str(c).strip() for c in df.columns]
            
            is_valid, validation_err = validate_dataset(df)
            if not is_valid:
                return None, validation_err
                
            return df, None
        except UnicodeDecodeError:
            continue
        except pd.errors.EmptyDataError:
            return None, "The CSV file does not contain any data."
        except pd.errors.ParserError as pe:
            last_error = f"CSV parsing error: {str(pe).splitlines()[0]}"
            continue
        except Exception as e:
            last_error = f"Unable to parse CSV file: {str(e)}"
            continue

    return None, last_error or "Unable to decode CSV file. The file encoding or structure is not supported."


def get_excel_sheet_names(file_obj) -> Tuple[List[str], Optional[str]]:
    """Inspect Excel file and extract all available sheet names."""
    try:
        if hasattr(file_obj, "read"):
            content_bytes = file_obj.read()
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            excel_file = pd.ExcelFile(io.BytesIO(content_bytes))
        elif isinstance(file_obj, str) and os.path.exists(file_obj):
            excel_file = pd.ExcelFile(file_obj)
        else:
            return [], "Invalid Excel input."

        sheet_names = excel_file.sheet_names
        if not sheet_names:
            return [], "The Excel workbook contains no visible worksheets."
        return sheet_names, None
    except Exception as e:
        return [], f"Unable to read Excel workbook sheets: {str(e)}"


def load_excel(
    file_obj,
    filename: str = "dataset.xlsx",
    sheet_name: Optional[str] = None
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Parse an Excel file (.xlsx, .xls) safely with specific sheet targeting."""
    try:
        if hasattr(file_obj, "read"):
            content_bytes = file_obj.read()
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            bio = io.BytesIO(content_bytes)
            if len(content_bytes) == 0:
                return None, "The uploaded Excel file is empty (0 bytes)."
        elif isinstance(file_obj, str) and os.path.exists(file_obj):
            bio = file_obj
        else:
            return None, "Invalid Excel file input."

        # Select sheet
        target_sheet = sheet_name if sheet_name else 0
        
        # Engine selection
        engine = "openpyxl" if filename.lower().endswith(".xlsx") else None
        
        try:
            df = pd.read_excel(bio, sheet_name=target_sheet, engine=engine)
        except Exception:
            # Fallback without explicit engine
            if hasattr(bio, "seek"):
                bio.seek(0)
            df = pd.read_excel(bio, sheet_name=target_sheet)

        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]
        
        is_valid, validation_err = validate_dataset(df)
        if not is_valid:
            return None, validation_err
            
        return df, None
    except Exception as e:
        return None, f"Unable to parse Excel file: {str(e)}"


def load_dataset_file(
    file_obj,
    filename: str,
    sheet_name: Optional[str] = None
) -> Tuple[Optional[pd.DataFrame], Optional[str], str]:
    """Unified entry point for loading either CSV or Excel data sources."""
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == ".csv":
        df, err = load_csv(file_obj, filename)
        return df, err, "CSV"
    elif ext in [".xlsx", ".xls"]:
        df, err = load_excel(file_obj, filename, sheet_name=sheet_name)
        return df, err, "Excel"
    else:
        return None, "Unsupported file format. Supported formats: CSV, XLSX, XLS.", "Unknown"


# =============================================================================
# COLUMN CLASSIFICATION & TYPE INFERENCE
# =============================================================================

# Known ID or non-aggregatable column naming patterns
ID_REGEX_PATTERN = re.compile(
    r"(?:^|_)(?:id|key|code|sku|uuid|guid|ssn|ein|zip|zipcode|postal|postal_code|phone|isbn|account_no|order_id|customer_id|cust_id|user_id|employee_id|item_id|product_id|trans_id|transaction_id)$",
    re.IGNORECASE
)

DATE_REGEX_PATTERN = re.compile(
    r"(?:^|_)(?:date|time|timestamp|datetime|year|month|day|dob|created_at|updated_at|period|quarter)$",
    re.IGNORECASE
)


def detect_column_type(series: pd.Series, col_name: str, total_rows: int) -> str:
    """
    Intelligently classify a column into one of 5 semantic data categories:
    - Numeric
    - Categorical
    - Date/Time
    - Text
    - Boolean
    """
    # 1. Check for Boolean dtype or boolean-like values
    if pd.api.types.is_bool_dtype(series):
        return "Boolean"

    # Drop NA for value-level analysis
    valid_series = series.dropna()
    valid_count = len(valid_series)
    
    if valid_count == 0:
        return "Text"

    unique_vals = valid_series.unique()
    unique_count = len(unique_vals)
    unique_ratio = unique_count / total_rows if total_rows > 0 else 0

    # 2. Check for Boolean-like column representations
    if unique_count <= 2:
        str_vals = {str(v).strip().lower() for v in unique_vals}
        bool_sets = [
            {"true", "false"},
            {"1", "0"},
            {"1.0", "0.0"},
            {"yes", "no"},
            {"y", "n"},
            {"t", "f"},
            {"active", "inactive"},
            {"enable", "disable"},
            {"enabled", "disabled"}
        ]
        if any(str_vals.issubset(s) for s in bool_sets):
            return "Boolean"

    # 3. Check for Datetime dtype or parsable dates
    if pd.api.types.is_datetime64_any_dtype(series):
        return "Date/Time"

    # Check if object/string column is date-like
    if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
        sample_subset = valid_series.head(40)
        # Fast regex name check
        is_date_named = bool(DATE_REGEX_PATTERN.search(col_name))
        
        # Test if sample can be parsed as dates
        try:
            # Check if values look like date strings (e.g. contain -, /, :, or standard formats)
            sample_str = sample_subset.astype(str)
            has_date_delimiters = sample_str.str.contains(r"[\/\-\:\sT]", regex=True).mean() > 0.7
            if has_date_delimiters or is_date_named:
                try:
                    parsed_dates = pd.to_datetime(sample_subset, errors="coerce", format="mixed")
                except TypeError:
                    parsed_dates = pd.to_datetime(sample_subset, errors="coerce")
                valid_date_ratio = parsed_dates.notna().mean()
                if valid_date_ratio >= 0.85:
                    return "Date/Time"
        except Exception:
            pass

    # 4. Check for Identifiers (ID, SKU, Codes) before numeric/categorical categorization
    is_id_name = bool(ID_REGEX_PATTERN.search(col_name))
    if is_id_name:
        # If highly unique identifier
        if unique_ratio >= 0.7 or unique_count > 50:
            return "Text"
        else:
            return "Categorical"

    # 5. Check for Numeric dtypes
    if pd.api.types.is_numeric_dtype(series):
        # If integer with 100% unique values and named like an ID/Index
        if unique_count == total_rows and total_rows > 30 and (is_id_name or "index" in col_name.lower()):
            return "Text"
        return "Numeric"

    # 6. Categorical vs Free-Text for object / string columns
    # Low cardinality relative to dataset size -> Categorical
    if (unique_count <= 25 and (unique_ratio <= 0.7 or total_rows <= 10)) or (unique_ratio <= 0.20 and unique_count < 100):
        return "Categorical"

    return "Text"


# =============================================================================
# DATASET METADATA COMPUTATION
# =============================================================================

def format_memory_size(bytes_val: int) -> str:
    """Format memory bytes into human-readable unit string."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"


def create_dataset_metadata(
    df: pd.DataFrame,
    filename: str,
    file_type: str = "CSV"
) -> Dict[str, Any]:
    """
    Calculate and build the comprehensive metadata schema for the active dataset.
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    total_cells = total_rows * total_cols
    
    # Memory footprint
    memory_bytes = int(df.memory_usage(deep=True).sum())
    memory_formatted = format_memory_size(memory_bytes)
    
    # Missing value statistics
    missing_series = df.isna().sum()
    total_missing_cells = int(missing_series.sum())
    overall_missing_pct = float((total_missing_cells / total_cells * 100)) if total_cells > 0 else 0.0
    cols_with_missing_count = int((missing_series > 0).sum())
    
    # Duplicate row statistics
    duplicate_rows_count = int(df.duplicated().sum())
    duplicate_pct = float((duplicate_rows_count / total_rows * 100)) if total_rows > 0 else 0.0

    # Column-level type detection & profiling
    column_types: Dict[str, str] = {}
    column_details: List[Dict[str, Any]] = []
    columns_by_type: Dict[str, List[str]] = {
        "Numeric": [],
        "Categorical": [],
        "Date/Time": [],
        "Text": [],
        "Boolean": []
    }

    for col in df.columns:
        series = df[col]
        detected_type = detect_column_type(series, str(col), total_rows)
        column_types[col] = detected_type
        
        if detected_type in columns_by_type:
            columns_by_type[detected_type].append(col)
        else:
            columns_by_type["Text"].append(col)

        col_missing = int(series.isna().sum())
        col_missing_pct = float((col_missing / total_rows * 100)) if total_rows > 0 else 0.0
        col_non_null = total_rows - col_missing
        col_unique = int(series.nunique(dropna=True))
        
        # Sample non-null values
        samples = [str(v) for v in series.dropna().head(3).tolist()]
        sample_str = ", ".join(samples) if samples else "—"

        column_details.append({
            "column_name": str(col),
            "detected_type": detected_type,
            "pandas_dtype": str(series.dtype),
            "non_null_count": col_non_null,
            "missing_count": col_missing,
            "missing_percentage": col_missing_pct,
            "unique_count": col_unique,
            "sample_preview": sample_str
        })

    column_types_count = {
        k: len(v) for k, v in columns_by_type.items()
    }

    return {
        "name": filename,
        "filename": filename,
        "dataset_name": filename,
        "file_type": file_type,
        "total_rows": total_rows,
        "total_columns": total_cols,
        "total_cells": total_cells,
        "memory_bytes": memory_bytes,
        "memory_formatted": memory_formatted,
        "missing_cells": total_missing_cells,
        "missing_percentage": overall_missing_pct,
        "columns_with_missing": cols_with_missing_count,
        "duplicate_rows": duplicate_rows_count,
        "duplicate_percentage": duplicate_pct,
        "column_types": column_types,
        "column_types_count": column_types_count,
        "columns_by_type": columns_by_type,
        "column_details": column_details
    }


# =============================================================================
# SAMPLE DATASET CATALOG
# =============================================================================

def get_available_sample_datasets() -> Dict[str, Dict[str, Any]]:
    """Return verified sample datasets available in the workspace."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    sample_dir = os.path.join(base_dir, "sample_data")
    
    catalog = {
        "customer_demographics": {
            "key": "customer_demographics",
            "name": "Customer Demographics (Stitch Preview)",
            "filename": "customer_demographics.csv",
            "description": "Customer profiles, demographics, household income, and regional locations.",
            "file_type": "CSV",
            "path": os.path.join(sample_dir, "customer_demographics.csv")
        },
        "saas_sales": {
            "key": "saas_sales",
            "name": "SaaS Sales & Revenue",
            "filename": "saas_sales_data.csv",
            "description": "B2B subscription data: customer tiers, MRR, churn status, and contract terms.",
            "file_type": "CSV",
            "path": os.path.join(sample_dir, "saas_sales_data.csv")
        },
        "ecommerce": {
            "key": "ecommerce",
            "name": "E-Commerce Global Orders",
            "filename": "ecommerce_orders.csv",
            "description": "Global multi-category retail transactions, order profits, shipping modes, and sales.",
            "file_type": "CSV",
            "path": os.path.join(sample_dir, "ecommerce_orders.csv")
        }
    }
    
    # Filter to only existing files on disk
    return {k: v for k, v in catalog.items() if os.path.exists(v["path"])}


def load_sample_dataset_by_key(dataset_key: str) -> Tuple[Optional[pd.DataFrame], Optional[str], str]:
    """Load a cataloged sample dataset by key."""
    catalog = get_available_sample_datasets()
    if dataset_key not in catalog:
        return None, f"Sample dataset '{dataset_key}' not found.", "Unknown"
        
    info = catalog[dataset_key]
    df, err = load_csv(info["path"], info["filename"])
    return df, err, info["file_type"]


# =============================================================================
# SESSION STATE MANAGEMENT
# =============================================================================

def set_active_dataset(df: pd.DataFrame, name: str, file_type: str = "CSV") -> None:
    """
    Store the active dataset, pristine original copy, and calculated metadata
    in the central Streamlit session state architecture.
    """
    from modules.config import reset_workflow_progress, log_activity
    metadata = create_dataset_metadata(df, name, file_type)
    st.session_state["dataset"] = df
    st.session_state["original_dataset"] = df.copy(deep=True)
    st.session_state["cleaned_dataset"] = None
    st.session_state["dataset_name"] = name
    st.session_state["dataset_metadata"] = metadata
    st.session_state["dataset_file_type"] = file_type
    reset_workflow_progress()
    log_activity(f"Loaded dataset '{name}' ({len(df):,} rows × {len(df.columns)} cols)", "database")


def clear_dataset_state() -> None:
    """
    Reset all dataset-dependent session state while preserving appearance,
    routing, and application preferences.
    """
    from modules.config import reset_workflow_progress, log_activity
    prev_name = st.session_state.get("dataset_name", "dataset")
    st.session_state["dataset"] = None
    st.session_state["original_dataset"] = None
    st.session_state["cleaned_dataset"] = None
    st.session_state["dataset_name"] = None
    st.session_state["dataset_metadata"] = None
    st.session_state["dataset_file_type"] = None
    reset_workflow_progress()
    log_activity(f"Cleared active dataset '{prev_name}'", "x")


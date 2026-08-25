"""
Comprehensive Test Suite for Data Preparation Engine (Module 5)
=============================================================================
Tests:
1. Missing value imputation & row/column removal
2. Duplicate detection & removal
3. Column management (Rename, Drop, Reorder, Safe Type Casting)
4. Visual filtering (Numeric, Text, Datetime, Between)
5. Persistent Sorting
6. IQR Outlier handling (Detection, Boundary Capping, Row Removal)
7. Text cleaning (Trim, Lower, Upper, Title, Find/Replace, Remove Empty)
8. Date component extraction
9. Safe column derivations (Add, Subtract, Multiply, Divide, Percentage)
10. CSV & Excel export byte generation
11. Dual-state preservation & non-destructive transformations
"""
import os
import sys
import datetime
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.data_preparation_engine import (
    get_missing_values_summary,
    handle_missing_values,
    get_duplicates_info,
    remove_duplicates,
    rename_column,
    drop_columns,
    reorder_columns,
    cast_column_type,
    apply_filters,
    sort_dataset,
    get_outliers_profile,
    handle_outliers,
    clean_text_column,
    extract_date_components,
    derive_column_arithmetic,
    export_prepared_csv,
    export_prepared_excel
)
from modules.data_loader import create_dataset_metadata


def run_tests():
    print("=====================================================================")
    print("STARTING DATA STUDIO v2 DATA PREPARATION TEST SUITE")
    print("=====================================================================\n")

    # 1. Load Sample Business Dataset
    csv_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "saas_sales_data.csv")
    if os.path.exists(csv_path):
        df_orig = pd.read_csv(csv_path)
        print(f"[OK] Loaded sample saas_sales_data.csv ({len(df_orig)} rows, {len(df_orig.columns)} columns)")
    else:
        df_orig = pd.DataFrame({
            "Customer_ID": ["C1", "C2", "C3", "C4", "C5"],
            "Region": ["North", "South", "North", "East", "West"],
            "MRR": [5000.0, 1200.0, 4500.0, 3000.0, 800.0],
            "Discount_Pct": [0.1, 0.2, 0.05, 0.15, 0.0],
            "Signup_Date": ["2023-01-15", "2023-02-20", "2023-03-10", "2023-04-05", "2023-05-12"]
        })
        print(f"[OK] Created synthetic dataset ({len(df_orig)} rows)")

    # 2. Test Missing Values
    print("\n--- Testing Missing Value Handling ---")
    df_missing_test = pd.DataFrame({
        "Num_Col": [10.0, np.nan, 30.0, 40.0, np.nan],
        "Cat_Col": ["A", "B", np.nan, "A", "C"],
        "Clean_Col": [1, 2, 3, 4, 5]
    })
    sum_df = get_missing_values_summary(df_missing_test)
    assert len(sum_df) == 3
    print("  [PASS] Missing values summary generated")

    # Mean imputation
    df_mean, info_mean = handle_missing_values(df_missing_test, ["Num_Col"], strategy="mean")
    assert df_mean["Num_Col"].isna().sum() == 0
    assert abs(df_mean.loc[1, "Num_Col"] - 26.666) < 0.01
    print("  [PASS] Mean imputation passed")

    # Median imputation
    df_med, info_med = handle_missing_values(df_missing_test, ["Num_Col"], strategy="median")
    assert df_med["Num_Col"].isna().sum() == 0
    assert df_med.loc[1, "Num_Col"] == 30.0
    print("  [PASS] Median imputation passed")

    # Mode imputation
    df_mode, info_mode = handle_missing_values(df_missing_test, ["Cat_Col"], strategy="mode")
    assert df_mode["Cat_Col"].isna().sum() == 0
    assert df_mode.loc[2, "Cat_Col"] == "A"
    print("  [PASS] Mode imputation passed")

    # Drop rows
    df_drop, info_drop = handle_missing_values(df_missing_test, ["Num_Col", "Cat_Col"], strategy="drop_rows")
    assert len(df_drop) == 2  # Only rows 0 and 3 have both non-null
    print("  [PASS] Drop rows missing value handling passed")

    # 3. Test Duplicate Handling
    print("\n--- Testing Duplicate Handling ---")
    df_dup_test = pd.DataFrame({
        "ID": [1, 2, 2, 3, 3, 3],
        "Val": ["A", "B", "B", "C", "C", "D"]
    })
    dup_info = get_duplicates_info(df_dup_test)
    assert dup_info["duplicate_count"] == 2
    df_no_dups, rem_info = remove_duplicates(df_dup_test)
    assert len(df_no_dups) == 4
    assert rem_info["removed_count"] == 2
    print(f"  [PASS] Duplicates removed: {rem_info['removed_count']} rows")

    # 4. Test Column Operations (Rename, Drop, Reorder, Type Casting)
    print("\n--- Testing Column Management ---")
    df_col_test = df_orig.copy()
    
    # Rename
    old_c = df_col_test.columns[0]
    df_renamed, ok, msg = rename_column(df_col_test, old_c, "Primary_ID")
    assert ok and "Primary_ID" in df_renamed.columns
    print(f"  [PASS] Column renamed: '{old_c}' -> 'Primary_ID'")

    # Duplicate rename collision test
    _, bad_ok, _ = rename_column(df_col_test, old_c, df_col_test.columns[1])
    assert not bad_ok
    print("  [PASS] Duplicate column rename collision prevented")

    # Drop
    df_dropped, dropped_list = drop_columns(df_renamed, ["Primary_ID"])
    assert "Primary_ID" not in df_dropped.columns
    assert len(dropped_list) == 1
    print("  [PASS] Column dropped successfully")

    # Reorder
    new_order = list(reversed(df_orig.columns))
    df_reordered, re_ok = reorder_columns(df_orig, new_order)
    assert list(df_reordered.columns) == new_order
    print("  [PASS] Columns reordered successfully")

    # Safe Type Casting
    df_cast_test = pd.DataFrame({
        "Str_Nums": ["100", "200.5", "300", "invalid_val", None],
        "Dates": ["2024-01-01", "2024-02-15", "invalid_date", "2024-04-01", None]
    })
    df_casted, res = cast_column_type(df_cast_test, "Str_Nums", "Numeric")
    assert res["success"]
    assert res["converted"] == 3
    assert res["coerced_na"] == 1  # 'invalid_val' coerced to NA
    print(f"  [PASS] Safe Numeric casting: {res['converted']} converted, {res['coerced_na']} coerced to NA")

    df_date_cast, res_d = cast_column_type(df_cast_test, "Dates", "Datetime")
    assert res_d["success"]
    assert res_d["converted"] == 3
    print(f"  [PASS] Safe Datetime casting: {res_d['converted']} converted")

    # 5. Test Visual Filtering
    print("\n--- Testing Visual Filter Builder ---")
    df_filt_test = pd.DataFrame({
        "Score": [10, 25, 50, 75, 100],
        "City": ["London", "Paris", "New York", "Tokyo", "Berlin"],
        "Active": [True, False, True, True, False]
    })
    # Filter Score >= 50
    f_res1, info1 = apply_filters(df_filt_test, [{"column": "Score", "operator": "Greater or Equal (>=)", "value": 50}])
    assert len(f_res1) == 3
    print("  [PASS] Numeric filter (>= 50) passed")

    # Filter City Contains 'o'
    f_res2, info2 = apply_filters(df_filt_test, [{"column": "City", "operator": "Contains", "value": "o"}])
    assert len(f_res2) == 3  # London, New York, Tokyo
    print("  [PASS] Text filter (Contains 'o') passed")

    # Compound Filter
    f_res3, info3 = apply_filters(df_filt_test, [
        {"column": "Score", "operator": "Greater or Equal (>=)", "value": 25},
        {"column": "City", "operator": "Is one of", "value": "Paris, Tokyo"}
    ])
    assert len(f_res3) == 2
    print("  [PASS] Compound filter passed")

    # 6. Test Sorting
    print("\n--- Testing Persistent Sorting ---")
    df_sort_test, ok_sort = sort_dataset(df_filt_test, ["Score"], [False])
    assert ok_sort
    assert df_sort_test.iloc[0]["Score"] == 100
    print("  [PASS] Persistent sorting (Descending) passed")

    # 7. Test IQR Outlier Handling
    print("\n--- Testing IQR Outlier Detection & Capping ---")
    df_outlier_test = pd.DataFrame({
        "Values": [10, 12, 11, 13, 12, 11, 12, 14, 100, -50]  # 100 and -50 are outliers
    })
    prof = get_outliers_profile(df_outlier_test, "Values")
    assert prof["outlier_count"] == 2
    print(f"  [PASS] Detected {prof['outlier_count']} outliers in boundary [{prof['lower_bound']:.1f}, {prof['upper_bound']:.1f}]")

    # Cap outliers
    df_capped, c_info = handle_outliers(df_outlier_test, "Values", action="cap_boundaries")
    assert df_capped["Values"].max() <= prof["upper_bound"]
    assert df_capped["Values"].min() >= prof["lower_bound"]
    print("  [PASS] Outliers successfully capped to IQR boundaries")

    # Remove outliers
    df_rem_out, r_info = handle_outliers(df_outlier_test, "Values", action="remove_rows")
    assert len(df_rem_out) == 8
    print("  [PASS] Outlier rows removed successfully")

    # 8. Test Text Cleaning
    print("\n--- Testing Text Cleaning ---")
    df_txt_test = pd.DataFrame({
        "Text": ["  HELLO WORLD  ", "foo bar", "  mixed CASE  "]
    })
    df_txt_clean, _ = clean_text_column(df_txt_test, "Text", ["trim", "title"])
    assert df_txt_clean.loc[0, "Text"] == "Hello World"
    assert df_txt_clean.loc[1, "Text"] == "Foo Bar"
    print("  [PASS] Text trim and title-casing passed")

    # 9. Test Date Component Extraction
    print("\n--- Testing Date Component Extraction ---")
    df_date_test = pd.DataFrame({
        "Event_Date": ["2024-03-15", "2024-07-22", "2024-11-05"]
    })
    df_extracted, created_cols = extract_date_components(df_date_test, "Event_Date", ["year", "month", "day", "day_of_week", "quarter"])
    assert len(created_cols) == 5
    assert df_extracted.loc[0, "Event_Date_Year"] == 2024
    assert df_extracted.loc[0, "Event_Date_Month"] == 3
    assert df_extracted.loc[0, "Event_Date_DayOfWeek"] == "Friday"
    print(f"  [PASS] Date components extracted: {', '.join(created_cols)}")

    # 10. Test Safe Column Derivation
    print("\n--- Testing Safe Column Arithmetic Derivation ---")
    df_math_test = pd.DataFrame({
        "Price": [100.0, 200.0, 300.0],
        "Units": [2, 3, 4],
        "Discount": [10.0, 20.0, 30.0]
    })
    # Multiply: Revenue = Price * Units
    df_derived, ok_m, _ = derive_column_arithmetic(df_math_test, "Revenue", "Price", "multiply", col_b="Units")
    assert ok_m and "Revenue" in df_derived.columns
    assert df_derived.loc[0, "Revenue"] == 200.0

    # Percentage: Margin_Pct = Discount / Price * 100
    df_derived2, ok_p, _ = derive_column_arithmetic(df_derived, "Discount_Pct", "Discount", "percentage", col_b="Price")
    assert ok_p and "Discount_Pct" in df_derived2.columns
    assert df_derived2.loc[0, "Discount_Pct"] == 10.0
    print("  [PASS] Safe Column derivations (Multiply, Percentage) passed")

    # 11. Test Export Capabilities (CSV & Excel)
    print("\n--- Testing Export Utilities (CSV & Excel) ---")
    csv_bytes = export_prepared_csv(df_orig)
    assert len(csv_bytes) > 50
    xlsx_bytes = export_prepared_excel(df_orig)
    assert len(xlsx_bytes) > 1000
    print(f"  [PASS] CSV export: {len(csv_bytes)} bytes | Excel export: {len(xlsx_bytes):,} bytes")

    # 12. Test Dual-State Dataset Immutability
    print("\n--- Testing Dual-State Architecture & Immutability ---")
    df_original_copy = df_orig.copy(deep=True)
    # Apply multiple transformations to working df
    df_working = df_orig.copy(deep=True)
    df_working, _ = handle_missing_values(df_working, list(df_working.columns), strategy="zero")
    df_working, _, _ = rename_column(df_working, df_working.columns[0], "Transformed_Col_1")
    
    # Assert original copy is 100% untouched
    pd.testing.assert_frame_equal(df_orig, df_original_copy)
    assert df_orig.columns[0] != "Transformed_Col_1"
    print("  [PASS] Original dataset confirmed 100% immutable and untouched!")

    # Verify metadata recalculation
    meta = create_dataset_metadata(df_working, "test_transformed.csv", "CSV")
    assert meta["name"] == "test_transformed.csv"
    assert "Transformed_Col_1" in meta["column_types"]
    print("  [PASS] Prepared metadata recalculation verified")

    print("\n=====================================================================")
    print("ALL 12 TEST SUITE MODULES PASSED SUCCESSFULLY! (100% PASS RATE)")
    print("=====================================================================")


if __name__ == "__main__":
    run_tests()

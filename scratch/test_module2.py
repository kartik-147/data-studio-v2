"""
Automated unit and integration test suite for Module 2 (Data Loader & Dataset Workspace)
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

from modules.data_loader import (
    load_csv,
    load_excel,
    get_excel_sheet_names,
    load_dataset_file,
    detect_column_type,
    create_dataset_metadata,
    get_available_sample_datasets,
    load_sample_dataset_by_key,
    validate_dataset
)

def run_tests():
    print("=== STARTING MODULE 2 TEST SUITE ===")
    
    # 1. Test CSV sample datasets loading
    print("\n--- Test 1: Sample CSV Loading ---")
    saas_df, err, ftype = load_sample_dataset_by_key("saas_sales")
    assert err is None, f"Failed to load saas_sales: {err}"
    assert saas_df is not None and len(saas_df) > 0, "saas_df is empty"
    print(f"Loaded saas_sales: {len(saas_df)} rows, {len(saas_df.columns)} cols, type: {ftype}")
    
    ecom_df, err, ftype = load_sample_dataset_by_key("ecommerce")
    assert err is None, f"Failed to load ecommerce: {err}"
    assert ecom_df is not None and len(ecom_df) > 0, "ecom_df is empty"
    print(f"Loaded ecommerce: {len(ecom_df)} rows, {len(ecom_df.columns)} cols, type: {ftype}")

    # 2. Test metadata creation and column types on saas_sales
    print("\n--- Test 2: Metadata & Column Classification on SaaS Sales ---")
    saas_meta = create_dataset_metadata(saas_df, "saas_sales_data.csv", "CSV")
    print(f"Total rows: {saas_meta['total_rows']}")
    print(f"Total cols: {saas_meta['total_columns']}")
    print(f"Memory formatted: {saas_meta['memory_formatted']}")
    print(f"Detected column types: {saas_meta['column_types']}")
    print(f"Type counts: {saas_meta['column_types_count']}")
    
    assert saas_meta["column_types"]["Customer_ID"] in ["Text", "Categorical"], "Customer_ID should not be numeric"
    assert saas_meta["column_types"]["Signup_Date"] == "Date/Time", "Signup_Date should be Date/Time"
    assert saas_meta["column_types"]["MRR"] == "Numeric", "MRR should be Numeric"
    assert saas_meta["column_types"]["Region"] == "Categorical", "Region should be Categorical"
    print("Column classifications verified for SaaS Sales!")

    # 3. Test metadata creation and column types on E-Commerce
    print("\n--- Test 3: Metadata & Column Classification on E-Commerce ---")
    ecom_meta = create_dataset_metadata(ecom_df, "ecommerce_orders.csv", "CSV")
    assert ecom_meta["column_types"]["Order_ID"] in ["Text", "Categorical"], "Order_ID should not be numeric"
    assert ecom_meta["column_types"]["Order_Date"] == "Date/Time", "Order_Date should be Date/Time"
    assert ecom_meta["column_types"]["Sales"] == "Numeric", "Sales should be Numeric"
    assert ecom_meta["column_types"]["Profit"] == "Numeric", "Profit should be Numeric"
    print(f"E-Commerce types: {ecom_meta['column_types']}")
    print("Column classifications verified for E-Commerce!")

    # 4. Test Excel reading and multi-sheet support
    print("\n--- Test 4: Excel Multi-Sheet Support ---")
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        saas_df.to_excel(writer, sheet_name="SaaS Metrics", index=False)
        ecom_df.to_excel(writer, sheet_name="Orders 2025", index=False)
    excel_buffer.seek(0)
    
    sheets, s_err = get_excel_sheet_names(excel_buffer)
    assert s_err is None, f"Failed to get sheets: {s_err}"
    assert sheets == ["SaaS Metrics", "Orders 2025"], f"Unexpected sheets: {sheets}"
    print(f"Excel sheets detected: {sheets}")

    # Load sheet 1
    excel_buffer.seek(0)
    df_sheet1, err1, _ = load_dataset_file(excel_buffer, "test.xlsx", sheet_name="SaaS Metrics")
    assert err1 is None and len(df_sheet1) == len(saas_df), "Failed sheet 1 loading"
    
    # Load sheet 2
    excel_buffer.seek(0)
    df_sheet2, err2, _ = load_dataset_file(excel_buffer, "test.xlsx", sheet_name="Orders 2025")
    assert err2 is None and len(df_sheet2) == len(ecom_df), "Failed sheet 2 loading"
    print("Multi-sheet Excel loading verified!")

    # 5. Test Missing and Duplicate Values detection
    print("\n--- Test 5: Missing and Duplicate Values ---")
    dirty_data = pd.DataFrame({
        "ID": ["A1", "A2", "A3", "A3", "A4"],
        "Value": [10.0, np.nan, 30.0, 30.0, np.nan],
        "Flag": [True, False, True, True, False]
    })
    dirty_meta = create_dataset_metadata(dirty_data, "dirty.csv", "CSV")
    assert dirty_meta["missing_cells"] == 2, f"Expected 2 missing cells, got {dirty_meta['missing_cells']}"
    assert dirty_meta["duplicate_rows"] == 1, f"Expected 1 duplicate row, got {dirty_meta['duplicate_rows']}"
    assert dirty_meta["column_types"]["Flag"] == "Boolean", "Flag should be Boolean"
    print(f"Missing count: {dirty_meta['missing_cells']}, Duplicates: {dirty_meta['duplicate_rows']}")
    print("Missing and duplicate detection verified!")

    # 6. Test Invalid & Empty files
    print("\n--- Test 6: Invalid & Empty Files Handling ---")
    empty_csv = io.BytesIO(b"")
    empty_df, err = load_csv(empty_csv, "empty.csv")
    assert empty_df is None and err is not None, "Empty file should return error"
    print(f"Empty file handled cleanly: '{err}'")

    zero_rows_csv = io.BytesIO(b"Col1,Col2,Col3\n")
    zero_df, err = load_csv(zero_rows_csv, "zero.csv")
    assert zero_df is None and err is not None, "Zero rows file should return error"
    print(f"Zero-row file handled cleanly: '{err}'")

    print("\n=== ALL MODULE 2 UNIT & INTEGRATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()

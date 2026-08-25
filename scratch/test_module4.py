"""
Automated unit & integration test suite for Module 4 (Data Quality Engine & Workspace)
"""
import os
import sys
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

from modules.data_loader import (
    load_sample_dataset_by_key,
    create_dataset_metadata
)
from modules.data_quality_engine import (
    analyze_data_quality,
    calculate_data_quality_score,
    analyze_missing_values,
    analyze_duplicates,
    analyze_consistency_and_structure,
    analyze_validity,
    detect_outliers_iqr,
    generate_missing_bar_chart,
    generate_outlier_bar_chart
)

def run_tests():
    print("=== STARTING MODULE 4 DATA QUALITY TEST SUITE ===")

    # 1. Test on Clean Sample Datasets (SaaS Sales & E-Commerce)
    print("\n--- Test 1: Clean Datasets Audit ---")
    saas_df, _, _ = load_sample_dataset_by_key("saas_sales")
    saas_meta = create_dataset_metadata(saas_df, "saas_sales_data.csv", "CSV")
    
    # Store copy to verify immutability
    saas_copy = saas_df.copy(deep=True)
    
    report_saas = analyze_data_quality(saas_df, saas_meta)
    
    # Verify immutability
    pd.testing.assert_frame_equal(saas_df, saas_copy)
    print("Immutability verified: dataset was not mutated during analysis.")

    print(f"SaaS Sales Quality Score: {report_saas['overall_score']} / 100 ({report_saas['status']})")
    print(f"Breakdown: {report_saas['breakdown']}")
    assert 0 <= report_saas["overall_score"] <= 100, "Score out of range [0, 100]"
    assert report_saas["breakdown"]["Completeness"] == 100.0, "SaaS Sales should have 100% completeness"
    assert report_saas["breakdown"]["Uniqueness"] == 100.0, "SaaS Sales should have 100% uniqueness"

    # 2. Test on Synthetic Dirty Dataset
    print("\n--- Test 2: Synthetic Problematic Dataset Quality Audit ---")
    dirty_df = pd.DataFrame({
        "Customer_ID": [f"CUST_{i}" for i in range(20)],
        "Age": [25, 30, -5, 45, 29, 32, 40, 50, 22, 28, 35, 60, 31, 27, 44, 38, 52, 29, 33, 30], # 1 negative age
        "Country": ["India"] * 20, # Constant column (zero variance)
        "Empty_Col": [np.nan] * 20, # 100% Empty column
        "Duplicate_A": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        "Duplicate_B": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20], # Duplicate column pair
        "Income": [50000.0, 60000.0, np.nan, 75000.0, np.nan, 55000.0, 80000.0, 950000.0, # 1 massive outlier (950k) + nulls
                   52000.0, 61000.0, 72000.0, np.nan, 58000.0, 64000.0, 71000.0, 83000.0,
                   54000.0, 62000.0, 70000.0, 50000.0],
        "Score_Str": ["10", "20", "N/A", "30", "40", "error", "50", "60", "70", "80", "90", "100", "110", "120", "130", "140", "150", "160", "170", "180"] # Mixed types
    })
    # Add 2 duplicate rows
    dirty_df = pd.concat([dirty_df, dirty_df.iloc[[0, 1]]], ignore_index=True)
    
    dirty_meta = create_dataset_metadata(dirty_df, "dirty.csv", "CSV")
    report_dirty = analyze_data_quality(dirty_df, dirty_meta)
    
    print(f"Dirty Dataset Overall Score: {report_dirty['overall_score']} / 100 ({report_dirty['status']})")
    print(f"Breakdown: {report_dirty['breakdown']}")
    
    # Verify Empty column detected
    assert "Empty_Col" in report_dirty["consistency_analysis"]["empty_columns"], "Empty_Col was not detected"
    print("Empty column detection verified!")

    # Verify Constant column detected
    const_cols = [c["column"] for c in report_dirty["consistency_analysis"]["constant_columns"]]
    assert "Country" in const_cols, "Country constant column was not detected"
    print("Constant column detection verified!")

    # Verify Duplicate columns detected
    dup_cols = report_dirty["duplicate_analysis"]["duplicate_columns"]
    assert any("Duplicate_A" in pair and "Duplicate_B" in pair for pair in dup_cols), "Duplicate column pair not detected"
    print(f"Duplicate column pair detected: {dup_cols}")

    # Verify Duplicate rows detected
    assert report_dirty["duplicate_analysis"]["duplicate_rows"] == 2, "Expected 2 duplicate rows"
    print("Duplicate rows verified (2 rows detected)!")

    # Verify Outliers detected in Income
    outlier_cols = [o["column"] for o in report_dirty["outlier_analysis"]["column_outliers"]]
    assert "Income" in outlier_cols, "Income outlier (950k) not detected"
    print("Income outlier detection verified!")

    # Verify Negative age detected in Validity
    val_issues = [v["issue_type"] for v in report_dirty["validity_analysis"]["invalid_findings"]]
    assert "Unexpected Negative Values" in val_issues, "Negative age was not caught"
    print("Negative age invalidity detection verified!")

    # Verify Problematic columns ranked worst first
    worst_col = report_dirty["column_quality_scores"][0]["column"]
    assert worst_col in ["Empty_Col", "Income", "Score_Str", "Country"], f"Unexpected worst column: {worst_col}"
    print(f"Top 3 most problematic columns: {[c['column'] + ' (' + str(c['quality_score']) + ')' for c in report_dirty['column_quality_scores'][:3]]}")

    # 3. Test Plotly Visualizations (Dark and Light)
    print("\n--- Test 3: Plotly Visualizations Generation ---")
    for theme in ["Dark", "Light"]:
        miss_chart = generate_missing_bar_chart(report_dirty["missing_analysis"]["column_missing_details"], theme=theme)
        assert miss_chart is not None, f"Missing chart failed for {theme}"
        
        out_chart = generate_outlier_bar_chart(report_dirty["outlier_analysis"]["column_outliers"], theme=theme)
        assert out_chart is not None, f"Outlier chart failed for {theme}"
        print(f"Charts generated successfully for {theme} mode!")

    print("\n=== ALL MODULE 4 DATA QUALITY UNIT & INTEGRATION TESTS PASSED! ===")

if __name__ == "__main__":
    run_tests()

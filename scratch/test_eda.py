"""
Verification test script for Module 6 — EDA (Exploratory Data Analysis).
Tests calculations, edge cases, Plotly chart generation, and automated insights.
"""
import sys
import os
import io
import pandas as pd
import numpy as np

# Force UTF-8 on stdout for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.eda_engine import (
    compute_summary_statistics,
    compute_correlation_matrix,
    extract_strongest_correlations,
    compute_iqr_outliers,
    analyze_column_deep_dive,
    generate_eda_insights,
    generate_correlation_heatmap,
    generate_distribution_histogram,
    generate_distribution_boxplot,
    generate_outlier_inspector_chart,
    generate_categorical_barchart,
    generate_datetime_timeline_chart,
    interpret_skewness,
    interpret_kurtosis
)
from modules.eda_page import render_eda_page
from modules.eda_tools import render_eda_page as tools_render_eda_page


def test_saas_sales_data():
    print("\n--- Testing with saas_sales_data.csv ---")
    df = pd.read_csv("sample_data/saas_sales_data.csv")
    print(f"Loaded dataset: {len(df)} rows, {len(df.columns)} columns")

    # 1. Summary statistics
    summary_df = compute_summary_statistics(df)
    assert not summary_df.empty, "Summary stats should not be empty"
    print(f"[OK] Summary statistics calculated: {len(summary_df)} numeric features")
    for col in ["Mean", "Median", "Std Dev", "Min", "25% (Q1)", "50% (Q2)", "75% (Q3)", "Max", "Skewness", "Kurtosis"]:
        assert col in summary_df.columns, f"Missing {col} in summary table"

    # 2. Correlations
    corr_p = compute_correlation_matrix(df, method="pearson")
    corr_s = compute_correlation_matrix(df, method="spearman")
    assert not corr_p.empty, "Pearson correlation matrix should not be empty"
    assert not corr_s.empty, "Spearman correlation matrix should not be empty"
    pos_pairs, neg_pairs = extract_strongest_correlations(corr_p)
    print(f"[OK] Pearson correlation computed ({len(corr_p.columns)}x{len(corr_p.columns)}), Top positive pairs: {len(pos_pairs)}, Top negative pairs: {len(neg_pairs)}")

    # 3. IQR Outliers
    outliers = compute_iqr_outliers(df)
    assert "summary_df" in outliers
    print(f"[OK] Outlier analysis: Total outliers = {outliers['total_outliers']}, Overall rate = {outliers['overall_outlier_rate']:.2f}%")

    # 4. Column Deep Dive
    for col in df.columns:
        profile = analyze_column_deep_dive(df, col)
        assert profile, f"Profile for {col} failed"
    print(f"[OK] Deep dive profiled across all {len(df.columns)} columns")

    # 5. Deterministic Insights
    insights = generate_eda_insights(df)
    print(f"[OK] Generated {len(insights)} deterministic insights:")
    for ins in insights:
        print(f"     - [{ins['category']}] ({ins['severity']}) {ins['title']}")

    # 6. Plotly Figures
    fig_heat = generate_correlation_heatmap(corr_p, theme="Dark")
    assert fig_heat is not None, "Heatmap fig should not be None"
    fig_hist = generate_distribution_histogram(df[summary_df.iloc[0]["Column"]], summary_df.iloc[0]["Column"], theme="Light")
    assert fig_hist is not None, "Hist fig should not be None"
    fig_box = generate_distribution_boxplot(df[summary_df.iloc[0]["Column"]], summary_df.iloc[0]["Column"], theme="Dark")
    assert fig_box is not None, "Box fig should not be None"
    print("[OK] Plotly figures generated successfully in Dark and Light themes")


def test_ecommerce_orders():
    print("\n--- Testing with ecommerce_orders.csv ---")
    df = pd.read_csv("sample_data/ecommerce_orders.csv")
    print(f"Loaded dataset: {len(df)} rows, {len(df.columns)} columns")

    summary_df = compute_summary_statistics(df)
    print(f"[OK] Summary statistics calculated: {len(summary_df)} numeric features")

    insights = generate_eda_insights(df)
    print(f"[OK] Generated {len(insights)} deterministic insights")

    # Test categorical & datetime deep dives
    for col in df.columns:
        profile = analyze_column_deep_dive(df, col)
        det_type = profile["detected_type"]
        if det_type in ["Categorical", "Text"]:
            fig_bar = generate_categorical_barchart(profile.get("frequency_table", pd.DataFrame()), col)
        elif det_type == "Date/Time" and "dt_series" in profile:
            fig_tl = generate_datetime_timeline_chart(profile["dt_series"], col)
    print("[OK] Categorical and Datetime deep dives and charts generated without error")


def test_edge_cases():
    print("\n--- Testing Edge Cases ---")

    # 1. Dataset with 0 numeric columns
    df_no_num = pd.DataFrame({
        "category": ["A", "B", "C", "A", "B"],
        "label": ["High", "Low", "Medium", "High", "Low"]
    })
    stats_0 = compute_summary_statistics(df_no_num)
    assert stats_0.empty, "Stats should be empty for 0 numeric columns"
    corr_0 = compute_correlation_matrix(df_no_num)
    assert corr_0.empty, "Corr should be empty for 0 numeric columns"
    pos_0, neg_0 = extract_strongest_correlations(corr_0)
    assert pos_0 == [] and neg_0 == []
    ins_0 = generate_eda_insights(df_no_num)
    print("[OK] Passed 0 numeric columns edge case")

    # 2. Dataset with only 1 numeric column
    df_1_num = pd.DataFrame({
        "val": [10.5, 20.2, 30.1, 40.8, 50.0],
        "category": ["A", "B", "C", "A", "B"]
    })
    stats_1 = compute_summary_statistics(df_1_num)
    assert len(stats_1) == 1
    corr_1 = compute_correlation_matrix(df_1_num)
    assert corr_1.empty, "Corr should be empty for 1 numeric column"
    ins_1 = generate_eda_insights(df_1_num)
    print("[OK] Passed 1 numeric column edge case")

    # 3. Dataset with missing values, extreme outliers, and constant columns
    df_complex = pd.DataFrame({
        "num_skewed": [1, 2, 2, 3, 2, 3, 2, 100, 200, np.nan],
        "constant_col": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
        "all_nulls": [np.nan] * 10,
        "dup_col": ["X", "X", "Y", "Y", "X", "X", "Y", "Y", "X", "X"]
    })
    stats_c = compute_summary_statistics(df_complex)
    assert len(stats_c) >= 2
    outliers_c = compute_iqr_outliers(df_complex)
    assert outliers_c["total_outliers"] > 0
    ins_c = generate_eda_insights(df_complex)
    assert len(ins_c) > 0
    print(f"[OK] Passed complex edge case (skewness, constants, outliers, missingness)")

    # 4. Statistical helper functions
    assert interpret_skewness(0.1)["category"] == "symmetric"
    assert interpret_skewness(1.8)["category"] == "right_high"
    assert interpret_skewness(-2.1)["category"] == "left_high"
    assert interpret_kurtosis(1.2)["category"] == "leptokurtic"
    assert interpret_kurtosis(-0.8)["category"] == "platykurtic"
    print("[OK] Passed skewness and kurtosis interpretation helpers")


if __name__ == "__main__":
    test_saas_sales_data()
    test_ecommerce_orders()
    test_edge_cases()
    print("\nALL EDA TESTS PASSED SUCCESSFULLY!")

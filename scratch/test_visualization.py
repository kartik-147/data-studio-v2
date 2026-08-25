"""
Comprehensive Test Suite for Visualization Studio (Module 8)
=============================================================================
Tests:
1. All 12 Chart Types (Bar, Horizontal Bar, Grouped Bar, Line, Area, Scatter, Bubble, Histogram, Box, Pie, Donut, Heatmap, Violin)
2. Aggregation modes (Count, Sum, Mean, Median, Min, Max)
3. Edge case datasets:
   - Mixed business dataset (saas_sales_data.csv)
   - Numeric-only dataset
   - Categorical-only dataset
   - Missing values & NaNs dataset
   - Single-column dataset
   - Small 3-row dataset
   - Empty/None dataset
4. Deterministic Smart Recommendations Engine
5. Deterministic Analytical Chart Insights Engine
6. Multi-Format Export: PNG, HTML, JSON
7. Light and Dark Themes
"""
import os
import sys
import json
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.visualization_engine import (
    CHART_FAMILIES,
    CHART_METADATA,
    get_dataset_column_types,
    is_chart_compatible,
    get_compatible_chart_types,
    aggregate_data,
    build_chart,
    generate_chart_recommendations,
    generate_chart_insights,
    export_chart_png,
    export_chart_html,
    export_chart_config_json
)


def run_tests():
    print("=====================================================================")
    print("STARTING DATA STUDIO v2 VISUALIZATION STUDIO TEST SUITE")
    print("=====================================================================\n")

    # 1. Load Standard Mixed Dataset
    csv_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "saas_sales_data.csv")
    if os.path.exists(csv_path):
        df_mixed = pd.read_csv(csv_path)
        print(f"[OK] Loaded sample saas_sales_data.csv ({len(df_mixed)} rows, {len(df_mixed.columns)} columns)")
    else:
        # Synthetic fallback
        df_mixed = pd.DataFrame({
            "Customer": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"],
            "Region": ["North", "South", "North", "East", "West", "East"],
            "Tier": ["Enterprise", "SMB", "Enterprise", "Mid-Market", "SMB", "Enterprise"],
            "MRR": [5000.0, 1200.0, 4500.0, 3000.0, 800.0, 6200.0],
            "ARR": [60000.0, 14400.0, 54000.0, 36000.0, 9600.0, 74400.0],
            "Quantity": [10, 3, 8, 5, 2, 12],
            "Date": pd.date_range("2024-01-01", periods=6, freq="ME")
        })
        print(f"[OK] Created synthetic mixed dataset ({len(df_mixed)} rows)")

    col_types = get_dataset_column_types(df_mixed)
    print(f"  - Detected Types: Numeric={col_types['Numeric']}, Categorical={col_types['Categorical']}, Date/Time={col_types['Date/Time']}")

    # 2. Test All 12 Chart Types on Mixed Dataset
    print("\n--- Testing 12 Chart Types on Mixed Dataset ---")

    date_col = "Signup_Date" if "Signup_Date" in df_mixed.columns else ("Date" if "Date" in df_mixed.columns else df_mixed.columns[0])
    size_col = "Active_Users" if "Active_Users" in df_mixed.columns else ("Quantity" if "Quantity" in df_mixed.columns else "Discount_Pct")
    y_metric = "MRR" if "MRR" in df_mixed.columns else col_types["Numeric"][0]
    sec_metric = "Satisfaction_Score" if "Satisfaction_Score" in df_mixed.columns else (col_types["Numeric"][1] if len(col_types["Numeric"]) > 1 else y_metric)

    test_configs = {
        "bar": {"x": "Region", "y": y_metric, "agg": "Sum", "sort": "value_desc", "top_n": 10},
        "horizontal_bar": {"y": "Region", "x": y_metric, "agg": "Mean", "sort": "value_asc", "top_n": 10},
        "grouped_bar": {"x": "Region", "y": y_metric, "color": "Plan_Tier" if "Plan_Tier" in df_mixed.columns else None, "agg": "Sum", "barmode": "group"},
        "line": {"x": date_col, "y": y_metric, "agg": "Sum", "show_markers": True},
        "area": {"x": date_col, "y": y_metric, "agg": "Sum"},
        "scatter": {"x": y_metric, "y": sec_metric, "color": "Region", "show_trendline": True},
        "bubble": {"x": y_metric, "y": sec_metric, "size": size_col, "color": "Region"},
        "histogram": {"x": y_metric, "nbins": 15, "marginal": "box"},
        "box": {"y": y_metric, "x": "Region", "points": "outliers"},
        "pie": {"x": "Region", "y": y_metric, "agg": "Sum", "top_n": 5},
        "donut": {"x": "Region", "y": y_metric, "agg": "Sum", "top_n": 5},
        "heatmap": {"columns": col_types["Numeric"], "method": "pearson"},
        "violin": {"y": y_metric, "x": "Region", "show_box": True, "points": "outliers"}
    }

    for c_type, cfg in test_configs.items():
        # Test Dark Theme
        fig_dark, data_df, err = build_chart(c_type, df_mixed, cfg, theme="Dark")
        assert err is None, f"Error building {c_type} (Dark): {err}"
        assert fig_dark is not None, f"Figure was None for {c_type} (Dark)"

        # Test Light Theme
        fig_light, _, err_l = build_chart(c_type, df_mixed, cfg, theme="Light")
        assert err_l is None, f"Error building {c_type} (Light): {err_l}"
        assert fig_light is not None, f"Figure was None for {c_type} (Light)"

        # Test Insights
        insights = generate_chart_insights(c_type, df_mixed, cfg, data_df=data_df)
        print(f"  [PASS] {c_type:<15}: Built successfully | Insights count={len(insights)}")

    # 3. Test All Aggregation Functions
    print("\n--- Testing Aggregation Options (Count, Sum, Mean, Median, Min, Max) ---")
    for agg in ["Count", "Sum", "Mean", "Median", "Minimum", "Maximum"]:
        agg_df, eff_x, eff_y = aggregate_data(df_mixed, x_col="Region", y_col="MRR", agg_func=agg)
        assert not agg_df.empty, f"Agg df was empty for agg={agg}"
        print(f"  [PASS] Aggregation '{agg}': Returned {len(agg_df)} rows for {eff_y}")

    # 4. Test Smart Recommendation Engine
    print("\n--- Testing Deterministic Recommendations Engine ---")
    recs = generate_chart_recommendations(df_mixed)
    assert len(recs) >= 3, f"Expected at least 3 recommendations, got {len(recs)}"
    for r in recs:
        print(f"  [PASS] Recommendation: {r['title']} ({r['chart_type']}) - {r['badge']}")
        # Verify recommendation config can be built directly
        fig_r, _, err_r = build_chart(r["chart_type"], df_mixed, r["config"])
        assert err_r is None, f"Recommended chart failed to build: {err_r}"

    # 5. Test Edge Cases
    print("\n--- Testing Edge Case Datasets ---")

    # A. Numeric-only dataset
    df_num_only = pd.DataFrame({
        "Metric_A": [10.5, 20.3, 15.2, 40.8, 30.1, 55.4],
        "Metric_B": [100, 200, 150, 400, 300, 550],
        "Metric_C": [1.1, 2.2, 1.5, 4.0, 3.1, 5.5]
    })
    types_num = get_dataset_column_types(df_num_only)
    compat_num = get_compatible_chart_types(df_num_only, types_num)
    assert "histogram" in compat_num["Distribution"]
    assert "scatter" in compat_num["Relationships"]
    fig, _, err = build_chart("histogram", df_num_only, {"x": "Metric_A", "nbins": 10})
    assert err is None
    fig_corr, _, err = build_chart("heatmap", df_num_only, {"columns": ["Metric_A", "Metric_B", "Metric_C"]})
    assert err is None
    print("  [PASS] Numeric-only dataset handled cleanly")

    # B. Categorical-only dataset
    df_cat_only = pd.DataFrame({
        "Category_1": ["Red", "Blue", "Red", "Green", "Blue", "Red"],
        "Category_2": ["Small", "Large", "Medium", "Small", "Medium", "Large"]
    })
    types_cat = get_dataset_column_types(df_cat_only)
    compat_cat = get_compatible_chart_types(df_cat_only, types_cat)
    assert "bar" in compat_cat["Comparison"]
    assert "pie" in compat_cat["Composition"]
    fig_cat_bar, _, err = build_chart("bar", df_cat_only, {"x": "Category_1", "y": None, "agg": "Count"})
    assert err is None
    fig_cat_pie, _, err = build_chart("pie", df_cat_only, {"x": "Category_1", "y": None, "agg": "Count"})
    assert err is None
    recs_cat = generate_chart_recommendations(df_cat_only)
    assert len(recs_cat) >= 1
    print("  [PASS] Categorical-only dataset handled cleanly (Auto-count mode)")

    # C. Dataset with Missing Values / NaNs
    df_missing = pd.DataFrame({
        "Category": ["A", None, "B", "C", None, "A"],
        "Value_1": [10.0, np.nan, 30.0, np.nan, 50.0, 60.0],
        "Value_2": [np.nan, 20.0, 40.0, 60.0, 80.0, np.nan]
    })
    fig_m_bar, _, err = build_chart("bar", df_missing, {"x": "Category", "y": "Value_1", "agg": "Sum"})
    assert err is None
    fig_m_scatter, _, err = build_chart("scatter", df_missing, {"x": "Value_1", "y": "Value_2"})
    assert err is None
    fig_m_hist, _, err = build_chart("histogram", df_missing, {"x": "Value_1"})
    assert err is None
    print("  [PASS] Dataset with missing values / NaNs handled cleanly")

    # D. Single-column dataset
    df_single = pd.DataFrame({"Values": [10, 20, 30, 40, 50]})
    fig_s_hist, _, err = build_chart("histogram", df_single, {"x": "Values", "nbins": 5})
    assert err is None
    fig_s_box, _, err = build_chart("box", df_single, {"y": "Values"})
    assert err is None
    print("  [PASS] Single-column dataset handled cleanly")

    # E. Small 3-row dataset
    df_small = pd.DataFrame({
        "City": ["Tokyo", "Paris", "NYC"],
        "Population": [14000000, 2100000, 8400000]
    })
    fig_small, _, err = build_chart("bar", df_small, {"x": "City", "y": "Population", "agg": "Sum"})
    assert err is None
    print("  [PASS] Small 3-row dataset handled cleanly")

    # F. Empty / None dataset
    fig_empty, _, err = build_chart("bar", pd.DataFrame(), {"x": "None", "y": "None"})
    assert err is not None
    print("  [PASS] Empty dataset handled with proper error message")

    # 6. Test Multi-Format Export Capabilities
    print("\n--- Testing Multi-Format Export Options (PNG, HTML, JSON) ---")
    sample_fig, _, _ = build_chart("bar", df_mixed, test_configs["bar"])
    
    # PNG export (Kaleido)
    png_bytes, png_err = export_chart_png(sample_fig)
    assert png_err is None, f"PNG export failed: {png_err}"
    assert png_bytes is not None and len(png_bytes) > 1000, f"Invalid PNG bytes len={len(png_bytes) if png_bytes else 0}"
    print(f"  [PASS] PNG Export generated: {len(png_bytes):,} bytes")

    # HTML export
    html_str = export_chart_html(sample_fig, title="Test Bar Chart")
    assert "plotly" in html_str.lower() and "<html" in html_str.lower()
    print(f"  [PASS] HTML Export generated: {len(html_str):,} characters")

    # JSON export
    json_str = export_chart_config_json(test_configs["bar"], "bar")
    parsed_json = json.loads(json_str)
    assert parsed_json["chart_type"] == "bar"
    assert parsed_json["configuration"]["x"] == "Region"
    print(f"  [PASS] JSON Config Export generated: valid schema verified")

    print("\n=====================================================================")
    print("ALL TESTS PASSED SUCCESSFULLY! (100% PASS RATE)")
    print("=====================================================================")


if __name__ == "__main__":
    run_tests()

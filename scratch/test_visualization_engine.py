"""
Automated unit verification script for Visualization Engine and All 25 Chart Types.
"""
import sys
import os
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.visualization_engine import (
    CHART_FAMILIES,
    CHART_METADATA,
    build_chart,
    generate_chart_recommendations,
    generate_chart_insights,
    export_chart_png,
    export_chart_html,
    export_chart_config_json,
    get_dataset_column_types,
    get_compatible_chart_types,
    is_chart_compatible
)
import modules.visualization as viz
import modules.ui_components as ui
import modules.overview as ov
import modules.settings as st_page
import modules.admin_analytics as admin_page
import modules.dashboard as dash
import modules.eda_page as eda
import modules.data_quality as dq
import modules.data_preparation as dp
import modules.data_profiler as dprof
import modules.ai_analyst as ai

print("[OK] All 11 application modules imported successfully without errors!")

# Create a rich sample dataset with multiple numeric, categorical, and datetime columns
np.random.seed(42)
n_rows = 120
sample_df = pd.DataFrame({
    "Order_Date": pd.date_range(start="2024-01-01", periods=n_rows, freq="D"),
    "Region": np.random.choice(["North America", "Europe", "Asia-Pacific", "Latin America"], size=n_rows),
    "Category": np.random.choice(["Electronics", "Furniture", "Office Supplies", "Apparel"], size=n_rows),
    "Sub_Category": np.random.choice(["Phones", "Chairs", "Paper", "Laptops", "Desks", "Shoes"], size=n_rows),
    "Sales": np.random.uniform(50, 5000, size=n_rows).round(2),
    "Profit": np.random.uniform(-500, 1500, size=n_rows).round(2),
    "Quantity": np.random.randint(1, 20, size=n_rows),
    "Discount": np.random.choice([0.0, 0.05, 0.1, 0.15, 0.2, 0.3], size=n_rows),
    "Customer_Rating": np.random.uniform(1.0, 5.0, size=n_rows).round(1)
})

print(f"Sample Dataset Shape: {sample_df.shape}")
col_types = get_dataset_column_types(sample_df)
print(f"Column types: {col_types}")

# Test all 25 chart types
all_charts = []
for fam, charts in CHART_FAMILIES.items():
    all_charts.extend(charts)

print(f"\nTesting {len(all_charts)} chart types...")
success_count = 0
failed_charts = []

test_configs = {
    "bar": {"x": "Category", "y": "Sales", "agg": "Sum", "sort": "value_desc", "top_n": 10},
    "horizontal_bar": {"y": "Region", "x": "Profit", "agg": "Sum", "sort": "value_desc", "top_n": 10},
    "grouped_bar": {"x": "Category", "y": "Sales", "color": "Region", "barmode": "group", "agg": "Sum"},
    "lollipop": {"x": "Category", "y": "Sales", "agg": "Sum", "sort": "value_desc", "top_n": 10},
    "waterfall": {"x": "Category", "y": "Profit", "agg": "Sum"},
    "radar": {"metrics": ["Sales", "Profit", "Quantity", "Customer_Rating"], "agg": "Mean", "x": "Category"},
    "line": {"x": "Order_Date", "y": "Sales", "agg": "Sum", "show_markers": True},
    "area": {"x": "Order_Date", "y": "Sales", "agg": "Sum"},
    "stepline": {"x": "Order_Date", "y": "Profit", "agg": "Sum"},
    "multi_line": {"x": "Order_Date", "metrics": ["Sales", "Profit", "Quantity"], "agg": "Sum"},
    "scatter": {"x": "Sales", "y": "Profit", "color": "Category", "show_trendline": True},
    "bubble": {"x": "Sales", "y": "Profit", "size": "Quantity", "color": "Region"},
    "scatter_3d": {"x": "Sales", "y": "Profit", "z": "Quantity", "color": "Category"},
    "density_contour": {"x": "Sales", "y": "Profit", "color": "Category"},
    "histogram": {"x": "Sales", "nbins": 25, "marginal": "box"},
    "box": {"y": "Sales", "x": "Category", "color": "Category", "points": "outliers"},
    "violin": {"y": "Profit", "x": "Region", "color": "Region", "show_box": True},
    "ecdf": {"x": "Sales", "color": "Category"},
    "pie": {"x": "Category", "y": "Sales", "agg": "Sum", "top_n": 8},
    "donut": {"x": "Region", "y": "Profit", "agg": "Sum", "top_n": 8},
    "treemap": {"x": "Category", "sub_category": "Sub_Category", "y": "Sales", "agg": "Sum"},
    "sunburst": {"x": "Region", "sub_category": "Category", "y": "Sales", "agg": "Sum"},
    "funnel": {"x": "Category", "y": "Sales", "agg": "Sum", "top_n": 8},
    "heatmap": {"columns": ["Sales", "Profit", "Quantity", "Discount", "Customer_Rating"], "method": "pearson"},
    "gauge": {"y": "Sales", "agg": "Mean"}
}

for c_type in all_charts:
    cfg = test_configs.get(c_type, {"x": "Category", "y": "Sales", "agg": "Sum"})
    fig, data_df, err = build_chart(c_type, sample_df, cfg, theme="Dark")
    if err or fig is None:
        print(f"[FAIL] {c_type} - {err}")
        failed_charts.append((c_type, err))
    else:
        # Test insights generation
        insights = generate_chart_insights(c_type, sample_df, cfg, data_df=data_df)
        print(f"[PASS] {c_type:16} (Figure generated successfully, {len(insights)} insights calculated)")
        success_count += 1

print(f"\nResults: {success_count}/{len(all_charts)} Chart Types Tested Successfully!")
if failed_charts:
    print(f"Failed charts: {failed_charts}")
    sys.exit(1)

# Test recommendations
recs = generate_chart_recommendations(sample_df)
print(f"[OK] Smart Recommendations generated: {len(recs)} suggestions")
for r in recs:
    print(f"  - [{r['family']}] {r['title']} ({r['chart_type']})")

# Test HTML export
html_str = export_chart_html(fig)
assert len(html_str) > 100, "HTML export is empty"
print("[OK] HTML export verified")

# Test JSON export
json_str = export_chart_config_json(cfg, "bar")
assert "app" in json_str, "JSON export is invalid"
print("[OK] Config JSON export verified")

# Test Workflow Navigation structure across all modules
print("\nVerifying workflow navigation across all pages...")
for step in ui.ANALYTICAL_WORKFLOW_STEPS:
    print(f"  - Workflow Step: {step['page_key']} -> {step['name']} ({step['icon']})")

print("\nALL TESTS COMPLETED AND VERIFIED SUCCESSFULLY!")


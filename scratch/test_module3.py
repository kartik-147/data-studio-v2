"""
Automated unit & integration test suite for Module 3 (Automatic Dataset Dashboard)
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
from modules.dashboard_engine import (
    select_analytical_columns,
    prioritize_numeric_columns,
    prioritize_categorical_columns,
    select_primary_kpi_metric,
    generate_smart_insights,
    generate_composition_chart,
    generate_numeric_distribution_chart,
    generate_categorical_bar_chart,
    generate_time_trend_chart,
    generate_correlation_heatmap
)

def run_tests():
    print("=== STARTING MODULE 3 DASHBOARD TEST SUITE ===")

    # 1. Test on SaaS Sales Data
    print("\n--- Test 1: Dashboard Engine on SaaS Sales Dataset ---")
    saas_df, _, _ = load_sample_dataset_by_key("saas_sales")
    saas_meta = create_dataset_metadata(saas_df, "saas_sales_data.csv", "CSV")
    
    cols = select_analytical_columns(saas_df, saas_meta)
    print(f"Analytical cols: numeric={cols['numeric']}, cat={cols['categorical']}, dt={cols['datetime']}, text={cols['text']}")
    
    assert "Customer_ID" not in cols["numeric"], "Customer_ID should be excluded from numeric"
    assert "MRR" in cols["numeric"], "MRR should be in numeric"
    assert "Signup_Date" in cols["datetime"], "Signup_Date should be in datetime"
    
    ranked_num = prioritize_numeric_columns(saas_df, cols["numeric"])
    ranked_cat = prioritize_categorical_columns(saas_df, cols["categorical"])
    print(f"Ranked numeric: {ranked_num}")
    print(f"Ranked cat: {ranked_cat}")
    
    # Primary KPI selection
    kpi = select_primary_kpi_metric(saas_df, ranked_num)
    assert kpi is not None, "Primary KPI should not be None"
    print(f"Primary KPI: {kpi['label']} = {kpi['value']}")
    
    # Insights generation
    insights = generate_smart_insights(saas_df, saas_meta, cols)
    assert len(insights) >= 3, f"Expected >= 3 insights, got {len(insights)}"
    print(f"Generated {len(insights)} deterministic insights:")
    for ins in insights:
        print(f"  • [{ins['title']}] {ins['text']}")

    # Charts generation (Dark & Light)
    for theme in ["Dark", "Light"]:
        donut = generate_composition_chart(saas_meta, theme=theme)
        assert donut is not None, "Composition chart failed"
        
        hist = generate_numeric_distribution_chart(saas_df, ranked_num[0], theme=theme)
        assert hist is not None, "Histogram failed"
        
        bar = generate_categorical_bar_chart(saas_df, ranked_cat[0], theme=theme)
        assert bar is not None, "Bar chart failed"
        
        trend = generate_time_trend_chart(saas_df, cols["datetime"][0], metric_col=ranked_num[0], theme=theme)
        assert trend is not None, "Time trend chart failed"
        
        corr_fig, top_pair = generate_correlation_heatmap(saas_df, ranked_num, theme=theme)
        assert corr_fig is not None and top_pair is not None, "Correlation heatmap failed"
        print(f"Theme {theme} charts verified! Top corr pair: {top_pair}")

    # 2. Test on E-Commerce Dataset
    print("\n--- Test 2: Dashboard Engine on E-Commerce Dataset ---")
    ecom_df, _, _ = load_sample_dataset_by_key("ecommerce")
    ecom_meta = create_dataset_metadata(ecom_df, "ecommerce_orders.csv", "CSV")
    ecom_cols = select_analytical_columns(ecom_df, ecom_meta)
    ecom_ranked_num = prioritize_numeric_columns(ecom_df, ecom_cols["numeric"])
    ecom_kpi = select_primary_kpi_metric(ecom_df, ecom_ranked_num)
    print(f"E-Commerce KPI: {ecom_kpi['label']} = {ecom_kpi['value']}")
    assert "Sales" in ecom_ranked_num or "Profit" in ecom_ranked_num

    # 3. Test Edge Cases (Only Numeric, Only Categorical, Only Text, Single Row)
    print("\n--- Test 3: Edge Cases ---")
    
    # 3a. Only Numeric
    num_only_df = pd.DataFrame({"A": [1.0, 2.0, 3.0, 4.0], "B": [10.0, 20.0, 30.0, 40.0]})
    meta_num = create_dataset_metadata(num_only_df, "num.csv")
    cols_num = select_analytical_columns(num_only_df, meta_num)
    assert len(cols_num["numeric"]) == 2 and len(cols_num["categorical"]) == 0
    ins_num = generate_smart_insights(num_only_df, meta_num, cols_num)
    assert len(ins_num) > 0
    print("Numeric-only dataset handled safely!")

    # 3b. Only Categorical
    cat_only_df = pd.DataFrame({"Dept": ["Sales", "HR", "Sales", "IT"], "Role": ["Senior", "Junior", "Senior", "Lead"]})
    meta_cat = create_dataset_metadata(cat_only_df, "cat.csv")
    cols_cat = select_analytical_columns(cat_only_df, meta_cat)
    assert len(cols_cat["categorical"]) == 2 and len(cols_cat["numeric"]) == 0
    ins_cat = generate_smart_insights(cat_only_df, meta_cat, cols_cat)
    assert len(ins_cat) > 0
    print("Categorical-only dataset handled safely!")

    # 3c. Only Text / ID
    text_only_df = pd.DataFrame({"ID": [f"ID_{i}" for i in range(20)], "Notes": [f"Note text {i}" for i in range(20)]})
    meta_text = create_dataset_metadata(text_only_df, "text.csv")
    cols_text = select_analytical_columns(text_only_df, meta_text)
    assert len(cols_text["text"]) == 2
    ins_text = generate_smart_insights(text_only_df, meta_text, cols_text)
    assert len(ins_text) > 0
    print("Text-only dataset handled safely!")

    print("\n=== ALL MODULE 3 UNIT & INTEGRATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()

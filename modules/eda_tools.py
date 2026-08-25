"""
DATA STUDIO v2 — EDA Module Interface & Router Integration (Module 6)
=============================================================================
Re-exports the primary EDA page view and calculations for seamless routing.
"""
from modules.eda_page import render_eda_page
from modules.eda_engine import (
    compute_summary_statistics,
    compute_correlation_matrix,
    compute_iqr_outliers,
    analyze_column_deep_dive,
    generate_eda_insights
)

__all__ = [
    "render_eda_page",
    "compute_summary_statistics",
    "compute_correlation_matrix",
    "compute_iqr_outliers",
    "analyze_column_deep_dive",
    "generate_eda_insights"
]

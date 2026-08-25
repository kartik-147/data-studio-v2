"""
DATA STUDIO v2 — Overview Landing Module (Module 1 Foundation)
"""
from modules.ui_components import render_notification
import streamlit as st
from modules.ui_components import (
    render_page_header,
    render_empty_state,
    render_section_header,
    render_metric_card
)

from modules.config import is_dataset_loaded

def render_overview_page() -> None:
    """Render the Overview landing view with pre-dataset onboarding and workflow guide."""
    # Page Header with Lucide icon
    render_page_header(
        title="Welcome to Data Studio",
        subtitle="Upload a dataset to explore, analyze, visualize, and uncover insights from your data.",
        icon="home"
    )
    
    dataset_loaded = is_dataset_loaded()
    
    if not dataset_loaded:
        # Empty workspace state card
        render_empty_state(
            title="No dataset loaded",
            description="Upload a CSV or Excel file to start exploring your data and generating automated analytical dashboards.",
            icon="database"
        )
        
        # Primary Action Button: Navigates cleanly to Dataset page
        action_col_left, action_col_center, action_col_right = st.columns([1, 2, 1])
        with action_col_center:
            if st.button("Upload Your First Dataset", key="overview_cta_btn", use_container_width=True, type="primary"):
                st.session_state["current_page"] = "Dataset"
                st.rerun()
    else:
        name = st.session_state.get("dataset_name", "dataset")
        meta = st.session_state.get("dataset_metadata", {})
        rows = meta.get("total_rows", 0)
        cols = meta.get("total_columns", 0)
        
        render_notification(
            title=f"Active Dataset: {name}",
            message=f"{rows:,} records and {cols} columns loaded into memory. Ready for inspection and exploratory analysis.",
            variant="success"
        )
        
        action_col_left, action_col_center, action_col_right = st.columns([1, 2, 1])
        with action_col_center:
            if st.button("Open Dataset Workspace", key="overview_goto_dataset_btn", use_container_width=True, type="primary"):
                st.session_state["current_page"] = "Dataset"
                st.rerun()
                
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    
    # Section: Analytical Workflow
    render_section_header(
        title="Analysis Workflow",
        subtitle="How Data Studio transforms raw data into actionable intelligence."
    )
    
    # 4-Step Structured Workflow
    st.markdown("""
    <div class="ds-workflow-container">
        <div class="ds-workflow-step">
            <span class="ds-step-num">STEP 01</span>
            <span class="ds-step-title">Upload Dataset</span>
            <span class="ds-step-desc">Connect CSV or Excel files with automated schema and encoding detection.</span>
        </div>
        <div class="ds-workflow-step">
            <span class="ds-step-num">STEP 02</span>
            <span class="ds-step-title">Inspect Data</span>
            <span class="ds-step-desc">Profile data types, missing rates, duplicate records, and health scores.</span>
        </div>
        <div class="ds-workflow-step">
            <span class="ds-step-num">STEP 03</span>
            <span class="ds-step-title">Build Dashboard</span>
            <span class="ds-step-desc">Automatically compute executive KPIs and select high-priority charts.</span>
        </div>
        <div class="ds-workflow-step">
            <span class="ds-step-num">STEP 04</span>
            <span class="ds-step-title">Explore Insights</span>
            <span class="ds-step-desc">Run deep-dive EDA, interactive chart exploration, and natural language AI queries.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

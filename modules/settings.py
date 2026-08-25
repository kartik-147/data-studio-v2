"""
DATA STUDIO v2 — Settings Module (Module 1 Foundation)
"""
import streamlit as st
from modules.ui_components import (
    render_page_header,
    render_section_header,
    render_metric_card,
    render_notification
)
from modules.config import APP_VERSION, APP_NAME
from modules.data_loader import clear_dataset_state

def render_settings_page() -> None:
    """Render application settings and appearance preferences."""
    render_page_header(
        title="Settings",
        subtitle="Manage workspace appearance, view session properties, and configure application preferences.",
        icon="settings"
    )
    
    # Section: Theme & Appearance
    render_section_header(
        title="Appearance & Theme",
        subtitle="Customize the visual mode across all Data Studio modules."
    )
    
    current_theme = st.session_state.get("theme", "Dark")
    col_theme_1, col_theme_2 = st.columns([1, 3])
    with col_theme_1:
        theme_choice = st.radio(
            "Color Theme",
            options=["Dark", "Light"],
            index=0 if current_theme == "Dark" else 1,
            label_visibility="collapsed",
            horizontal=True
        )
        if theme_choice != current_theme:
            st.session_state["theme"] = theme_choice
            st.rerun()
            
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    # Section: Session Information
    render_section_header(
        title="Session Diagnostics",
        subtitle="Active session parameters and system state."
    )
    
    c1, c2, c3 = st.columns(3)
    with c1:
        render_metric_card(
            label="Active Route",
            value=st.session_state.get("current_page", "Overview"),
            status="Route"
        )
    with c2:
        dataset_name = st.session_state.get("dataset_name")
        render_metric_card(
            label="Active Dataset",
            value="Loaded" if dataset_name else "None",
            description=dataset_name or "No dataset active",
            status="Session"
        )
    with c3:
        render_metric_card(
            label="Platform Version",
            value=APP_VERSION,
            status="Stable"
        )
        
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Section: Reset Session
    render_section_header(
        title="Workspace State Management",
        subtitle="Clear or reset session state back to default initialization."
    )
    
    if st.button("Reset Session State", key="settings_reset_session_btn"):
        clear_dataset_state()
        st.session_state["current_page"] = "Overview"
        st.session_state["theme"] = "Dark"
        st.success("Session state reset to defaults.")
        st.rerun()


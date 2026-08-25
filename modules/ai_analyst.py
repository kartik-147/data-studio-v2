"""
DATA STUDIO v2 — AI Analyst Module (Premium UI v2 Workspace Landing)
=============================================================================
Professional AI workspace landing state — not a generic placeholder.
Shows the active dataset context, quick analysis actions, and a coming-soon
conversational interface with clear visual framing.
"""
import streamlit as st
from modules.ui_components import (
    render_page_header,
    render_notification,
    render_empty_state,
    get_icon_svg,
)
from modules.config import is_dataset_loaded


def render_ai_analyst_page() -> None:
    """Render the AI Analyst workspace landing state."""
    render_page_header(
        title="AI Analyst",
        subtitle="Natural language data exploration, automated insights, and AI-powered question answering.",
        icon="sparkles",
        badge="Coming Soon"
    )

    dataset_loaded = is_dataset_loaded()

    # ── AI Workspace Hero ──────────────────────────────────────────────────────
    ai_icon = get_icon_svg("sparkles", 28)

    hero_html = (
        f'<div class="ds-ai-workspace">'
        f'<div class="ds-ai-icon-circle">{ai_icon}</div>'
        f'<div class="ds-ai-title">AI Data Analyst</div>'
        f'<div class="ds-ai-subtitle">'
        f'Ask questions about your data in plain English. Get instant answers, '
        f'visualizations, and automated insight narratives — no SQL or code required.'
        f'</div>'
        # Quick action chips
        f'<div class="ds-ai-actions">'
        f'<span class="ds-ai-action-chip">{get_icon_svg("search", 13)} Explain this dataset</span>'
        f'<span class="ds-ai-action-chip">{get_icon_svg("trending-up", 13)} Find key trends</span>'
        f'<span class="ds-ai-action-chip">{get_icon_svg("alert-triangle", 13)} Detect anomalies</span>'
        f'<span class="ds-ai-action-chip">{get_icon_svg("activity", 13)} Show correlations</span>'
        f'<span class="ds-ai-action-chip">{get_icon_svg("bar-chart-3", 13)} Suggest visualizations</span>'
        f'<span class="ds-ai-action-chip">{get_icon_svg("zap", 13)} Auto-summarize data</span>'
        f'</div>'
        f'</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    # ── Dataset Context or Prompt to Upload ───────────────────────────────────
    if not dataset_loaded:
        render_notification(
            title="No dataset loaded",
            message=(
                "Upload a dataset first to enable AI-powered analysis. "
                "The AI Analyst works directly with your active dataset in memory."
            ),
            variant="info"
        )
        col_l, col_c, col_r = st.columns([1, 2, 1])
        with col_c:
            if st.button(
                "Upload a Dataset →",
                key="ai_upload_btn",
                type="primary",
                use_container_width=True
            ):
                st.session_state["current_page"] = "Dataset"
                st.rerun()
    else:
        render_notification(
            title="Dataset Ready for AI Analysis",
            message=(
                f"Dataset '{st.session_state.get('dataset_name', 'dataset')}' is loaded and ready. "
                "The AI interface will be available in the next module release."
            ),
            variant="success"
        )

    # ── Conversational Interface Placeholder ───────────────────────────────────
    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:14px;font-weight:600;color:var(--text-primary);'
        'margin-bottom:10px;letter-spacing:-0.01em;">Conversational Interface</div>',
        unsafe_allow_html=True
    )

    # Mock chat area
    chat_area_html = (
        '<div style="background:var(--surface);border:1.5px dashed var(--border);'
        'border-radius:12px;padding:40px 32px;text-align:center;margin-bottom:14px;">'
        '<div style="font-size:32px;margin-bottom:10px;opacity:0.25;">💬</div>'
        '<div style="font-size:14px;font-weight:600;color:var(--text-muted);margin-bottom:4px;">'
        'Conversational interface in development</div>'
        '<div style="font-size:12.5px;color:var(--text-muted);max-width:360px;margin:0 auto;line-height:1.5;">'
        'Ask natural language questions, get instant data answers and chart suggestions.'
        '</div>'
        '</div>'
    )
    st.markdown(chat_area_html, unsafe_allow_html=True)

    # Disabled input bar (visual mock)
    st.text_input(
        "Ask anything about your data…",
        placeholder="e.g. 'What are the top 5 products by revenue?' or 'Show me the trend over time'",
        disabled=True,
        key="ai_chat_input_mock",
        label_visibility="collapsed"
    )

    # ── What's Coming Section ─────────────────────────────────────────────────
    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:14px;font-weight:600;color:var(--text-primary);'
        'margin-bottom:10px;letter-spacing:-0.01em;">What\'s Coming in Module 9</div>',
        unsafe_allow_html=True
    )

    features = [
        ("sparkles", "Natural Language Queries", "Ask questions in plain English and get instant SQL-powered answers."),
        ("bar-chart-3", "Auto Visualization", "AI selects the most relevant chart type for your question automatically."),
        ("file-text", "Insight Narratives", "Automatically generated written summaries of data trends and anomalies."),
        ("cpu", "Smart Suggestions", "Proactive analysis suggestions based on your dataset's characteristics."),
        ("zap", "Quick Calculations", "Instant aggregations, percentages, rankings, and time-series analysis."),
    ]

    feat_col1, feat_col2 = st.columns(2, gap="medium")
    for i, (icon_name, feat_title, feat_desc) in enumerate(features):
        with (feat_col1 if i % 2 == 0 else feat_col2):
            icon_svg = get_icon_svg(icon_name, 15)
            feat_html = (
                f'<div class="ds-insight-card" style="margin-bottom:8px;">'
                f'<div class="ds-insight-icon ds-insight-icon-info">{icon_svg}</div>'
                f'<div class="ds-insight-body">'
                f'<div class="ds-insight-title">{feat_title}</div>'
                f'<div class="ds-insight-description">{feat_desc}</div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(feat_html, unsafe_allow_html=True)

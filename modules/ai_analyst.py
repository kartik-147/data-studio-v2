"""
DATA STUDIO v2 &mdash; AI Analyst Module (3-Mode Interactive Workspace)
=============================================================================
Three internal analytical modes powered by the existing EDA and quality engines:

  ASK          &mdash; Dataset-aware Q&A with deterministic answers from engine functions.
                 Clearly labeled "Analytics Engine Answer" &mdash; not a hallucinated AI response.
  INVESTIGATE  &mdash; Structured root-cause analysis: pick a metric, pick a dimension,
                 get correlation findings, outlier detection, and ranked explanations.
  DATA STORY   &mdash; Chapter-based narrative generated from real session data:
                 dataset context, quality audit, transformations, key patterns,
                 strongest correlations, and next recommended investigations.

All answers are deterministic and sourced from:
  - compute_summary_statistics     (EDA engine)
  - compute_correlation_matrix     (EDA engine)
  - extract_strongest_correlations (EDA engine)
  - compute_iqr_outliers           (EDA engine)
  - generate_eda_insights          (EDA engine)
  - dataset_metadata               (session state &mdash; built by data_loader)
  - prep_history                   (session state &mdash; built by data_preparation)

Read-only analysis: NEVER mutates the underlying dataset.
"""
from __future__ import annotations
import html
from typing import Optional, Dict, Any, List

import pandas as pd
import streamlit as st

from modules.config import is_dataset_loaded, log_activity
from modules.ui_components import (
    render_page_header,
    render_notification,
    render_empty_state,
    render_section_header,
    render_next_workflow_steps,
    get_icon_svg,
)
from modules.eda_engine import (
    compute_summary_statistics,
    compute_correlation_matrix,
    extract_strongest_correlations,
    compute_iqr_outliers,
    generate_eda_insights,
    generate_distribution_histogram,
    generate_categorical_barchart,
)


# ─────────────────────────────────────────────────────────────────────────────
# SESSION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _init_ai_state() -> None:
    """Ensure all AI Analyst session keys are initialised."""
    if "ai_analyst_mode" not in st.session_state:
        st.session_state["ai_analyst_mode"] = "ask"
    if "ai_ask_question" not in st.session_state:
        st.session_state["ai_ask_question"] = ""
    if "ai_ask_result" not in st.session_state:
        st.session_state["ai_ask_result"] = None
    if "ai_story_cache" not in st.session_state:
        st.session_state["ai_story_cache"] = None
    if "ai_investigate_result" not in st.session_state:
        st.session_state["ai_investigate_result"] = None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def render_ai_analyst_page() -> None:
    """Render the AI Analyst 3-mode interactive workspace."""
    _init_ai_state()

    render_page_header(
        title="AI Analyst",
        subtitle="Ask questions, investigate patterns, and generate a data story &mdash; powered by your dataset's analytical engines.",
        icon="sparkles",
    )

    dataset_loaded = is_dataset_loaded()

    if not dataset_loaded:
        _render_no_dataset_state()
        return

    # ── Mode Switcher ──────────────────────────────────────────────────────────
    _render_mode_switcher()

    mode = st.session_state.get("ai_analyst_mode", "ask")

    # ── Mode Router ────────────────────────────────────────────────────────────
    if mode == "ask":
        _render_ask_mode()
    elif mode == "investigate":
        _render_investigate_mode()
    elif mode == "story":
        _render_story_mode()

    # ── Workflow Navigation ────────────────────────────────────────────────────
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    render_next_workflow_steps("AI Analyst")


# ─────────────────────────────────────────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────────────────────────────────────────

def _render_no_dataset_state() -> None:
    """Empty state shown when no dataset is loaded."""
    render_empty_state(
        title="No dataset loaded for AI analysis",
        description=(
            "Upload a dataset first to enable AI-powered analysis. "
            "The AI Analyst works directly with your active dataset in memory."
        ),
        icon="sparkles",
    )
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        if st.button(
            "Upload a Dataset →",
            key="ai_upload_btn",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["current_page"] = "Dataset"
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# MODE SWITCHER
# ─────────────────────────────────────────────────────────────────────────────

def _render_mode_switcher() -> None:
    """Render three pill-style mode buttons (ASK / INVESTIGATE / DATA STORY)."""
    current_mode = st.session_state.get("ai_analyst_mode", "ask")
    modes = [
        ("ask",        "search",    "ASK"),
        ("investigate","activity",  "INVESTIGATE"),
        ("story",      "file-text", "DATA STORY"),
    ]
    cols = st.columns([2, 2, 2, 6], gap="small")
    for idx, (mode_key, icon_name, label) in enumerate(modes):
        with cols[idx]:
            is_active = current_mode == mode_key
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                f"{label}",
                key=f"ai_mode_{mode_key}",
                type=btn_type,
                use_container_width=True,
            ):
                if st.session_state["ai_analyst_mode"] != mode_key:
                    st.session_state["ai_analyst_mode"] = mode_key
                    # Reset results when switching modes
                    st.session_state["ai_ask_result"] = None
                    st.session_state["ai_investigate_result"] = None
                    st.rerun()

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<hr style='border: none; border-top: 1px solid var(--border); margin: 0 0 20px 0;'>",
        unsafe_allow_html=True,
    )


# =============================================================================
# MODE 1: ASK
# =============================================================================

def _generate_suggested_questions(df: pd.DataFrame) -> List[str]:
    """Build a list of dataset-aware suggested questions from column names and types."""
    questions = []
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if df[c].dtype == object or str(df[c].dtype) == "category"]
    datetime_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

    questions.append(f"How many rows and columns does this dataset have?")
    questions.append(f"What is the overall data quality of this dataset?")

    if numeric_cols:
        col = numeric_cols[0]
        questions.append(f"What is the average value of '{col}'?")
        questions.append(f"Which column has the most outliers?")
        if len(numeric_cols) >= 2:
            questions.append(f"What is the strongest correlation in this dataset?")

    if cat_cols:
        col = cat_cols[0]
        questions.append(f"What are the top values in '{col}'?")
        questions.append(f"How many unique values does '{col}' have?")

    questions.append(f"Which columns have missing values?")
    questions.append(f"Are there duplicate rows in this dataset?")

    if datetime_cols:
        col = datetime_cols[0]
        questions.append(f"What is the date range in '{col}'?")

    return questions[:8]


def _answer_question(q: str, df: pd.DataFrame, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Answer a natural-language question about the dataset using deterministic engine functions.
    Returns a dict with: answer (str), source (str), followups (list[str]), extra (any).
    """
    q_lower = q.lower().strip()
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if df[c].dtype == object or str(df[c].dtype) == "category"]

    # ── Shape / size questions ──
    if any(kw in q_lower for kw in ["how many rows", "how many columns", "shape", "size", "dimension", "rows and columns"]):
        rows, cols = df.shape
        answer = (
            f"This dataset contains **{rows:,} rows** and **{cols} columns**. "
            f"Total data cells: {rows * cols:,}. "
            f"Memory usage: {metadata.get('memory_formatted', 'N/A')}."
        )
        return {
            "answer": answer,
            "source": "Dataset Metadata",
            "followups": ["Which columns have missing values?", "What is the data quality score?", "What types of columns exist?"],
            "extra": None,
        }

    # ── Quality / health ──
    if any(kw in q_lower for kw in ["quality", "health", "score", "completeness", "overall"]):
        qs = metadata.get("quality_score")
        missing_pct = metadata.get("missing_percentage", 0.0)
        dup_pct = metadata.get("duplicate_percentage", 0.0)
        if qs is not None:
            status = "Excellent" if qs >= 90 else ("Good" if qs >= 75 else ("Fair" if qs >= 60 else "Poor"))
            answer = (
                f"The dataset has an overall quality score of **{qs:.1f}%** ({status}). "
                f"Missing values: {missing_pct:.1f}%. Duplicate rows: {dup_pct:.1f}%. "
            )
            if missing_pct > 10:
                answer += "High missing rates detected &mdash; review in Data Quality and clean in Data Preparation."
            elif qs >= 85:
                answer += "Data integrity is high and the dataset is ready for analysis."
        else:
            answer = "Quality score has not been computed yet. Visit the **Data Quality** module to run a full audit."
        return {
            "answer": answer,
            "source": "Dataset Metadata",
            "followups": ["Which columns have missing values?", "Are there duplicate rows?", "Which column has the most outliers?"],
            "extra": None,
        }

    # ── Missing values ──
    if any(kw in q_lower for kw in ["missing", "null", "nan", "empty", "incomplete"]):
        missing = df.isna().sum()
        missing_cols = missing[missing > 0].sort_values(ascending=False)
        if missing_cols.empty:
            answer = "✅ **No missing values** detected in any column. The dataset is 100% complete."
        else:
            top_miss = ", ".join(
                f"**{c}** ({v} missing, {v/len(df)*100:.1f}%)"
                for c, v in missing_cols.head(5).items()
            )
            answer = (
                f"**{len(missing_cols)} column(s)** contain missing values. "
                f"Top affected: {top_miss}."
            )
            if len(missing_cols) > 5:
                answer += f" Plus {len(missing_cols) - 5} more columns."
        return {
            "answer": answer,
            "source": "Missing Value Analysis",
            "followups": ["What is the overall data quality?", "How can I fix missing values?", "Are there duplicate rows?"],
            "extra": None,
        }

    # ── Duplicates ──
    if any(kw in q_lower for kw in ["duplicate", "duplicated", "repeated", "duplicate row"]):
        dup_count = int(df.duplicated().sum())
        dup_pct = dup_count / len(df) * 100 if len(df) > 0 else 0
        if dup_count == 0:
            answer = "✅ **No duplicate rows** found in this dataset."
        else:
            answer = (
                f"**{dup_count:,} duplicate rows** detected ({dup_pct:.1f}% of dataset). "
                f"Duplicates can bias statistical aggregations &mdash; use **Data Preparation → Remove Duplicates** to clean."
            )
        return {
            "answer": answer,
            "source": "Duplicate Analysis",
            "followups": ["What is the overall data quality?", "Which columns have missing values?"],
            "extra": None,
        }

    # ── Average / mean ──
    if any(kw in q_lower for kw in ["average", "mean", "avg"]):
        # Try to match a column name from the question
        matched_col = None
        for col in numeric_cols:
            if col.lower() in q_lower:
                matched_col = col
                break

        if matched_col:
            mean_val = df[matched_col].mean()
            median_val = df[matched_col].median()
            std_val = df[matched_col].std()
            answer = (
                f"For **'{matched_col}'**: Mean = **{mean_val:,.2f}**, "
                f"Median = {median_val:,.2f}, Std Dev = {std_val:,.2f}. "
            )
            skew = df[matched_col].skew()
            if abs(skew) > 0.5:
                direction = "right" if skew > 0 else "left"
                answer += f"The distribution is {direction}-skewed (skewness = {skew:.2f})."
        elif numeric_cols:
            stats_df = compute_summary_statistics(df, numeric_cols[:5])
            if not stats_df.empty:
                lines = [f"**{row['Column']}**: Mean = {row['Mean']:,.2f}" for _, row in stats_df.iterrows()]
                answer = "Summary of means for numeric columns:\n\n" + "\n\n".join(lines)
            else:
                answer = "No numeric columns available for mean calculation."
        else:
            answer = "No numeric columns found in this dataset."
        return {
            "answer": answer,
            "source": "Summary Statistics Engine",
            "followups": ["What is the correlation between columns?", "Which column has the most outliers?"],
            "extra": None,
        }

    # ── Correlation ──
    if any(kw in q_lower for kw in ["correlation", "correlated", "relationship", "strongest"]):
        if len(numeric_cols) < 2:
            answer = "At least 2 numeric columns are required to compute correlations. This dataset has fewer."
        else:
            corr = compute_correlation_matrix(df, numeric_cols)
            pos_pairs, neg_pairs = extract_strongest_correlations(corr, top_n=3)
            lines = []
            for p in pos_pairs[:3]:
                lines.append(
                    f"▲ **{p['Variable 1']}** ↔ **{p['Variable 2']}**: r = {p['Correlation (r)']:.2f} ({p['Strength']})"
                )
            for p in neg_pairs[:2]:
                lines.append(
                    f"▼ **{p['Variable 1']}** ↔ **{p['Variable 2']}**: r = {p['Correlation (r)']:.2f} ({p['Strength']})"
                )
            if lines:
                answer = "**Top correlations in this dataset:**\n\n" + "\n\n".join(lines)
                if pos_pairs and abs(pos_pairs[0]["Correlation (r)"]) >= 0.7:
                    answer += f"\n\nThe strongest relationship is between **{pos_pairs[0]['Variable 1']}** and **{pos_pairs[0]['Variable 2']}** &mdash; worth investigating further."
            else:
                answer = "No significant correlations detected between numeric columns."
        return {
            "answer": answer,
            "source": "Correlation Matrix Engine (Pearson)",
            "followups": ["What are the top 5 values in a category?", "Which column has the most outliers?"],
            "extra": None,
        }

    # ── Outliers ──
    if any(kw in q_lower for kw in ["outlier", "outliers", "anomaly", "anomalies", "extreme"]):
        if not numeric_cols:
            answer = "Outlier analysis requires numeric columns. None were found."
        else:
            outlier_data = compute_iqr_outliers(df, numeric_cols[:6])
            total = outlier_data.get("total_outliers", 0)
            if total == 0:
                answer = "No IQR outliers detected across numeric columns (using 1.5× IQR fence rule)."
            else:
                lines = []
                for col, info in outlier_data.get("outliers_by_column", {}).items():
                    if info["count"] > 0:
                        lines.append(f"• **{col}**: {info['count']:,} outliers ({info['percentage']:.1f}%)")
                answer = f"Found **{total:,} potential outliers** across columns:\n\n" + "\n".join(lines)
        return {
            "answer": answer,
            "source": "Outlier Detection Engine (IQR)",
            "followups": ["What is the strongest correlation?", "What is the average value?"],
            "extra": None,
            "is_llm": False,
        }

    # ── Specific column averages ──
    for col in numeric_cols:
        if col.lower() in q_lower:
            s = df[col].dropna()
            mean_val = s.mean()
            median_val = s.median()
            std_val = s.std()
            min_val = s.min()
            max_val = s.max()
            answer = (
                f"Summary for column **'{col}'**:\n\n"
                f"• **Mean (Average)**: {mean_val:,.2f}\n"
                f"• **Median**: {median_val:,.2f}\n"
                f"• **Standard Deviation**: {std_val:,.2f}\n"
                f"• **Range**: [{min_val:,.2f}, {max_val:,.2f}]\n"
                f"• **Non-null count**: {len(s):,} of {len(df):,}"
            )
            return {
                "answer": answer,
                "source": f"Descriptive Statistics ({col})",
                "followups": [f"What are the outliers in '{col}'?", "What is the strongest correlation?"],
                "extra": None,
                "is_llm": False,
            }

    # ── Specific category top values ──
    for col in cat_cols:
        if col.lower() in q_lower:
            s = df[col].dropna()
            top = s.value_counts().head(5)
            lines = [f"• **{val}**: {cnt:,} ({cnt/len(df)*100:.1f}%)" for val, cnt in top.items()]
            answer = (
                f"Top categories for **'{col}'** ({s.nunique()} unique values total):\n\n"
                + "\n".join(lines)
            )
            return {
                "answer": answer,
                "source": f"Categorical Frequency ({col})",
                "followups": ["What are the missing values?", "What is the overall data quality?"],
                "extra": None,
                "is_llm": False,
            }

    # ── Default automated insights ──
    insights = generate_eda_insights(df, metadata)
    if insights:
        top = insights[:3]
        lines = [f"**{ins['title']}** &mdash; {ins['observation']}" for ins in top if "observation" in ins]
        answer = (
            "Here are the top **automated data observations** for this dataset:\n\n"
            + "\n\n".join(f"• {l}" for l in lines)
        )
    else:
        answer = (
            "I couldn't find a specific match for your question in the rule engine. "
            "Enter an API key in the AI Settings drawer above to enable real LLM comprehension in any language!"
        )
    return {
        "answer": answer,
        "source": "Automated Insights Engine",
        "followups": ["How many rows does this dataset have?", "Which columns have missing values?", "What is the strongest correlation?"],
        "extra": None,
        "is_llm": False,
    }


def _answer_question(q: str, df: pd.DataFrame, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for Q&A: delegates to real LLM (Gemini / OpenAI) with automatic
    fallback to deterministic Analytics Engine.
    """
    from modules.llm_service import ask_ai_analyst
    return ask_ai_analyst(q, df, metadata)


def _render_ask_mode() -> None:
    """Render ASK mode: multilingual generative AI Q&A with model switcher."""
    from modules.llm_service import get_ai_api_key, set_ai_api_key

    df: pd.DataFrame = st.session_state.get("dataset")
    metadata: Dict[str, Any] = st.session_state.get("dataset_metadata") or {}
    dataset_name = st.session_state.get("dataset_name", "dataset")

    render_section_header(
        title="Ask AI Analyst",
        subtitle=f"Ask questions in any language (English, Hindi, Spanish, etc.) grounded in '{dataset_name}'."
    )

    # ── AI Model & API Key Configuration Drawer ────────────────────────────────
    active_key, active_provider = get_ai_api_key()
    is_llm_active = bool(active_key)

    with st.expander(
        f"{'✨ Real Generative AI: Active' if is_llm_active else '⚙️ AI Model & API Key Configuration (Click to enable Gemini/OpenAI)'}",
        expanded=not is_llm_active
    ):
        st.markdown(
            """
            <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 8px;">
                Enter a free <strong>Google Gemini API Key</strong> (or OpenAI Key) to unlock real generative LLM answers in any language (English, हिंदी, Español, Français, etc.) grounded in your dataset.
            </div>
            """,
            unsafe_allow_html=True
        )

        cfg_col1, cfg_col2, cfg_col3 = st.columns([4, 2, 2], gap="small")
        with cfg_col1:
            entered_key = st.text_input(
                "API Key",
                value=active_key or "",
                type="password",
                placeholder="Paste Gemini or OpenAI API Key here...",
                key="ai_analyst_key_input",
                label_visibility="collapsed"
            )
        with cfg_col2:
            selected_provider = st.selectbox(
                "Provider",
                options=["Gemini", "OpenAI"],
                index=0 if active_provider == "gemini" else 1,
                key="ai_analyst_provider_sel",
                label_visibility="collapsed"
            )
        with cfg_col3:
            if st.button("Save Key", key="ai_save_key_btn", type="primary", use_container_width=True):
                if entered_key.strip():
                    set_ai_api_key(entered_key, selected_provider.lower())
                    st.toast(f"Saved {selected_provider} API Key! Real LLM enabled. ✓")
                    st.rerun()
                else:
                    st.session_state["ai_api_key"] = None
                    st.toast("API Key cleared. Using Analytics Engine mode.")
                    st.rerun()

    # Suggested questions
    suggested = _generate_suggested_questions(df)
    st.markdown(
        '<div class="ds-ai-suggested-label">Suggested questions &mdash; click to use or type your own question in any language</div>',
        unsafe_allow_html=True,
    )

    # Render suggested question buttons in a grid
    suggest_cols = st.columns(4, gap="small")
    for i, q in enumerate(suggested):
        with suggest_cols[i % 4]:
            if st.button(q, key=f"ai_suggest_{i}", use_container_width=True):
                st.session_state["ai_ask_question"] = q
                with st.spinner("Analyzing dataset with AI..."):
                    result = _answer_question(q, df, metadata)
                    st.session_state["ai_ask_result"] = result
                log_activity(f"AI Analyst: asked '{q}'", "sparkles")
                st.rerun()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Question input
    question_val = st.session_state.get("ai_ask_question", "")
    user_question = st.text_input(
        "Type your question in any language:",
        value=question_val,
        placeholder="e.g. 'What are the main drivers of sales?' or 'इस डेटासेट में सबसे ज्यादा ट्रेंडिंग केटेगरी कौन सी है?'",
        key="ai_ask_text_input",
        label_visibility="collapsed",
    )

    ask_col1, ask_col2, ask_col3 = st.columns([4, 1, 1], gap="small")
    with ask_col2:
        ask_btn = st.button("Ask", key="ai_ask_submit_btn", type="primary", use_container_width=True)
    with ask_col3:
        clear_btn = st.button("Clear", key="ai_ask_clear_btn", use_container_width=True)

    if clear_btn:
        st.session_state["ai_ask_question"] = ""
        st.session_state["ai_ask_result"] = None
        st.rerun()

    if ask_btn and user_question.strip():
        st.session_state["ai_ask_question"] = user_question
        with st.spinner("AI Analyst is examining dataset and generating answer..."):
            result = _answer_question(user_question, df, metadata)
            st.session_state["ai_ask_result"] = result
        log_activity(f"AI Analyst: asked '{user_question[:60]}'", "sparkles")
        st.rerun()

    # Answer area
    result = st.session_state.get("ai_ask_result")
    if result:
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        is_llm = result.get("is_llm", False)
        source_label = html.escape(result.get("source", "Engine"))
        source_icon = get_icon_svg("sparkles" if is_llm else "cpu", 11)
        source_badge_style = "background: rgba(139, 92, 246, 0.15); color: #8b5cf6; border: 1px solid rgba(139, 92, 246, 0.3);" if is_llm else ""
        source_badge_tag = "GENERATIVE AI LLM" if is_llm else "ANALYTICS ENGINE"
        
        st.markdown(
            f'<div class="ds-ai-answer-card">'
            f'<div style="margin-bottom: 10px;">'
            f'<span class="ds-ai-answer-source" style="{source_badge_style}">'
            f'{source_icon}&nbsp; {source_badge_tag} · {source_label}'
            f'</span>'
            f'</div>'
            f'<div class="ds-ai-answer-text" style="font-size:14px; line-height:1.65;">',
            unsafe_allow_html=True
        )
        st.markdown(result.get("answer", ""))
        st.markdown('</div></div>', unsafe_allow_html=True)

        # Follow-up suggestions
        if result.get("followups"):
            st.markdown(
                '<div class="ds-ai-followup-label">Follow-up questions</div>',
                unsafe_allow_html=True,
            )
            fu_cols = st.columns(len(result["followups"]), gap="small")
            for idx, fq in enumerate(result["followups"]):
                with fu_cols[idx]:
                    if st.button(fq, key=f"ai_followup_{idx}", use_container_width=True):
                        st.session_state["ai_ask_question"] = fq
                        r2 = _answer_question(fq, df, metadata)
                        st.session_state["ai_ask_result"] = r2
                        st.rerun()

        # Deep links
        link_col1, link_col2, _ = st.columns([2, 2, 4], gap="small")
        with link_col1:
            if st.button("Explore in Analyze (EDA) →", key="ai_goto_eda", use_container_width=True):
                st.session_state["current_page"] = "EDA"
                st.rerun()
        with link_col2:
            if st.button("Create a Visualization →", key="ai_goto_viz", use_container_width=True):
                st.session_state["current_page"] = "Visualization"
                st.rerun()


# =============================================================================
# MODE 2: INVESTIGATE
# =============================================================================

def _render_investigate_mode() -> None:
    """Render INVESTIGATE mode: structured root-cause analysis form."""
    df: pd.DataFrame = st.session_state.get("dataset")
    metadata: Dict[str, Any] = st.session_state.get("dataset_metadata") or {}

    render_section_header(
        title="Root Cause Investigation",
        subtitle="Select a target metric and a comparison dimension to identify patterns, outliers, and possible explanations."
    )

    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if df[c].dtype == object or str(df[c].dtype) == "category"]
    datetime_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

    if not numeric_cols:
        render_notification(
            title="No numeric columns available",
            message="INVESTIGATE mode requires at least one numeric column as a target metric.",
            variant="warning"
        )
        return

    # ── Investigation Form ─────────────────────────────────────────────────────
    st.markdown(
        '<div class="ds-investigate-form">',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ds-investigate-section-label">Investigation Setup</div>',
        unsafe_allow_html=True,
    )
    form_c1, form_c2, form_c3 = st.columns(3, gap="medium")

    with form_c1:
        target_metric = st.selectbox(
            "Target metric (what to investigate)",
            options=numeric_cols,
            key="inv_target_metric",
            help="The numeric column you want to understand better.",
        )

    with form_c2:
        dim_options = cat_cols if cat_cols else numeric_cols
        comparison_dim = st.selectbox(
            "Comparison dimension (split by)",
            options=dim_options,
            key="inv_comparison_dim",
            help="The column to group by when comparing the target metric.",
        )

    with form_c3:
        time_options = ["None"] + datetime_cols + [c for c in numeric_cols if "year" in c.lower() or "date" in c.lower()]
        time_col = st.selectbox(
            "Time column (optional)",
            options=time_options,
            key="inv_time_col",
            help="Optional: a date or year column for trend context.",
        )
        time_col = None if time_col == "None" else time_col

    st.markdown("</div>", unsafe_allow_html=True)

    run_col, _, _ = st.columns([2, 4, 4], gap="small")
    with run_col:
        run_btn = st.button(
            "Run Investigation →",
            key="inv_run_btn",
            type="primary",
            use_container_width=True,
        )

    if run_btn:
        with st.spinner("Running investigation..."):
            result = _run_investigation(df, target_metric, comparison_dim, time_col)
        st.session_state["ai_investigate_result"] = result
        log_activity(f"AI Analyst: investigated '{target_metric}' by '{comparison_dim}'", "activity")
        st.rerun()

    # ── Results ────────────────────────────────────────────────────────────────
    result = st.session_state.get("ai_investigate_result")
    if result and result.get("target") == target_metric and result.get("dimension") == comparison_dim:
        _render_investigation_results(result, df, metadata)
    elif result and (result.get("target") != target_metric or result.get("dimension") != comparison_dim):
        st.info("Configuration changed. Click **Run Investigation →** to update results.")


def _run_investigation(
    df: pd.DataFrame,
    target: str,
    dimension: str,
    time_col: Optional[str],
) -> Dict[str, Any]:
    """Compute all investigation findings deterministically from engine functions."""
    result: Dict[str, Any] = {
        "target": target,
        "dimension": dimension,
        "time_col": time_col,
    }

    # 1. Basic stats for target
    s = df[target].dropna()
    result["target_mean"] = float(s.mean()) if len(s) > 0 else None
    result["target_std"] = float(s.std()) if len(s) > 1 else None
    result["target_min"] = float(s.min()) if len(s) > 0 else None
    result["target_max"] = float(s.max()) if len(s) > 0 else None
    result["target_missing"] = int(df[target].isna().sum())

    # 2. Group by dimension &mdash; mean of target per category
    try:
        if df[dimension].dtype == object or str(df[dimension].dtype) == "category":
            grouped = df.groupby(dimension)[target].agg(["mean", "count", "std"]).reset_index()
            grouped.columns = ["Category", "Mean", "Count", "Std"]
            grouped = grouped.sort_values("Mean", ascending=False)
            result["group_df"] = grouped.head(15)
        else:
            # numeric dimension: bin it
            df_tmp = df.copy()
            df_tmp["_bin"] = pd.cut(df_tmp[dimension], bins=min(10, df_tmp[dimension].nunique()), precision=1)
            grouped = df_tmp.groupby("_bin")[target].agg(["mean", "count"]).reset_index()
            grouped.columns = ["Category", "Mean", "Count"]
            grouped = grouped.sort_values("Mean", ascending=False)
            result["group_df"] = grouped.head(10)
    except Exception:
        result["group_df"] = None

    # 3. Correlation &mdash; target vs all other numeric cols
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(numeric_cols) >= 2:
        corr_matrix = compute_correlation_matrix(df, numeric_cols)
        if not corr_matrix.empty and target in corr_matrix.columns:
            target_corrs = corr_matrix[target].drop(target).sort_values(key=abs, ascending=False)
            result["top_correlators"] = [
                {"col": c, "r": float(v)} for c, v in target_corrs.head(4).items()
            ]
        else:
            result["top_correlators"] = []
    else:
        result["top_correlators"] = []

    # 4. Outliers for target column only
    outlier_data = compute_iqr_outliers(df, [target])
    col_outliers = outlier_data.get("column_outliers", {}).get(target, {})
    result["outlier_count"] = col_outliers.get("outlier_count", 0)
    result["outlier_pct"] = col_outliers.get("outlier_pct", 0.0)
    result["outlier_bounds"] = (
        col_outliers.get("lower_bound"), col_outliers.get("upper_bound")
    ) if col_outliers else (None, None)

    # 5. Confidence score based on strength of grouped difference
    confidence = "Low"
    group_df = result.get("group_df")
    if group_df is not None and len(group_df) > 1:
        try:
            std_of_means = float(group_df["Mean"].std())
            overall_std = result.get("target_std") or 1.0
            cv = std_of_means / overall_std if overall_std > 0 else 0
            if cv > 0.5:
                confidence = "High"
            elif cv > 0.2:
                confidence = "Medium"
        except Exception:
            confidence = "Low"
    result["confidence"] = confidence

    # 6. Possible explanations (deterministic rule-based)
    explanations = []
    if result.get("outlier_pct", 0) > 5:
        explanations.append(f"High outlier rate ({result['outlier_pct']:.1f}%) in '{target}' may be inflating or suppressing averages.")
    if result.get("top_correlators"):
        top = result["top_correlators"][0]
        if abs(top["r"]) >= 0.5:
            direction = "positively" if top["r"] > 0 else "negatively"
            explanations.append(f"'{target}' is {direction} correlated with '{top['col']}' (r = {top['r']:.2f}), which may be a key driver.")
    if result.get("target_missing", 0) > 0:
        explanations.append(f"{result['target_missing']:,} missing values in '{target}' &mdash; results may be biased toward observed subsets.")
    if not explanations:
        explanations.append(f"No strong drivers identified. Variation in '{target}' appears distributed across categories.")

    result["explanations"] = explanations
    return result


def _render_investigation_results(result: Dict[str, Any], df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Render the investigation findings in structured sections."""
    target = result["target"]
    dimension = result["dimension"]
    confidence = result.get("confidence", "Low")
    conf_class = f"ds-confidence-{confidence.lower()}"

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # ── Problem Statement ──────────────────────────────────────────────────────
    conf_badge = (
        f'<span class="ds-confidence-badge {conf_class}">'
        f'Confidence: {confidence}'
        f'</span>'
    )
    st.markdown(
        f'<div class="ds-investigate-finding">'
        f'<div class="ds-investigate-section-label">Investigation Summary</div>'
        f'<div style="font-size:15px; font-weight:700; color:var(--text-primary); margin-bottom:6px;">'
        f'How does <em>{html.escape(target)}</em> vary across <em>{html.escape(dimension)}</em>?'
        f'</div>'
        f'<div style="font-size:13px; color:var(--text-secondary); margin-bottom:10px;">'
        f'Mean = {result.get("target_mean", 0):,.2f} &nbsp;|&nbsp; '
        f'Std Dev = {result.get("target_std", 0):,.2f} &nbsp;|&nbsp; '
        f'Range [{result.get("target_min", 0):,.2f} – {result.get("target_max", 0):,.2f}]'
        f'</div>'
        f'{conf_badge}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Group Comparison ───────────────────────────────────────────────────────
    group_df = result.get("group_df")
    if group_df is not None and not group_df.empty:
        st.markdown(
            f'<div class="ds-investigate-section-label" style="margin-top:16px;">'
            f"&lsquo;{html.escape(target)}&rsquo; by Category &mdash; Top Groups (by mean)"
            f'</div>',
            unsafe_allow_html=True,
        )
        current_theme = st.session_state.get("theme", "Light")
        try:
            chart = generate_categorical_barchart(
                df=df,
                cat_col=dimension,
                num_col=target,
                agg="mean",
                top_n=12,
                sort_desc=True,
                theme=current_theme,
                title=f"Average {target} by {dimension}",
            )
            st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})
        except Exception:
            # Fallback: plain table
            st.dataframe(group_df.head(10), use_container_width=True)

    # ── Correlations ───────────────────────────────────────────────────────────
    top_corrs = result.get("top_correlators", [])
    if top_corrs:
        corr_lines = []
        for item in top_corrs:
            dir_arrow = "▲" if item["r"] > 0 else "▼"
            strength = "strong" if abs(item["r"]) >= 0.7 else ("moderate" if abs(item["r"]) >= 0.4 else "weak")
            corr_lines.append(
                f'<div class="ds-story-finding-item">'
                f'<span class="ds-story-finding-bullet">{dir_arrow}</span>'
                f'<span><strong>{html.escape(item["col"])}</strong>: r = {item["r"]:.2f} ({strength})</span>'
                f'</div>'
            )
        st.markdown(
            f'<div class="ds-investigate-finding">'
            f'<div class="ds-investigate-section-label">Correlated Variables</div>'
            f'{"".join(corr_lines)}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Outlier Summary ────────────────────────────────────────────────────────
    out_count = result.get("outlier_count", 0)
    bounds = result.get("outlier_bounds", (None, None))
    out_label = f"{out_count:,} outliers ({result.get('outlier_pct', 0):.1f}%)"
    out_status = "None detected ✅" if out_count == 0 else out_label
    bounds_str = ""
    if bounds[0] is not None and bounds[1] is not None:
        bounds_str = f" &mdash; IQR bounds: [{bounds[0]:,.2f}, {bounds[1]:,.2f}]"
    target_escaped = html.escape(target)
    st.markdown(
        f'<div class="ds-investigate-finding">'
        f"<div class=\"ds-investigate-section-label\">Outlier Profile for '{target_escaped}'</div>"
        f'<div style="font-size:14px; color:var(--text-primary);">{out_status}{bounds_str}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Explanations ───────────────────────────────────────────────────────────
    explanations = result.get("explanations", [])
    if explanations:
        exp_lines = "".join(
            f'<div class="ds-story-finding-item">'
            f'<span class="ds-story-finding-bullet">→</span>'
            f'<span>{html.escape(e)}</span>'
            f'</div>'
            for e in explanations
        )
        st.markdown(
            f'<div class="ds-investigate-finding">'
            f'<div class="ds-investigate-section-label">Possible Explanations</div>'
            f'{exp_lines}'
            f'<div style="font-size:11px; color:var(--text-muted); margin-top:10px;">'
            f'These explanations are deterministic &mdash; sourced from statistical evidence, not inferred by an AI model.'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Deep links ─────────────────────────────────────────────────────────────
    dl_col1, dl_col2, _ = st.columns([2, 2, 4], gap="small")
    with dl_col1:
        if st.button("Deep Dive in Analyze (EDA) →", key="inv_goto_eda", use_container_width=True):
            st.session_state["current_page"] = "EDA"
            st.rerun()
    with dl_col2:
        if st.button("Visualize this relationship →", key="inv_goto_viz", use_container_width=True):
            st.session_state["current_page"] = "Visualization"
            st.rerun()


# =============================================================================
# MODE 3: DATA STORY
# =============================================================================

def _build_data_story(df: pd.DataFrame, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate a chapter-based data story from real session state and engine outputs.
    Returns a list of chapter dicts: {num, title, content_lines, note}.
    """
    chapters = []
    dataset_name = st.session_state.get("dataset_name", "dataset")
    file_type = st.session_state.get("dataset_file_type", "CSV")

    # ── Chapter 1: Dataset Context ────────────────────────────────────────────
    rows = metadata.get("total_rows", len(df))
    cols_count = metadata.get("total_columns", len(df.columns))
    memory = metadata.get("memory_formatted", "N/A")
    numeric_count = sum(1 for c in df.columns if pd.api.types.is_numeric_dtype(df[c]))
    cat_count = len(df.columns) - numeric_count
    chapters.append({
        "num": "Chapter 1",
        "title": "Dataset Context",
        "lines": [
            f"Dataset: <strong>{html.escape(dataset_name)}</strong> ({file_type.upper()})",
            f"Dimensions: <strong>{rows:,} rows × {cols_count} columns</strong>",
            f"Memory footprint: <strong>{memory}</strong>",
            f"Column breakdown: <strong>{numeric_count} numeric</strong> + <strong>{cat_count} categorical / other</strong>",
        ],
        "note": None,
    })

    # ── Chapter 2: Data Health ────────────────────────────────────────────────
    quality_score = metadata.get("quality_score")
    missing_pct = metadata.get("missing_percentage", 0.0) or 0.0
    dup_pct = metadata.get("duplicate_percentage", 0.0) or 0.0
    health_lines = []
    if quality_score is not None:
        status = "Excellent" if quality_score >= 90 else ("Good" if quality_score >= 75 else ("Fair" if quality_score >= 60 else "Poor &mdash; needs attention"))
        health_lines.append(f"Overall quality score: <strong>{quality_score:.1f}% ({status})</strong>")
    health_lines.append(f"Missing values: <strong>{missing_pct:.1f}%</strong> of all data cells")
    health_lines.append(f"Duplicate rows: <strong>{dup_pct:.1f}%</strong> of total rows")
    if missing_pct > 20:
        health_lines.append("⚠ High missing rate &mdash; consider imputing or dropping incomplete columns.")
    if dup_pct > 5:
        health_lines.append("⚠ Significant duplicates &mdash; deduplication recommended before analysis.")
    chapters.append({
        "num": "Chapter 2",
        "title": "Data Health Assessment",
        "lines": health_lines,
        "note": "Quality score sourced from the Data Quality module audit." if quality_score else "Visit Data Quality to compute the full health audit.",
    })

    # ── Chapter 3: Transformations Applied ───────────────────────────────────
    prep_history = st.session_state.get("prep_history", [])
    if prep_history:
        transform_lines = [f"<strong>{len(prep_history)} transformation(s)</strong> applied via Data Preparation:"]
        for step in prep_history[-6:]:
            step_str = step if isinstance(step, str) else str(step.get("description", step))
            transform_lines.append(f"• {html.escape(step_str[:120])}")
        note = "Working copy reflects all applied transformations. Original dataset preserved."
    else:
        transform_lines = ["No transformations recorded. The dataset is in its original uploaded state."]
        note = "Visit Data Preparation to clean, impute, filter, or cast columns."
    chapters.append({
        "num": "Chapter 3",
        "title": "Data Preparation History",
        "lines": transform_lines,
        "note": note,
    })

    # ── Chapter 4: Major Patterns ─────────────────────────────────────────────
    insights = generate_eda_insights(df, metadata)
    if insights:
        pattern_lines = [f"Top <strong>{min(len(insights), 5)} automated data observations</strong>:"]
        for ins in insights[:5]:
            pattern_lines.append(f"• <strong>{html.escape(ins.get('severity', 'OBSERVATION'))}</strong> &mdash; {html.escape(ins.get('title', ''))}")
    else:
        pattern_lines = ["No major pattern anomalies detected. Dataset appears statistically well-distributed."]
    chapters.append({
        "num": "Chapter 4",
        "title": "Key Data Patterns",
        "lines": pattern_lines,
        "note": "Observations generated by rule-based statistical analysis &mdash; not AI-generated text.",
    })

    # ── Chapter 5: Strongest Relationships ────────────────────────────────────
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(numeric_cols) >= 2:
        corr_matrix = compute_correlation_matrix(df, numeric_cols)
        pos_pairs, neg_pairs = extract_strongest_correlations(corr_matrix, top_n=3)
        rel_lines = []
        all_pairs = pos_pairs[:3] + neg_pairs[:2]
        if all_pairs:
            rel_lines.append(f"<strong>{len(all_pairs)} notable correlations</strong> detected:")
            for p in all_pairs:
                direction = "▲ Positive" if p["Correlation (r)"] > 0 else "▼ Negative"
                rel_lines.append(
                    f"• {direction}: <strong>'{html.escape(p['Variable 1'])}'</strong> ↔ "
                    f"<strong>'{html.escape(p['Variable 2'])}'</strong> "
                    f"(r = {p['Correlation (r)']:.2f}, {html.escape(p['Strength'])})"
                )
        else:
            rel_lines = ["No strong correlations detected between numeric columns."]
    else:
        rel_lines = ["Fewer than 2 numeric columns &mdash; correlation analysis not applicable."]
    chapters.append({
        "num": "Chapter 5",
        "title": "Key Relationships",
        "lines": rel_lines,
        "note": "Computed using Pearson correlation coefficient (r).",
    })

    # ── Chapter 6: Outlier Summary ────────────────────────────────────────────
    if numeric_cols:
        outlier_report = compute_iqr_outliers(df, numeric_cols[:8])  # limit for speed
        total_out = outlier_report.get("total_outliers", 0)
        affected = outlier_report.get("affected_columns_count", 0)
        rate = outlier_report.get("overall_outlier_rate", 0.0)
        if total_out == 0:
            out_lines = ["✅ No outliers detected across any numeric column (IQR method)."]
        else:
            out_lines = [
                f"<strong>{total_out:,} outlier data points</strong> across <strong>{affected} column(s)</strong> ({rate:.1f}% overall rate)."
            ]
            col_outs = outlier_report.get("column_outliers", {})
            sorted_cols = sorted(col_outs.items(), key=lambda x: x[1]["outlier_count"], reverse=True)
            for c, cd in sorted_cols[:4]:
                if cd["outlier_count"] > 0:
                    out_lines.append(f"• <strong>'{html.escape(c)}'</strong>: {cd['outlier_count']} outliers ({cd['outlier_pct']:.1f}%)")
    else:
        out_lines = ["No numeric columns available for outlier analysis."]
    chapters.append({
        "num": "Chapter 6",
        "title": "Outlier Landscape",
        "lines": out_lines,
        "note": "IQR method: outliers fall outside [Q1 − 1.5×IQR, Q3 + 1.5×IQR].",
    })

    # ── Chapter 7: Recommended Next Investigations ─────────────────────────────
    rec_lines = []
    if insights and any(i.get("category") == "Missing Data" for i in insights):
        rec_lines.append("Investigate which groups are most affected by missing values.")
    if pos_pairs if len(numeric_cols) >= 2 else False:
        top_pair = pos_pairs[0] if pos_pairs else None
        if top_pair and abs(top_pair["Correlation (r)"]) >= 0.6:
            rec_lines.append(f"Investigate the relationship between '{top_pair['Variable 1']}' and '{top_pair['Variable 2']}' &mdash; high correlation suggests a potential causal link.")
    if total_out > 0 if numeric_cols else False:
        rec_lines.append("Investigate the outlier rows for data entry errors or genuine extreme events.")
    if not rec_lines:
        rec_lines = [
            "Explore column distributions in Analyze (EDA).",
            "Build visualizations to communicate findings.",
            "Generate an executive dashboard for stakeholder sharing.",
        ]
    chapters.append({
        "num": "Chapter 7",
        "title": "Recommended Next Investigations",
        "lines": rec_lines,
        "note": None,
    })

    return chapters


def _render_story_mode() -> None:
    """Render DATA STORY mode: chapter-based narrative from real session data."""
    df: pd.DataFrame = st.session_state.get("dataset")
    metadata: Dict[str, Any] = st.session_state.get("dataset_metadata") or {}
    dataset_name = st.session_state.get("dataset_name", "dataset")

    render_section_header(
        title="Data Story",
        subtitle=f"A chapter-based narrative generated from real analysis of '{dataset_name}'."
    )

    # Source badge
    st.markdown(
        '<div style="margin-bottom:16px;">'
        '<span class="ds-ai-answer-source">'
        + get_icon_svg("cpu", 11)
        + '&nbsp; ALL CONTENT SOURCED FROM ANALYTICS ENGINES &mdash; NOT AI-GENERATED TEXT'
        '</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Generate / Regenerate button
    gen_col, _, _ = st.columns([2, 4, 4], gap="small")
    with gen_col:
        gen_btn = st.button(
            "Generate Story →",
            key="story_generate_btn",
            type="primary",
            use_container_width=True,
        )

    if gen_btn:
        with st.spinner("Generating your data story from analysis results..."):
            chapters = _build_data_story(df, metadata)
        st.session_state["ai_story_cache"] = chapters
        log_activity(f"AI Analyst: generated Data Story for '{dataset_name}'", "file-text")
        st.rerun()

    story = st.session_state.get("ai_story_cache")

    if not story:
        st.markdown(
            '<div class="ds-story-not-ready">'
            '<div style="font-size:28px; margin-bottom:10px; opacity:0.3;">📖</div>'
            '<div style="font-size:15px; font-weight:600; color:var(--text-secondary); margin-bottom:4px;">Story not yet generated</div>'
            '<div style="font-size:13px;">Click <strong>Generate Story →</strong> above to build a chapter-based narrative '
            'from your dataset\'s quality audit, transformation history, key patterns, and correlations.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Render Chapters ────────────────────────────────────────────────────────
    for chapter in story:
        with st.expander(
            f"**{chapter['num']}** &mdash; {chapter['title']}",
            expanded=(chapter["num"] in ["Chapter 1", "Chapter 4", "Chapter 5", "Chapter 7"]),
        ):
            for line in chapter["lines"]:
                st.markdown(
                    f'<div class="ds-story-finding-item">'
                    f'<span class="ds-story-finding-bullet">›</span>'
                    f'<span class="ds-story-chapter-content">{line}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            if chapter.get("note"):
                st.markdown(
                    f'<div style="font-size:11px; color:var(--text-muted); margin-top:10px; '
                    f'padding-top:8px; border-top:1px solid var(--border);">'
                    f'📎 {html.escape(chapter["note"])}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Deep Links ─────────────────────────────────────────────────────────────
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    dl1, dl2, dl3, _ = st.columns([2, 2, 2, 2], gap="small")
    with dl1:
        if st.button("Explore in Analyze →", key="story_goto_eda", use_container_width=True):
            st.session_state["current_page"] = "EDA"
            st.rerun()
    with dl2:
        if st.button("Open Visualize →", key="story_goto_viz", use_container_width=True):
            st.session_state["current_page"] = "Visualization"
            st.rerun()
    with dl3:
        if st.button("Open Dashboard →", key="story_goto_dash", use_container_width=True):
            st.session_state["current_page"] = "Dashboard"
            st.rerun()

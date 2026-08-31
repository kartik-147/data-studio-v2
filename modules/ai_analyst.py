"""
DATA STUDIO v2 — AI Analyst Module (Interactive Workspace)
=============================================================================
Three analytical modes delivering automated intelligence:
  1. AI DATA CHAT & Q&A: Natural language Q&A supporting free-form inquiries
     in any language (via Google Gemini / OpenAI) with intelligent fallback
     to a built-in mathematical Natural Language & Statistical Query Engine.
  2. ROOT-CAUSE INVESTIGATION: Structured driver analysis (target metric vs
     dimension) with grouped distributions, correlation factors, and confidence scoring.
  3. EXECUTIVE DATA STORY: 7-chapter automated briefing generated directly
     from active session metrics, quality audit, and EDA patterns.
"""
from __future__ import annotations
import html
import re
import textwrap
from typing import Optional, Dict, Any, List

import pandas as pd
import streamlit as st

from modules.config import is_dataset_loaded, log_activity, mark_workflow_step
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
    generate_categorical_barchart,
)
from modules.auth import get_current_user
from modules.firebase_service import is_admin_user
from modules.data_loader import (
    get_available_sample_datasets,
    load_sample_dataset_by_key,
    set_active_dataset
)
from modules.llm_service import (
    ask_ai_analyst,
    get_ai_api_key,
    set_ai_api_key,
    test_ai_connection,
)


# ─────────────────────────────────────────────────────────────────────────────
# SESSION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _init_ai_state() -> None:
    """Ensure all AI Analyst session keys are initialised."""
    if "ai_chat_history" not in st.session_state:
        st.session_state["ai_chat_history"] = []
    if "ai_ask_input" not in st.session_state:
        st.session_state["ai_ask_input"] = ""
    if "ai_story_cache" not in st.session_state:
        st.session_state["ai_story_cache"] = None
    if "ai_investigate_result" not in st.session_state:
        st.session_state["ai_investigate_result"] = None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def render_ai_analyst_page() -> None:
    """Render the AI Analyst interactive workspace."""
    _init_ai_state()
    mark_workflow_step("ai_analyst", True)

    render_page_header(
        title="AI Analyst",
        subtitle="Ask questions in natural language, perform root-cause investigations, and generate automated data stories.",
        icon="sparkles",
    )

    if not is_dataset_loaded():
        _render_no_dataset_state(module_name="AI Analyst", key_prefix="ai")
        return

    df: pd.DataFrame = st.session_state.get("dataset")
    metadata: Dict[str, Any] = st.session_state.get("dataset_metadata") or {}
    dataset_name = st.session_state.get("dataset_name", "dataset.csv")
    file_type = st.session_state.get("dataset_file_type", "CSV")

    # ── Top Context Action Bar ───────────────────────────────────────────────
    _render_ai_context_bar(df, dataset_name, file_type, metadata)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # ── 3 Main Analytical Tabs ───────────────────────────────────────────────
    tab_chat, tab_investigate, tab_story = st.tabs([
        "AI DATA CHAT & Q&A",
        "ROOT-CAUSE INVESTIGATION",
        "EXECUTIVE DATA STORY"
    ])

    with tab_chat:
        _render_chat_tab(df, metadata, dataset_name)

    with tab_investigate:
        _render_investigate_tab(df, metadata)

    with tab_story:
        _render_story_tab(df, metadata, dataset_name)

    # ── Standardized Bottom Workflow Steps ───────────────────────────────────
    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    render_next_workflow_steps("AI Analyst")


def render_data_story_page() -> None:
    """Render the Executive Data Story mode directly from the primary navigation."""
    render_page_header(
        title="Data Story",
        subtitle="Transform complex analytics into an automated, executive-ready narrative briefing.",
        icon="book-open"
    )

    if not is_dataset_loaded():
        _render_no_dataset_state(module_name="Data Story", key_prefix="story")
        return

    df: pd.DataFrame = st.session_state.get("dataset")
    metadata: Dict[str, Any] = st.session_state.get("dataset_metadata") or {}
    dataset_name = st.session_state.get("dataset_name", "dataset.csv")
    file_type = st.session_state.get("dataset_file_type", "CSV")

    # Top Context Action Bar
    _render_ai_context_bar(df, dataset_name, file_type, metadata)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    _render_story_tab(df, metadata, dataset_name)

    # Standardized Bottom Workflow Steps
    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    render_next_workflow_steps("Data Story")


# ─────────────────────────────────────────────────────────────────────────────
# CONTEXT BAR & AI CONFIG DRAWER
# ─────────────────────────────────────────────────────────────────────────────

def _render_ai_context_bar(
    df: pd.DataFrame,
    dataset_name: str,
    file_type: str,
    metadata: Dict[str, Any]
) -> None:
    """Render compact context bar with active AI engine indicator and config popover."""
    user = get_current_user()
    is_admin = is_admin_user(user)

    col_info, col_actions = st.columns([7, 5] if is_admin else [9, 3])

    api_key, provider = get_ai_api_key()
    has_llm = bool(api_key)

    total_rows = metadata.get("total_rows", len(df))
    total_cols = metadata.get("total_columns", len(df.columns))

    with col_info:
        engine_label = f"✨ {provider.capitalize()} LLM Active" if has_llm else "⚡ Analytics Engine Active"
        badge_cls = "ds-badge-numeric" if has_llm else "ds-badge-neutral"
        banner_html = (
            f'<div class="ds-active-banner" style="margin-bottom: 8px; padding: 10px 16px;">'
            f'<div class="ds-active-banner-left">'
            f'<div class="ds-brand-badge" style="background: var(--accent);">AI</div>'
            f'<div>'
            f'<div class="ds-active-banner-name" style="font-size: 15px;">{html.escape(dataset_name)}</div>'
            f'<div class="ds-active-banner-meta" style="font-size: 12px;">'
            f'{total_rows:,} rows · {total_cols} cols · '
            f'<span class="ds-badge {badge_cls}" style="font-size: 11px;">{engine_label}</span>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(banner_html, unsafe_allow_html=True)

    with col_actions:
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        if is_admin:
            ac1, ac2 = st.columns([6, 6])
            with ac1:
                with st.popover("⚙️ AI Configuration", use_container_width=True):
                    st.markdown("<div style='font-weight: 600; font-size: 13.5px; margin-bottom: 2px;'>Generative AI Settings</div>", unsafe_allow_html=True)
                    st.caption("Connect Google Gemini (free at aistudio.google.com) or OpenAI to unlock open-ended conversational intelligence.")

                    cur_key, cur_prov = get_ai_api_key()

                    if cur_key:
                        st.markdown(
                            f"<div style='background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 6px; padding: 6px 10px; font-size: 12px; color: #10b981; margin-bottom: 10px;'>"
                            f"✨ <strong>{cur_prov.capitalize()} LLM Active</strong>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            "<div style='background: rgba(100, 116, 139, 0.1); border: 1px solid rgba(100, 116, 139, 0.2); border-radius: 6px; padding: 6px 10px; font-size: 12px; color: var(--text-secondary); margin-bottom: 10px;'>"
                            "⚡ <strong>Offline Analytics Engine Active</strong>"
                            "</div>",
                            unsafe_allow_html=True
                        )

                    input_key = st.text_input(
                        "API Key",
                        value="",
                        type="password",
                        placeholder="•••••••• (Key Active)" if cur_key else "Paste Gemini (AIzaSy...) or OpenAI Key...",
                        key="pop_ai_key_input",
                        help="Keys are stored securely in session memory only."
                    )
                    sel_prov = st.selectbox(
                        "Provider",
                        options=["Gemini", "OpenAI"],
                        index=0 if cur_prov == "gemini" else 1,
                        key="pop_ai_provider_sel"
                    )

                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if st.button("Save Key", key="pop_save_key_btn", type="primary", use_container_width=True):
                            if input_key.strip():
                                set_ai_api_key(input_key.strip(), sel_prov.lower())
                                st.toast(f"{sel_prov} API Key saved successfully!")
                                st.rerun()
                            else:
                                st.toast("Please enter an API key to save.")
                    with btn_c2:
                        if st.button("Test Key", key="pop_test_key_btn", use_container_width=True):
                            test_k = input_key.strip() or cur_key or ""
                            if not test_k:
                                st.warning("Please enter or save an API key to test.")
                            else:
                                with st.spinner("Testing API connection..."):
                                    ok, msg = test_ai_connection(test_k, sel_prov.lower())
                                    if ok:
                                        st.success(msg)
                                    else:
                                        st.error(msg)

                    if cur_key:
                        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                        if st.button("Remove Key (Use Offline Engine)", key="pop_clear_key_btn", use_container_width=True):
                            set_ai_api_key(None, "gemini")
                            st.toast("Switched to built-in Analytics Engine.")
                            st.rerun()
            with ac2:
                if st.button("Clear Chat History", key="ctx_clear_chat_btn", use_container_width=True):
                    st.session_state["ai_chat_history"] = []
                    st.session_state["ai_ask_input"] = ""
                    st.toast("Chat history cleared.")
                    st.rerun()
        else:
            if st.button("Clear Chat History", key="ctx_clear_chat_btn", use_container_width=True):
                st.session_state["ai_chat_history"] = []
                st.session_state["ai_ask_input"] = ""
                st.toast("Chat history cleared.")
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: AI DATA CHAT & Q&A
# ─────────────────────────────────────────────────────────────────────────────

def _generate_suggested_questions(df: pd.DataFrame) -> List[str]:
    """Build a list of dataset-aware suggested questions from active columns."""
    questions = []
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]

    questions.append("Summarize this dataset and its key metrics")
    questions.append("What are the columns and their data types?")

    if numeric_cols:
        col = numeric_cols[0]
        questions.append(f"What is the average value of '{col}'?")
        questions.append(f"Which record has the highest '{col}'?")
        if len(numeric_cols) >= 2:
            questions.append("What are the strongest correlations in this dataset?")

    if cat_cols:
        col = cat_cols[0]
        questions.append(f"What are the top categories in '{col}'?")
        if numeric_cols:
            questions.append(f"Breakdown of '{numeric_cols[0]}' by '{col}'")

    questions.append("Which columns have missing values or anomalies?")
    return questions[:6]


def _render_chat_tab(df: pd.DataFrame, metadata: Dict[str, Any], dataset_name: str) -> None:
    """Render interactive multi-turn AI Data Chat interface."""
    # ── Suggested Questions Carousel / Grid ──────────────────────────────────
    suggested = _generate_suggested_questions(df)
    st.markdown(
        "<div style='font-size: 12.5px; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px;'>"
        "💡 Quick Questions (Click to Ask):"
        "</div>",
        unsafe_allow_html=True
    )

    sug_cols = st.columns(3, gap="small")
    for idx, q_text in enumerate(suggested):
        with sug_cols[idx % 3]:
            if st.button(q_text, key=f"sug_q_btn_{idx}", use_container_width=True):
                _execute_ai_query(q_text, df, metadata)
                st.rerun()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # ── Chat Input Form ──────────────────────────────────────────────────────
    with st.form(key="ai_chat_query_form", clear_on_submit=False):
        f_col1, f_col2 = st.columns([9, 2], gap="small")
        with f_col1:
            user_input = st.text_input(
                "Ask a question about your dataset:",
                value=st.session_state.get("ai_ask_input", ""),
                placeholder="Ask in any language: e.g., 'What are the main drivers of sales?' or 'Highest income by gender'...",
                label_visibility="collapsed",
                key="ai_form_input_field"
            )
        with f_col2:
            submit_btn = st.form_submit_button("Ask Analyst", type="primary", use_container_width=True)

        if submit_btn and user_input and user_input.strip():
            _execute_ai_query(user_input.strip(), df, metadata)
            st.session_state["ai_ask_input"] = ""
            st.rerun()

    # ── Chat History Thread ──────────────────────────────────────────────────
    history = st.session_state.get("ai_chat_history", [])

    if not history:
        st.markdown(
            """
            <div style="background: var(--surface-container); border: 1px dashed var(--border); border-radius: 8px; padding: 24px; text-align: center; margin-top: 16px;">
                <div style="font-size: 28px; margin-bottom: 8px; opacity: 0.5;">💬</div>
                <div style="font-weight: 600; color: var(--text-primary); font-size: 15px; margin-bottom: 4px;">Start a Conversation with Your Data</div>
                <div style="font-size: 13px; color: var(--text-secondary); max-width: 540px; margin: 0 auto;">
                    Ask free-form analytical questions above, or click any suggested prompt to inspect patterns, calculations, and data breakdowns.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Render turns in reverse chronological order (newest on top)
    for t_idx, turn in enumerate(reversed(history)):
        q = turn.get("question", "")
        ans = turn.get("answer", "")
        source = turn.get("source", "Analytics Engine")
        is_llm = turn.get("is_llm", False)
        table_df = turn.get("table")
        followups = turn.get("followups", [])

        # User Question Bubble
        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-end; margin-top: 12px; margin-bottom: 8px;">
                <div style="background: var(--surface-container-high); border: 1px solid var(--border); border-radius: 12px 12px 2px 12px; padding: 8px 14px; max-width: 80%;">
                    <div style="font-size: 10.5px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px;">YOU</div>
                    <div style="font-size: 13.5px; color: var(--text-primary); font-weight: 500;">{html.escape(q)}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # AI Answer Card in Container
        source_badge_style = "background: rgba(139, 92, 246, 0.12); color: #8b5cf6; border: 1px solid rgba(139, 92, 246, 0.25);" if is_llm else "background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.25);"
        source_badge_tag = "GENERATIVE AI LLM" if is_llm else "ANALYTICS ENGINE"
        source_icon = get_icon_svg("sparkles" if is_llm else "cpu", 11)

        with st.container(border=True):
            st.markdown(
                f"""
                <div style="margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
                    <span style="{source_badge_style} display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 5px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px;">
                        {source_icon}&nbsp; {source_badge_tag} · {html.escape(source)}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(ans)

            # Attached Dataframe if available
            if table_df is not None and isinstance(table_df, pd.DataFrame) and not table_df.empty:
                st.dataframe(table_df, use_container_width=True, hide_index=False)

            # Fallback Notice if LLM failed
            if turn.get("fallback_warning"):
                st.caption(f"⚠️ *{turn['fallback_warning']}*")

            # Follow-up Suggestions
            if followups:
                st.markdown(
                    "<div style='font-size: 11.5px; font-weight: 600; color: var(--text-muted); margin-top: 12px; margin-bottom: 6px;'>Suggested Follow-Ups:</div>",
                    unsafe_allow_html=True
                )
                f_cols = st.columns(min(len(followups), 3), gap="small")
                for f_i, f_text in enumerate(followups[:3]):
                    with f_cols[f_i]:
                        if st.button(f_text, key=f"fu_btn_{t_idx}_{f_i}", use_container_width=True):
                            _execute_ai_query(f_text, df, metadata)
                            st.rerun()

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)


def _execute_ai_query(query: str, df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Execute AI query and append to conversation history."""
    with st.spinner("AI Analyst is examining dataset and preparing response..."):
        result = ask_ai_analyst(query, df, metadata)
        if result.get("fallback_warning"):
            st.toast(result["fallback_warning"], icon="⚠️")
        turn_data = {
            "question": query,
            "answer": result.get("answer", ""),
            "source": result.get("source", "Analytics Engine"),
            "is_llm": result.get("is_llm", False),
            "table": result.get("table"),
            "followups": result.get("followups", []),
            "fallback_warning": result.get("fallback_warning")
        }
        st.session_state.setdefault("ai_chat_history", []).append(turn_data)
        log_activity(f"AI Analyst: asked '{query[:50]}'", "sparkles")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: ROOT-CAUSE INVESTIGATION
# ─────────────────────────────────────────────────────────────────────────────

def _render_investigate_tab(df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Render INVESTIGATE mode: structured root-cause analysis form."""
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    datetime_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

    if not numeric_cols:
        render_notification(
            title="No numeric columns available",
            message="Root-cause investigation requires at least one numeric column as a target metric.",
            variant="warning"
        )
        return

    st.markdown("#### Root-Cause Setup")
    st.caption("Select a target metric and comparison dimension to identify drivers, anomalies, and ranked explanations.")

    form_c1, form_c2, form_c3 = st.columns(3, gap="medium")

    with form_c1:
        target_metric = st.selectbox(
            "Target Metric (What to investigate)",
            options=numeric_cols,
            key="inv_target_metric",
            help="The numeric column you want to understand better."
        )

    with form_c2:
        dim_options = cat_cols if cat_cols else numeric_cols
        comparison_dim = st.selectbox(
            "Comparison Dimension (Split by)",
            options=dim_options,
            key="inv_comparison_dim",
            help="The column to group by when comparing the target metric."
        )

    with form_c3:
        time_options = ["None"] + datetime_cols + [c for c in numeric_cols if "year" in c.lower() or "date" in c.lower()]
        time_col = st.selectbox(
            "Time Column (Optional)",
            options=time_options,
            key="inv_time_col",
            help="Optional: a date or year column for trend context."
        )
        time_col = None if time_col == "None" else time_col

    run_col, _, _ = st.columns([3, 4, 5])
    with run_col:
        run_btn = st.button("Run Root-Cause Investigation →", key="inv_run_btn", type="primary", use_container_width=True)

    if run_btn:
        with st.spinner("Computing statistical breakdown and correlation drivers..."):
            result = _run_investigation(df, target_metric, comparison_dim, time_col)
            st.session_state["ai_investigate_result"] = result
            log_activity(f"AI Analyst: investigated '{target_metric}' by '{comparison_dim}'", "activity")
            st.rerun()

    result = st.session_state.get("ai_investigate_result")
    if result and result.get("target") == target_metric and result.get("dimension") == comparison_dim:
        _render_investigation_results(result, df, metadata)
    elif result and (result.get("target") != target_metric or result.get("dimension") != comparison_dim):
        st.info("Configuration changed. Click **Run Root-Cause Investigation →** to update results.")


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

    # 2. Group by dimension
    try:
        if not pd.api.types.is_numeric_dtype(df[dimension]):
            grouped = df.groupby(dimension)[target].agg(["mean", "count", "std"]).reset_index()
            grouped.columns = ["Category", "Mean", "Count", "Std"]
            grouped["Mean"] = grouped["Mean"].round(2)
            grouped = grouped.sort_values("Mean", ascending=False)
            result["group_df"] = grouped.head(15)
        else:
            df_tmp = df.copy()
            df_tmp["_bin"] = pd.cut(df_tmp[dimension], bins=min(10, max(2, df_tmp[dimension].nunique())), precision=1)
            grouped = df_tmp.groupby("_bin", observed=False)[target].agg(["mean", "count"]).reset_index()
            grouped.columns = ["Category", "Mean", "Count"]
            grouped["Mean"] = grouped["Mean"].round(2)
            grouped["Category"] = grouped["Category"].astype(str)
            grouped = grouped.sort_values("Mean", ascending=False)
            result["group_df"] = grouped.head(10)
    except Exception:
        result["group_df"] = None

    # 3. Correlations
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

    # 4. Outliers
    outlier_data = compute_iqr_outliers(df, [target])
    col_outliers = outlier_data.get("column_outliers", {}).get(target, {})
    result["outlier_count"] = col_outliers.get("outlier_count", 0)
    result["outlier_pct"] = col_outliers.get("outlier_pct", 0.0)
    result["outlier_bounds"] = (
        col_outliers.get("lower_bound"), col_outliers.get("upper_bound")
    ) if col_outliers else (None, None)

    # 5. Confidence score
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

    # 6. Explanations
    explanations = []
    if result.get("outlier_pct", 0) > 5:
        explanations.append(f"High outlier rate ({result['outlier_pct']:.1f}%) in '{target}' may be skewing distribution averages.")
    if result.get("top_correlators"):
        top = result["top_correlators"][0]
        if abs(top["r"]) >= 0.5:
            direction = "positively" if top["r"] > 0 else "negatively"
            explanations.append(f"'{target}' is strongly {direction} correlated with '{top['col']}' (r = {top['r']:.2f}), making it a primary driver.")
    if result.get("target_missing", 0) > 0:
        explanations.append(f"{result['target_missing']:,} missing values in '{target}' — observations may reflect subtle subset bias.")
    if not explanations:
        explanations.append(f"No anomalous drivers identified. Variance in '{target}' is evenly distributed across '{dimension}'.")

    result["explanations"] = explanations
    return result


def _render_investigation_results(result: Dict[str, Any], df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Render the investigation findings in structured sections."""
    target = result["target"]
    dimension = result["dimension"]
    confidence = result.get("confidence", "Low")
    conf_class = f"ds-confidence-{confidence.lower()}"

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Problem Statement Card
    conf_badge = f'<span class="ds-confidence-badge {conf_class}">Confidence: {confidence}</span>'
    st.markdown(
        f"""
        <div class="ds-investigate-finding">
            <div class="ds-investigate-section-label">Investigation Summary</div>
            <div style="font-size:15px; font-weight:700; color:var(--text-primary); margin-bottom:6px;">
                How does <em>{html.escape(target)}</em> vary across <em>{html.escape(dimension)}</em>?
            </div>
            <div style="font-size:13px; color:var(--text-secondary); margin-bottom:10px;">
                Mean = {result.get("target_mean", 0):,.2f} &nbsp;|&nbsp;
                Std Dev = {result.get("target_std", 0):,.2f} &nbsp;|&nbsp;
                Range [{result.get("target_min", 0):,.2f} – {result.get("target_max", 0):,.2f}]
            </div>
            {conf_badge}
        </div>
        """,
        unsafe_allow_html=True
    )

    # Group Comparison Bar Chart
    group_df = result.get("group_df")
    if group_df is not None and not group_df.empty:
        st.markdown(
            f"<div class='ds-investigate-section-label' style='margin-top:16px;'>"
            f"Average '{html.escape(target)}' by '{html.escape(dimension)}'"
            f"</div>",
            unsafe_allow_html=True
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
            st.dataframe(group_df.head(10), use_container_width=True)

    # Correlation Drivers
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
            f"""
            <div class="ds-investigate-finding">
                <div class="ds-investigate-section-label">Correlated Feature Drivers</div>
                {"".join(corr_lines)}
            </div>
            """,
            unsafe_allow_html=True
        )

    # Explanations
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
            f"""
            <div class="ds-investigate-finding">
                <div class="ds-investigate-section-label">Deterministic Analytical Explanations</div>
                {exp_lines}
            </div>
            """,
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: EXECUTIVE DATA STORY
# ─────────────────────────────────────────────────────────────────────────────

def _build_data_story(df: pd.DataFrame, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate a 7-chapter automated executive data briefing from real session state."""
    chapters = []
    dataset_name = st.session_state.get("dataset_name", "dataset")
    file_type = st.session_state.get("dataset_file_type", "CSV")

    # Chapter 1: Dataset Context
    rows = metadata.get("total_rows", len(df))
    cols_count = metadata.get("total_columns", len(df.columns))
    memory = metadata.get("memory_formatted", "N/A")
    numeric_count = sum(1 for c in df.columns if pd.api.types.is_numeric_dtype(df[c]))
    cat_count = len(df.columns) - numeric_count
    chapters.append({
        "num": "Chapter 1",
        "title": "Dataset Context & Baseline",
        "lines": [
            f"Dataset Name: <strong>{html.escape(dataset_name)}</strong> ({file_type.upper()})",
            f"Dimensions: <strong>{rows:,} observations × {cols_count} features</strong>",
            f"Memory Footprint: <strong>{memory}</strong>",
            f"Feature Breakdown: <strong>{numeric_count} numeric</strong> + <strong>{cat_count} categorical / text</strong>",
        ],
        "note": None,
    })

    # Chapter 2: Data Health
    quality_score = metadata.get("quality_score", 95.0)
    missing_pct = metadata.get("missing_percentage", 0.0) or 0.0
    dup_pct = metadata.get("duplicate_percentage", 0.0) or 0.0
    status = "Excellent" if quality_score >= 90 else ("Good" if quality_score >= 75 else "Needs Attention")
    chapters.append({
        "num": "Chapter 2",
        "title": "Data Integrity & Health Audit",
        "lines": [
            f"Composite Quality Score: <strong>{quality_score:.1f}% ({status})</strong>",
            f"Missing Values Rate: <strong>{missing_pct:.2f}%</strong> of total data points",
            f"Duplicate Records: <strong>{dup_pct:.2f}%</strong> of total records",
        ],
        "note": "Computed via Data Quality audit engine.",
    })

    # Chapter 3: Transformations Applied
    prep_history = st.session_state.get("prep_history", [])
    if prep_history:
        transform_lines = [f"<strong>{len(prep_history)} preparation steps</strong> applied:"]
        for step in prep_history[-6:]:
            step_str = step if isinstance(step, str) else str(step.get("description", step))
            transform_lines.append(f"• {html.escape(step_str[:120])}")
        note = "Interactive working dataset active in analysis."
    else:
        transform_lines = ["No transformations recorded. Dataset is in original uploaded state."]
        note = "Visit Data Preparation to clean, cast, or derive features."
    chapters.append({
        "num": "Chapter 3",
        "title": "Data Preparation History",
        "lines": transform_lines,
        "note": note,
    })

    # Chapter 4: Key Patterns & Insights
    insights = generate_eda_insights(df, metadata)
    if insights:
        pattern_lines = [f"Top <strong>{min(len(insights), 5)} automated data observations</strong>:"]
        for ins in insights[:5]:
            pattern_lines.append(f"• <strong>{html.escape(ins.get('severity', 'OBSERVATION'))}</strong> — {html.escape(ins.get('title', ''))}: {html.escape(ins.get('observation', ''))}")
    else:
        pattern_lines = ["No major anomalies detected. Features appear well-distributed."]
    chapters.append({
        "num": "Chapter 4",
        "title": "Major Analytical Patterns",
        "lines": pattern_lines,
        "note": "Derived from statistical distribution and variance analysis.",
    })

    # Chapter 5: Strongest Relationships
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(numeric_cols) >= 2:
        corr_matrix = compute_correlation_matrix(df, numeric_cols)
        pos_pairs, neg_pairs = extract_strongest_correlations(corr_matrix, top_n=3)
        all_pairs = pos_pairs[:3] + neg_pairs[:2]
        if all_pairs:
            rel_lines = [f"<strong>{len(all_pairs)} primary correlations</strong> identified:"]
            for p in all_pairs:
                direction = "▲ Positive" if p["Correlation (r)"] > 0 else "▼ Negative"
                rel_lines.append(
                    f"• {direction}: <strong>'{html.escape(p['Variable 1'])}'</strong> ↔ "
                    f"<strong>'{html.escape(p['Variable 2'])}'</strong> "
                    f"(r = <strong>{p['Correlation (r)']:.2f}</strong>, {html.escape(p['Strength'])})"
                )
        else:
            rel_lines = ["No high correlation coefficients (r > 0.4) detected."]
    else:
        rel_lines = ["Fewer than 2 numeric columns available for correlation analysis."]
    chapters.append({
        "num": "Chapter 5",
        "title": "Key Statistical Relationships",
        "lines": rel_lines,
        "note": "Calculated via Pearson correlation matrix.",
    })

    # Chapter 6: Outlier Landscape
    if numeric_cols:
        outlier_report = compute_iqr_outliers(df, numeric_cols[:8])
        total_out = outlier_report.get("total_outliers", 0)
        affected = outlier_report.get("affected_columns_count", 0)
        rate = outlier_report.get("overall_outlier_rate", 0.0)
        if total_out == 0:
            out_lines = ["✅ Zero outliers detected across numeric columns (1.5× IQR standard)."]
        else:
            out_lines = [
                f"<strong>{total_out:,} outlier data points</strong> detected across <strong>{affected} feature(s)</strong> ({rate:.1f}% rate)."
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
        "title": "Outlier & Anomaly Landscape",
        "lines": out_lines,
        "note": "Computed using IQR fencing method [Q1 - 1.5×IQR, Q3 + 1.5×IQR].",
    })

    # Chapter 7: Recommended Next Steps
    rec_lines = [
        "Explore distributions and subgroup interactions in <strong>Analyze (EDA)</strong>.",
        "Build executive charts and scatter plots in <strong>Visualization Studio</strong>.",
        "Assemble unified KPI dashboards in <strong>Dashboard Studio</strong>."
    ]
    chapters.append({
        "num": "Chapter 7",
        "title": "Recommended Analytical Next Steps",
        "lines": rec_lines,
        "note": None,
    })

    return chapters


def _render_story_tab(df: pd.DataFrame, metadata: Dict[str, Any], dataset_name: str) -> None:
    """Render DATA STORY mode with 1-click narrative briefing and export."""
    gen_col, dl_col, _ = st.columns([3, 3, 6], gap="small")
    with gen_col:
        gen_btn = st.button("Generate Executive Story →", key="story_generate_btn", type="primary", use_container_width=True)

    if gen_btn or st.session_state.get("ai_story_cache") is None:
        chapters = _build_data_story(df, metadata)
        st.session_state["ai_story_cache"] = chapters

    story = st.session_state.get("ai_story_cache")

    if story:
        # Build text export of story
        story_text_lines = [f"# Executive Data Story: {dataset_name}\n"]
        for ch in story:
            story_text_lines.append(f"## {ch['num']}: {ch['title']}")
            for line in ch["lines"]:
                # strip html tags for plaintext export
                clean_l = re.sub(r"<[^>]+>", "", line)
                story_text_lines.append(f"- {clean_l}")
            if ch.get("note"):
                story_text_lines.append(f"> Note: {ch['note']}")
            story_text_lines.append("")

        story_export_str = "\n".join(story_text_lines)

        with dl_col:
            st.download_button(
                "Download Executive Briefing (.md)",
                data=story_export_str,
                file_name=f"executive_story_{dataset_name}.md",
                mime="text/markdown",
                key="dl_story_brief_btn",
                use_container_width=True
            )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        for chapter in story:
            with st.expander(
                f"**{chapter['num']}** — {chapter['title']}",
                expanded=True
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
                        f'<div style="font-size:11px; color:var(--text-muted); margin-top:10px; padding-top:8px; border-top:1px solid var(--border);">'
                        f'📎 {html.escape(chapter["note"])}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )


# ─────────────────────────────────────────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────────────────────────────────────────

def _render_no_dataset_state(module_name: str = "AI Analyst", key_prefix: str = "ai") -> None:
    """Empty state shown when no dataset is loaded."""
    render_empty_state(
        title=f"No dataset loaded for {module_name}",
        description=f"Upload a CSV or Excel dataset or load a sample dataset to enable natural language Q&A, root-cause investigations, and automated executive data stories.",
        icon="sparkles" if module_name == "AI Analyst" else "book-open",
    )

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    render_section_header(
        title="Quick Start with Sample Data",
        subtitle=f"Select a pre-loaded business dataset to immediately explore the {module_name} workspace."
    )

    sample_catalog = get_available_sample_datasets()
    cols = st.columns(len(sample_catalog) if sample_catalog else 1)
    for idx, (key, info) in enumerate(sample_catalog.items()):
        with cols[idx]:
            st.markdown(f"**{info['name']}**")
            st.caption(info["description"])
            if st.button(f"Load {info['name']}", key=f"{key_prefix}_sample_load_{key}", type="primary", use_container_width=True):
                with st.spinner(f"Loading {info['name']}..."):
                    s_df, s_err, s_file_type = load_sample_dataset_by_key(key)
                    if not s_err and s_df is not None:
                        set_active_dataset(s_df, info["filename"], s_file_type)
                        st.toast(f"{info['name']} loaded successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to load sample dataset: {s_err}")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    btn_c1, btn_c2, btn_c3 = st.columns([1, 2, 1])
    with btn_c2:
        if st.button("Upload Custom Dataset", key=f"{key_prefix}_goto_dataset_btn", use_container_width=True):
            st.session_state["current_page"] = "Dataset"
            st.rerun()

"""
DATA STUDIO v2 — Real LLM / Generative AI Analyst Service
=============================================================================
Provides real Large Language Model (LLM) intelligence for natural language Q&A,
multilingual understanding (Hindi, English, Spanish, French, German, etc.),
and dataset-grounded analytical commentary.

Supported Providers:
  1. Google Gemini API (gemini-1.5-flash, gemini-2.0-flash, gemini-1.5-pro)
  2. OpenAI / OpenRouter / Groq (gpt-4o, gpt-4o-mini, etc.)
  3. Built-in Deterministic Analytics Engine (Fallback when offline/no key)
"""
from __future__ import annotations
import os
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import streamlit as st

from modules.eda_engine import (
    compute_summary_statistics,
    compute_correlation_matrix,
    extract_strongest_correlations,
    compute_iqr_outliers,
    generate_eda_insights,
)


# ─────────────────────────────────────────────────────────────────────────────
# API KEY RESOLUTION & PERSISTENCE
# ─────────────────────────────────────────────────────────────────────────────

def get_ai_api_key() -> Tuple[Optional[str], str]:
    """
    Retrieve active API key and provider from session state or environment.
    Returns (api_key, provider_name).
    """
    # 1. Session State
    session_key = st.session_state.get("ai_api_key")
    provider = st.session_state.get("ai_provider", "gemini").lower()
    if session_key and session_key.strip():
        return session_key.strip(), provider

    # 2. Environment Variables
    gemini_env = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_env:
        return gemini_env.strip(), "gemini"

    openai_env = os.environ.get("OPENAI_API_KEY")
    if openai_env:
        return openai_env.strip(), "openai"

    return None, provider


def set_ai_api_key(api_key: str, provider: str = "gemini") -> None:
    """Store the user-supplied API key in session state."""
    st.session_state["ai_api_key"] = api_key.strip()
    st.session_state["ai_provider"] = provider.lower()


# ─────────────────────────────────────────────────────────────────────────────
# DATASET CONTEXT GROUNDING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def build_dataset_llm_context(df: pd.DataFrame, metadata: Dict[str, Any]) -> str:
    """
    Extracts a comprehensive, token-efficient statistical profile of the active
    dataset to ground the LLM in real numbers, preventing hallucination.
    """
    if df is None or df.empty:
        return "No active dataset."

    dataset_name = st.session_state.get("dataset_name", "dataset.csv")
    total_rows, total_cols = df.shape

    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    datetime_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

    lines = []
    lines.append(f"DATASET NAME: {dataset_name}")
    lines.append(f"DIMENSIONS: {total_rows:,} rows × {total_cols} columns")
    lines.append(f"QUALITY INDEX: {metadata.get('quality_score', 95.0):.1f}%")
    lines.append(f"MISSING CELLS RATE: {metadata.get('missing_percentage', 0.0):.2f}%")
    lines.append(f"DUPLICATE ROWS: {int(df.duplicated().sum()):,}")

    # Column Types Summary
    lines.append(f"\nNUMERIC COLUMNS ({len(numeric_cols)}): {', '.join(numeric_cols[:15])}")
    lines.append(f"CATEGORICAL COLUMNS ({len(cat_cols)}): {', '.join(cat_cols[:15])}")
    if datetime_cols:
        lines.append(f"DATETIME COLUMNS ({len(datetime_cols)}): {', '.join(datetime_cols[:5])}")

    # Summary Statistics for Numeric Features
    if numeric_cols:
        lines.append("\n--- NUMERIC DESCRIPTIVE STATISTICS ---")
        stats_df = compute_summary_statistics(df, numeric_cols[:8])
        for _, row in stats_df.iterrows():
            lines.append(
                f"• {row['Column']}: Count={row['Count']}, Mean={row['Mean']:,.2f}, "
                f"Median={row['Median']:,.2f}, Std={row['Std Dev']:,.2f}, "
                f"Min={row['Min']:,.2f}, Max={row['Max']:,.2f}, Missing={row['Missing %']:.1f}%"
            )

    # Top Categories for Categorical Features
    if cat_cols:
        lines.append("\n--- CATEGORICAL FREQUENCIES (TOP 5 VALUES) ---")
        for col in cat_cols[:6]:
            s = df[col].dropna()
            val_counts = s.value_counts().head(5)
            counts_str = ", ".join([f"'{k}': {v:,} ({(v/len(df)*100):.1f}%)" for k, v in val_counts.items()])
            lines.append(f"• {col} ({s.nunique()} unique): {counts_str}")

    # Correlations
    if len(numeric_cols) >= 2:
        corr_matrix = compute_correlation_matrix(df, numeric_cols[:8])
        pos_pairs, neg_pairs = extract_strongest_correlations(corr_matrix, top_n=3)
        if pos_pairs or neg_pairs:
            lines.append("\n--- STRONGEST CORRELATIONS ---")
            for p in pos_pairs[:3]:
                lines.append(f"• Positive: {p['Variable 1']} ↔ {p['Variable 2']} (r = {p['Correlation (r)']:.2f})")
            for p in neg_pairs[:2]:
                lines.append(f"• Negative: {p['Variable 1']} ↔ {p['Variable 2']} (r = {p['Correlation (r)']:.2f})")

    # Outliers
    if numeric_cols:
        outlier_data = compute_iqr_outliers(df, numeric_cols[:6])
        if outlier_data.get("total_outliers", 0) > 0:
            lines.append(f"\n--- POTENTIAL OUTLIERS (IQR METHOD) ---")
            lines.append(f"Total outliers: {outlier_data['total_outliers']:,} across {outlier_data['affected_columns_count']} columns")

    # First 5 sample rows as tabular text
    lines.append("\n--- SAMPLE DATA (FIRST 5 ROWS) ---")
    sample_preview = df.head(5).to_string(index=False, max_cols=10)
    lines.append(sample_preview)

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# GEMINI API CALLER
# ─────────────────────────────────────────────────────────────────────────────

def _call_gemini_api(prompt: str, context: str, api_key: str) -> Dict[str, Any]:
    """Call Google Gemini 1.5/2.0 Flash API with fallback to direct HTTP REST."""
    system_instruction = (
        "You are an expert, multilingual AI Data Analyst embedded in Data Studio v2. "
        "Your role is to answer questions strictly grounded in the provided dataset context.\n\n"
        "RULES:\n"
        "1. Answer in the EXACT language the user asks in (e.g. if asked in Hindi, respond in Hindi; "
        "if in Spanish, respond in Spanish; if in English, respond in English).\n"
        "2. Ground every fact, percentage, and metric strictly in the provided dataset numbers.\n"
        "3. Format your response cleanly with bold key figures, bullet points, and concise executive explanations.\n"
        "4. At the very end of your response, add a section called 'Follow-up Questions:' with 3 relevant, interesting questions."
    )

    # 1. Attempt using google.generativeai SDK if available
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Prefer fast & accurate flash model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )
        full_content = f"--- ACTIVE DATASET CONTEXT ---\n{context}\n\n--- USER QUESTION ---\n{prompt}"
        response = model.generate_content(full_content)
        raw_text = response.text
        return _parse_llm_response(raw_text, "Google Gemini 1.5 Flash")
    except Exception:
        pass

    # 2. Fallback: Direct HTTP REST Call to Gemini API (zero external dependency)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{system_instruction}\n\n--- DATASET CONTEXT ---\n{context}\n\n--- USER QUESTION ---\n{prompt}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return _parse_llm_response(raw_text, "Google Gemini API (REST)")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("error", {}).get("message", str(e))
        except Exception:
            msg = str(e)
        raise RuntimeError(f"Gemini API Error: {msg}")
    except Exception as e:
        raise RuntimeError(f"Gemini Request Failed: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# OPENAI / CUSTOM ENDPOINT CALLER
# ─────────────────────────────────────────────────────────────────────────────

def _call_openai_api(prompt: str, context: str, api_key: str) -> Dict[str, Any]:
    """Call OpenAI compatible chat completion endpoint via HTTP REST."""
    url = "https://api.openai.com/v1/chat/completions"
    system_msg = (
        "You are an expert, multilingual AI Data Analyst embedded in Data Studio v2. "
        "Answer questions strictly grounded in the provided dataset context. "
        "Answer in the EXACT language the user asked in. Format with bold numbers and bullet points. "
        "At the end, add 'Follow-up Questions:' with 3 relevant questions."
    )
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": f"{system_msg}\n\n--- DATASET CONTEXT ---\n{context}"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1000
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_text = data["choices"][0]["message"]["content"]
            return _parse_llm_response(raw_text, "OpenAI GPT-4o-mini")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("error", {}).get("message", str(e))
        except Exception:
            msg = str(e)
        raise RuntimeError(f"OpenAI API Error: {msg}")
    except Exception as e:
        raise RuntimeError(f"OpenAI Request Failed: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# RESPONSE PARSER
# ─────────────────────────────────────────────────────────────────────────────

def _parse_llm_response(raw_text: str, source_label: str) -> Dict[str, Any]:
    """Extract follow-up suggestions from LLM answer."""
    followups = []
    answer_text = raw_text

    # Search for follow-up questions section
    lower_text = raw_text.lower()
    split_markers = ["follow-up questions:", "follow up questions:", "suggested questions:", "related questions:"]
    
    for marker in split_markers:
        if marker in lower_text:
            idx = lower_text.find(marker)
            answer_text = raw_text[:idx].strip()
            followup_block = raw_text[idx + len(marker):].strip()
            for line in followup_block.split("\n"):
                line_clean = line.strip().lstrip("0123456789.-*• ").strip()
                if line_clean and len(line_clean) > 8:
                    followups.append(line_clean)
            break

    if not followups:
        followups = [
            "What are the top correlations in this data?",
            "Which category has the highest average value?",
            "Are there any notable anomalies or outliers?"
        ]

    return {
        "answer": answer_text,
        "source": source_label,
        "followups": followups[:3],
        "is_llm": True
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PUBLIC QUERY FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def ask_ai_analyst(
    question: str,
    df: pd.DataFrame,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main dispatcher for AI Analyst queries:
    1. If an LLM API key is available (Gemini or OpenAI), calls real generative AI
       with full multilingual and complex question comprehension.
    2. If no API key is set or offline, falls back to deterministic Analytics Engine.
    """
    api_key, provider = get_ai_api_key()

    if api_key:
        context = build_dataset_llm_context(df, metadata)
        try:
            if provider == "openai":
                return _call_openai_api(question, context, api_key)
            else:
                return _call_gemini_api(question, context, api_key)
        except Exception as e:
            # Fallback to deterministic with error notice
            err_msg = str(e)
            st.warning(f"AI LLM query encountered an issue ({err_msg}). Falling back to Analytics Engine.")

    # Fallback to deterministic rule-based engine
    from modules.ai_analyst import _answer_question_deterministic
    return _answer_question_deterministic(question, df, metadata)

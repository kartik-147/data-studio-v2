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

def _search_secrets_recursively(obj: Any) -> Tuple[Optional[str], str]:
    """Recursively traverse st.secrets (including nested tables like [firebase], [gemini], etc.)"""
    if isinstance(obj, str):
        v_str = obj.strip()
        if v_str.startswith("AIzaSy"):
            return v_str, "gemini"
        if v_str.startswith("sk-") and len(v_str) > 20:
            return v_str, "openai"
        return None, "gemini"

    if isinstance(obj, dict) or hasattr(obj, "items"):
        # First pass: check direct keys in this dict
        for k, v in obj.items():
            k_lower = str(k).lower()
            if isinstance(v, str) and v.strip():
                v_str = v.strip()
                if "gemini" in k_lower or "google" in k_lower or "ai_api" in k_lower or "llm_key" in k_lower:
                    return v_str, "gemini"
                if "openai" in k_lower:
                    return v_str, "openai"
                if v_str.startswith("AIzaSy"):
                    return v_str, "gemini"
                if v_str.startswith("sk-") and len(v_str) > 20:
                    return v_str, "openai"

        # Second pass: recurse into nested dicts/sections
        for k, v in obj.items():
            if isinstance(v, dict) or hasattr(v, "items"):
                found_key, prov = _search_secrets_recursively(v)
                if found_key:
                    return found_key, prov

    return None, "gemini"


def get_ai_api_key() -> Tuple[Optional[str], str]:
    """
    Retrieve active API key and provider from session state, st.secrets (recursively), or environment.
    Returns (api_key, provider_name).
    """
    # 1. Session State (User entered directly in UI)
    session_key = st.session_state.get("ai_api_key")
    provider = st.session_state.get("ai_provider", "gemini").lower()
    if session_key and str(session_key).strip():
        return str(session_key).strip(), provider

    # 2. Streamlit Cloud Secrets (st.secrets) — deep recursive search
    try:
        if hasattr(st, "secrets") and st.secrets:
            secret_key, secret_prov = _search_secrets_recursively(st.secrets)
            if secret_key:
                return secret_key, secret_prov
    except Exception:
        pass

    # 3. Environment Variables
    env_gemini = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if env_gemini and env_gemini.strip():
        return env_gemini.strip(), "gemini"

    env_openai = os.environ.get("OPENAI_API_KEY")
    if env_openai and env_openai.strip():
        return env_openai.strip(), "openai"

    return None, provider

    # 3. Environment Variables
    env_gemini = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if env_gemini and env_gemini.strip():
        return env_gemini.strip(), "gemini"

    env_openai = os.environ.get("OPENAI_API_KEY")
    if env_openai and env_openai.strip():
        return env_openai.strip(), "openai"

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

# ─────────────────────────────────────────────────────────────────────────────
# GEMINI API CALLER (MULTI-MODEL AUTO-FALLBACK)
# ─────────────────────────────────────────────────────────────────────────────

def _call_gemini_api(prompt: str, context: str, api_key: str) -> Dict[str, Any]:
    """
    Call Google Gemini API with automatic multi-model fallback across SDK and REST.
    Tries 1.5-flash, 2.0-flash, 1.5-pro, and gemini-pro across v1beta and v1 endpoints.
    """
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
        sdk_models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-pro"]
        for m_name in sdk_models:
            try:
                model = genai.GenerativeModel(
                    model_name=m_name,
                    system_instruction=system_instruction
                )
                full_content = f"--- ACTIVE DATASET CONTEXT ---\n{context}\n\n--- USER QUESTION ---\n{prompt}"
                response = model.generate_content(full_content)
                if response and response.text:
                    return _parse_llm_response(response.text, f"Google Gemini ({m_name})")
            except Exception:
                continue
    except Exception:
        pass

    # 2. Fallback: Direct HTTP REST with multi-model fallback
    candidate_endpoints = [
        ("v1beta", "gemini-1.5-flash"),
        ("v1beta", "gemini-2.0-flash"),
        ("v1beta", "gemini-1.5-flash-latest"),
        ("v1", "gemini-1.5-flash"),
        ("v1beta", "gemini-1.5-pro"),
        ("v1beta", "gemini-pro"),
        ("v1", "gemini-pro"),
    ]

    last_err = None
    for api_ver, mod_name in candidate_endpoints:
        url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{mod_name}:generateContent?key={api_key}"
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
                return _parse_llm_response(raw_text, f"Google Gemini REST ({mod_name})")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(err_body)
                last_err = err_json.get("error", {}).get("message", str(e))
            except Exception:
                last_err = str(e)
            # If model not found (404/400), try next candidate model
            continue
        except Exception as e:
            last_err = str(e)
            continue

    raise RuntimeError(f"Gemini API Error: {last_err or 'All Gemini model endpoints failed'}")


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
# SELF-CONTAINED DETERMINISTIC FALLBACK ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def _answer_question_deterministic(q: str, df: pd.DataFrame, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Self-contained fallback engine for answering dataset questions when offline or no API key is present.
    """
    q_lower = q.lower().strip()
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if df[c].dtype == object or str(df[c].dtype) == "category"]

    # Shape / size
    if any(kw in q_lower for kw in ["how many rows", "how many columns", "shape", "size", "dimension", "rows and columns"]):
        rows, cols = df.shape
        answer = (
            f"This dataset contains **{rows:,} rows** and **{cols} columns** "
            f"({rows * cols:,} total data cells).\n\n"
            f"• **Numeric columns**: {len(numeric_cols)}\n"
            f"• **Categorical columns**: {len(cat_cols)}\n"
            f"• **Memory usage**: {metadata.get('memory_formatted', 'N/A')}"
        )
        return {
            "answer": answer,
            "source": "Dataset Dimensions",
            "followups": ["What are the column names?", "What is the overall data quality?"],
            "is_llm": False,
        }

    # Quality score
    if any(kw in q_lower for kw in ["quality", "health", "score", "how clean", "cleanliness"]):
        qs = metadata.get("quality_score", 95.0)
        missing_pct = metadata.get("missing_percentage", 0.0)
        dup_pct = metadata.get("duplicate_percentage", 0.0)
        status = "Excellent" if qs >= 90 else ("Good" if qs >= 75 else "Needs Attention")
        answer = (
            f"The **Data Quality Score is {qs:.1f}%** ({status}).\n\n"
            f"• **Missing values rate**: {missing_pct:.2f}%\n"
            f"• **Duplicate rows**: {dup_pct:.2f}%\n"
            f"• **Completeness**: {100 - missing_pct:.1f}% of cells populated."
        )
        return {
            "answer": answer,
            "source": "Data Quality Engine",
            "followups": ["Which columns have missing values?", "Which columns have outliers?"],
            "is_llm": False,
        }

    # Missing values
    if any(kw in q_lower for kw in ["missing", "null", "nan", "blank", "empty"]):
        missing_s = df.isna().sum()
        missing_cols = missing_s[missing_s > 0].sort_values(ascending=False)
        if missing_cols.empty:
            answer = "Great news! This dataset contains **no missing values** (0 null cells across all columns)."
        else:
            top_missing = missing_cols.head(5)
            lines = [f"• **{col}**: {cnt:,} missing ({cnt/len(df)*100:.1f}%)" for col, cnt in top_missing.items()]
            answer = f"Found missing values in **{len(missing_cols)} column(s)**:\n\n" + "\n".join(lines)
        return {
            "answer": answer,
            "source": "Missing Value Analysis",
            "followups": ["What are the duplicate rows?", "How many rows does this dataset have?"],
            "is_llm": False,
        }

    # Duplicate rows
    if any(kw in q_lower for kw in ["duplicate", "duplicate rows", "repeats", "redundant"]):
        dup_count = int(df.duplicated().sum())
        if dup_count == 0:
            answer = "This dataset contains **0 duplicate rows** — all records are unique."
        else:
            pct = dup_count / len(df) * 100
            answer = (
                f"This dataset contains **{dup_count:,} duplicate rows** "
                f"({pct:.2f}% of all rows). You can remove them in **Data Preparation**."
            )
        return {
            "answer": answer,
            "source": "Deduplication Engine",
            "followups": ["Which columns have missing values?", "What is the overall data quality?"],
            "is_llm": False,
        }

    # Strongest correlation
    if any(kw in q_lower for kw in ["correlation", "correlated", "relationship", "strongest correlation"]):
        if len(numeric_cols) < 2:
            answer = "Correlation analysis requires at least 2 numeric columns. This dataset has fewer."
        else:
            corr_matrix = compute_correlation_matrix(df, numeric_cols[:8])
            pos, neg = extract_strongest_correlations(corr_matrix, top_n=2)
            lines = []
            if pos:
                lines.append(f"• Strongest positive: **{pos[0]['Variable 1']}** ↔ **{pos[0]['Variable 2']}** (r = **{pos[0]['Correlation (r)']:.2f}**)")
            if neg:
                lines.append(f"• Strongest negative: **{neg[0]['Variable 1']}** ↔ **{neg[0]['Variable 2']}** (r = **{neg[0]['Correlation (r)']:.2f}**)")
            answer = "Top correlation findings:\n\n" + "\n".join(lines) if lines else "No significant correlations found."
        return {
            "answer": answer,
            "source": "Correlation Engine",
            "followups": ["What is the average value?", "Which column has the most outliers?"],
            "is_llm": False,
        }

    # Outliers
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
            "is_llm": False,
        }

    # Specific column averages
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
                "is_llm": False,
            }

    # Default automated insights
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
            "Configure an active Google Gemini key to ask any free-form questions in your native language!"
        )
    return {
        "answer": answer,
        "source": "Automated Insights Engine",
        "followups": ["How many rows does this dataset have?", "Which columns have missing values?", "What is the strongest correlation?"],
        "is_llm": False,
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
            # Display warning and cleanly fallback
            err_msg = str(e)
            st.warning(f"AI LLM query encountered an issue ({err_msg}). Falling back to Analytics Engine.")

    # Self-contained fallback to deterministic rule-based engine (ZERO circular imports)
    return _answer_question_deterministic(question, df, metadata)


def test_ai_connection(api_key: Optional[str] = None, provider: str = "gemini") -> Tuple[bool, str]:
    """Test connection to Gemini or OpenAI API to verify key validity."""
    key = api_key or get_ai_api_key()[0]
    if not key:
        return False, "No API key found. Please enter an API key or add GEMINI_API_KEY to Streamlit Secrets."

    prov = (provider or "gemini").lower()
    if prov == "openai":
        try:
            res = _call_openai_api("Respond with 'OK'", "Test dataset", key)
            return True, "Connected successfully to OpenAI API! ✓"
        except Exception as e:
            return False, f"OpenAI error: {str(e)}"
    else:
        try:
            res = _call_gemini_api("Respond with 'OK'", "Test dataset", key)
            return True, f"Connected successfully to {res.get('source', 'Google Gemini')}! ✓"
        except Exception as e:
            return False, f"Gemini error: {str(e)}"

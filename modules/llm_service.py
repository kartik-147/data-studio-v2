"""
DATA STUDIO v2 — Real LLM & Smart Natural Language Analytics Service
=============================================================================
Provides hybrid analytical intelligence:
1. Real Generative AI (Google Gemini 2.0/1.5 Flash & Pro, OpenAI GPT-4o-mini)
   with full multilingual comprehension (English, Hindi, Spanish, etc.) grounded
   in dataset context.
2. Built-in Deterministic Natural Language Engine (NL2Query & Statistical Engine)
   that computes mathematical results directly on pandas DataFrames when offline
   or when no API key is supplied.
"""
from __future__ import annotations
import os
import json
import re
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import numpy as np
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
# GEMINI API CALLER (MULTI-MODEL AUTO-FALLBACK)
# ─────────────────────────────────────────────────────────────────────────────

def _call_gemini_api(prompt: str, context: str, api_key: str) -> Dict[str, Any]:
    """
    Call Google Gemini API with automatic multi-model fallback across SDK and REST.
    Tries 2.0-flash, 1.5-flash, 1.5-pro, and gemini-2.5-flash endpoints.
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
        sdk_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
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
        ("v1beta", "gemini-2.0-flash"),
        ("v1beta", "gemini-1.5-flash"),
        ("v1beta", "gemini-1.5-flash-latest"),
        ("v1", "gemini-1.5-flash"),
        ("v1beta", "gemini-1.5-pro"),
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
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "DataStudio/2.0"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return _parse_llm_response(raw_text, f"Google Gemini ({mod_name})")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(err_body)
                last_err = err_json.get("error", {}).get("message", str(e))
            except Exception:
                last_err = str(e)
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
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "DataStudio/2.0"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_text = data["choices"][0]["message"]["content"]
            return _parse_llm_response(raw_text, "OpenAI (GPT-4o-mini)")
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
# SMART NLP FUZZY COLUMN & ENTITY MATCHERS
# ─────────────────────────────────────────────────────────────────────────────

def _find_best_matching_column(query: str, columns: List[str]) -> Optional[str]:
    """Find column from dataset that best matches words in user query."""
    q_clean = re.sub(r"[^\w\s]", " ", query.lower())
    q_words = set(q_clean.split())

    # 1. Exact or normalized match
    for col in columns:
        col_norm = re.sub(r"[^\w\s]", " ", col.lower()).strip()
        if col.lower() in query.lower() or col_norm in q_clean:
            return col

    # 2. Word token match
    for col in columns:
        col_words = set(re.sub(r"[^\w\s]", " ", col.lower()).split())
        if col_words and col_words.issubset(q_words):
            return col

    # 3. Partial word intersection
    best_col = None
    best_overlap = 0
    for col in columns:
        col_words = set(re.sub(r"[^\w\s]", " ", col.lower()).split())
        overlap = len(col_words.intersection(q_words))
        if overlap > best_overlap:
            best_overlap = overlap
            best_col = col

    return best_col if best_overlap > 0 else None


def _find_all_matching_columns(query: str, columns: List[str]) -> List[str]:
    """Extract all columns mentioned in user query."""
    matched = []
    q_lower = query.lower()
    for col in columns:
        col_norm = col.lower().replace("_", " ")
        if col.lower() in q_lower or col_norm in q_lower:
            matched.append(col)
    return matched


# ─────────────────────────────────────────────────────────────────────────────
# DETERMINISTIC NATURAL LANGUAGE & STATISTICAL ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def _answer_question_deterministic(q: str, df: pd.DataFrame, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Intelligent Natural Language & Statistical Query Engine that computes real
    mathematical results, aggregations, distributions, extremes, and correlations directly
    on pandas DataFrames without needing an external API key.
    """
    if df is None or df.empty:
        return {
            "answer": "No dataset is currently loaded in the workspace. Please upload or load a dataset first.",
            "source": "Analytics Engine",
            "followups": ["How to upload a dataset?"],
            "is_llm": False
        }

    q_lower = q.lower().strip()
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    all_cols = list(df.columns)
    dataset_name = st.session_state.get("dataset_name", "dataset")

    # ── 1. Columns & Schema ──────────────────────────────────────────────────
    if any(kw in q_lower for kw in ["what are the column", "list column", "show column", "column name", "column list", "schema", "features", "data type", "dtypes"]):
        type_details = metadata.get("column_details", [])
        if type_details:
            lines = [f"• **{c['column_name']}** ({c['detected_type']}) — Dtype: `{c['pandas_dtype']}`, {c['non_null_count']:,} non-null values" for c in type_details[:15]]
            schema_text = "\n".join(lines)
        else:
            schema_text = "\n".join([f"• **{c}** ({df[c].dtype})" for c in all_cols[:15]])

        answer = (
            f"The dataset **'{dataset_name}'** contains **{len(all_cols)} columns**:\n\n"
            f"{schema_text}\n\n"
            f"• **Numeric ({len(numeric_cols)})**: {', '.join(numeric_cols[:6]) if numeric_cols else 'None'}\n"
            f"• **Categorical / Text ({len(cat_cols)})**: {', '.join(cat_cols[:6]) if cat_cols else 'None'}"
        )
        return {
            "answer": answer,
            "source": "Dataset Schema Engine",
            "followups": ["How many rows does this dataset have?", "What is the overall data quality?", "Show sample rows"],
            "is_llm": False
        }

    # ── 2. Shape, Rows, Dimensions, Size ─────────────────────────────────────
    if any(kw in q_lower for kw in ["how many row", "row count", "how many col", "shape", "size", "dimension", "rows and column", "total record"]):
        rows, cols = df.shape
        answer = (
            f"This dataset contains **{rows:,} rows** and **{cols} columns** "
            f"({rows * cols:,} total data cells).\n\n"
            f"• **Numeric features**: {len(numeric_cols)}\n"
            f"• **Categorical / text features**: {len(cat_cols)}\n"
            f"• **Memory usage**: {metadata.get('memory_formatted', 'N/A')}\n"
            f"• **Completeness**: {100 - metadata.get('missing_percentage', 0.0):.1f}% populated"
        )
        return {
            "answer": answer,
            "source": "Dataset Dimensions Engine",
            "followups": ["What are the column names?", "What is the overall data quality?", "Which column has the most outliers?"],
            "is_llm": False,
        }

    # ── 3. Data Quality, Health, Cleanliness ──────────────────────────────────
    if any(kw in q_lower for kw in ["quality", "health", "score", "how clean", "cleanliness", "audit"]):
        qs = metadata.get("quality_score", 95.0)
        missing_pct = metadata.get("missing_percentage", 0.0)
        dup_pct = metadata.get("duplicate_percentage", 0.0)
        missing_cnt = metadata.get("missing_cells", 0)
        dup_cnt = metadata.get("duplicate_rows", int(df.duplicated().sum()))
        status = "Excellent" if qs >= 90 else ("Good" if qs >= 75 else "Needs Attention")

        answer = (
            f"The **Data Quality Score is {qs:.1f}%** ({status}).\n\n"
            f"• **Missing Cells**: {missing_cnt:,} ({missing_pct:.2f}% rate)\n"
            f"• **Duplicate Records**: {dup_cnt:,} ({dup_pct:.2f}% rate)\n"
            f"• **Completeness Index**: {100 - missing_pct:.1f}%\n\n"
            f"You can explore full column-by-column quality breakdown in the **Data Quality** module."
        )
        return {
            "answer": answer,
            "source": "Data Quality Engine",
            "followups": ["Which columns have missing values?", "Are there duplicate rows?", "Which columns have outliers?"],
            "is_llm": False,
        }

    # ── 4. Missing Values & Nulls ─────────────────────────────────────────────
    if any(kw in q_lower for kw in ["missing", "null", "nan", "blank", "empty"]):
        missing_s = df.isna().sum()
        missing_cols = missing_s[missing_s > 0].sort_values(ascending=False)
        if missing_cols.empty:
            answer = "Great news! This dataset is **100% complete with 0 missing values** across all columns."
        else:
            top_missing = missing_cols.head(6)
            lines = [f"• **{col}**: {cnt:,} nulls ({(cnt/len(df)*100):.1f}% missing)" for col, cnt in top_missing.items()]
            answer = (
                f"Detected missing values in **{len(missing_cols)} column(s)** ({missing_s.sum():,} total null cells):\n\n"
                + "\n".join(lines) + "\n\n"
                f"You can impute or remove missing values in **Data Preparation**."
            )
        return {
            "answer": answer,
            "source": "Completeness Engine",
            "followups": ["What is the overall data quality?", "How many rows does this dataset have?", "Are there duplicate rows?"],
            "is_llm": False,
        }

    # ── 5. Duplicate Rows ─────────────────────────────────────────────────────
    if any(kw in q_lower for kw in ["duplicate", "duplicate row", "repeats", "redundant", "dedup"]):
        dup_count = int(df.duplicated().sum())
        if dup_count == 0:
            answer = "This dataset contains **0 duplicate rows** — every record is distinct and unique."
        else:
            pct = dup_count / len(df) * 100
            answer = (
                f"Found **{dup_count:,} duplicate rows** ({pct:.2f}% of total rows).\n\n"
                f"You can deduplicate these records with 1 click in the **Data Preparation** module."
            )
        return {
            "answer": answer,
            "source": "Deduplication Engine",
            "followups": ["Which columns have missing values?", "What is the overall data quality?"],
            "is_llm": False,
        }

    # ── 6. Grouped Breakdown / Aggregations (e.g. "Sales by Region", "Income by Gender") ──
    if " by " in q_lower or " across " in q_lower or " per " in q_lower or " grouped by " in q_lower:
        matched_cols = _find_all_matching_columns(q, all_cols)
        matched_num = [c for c in matched_cols if c in numeric_cols]
        matched_cat = [c for c in matched_cols if c in cat_cols]

        if not matched_num and numeric_cols:
            matched_num = [numeric_cols[0]]
        if not matched_cat and cat_cols:
            matched_cat = [cat_cols[0]]

        if matched_num and matched_cat:
            num_c = matched_num[0]
            cat_c = matched_cat[0]
            try:
                grouped = df.groupby(cat_c)[num_c].agg(["mean", "sum", "count"]).reset_index()
                grouped = grouped.sort_values("mean", ascending=False)
                top_3 = grouped.head(3)
                lines = []
                for _, row in top_3.iterrows():
                    lines.append(f"• **{row[cat_c]}**: Average = **{row['mean']:,.2f}** | Total = **{row['sum']:,.2f}** (n={int(row['count']):,})")

                top_cat = top_3.iloc[0][cat_c]
                top_avg = top_3.iloc[0]['mean']

                answer = (
                    f"Breakdown of **'{num_c}'** across **'{cat_c}'**:\n\n"
                    f"Highest average is in **{top_cat}** with an average of **{top_avg:,.2f}**.\n\n"
                    f"**Top Groups:**\n" + "\n".join(lines)
                )
                return {
                    "answer": answer,
                    "source": f"Grouped Aggregation ({num_c} by {cat_c})",
                    "followups": [f"What is the distribution of '{num_c}'?", f"What are the top values in '{cat_c}'?", "What are the strongest correlations?"],
                    "is_llm": False,
                    "table": grouped.head(10)
                }
            except Exception:
                pass

    # ── 7. Top / Maximum / Highest Extremes ───────────────────────────────────
    if any(kw in q_lower for kw in ["highest", "maximum", "max ", "max of", "top ", "most expensive", "cheapest", "lowest", "minimum", "min ", "min of", "best", "worst", "oldest", "youngest"]):
        is_lowest = any(kw in q_lower for kw in ["lowest", "minimum", "min ", "cheapest", "worst", "youngest"])
        matched_col = _find_best_matching_column(q, numeric_cols)
        if matched_col:
            s = df[matched_col].dropna()
            if not s.empty:
                extreme_val = s.min() if is_lowest else s.max()
                extreme_label = "Minimum (Lowest)" if is_lowest else "Maximum (Highest)"
                idx = s.idxmin() if is_lowest else s.idxmax()
                record = df.loc[idx]

                rec_summary = ", ".join([f"{col}: {record[col]}" for col in df.columns[:4]])

                answer = (
                    f"The **{extreme_label}** for **'{matched_col}'** is **{extreme_val:,.2f}**.\n\n"
                    f"• **Full Record Context**: {rec_summary}\n"
                    f"• **Mean (Average)**: {s.mean():,.2f}\n"
                    f"• **Median**: {s.median():,.2f}\n"
                    f"• **Total Non-Null Observations**: {len(s):,}"
                )
                return {
                    "answer": answer,
                    "source": f"Extremes Analysis ({matched_col})",
                    "followups": [f"What is the distribution of '{matched_col}'?", f"Are there outliers in '{matched_col}'?", "What is the strongest correlation?"],
                    "is_llm": False
                }

    # ── 8. Specific Column Descriptive Statistics ─────────────────────────────
    matched_num_col = _find_best_matching_column(q, numeric_cols)
    if matched_num_col and any(kw in q_lower for kw in ["average", "mean", "median", "describe", "summary", "stats", "distribution", "variance", "std"]):
        s = df[matched_num_col].dropna()
        if not s.empty:
            answer = (
                f"Statistical Profile for **'{matched_num_col}'**:\n\n"
                f"• **Mean (Average)**: **{s.mean():,.2f}**\n"
                f"• **Median**: **{s.median():,.2f}**\n"
                f"• **Std Dev**: **{s.std():,.2f}**\n"
                f"• **Range**: [{s.min():,.2f} to {s.max():,.2f}]\n"
                f"• **25% – 75% IQR**: [{s.quantile(0.25):,.2f} – {s.quantile(0.75):,.2f}]\n"
                f"• **Observations**: {len(s):,} non-null values"
            )
            return {
                "answer": answer,
                "source": f"Descriptive Statistics ({matched_num_col})",
                "followups": [f"Are there outliers in '{matched_num_col}'?", f"What is the strongest correlation with '{matched_num_col}'?"],
                "is_llm": False
            }

    # ── 9. Categorical Cardinality & Top Frequencies ──────────────────────────
    matched_cat_col = _find_best_matching_column(q, cat_cols)
    if matched_cat_col:
        s = df[matched_cat_col].dropna()
        if not s.empty:
            v_counts = s.value_counts()
            top_5 = v_counts.head(5)
            lines = [f"• **{cat}**: {cnt:,} occurrences ({(cnt/len(df)*100):.1f}%)" for cat, cnt in top_5.items()]

            answer = (
                f"Categorical Profile for **'{matched_cat_col}'**:\n\n"
                f"• **Distinct Categories**: **{s.nunique():,}**\n"
                f"• **Most Common Value**: **{top_5.index[0]}** ({top_5.iloc[0]:,} times)\n\n"
                f"**Top Categories:**\n" + "\n".join(lines)
            )
            return {
                "answer": answer,
                "source": f"Frequency Analysis ({matched_cat_col})",
                "followups": [f"How does '{matched_cat_col}' relate to numeric features?", "What are the other columns?"],
                "is_llm": False
            }

    # ── 10. Correlations & Relationships ─────────────────────────────────────
    if any(kw in q_lower for kw in ["correlation", "correlated", "relationship", "relation", "driver", "factors"]):
        if len(numeric_cols) < 2:
            answer = "Correlation analysis requires at least 2 numeric features. This dataset has fewer."
        else:
            corr_matrix = compute_correlation_matrix(df, numeric_cols[:10])
            pos, neg = extract_strongest_correlations(corr_matrix, top_n=3)
            lines = []
            if pos:
                for p in pos[:2]:
                    lines.append(f"• **Positive**: '{p['Variable 1']}' <-> '{p['Variable 2']}' (r = **{p['Correlation (r)']:.2f}**, {p['Strength']})")
            if neg:
                for p in neg[:2]:
                    lines.append(f"• **Negative**: '{p['Variable 1']}' <-> '{p['Variable 2']}' (r = **{p['Correlation (r)']:.2f}**, {p['Strength']})")

            answer = "Strongest statistical relationships in this dataset:\n\n" + ("\n".join(lines) if lines else "No significant correlations found.")
        return {
            "answer": answer,
            "source": "Correlation Engine",
            "followups": ["Which columns have outliers?", "What is the overall data quality?", "What are the key drivers?"],
            "is_llm": False,
        }

    # ── 11. Outliers & Anomalies ─────────────────────────────────────────────
    if any(kw in q_lower for kw in ["outlier", "anomaly", "anomalies", "extreme", "abnormal"]):
        if not numeric_cols:
            answer = "Outlier detection requires numeric columns. None were found in this dataset."
        else:
            outlier_data = compute_iqr_outliers(df, numeric_cols[:8])
            total = outlier_data.get("total_outliers", 0)
            if total == 0:
                answer = "No IQR outliers detected across numeric columns using the standard 1.5× IQR fence rule."
            else:
                lines = []
                for col, info in outlier_data.get("column_outliers", {}).items():
                    if info["outlier_count"] > 0:
                        lines.append(f"• **{col}**: {info['outlier_count']:,} outliers ({info['outlier_pct']:.1f}% rate) outside [{info['lower_bound']:,.1f}, {info['upper_bound']:,.1f}]")
                answer = f"Detected **{total:,} potential outlier values** across numeric features:\n\n" + "\n".join(lines)
        return {
            "answer": answer,
            "source": "Outlier Detection Engine (IQR)",
            "followups": ["What is the strongest correlation?", "What is the overall data quality?"],
            "is_llm": False,
        }

    # ── 12. Sample Data / Preview ────────────────────────────────────────────
    if any(kw in q_lower for kw in ["sample", "preview", "first 5", "first 10", "head", "show data", "table"]):
        answer = f"Here is a preview of the first 5 records in **'{dataset_name}'**:"
        return {
            "answer": answer,
            "source": "Dataset Preview",
            "followups": ["What are the column names?", "What is the overall data quality?"],
            "is_llm": False,
            "table": df.head(5)
        }

    # ── 13. Comprehensive Default / Automated Insights ───────────────────────
    insights = generate_eda_insights(df, metadata)
    if insights:
        top = insights[:4]
        lines = [f"• **{ins.get('title', 'Finding')}**: {ins.get('observation', '')}" for ins in top if "observation" in ins]
        answer = (
            f"Here are the top **analytical observations** extracted from **'{dataset_name}'**:\n\n"
            + "\n\n".join(lines) + "\n\n"
            f"*(Tip: Enter a Google Gemini API Key in AI Settings above to ask free-form questions in any language!)*"
        )
    else:
        cat_example = cat_cols[0] if cat_cols else 'categories'
        num_example = numeric_cols[0] if numeric_cols else 'values'
        answer = (
            f"Dataset Summary for **'{dataset_name}'**:\n\n"
            f"• **Records**: {len(df):,} rows × {len(df.columns)} columns\n"
            f"• **Features**: {', '.join(df.columns[:8])}\n"
            f"• **Completeness**: {100 - metadata.get('missing_percentage', 0.0):.1f}%\n\n"
            f"Try asking about specific columns (e.g. *'What is the highest {num_example}?'* or *'Breakdown of {cat_example}'*)."
        )

    return {
        "answer": answer,
        "source": "Automated Insights Engine",
        "followups": [
            f"What is the average {numeric_cols[0]}?" if numeric_cols else "What are the columns?",
            "What are the strongest correlations?",
            "What is the overall data quality?"
        ],
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

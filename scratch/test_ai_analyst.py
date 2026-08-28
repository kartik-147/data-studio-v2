import sys
import os
import re
sys.path.insert(0, os.path.abspath("."))
import pandas as pd
import numpy as np
from modules.llm_service import ask_ai_analyst, _answer_question_deterministic
from modules.data_loader import create_dataset_metadata

# Create realistic test dataframe
data = {
    "Customer_ID": [f"CUST-{1000+i}" for i in range(20)],
    "Age": [25, 34, 45, 29, 52, 38, 41, 23, 61, 30, 48, 55, 33, 27, 39, 44, 50, 28, 36, 42],
    "Gender": ["Male", "Female", "Female", "Male", "Female", "Male", "Female", "Male", "Female", "Male"] * 2,
    "Income": [55000, 78000, 112000, 64000, 145000, 89000, 95000, 48000, 160000, 72000, 125000, 138000, 81000, 62000, 91000, 105000, 130000, 67000, 86000, 99000],
    "Location": ["New York", "Austin", "Seattle", "Chicago", "Austin"] * 4
}
df = pd.DataFrame(data)
metadata = create_dataset_metadata(df, "test_customers.csv", "CSV")

print(f"Dataset initialized: {df.shape[0]} rows, {df.shape[1]} columns")

test_queries = [
    "hii",
    "hello",
    "help",
    "How many rows and columns are in this dataset?",
    "What are the column names and data types?",
    "What is the average Age?",
    "What is the highest Income?",
    "Show Income by Location",
    "What are the strongest correlations?",
    "Are there any missing values?",
    "Tell me an overview of this dataset",
    "Lowest age in the data",
    "Distribution of Gender"
]

print("\n--- Running Deterministic Natural Language Engine Tests ---")
for i, q in enumerate(test_queries, 1):
    res = ask_ai_analyst(q, df, metadata)
    print(f"\n[Test {i}] Q: {q}")
    print(f"Source: {res['source']}")
    ans_safe = res['answer'][:120].encode('ascii', 'replace').decode('ascii')
    print(f"Answer snippet: {ans_safe}...")
    if "table" in res and res["table"] is not None:
        print(f"Attached Table Shape: {res['table'].shape}")
    print("Follow-ups:", res.get("followups", []))
    assert res["answer"] and len(res["answer"]) > 10, f"Query '{q}' returned empty answer!"

from modules.ai_analyst import _run_investigation, _build_data_story

print("\n--- Testing Root-Cause Investigation ---")
inv_res = _run_investigation(df, target="Income", dimension="Location", time_col=None)
print("Investigation Target:", inv_res["target"])
print("Target Mean:", inv_res["target_mean"])
print("Confidence:", inv_res["confidence"])
assert inv_res["group_df"] is not None
print("Explanations:", inv_res["explanations"])

print("\n--- Testing Data Story Generation & Text Cleaning ---")
chapters = _build_data_story(df, metadata)
assert len(chapters) == 7, f"Expected 7 chapters, got {len(chapters)}"
for ch in chapters:
    print(f"[{ch['num']}] {ch['title']} ({len(ch['lines'])} lines)")
    for line in ch['lines']:
        clean_l = re.sub(r"<[^>]+>", "", line)
        assert len(clean_l) > 0

print("\n>>> ALL AI ANALYST, INVESTIGATION, AND DATA STORY TESTS PASSED SUCCESSFULLY! <<<")

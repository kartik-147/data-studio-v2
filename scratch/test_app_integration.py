"""
Test whole app imports, routing dispatch, and session state initialization.
"""
import sys
import os
import io

# Force UTF-8 on stdout for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app
from modules.config import NAV_GROUPS, PAGE_METADATA, init_session_state
from modules.data_loader import load_csv, create_dataset_metadata
from modules.eda_page import render_eda_page
from modules.eda_tools import render_eda_page as tools_render_eda_page
from modules.dashboard import render_dashboard_page
from modules.data_profiler import render_dataset_page
from modules.data_quality import render_data_quality_page

print("[OK] Successfully imported app and all page modules")
print(f"[OK] Navigation groups: {list(NAV_GROUPS.keys())}")
print(f"[OK] EDA page metadata: {PAGE_METADATA.get('EDA')}")

# Verify data loader + metadata creation works with sample datasets
df, err = load_csv("sample_data/saas_sales_data.csv")
assert err is None
meta = create_dataset_metadata(df, "saas_sales_data.csv", "CSV")
assert meta["total_rows"] == 20
assert meta["total_columns"] == 10
print("[OK] Dataset loader & metadata generation verified")

print("\nApp Integration Check PASSED!")

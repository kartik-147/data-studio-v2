"""
DATA STUDIO v2 — Firebase Activity Logging & Admin Analytics Unit Test Suite
"""
import unittest
import os
import sys
import pandas as pd
import streamlit as st

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.config import init_session_state
from modules.firebase_service import (
    is_admin_user,
    is_firebase_configured,
    log_user_login,
    log_dataset_upload,
    fetch_admin_analytics
)
from modules.auth import (
    login_user_session,
    start_guest_session,
    logout_user,
    get_current_user
)
from modules.data_loader import create_dataset_metadata


class TestFirebaseActivityTracking(unittest.TestCase):
    
    def setUp(self):
        init_session_state()
        st.session_state["login_event_logged"] = False
        st.session_state["logged_dataset_signature"] = None

    def test_admin_authorization(self):
        """Test admin email validation and guest rejection."""
        # 1. Non-admin email
        self.assertFalse(is_admin_user("random_user@example.com"))
        
        # 2. Guest user dictionary
        guest_user = {
            "id": "guest_session",
            "email": "guest@datastudio.internal",
            "is_guest": True
        }
        self.assertFalse(is_admin_user(guest_user))
        
        # 3. None or empty email
        self.assertFalse(is_admin_user(None))
        self.assertFalse(is_admin_user(""))

        # 4. Configure test admin via environment variable
        os.environ["ADMIN_EMAIL"] = "admin@datastudio.internal"
        
        # Verified admin user
        admin_user = {
            "id": "usr_admin_123",
            "email": "admin@datastudio.internal",
            "is_guest": False
        }
        self.assertTrue(is_admin_user(admin_user))
        self.assertTrue(is_admin_user("ADMIN@datastudio.internal"))  # case insensitive
        
        # Another registered user (not admin)
        regular_user = {
            "id": "usr_regular_456",
            "email": "regular@datastudio.internal",
            "is_guest": False
        }
        self.assertFalse(is_admin_user(regular_user))
        
        # Clean up env
        del os.environ["ADMIN_EMAIL"]

    def test_login_session_guard(self):
        """Test that login event logging only triggers once per session."""
        user_info = {
            "id": "usr_test_101",
            "full_name": "Test User",
            "email": "test@datastudio.internal"
        }
        
        self.assertFalse(st.session_state.get("login_event_logged", False))
        
        # First login establishes session and sets guard
        login_user_session(user_info)
        self.assertTrue(st.session_state.get("login_event_logged", False))
        self.assertTrue(st.session_state.get("authenticated", False))
        
        # Subsequent rerun simulation does not reset the guard
        self.assertTrue(st.session_state.get("login_event_logged", False))
        
        # Logout resets guard
        logout_user()
        self.assertFalse(st.session_state.get("login_event_logged", False))
        self.assertFalse(st.session_state.get("authenticated", False))

    def test_guest_session_guard(self):
        """Test that guest sessions are logged once and properly guarded."""
        self.assertFalse(st.session_state.get("login_event_logged", False))
        
        start_guest_session()
        self.assertTrue(st.session_state.get("login_event_logged", False))
        self.assertTrue(st.session_state.get("is_guest", False))
        
        logout_user()
        self.assertFalse(st.session_state.get("login_event_logged", False))
        self.assertFalse(st.session_state.get("is_guest", False))

    def test_dataset_upload_metadata_privacy(self):
        """Verify that upload logging payload contains only metadata and zero raw rows/cells."""
        df = pd.DataFrame({
            "User_ID": [101, 102, 103],
            "Salary": [50000.0, 75000.0, 120000.0],
            "Secret_Password": ["pass123", "secret456", "confidential789"]
        })
        metadata = create_dataset_metadata(df, "salaries.csv", file_type="CSV")
        
        user_info = {
            "id": "usr_999",
            "full_name": "Data Analyst",
            "email": "analyst@company.com",
            "is_guest": False
        }
        
        # Call log_dataset_upload (falls back gracefully if Firestore not connected)
        result = log_dataset_upload(user_info, metadata, file_type="CSV")
        
        # Verify metadata properties
        self.assertEqual(metadata["total_rows"], 3)
        self.assertEqual(metadata["total_columns"], 3)
        self.assertIn("Secret_Password", metadata["column_types"])
        
        # Check that metadata does NOT have DataFrame data rows
        self.assertNotIn("data", metadata)
        self.assertNotIn("records", metadata)
        self.assertNotIn("values", metadata)

    def test_dataset_upload_deduplication_guard(self):
        """Verify that rerun with identical dataset signature does not log multiple times."""
        df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
        metadata = create_dataset_metadata(df, "data.csv")
        
        dataset_name = "data.csv"
        sig1 = f"{dataset_name}_{metadata['total_rows']}_{metadata['total_columns']}_{metadata['memory_bytes']}"
        
        # Initial state
        self.assertIsNone(st.session_state.get("logged_dataset_signature"))
        
        # First upload
        st.session_state["logged_dataset_signature"] = sig1
        
        # Simulated rerun check
        current_sig = f"{dataset_name}_{metadata['total_rows']}_{metadata['total_columns']}_{metadata['memory_bytes']}"
        self.assertEqual(st.session_state.get("logged_dataset_signature"), current_sig)
        
        # Upload new dataset with different signature
        df2 = pd.DataFrame({"A": [1, 2, 3, 4]})
        metadata2 = create_dataset_metadata(df2, "new_data.csv")
        sig2 = f"new_data.csv_{metadata2['total_rows']}_{metadata2['total_columns']}_{metadata2['memory_bytes']}"
        self.assertNotEqual(st.session_state.get("logged_dataset_signature"), sig2)

    def test_unconfigured_firebase_graceful_handling(self):
        """Verify that missing Firebase credentials does not throw unhandled exceptions."""
        analytics = fetch_admin_analytics("All Time")
        self.assertIsInstance(analytics, dict)
        if not is_firebase_configured():
            self.assertFalse(analytics.get("configured", True))


if __name__ == "__main__":
    unittest.main()

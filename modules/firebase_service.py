"""
DATA STUDIO v2 — Firebase Activity Logging & Admin Service
=============================================================================
Privacy-first cloud activity tracking using Firebase Firestore (Admin SDK).
Strictly logs dataset metadata (schema, counts, types) without storing raw data.
"""
from typing import Optional, Dict, Any, List, Tuple
import os
import datetime
import uuid
import streamlit as st

from modules.config import APP_VERSION

# Global flag to track Firebase module availability
FIREBASE_AVAILABLE = False
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False


# =============================================================================
# FIREBASE ADMIN SDK INITIALIZATION (SINGLETON)
# =============================================================================

def get_firestore_client():
    """
    Safely initialize and retrieve the Firestore client singleton.
    Loads credentials securely from st.secrets['firebase'] or local serviceAccountKey.json.
    Returns None gracefully if credentials are not configured or SDK is unavailable.
    """
    if not FIREBASE_AVAILABLE:
        return None

    try:
        # If Firebase app is already initialized, return existing client
        if firebase_admin._apps:
            return firestore.client()

        cred = None

        # Safely attempt to read Streamlit secrets
        try:
            if hasattr(st, "secrets") and len(st.secrets) > 0:
                if "firebase" in st.secrets:
                    firebase_config = dict(st.secrets["firebase"])
                    # Format escaped newlines in private key if present
                    if "private_key" in firebase_config and isinstance(firebase_config["private_key"], str):
                        firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")
                    cred = credentials.Certificate(firebase_config)
                elif "firebase_service_account" in st.secrets:
                    account_info = st.secrets["firebase_service_account"]
                    if isinstance(account_info, dict):
                        cred = credentials.Certificate(account_info)
        except Exception:
            # StreamlitSecretNotFoundError or parsing error when no secrets exist
            pass

        # Check for local serviceAccountKey.json file (development fallback)
        if cred is None and os.path.exists("serviceAccountKey.json"):
            try:
                cred = credentials.Certificate("serviceAccountKey.json")
            except Exception:
                pass

        if cred is not None:
            firebase_admin.initialize_app(cred)
            return firestore.client()

        return None
    except Exception as e:
        # Graceful failure without crashing the host application
        print(f"[DataStudio Warning] Firebase initialization failed: {e}")
        return None


def is_firebase_configured() -> bool:
    """Return True if Firestore client can be successfully obtained."""
    try:
        return get_firestore_client() is not None
    except Exception:
        return False


# =============================================================================
# ADMIN AUTHORIZATION
# =============================================================================

def get_configured_admin_email() -> Optional[str]:
    """Retrieve configured admin email from Streamlit secrets or environment."""
    try:
        if hasattr(st, "secrets") and len(st.secrets) > 0:
            if "admin" in st.secrets and "email" in st.secrets["admin"]:
                return str(st.secrets["admin"]["email"]).strip().lower()
            if "ADMIN_EMAIL" in st.secrets:
                return str(st.secrets["ADMIN_EMAIL"]).strip().lower()
    except Exception:
        pass
    
    return os.environ.get("ADMIN_EMAIL", "").strip().lower() or None


def is_admin_user(user_or_email: Any) -> bool:
    """
    Strict server-side validation: Check if active user has administrative privileges.
    Guest sessions are NEVER granted admin access.
    """
    if not user_or_email:
        return False

    # Extract user attributes if dictionary passed
    if isinstance(user_or_email, dict):
        if user_or_email.get("is_guest", False):
            return False
        email = str(user_or_email.get("email", "")).strip().lower()
    else:
        email = str(user_or_email).strip().lower()

    if not email:
        return False

    admin_email = get_configured_admin_email()
    if not admin_email:
        return False

    return email == admin_email


# =============================================================================
# USER LOGIN TRACKING
# =============================================================================

def log_user_login(user_info: Dict[str, Any]) -> bool:
    """
    Record user login event to Firestore collections 'users' and 'login_logs'.
    Protected by session guards in the caller to prevent duplicate logs on rerun.
    """
    db = get_firestore_client()
    if db is None:
        return False

    try:
        user_id = user_info.get("id", str(uuid.uuid4()))
        full_name = user_info.get("full_name", "User")
        email = user_info.get("email", "")
        is_guest = user_info.get("is_guest", False)
        auth_provider = "guest" if is_guest else "email_password"
        
        now = datetime.datetime.now(datetime.timezone.utc)
        now_str = now.isoformat()

        # 1. Update 'users' collection for registered accounts
        if not is_guest and email:
            user_doc_ref = db.collection("users").document(str(user_id))
            user_doc = user_doc_ref.get()
            
            user_data = {
                "user_id": str(user_id),
                "full_name": full_name,
                "email": email,
                "auth_provider": auth_provider,
                "last_login_at": now_str
            }
            if not user_doc.exists:
                user_data["created_at"] = now_str
                user_doc_ref.set(user_data)
            else:
                user_doc_ref.update({
                    "last_login_at": now_str,
                    "full_name": full_name,
                    "email": email
                })

        # 2. Add event to 'login_logs' collection
        log_data = {
            "log_id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "full_name": full_name,
            "email": email if not is_guest else "guest@session",
            "auth_provider": auth_provider,
            "login_time": now_str,
            "app_version": APP_VERSION
        }
        db.collection("login_logs").add(log_data)
        return True
    except Exception as e:
        print(f"[DataStudio Warning] Failed to log login event to Firestore: {e}")
        return False


# =============================================================================
# DATASET UPLOAD TRACKING (METADATA ONLY — PRIVACY FIRST)
# =============================================================================

def log_dataset_upload(
    user_info: Dict[str, Any],
    metadata: Dict[str, Any],
    file_type: str = "CSV"
) -> bool:
    """
    Record dataset upload structural metadata in 'dataset_uploads' collection.
    PRIVACY GUARANTEE: NEVER stores raw dataset values, rows, or cells.
    """
    db = get_firestore_client()
    if db is None:
        return False

    try:
        user_id = user_info.get("id", "guest")
        full_name = user_info.get("full_name", "Guest")
        email = user_info.get("email", "guest@session")
        is_guest = user_info.get("is_guest", False)
        auth_provider = "guest" if is_guest else "email_password"

        dataset_name = metadata.get("filename", "dataset")
        extension = dataset_name.split(".")[-1].lower() if "." in dataset_name else ""

        # Extract clean column types map (lowercase for consistency)
        raw_types = metadata.get("column_types", {})
        clean_types = {str(k): str(v).lower() for k, v in raw_types.items()}
        type_counts = metadata.get("type_counts", {})

        memory_bytes = metadata.get("memory_bytes", 0)
        memory_mb = round(memory_bytes / (1024 * 1024), 3) if memory_bytes else 0.0

        now = datetime.datetime.now(datetime.timezone.utc)
        now_str = now.isoformat()

        upload_payload = {
            "upload_id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "full_name": full_name,
            "email": email,
            "auth_provider": auth_provider,
            "dataset_name": dataset_name,
            "file_type": file_type,
            "file_extension": extension,
            "file_size_bytes": memory_bytes,
            "file_size_mb": memory_mb,
            "row_count": int(metadata.get("total_rows", 0)),
            "column_count": int(metadata.get("total_columns", 0)),
            "column_names": list(clean_types.keys()),
            "column_types": clean_types,
            "numeric_column_count": int(type_counts.get("Numeric", 0)),
            "categorical_column_count": int(type_counts.get("Categorical", 0)),
            "datetime_column_count": int(type_counts.get("Date/Time", 0)),
            "total_missing_values": int(metadata.get("total_missing_cells", 0)),
            "missing_percentage": round(float(metadata.get("missing_percentage", 0.0)), 2),
            "upload_time": now_str
        }

        db.collection("dataset_uploads").add(upload_payload)
        return True
    except Exception as e:
        print(f"[DataStudio Warning] Failed to log dataset metadata to Firestore: {e}")
        return False


# =============================================================================
# ADMIN ANALYTICS QUERY & AGGREGATION ENGINE
# =============================================================================

def _parse_iso_timestamp(ts_val: Any) -> Optional[datetime.datetime]:
    """Parse various Firestore timestamp representations into timezone-aware UTC datetime."""
    if not ts_val:
        return None
    try:
        if isinstance(ts_val, datetime.datetime):
            if ts_val.tzinfo is None:
                return ts_val.replace(tzinfo=datetime.timezone.utc)
            return ts_val
        if isinstance(ts_val, str):
            # Parse ISO string
            dt = datetime.datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                return dt.replace(tzinfo=datetime.timezone.utc)
            return dt
    except Exception:
        pass
    return None


def fetch_admin_analytics(date_filter: str = "All Time") -> Dict[str, Any]:
    """
    Retrieve and compute administrative metrics, distributions, and activity feeds.
    Applies date filtering on demand: 'Today', 'Last 7 Days', 'Last 30 Days', 'All Time'.
    """
    db = get_firestore_client()
    if db is None:
        return {"configured": False}

    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff_time: Optional[datetime.datetime] = None

    if date_filter == "Today":
        cutoff_time = datetime.datetime(now.year, now.month, now.day, tzinfo=datetime.timezone.utc)
    elif date_filter == "Last 7 Days":
        cutoff_time = now - datetime.timedelta(days=7)
    elif date_filter == "Last 30 Days":
        cutoff_time = now - datetime.timedelta(days=30)
    else:
        cutoff_time = None

    try:
        # 1. Fetch Users
        users_docs = db.collection("users").stream()
        all_users = [doc.to_dict() for doc in users_docs]

        # 2. Fetch Login Logs
        login_docs = db.collection("login_logs").stream()
        all_logins = [doc.to_dict() for doc in login_docs]

        # 3. Fetch Dataset Uploads
        upload_docs = db.collection("dataset_uploads").stream()
        all_uploads = [doc.to_dict() for doc in upload_docs]

        # Apply cutoff filters to logs & uploads
        filtered_logins = []
        today_logins_count = 0
        today_start = datetime.datetime(now.year, now.month, now.day, tzinfo=datetime.timezone.utc)

        for l in all_logins:
            dt = _parse_iso_timestamp(l.get("login_time"))
            if dt and dt >= today_start:
                today_logins_count += 1
            if cutoff_time is None or (dt and dt >= cutoff_time):
                filtered_logins.append(l)

        filtered_uploads = []
        today_uploads_count = 0
        for u in all_uploads:
            dt = _parse_iso_timestamp(u.get("upload_time"))
            if dt and dt >= today_start:
                today_uploads_count += 1
            if cutoff_time is None or (dt and dt >= cutoff_time):
                filtered_uploads.append(u)

        # Unique active users during filtered period
        active_emails = set()
        for l in filtered_logins:
            e = l.get("email")
            if e and e != "guest@session":
                active_emails.add(e)
        for u in filtered_uploads:
            e = u.get("email")
            if e and e != "guest@session":
                active_emails.add(e)

        # Format / File Type analytics
        file_type_counts: Dict[str, int] = {}
        total_rows_sum = 0
        total_cols_sum = 0
        total_size_mb_sum = 0.0
        column_type_frequencies: Dict[str, int] = {}

        for u in filtered_uploads:
            ft = u.get("file_type", "CSV")
            file_type_counts[ft] = file_type_counts.get(ft, 0) + 1
            total_rows_sum += u.get("row_count", 0)
            total_cols_sum += u.get("column_count", 0)
            total_size_mb_sum += u.get("file_size_mb", 0.0)

            for col_type in u.get("column_types", {}).values():
                c_clean = str(col_type).capitalize()
                column_type_frequencies[c_clean] = column_type_frequencies.get(c_clean, 0) + 1

        upload_count = len(filtered_uploads)
        avg_rows = int(total_rows_sum / upload_count) if upload_count > 0 else 0
        avg_cols = int(total_cols_sum / upload_count) if upload_count > 0 else 0
        avg_size_mb = round(total_size_mb_sum / upload_count, 2) if upload_count > 0 else 0.0

        # Build chronological recent activity timeline (combined logins & uploads)
        activity_items = []
        for l in filtered_logins:
            dt = _parse_iso_timestamp(l.get("login_time"))
            is_g = (l.get("auth_provider") == "guest")
            u_name = l.get("full_name", "User")
            activity_items.append({
                "timestamp": dt or now,
                "timestamp_str": l.get("login_time", ""),
                "user": u_name,
                "email": l.get("email", ""),
                "action": "Guest Demo Started" if is_g else "User Logged In",
                "details": f"Session authenticated via {l.get('auth_provider', 'email_password')}",
                "type": "login",
                "is_guest": is_g
            })

        for u in filtered_uploads:
            dt = _parse_iso_timestamp(u.get("upload_time"))
            u_name = u.get("full_name", "User")
            ds_name = u.get("dataset_name", "dataset")
            r_cnt = u.get("row_count", 0)
            c_cnt = u.get("column_count", 0)
            activity_items.append({
                "timestamp": dt or now,
                "timestamp_str": u.get("upload_time", ""),
                "user": u_name,
                "email": u.get("email", ""),
                "action": f"Uploaded {ds_name}",
                "details": f"{r_cnt:,} rows × {c_cnt} cols ({u.get('file_type', 'CSV')})",
                "type": "upload",
                "is_guest": (u.get("auth_provider") == "guest")
            })

        # Sort activity timeline descending
        activity_items.sort(key=lambda x: x["timestamp"], reverse=True)

        # Build user upload counts map
        user_upload_counts: Dict[str, int] = {}
        for u in all_uploads:
            e = u.get("email")
            if e:
                user_upload_counts[e] = user_upload_counts.get(e, 0) + 1

        # Enrich all_users with upload counts and parse timestamps
        enriched_users = []
        for usr in all_users:
            u_email = usr.get("email", "")
            enriched_users.append({
                "user_id": usr.get("user_id", ""),
                "full_name": usr.get("full_name", "User"),
                "email": u_email,
                "auth_provider": usr.get("auth_provider", "email_password"),
                "created_at": usr.get("created_at", "N/A"),
                "last_login_at": usr.get("last_login_at", "N/A"),
                "upload_count": user_upload_counts.get(u_email, 0)
            })
        enriched_users.sort(key=lambda x: x.get("last_login_at", ""), reverse=True)

        # Sort upload history descending
        sorted_uploads = sorted(filtered_uploads, key=lambda x: x.get("upload_time", ""), reverse=True)

        return {
            "configured": True,
            "kpis": {
                "total_registered_users": len(all_users),
                "total_login_events": len(filtered_logins),
                "total_dataset_uploads": len(filtered_uploads),
                "unique_active_users": len(active_emails),
                "today_logins": today_logins_count,
                "today_uploads": today_uploads_count,
                "avg_rows": avg_rows,
                "avg_cols": avg_cols,
                "avg_size_mb": avg_size_mb
            },
            "file_type_counts": file_type_counts,
            "column_type_frequencies": column_type_frequencies,
            "recent_activity": activity_items[:50],  # Top 50 recent events
            "users": enriched_users,
            "uploads": sorted_uploads
        }
    except Exception as e:
        print(f"[DataStudio Warning] Error querying Firestore analytics: {e}")
        return {"configured": True, "error": str(e)}

"""
DATA STUDIO v2 — Admin Analytics & Activity Logging Dashboard
=============================================================================
Administrative analytics view providing cloud-backed insights into user logins,
session activity, and dataset metadata uploads. Strictly accessible by admin.
"""
from typing import Dict, Any, List, Optional
import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.auth import get_current_user
from modules.firebase_service import (
    is_admin_user,
    is_firebase_configured,
    fetch_admin_analytics,
    get_configured_admin_email
)
from modules.ui_components import (
    render_page_header,
    render_section_header,
    render_metric_card,
    render_notification,
    render_empty_state,
    get_icon_svg
)


def _apply_theme_to_fig(fig: go.Figure, theme: str = "Dark", height: int = 280) -> go.Figure:
    """Apply consistent design system theme to Plotly figures."""
    is_light = (theme.lower() == "light")
    text_color = "#0f172a" if is_light else "#f8fafc"
    subtext_color = "#64748b" if is_light else "#94a3b8"
    grid_color = "#e2e8f0" if is_light else "#1e293b"

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=text_color, size=11),
        margin=dict(l=20, r=20, t=30, b=20),
        height=height,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=subtext_color, size=10)
        )
    )
    return fig


def render_admin_analytics_page() -> None:
    """Render the protected Admin Analytics Dashboard."""
    current_theme = st.session_state.get("theme", "Dark")
    user = get_current_user()

    # 1. Server-side Authorization Check
    if not is_admin_user(user):
        render_page_header(
            title="Admin Analytics",
            subtitle="Restricted Administrative Control Panel",
            icon="shield"
        )
        render_notification(
            title="Access Denied",
            message="You do not have administrative privileges to view this page. Please sign in with an authorized admin account.",
            variant="error"
        )
        st.stop()

    # 2. Standardized Page Header
    render_page_header(
        title="Admin Analytics",
        subtitle=f"Cloud activity logs and dataset ingestion metrics · Admin: {user.get('email')}",
        icon="shield-check"
    )

    # 3. Check Firebase Configuration
    if not is_firebase_configured():
        render_notification(
            title="Activity Database Not Configured",
            message="Firebase Firestore is not yet initialized. Configure your Firebase credentials in Streamlit secrets to activate activity tracking.",
            variant="warning"
        )
        _render_setup_guide()
        return

    # 4. Filter Controls & Refresh Bar
    col_filters, col_refresh = st.columns([7, 3])
    with col_filters:
        date_filter = st.radio(
            "Date Range Filter",
            options=["Today", "Last 7 Days", "Last 30 Days", "All Time"],
            index=3,
            horizontal=True,
            label_visibility="collapsed",
            key="admin_date_filter_radio"
        )
    with col_refresh:
        if st.button("Refresh Analytics", key="admin_refresh_data_btn", use_container_width=True):
            st.toast("Analytics synchronized from Firestore.")
            st.rerun()

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 5. Fetch Analytics Data
    with st.spinner("Querying activity records from Firestore..."):
        data = fetch_admin_analytics(date_filter=date_filter)

    if not data.get("configured") or "error" in data:
        err_msg = data.get("error", "Unable to retrieve analytics records.")
        render_notification(
            title="Query Error",
            message=f"Firestore returned an error while querying logs: {err_msg}",
            variant="error"
        )
        return

    kpis = data.get("kpis", {})

    # 6. Admin KPI Grid (6 Top Metrics)
    _render_kpi_grid(kpis)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 7. Tabbed Logs, Statistics & Audit Tables (5 Sections)
    tab_activity, tab_users, tab_uploads, tab_stats, tab_system = st.tabs([
        "RECENT ACTIVITY",
        "USER DIRECTORY",
        "DATASET UPLOADS",
        "DATASET STATISTICS",
        "SYSTEM OVERVIEW"
    ])

    with tab_activity:
        _render_tab_activity(data.get("recent_activity", []))

    with tab_users:
        _render_tab_users(data.get("users", []))

    with tab_uploads:
        _render_tab_uploads(data.get("uploads", []))

    with tab_stats:
        _render_tab_dataset_statistics(data, current_theme)

    with tab_system:
        _render_tab_system_overview(data)


# =============================================================================
# SECTION RENDERERS
# =============================================================================

def _render_kpi_grid(kpis: Dict[str, Any]) -> None:
    """Render top 6 administrative KPI cards."""
    render_section_header(
        title="Administrative KPIs",
        subtitle="Platform health, user volume, and data ingestion metrics."
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        render_metric_card(
            label="Total Registered Users",
            value=f"{kpis.get('total_registered_users', 0):,}",
            status="Accounts",
            icon="users"
        )
    with c2:
        render_metric_card(
            label="Total Login Events",
            value=f"{kpis.get('total_login_events', 0):,}",
            status="Sessions",
            icon="activity"
        )
    with c3:
        render_metric_card(
            label="Total Dataset Uploads",
            value=f"{kpis.get('total_dataset_uploads', 0):,}",
            status="Uploads",
            icon="database"
        )
    with c4:
        render_metric_card(
            label="Recent Active Users",
            value=f"{kpis.get('unique_active_users', 0):,}",
            status="Unique",
            icon="shield-check"
        )
    with c5:
        avg_mb = kpis.get("avg_size_mb", 0.0)
        render_metric_card(
            label="Average Dataset Size",
            value=f"{avg_mb:.2f} MB" if avg_mb > 0 else f"{kpis.get('avg_rows', 0):,} rows",
            status="Avg Size",
            icon="table"
        )
    with c6:
        render_metric_card(
            label="Total Records Analyzed",
            value=f"{kpis.get('total_records_analyzed', 0):,}",
            status="Total Rows",
            icon="bar-chart-3"
        )



def _render_visual_summaries(data: Dict[str, Any], theme: str) -> None:
    """Render file format distribution and dataset size averages."""
    col_chart, col_stats = st.columns([5, 5], gap="large")

    with col_chart:
        render_section_header(
            title="File Format Distribution",
            subtitle="Uploaded dataset format breakdown."
        )
        ft_counts = data.get("file_type_counts", {})
        if ft_counts:
            labels = list(ft_counts.keys())
            values = list(ft_counts.values())
            colors = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b"]

            fig = go.Figure(data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.55,
                    marker=dict(colors=colors[:len(labels)]),
                    textinfo="label+percent",
                    hoverinfo="label+value+percent"
                )
            ])
            _apply_theme_to_fig(fig, theme=theme, height=220)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No dataset upload records found for the selected period.")

    with col_stats:
        render_section_header(
            title="Ingestion Averages",
            subtitle="Average volume and dimensions per uploaded dataset."
        )
        kpis = data.get("kpis", {})
        
        stat_html = (
            f'<div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: var(--space-4);">'
            f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">'
            f'<div>'
            f'<div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Avg Rows / Dataset</div>'
            f'<div style="font-size: 18px; font-weight: 700; color: var(--text-primary);">{kpis.get("avg_rows", 0):,}</div>'
            f'</div>'
            f'<div>'
            f'<div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Avg Columns / Dataset</div>'
            f'<div style="font-size: 18px; font-weight: 700; color: var(--text-primary);">{kpis.get("avg_cols", 0)}</div>'
            f'</div>'
            f'<div>'
            f'<div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Avg Memory Size</div>'
            f'<div style="font-size: 18px; font-weight: 700; color: #60a5fa;">{kpis.get("avg_size_mb", 0.0)} MB</div>'
            f'</div>'
            f'<div>'
            f'<div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Cloud Logging Policy</div>'
            f'<div style="font-size: 14px; font-weight: 600; color: var(--color-success);">Metadata Only (Privacy First)</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(stat_html, unsafe_allow_html=True)


# =============================================================================
# TAB RENDERERS
# =============================================================================

def _render_tab_activity(activity_list: List[Dict[str, Any]]) -> None:
    """Render unified chronological feed of logins and uploads."""
    if not activity_list:
        st.info("No activity records available for this time range.")
        return

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    for item in activity_list[:30]:
        action = item["action"]
        user_name = item["user"]
        email = item["email"]
        details = item["details"]
        ts_str = item["timestamp_str"]
        is_guest = item.get("is_guest", False)

        badge_color = "var(--color-warning)" if is_guest else "var(--accent)"
        badge_label = "GUEST" if is_guest else "USER"
        icon_name = "upload" if item["type"] == "upload" else "shield-check"

        row_html = (
            f'<div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 10px 14px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">'
            f'<div style="display: flex; align-items: center; gap: 12px;">'
            f'<div style="display: flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: var(--radius-sm); background: var(--surface-hover); color: var(--accent);">'
            f'{get_icon_svg(icon_name, 15)}'
            f'</div>'
            f'<div>'
            f'<div style="font-size: 13px; font-weight: 600; color: var(--text-primary); display: flex; align-items: center; gap: 6px;">'
            f'{user_name} <span style="font-size: 10px; font-weight: 600; padding: 1px 5px; border-radius: 3px; background: rgba(59, 130, 246, 0.1); color: {badge_color};">{badge_label}</span>'
            f'<span style="font-size: 12px; font-weight: 400; color: var(--text-secondary);">— {action}</span>'
            f'</div>'
            f'<div style="font-size: 11px; color: var(--text-muted); margin-top: 1px;">{email} • {details}</div>'
            f'</div>'
            f'</div>'
            f'<div style="font-size: 11px; font-family: var(--font-mono); color: var(--text-muted);">{ts_str[:19].replace("T", " ")} UTC</div>'
            f'</div>'
        )
        st.markdown(row_html, unsafe_allow_html=True)


def _render_tab_users(users_list: List[Dict[str, Any]]) -> None:
    """Render searchable registered user directory."""
    if not users_list:
        st.info("No registered users found in Firestore database.")
        return

    search_query = st.text_input(
        "Search Users",
        placeholder="Filter by name or email address...",
        key="admin_user_search_input"
    )

    filtered = users_list
    if search_query:
        q = search_query.strip().lower()
        filtered = [u for u in users_list if q in u.get("full_name", "").lower() or q in u.get("email", "").lower()]

    rows = []
    for u in filtered:
        rows.append({
            "Full Name": u.get("full_name", "User"),
            "Email Address": u.get("email", ""),
            "Auth Provider": u.get("auth_provider", "email_password"),
            "Total Uploads": u.get("upload_count", 0),
            "Last Login": str(u.get("last_login_at", ""))[:19].replace("T", " "),
            "First Seen": str(u.get("created_at", ""))[:19].replace("T", " ")
        })

    df_users = pd.DataFrame(rows)
    st.dataframe(df_users, use_container_width=True, hide_index=True)


def _render_tab_uploads(uploads_list: List[Dict[str, Any]]) -> None:
    """Render dataset upload history table."""
    if not uploads_list:
        st.info("No dataset upload records found for the selected period.")
        return

    search_ds = st.text_input(
        "Search Uploads",
        placeholder="Filter by dataset name, user, or email...",
        key="admin_upload_search_input"
    )

    filtered = uploads_list
    if search_ds:
        q = search_ds.strip().lower()
        filtered = [
            u for u in uploads_list
            if q in u.get("dataset_name", "").lower() or q in u.get("email", "").lower() or q in u.get("full_name", "").lower()
        ]

    rows = []
    for u in filtered:
        rows.append({
            "Dataset Name": u.get("dataset_name", ""),
            "File Type": u.get("file_type", "CSV"),
            "Rows": f"{u.get('row_count', 0):,}",
            "Cols": u.get("column_count", 0),
            "Size (MB)": f"{u.get('file_size_mb', 0.0):.2f}",
            "Missing %": f"{u.get('missing_percentage', 0.0):.1f}%",
            "User": u.get("full_name", "User"),
            "Email": u.get("email", ""),
            "Upload Time": str(u.get("upload_time", ""))[:19].replace("T", " ")
        })

    df_uploads = pd.DataFrame(rows)
    st.dataframe(df_uploads, use_container_width=True, hide_index=True)


def _render_tab_dataset_statistics(data: Dict[str, Any], theme: str) -> None:
    """Render comprehensive dataset statistics, formats, column distributions, and averages."""
    col_chart1, col_chart2 = st.columns([5, 5], gap="large")

    with col_chart1:
        render_section_header(
            title="File Format Distribution",
            subtitle="Uploaded dataset format breakdown."
        )
        ft_counts = data.get("file_type_counts", {})
        if ft_counts:
            labels = list(ft_counts.keys())
            values = list(ft_counts.values())
            colors = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b"]

            fig = go.Figure(data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.55,
                    marker=dict(colors=colors[:len(labels)]),
                    textinfo="label+percent",
                    hoverinfo="label+value+percent"
                )
            ])
            _apply_theme_to_fig(fig, theme=theme, height=220)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No dataset upload records found.")

    with col_chart2:
        render_section_header(
            title="Column Type Frequencies",
            subtitle="Aggregated schema types across all datasets."
        )
        col_frequencies = data.get("column_type_frequencies", {})
        if col_frequencies:
            labels = list(col_frequencies.keys())
            values = list(col_frequencies.values())

            fig2 = go.Figure(data=[
                go.Bar(
                    x=labels,
                    y=values,
                    marker=dict(color="#3b82f6"),
                    text=values,
                    textposition="auto"
                )
            ])
            _apply_theme_to_fig(fig2, theme=theme, height=220)
            fig2.update_layout(xaxis_title="Data Type", yaxis_title="Count")
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No schema frequency records available.")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    render_section_header(
        title="Ingestion Averages & Dimensions",
        subtitle="Summary metrics across all uploaded datasets in this period."
    )
    kpis = data.get("kpis", {})
    stat_html = (
        f'<div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: var(--space-4); margin-bottom: 12px;">'
        f'<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;">'
        f'<div>'
        f'<div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Avg Rows / Dataset</div>'
        f'<div style="font-size: 18px; font-weight: 700; color: var(--text-primary);">{kpis.get("avg_rows", 0):,}</div>'
        f'</div>'
        f'<div>'
        f'<div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Avg Columns / Dataset</div>'
        f'<div style="font-size: 18px; font-weight: 700; color: var(--text-primary);">{kpis.get("avg_cols", 0)}</div>'
        f'</div>'
        f'<div>'
        f'<div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Avg File Size</div>'
        f'<div style="font-size: 18px; font-weight: 700; color: #60a5fa;">{kpis.get("avg_size_mb", 0.0):.2f} MB</div>'
        f'</div>'
        f'<div>'
        f'<div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Total Records Ingested</div>'
        f'<div style="font-size: 18px; font-weight: 700; color: var(--color-success);">{kpis.get("total_records_analyzed", 0):,}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(stat_html, unsafe_allow_html=True)


def _render_tab_system_overview(data: Dict[str, Any]) -> None:
    """Render system diagnostics, database status, and privacy configuration."""
    render_section_header(
        title="System Architecture & Cloud Services",
        subtitle="Real-time operational status and security posture."
    )

    sys1, sys2, sys3 = st.columns(3)
    with sys1:
        render_metric_card(
            label="Database Engine",
            value="Firestore Cloud",
            description="Active & Synced",
            status="Online",
            icon="database",
            change_type="success"
        )
    with sys2:
        admin_email = get_configured_admin_email() or "Configured in Secrets"
        render_metric_card(
            label="Authorized Admin",
            value=admin_email.split("@")[0],
            description=admin_email,
            status="Admin Role",
            icon="shield-check",
            change_type="neutral"
        )
    with sys3:
        render_metric_card(
            label="Platform Version",
            value="Data Studio v2",
            description="Enterprise Edition",
            status="Stable",
            icon="zap",
            change_type="success"
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    render_section_header(
        title="Privacy & Data Governance Posture",
        subtitle="Zero raw dataset persistence architecture."
    )

    st.markdown(
        """
        <div style="background: var(--surface); border: 1px solid var(--border); border-left: 4px solid var(--color-success); border-radius: var(--radius-md); padding: 16px 20px; line-height: 1.55;">
            <div style="font-size: 14px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">
                Privacy-First Metadata Logging Guarantee
            </div>
            <div style="font-size: 13px; color: var(--text-secondary);">
                Data Studio operates on a strict zero-data-retention architecture. Only high-level dataset metadata 
                (row count, column count, memory footprint, column type names, and timestamp) and user authentication logs 
                are synchronized with Firebase Firestore. Raw customer dataset records and cell contents remain exclusively 
                in ephemeral in-memory session compute and are never saved or sent to any remote database.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def _render_setup_guide() -> None:
    """Display clean setup guide when Firebase credentials are not yet configured."""
    guide_html = (
        '<div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: var(--space-5); margin-top: var(--space-4);">'
        '<div style="font-size: 15px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px;">How to Configure Firebase Activity Logging</div>'
        '<div style="font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 12px;">'
        'To enable activity tracking across deployments, create a Firebase project, generate a service account key, and configure your secrets:'
        '</div>'
        '<div style="background: var(--bg-secondary); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 12px; font-family: var(--font-mono); font-size: 12px; color: var(--text-primary); margin-bottom: 12px;">'
        '# .streamlit/secrets.toml (or Streamlit Cloud App Secrets)<br><br>'
        '[admin]<br>'
        'email = "admin@company.com"<br><br>'
        '[firebase]<br>'
        'type = "service_account"<br>'
        'project_id = "your-project-id"<br>'
        'private_key_id = "your-key-id"<br>'
        'private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"<br>'
        'client_email = "firebase-adminsdk@your-project-id.iam.gserviceaccount.com"<br>'
        'client_id = "your-client-id"<br>'
        'auth_uri = "https://accounts.google.com/o/oauth2/auth"<br>'
        'token_uri = "https://oauth2.googleapis.com/token"'
        '</div>'
        '<div style="font-size: 12px; color: var(--text-muted);">'
        'For Streamlit Community Cloud: Go to <b>App Settings &rarr; Secrets</b> and paste the configuration above.'
        '</div>'
        '</div>'
    )
    st.markdown(guide_html, unsafe_allow_html=True)


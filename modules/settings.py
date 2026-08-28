"""
DATA STUDIO v2 — Settings Module (Premium UI v2)
=============================================================================
Workspace appearance, session diagnostics, and dataset state management.
Now includes three-way theme selector (Light / Dark / System preview).
"""
import streamlit as st
from modules.ui_components import (
    render_page_header,
    render_section_header,
    render_metric_card,
    render_notification,
    render_next_workflow_steps,
    get_icon_svg,
)
from modules.config import APP_VERSION, APP_NAME
from modules.data_loader import clear_dataset_state
from modules.auth import get_current_user


def render_settings_page() -> None:
    """Render premium application settings and appearance preferences."""
    render_page_header(
        title="Settings",
        subtitle="Workspace configuration, appearance preferences, and session management.",
        icon="settings"
    )

    # ── Appearance & Theme ─────────────────────────────────────────────────────
    render_section_header(
        title="Appearance & Theme",
        subtitle="Choose the visual mode across all Data Studio views."
    )

    current_theme = st.session_state.get("theme", "Light")

    # Theme selection cards
    th_col1, th_col2, th_col3 = st.columns(3, gap="small")

    def _theme_card(col, theme_key: str, icon_name: str, bg: str, fg: str, surf: str, border: str):
        """Render a visual theme preview swatch card."""
        with col:
            is_active = current_theme == theme_key
            active_border = "2px solid var(--accent)" if is_active else "1px solid var(--border)"
            active_badge = (
                f'<div style="position:absolute;top:8px;right:8px;font-size:9px;font-weight:700;'
                f'text-transform:uppercase;background:var(--accent);color:#fff;border-radius:3px;'
                f'padding:2px 6px;letter-spacing:0.04em;">Active</div>'
            ) if is_active else ""
            icon_svg = get_icon_svg(icon_name, 16)

            card_html = (
                f'<div style="background:{surf};border:{active_border};border-radius:10px;'
                f'padding:14px;cursor:pointer;position:relative;margin-bottom:8px;'
                f'box-shadow:var(--shadow-sm);">'
                f'{active_badge}'
                f'<div style="background:{bg};border-radius:6px;height:52px;margin-bottom:10px;'
                f'display:flex;align-items:center;justify-content:center;gap:6px;'
                f'border:1px solid {border};">'
                f'<div style="width:8px;height:8px;border-radius:50%;background:{fg};opacity:0.4;"></div>'
                f'<div style="width:18px;height:4px;border-radius:2px;background:{fg};opacity:0.3;"></div>'
                f'<div style="width:12px;height:4px;border-radius:2px;background:{fg};opacity:0.2;"></div>'
                f'</div>'
                f'<div style="display:flex;align-items:center;gap:7px;">'
                f'<div style="color:{fg if is_active else "var(--text-muted)"};">{icon_svg}</div>'
                f'<span style="font-size:13px;font-weight:{"700" if is_active else "500"};'
                f'color:{"var(--accent)" if is_active else "var(--text-secondary)"};">'
                f'{theme_key} Mode</span>'
                f'</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

            if st.button(
                f"{'✓ ' if is_active else ''}Use {theme_key}",
                key=f"theme_btn_{theme_key}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                if theme_key != current_theme:
                    st.session_state["theme"] = theme_key
                    st.rerun()

    _theme_card(
        th_col1, "Light", "sun",
        bg="#f8fafc", fg="#0f172a", surf="var(--surface)", border="#e2e8f0"
    )
    _theme_card(
        th_col2, "Dark", "moon",
        bg="#0b0f19", fg="#f1f5f9", surf="var(--surface)", border="#1e2d45"
    )

    with th_col3:
        st.markdown(
            '<div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;'
            'padding:14px;cursor:default;margin-bottom:8px;box-shadow:var(--shadow-xs);">'
            '<div style="background:linear-gradient(135deg,#f8fafc 50%,#0b0f19 50%);border-radius:6px;'
            'height:52px;margin-bottom:10px;border:1px solid var(--border);"></div>'
            '<div style="font-size:13px;font-weight:500;color:var(--text-muted);">System Theme</div>'
            '<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">'
            'Coming soon — follows OS preference.</div>'
            '</div>',
            unsafe_allow_html=True
        )

    # ── Session Diagnostics ────────────────────────────────────────────────────
    render_section_header(
        title="Session Diagnostics",
        subtitle="Active session parameters, identity, and memory footprint."
    )

    user = get_current_user()
    c1, c2, c3 = st.columns(3)

    with c1:
        render_metric_card(
            label="Active Route",
            value=st.session_state.get("current_page", "Overview"),
            status="Route",
            icon="grid"
        )
    with c2:
        dataset_name = st.session_state.get("dataset_name")
        df = st.session_state.get("dataset")
        if dataset_name and df is not None:
            value = f"{df.shape[0]:,}r"
            desc = f"{df.shape[1]} cols · {dataset_name}"
        else:
            value = "None"
            desc = "No dataset active"
        render_metric_card(
            label="Active Dataset",
            value=value,
            description=desc[:28],
            status="Session",
            icon="database"
        )
    with c3:
        render_metric_card(
            label="User Identity",
            value=user.get("full_name", "User"),
            description=user.get("email", ""),
            status="Guest" if user.get("is_guest") else "Registered",
            icon="users"
        )

    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

    # Version info row
    app_info_html = (
        f'<div style="display:flex;gap:16px;margin-top:8px;">'
        f'<div style="font-size:11.5px;color:var(--text-muted);">'
        f'<span style="font-weight:600;color:var(--text-secondary);">Platform:</span> {APP_NAME} {APP_VERSION}</div>'
        f'<div style="font-size:11.5px;color:var(--text-muted);">'
        f'<span style="font-weight:600;color:var(--text-secondary);">Theme:</span> {current_theme}</div>'
        f'<div style="font-size:11.5px;color:var(--text-muted);">'
        f'<span style="font-weight:600;color:var(--text-secondary);">Dataset:</span> '
        f'{"Loaded" if st.session_state.get("dataset") is not None else "None"}</div>'
        f'</div>'
    )
    st.markdown(app_info_html, unsafe_allow_html=True)

    # ── AI & LLM Model Configuration (Admin Only) ──────────────────────────────
    from modules.firebase_service import is_admin_user
    user = get_current_user()
    if is_admin_user(user):
        render_section_header(
            title="Generative AI & LLM Model (Admin)",
            subtitle="Configure your AI Provider (Google Gemini / OpenAI) for multilingual natural language data analysis."
        )

        from modules.llm_service import get_ai_api_key, set_ai_api_key, test_ai_connection
        active_key, active_provider = get_ai_api_key()

        ai_c1, ai_c2, ai_c3, ai_c4 = st.columns([4, 2, 2, 2], gap="small")
        with ai_c1:
            st_key_input = st.text_input(
                "AI API Key",
                value="",
                type="password",
                placeholder="•••••••••••••••• (API Key Active & Secured)" if active_key else "Paste Gemini or OpenAI API Key...",
                key="settings_ai_api_key_input",
                help="Your API key is securely encrypted in memory/secrets and never revealed to guests or users."
            )
        with ai_c2:
            st_prov_sel = st.selectbox(
                "AI Provider",
                options=["Gemini", "OpenAI"],
                index=0 if active_provider == "gemini" else 1,
                key="settings_ai_provider_sel"
            )
        with ai_c3:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            if st.button("Save Key", key="settings_save_ai_key_btn", type="primary", use_container_width=True):
                input_val = (st_key_input or "").strip()
                if input_val:
                    set_ai_api_key(input_val, st_prov_sel.lower())
                    st.toast(f"Saved {st_prov_sel} API Key! Real LLM enabled. ✓")
                    st.rerun()
                elif active_key:
                    st.toast("Existing secured key remains active.")
                else:
                    st.session_state["ai_api_key"] = None
                    st.toast("AI API Key cleared.")
                    st.rerun()
        with ai_c4:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            if st.button("Test Key", key="settings_test_ai_key_btn", use_container_width=True):
                test_target_key = (st_key_input or active_key or "").strip()
                with st.spinner("Testing API connection..."):
                    ok, msg = test_ai_connection(test_target_key, st_prov_sel.lower())
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

        status_color = "#10b981" if active_key else "#64748b"
        status_source = f"Active ({active_provider.title()} · Secured)" if active_key else "Inactive (Using Analytics Engine Mode)"
        st.markdown(
            f"""
            <div style="font-size:12px; color:var(--text-secondary); margin-top:4px; margin-bottom:16px;">
                <span style="color:{status_color}; font-weight:700;">● Status:</span> <strong style="color:{status_color};">{status_source}</strong> · 
                <em>API key is protected and hidden from non-admin users. Multilingual Q&A is active for all users.</em>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ── Dataset State Management ───────────────────────────────────────────────
    render_section_header(
        title="Dataset State Management",
        subtitle="Purge active dataset from memory and reset to the initial workspace state."
    )

    if st.session_state.get("dataset") is not None:
        render_notification(
            title="Active Dataset in Memory",
            message=(
                f"Dataset '{st.session_state.get('dataset_name', 'dataset')}' is currently loaded. "
                "Clearing it will remove all analysis results and return you to the upload screen."
            ),
            variant="warning"
        )

    col_btn, col_info = st.columns([2, 5])
    with col_btn:
        if st.button(
            "Clear Active Dataset",
            key="settings_reset_dataset_btn",
            type="secondary" if st.session_state.get("dataset") is None else "primary"
        ):
            clear_dataset_state()
            st.session_state["current_page"] = "Overview"
            st.toast("Active dataset cleared from memory.")
            st.rerun()
    with col_info:
        st.markdown(
            '<div style="padding:8px 0;font-size:12px;color:var(--text-muted);">'
            'This resets the dataset, cleaned dataset, dataset name, and all metadata. '
            'Your account and history are not affected.</div>',
            unsafe_allow_html=True
        )

    # ── Standardized Bottom Next Workflow Steps Section ──────────────────
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    render_next_workflow_steps("Settings")


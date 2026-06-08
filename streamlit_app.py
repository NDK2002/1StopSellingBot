"""Streamlit Chat UI for 1StopSellingBot."""

import json
import uuid

import httpx
import streamlit as st
import streamlit.components.v1 as components

# ── Config ────────────────────────────────────────────────────────────
API_BASE_URL = "http://localhost:8000"
CHAT_SESSION_STORAGE_KEY = "1stopsellingbot.chat_session_id"

st.set_page_config(
    page_title="1StopSellingBot - Trợ lý mua hàng",
    page_icon="🛒",
    layout="centered",
)

# ── Custom CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp {
        max-width: 800px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.75rem;
        margin-bottom: 0.5rem;
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 20%;
    }
    .bot-message {
        background: #f0f2f6;
        color: #1a1a2e;
        margin-right: 20%;
    }
    .staff-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        margin-right: 20%;
        border-left: 4px solid #f5576c;
    }
    .escalation-banner {
        background: #fef3c7;
        color: #92400e;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f59e0b;
        margin-bottom: 1rem;
    }
    /* Robust Sticky Header */
    [data-testid="stVerticalBlock"] > div:has(.header-fixed-target) {
        position: sticky;
        top: 0;
        z-index: 999;
        background-color: #0e1117;
        padding-top: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #262730;
    }
    .header-fixed-target {
        display: none;
    }
</style>
""", unsafe_allow_html=True)


# ── Route: /session?session_id=xxx ────────────────────────────────────
# (routing logic at bottom of file after function definitions)


def _set_chat_session_id(session_id: str):
    st.query_params["chat_session_id"] = session_id
    _sync_chat_session_storage(session_id)


def _sync_chat_session_storage(session_id: str):
    components.html(
        f"""
        <script>
            const key = {CHAT_SESSION_STORAGE_KEY!r};
            const sessionId = {session_id!r};
            window.parent.localStorage.setItem(key, sessionId);
        </script>
        """,
        height=0,
    )


def _bootstrap_chat_session_from_storage():
    components.html(
        f"""
        <script>
            const key = {CHAT_SESSION_STORAGE_KEY!r};
            const params = new URLSearchParams(window.parent.location.search);
            const urlSessionId = params.get("chat_session_id");
            const savedSessionId = window.parent.localStorage.getItem(key);

            if (!urlSessionId && savedSessionId) {{
                params.set("chat_session_id", savedSessionId);
                const nextUrl = `${{window.parent.location.pathname}}?${{params.toString()}}${{window.parent.location.hash}}`;
                window.parent.history.replaceState(null, "", nextUrl);
                window.parent.location.reload();
            }} else if (urlSessionId) {{
                window.parent.localStorage.setItem(key, urlSessionId);
            }}
        </script>
        """,
        height=0,
    )


def _session_has_active_escalation(session_id: str) -> bool:
    try:
        resp = httpx.get(f"{API_BASE_URL}/api/escalations", timeout=5.0)
        if resp.status_code != 200:
            return False
        return any(
            esc.get("session_id") == session_id
            and esc.get("status") in ["pending", "assigned", "in_progress"]
            for esc in resp.json()
        )
    except Exception:
        return False


def _load_customer_chat_history(session_id: str) -> tuple[list[dict], bool]:
    try:
        resp = httpx.get(
            f"{API_BASE_URL}/api/escalations/session/{session_id}/history",
            timeout=5.0,
        )
        if resp.status_code != 200:
            return [], False
        messages = resp.json()
        return messages, _session_has_active_escalation(session_id)
    except Exception:
        return [], False


def _render_session_viewer(session_id: str):
    """Read-only session viewer - used by staff via deep link."""
    st.title("📋 Lịch sử hội thoại")

    # Fetch escalation info
    try:
        esc_resp = httpx.get(
            f"{API_BASE_URL}/api/escalations",
            timeout=10.0,
        )
        escalations = esc_resp.json() if esc_resp.status_code == 200 else []
        active_esc = next(
            (e for e in escalations if e["session_id"] == session_id and e.get("status") in ["assigned", "in_progress", "pending"]),
            None
        )
    except Exception:
        active_esc = None

    # Show escalation info
    if active_esc:
        reason_map = {
            "low_confidence": "Bot không chắc chắn",
            "user_request": "Khách yêu cầu gặp nhân viên",
            "complex_issue": "Vấn đề phức tạp",
            "complaint": "Khách khiếu nại",
            "order_issue": "Vấn đề đơn hàng",
        }
        reason_text = reason_map.get(active_esc.get("reason", ""), active_esc.get("reason", ""))
        st.markdown(f"""
        <div class="escalation-banner">
            🔔 <b>Escalation:</b> {reason_text}<br>
            📝 {active_esc.get("customer_summary", "Không có tóm tắt")}
        </div>
        """, unsafe_allow_html=True)

    st.caption(f"Session: `{session_id}`")
    st.divider()

    # Fetch and display conversation history in a realtime fragment
    @st.fragment(run_every="3s")
    def render_staff_chat_history():
        try:
            resp = httpx.get(
                f"{API_BASE_URL}/api/escalations/session/{session_id}/history",
                timeout=10.0,
            )
            resp.raise_for_status()
            messages = resp.json()
        except Exception as e:
            st.error(f"Không thể tải lịch sử: {e}")
            return

        if not messages:
            st.info("Chưa có tin nhắn nào trong session này.")
            return

        # Display messages
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            metadata = msg.get("metadata") or {}

            if role == "user":
                with st.chat_message("user"):
                    st.markdown(content)
            else:
                source = metadata.get("source", "bot")
                if source == "staff":
                    with st.chat_message("assistant", avatar="👤"):
                        st.markdown(f"**[Nhân viên]** {content}")
                else:
                    with st.chat_message("assistant"):
                        st.markdown(content)

    render_staff_chat_history()

    # Staff reply form
    st.divider()
    st.subheader("💬 Trả lời khách")

    with st.form("staff_reply_form", clear_on_submit=True):
        reply_text = st.text_area("Nhập phản hồi:", height=100)
        col1, col2 = st.columns([3, 1])

        with col1:
            submitted = st.form_submit_button("📤 Gửi", use_container_width=True)
        with col2:
            resolve = st.form_submit_button("✅ Giải quyết", use_container_width=True)

    if submitted and reply_text:
        if active_esc:
            try:
                httpx.post(
                    f"{API_BASE_URL}/api/escalations/{active_esc['id']}/reply",
                    json={"session_id": session_id, "message": reply_text},
                    timeout=10.0,
                )
                st.success("Đã gửi phản hồi!")
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi gửi: {e}")
        else:
            st.warning("Không tìm thấy escalation đang hoạt động.")

    if resolve:
        if active_esc:
            try:
                httpx.post(
                    f"{API_BASE_URL}/api/escalations/{active_esc['id']}/resolve",
                    json={"staff_notes": reply_text or "Đã giải quyết"},
                    timeout=10.0,
                )
                st.success("✅ Đã giải quyết escalation!")
            except Exception as e:
                st.error(f"Lỗi: {e}")
        else:
            st.warning("Không tìm thấy escalation.")

    # Auto-refresh
    if st.button("🔄 Tải lại tin nhắn"):
        st.rerun()


def _render_chat_ui():
    """Main chat interface for customers."""
    _bootstrap_chat_session_from_storage()

    # ── Session State
    if "session_id" not in st.session_state:
        initial_id = st.query_params.get("chat_session_id") or str(uuid.uuid4())
        st.session_state.session_id = initial_id
        _set_chat_session_id(initial_id)
    if "messages" not in st.session_state:
        messages, has_staff_reply = _load_customer_chat_history(st.session_state.session_id)
        st.session_state.messages = messages
        st.session_state.is_escalated = has_staff_reply
    if "is_escalated" not in st.session_state:
        st.session_state.is_escalated = False

    # ── Sidebar Header & Suggestions
    with st.sidebar:
        st.title("🛒 1StopSellingBot")
        st.caption("Trợ lý mua hàng thông minh - hỏi về sản phẩm, tồn kho, chính sách, hoặc đặt hàng")

        # ── Escalation Status in Sidebar
        if st.session_state.get("is_escalated"):
            st.divider()
            st.success("🟢 **Đang kết nối Nhân viên**")
            st.caption("Chế độ hỗ trợ trực tiếp đang hoạt động.")
            if st.button("❌ Hủy yêu cầu hỗ trợ", use_container_width=True, key="cancel_support_sidebar_btn"):
                try:
                    resp = httpx.post(f"{API_BASE_URL}/api/escalations/session/{st.session_state.session_id}/resolve")
                    if resp.status_code == 200:
                        st.session_state.is_escalated = False
                        st.success("Đã quay lại chế độ Chatbot!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")

        st.divider()
        
        st.markdown("**💡 Gợi ý nhanh:**")
        examples = [
            "Áo thun nam còn hàng không?",
            "Cho tôi biết chính sách đổi trả.",
            "Tôi muốn mua 2 cái áo thun size M.",
            "Tạo đơn hàng cho tôi.",
            "Cho tôi gặp nhân viên.",
        ]
        for i, ex in enumerate(examples):
            if st.button(ex, key=f"side_ex_{i}", use_container_width=True):
                st.session_state.pending_message = ex
                st.rerun()
        
        st.divider()
        if st.button("🔄 Reset hội thoại", use_container_width=True):
            st.session_state.messages = []
            st.session_state.is_escalated = False
            st.session_state.session_id = str(uuid.uuid4())
            _set_chat_session_id(st.session_state.session_id)
            st.rerun()

    # ── Chat History
    @st.fragment(run_every="3s" if st.session_state.get("is_escalated") else None)
    def render_history():
        if st.session_state.get("is_escalated"):
            try:
                resp = httpx.get(
                    f"{API_BASE_URL}/api/escalations/session/{st.session_state.session_id}/history",
                    timeout=5.0
                )
                if resp.status_code == 200:
                    messages = resp.json()
                    if messages:
                        for msg in messages:
                            role = msg.get("role", "user")
                            content = msg.get("content", "")
                            metadata = msg.get("metadata") or {}
                            
                            if role == "user":
                                with st.chat_message("user"):
                                    st.markdown(content)
                            else:
                                source = metadata.get("source", "bot")
                                if source == "staff":
                                    user = metadata.get("user", {})
                                    with st.chat_message("assistant", avatar="👤"):
                                        st.markdown(f"**[{user.get('name')}]** {content}")
                                else:
                                    with st.chat_message("assistant"):
                                        st.markdown(content)
                        return
            except Exception:
                pass
        
        # Fallback / Non-escalated
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    render_history()

    # ── Chat Input
    pending = st.session_state.pop("pending_message", None)
    user_input = st.chat_input("Nhập câu hỏi của bạn...") or pending

    if user_input:
        if not st.session_state.get("is_escalated"):
            st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Đang xử lý..."):
                try:
                    response = httpx.post(
                        f"{API_BASE_URL}/api/chat",
                        json={
                            "message": user_input,
                            "session_id": st.session_state.session_id,
                        },
                        timeout=60.0,
                    )
                    response.raise_for_status()
                    data = response.json()
                    reply = data["reply"]
                    st.session_state.session_id = data.get("session_id", st.session_state.session_id)
                    _set_chat_session_id(st.session_state.session_id)

                    should_rerun = False
                    if data.get("escalated"):
                        if not st.session_state.get("is_escalated"):
                            reply += "\n\n⏳ _Đang kết nối với nhân viên hỗ trợ..._"
                            st.session_state.is_escalated = True
                            should_rerun = True

                except httpx.ConnectError:
                    reply = "❌ Không thể kết nối đến server. Hãy đảm bảo FastAPI đang chạy tại `localhost:8000`."
                    should_rerun = False
                except Exception as e:
                    reply = f"❌ Lỗi: {str(e)}"
                    should_rerun = False

            if not st.session_state.get("is_escalated") or should_rerun:
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            
            if should_rerun or st.session_state.get("is_escalated"):
                st.rerun()


# ── Routing ───────────────────────────────────────────────────────────
params = st.query_params
view_session_id = params.get("session_id")

if view_session_id:
    _render_session_viewer(view_session_id)
else:
    _render_chat_ui()

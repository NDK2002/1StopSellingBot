"""Streamlit Chat UI for 1StopSellingBot MVP."""

import uuid

import httpx
import streamlit as st

# ── Config ────────────────────────────────────────────────────────────
API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="1StopSellingBot — Trợ lý mua hàng",
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
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Header ────────────────────────────────────────────────────────────
st.title("🛒 1StopSellingBot")
st.caption("Trợ lý mua hàng thông minh — hỏi về sản phẩm, tồn kho, chính sách, hoặc đặt hàng")

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Cài đặt")
    st.text(f"Session: {st.session_state.session_id[:8]}...")

    if st.button("🔄 Reset hội thoại", use_container_width=True):
        try:
            httpx.delete(f"{API_BASE_URL}/api/chat/sessions/{st.session_state.session_id}")
        except Exception:
            pass
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.divider()
    st.subheader("💡 Ví dụ câu hỏi")
    examples = [
        "Áo thun nam còn hàng không?",
        "Cho tôi biết chính sách đổi trả.",
        "Tôi muốn mua 2 cái áo thun size M.",
        "Tạo đơn hàng cho tôi.",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True, key=f"ex_{ex}"):
            st.session_state.pending_message = ex
            st.rerun()

# ── Chat History ──────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat Input ────────────────────────────────────────────────────────
pending = st.session_state.pop("pending_message", None)
user_input = st.chat_input("Nhập câu hỏi của bạn...") or pending

if user_input:
    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call API
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
            except httpx.ConnectError:
                reply = "❌ Không thể kết nối đến server. Hãy đảm bảo FastAPI đang chạy tại `localhost:8000`."
            except Exception as e:
                reply = f"❌ Lỗi: {str(e)}"

        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

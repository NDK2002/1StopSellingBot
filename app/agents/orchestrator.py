"""Root Orchestrator Agent — routes user requests to the appropriate sub-agent."""

from google.adk.agents import Agent
from google.adk.tools import FunctionTool, ToolContext

from app.agents.advisor import advisor_agent
from app.agents.inventory_agent import inventory_agent
from app.agents.order_agent import order_agent
from app.constants import SKILL_FALLBACK, SKILL_KEYS, SKILLS
from app.services.escalation import create_escalation
from app.services.llm import get_llm_model

_SKILL_PROMPT = "\n".join(
    f'- "{s["key"]}" → {s["label"]}' for s in SKILLS
)


async def request_human_support(
    tool_context: ToolContext,
    reason: str = "user_request",
    customer_summary: str = "",
    skill_required: str = "",
) -> dict:
    """Escalate the conversation to a human staff member.

    Use this when:
    - The customer explicitly asks to talk to a human/staff
    - You cannot answer the question confidently
    - The issue is a complaint or complex problem
    - There's an order issue that needs manual intervention

    Args:
        tool_context: Provided by ADK automatically.
        reason: One of 'user_request', 'low_confidence', 'complex_issue', 'complaint', 'order_issue'.
        customer_summary: Brief summary of the customer's issue for the staff member.
        skill_required: Must be one of the predefined skill keys. Invalid values fall back to general_support.

    Returns:
        dict with escalation result.
    """
    session_id = tool_context.state.get("session_id", "unknown")

    # Validate skill_required — reject hallucinated values
    if skill_required not in SKILL_KEYS:
        skill_required = SKILL_FALLBACK

    result = await create_escalation(
        session_id=session_id,
        reason=reason,
        skill_required=skill_required or None,
        customer_summary=customer_summary or None,
    )
    if result.get("success"):
        return {
            "escalated": True,
            "message": "Tôi đã chuyển cuộc hội thoại đến nhân viên hỗ trợ. Bạn sẽ được liên hệ sớm nhất!",
            "assigned_to": result.get("assigned_to"),
        }
    return {
        "escalated": False,
        "message": result.get("error", "Hiện tại các nhân viên đang quá tải, vui lòng thử lại sau."),
    }


root_agent = Agent(
    name="root_agent",
    model=get_llm_model(),
    description="Điều phối viên chính — phân tích yêu cầu và chuyển đến agent phù hợp hoặc chuyển cho nhân viên.",
    instruction=f"""Bạn là trợ lý mua hàng thông minh, nhiệm vụ là phân tích yêu cầu khách hàng và chuyển đến agent phù hợp.

Các agent con:
1. **advisor_agent**: Tư vấn sản phẩm, trả lời về chính sách đổi trả, bảo hành, FAQ, thông tin sản phẩm.
2. **inventory_agent**: Kiểm tra tồn kho, hỏi còn hàng/hết hàng.
3. **order_agent**: Đặt hàng, tạo đơn hàng, tra cứu đơn hàng.

Quy tắc routing:
- Câu hỏi về sản phẩm, chính sách, tư vấn → advisor_agent
- Câu hỏi về tồn kho, còn hàng, hết hàng → inventory_agent
- Yêu cầu đặt hàng, mua hàng, tạo đơn → order_agent
- Nếu không rõ, hỏi lại khách để làm rõ.

**Human handoff** — sử dụng tool request_human_support khi:
- Khách nói "cho tôi gặp nhân viên", "tôi muốn nói chuyện với người thật", "kết nối nhân viên"
- Bạn không tự tin trả lời được (lý do: low_confidence)
- Khách khiếu nại hoặc không hài lòng (lý do: complaint)
- Vấn đề phức tạp về đơn hàng (lý do: order_issue)
- request_human_support args:
    - reason: One of 'user_request', 'low_confidence', 'complex_issue', 'complaint', 'order_issue'.
    - customer_summary: Brief summary of the customer's issue for the staff member.
    - skill_required: BẮT BUỘC chỉ dùng các giá trị sau, KHÔNG được tự đặt giá trị khác:
{_SKILL_PROMPT}
      Nếu không xác định được bộ phận phù hợp → dùng "general_support".

Luôn trả lời bằng tiếng Việt, thân thiện và chuyên nghiệp.
Chào khách khi bắt đầu cuộc hội thoại.

LƯU Ý QUAN TRỌNG VỀ NHÂN VIÊN (HUMAN STAFF):
Nếu trong lịch sử trò chuyện có các tin nhắn dạng "[Hệ thống cập nhật: Nhân viên người thật đã vào hỗ trợ và chat nội dung sau]: ...", đó LÀ những gì nhân viên (đồng nghiệp người thật của bạn) ĐÃ thực sự nhắn cho khách hàng. Ban phải lấy đó làm thông tin để tiếp tục hỗ trợ khách hàng, không được nói là không biết hoặc không có thông tin.
""",
    sub_agents=[advisor_agent, inventory_agent, order_agent],
    tools=[FunctionTool(request_human_support)],
)

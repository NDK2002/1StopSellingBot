"""Root Orchestrator Agent — routes user requests to the appropriate sub-agent."""

# import logging

from google.adk.agents import Agent
from google.adk.tools import FunctionTool, ToolContext

from app.agents.advisor import advisor_agent
from app.agents.inventory_agent import inventory_agent
from app.agents.order_agent import order_agent
from app.services.escalation import create_escalation
from app.services.llm import get_llm_model

# logging.basicConfig(
#     level=logging.DEBUG,
#     format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
# )


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
        skill_required: Optional skill needed, e.g. 'order_support', 'returns', 'technical'.

    Returns:
        dict with escalation result.
    """
    # Get session_id from ADK session state (injected by chat router)
    session_id = tool_context.state.get("session_id", "unknown")

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
    instruction="""Bạn là trợ lý mua hàng thông minh, nhiệm vụ là phân tích yêu cầu khách hàng và chuyển đến agent phù hợp.

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
    - skill_required: Optional skill needed, e.g. 'order_support', 'returns', 'technical'.
    - customer_summary: Brief summary of the customer's issue for the staff member.

Luôn trả lời bằng tiếng Việt, thân thiện và chuyên nghiệp.
Chào khách khi bắt đầu cuộc hội thoại.

LƯU Ý QUAN TRỌNG VỀ NHÂN VIÊN (HUMAN STAFF):
Nếu trong lịch sử trò chuyện có các tin nhắn dạng "[Hệ thống cập nhật: Nhân viên người thật đã vào hỗ trợ và chat nội dung sau]: ...", đó LÀ những gì nhân viên (đồng nghiệp người thật của bạn) ĐÃ thực sự nhắn cho khách hàng. Ban phải lấy đó làm thông tin để tiếp tục hỗ trợ khách hàng, không được nói là không biết hoặc không có thông tin.
""",
    sub_agents=[advisor_agent, inventory_agent, order_agent],
    tools=[FunctionTool(request_human_support)],
)

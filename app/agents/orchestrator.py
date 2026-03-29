"""Root Orchestrator Agent — routes user requests to the appropriate sub-agent."""

from google.adk.agents import Agent

from app.agents.advisor import advisor_agent
from app.agents.inventory_agent import inventory_agent
from app.agents.order_agent import order_agent
from app.services.llm import get_llm_model
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

root_agent = Agent(
    name="root_agent",
    model=get_llm_model(),
    description="Điều phối viên chính — phân tích yêu cầu và chuyển đến agent phù hợp.",
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

Luôn trả lời bằng tiếng Việt, thân thiện và chuyên nghiệp.
Chào khách khi bắt đầu cuộc hội thoại.
""",
    sub_agents=[advisor_agent, inventory_agent, order_agent],
)

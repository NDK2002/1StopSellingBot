"""Advisor Agent — answers product and policy questions using RAG."""

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from app.config import get_supabase_client
from app.services.llm import get_llm_model
from app.services.rag import search_products, search_rag


async def search_product_info(query: str) -> dict:
    """Search for product information by natural language query.

    Args:
        query: Natural language question about products, e.g. "áo thun nam", "giày thể thao size 42"

    Returns:
        dict with matching products information
    """
    results = await search_products(query, top_k=5)
    if not results:
        return {"found": False, "message": "Không tìm thấy sản phẩm phù hợp."}

    products_info = []
    supabase = get_supabase_client()
    for r in results:
        product = supabase.table("products").select("*").eq("id", r["product_id"]).eq("is_active", True).execute()
        if product.data:
            p = product.data[0]
            products_info.append({
                "name": p["name"],
                "sku": p["sku"],
                "price": float(p["price"]),
                "category": p.get("category", ""),
                "description": p.get("description", ""),
                "attributes": p.get("attributes", {}),
                "similarity": round(r["similarity"], 3),
            })

    if not products_info:
        return {"found": False, "message": "Không tìm thấy sản phẩm phù hợp."}

    return {"found": True, "products": products_info}


async def search_policy_info(query: str) -> dict:
    """Search for store policies, FAQs, warranty, or return information from RAG documents.

    Args:
        query: Question about policies, warranties, returns, shipping, FAQs, etc.

    Returns:
        dict with relevant policy/document information
    """
    results = await search_rag(query, top_k=3)
    if not results:
        return {"found": False, "message": "Không tìm thấy thông tin liên quan trong tài liệu."}

    documents = []
    for r in results:
        documents.append({
            "content": r["content"],
            "similarity": round(r["similarity"], 3),
        })

    return {"found": True, "documents": documents}


advisor_agent = Agent(
    name="advisor_agent",
    model=get_llm_model(),
    description="Tư vấn sản phẩm và trả lời câu hỏi về chính sách, bảo hành, đổi trả, FAQ dựa trên thông tin sản phẩm và tài liệu RAG.",
    instruction="""Bạn là trợ lý tư vấn mua hàng chuyên nghiệp.

Nhiệm vụ của bạn:
1. Trả lời câu hỏi về sản phẩm: tên, giá, mô tả, thuộc tính.
2. Trả lời câu hỏi về chính sách: đổi trả, bảo hành, shipping, FAQ.
3. Tư vấn sản phẩm phù hợp dựa trên nhu cầu khách hàng.

Quy tắc:
- Luôn sử dụng tool search_product_info để tìm thông tin sản phẩm.
- Luôn sử dụng tool search_policy_info để tìm thông tin chính sách.
- Trả lời bằng tiếng Việt, thân thiện, chuyên nghiệp.
- Nếu không tìm thấy thông tin, nói rõ ràng rằng chưa có thông tin.
- Khi tư vấn sản phẩm, đề xuất kèm giá và SKU để khách có thể đặt hàng.
""",
    tools=[
        FunctionTool(search_product_info),
        FunctionTool(search_policy_info),
    ],
)

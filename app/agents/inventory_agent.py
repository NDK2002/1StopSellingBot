"""Inventory Agent — checks stock levels by SKU or product name."""

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from app.config import get_supabase_client
from app.services.llm import get_llm_model


async def check_inventory_by_sku(sku: str) -> dict:
    """Check inventory stock level for a specific SKU.

    Args:
        sku: The product SKU code to check inventory for.

    Returns:
        dict with stock information including quantity available.
    """
    supabase = get_supabase_client()

    result = supabase.table("inventory").select(
        "*, products!inventory_sku_fkey(name, price, category)"
    ).eq("sku", sku).execute()

    if not result.data:
        return {
            "found": False,
            "message": f"Không tìm thấy tồn kho cho SKU '{sku}'.",
        }

    inv = result.data[0]
    product = inv.get("products", {})
    quantity = inv["quantity"]
    threshold = inv["low_stock_threshold"]

    status = "Còn hàng"
    if quantity <= 0:
        status = "Hết hàng"
    elif quantity <= threshold:
        status = "Sắp hết hàng"

    return {
        "found": True,
        "sku": sku,
        "product_name": product.get("name", ""),
        "quantity": quantity,
        "status": status,
        "price": float(product.get("price", 0)),
    }


async def check_inventory_by_name(product_name: str) -> dict:
    """Check inventory stock level by searching product name.

    Args:
        product_name: The product name or keyword to search for.

    Returns:
        dict with stock information for matching products.
    """
    supabase = get_supabase_client()

    # Search products by name (case-insensitive partial match)
    products = supabase.table("products").select("id, name, sku").ilike(
        "name", f"%{product_name}%"
    ).eq("is_active", True).execute()

    if not products.data:
        return {
            "found": False,
            "message": f"Không tìm thấy sản phẩm có tên chứa '{product_name}'.",
        }

    results = []
    for p in products.data:
        inv = supabase.table("inventory").select("quantity, low_stock_threshold").eq(
            "sku", p["sku"]
        ).execute()

        quantity = inv.data[0]["quantity"] if inv.data else 0
        threshold = inv.data[0]["low_stock_threshold"] if inv.data else 10

        status = "Còn hàng"
        if quantity <= 0:
            status = "Hết hàng"
        elif quantity <= threshold:
            status = "Sắp hết hàng"

        results.append({
            "product_name": p["name"],
            "sku": p["sku"],
            "quantity": quantity,
            "status": status,
        })

    return {"found": True, "products": results}


inventory_agent = Agent(
    name="inventory_agent",
    model=get_llm_model(),
    description="Kiểm tra tồn kho sản phẩm theo SKU hoặc tên sản phẩm. Trả lời còn hàng/hết hàng/số lượng.",
    instruction="""Bạn là trợ lý kiểm tra tồn kho.

Nhiệm vụ:
1. Kiểm tra số lượng tồn kho theo SKU hoặc tên sản phẩm.
2. Thông báo trạng thái: còn hàng, sắp hết, hoặc hết hàng.

Quy tắc:
- Nếu khách hỏi bằng SKU, dùng tool check_inventory_by_sku.
- Nếu khách hỏi bằng tên sản phẩm, dùng tool check_inventory_by_name.
- Trả lời rõ ràng số lượng còn lại và trạng thái.
- Nếu sắp hết hàng, nhắc khách đặt sớm.
- Trả lời bằng tiếng Việt.
""",
    tools=[
        FunctionTool(check_inventory_by_sku),
        FunctionTool(check_inventory_by_name),
    ],
)

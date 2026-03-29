"""Order Agent — collects order info and creates orders."""

import uuid
from datetime import datetime

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from app.config import get_supabase_client
from app.services.llm import get_llm_model
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)


async def lookup_product_for_order(sku: str) -> dict:
    """Look up product details and availability before ordering.

    Args:
        sku: The product SKU to look up.

    Returns:
        dict with product details and availability.
    """
    supabase = get_supabase_client()

    product = supabase.table("products").select("*").eq("sku", sku).eq("is_active", True).execute()
    if not product.data:
        return {"available": False, "message": f"Sản phẩm SKU '{sku}' không tồn tại hoặc đã ngừng bán."}

    p = product.data[0]
    inv = supabase.table("inventory").select("quantity").eq("sku", sku).execute()
    quantity = inv.data[0]["quantity"] if inv.data else 0

    return {
        "available": quantity > 0,
        "product_name": p["name"],
        "sku": p["sku"],
        "price": float(p["price"]),
        "stock": quantity,
    }


async def create_order(
    customer_name: str,
    customer_phone: str,
    customer_address: str,
    items: list[dict],
    customer_email: str = "",
    notes: str = "",
) -> dict:
    """Create a new order after collecting all required information.

    Args:
        customer_name: Full name of the customer.
        customer_phone: Phone number of the customer.
        customer_address: Delivery address.
        items: List of items, each with 'sku' and 'quantity' keys. Example: [{"sku": "AT001", "quantity": 2}]
        customer_email: Optional email address.
        notes: Optional order notes.

    Returns:
        dict with order confirmation details.
    """
    supabase = get_supabase_client()

    # Validate items
    order_items = []
    total_amount = 0.0

    for item in items:
        sku = item.get("sku", "")
        qty = item.get("quantity", 1)

        product = supabase.table("products").select("id, name, sku, price").eq("sku", sku).eq("is_active", True).execute()
        if not product.data:
            return {"success": False, "error": f"Sản phẩm SKU '{sku}' không tồn tại."}

        p = product.data[0]
        inv = supabase.table("inventory").select("quantity").eq("sku", sku).execute()
        stock = inv.data[0]["quantity"] if inv.data else 0

        if stock < qty:
            return {"success": False, "error": f"'{p['name']}' chỉ còn {stock} sản phẩm, không đủ {qty}."}

        subtotal = float(p["price"]) * qty
        total_amount += subtotal
        order_items.append({
            "product_id": p["id"],
            "sku": p["sku"],
            "product_name": p["name"],
            "quantity": qty,
            "unit_price": float(p["price"]),
            "subtotal": subtotal,
        })

    # Generate order number
    now = datetime.now()
    short_id = uuid.uuid4().hex[:6].upper()
    order_number = f"ORD-{now.strftime('%Y%m%d')}-{short_id}"

    # Create order
    order_result = supabase.table("orders").insert({
        "order_number": order_number,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "customer_email": customer_email,
        "customer_address": customer_address,
        "total_amount": total_amount,
        "notes": notes,
        "status": "pending",
    }).execute()

    if not order_result.data:
        return {"success": False, "error": "Lỗi hệ thống khi tạo đơn hàng."}

    order_id = order_result.data[0]["id"]

    # Create order items
    for oi in order_items:
        oi["order_id"] = order_id
    supabase.table("order_items").insert(order_items).execute()

    # Decrease inventory
    for item in items:
        inv = supabase.table("inventory").select("quantity").eq("sku", item["sku"]).execute()
        if inv.data:
            new_qty = inv.data[0]["quantity"] - item["quantity"]
            supabase.table("inventory").update({"quantity": new_qty}).eq("sku", item["sku"]).execute()

    return {
        "success": True,
        "order_number": order_number,
        "total_amount": total_amount,
        "items_count": len(order_items),
        "status": "pending",
        "message": f"Đơn hàng {order_number} đã được tạo thành công! Tổng tiền: {total_amount:,.0f} VNĐ.",
    }


async def lookup_order(order_number: str) -> dict:
    """Look up an existing order by order number.

    Args:
        order_number: The order number (e.g. ORD-20260327-ABC123).

    Returns:
        dict with order details.
    """
    supabase = get_supabase_client()
    result = supabase.table("orders").select("*").eq("order_number", order_number).execute()
    if not result.data:
        return {"found": False, "message": f"Không tìm thấy đơn hàng '{order_number}'."}

    order = result.data[0]
    items = supabase.table("order_items").select("*").eq("order_id", order["id"]).execute()

    return {
        "found": True,
        "order_number": order["order_number"],
        "customer_name": order["customer_name"],
        "status": order["status"],
        "total_amount": float(order["total_amount"]),
        "items": [
            {"name": i["product_name"], "qty": i["quantity"], "price": float(i["unit_price"])}
            for i in (items.data or [])
        ],
        "created_at": order["created_at"],
    }


order_agent = Agent(
    name="order_agent",
    model=get_llm_model(),
    description="Thu thập thông tin và tạo đơn hàng. Tra cứu đơn hàng đã có.",
    instruction="""Bạn là trợ lý đặt hàng.

Nhiệm vụ:
1. Thu thập đầy đủ thông tin đặt hàng từ khách:
   - Sản phẩm (SKU) và số lượng
   - Tên khách hàng
   - Số điện thoại
   - Địa chỉ giao hàng
2. Kiểm tra sản phẩm có sẵn bằng tool lookup_product_for_order.
3. Tạo đơn hàng bằng tool create_order khi đã đủ thông tin.
4. Tra cứu đơn hàng bằng tool lookup_order.

Quy tắc:
- PHẢI thu thập đủ: tên, SĐT, địa chỉ, sản phẩm + số lượng trước khi tạo đơn.
- Nếu thiếu thông tin, hỏi lại khách.
- Xác nhận lại đơn hàng trước khi tạo.
- Sử dụng lookup_product_for_order để kiểm tra giá và tồn kho trước.
- Trả lời bằng tiếng Việt, lịch sự.
""",
    tools=[
        FunctionTool(lookup_product_for_order),
        FunctionTool(create_order),
        FunctionTool(lookup_order),
    ],
)

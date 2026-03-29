"""Order API routes."""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.config import get_supabase_client
from app.models.schemas import OrderCreate, OrderResponse

router = APIRouter(prefix="/api/orders", tags=["orders"])


def generate_order_number() -> str:
    """Generate a unique order number."""
    now = datetime.now()
    short_id = uuid.uuid4().hex[:6].upper()
    return f"ORD-{now.strftime('%Y%m%d')}-{short_id}"


@router.post("", response_model=OrderResponse)
async def create_order(order: OrderCreate):
    """Create a new order with items."""
    supabase = get_supabase_client()

    # Validate all SKUs and get product info
    items_data = []
    total_amount = 0.0

    for item in order.items:
        product_result = (
            supabase.table("products")
            .select("id, name, sku, price")
            .eq("sku", item.sku)
            .eq("is_active", True)
            .execute()
        )
        if not product_result.data:
            raise HTTPException(
                status_code=400, detail=f"Product with SKU '{item.sku}' not found or inactive"
            )

        product = product_result.data[0]

        # Check inventory
        inv_result = supabase.table("inventory").select("quantity").eq("sku", item.sku).execute()
        if inv_result.data:
            available = inv_result.data[0]["quantity"]
            if available < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for '{product['name']}'. Available: {available}, Requested: {item.quantity}",
                )

        subtotal = product["price"] * item.quantity
        total_amount += subtotal
        items_data.append({
            "product_id": product["id"],
            "sku": product["sku"],
            "product_name": product["name"],
            "quantity": item.quantity,
            "unit_price": float(product["price"]),
            "subtotal": float(subtotal),
        })

    # Create order
    order_number = generate_order_number()
    order_result = supabase.table("orders").insert({
        "order_number": order_number,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "customer_email": order.customer_email,
        "customer_address": order.customer_address,
        "total_amount": float(total_amount),
        "notes": order.notes,
        "status": "pending",
    }).execute()

    if not order_result.data:
        raise HTTPException(status_code=500, detail="Failed to create order")

    order_id = order_result.data[0]["id"]

    # Create order items
    for item_data in items_data:
        item_data["order_id"] = order_id
    supabase.table("order_items").insert(items_data).execute()

    # Decrease inventory
    for item in order.items:
        inv = supabase.table("inventory").select("quantity").eq("sku", item.sku).execute()
        if inv.data:
            new_qty = inv.data[0]["quantity"] - item.quantity
            supabase.table("inventory").update({"quantity": new_qty}).eq("sku", item.sku).execute()

    # Return full order
    return await get_order(order_id)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    """Get order details with items."""
    supabase = get_supabase_client()

    order_result = supabase.table("orders").select("*").eq("id", order_id).execute()
    if not order_result.data:
        raise HTTPException(status_code=404, detail="Order not found")

    order = order_result.data[0]

    # Get order items
    items_result = supabase.table("order_items").select("*").eq("order_id", order_id).execute()
    order["items"] = items_result.data or []

    return order


@router.get("")
async def list_orders(status: str | None = None, limit: int = 50, offset: int = 0):
    """List orders with optional status filter."""
    supabase = get_supabase_client()
    query = supabase.table("orders").select("*")
    if status:
        query = query.eq("status", status)
    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return result.data or []

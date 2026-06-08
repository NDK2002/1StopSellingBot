"""Inventory API routes."""

from fastapi import APIRouter, HTTPException

from app.config import get_supabase_client
from app.models.schemas import InventoryResponse, InventoryUpsert

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.post("", response_model=InventoryResponse)
async def upsert_inventory(inv: InventoryUpsert):
    """Create or update inventory for a product by SKU."""
    supabase = get_supabase_client()

    # Find product by SKU
    product_result = supabase.table("products").select("id").eq("sku", inv.sku).execute()
    if not product_result.data:
        raise HTTPException(status_code=404, detail=f"Product with SKU '{inv.sku}' not found")

    product_id = product_result.data[0]["id"]

    # Upsert inventory
    result = supabase.table("inventory").upsert(
        {
            "product_id": product_id,
            "sku": inv.sku,
            "quantity": inv.quantity,
            "low_stock_threshold": inv.low_stock_threshold,
        },
        on_conflict="sku",
    ).execute()

    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to upsert inventory")
    return result.data[0]


@router.get("/{sku}", response_model=InventoryResponse)
async def get_inventory(sku: str):
    """Get inventory for a specific SKU."""
    supabase = get_supabase_client()
    result = supabase.table("inventory").select("*").eq("sku", sku).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail=f"Inventory for SKU '{sku}' not found")
    return result.data[0]


@router.get("")
async def list_inventory(low_stock_only: bool = False):
    """List all inventory, optionally filtered to low-stock items."""
    supabase = get_supabase_client()
    if low_stock_only:
        # Use RPC or raw query for column comparison
        result = supabase.rpc("get_low_stock_inventory").execute()
    else:
        result = supabase.table("inventory").select("*, products!inventory_product_id_fkey(name, category)").execute()
    return result.data or []

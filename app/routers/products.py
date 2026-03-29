"""Product CRUD API routes."""

from fastapi import APIRouter, HTTPException

from app.config import get_supabase_client
from app.models.schemas import ProductCreate, ProductResponse, ProductUpdate
from app.services.embedding import build_product_text, create_embedding

router = APIRouter(prefix="/api/products", tags=["products"])


@router.post("", response_model=ProductResponse)
async def create_product(product: ProductCreate):
    """Create a new product."""
    supabase = get_supabase_client()
    data = product.model_dump()
    result = supabase.table("products").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to create product")
    return result.data[0]


@router.get("", response_model=list[ProductResponse])
async def list_products(
    category: str | None = None,
    is_active: bool | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """List all products with optional filters."""
    supabase = get_supabase_client()
    query = supabase.table("products").select("*")
    if category:
        query = query.eq("category", category)
    if is_active is not None:
        query = query.eq("is_active", is_active)
    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return result.data


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """Get a single product by ID."""
    supabase = get_supabase_client()
    result = supabase.table("products").select("*").eq("id", product_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Product not found")
    return result.data[0]


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, product: ProductUpdate):
    """Update a product."""
    supabase = get_supabase_client()
    data = product.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = supabase.table("products").update(data).eq("id", product_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Product not found")
    return result.data[0]


@router.delete("/{product_id}")
async def delete_product(product_id: str):
    """Delete a product."""
    supabase = get_supabase_client()
    result = supabase.table("products").delete().eq("id", product_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted", "id": product_id}


# ── Embedding endpoints ──────────────────────────────────────────────

@router.post("/{product_id}/embed")
async def embed_product(product_id: str):
    """Embed a single product's info into pgvector."""
    supabase = get_supabase_client()

    # Get product
    result = supabase.table("products").select("*").eq("id", product_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Product not found")

    product = result.data[0]
    text = build_product_text(product)
    embedding = await create_embedding(text)

    # Upsert embedding
    supabase.table("product_embeddings").upsert(
        {
            "product_id": product_id,
            "content": text,
            "embedding": embedding,
        },
        on_conflict="product_id",
    ).execute()

    return {"message": "Product embedded", "product_id": product_id}


@router.post("/embed-all")
async def embed_all_products():
    """Embed all active products."""
    supabase = get_supabase_client()
    result = supabase.table("products").select("*").eq("is_active", True).execute()
    products = result.data or []

    count = 0
    for product in products:
        text = build_product_text(product)
        embedding = await create_embedding(text)
        supabase.table("product_embeddings").upsert(
            {
                "product_id": product["id"],
                "content": text,
                "embedding": embedding,
            },
            on_conflict="product_id",
        ).execute()
        count += 1

    return {"message": f"Embedded {count} products", "count": count}

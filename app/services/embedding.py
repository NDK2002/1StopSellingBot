"""Embedding service using Google's gemini-embedding-001 model."""

from google import genai
from google.genai import types
from app.config import get_settings

EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768


def get_genai_client() -> genai.Client:
    settings = get_settings()
    return genai.Client(api_key=settings.google_api_key)


async def create_embedding(text: str) -> list[float]:
    """Create embedding for a text using gemini-embedding-001."""
    client = get_genai_client()
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
    )
    return list(result.embeddings[0].values)


async def create_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Create embeddings for multiple texts."""
    client = get_genai_client()
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
    )
    return [list(e.values) for e in result.embeddings]


def build_product_text(product: dict) -> str:
    """Build a text representation of a product for embedding."""
    parts = [
        f"Tên sản phẩm: {product.get('name', '')}",
        f"SKU: {product.get('sku', '')}",
    ]
    if product.get("description"):
        parts.append(f"Mô tả: {product['description']}")
    if product.get("category"):
        parts.append(f"Danh mục: {product['category']}")
    if product.get("price"):
        parts.append(f"Giá: {product['price']:,.0f} VNĐ")
    if product.get("attributes"):
        attrs = ", ".join(f"{k}: {v}" for k, v in product["attributes"].items())
        parts.append(f"Thuộc tính: {attrs}")
    return "\n".join(parts)

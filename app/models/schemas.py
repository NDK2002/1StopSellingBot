"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Products ──────────────────────────────────────────────────────────
class ProductCreate(BaseModel):
    name: str
    sku: str
    description: str | None = None
    category: str | None = None
    attributes: dict = Field(default_factory=dict)
    price: float = 0.0
    image_url: str | None = None
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    attributes: dict | None = None
    price: float | None = None
    image_url: str | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: str
    name: str
    sku: str
    description: str | None = None
    category: str | None = None
    attributes: dict = Field(default_factory=dict)
    price: float
    image_url: str | None = None
    is_active: bool
    created_at: str
    updated_at: str


# ── Inventory ─────────────────────────────────────────────────────────
class InventoryUpsert(BaseModel):
    sku: str
    quantity: int
    low_stock_threshold: int = 10


class InventoryResponse(BaseModel):
    id: str
    product_id: str
    sku: str
    quantity: int
    low_stock_threshold: int
    updated_at: str


# ── Orders ────────────────────────────────────────────────────────────
class OrderItemCreate(BaseModel):
    sku: str
    quantity: int = 1


class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: str | None = None
    customer_email: str | None = None
    customer_address: str | None = None
    items: list[OrderItemCreate]
    notes: str | None = None


class OrderItemResponse(BaseModel):
    id: str
    product_id: str
    sku: str
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float


class OrderResponse(BaseModel):
    id: str
    order_number: str
    customer_name: str
    customer_phone: str | None = None
    customer_email: str | None = None
    customer_address: str | None = None
    status: str
    total_amount: float
    notes: str | None = None
    items: list[OrderItemResponse] = Field(default_factory=list)
    created_at: str
    updated_at: str


# ── RAG ───────────────────────────────────────────────────────────────
class RAGDocumentCreate(BaseModel):
    title: str
    content: str
    doc_type: str = "text"
    metadata: dict = Field(default_factory=dict)


class RAGDocumentUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    metadata: dict | None = None


class RAGDocumentResponse(BaseModel):
    id: str
    title: str
    content: str | None = None
    doc_type: str
    file_path: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: str
    updated_at: str


# ── Chat ──────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str

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
    escalated: bool = False


# ── Staff (Phase 2) ──────────────────────────────────────────────────
class StaffCreate(BaseModel):
    name: str
    email: str | None = None
    telegram_chat_id: str | None = None
    skills: list[str] = Field(default_factory=list)
    is_available: bool = True
    max_concurrent: int = 5
    password: str | None = None
    role: str = "staff"


class StaffUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    telegram_chat_id: str | None = None
    skills: list[str] | None = None
    is_available: bool | None = None
    max_concurrent: int | None = None
    password: str | None = None
    role: str | None = None


class StaffResponse(BaseModel):
    id: str
    name: str
    email: str | None = None
    telegram_chat_id: str | None = None
    skills: list[str] = Field(default_factory=list)
    is_available: bool
    max_concurrent: int
    current_load: int
    role: str | None = None
    created_at: str
    updated_at: str


# ── Escalation (Phase 2) ─────────────────────────────────────────────
class EscalationCreate(BaseModel):
    session_id: str
    reason: str = "low_confidence"
    skill_required: str | None = None
    customer_summary: str | None = None


class EscalationUpdate(BaseModel):
    status: str | None = None
    staff_notes: str | None = None

class EscalationAssign(BaseModel):
    new_staff_id: str


class EscalationResponse(BaseModel):
    id: str
    session_id: str
    staff_id: str | None = None
    reason: str
    status: str
    skill_required: str | None = None
    priority: int
    customer_summary: str | None = None
    staff_notes: str | None = None
    assigned_at: str | None = None
    resolved_at: str | None = None
    created_at: str
    updated_at: str


class TakeoverMessage(BaseModel):
    """Staff sends a message to customer via admin takeover."""
    session_id: str
    message: str


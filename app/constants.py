"""Application-wide constants."""

SKILLS: list[dict] = [
    {"key": "order_support",     "label": "Đơn hàng"},
    {"key": "inventory_support", "label": "Nhân viên kho"},
    {"key": "technical_support", "label": "Kỹ thuật / Bảo hành"},
    {"key": "product_support",   "label": "Tư vấn sản phẩm"},
    {"key": "general_support",   "label": "Hỗ trợ chung"},
]

SKILL_KEYS: list[str] = [s["key"] for s in SKILLS]

SKILL_FALLBACK = "general_support"

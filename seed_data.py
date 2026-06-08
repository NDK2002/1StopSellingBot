"""Seed data script — creates sample products, inventory, and RAG documents."""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import get_supabase_client
from app.services.embedding import build_product_text, create_embedding
from app.services.rag import index_document


SAMPLE_PRODUCTS = [
    {
        "name": "Áo thun nam basic cotton",
        "sku": "AT001",
        "description": "Áo thun nam basic chất liệu cotton 100%, thoáng mát, phù hợp mặc hàng ngày. Có các size S, M, L, XL.",
        "category": "Áo thun",
        "attributes": {"chất liệu": "cotton 100%", "size": "S, M, L, XL", "màu": "trắng, đen, xám, navy"},
        "price": 199000,
        "is_active": True,
    },
    {
        "name": "Áo thun nữ cổ tròn",
        "sku": "AT002",
        "description": "Áo thun nữ cổ tròn, phom slim fit, chất liệu cotton pha spandex co giãn tốt.",
        "category": "Áo thun",
        "attributes": {"chất liệu": "cotton pha spandex", "size": "S, M, L", "màu": "hồng, trắng, đen"},
        "price": 179000,
        "is_active": True,
    },
    {
        "name": "Quần jeans nam slim fit",
        "sku": "QJ001",
        "description": "Quần jeans nam dáng slim fit, vải denim cao cấp, co giãn nhẹ, thoải mái vận động.",
        "category": "Quần jeans",
        "attributes": {"chất liệu": "denim co giãn", "size": "29, 30, 31, 32, 33, 34", "màu": "xanh đậm, xanh nhạt"},
        "price": 450000,
        "is_active": True,
    },
    {
        "name": "Giày sneaker nam trắng",
        "sku": "GS001",
        "description": "Giày sneaker nam trắng, đế cao su chống trượt. Phù hợp đi học, đi chơi, mặc với nhiều phong cách.",
        "category": "Giày dép",
        "attributes": {"chất liệu": "da PU", "size": "39, 40, 41, 42, 43", "màu": "trắng"},
        "price": 650000,
        "is_active": True,
    },
    {
        "name": "Ba lô laptop 15.6 inch",
        "sku": "BL001",
        "description": "Ba lô đựng laptop 15.6 inch, chống nước, nhiều ngăn tiện dụng. Có đệm lưng thoáng khí.",
        "category": "Phụ kiện",
        "attributes": {"chất liệu": "polyester chống nước", "kích thước": "laptop 15.6 inch", "màu": "đen, xám"},
        "price": 350000,
        "is_active": True,
    },
]

SAMPLE_INVENTORY = [
    {"sku": "AT001", "quantity": 150, "low_stock_threshold": 20},
    {"sku": "AT002", "quantity": 100, "low_stock_threshold": 15},
    {"sku": "QJ001", "quantity": 80, "low_stock_threshold": 10},
    {"sku": "GS001", "quantity": 50, "low_stock_threshold": 10},
    {"sku": "BL001", "quantity": 30, "low_stock_threshold": 5},
]

SAMPLE_RAG_DOCS = [
    {
        "title": "Chính sách đổi trả",
        "content": """# Chính sách đổi trả hàng

## Điều kiện đổi trả
- Sản phẩm còn nguyên tem, nhãn mác, chưa qua sử dụng.
- Thời gian đổi trả: trong vòng 7 ngày kể từ ngày nhận hàng.
- Sản phẩm lỗi do nhà sản xuất được đổi miễn phí.
- Sản phẩm đổi size: miễn phí 1 lần, từ lần thứ 2 khách chịu phí ship.

## Quy trình đổi trả
1. Liên hệ hotline hoặc chat với bot để yêu cầu đổi trả.
2. Cung cấp mã đơn hàng và lý do đổi trả.
3. Gửi hàng về kho theo hướng dẫn.
4. Nhận hàng mới hoặc hoàn tiền trong 3-5 ngày làm việc.

## Các trường hợp KHÔNG được đổi trả
- Sản phẩm đã qua sử dụng, giặt, hoặc có mùi.
- Sản phẩm sale off trên 50%.
- Đồ lót, tất, khẩu trang.
- Quà tặng kèm.

## Hoàn tiền
- Hoàn tiền qua chuyển khoản ngân hàng trong 3-5 ngày làm việc.
- Hoàn tiền 100% nếu lỗi do shop.
- Hoàn tiền trừ phí ship nếu lỗi do khách.""",
        "doc_type": "text",
    },
    {
        "title": "Chính sách bảo hành",
        "content": """# Chính sách bảo hành

## Thời gian bảo hành
- Giày dép: bảo hành 3 tháng lỗi keo, đứt chỉ.
- Ba lô, túi xách: bảo hành 6 tháng lỗi khóa kéo, đường may.
- Quần áo: bảo hành 1 tháng lỗi đường may, nút, khóa.

## Điều kiện bảo hành
- Sản phẩm bị lỗi do nhà sản xuất.
- Còn phiếu bảo hành hoặc hóa đơn mua hàng.
- Chưa qua sửa chữa bởi bên thứ 3.

## Không áp dụng bảo hành
- Hư hỏng do sử dụng sai cách.
- Phai màu do giặt sai hướng dẫn.
- Hết thời hạn bảo hành.""",
        "doc_type": "text",
    },
    {
        "title": "Hướng dẫn mua hàng và vận chuyển",
        "content": """# Hướng dẫn mua hàng

## Cách đặt hàng
1. Chọn sản phẩm và cho vào giỏ hàng.
2. Cung cấp thông tin: tên, số điện thoại, địa chỉ giao hàng.
3. Xác nhận đơn hàng.
4. Thanh toán khi nhận hàng (COD) hoặc chuyển khoản trước.

## Phí vận chuyển
- Nội thành TP.HCM: 20.000 VNĐ (miễn phí đơn trên 500.000 VNĐ).
- Ngoại thành TP.HCM: 30.000 VNĐ.
- Các tỉnh khác: 30.000 - 50.000 VNĐ tùy khu vực.
- Miễn phí ship toàn quốc cho đơn hàng trên 1.000.000 VNĐ.

## Thời gian giao hàng
- Nội thành: 1-2 ngày.
- Ngoại thành: 2-3 ngày.
- Tỉnh khác: 3-5 ngày.

## Phương thức thanh toán
- Thanh toán khi nhận hàng (COD).
- Chuyển khoản ngân hàng.
- Ví điện tử: Momo, ZaloPay, VNPay.""",
        "doc_type": "text",
    },
]


async def seed():
    print("🌱 Cleaning existing data...")
    supabase = get_supabase_client()
    
    # Order matters for foreign keys
    # Use id > 0 for integer IDs or neq for UUIDs/strings
    supabase.table("order_items").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    supabase.table("orders").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    supabase.table("inventory").delete().neq("sku", "0").execute()
    supabase.table("product_embeddings").delete().neq("content", "").execute()
    supabase.table("products").delete().neq("sku", "0").execute()
    supabase.table("rag_chunks").delete().neq("content", "").execute()
    supabase.table("rag_documents").delete().neq("title", "").execute()
    
    # New deletions to avoid FK errors
    supabase.table("conversations").delete().neq("session_id", "").execute()
    supabase.table("escalations").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    
    supabase.table("staff").delete().eq("email", "manager@gmail.com").execute()

    print("🌱 Seeding database...")
    # 1. Create products
    print("  📦 Creating products...")
    for product in SAMPLE_PRODUCTS:
        result = supabase.table("products").insert(product).execute()
        print(f"    ✅ {product['name']} ({product['sku']})")

    # 2. Create inventory
    print("  📊 Creating inventory...")
    for inv in SAMPLE_INVENTORY:
        product = supabase.table("products").select("id").eq("sku", inv["sku"]).execute()
        if product.data:
            supabase.table("inventory").insert(
                {**inv, "product_id": product.data[0]["id"]},
            ).execute()
            print(f"    ✅ {inv['sku']}: {inv['quantity']} units")

    # 3. Embed products
    print("  🧠 Embedding products...")
    products = supabase.table("products").select("*").eq("is_active", True).execute()
    for p in products.data:
        text = build_product_text(p)
        embedding = await create_embedding(text)
        supabase.table("product_embeddings").insert(
            {"product_id": p["id"], "content": text, "embedding": embedding},
        ).execute()
        print(f"    ✅ Embedded: {p['name']}")

    # 4. Create and index RAG documents
    print("  📄 Creating RAG documents...")
    for doc in SAMPLE_RAG_DOCS:
        result = supabase.table("rag_documents").insert({
            "title": doc["title"],
            "content": doc["content"],
            "doc_type": doc["doc_type"],
        }).execute()
        if result.data:
            doc_id = result.data[0]["id"]
            chunk_count = await index_document(doc_id, doc["content"])
            print(f"    ✅ {doc['title']} ({chunk_count} chunks)")

    # 5. Create sample users
    print("  👥 Creating users...")
    users = [
        {
            "name": "Manager",
            "email": "manager@gmail.com",
            "telegram_chat_id": "123",
            "skills": ["order_support", "inventory_support", "technical_support", "product_support", "general_support"],
            "is_available": True,
            "max_concurrent": 5,
            "current_load": 0,
            "created_at": "2026-03-29 05:48:23.413863+00",
            "updated_at": "2026-06-06 06:51:38.837294+00",
            "password_hash": "$2b$12$lTU2h5dV.2wo87oL2wOetO1RcYIU6TK21dFr9eQZ1DmRIfSlLUNWq", # 123456
            "role": "admin"
        }
    ]
    for user in users:
        result = supabase.table("staff").insert(user).execute()
        print(f"    ✅ {user['name']} ({user['role']})")

    print("\n✅ Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())

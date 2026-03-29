# 1StopSellingBot — MVP Phase 1

Hệ thống Chatbot Hỗ trợ Mua hàng thông minh sử dụng Google ADK multi-agent.

## Tech Stack
- **FastAPI** — Backend API
- **Google ADK** — Multi-agent framework
- **Gemini 2.0 Flash** — LLM chính
- **text-embedding-004** — Embeddings
- **Supabase** — Database (Postgres + pgvector)
- **Streamlit** — Demo UI

## Cấu trúc Project

```
app/
├── main.py              # FastAPI entry point
├── config.py            # Settings & Supabase client
├── routers/
│   ├── products.py      # CRUD products + embedding
│   ├── inventory.py     # Inventory management
│   ├── orders.py        # Order creation & lookup
│   ├── rag.py           # RAG document management
│   └── chat.py          # Chat endpoint (ADK agents)
├── services/
│   ├── embedding.py     # Google embedding service
│   └── rag.py           # RAG chunking & retrieval
├── agents/
│   ├── advisor.py       # Product & policy Q&A
│   ├── inventory_agent.py  # Stock checking
│   ├── order_agent.py   # Order creation
│   └── orchestrator.py  # Root agent (router)
└── models/
    └── schemas.py       # Pydantic schemas

streamlit_app.py         # Streamlit chat UI
seed_data.py             # Sample data seeder
```

## Setup

### 1. Cấu hình environment

```bash
cp .env.example .env
```

Điền các giá trị vào file `.env`:
- `SUPABASE_URL` — URL của Supabase project
- `SUPABASE_ANON_KEY` — Anon key
- `SUPABASE_SERVICE_ROLE_KEY` — Service role key (optional)
- `GOOGLE_API_KEY` — Google AI API key

### 2. Cài dependencies

```bash
uv sync
```

### 3. Seed dữ liệu mẫu

```bash
uv run python seed_data.py
```

### 4. Chạy FastAPI server

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### 5. Chạy Streamlit UI

```bash
uv run streamlit run streamlit_app.py
```

## API Endpoints

### Products
- `POST /api/products` — Tạo sản phẩm
- `GET /api/products` — Danh sách sản phẩm
- `GET /api/products/{id}` — Chi tiết sản phẩm
- `PUT /api/products/{id}` — Cập nhật sản phẩm
- `DELETE /api/products/{id}` — Xóa sản phẩm
- `POST /api/products/{id}/embed` — Embed 1 sản phẩm
- `POST /api/products/embed-all` — Embed tất cả

### Inventory
- `POST /api/inventory` — Tạo/cập nhật tồn kho
- `GET /api/inventory/{sku}` — Xem tồn kho theo SKU

### Orders
- `POST /api/orders` — Tạo đơn hàng
- `GET /api/orders/{id}` — Chi tiết đơn hàng

### RAG
- `POST /api/rag/upload` — Upload tài liệu RAG
- `PUT /api/rag/{id}` — Cập nhật tài liệu
- `POST /api/rag/{id}/reindex` — Re-index tài liệu
- `GET /api/rag/documents` — Danh sách tài liệu
- `DELETE /api/rag/{id}` — Xóa tài liệu

### Chat
- `POST /api/chat` — Gửi tin nhắn
- `DELETE /api/chat/sessions/{id}` — Reset session

## Agents

| Agent | Chức năng |
|-------|-----------|
| `root_agent` | Điều phối, phân tích yêu cầu → route |
| `advisor_agent` | Tư vấn sản phẩm, chính sách (RAG) |
| `inventory_agent` | Kiểm tra tồn kho |
| `order_agent` | Tạo và tra cứu đơn hàng |

## Test Scenarios

```
"Áo thun nam còn hàng không?"
"Cho tôi biết chính sách đổi trả."
"Tôi muốn mua 2 cái áo thun size M."
"Tạo đơn hàng cho tôi với tên Nguyễn Văn A, SĐT 0901234567, địa chỉ 123 Lê Lợi Q1 TPHCM"
```

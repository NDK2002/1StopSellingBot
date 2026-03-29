# Hệ thống Chatbot Hỗ trợ Mua hàng — Roadmap & Requirements

---

## Tech Stack

### Frontend
| Công nghệ | Vai trò |
|---|---|
| Preact + Vite | Chatbot widget nhúng, hỗ trợ embed nhiều nền tảng |
| Shadow DOM | Cô lập CSS của widget với website host |
| React + Vite + TypeScript | Admin Panel UI |
| shadcn/ui | Component library cho Admin Panel |

### Backend
| Công nghệ | Vai trò |
|---|---|
| FastAPI (Python, uv) | AI Backend — serve agents, RAG, webhook API |
| Google ADK | Multi-agent framework |
| Gemini 2.0 Flash | LLM chính cho chatbot, low-stock alert, draft trả lời |
| Gemini 2.5 Pro | Xử lý reasoning phức tạp, routing nâng cao |
| text-embedding-004 | Tạo embedding cho RAG pipeline |
| Docling | Parse file PDF/DOCX/CSV khi import RAG |
| aiogram | Telegram Bot nội bộ |
| Celery | Worker xử lý background jobs |
| Celery Beat | Periodic jobs như SLA check, usage metering |

### Admin / Business Backend
| Công nghệ | Vai trò |
|---|---|
| FastAPI | Admin Panel backend — CRUD, auth, RBAC |
| WebSockets (FastAPI) | Realtime inbox Admin Panel |
| Celery / Redis | Jobs nội bộ background |

### Database & Storage
| Công nghệ | Vai trò |
|---|---|
| Supabase Postgres | Primary database |
| Supabase pgvector | Vector DB cho RAG |
| Supabase Realtime | Stream dữ liệu real-time khi cần |
| Supabase Storage | Lưu file RAG upload |
| Redis | Queue jobs, idempotency key, low-stock flag, cache |

### Security & Integration
| Công nghệ | Vai trò |
|---|---|
| JWT HS256 | Authentication token cho Admin/Staff |
| HMAC-SHA256 | Xác thực webhook từ doanh nghiệp |
| Telegram Bot API | Push notification cho staff và admin |
| Stripe | Billing, subscription, usage metering ở Phase 5 |
| Cloudflare API | Provision subdomain tenant ở Phase 5 |
| Docker Compose | Local dev + staging |
| Cloud Run / Railway | Production deploy |

---

## Kiến trúc tổng quan

```text
[Khách hàng]
    └── Chatbot Widget (Preact)
            │ WebSocket / HTTP
            ▼
    [FastAPI + Google ADK]
    ├── advisor_agent     ← RAG (pgvector Hybrid Search)
    ├── inventory_agent   ← Tool calling (Supabase Postgres)
    └── order_agent       ← Tool calling (Supabase Postgres)
            │
            ├── confidence thấp → Escalation Engine
            │       └── Skill-based routing → Telegram notify nhân viên
            │
            └── inventory xuống thấp → Low-stock Alert → Telegram notify admin

    [React + Vite + shadcn/ui]
    └── Admin Panel
        ├── /conversations  ← Inbox takeover realtime
        ├── /config/*       ← Chatbot, RAG, Staff, Widget, Integrations
        └── /reports        ← Hiệu suất nhân viên

    [Supabase]
    ├── Postgres (primary DB)
    ├── pgvector (RAG)
    ├── Realtime
    └── Storage

    JWT HS256 shared secret → Auth tokens
```

---

# Hệ thống Chatbot Hỗ trợ Mua hàng — Roadmap & Requirements

---

## Tech Stack cập nhật

### Phase 1 MVP
| Công nghệ | Vai trò |
|---|---|
| Streamlit | Giao diện chat nội bộ để demo và test nhanh MVP |
| FastAPI | Backend API cho agents, products, inventory, orders, RAG |
| Google ADK | Multi-agent framework |
| Gemini 2.0 Flash | LLM chính cho chatbot MVP |
| text-embedding-004 | Tạo embedding cho product info và RAG |
| Supabase Postgres | Primary database |
| Supabase pgvector | Vector DB cho embeddings |
| Supabase Storage | Lưu file RAG nếu cần |

### Các phase sau
| Công nghệ | Vai trò |
|---|---|
| React + Vite + shadcn/ui | Admin Panel UI |
| FastAPI | Admin Panel Backend, RBAC, Realtime inbox |
| aiogram | Telegram Bot nội bộ |
| Celery + RabbitMQ | Background jobs |
| Stripe | Billing |
| Cloudflare API | Provision subdomain tenant |

---

## Mục tiêu cập nhật

Phase 1 được đơn giản hóa để ra MVP nhanh. Giai đoạn này chưa làm widget nhúng, chưa làm Telegram, chưa làm admin panel hoàn chỉnh; thay vào đó dùng Streamlit để test end-to-end và Postman để kiểm tra toàn bộ API.

---

## Kiến trúc MVP Phase 1

```text
[Postman] ───────► [FastAPI]
                       │
[Streamlit UI] ───► [Google ADK Agents]
                       │
                       ├── Supabase Postgres
                       ├── Supabase pgvector
                       └── Supabase Storage
```

---

## Phase 1 — MVP đơn giản (3–4 tuần)

### Công nghệ sử dụng trong Phase 1
| Công nghệ | Dùng để làm gì |
|---|---|
| Streamlit | UI chat nội bộ để kiểm tra chatbot |
| FastAPI | Expose API cho CRUD product, inventory, order, RAG |
| Google ADK | Tạo các agent và tool calling |
| Gemini 2.0 Flash | Trả lời chat, gọi tool, truy vấn RAG |
| text-embedding-004 | Embed product info và tài liệu RAG |
| Supabase Postgres | Lưu products, inventory, orders, conversations |
| Supabase pgvector | Lưu embedding của product info và RAG chunks |
| Supabase Storage | Lưu file upload cho RAG nếu cần |
| Postman | Tạo data test và kiểm tra API |

### Mục tiêu MVP
- Các agent được tạo và hoạt động đúng.
- Các API hoạt động đúng khi test bằng Postman.
- Có thể upload/update dữ liệu RAG qua API.
- Thông qua Streamlit có thể:
  - kiểm tra thông tin sản phẩm,
  - kiểm tra tồn kho,
  - truy cập chính sách đổi trả từ RAG,
  - tạo đơn hàng.

### Phạm vi Phase 1
Phase này chỉ làm phần cốt lõi để chứng minh hệ thống chạy được. Không bao gồm Telegram, human handoff, admin panel production, widget nhúng hay multi-tenant.

### 1. Setup nền tảng
- Tạo Supabase project.
- Enable `pgvector`.
- Tạo các bảng cơ bản:
  - `products`
  - `inventory`
  - `orders`
  - `rag_documents`
  - `rag_chunks`
- Cấu hình FastAPI kết nối Supabase.
- Cấu hình Google ADK trong FastAPI.
- Tạo Streamlit app để chat test nội bộ.

### 2. Agents cần có
Tạo tối thiểu 3 agent trong Google ADK:

#### `advisor_agent`
- Trả lời câu hỏi về sản phẩm.
- Trả lời câu hỏi về chính sách đổi trả, bảo hành, FAQ từ RAG.
- Có thể kết hợp product info đã embed.

#### `inventory_agent`
- Kiểm tra tồn kho theo SKU hoặc tên sản phẩm.
- Trả lời còn hàng/hết hàng/số lượng còn lại.

#### `order_agent`
- Thu thập thông tin đặt hàng.
- Tạo đơn hàng khi đã đủ thông tin.
- Có thể tra cứu thông tin đơn hàng cơ bản nếu cần.

### 3. API bắt buộc cho Postman

#### Product APIs
- `POST /api/products`
  - tạo sản phẩm mới.
- `GET /api/products`
  - lấy danh sách sản phẩm.
- `GET /api/products/{id}`
  - lấy chi tiết 1 sản phẩm.
- `PUT /api/products/{id}`
  - cập nhật sản phẩm.
- `DELETE /api/products/{id}`
  - xóa sản phẩm.

#### Inventory APIs
- `POST /api/inventory`
  - tạo hoặc cập nhật tồn kho.
- `GET /api/inventory/{sku}`
  - xem tồn kho theo SKU.

#### Product Embedding APIs
- `POST /api/products/{id}/embed`
  - embed thông tin 1 sản phẩm vào pgvector.
- `POST /api/products/embed-all`
  - embed lại toàn bộ sản phẩm.
- Khi product update có thể gọi lại embed API bằng Postman để re-index.

#### RAG APIs
- `POST /api/rag/upload`
  - upload file hoặc gửi text nội dung để tạo tài liệu RAG.
- `PUT /api/rag/{document_id}`
  - cập nhật tài liệu RAG.
- `POST /api/rag/{document_id}/reindex`
  - chunk + embed lại tài liệu sau update.
- `GET /api/rag/documents`
  - lấy danh sách tài liệu RAG.
- `DELETE /api/rag/{document_id}`
  - xóa tài liệu RAG.

#### Order APIs
- `POST /api/orders`
  - tạo đơn hàng.
- `GET /api/orders/{order_id}`
  - lấy chi tiết đơn hàng.

### 4. Yêu cầu embedding

#### Embed product info
Mỗi sản phẩm cần có dữ liệu để embed, tối thiểu gồm:
- tên sản phẩm,
- mô tả,
- category,
- thuộc tính chính,
- giá tham khảo.

Mục đích:
- cho phép agent tìm sản phẩm theo ngôn ngữ tự nhiên,
- hỗ trợ tư vấn khi user không biết SKU.

#### Embed RAG documents
Tài liệu như:
- chính sách đổi trả,
- chính sách bảo hành,
- FAQ,
- hướng dẫn mua hàng.

Các tài liệu này sẽ được:
- chunk,
- embed,
- lưu vào pgvector,
- retrieve khi advisor_agent cần trả lời.

### 5. Streamlit MVP UI
Streamlit chỉ dùng để demo và test nhanh, gồm:
- 1 màn hình chat chính,
- ô nhập câu hỏi,
- vùng hiển thị lịch sử chat,
- nút reset hội thoại,
- có thể hiển thị tool result đơn giản nếu cần.

Các test scenario cần chạy được trên Streamlit:
- “Áo thun nam còn hàng không?”
- “Cho tôi biết chính sách đổi trả.”
- “Tôi muốn mua 2 cái áo thun size M.”
- “Tạo đơn hàng cho tôi với tên..., số điện thoại..., địa chỉ...”

### 6. MVP Acceptance Criteria
MVP được xem là hoàn thành khi:
- Có ít nhất 3 agents hoạt động trong Google ADK.
- CRUD product chạy đúng bằng Postman.
- API inventory chạy đúng bằng Postman.
- API upload/update/reindex RAG chạy đúng bằng Postman.
- Có thể embed product info và truy vấn được trong chat.
- Streamlit chat có thể:
  - hỏi thông tin sản phẩm,
  - hỏi tồn kho,
  - hỏi chính sách đổi trả từ RAG,
  - tạo đơn hàng.

### Deliverables Phase 1
- Source code FastAPI.
- Source code Streamlit demo app.
- Google ADK agent definitions.
- Bộ Postman collection.
- Schema Supabase cho MVP.
- Tài liệu hướng dẫn test local.

---

## Phase 2 — Escalation & Telegram (3–4 tuần)

### Mục tiêu
Sau khi MVP ổn định, bổ sung cơ chế human handoff.

### Công nghệ sử dụng
| Công nghệ | Mục đích |
|---|---|
| FastAPI | Escalation engine |
| aiogram | Telegram Bot nội bộ |
| JWT HS256 | Deep link takeover |
| Supabase Postgres | Staff, skills, conversations |

### Phạm vi
- Skill-based routing cho staff.
- Telegram notification cho staff.
- Deep link mở thẳng conversation.

---

## Phase 3 — Admin Panel & Production UI (4–5 tuần)

### Mục tiêu
Thay Streamlit bằng giao diện vận hành production.

### Công nghệ sử dụng
| Công nghệ | Mục đích |
|---|---|
| FastAPI | Backend Admin Panel & RBAC |
| React + Vite + shadcn/ui | UI Admin Panel |
| WebSockets (FastAPI) | Realtime inbox |
| Preact + Vite | Widget production để embed |
| Supabase Storage | RAG upload |
| Celery + RabbitMQ | Background processing |

### Phạm vi
- `/conversations` cho takeover.
- `/config/chatbot`, `/config/rag`, `/config/staff`, `/config/widget`.
- Widget production-ready thay cho Streamlit.

---

## Phase 4 — Đo lường hiệu suất (3–4 tuần)

### Mục tiêu
Đo hiệu suất phản hồi và chất lượng xử lý của nhân viên.

### Công nghệ sử dụng
| Công nghệ | Mục đích |
|---|---|
| Supabase Postgres | Lưu event logs |
| React + Vite + shadcn/ui | Dashboard báo cáo |
| Celery Beat | SLA check |
| aiogram | Notify supervisor |

### Phạm vi
- Event logging.
- FRT, Resolution Time, Missed Rate, CSAT.
- Dashboard báo cáo.
- SLA alert.

---

## Phase 5 — Multi-tenant SaaS Bridge (6–8 tuần)

### Mục tiêu
Biến hệ thống thành nền tảng dùng cho nhiều doanh nghiệp.

### Công nghệ sử dụng
| Công nghệ | Mục đích |
|---|---|
| Supabase Postgres + RLS | Multi-tenant isolation |
| FastAPI | Webhook bridge |
| HMAC-SHA256 | Xác thực webhook |
| Celery + RabbitMQ | Xử lý webhook async |
| React + Vite + shadcn/ui | Tenant onboarding + billing UI |
| Stripe | Subscription và usage metering |
| Cloudflare API | Provision subdomain |

### Phạm vi
- `tenant_id` cho toàn bộ dữ liệu.
- Webhook cho products, inventory, orders.
- RAG upload qua admin panel.
- Onboarding tenant mới.
- Billing và super admin portal.

---

## Tổng lộ trình

| Phase | Nội dung | Thời lượng |
|---|---|---|
| Phase 1 | MVP: Streamlit + Google ADK + FastAPI + Supabase | 3–4 tuần |
| Phase 2 | Escalation + Telegram + Low-stock Alert | 3–4 tuần |
| Phase 3 | Admin Panel + Production UI/Widget | 4–5 tuần |
| Phase 4 | Đo lường hiệu suất nhân viên | 3–4 tuần |
| Phase 5 | Multi-tenant SaaS Bridge | 6–8 tuần |

### Tổng thời gian
- Tuần tự: **19–25 tuần**
- Có thể rút ngắn nếu Phase 2–3 chồng một phần sau khi MVP ổn định.

---

## Ghi chú triển khai
- Phase 1 ưu tiên tốc độ ra MVP, không tối ưu kiến trúc sớm.
- Dùng Postman để seed data và test API trước khi làm admin panel.
- Streamlit chỉ là UI tạm cho MVP, không phải UI production.
- Product info và RAG được quản lý tách riêng: product thiên về structured data, RAG thiên về unstructured documents.
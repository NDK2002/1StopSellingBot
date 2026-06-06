# Design: Predefined Skill List for Escalation Routing

**Date:** 2026-06-07  
**Branch:** worktree-feature+predefined-skill-list  
**Status:** Approved

---

## Problem

When a customer requests to speak with a specific department (e.g., "nhân viên kho", "bộ phận vận chuyển"), the LLM hallucinates arbitrary `skill_required` values that don't match any staff skill in the database — causing escalation routing to fail or fall back incorrectly.

**Root cause:** `skill_required` in `request_human_support` is a free-form string. The LLM prompt only gave examples, not an enforced list.

**Teammate's partial fix (commit 9331468):**
- Updated orchestrator prompt to list specific skill values
- Changed `staff.tsx` from free-text input to checkbox with hardcoded `STAFF_SKILL_OPTIONS`
- Changed fallback in `escalation.py` from `"quản lý"` → `"general_support"`

**Remaining gaps:**
- Skill list is duplicated (hardcoded in `staff.tsx` AND in orchestrator prompt) — no single source of truth
- No `GET /api/skills` endpoint — frontend can't dynamically fetch the list
- No backend validation — `skill_required` still accepts any string
- Orchestrator prompt lacks Vietnamese labels to help LLM map customer intent to skill keys

---

## Skill List (agreed, using teammate's keys)

```python
SKILLS = [
    {"key": "order_support",     "label": "Đơn hàng"},
    {"key": "inventory_support", "label": "Nhân viên kho"},
    {"key": "technical_support", "label": "Kỹ thuật / Bảo hành"},
    {"key": "product_support",   "label": "Tư vấn sản phẩm"},
    {"key": "general_support",   "label": "Hỗ trợ chung (Fallback)"},
]
```

`"general_support"` is the fallback skill — used when no specific department is identified.

---

## Approach

**Hardcode in `app/constants.py`** (single source of truth). Chosen over database storage because:
- Department list rarely changes
- No DB migration needed
- Simpler for demo phase; easy to migrate to DB later

---

## Architecture

### 1. `app/constants.py` (new file)

Single source of truth for the skill list. Exports:
- `SKILLS` — list of `{"key": str, "label": str}` dicts
- `SKILL_KEYS` — list of valid key strings for validation

### 2. `GET /api/skills` (new endpoint in `app/routers/skills.py`)

Returns `SKILLS` list as JSON. Frontend fetches from here instead of hardcoding. No auth required (public metadata).

### 3. Backend validation in `app/agents/orchestrator.py`

In `request_human_support`, validate `skill_required` before passing to `create_escalation`:
- If value is in `SKILL_KEYS` → use as-is
- If value is empty or not in `SKILL_KEYS` → replace with `"general_support"`

### 4. Orchestrator prompt update

Inject skill list with Vietnamese labels so LLM can map customer intent to the correct key:

```
skill_required phải là một trong các giá trị sau (KHÔNG được dùng giá trị khác):
- "order_support"     → Khách có vấn đề về đơn hàng
- "inventory_support" → Khách hỏi về kho hàng, kiểm hàng
- "technical_support" → Kỹ thuật, bảo hành, lỗi sản phẩm
- "product_support"   → Tư vấn sản phẩm, giá cả
- "general_support"   → Không xác định được hoặc vấn đề chung
Nếu không chắc → dùng "general_support".
```

### 5. `admin-ui/src/routes/staff.tsx` update

Replace hardcoded `STAFF_SKILL_OPTIONS` with a `useQuery` that fetches from `GET /api/skills`. Checkbox UI stays the same — only the data source changes.

---

## Data Flow

```
Customer: "cho tôi gặp nhân viên kho"
    ↓
root_agent (sees skill list in prompt)
    ↓
request_human_support(skill_required="inventory_support")
    ↓
Backend validation: "inventory_support" ∈ SKILL_KEYS ✅
    ↓
create_escalation(skill_required="inventory_support")
    ↓
_find_best_staff: match staff with skill "inventory_support"
    ↓ (if no match)
fallback: staff with skill "general_support"
```

---

## Error Handling

- **LLM sends invalid skill:** silently replaced with `"general_support"` — never crashes, always routes somewhere
- **No staff with matching skill:** existing fallback to `general_support` staff in `_find_best_staff`
- **No staff available at all:** existing "nhân viên đang quá tải" response unchanged

---

## Files Changed

| File | Change |
|------|--------|
| `app/constants.py` | New — skill list source of truth |
| `app/routers/skills.py` | New — `GET /api/skills` endpoint |
| `app/main.py` | Register skills router |
| `app/agents/orchestrator.py` | Add validation + update prompt |
| `admin-ui/src/routes/staff.tsx` | Fetch skills from API instead of hardcode |

---

## Out of Scope

- Database-backed skill management (deferred to later phase)
- Backend validation on `StaffCreate`/`StaffUpdate` (staff skill validation — separate concern)
- Adding new skills via Admin UI (hardcoded for demo)

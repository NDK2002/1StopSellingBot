## Setup

### 1. Cấu hình environment

```bash
cp .env.example .env
```


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
make server
```

### 5. Chạy Streamlit UI

```bash
uv ui
```

### 6. Start Admin UI

```bash
make admin
```

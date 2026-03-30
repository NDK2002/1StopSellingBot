SHELL := /bin/bash

.PHONY: install seed server ui chat help

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

seed: ## Seed sample data
	uv run python seed_data.py

server: ## Start FastAPI server (port 8000)
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

ui: ## Start Streamlit chat UI
	uv run streamlit run streamlit_app.py

admin: ## Start Admin Panel React UI
	cd admin-ui && pnpm run dev

chat: ## Quick test chat via curl
	@read -p "Message: " msg; \
	curl -s -X POST http://localhost:8000/api/chat \
		-H "Content-Type: application/json" \
		-d "{\"message\": \"$$msg\"}" | python3 -m json.tool

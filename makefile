SHELL := /bin/bash

.PHONY: install seed server ui admin

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

"""FastAPI application entry point."""

# Load .env into OS environment BEFORE any other imports
# Google ADK reads GOOGLE_API_KEY from os.environ directly
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, escalation, inventory, orders, products, rag, staff

app = FastAPI(
    title="1StopSellingBot API",
    description="AI-powered shopping assistant with multi-agent architecture",
    version="0.2.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 1 routers
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(rag.router)
app.include_router(chat.router)

# Phase 2 routers
app.include_router(staff.router)
app.include_router(escalation.router)


@app.get("/")
async def root():
    return {
        "app": "1StopSellingBot",
        "version": "0.2.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}

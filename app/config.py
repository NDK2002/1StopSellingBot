"""Application configuration and Supabase client setup."""

from functools import lru_cache

from pydantic_settings import BaseSettings
from supabase import Client, create_client


class Settings(BaseSettings):
    """App settings loaded from environment variables."""

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str = ""
    google_api_key: str
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    groq_model: str = "groq/llama-3.3-70b-versatile"
    openrouter_model: str = "openrouter/google/gemini-2.0-flash-lite-001"
    telegram_bot_token: str = ""
    jwt_secret: str = "change-me-in-production"
    app_base_url: str = "http://localhost:8000"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    litellm_log: str = "ERROR"
    json_logs: str = "True"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_supabase_client() -> Client:
    """Create and return a Supabase client."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_supabase_admin_client() -> Client:
    """Create a Supabase client with service role key for admin operations."""
    settings = get_settings()
    key = settings.supabase_service_role_key or settings.supabase_anon_key
    return create_client(settings.supabase_url, key)

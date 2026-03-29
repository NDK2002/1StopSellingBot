"""LLM provider configuration — uses Groq via LiteLLM for Google ADK agents."""

import os

from google.adk.models.lite_llm import LiteLlm

from app.config import get_settings


def get_llm_model() -> LiteLlm:
    settings = get_settings()
    return LiteLlm(model=settings.openrouter_model)

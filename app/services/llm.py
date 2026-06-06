"""LLM provider configuration — uses LiteLLM for Google ADK agents."""

import os

from google.adk.models.lite_llm import LiteLlm

from app.config import get_settings


def get_llm_model() -> LiteLlm:
    settings = get_settings()
    litellm = LiteLlm(model=settings.openrouter_model)
    return litellm

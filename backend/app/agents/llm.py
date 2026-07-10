from typing import Literal

from langchain_openai import ChatOpenAI

from app.core.config import get_settings


def get_llm(role: Literal["planner", "summarizer", "validator"]) -> ChatOpenAI:
    """Factory for role-specific LLM clients. Used in Phase 2 agent nodes."""
    settings = get_settings()
    model_map = {
        "planner": settings.PLANNER_MODEL,
        "summarizer": settings.SUMMARIZER_MODEL,
        "validator": settings.VALIDATOR_MODEL,
    }
    temperature = 0.2 if role == "summarizer" else 0.0
    return ChatOpenAI(
        model=model_map[role],
        temperature=temperature,
        timeout=settings.LLM_TIMEOUT_SECONDS,
        max_retries=2,
        api_key=settings.OPENAI_API_KEY,
    )

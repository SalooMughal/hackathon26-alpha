from functools import lru_cache
from typing import Literal, TypeVar

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.core.config import get_settings

Role = Literal["sanitizer", "planner", "summarizer", "validator"]
SchemaT = TypeVar("SchemaT", bound=BaseModel)


@lru_cache
def get_llm(role: Role) -> ChatOpenAI:
    """Build a role-specific ChatOpenAI client on demand."""
    settings = get_settings()
    model_map = {
        "sanitizer": settings.SANITIZER_MODEL,
        "planner": settings.PLANNER_MODEL,
        "summarizer": settings.SUMMARIZER_MODEL,
        "validator": settings.VALIDATOR_MODEL,
    }
    temperature = 0.2 if role == "summarizer" else 0.0
    return ChatOpenAI(
        model=model_map[role],
        temperature=temperature,
        timeout=settings.LLM_TIMEOUT_SECONDS,
        max_retries=settings.LLM_MAX_RETRIES,
        api_key=settings.OPENAI_API_KEY,
    )


def get_structured_llm(role: Role, schema: type[SchemaT]):
    """Structured-output LLM for sanitizer, planner, and validator roles."""
    return get_llm(role).with_structured_output(schema, include_raw=True)

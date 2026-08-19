from typing import Optional

from langchain_groq import ChatGroq

from app.core.config import settings


def create_groq_chat(
    *,
    api_key: Optional[str] = None,
    temperature: float = 0.1,
) -> ChatGroq:
    """Create a consistently configured Groq chat model for the application."""
    return ChatGroq(
        api_key=api_key or settings.GROQ_API_KEY,
        model=settings.LLM_MODEL_NAME_GROQ,
        temperature=temperature,
        reasoning_effort=settings.GROQ_REASONING_EFFORT,
        model_kwargs={"include_reasoning": False},
    )

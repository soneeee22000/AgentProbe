"""Pydantic v2 request schemas for API endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SUPPORTED_PROVIDERS = Literal[
    "groq", "ollama", "openai", "anthropic", "google"
]


class RunRequest(BaseModel):
    """Request to start a new agent run."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The user's question",
    )
    model: str = Field(
        default="llama-3.1-8b-instant",
        description="LLM model ID",
    )
    provider: SUPPORTED_PROVIDERS = Field(
        default="groq",
        description="LLM provider",
    )
    max_steps: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum ReAct loop iterations",
    )


class RunListParams(BaseModel):
    """Query parameters for listing runs."""

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    model: str | None = Field(default=None)
    status: str | None = Field(default=None)

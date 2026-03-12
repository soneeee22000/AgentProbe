"""Pydantic v2 response schemas for API endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StepResponse(BaseModel):
    """Serialized agent step for API/SSE responses."""

    step_type: str
    content: str
    step_index: int
    timestamp: float
    tool_name: str | None = None
    tool_args: str | None = None
    failure_type: str = "none"
    token_count: int | None = None
    latency_ms: float | None = None


class RunSummaryResponse(BaseModel):
    """Compact run summary for list endpoints."""

    run_id: str
    query: str
    model: str
    provider: str
    succeeded: bool
    status: str
    step_count: int
    total_tokens: int
    duration_ms: float | None = None
    failures: list[str] = Field(default_factory=list)
    final_answer: str | None = None


class RunDetailResponse(RunSummaryResponse):
    """Full run detail including all steps."""

    steps: list[StepResponse] = Field(default_factory=list)


class RunListResponse(BaseModel):
    """Paginated list of runs."""

    runs: list[RunSummaryResponse]
    total: int
    limit: int
    offset: int


class ToolResponse(BaseModel):
    """Tool description for the frontend."""

    name: str
    description: str
    args_schema: str


class ToolListResponse(BaseModel):
    """List of available tools."""

    tools: list[ToolResponse]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    groq_key_set: bool
    tavily_key_set: bool
    ollama_available: bool = False
    providers: list[str] = Field(default_factory=list)

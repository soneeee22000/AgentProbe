"""Pydantic v2 schemas for benchmark endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateCaseRequest(BaseModel):
    """Request to create a custom benchmark case."""

    query: str = Field(..., min_length=1, description="The test query")
    category: str = Field(..., description="Case category")
    difficulty: str = Field(..., description="Difficulty level")
    expected_answer: str = Field(..., description="Expected answer")
    expected_tools: list[str] = Field(
        default_factory=list, description="Expected tool names"
    )


class StartSuiteRequest(BaseModel):
    """Request to start a benchmark suite run."""

    model: str = Field(
        default="llama-3.1-8b-instant", description="LLM model ID"
    )
    provider: str = Field(default="groq", description="LLM provider")
    category: str | None = Field(
        default=None, description="Filter cases by category"
    )
    difficulty: str | None = Field(
        default=None, description="Filter cases by difficulty"
    )


class BenchmarkCaseResponse(BaseModel):
    """Serialized benchmark case."""

    id: str
    query: str
    category: str
    difficulty: str
    expected_answer: str
    expected_tools: list[str] = Field(default_factory=list)
    is_builtin: bool = True


class BenchmarkResultResponse(BaseModel):
    """Serialized benchmark result."""

    suite_id: str
    case_id: str
    run_id: str
    passed: bool
    score: float = 0.0
    answer_correct: bool = False
    tools_correct: bool = False
    failures: list[str] = Field(default_factory=list)


class BenchmarkSuiteResponse(BaseModel):
    """Serialized benchmark suite."""

    id: str
    model_id: str
    provider: str
    status: str
    total_cases: int
    success_rate: float = 0.0
    avg_steps: float = 0.0
    failure_summary: dict[str, int] = Field(default_factory=dict)
    results: list[BenchmarkResultResponse] = Field(default_factory=list)


class BenchmarkSuiteListResponse(BaseModel):
    """List of benchmark suites."""

    suites: list[BenchmarkSuiteResponse]

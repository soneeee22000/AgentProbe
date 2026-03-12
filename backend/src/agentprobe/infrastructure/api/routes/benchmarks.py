"""Benchmark API routes — manage cases, run suites, view results."""

import json
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from agentprobe.application.schemas.benchmarks import (
    BenchmarkCaseResponse,
    BenchmarkResultResponse,
    BenchmarkSuiteListResponse,
    BenchmarkSuiteResponse,
    CreateCaseRequest,
    StartSuiteRequest,
)
from agentprobe.domain.entities.benchmark import (
    BenchmarkCase,
    BenchmarkCategory,
    BenchmarkDifficulty,
)
from agentprobe.infrastructure.api.dependencies import (
    get_benchmark_repository,
    get_eval_harness,
)

router = APIRouter(prefix="/api/v1/benchmarks", tags=["benchmarks"])


@router.get("/cases", response_model=list[BenchmarkCaseResponse])
async def list_cases(
    category: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
) -> list[BenchmarkCaseResponse]:
    """List benchmark cases with optional filters."""
    repo = get_benchmark_repository()
    cases = await repo.list_cases(category=category, difficulty=difficulty)
    return [
        BenchmarkCaseResponse(**case.to_dict())
        for case in cases
    ]


@router.get("/cases/{case_id}", response_model=BenchmarkCaseResponse)
async def get_case(case_id: str) -> BenchmarkCaseResponse:
    """Get a single benchmark case by ID."""
    repo = get_benchmark_repository()
    case = await repo.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=404, detail=f"Case '{case_id}' not found."
        )
    return BenchmarkCaseResponse(**case.to_dict())


@router.post("/cases", response_model=BenchmarkCaseResponse, status_code=201)
async def create_case(request: CreateCaseRequest) -> BenchmarkCaseResponse:
    """Create a custom benchmark case."""
    try:
        category = BenchmarkCategory(request.category)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {request.category}",
        )

    try:
        difficulty = BenchmarkDifficulty(request.difficulty)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid difficulty: {request.difficulty}",
        )

    case = BenchmarkCase(
        id=f"custom-{uuid.uuid4().hex[:6]}",
        query=request.query,
        category=category,
        difficulty=difficulty,
        expected_answer=request.expected_answer,
        expected_tools=request.expected_tools,
        is_builtin=False,
    )

    repo = get_benchmark_repository()
    await repo.save_case(case)
    return BenchmarkCaseResponse(**case.to_dict())


@router.post("/suites")
async def start_suite(request: StartSuiteRequest) -> StreamingResponse:
    """Start a benchmark suite run, streaming progress via SSE."""
    harness = get_eval_harness()

    async def event_stream() -> AsyncGenerator[str, None]:
        """Generate SSE events from eval harness."""
        async for event in harness.run_suite(
            model=request.model,
            provider=request.provider,
            category=request.category,
            difficulty=request.difficulty,
        ):
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/suites", response_model=BenchmarkSuiteListResponse)
async def list_suites() -> BenchmarkSuiteListResponse:
    """List all benchmark suites."""
    repo = get_benchmark_repository()
    suites = await repo.list_suites()
    return BenchmarkSuiteListResponse(
        suites=[
            BenchmarkSuiteResponse(
                **suite.to_dict(),
                results=[],
            )
            for suite in suites
        ]
    )


@router.get("/suites/{suite_id}", response_model=BenchmarkSuiteResponse)
async def get_suite(suite_id: str) -> BenchmarkSuiteResponse:
    """Get suite detail with all results."""
    repo = get_benchmark_repository()
    suite = await repo.get_suite(suite_id)
    if not suite:
        raise HTTPException(
            status_code=404, detail=f"Suite '{suite_id}' not found."
        )
    return BenchmarkSuiteResponse(
        **suite.to_dict(),
        results=[
            BenchmarkResultResponse(**r.to_dict())
            for r in suite.results
        ],
    )

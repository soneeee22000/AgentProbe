"""Run history endpoints — browse, inspect, delete, and replay past runs."""

import asyncio
import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from agentprobe.application.schemas.responses import (
    RunDetailResponse,
    RunListResponse,
    RunSummaryResponse,
    StepResponse,
)
from agentprobe.infrastructure.api.dependencies import get_run_repository

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


@router.get("", response_model=RunListResponse)
async def list_runs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    model: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> RunListResponse:
    """List agent runs with optional filters and pagination."""
    repo = get_run_repository()
    runs = await repo.list_runs(
        limit=limit,
        offset=offset,
        model=model,
        status=status,
    )
    total = await repo.count(model=model, status=status)

    return RunListResponse(
        runs=[
            RunSummaryResponse(
                run_id=r.run_id,
                query=r.query,
                model=r.model,
                provider=r.provider,
                succeeded=r.succeeded,
                status=r.status,
                step_count=len(r.steps),
                total_tokens=r.total_tokens,
                duration_ms=r.duration_ms,
                failures=[f.value for f in r.failures],
                final_answer=r.final_answer,
            )
            for r in runs
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{run_id}", response_model=RunDetailResponse)
async def get_run(run_id: str) -> RunDetailResponse:
    """Get a single run with all its steps."""
    repo = get_run_repository()
    run = await repo.get_by_id(run_id)

    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    return RunDetailResponse(
        run_id=run.run_id,
        query=run.query,
        model=run.model,
        provider=run.provider,
        succeeded=run.succeeded,
        status=run.status,
        step_count=len(run.steps),
        total_tokens=run.total_tokens,
        duration_ms=run.duration_ms,
        failures=[f.value for f in run.failures],
        final_answer=run.final_answer,
        steps=[
            StepResponse(
                step_type=s.step_type.value,
                content=s.content,
                step_index=s.step_index,
                timestamp=s.timestamp,
                tool_name=s.tool_name,
                tool_args=s.tool_args,
                failure_type=s.failure_type.value,
                token_count=s.token_count,
                latency_ms=s.latency_ms,
            )
            for s in run.steps
        ],
    )


@router.delete("/{run_id}")
async def delete_run(run_id: str) -> dict:
    """Delete a run and all its associated data."""
    repo = get_run_repository()
    deleted = await repo.delete(run_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    return {"deleted": True, "run_id": run_id}


@router.get("/{run_id}/replay")
async def replay_run(run_id: str) -> StreamingResponse:
    """Replay a run's steps as an SSE stream with simulated timing.

    Re-emits each saved step with a short delay to animate the trace.
    """
    repo = get_run_repository()
    run = await repo.get_by_id(run_id)

    if not run:
        raise HTTPException(
            status_code=404, detail=f"Run '{run_id}' not found."
        )

    async def replay_stream() -> AsyncGenerator[str, None]:
        """Yield steps as SSE events with timing delays."""
        for step in run.steps:
            step_dict = step.to_dict()
            yield f"data: {json.dumps(step_dict)}\n\n"
            await asyncio.sleep(0.3)
        yield 'data: {"step_type": "done"}\n\n'

    return StreamingResponse(
        replay_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

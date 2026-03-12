"""Agent run endpoints — start runs with SSE streaming."""

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from agentprobe.application.schemas.requests import RunRequest
from agentprobe.infrastructure.api.dependencies import get_orchestrator, get_settings

router = APIRouter(prefix="/api/v1", tags=["agent"])


async def _event_stream(
    query: str,
    model: str,
    provider: str,
    max_steps: int,
) -> ...:
    """Wrap the orchestrator's async generator into SSE format.

    Each agent step becomes: data: <json>\n\n
    """
    orchestrator = get_orchestrator(
        provider_name=provider,
        max_steps=max_steps,
    )
    async for step in orchestrator.execute(query, model=model, max_steps=max_steps):
        yield f"data: {json.dumps(step)}\n\n"

    yield 'data: {"step_type": "done"}\n\n'


@router.post("/run")
async def run_agent(request: RunRequest) -> StreamingResponse:
    """Start an agent run and stream each step as Server-Sent Events.

    The frontend opens this as an EventSource / fetch with streaming,
    and updates the UI in real-time as each step arrives.
    """
    settings = get_settings()

    if request.provider == "groq" and not settings.groq_api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY not set. Add it to your .env file.",
        )

    return StreamingResponse(
        _event_stream(
            query=request.query,
            model=request.model,
            provider=request.provider,
            max_steps=request.max_steps,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

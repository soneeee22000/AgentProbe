"""Tool listing endpoint."""

from fastapi import APIRouter

from agentprobe.application.schemas.responses import ToolListResponse, ToolResponse
from agentprobe.infrastructure.api.dependencies import get_tool_registry

router = APIRouter(prefix="/api/v1", tags=["tools"])


@router.get("/tools", response_model=ToolListResponse)
async def list_tools() -> ToolListResponse:
    """Return available tools for the frontend to display."""
    registry = get_tool_registry()
    return ToolListResponse(
        tools=[
            ToolResponse(
                name=t.name,
                description=t.description,
                args_schema=t.args_schema,
            )
            for t in registry.list_tools()
        ]
    )

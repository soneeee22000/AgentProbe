"""Custom tool CRUD endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from agentprobe.domain.entities.custom_tool import CustomTool

router = APIRouter(prefix="/api/v1/tools/custom", tags=["custom-tools"])


class CreateCustomToolRequest(BaseModel):
    """Request to create a custom tool."""

    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=500)
    args_schema: str = Field(default="", max_length=500)
    tool_type: str = Field(default="static", pattern="^(http|static)$")
    config: dict = Field(default_factory=dict)


class CustomToolResponse(BaseModel):
    """Custom tool response."""

    id: str
    name: str
    description: str
    args_schema: str
    tool_type: str
    config: dict


def _get_user_id(request: Request) -> str:
    """Extract user_id from request state.

    Raises:
        HTTPException: If no user_id is present on the request.
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id


def _get_repo():  # type: ignore[no-untyped-def]
    """Get the custom tool repository."""
    from agentprobe.infrastructure.api.dependencies import _ensure_db, _session_factory
    from agentprobe.infrastructure.persistence.repositories.custom_tool_repository import (
        SQLAlchemyCustomToolRepository,
    )
    _ensure_db()
    return SQLAlchemyCustomToolRepository(session_factory=_session_factory)


@router.post("", response_model=CustomToolResponse)
async def create_custom_tool(
    body: CreateCustomToolRequest, request: Request
) -> CustomToolResponse:
    """Create a new custom tool."""
    user_id = _get_user_id(request)
    repo = _get_repo()

    tool = CustomTool(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=body.name,
        description=body.description,
        args_schema=body.args_schema,
        tool_type=body.tool_type,
        config=body.config,
    )
    await repo.create(tool)

    return CustomToolResponse(
        id=tool.id,
        name=tool.name,
        description=tool.description,
        args_schema=tool.args_schema,
        tool_type=tool.tool_type,
        config=tool.config,
    )


@router.get("", response_model=list[CustomToolResponse])
async def list_custom_tools(request: Request) -> list[CustomToolResponse]:
    """List all custom tools for the current user."""
    user_id = _get_user_id(request)
    repo = _get_repo()
    tools = await repo.list_by_user(user_id)

    return [
        CustomToolResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            args_schema=t.args_schema,
            tool_type=t.tool_type,
            config=t.config,
        )
        for t in tools
    ]


@router.delete("/{tool_id}")
async def delete_custom_tool(tool_id: str, request: Request) -> dict:
    """Delete a custom tool."""
    user_id = _get_user_id(request)
    repo = _get_repo()
    tool = await repo.get(tool_id)

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    if tool.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await repo.delete(tool_id)
    return {"deleted": True}

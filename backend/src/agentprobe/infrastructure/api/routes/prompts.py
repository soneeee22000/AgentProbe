"""Prompt template CRUD endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from agentprobe.infrastructure.persistence.models.tables import PromptTemplateModel

router = APIRouter(prefix="/api/v1/prompts", tags=["prompts"])


class CreatePromptRequest(BaseModel):
    """Request to create a prompt template."""

    name: str = Field(..., min_length=1, max_length=100)
    system_prompt: str = Field(..., min_length=1, max_length=10000)
    is_default: bool = False


class UpdatePromptRequest(BaseModel):
    """Request to update a prompt template."""

    name: str | None = None
    system_prompt: str | None = None
    is_default: bool | None = None


class PromptResponse(BaseModel):
    """Prompt template response."""

    id: str
    name: str
    system_prompt: str
    is_default: bool


def _get_user_id(request: Request) -> str:
    """Extract user_id from request state.

    Raises:
        HTTPException: If no user_id is present on the request.
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id


def _get_session_factory():  # type: ignore[no-untyped-def]
    """Get the database session factory."""
    from agentprobe.infrastructure.api.dependencies import _ensure_db, _session_factory
    _ensure_db()
    return _session_factory


@router.post("", response_model=PromptResponse)
async def create_prompt(body: CreatePromptRequest, request: Request) -> PromptResponse:
    """Create a new prompt template."""

    user_id = _get_user_id(request)
    sf = _get_session_factory()
    prompt_id = str(uuid.uuid4())

    async with sf() as session:
        model = PromptTemplateModel(
            id=prompt_id,
            user_id=user_id,
            name=body.name,
            system_prompt=body.system_prompt,
            is_default=body.is_default,
        )
        session.add(model)
        await session.commit()

    return PromptResponse(
        id=prompt_id,
        name=body.name,
        system_prompt=body.system_prompt,
        is_default=body.is_default,
    )


@router.get("", response_model=list[PromptResponse])
async def list_prompts(request: Request) -> list[PromptResponse]:
    """List all prompt templates for the current user."""
    from sqlalchemy import select

    user_id = _get_user_id(request)
    sf = _get_session_factory()

    async with sf() as session:
        result = await session.execute(
            select(PromptTemplateModel).where(
                PromptTemplateModel.user_id == user_id
            )
        )
        models = result.scalars().all()

    return [
        PromptResponse(
            id=m.id,
            name=m.name,
            system_prompt=m.system_prompt,
            is_default=m.is_default,
        )
        for m in models
    ]


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: str, body: UpdatePromptRequest, request: Request
) -> PromptResponse:
    """Update a prompt template."""
    from sqlalchemy import select

    user_id = _get_user_id(request)
    sf = _get_session_factory()

    async with sf() as session:
        result = await session.execute(
            select(PromptTemplateModel).where(PromptTemplateModel.id == prompt_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise HTTPException(status_code=404, detail="Prompt not found")
        if model.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        if body.name is not None:
            model.name = body.name
        if body.system_prompt is not None:
            model.system_prompt = body.system_prompt
        if body.is_default is not None:
            model.is_default = body.is_default

        await session.commit()
        await session.refresh(model)

    return PromptResponse(
        id=model.id,
        name=model.name,
        system_prompt=model.system_prompt,
        is_default=model.is_default,
    )


@router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: str, request: Request) -> dict:
    """Delete a prompt template."""
    from sqlalchemy import select

    user_id = _get_user_id(request)
    sf = _get_session_factory()

    async with sf() as session:
        result = await session.execute(
            select(PromptTemplateModel).where(PromptTemplateModel.id == prompt_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise HTTPException(status_code=404, detail="Prompt not found")
        if model.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        await session.delete(model)
        await session.commit()

    return {"deleted": True}

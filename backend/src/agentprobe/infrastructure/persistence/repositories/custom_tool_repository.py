"""SQLAlchemy implementation of the custom tool repository."""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agentprobe.domain.entities.custom_tool import CustomTool
from agentprobe.domain.ports.custom_tool_repository import ICustomToolRepository
from agentprobe.infrastructure.persistence.models.tables import CustomToolModel


class SQLAlchemyCustomToolRepository(ICustomToolRepository):
    """Custom tool repository backed by SQLAlchemy.

    Args:
        session_factory: Async session factory for database access.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, tool: CustomTool) -> None:
        """Persist a new custom tool."""
        async with self._session_factory() as session:
            model = CustomToolModel(
                id=tool.id,
                user_id=tool.user_id,
                name=tool.name,
                description=tool.description,
                args_schema=tool.args_schema,
                tool_type=tool.tool_type,
                config=json.dumps(tool.config),
                created_at=tool.created_at,
            )
            session.add(model)
            await session.commit()

    async def list_by_user(self, user_id: str) -> list[CustomTool]:
        """List all custom tools for a user."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(CustomToolModel).where(CustomToolModel.user_id == user_id)
            )
            return [self._to_entity(m) for m in result.scalars().all()]

    async def get(self, tool_id: str) -> CustomTool | None:
        """Get a custom tool by ID."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(CustomToolModel).where(CustomToolModel.id == tool_id)
            )
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None

    async def delete(self, tool_id: str) -> None:
        """Delete a custom tool."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(CustomToolModel).where(CustomToolModel.id == tool_id)
            )
            model = result.scalar_one_or_none()
            if model:
                await session.delete(model)
                await session.commit()

    @staticmethod
    def _to_entity(model: CustomToolModel) -> CustomTool:
        """Convert ORM model to domain entity."""
        return CustomTool(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            description=model.description,
            args_schema=model.args_schema,
            tool_type=model.tool_type,
            config=json.loads(model.config),
            created_at=model.created_at,
        )

"""SQLAlchemy implementation of the memory repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agentprobe.domain.entities.memory import MemoryEntry
from agentprobe.domain.ports.memory_repository import IMemoryRepository
from agentprobe.infrastructure.persistence.models.tables import MemoryEntryModel


class SQLAlchemyMemoryRepository(IMemoryRepository):
    """Memory repository backed by SQLAlchemy.

    Args:
        session_factory: Async session factory for database access.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save(self, entry: MemoryEntry) -> None:
        """Persist a memory entry (upsert by user_id + key)."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(MemoryEntryModel).where(
                    MemoryEntryModel.user_id == entry.user_id,
                    MemoryEntryModel.key == entry.key,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.value = entry.value
                existing.source_run_id = entry.source_run_id
            else:
                model = MemoryEntryModel(
                    id=entry.id,
                    user_id=entry.user_id,
                    key=entry.key,
                    value=entry.value,
                    source_run_id=entry.source_run_id,
                    created_at=entry.created_at,
                )
                session.add(model)

            await session.commit()

    async def recall(self, user_id: str, key: str) -> MemoryEntry | None:
        """Recall a memory entry by key."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(MemoryEntryModel).where(
                    MemoryEntryModel.user_id == user_id,
                    MemoryEntryModel.key == key,
                )
            )
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None

    async def list_all(self, user_id: str) -> list[MemoryEntry]:
        """List all memory entries for a user."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(MemoryEntryModel).where(
                    MemoryEntryModel.user_id == user_id
                )
            )
            return [self._to_entity(m) for m in result.scalars().all()]

    async def delete(self, user_id: str, key: str) -> None:
        """Delete a memory entry."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(MemoryEntryModel).where(
                    MemoryEntryModel.user_id == user_id,
                    MemoryEntryModel.key == key,
                )
            )
            model = result.scalar_one_or_none()
            if model:
                await session.delete(model)
                await session.commit()

    @staticmethod
    def _to_entity(model: MemoryEntryModel) -> MemoryEntry:
        """Convert ORM model to domain entity."""
        return MemoryEntry(
            id=model.id,
            user_id=model.user_id,
            key=model.key,
            value=model.value,
            source_run_id=model.source_run_id,
            created_at=model.created_at,
        )

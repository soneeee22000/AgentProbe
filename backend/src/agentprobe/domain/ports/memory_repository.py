"""Port interface for agent memory persistence."""

from abc import ABC, abstractmethod

from agentprobe.domain.entities.memory import MemoryEntry


class IMemoryRepository(ABC):
    """Abstract interface for agent memory data access."""

    @abstractmethod
    async def save(self, entry: MemoryEntry) -> None:
        """Persist a memory entry (upsert by user_id + key)."""
        ...

    @abstractmethod
    async def recall(self, user_id: str, key: str) -> MemoryEntry | None:
        """Recall a memory entry by key for a user."""
        ...

    @abstractmethod
    async def list_all(self, user_id: str) -> list[MemoryEntry]:
        """List all memory entries for a user."""
        ...

    @abstractmethod
    async def delete(self, user_id: str, key: str) -> None:
        """Delete a memory entry."""
        ...

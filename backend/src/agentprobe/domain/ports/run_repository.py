"""Port interface for run persistence."""

from abc import ABC, abstractmethod

from ..entities.run import AgentRun


class IRunRepository(ABC):
    """Abstract interface for persisting and querying agent runs."""

    @abstractmethod
    async def save(self, run: AgentRun) -> None:
        """Persist a complete agent run with all its steps."""
        ...

    @abstractmethod
    async def get_by_id(self, run_id: str) -> AgentRun | None:
        """Retrieve a run by its ID, including all steps."""
        ...

    @abstractmethod
    async def list_runs(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        model: str | None = None,
        status: str | None = None,
    ) -> list[AgentRun]:
        """List runs with optional filters and pagination."""
        ...

    @abstractmethod
    async def delete(self, run_id: str) -> bool:
        """Delete a run and its steps. Returns True if found and deleted."""
        ...

    @abstractmethod
    async def count(
        self,
        *,
        model: str | None = None,
        status: str | None = None,
    ) -> int:
        """Count total runs matching filters."""
        ...

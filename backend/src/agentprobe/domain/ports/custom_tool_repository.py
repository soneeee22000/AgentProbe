"""Port interface for custom tool persistence."""

from abc import ABC, abstractmethod

from agentprobe.domain.entities.custom_tool import CustomTool


class ICustomToolRepository(ABC):
    """Abstract interface for custom tool data access."""

    @abstractmethod
    async def create(self, tool: CustomTool) -> None:
        """Persist a new custom tool."""
        ...

    @abstractmethod
    async def list_by_user(self, user_id: str) -> list[CustomTool]:
        """List all custom tools for a user."""
        ...

    @abstractmethod
    async def get(self, tool_id: str) -> CustomTool | None:
        """Get a custom tool by ID."""
        ...

    @abstractmethod
    async def delete(self, tool_id: str) -> None:
        """Delete a custom tool."""
        ...

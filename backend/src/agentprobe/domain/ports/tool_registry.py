"""Port interface for the tool registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class ToolDefinition:
    """Schema for a tool the agent can call."""

    name: str
    description: str
    args_schema: str
    fn: Callable[[str], str]


class IToolRegistry(ABC):
    """Abstract interface for managing agent tools.

    Tools are functions the agent can invoke via the ReAct loop.
    The registry provides prompt generation and dispatch.
    """

    @abstractmethod
    def register(self, tool: ToolDefinition) -> None:
        """Register a tool definition."""
        ...

    @abstractmethod
    def get(self, name: str) -> ToolDefinition | None:
        """Look up a tool by name."""
        ...

    @abstractmethod
    def exists(self, name: str) -> bool:
        """Check if a tool name is registered."""
        ...

    @abstractmethod
    def dispatch(self, name: str, args: str) -> str:
        """Execute a tool by name. Returns observation string."""
        ...

    @abstractmethod
    def get_tools_prompt(self) -> str:
        """Generate the tools section for the system prompt."""
        ...

    @abstractmethod
    def list_tools(self) -> list[ToolDefinition]:
        """Return all registered tools."""
        ...

"""Tool infrastructure — registry and built-in agent tools.

Exports the concrete ``ToolRegistry`` and a factory function
``create_default_registry`` that wires up all standard tools.
"""

from agentprobe.infrastructure.tools.calculator import register_calculator
from agentprobe.infrastructure.tools.read_file import register_read_file
from agentprobe.infrastructure.tools.registry import ToolRegistry
from agentprobe.infrastructure.tools.think import register_think
from agentprobe.infrastructure.tools.web_search import register_web_search

__all__ = [
    "ToolRegistry",
    "create_default_registry",
]


def create_default_registry(
    tavily_api_key: str | None = None,
    workspace_path: str | None = None,
) -> ToolRegistry:
    """Create a registry pre-loaded with all built-in tools.

    Args:
        tavily_api_key: Tavily API key for web search. When ``None``,
            the web search tool returns mock results.
        workspace_path: Absolute path to the workspace directory for
            the read-file tool. Defaults to the current working
            directory.

    Returns:
        A ``ToolRegistry`` with calculator, web_search, think, and
        read_file tools registered.
    """
    registry = ToolRegistry()

    register_calculator(registry)
    register_web_search(registry, api_key=tavily_api_key)
    register_think(registry)
    register_read_file(registry, workspace_path=workspace_path)

    return registry

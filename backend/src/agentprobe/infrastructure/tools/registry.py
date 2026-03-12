"""Concrete tool registry implementation.

Manages tool registration, lookup, dispatch, and prompt generation
for the ReAct agent loop.
"""

from __future__ import annotations

from agentprobe.domain.ports.tool_registry import IToolRegistry, ToolDefinition


class ToolRegistry(IToolRegistry):
    """In-memory registry that stores and dispatches agent tools.

    Tools are keyed by name and dispatched by matching the action
    string emitted by the LLM against registered tool names.
    """

    def __init__(self) -> None:
        """Initialise an empty tool registry."""
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool definition.

        Args:
            tool: The tool to register. Overwrites any existing tool
                with the same name.
        """
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        """Look up a tool by name.

        Args:
            name: The tool name to search for.

        Returns:
            The matching ``ToolDefinition``, or ``None`` if not found.
        """
        return self._tools.get(name)

    def exists(self, name: str) -> bool:
        """Check if a tool name is registered.

        Args:
            name: The tool name to check.

        Returns:
            ``True`` if the tool exists in the registry.
        """
        return name in self._tools

    def dispatch(self, name: str, args: str) -> str:
        """Execute a tool by name and return the observation string.

        Args:
            name: The tool name to dispatch.
            args: Raw argument string passed to the tool function.

        Returns:
            The tool's output string, or an error message if the tool
            does not exist or raises an exception.
        """
        tool = self._tools.get(name)
        if tool is None:
            available = ", ".join(sorted(self._tools.keys()))
            return (
                f"[ERROR] Tool '{name}' does not exist. "
                f"Available tools: {available}"
            )
        try:
            return tool.fn(args)
        except Exception as exc:
            return f"[ERROR] Tool '{name}' failed: {exc}"

    def get_tools_prompt(self) -> str:
        """Generate the tools section for the system prompt.

        Produces a formatted block describing each registered tool,
        suitable for injection into the agent's system message.

        Returns:
            A multi-line string listing all tools with their
            descriptions and argument schemas.
        """
        if not self._tools:
            return "No tools available."

        lines: list[str] = ["You have access to the following tools:", ""]
        for tool in self._tools.values():
            lines.append(f"### {tool.name}")
            lines.append(f"Description: {tool.description}")
            lines.append(f"Arguments: {tool.args_schema}")
            lines.append("")

        lines.append(
            "To use a tool, respond with:\n"
            "Action: <tool_name>\n"
            "Action Input: <arguments>"
        )
        return "\n".join(lines)

    def list_tools(self) -> list[ToolDefinition]:
        """Return all registered tools.

        Returns:
            A list of every ``ToolDefinition`` in registration order.
        """
        return list(self._tools.values())

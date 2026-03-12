"""Think tool for explicit chain-of-thought reasoning.

A no-op tool that simply echoes the agent's reasoning back as an
observation, giving the model a dedicated scratchpad step within
the ReAct loop without triggering any side effects.
"""

from agentprobe.domain.ports.tool_registry import ToolDefinition
from agentprobe.infrastructure.tools.registry import ToolRegistry


def _think(reasoning: str) -> str:
    """Echo the reasoning string back as an observation.

    Args:
        reasoning: The agent's internal reasoning or reflection.

    Returns:
        The same reasoning string, confirming it was recorded.
    """
    return reasoning


def register_think(registry: ToolRegistry) -> None:
    """Register the think tool with the given registry.

    Args:
        registry: The tool registry to register into.
    """
    registry.register(
        ToolDefinition(
            name="think",
            description=(
                "Use this tool to think step-by-step before acting. "
                "Write your reasoning as the input. The observation "
                "will echo it back — no side effects occur."
            ),
            args_schema='{"reasoning": "string (your internal reasoning)"}',
            fn=_think,
        )
    )

"""Calculator tool for safe mathematical expression evaluation.

Provides a sandboxed ``eval`` limited to whitelisted math functions
so the agent can perform arithmetic without arbitrary code execution.
"""

import math
from typing import Any

from agentprobe.domain.ports.tool_registry import ToolDefinition
from agentprobe.infrastructure.tools.registry import ToolRegistry

_ALLOWED_NAMES: dict[str, Any] = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "pow": pow,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
    "ceil": math.ceil,
    "floor": math.floor,
}


def _safe_eval(expression: str) -> str:
    """Evaluate a math expression in a restricted namespace.

    Args:
        expression: A mathematical expression string
            (e.g. ``"sqrt(144) + 3 * 2"``).

    Returns:
        The string representation of the computed result, or an
        error message if the expression is invalid.
    """
    try:
        result = eval(expression, {"__builtins__": {}}, _ALLOWED_NAMES)  # noqa: S307
        return str(result)
    except (SyntaxError, NameError, TypeError, ZeroDivisionError) as exc:
        return f"[ERROR] Invalid expression: {exc}"


def register_calculator(registry: ToolRegistry) -> None:
    """Register the calculator tool with the given registry.

    Args:
        registry: The tool registry to register into.
    """
    registry.register(
        ToolDefinition(
            name="calculator",
            description=(
                "Evaluate a mathematical expression. Supports basic "
                "arithmetic (+, -, *, /, **) and functions: sqrt, log, "
                "log10, log2, sin, cos, tan, abs, round, min, max, pow, "
                "ceil, floor. Constants: pi, e."
            ),
            args_schema='{"expression": "string (e.g. \'sqrt(144) + 3 * 2\')"}',
            fn=_safe_eval,
        )
    )

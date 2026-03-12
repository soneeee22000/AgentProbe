"""Custom tool domain entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class CustomTool:
    """User-defined tool for the agent.

    Attributes:
        id: Unique tool identifier.
        user_id: Owner user ID.
        name: Tool name (used in agent dispatch).
        description: Human-readable tool description.
        args_schema: Description of expected arguments.
        tool_type: Either 'http' (calls a URL) or 'static' (returns fixed response).
        config: Type-specific configuration (url, method, headers for http;
                response for static).
        created_at: Creation timestamp.
    """

    id: str
    user_id: str
    name: str
    description: str
    args_schema: str = ""
    tool_type: str = "static"
    config: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

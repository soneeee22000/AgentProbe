"""Prompt template domain entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class PromptTemplate:
    """A customizable system prompt template.

    Attributes:
        id: Unique template identifier.
        user_id: Owner user ID.
        name: Template display name.
        system_prompt: The system prompt text.
        is_default: Whether this is the user's default prompt.
        created_at: Creation timestamp.
    """

    id: str
    user_id: str
    name: str
    system_prompt: str
    is_default: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

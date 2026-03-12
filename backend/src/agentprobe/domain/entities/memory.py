"""Memory entry domain entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MemoryEntry:
    """A persistent memory entry for an agent.

    Allows agents to store and recall information across runs.

    Attributes:
        id: Unique memory entry identifier.
        user_id: Owner user ID.
        key: Memory key for retrieval.
        value: Memory value content.
        source_run_id: Run ID that created this memory (optional).
        created_at: Creation timestamp.
    """

    id: str
    user_id: str
    key: str
    value: str
    source_run_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

"""Agent memory tools — save and recall information across runs.

These tools allow the agent to persist key-value pairs that survive
across separate execution runs. Each user has an isolated memory space.
"""

import json
import uuid

from agentprobe.domain.entities.memory import MemoryEntry
from agentprobe.domain.ports.memory_repository import IMemoryRepository


def create_save_memory_tool(
    memory_repo: IMemoryRepository,
    user_id: str,
    run_id: str | None = None,
) -> tuple[str, str, str, object]:
    """Create a save_memory tool bound to a specific user.

    Returns:
        Tuple of (name, description, args_schema, handler_fn).
    """
    async def handler(args: str) -> str:
        """Save a key-value pair to persistent memory."""
        try:
            parsed = json.loads(args)
            key = parsed.get("key", "")
            value = parsed.get("value", "")
        except (json.JSONDecodeError, AttributeError):
            parts = args.split("=", 1)
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""

        if not key or not value:
            return (
                '[ERROR] save_memory requires key and value. '
                'Use: {"key": "...", "value": "..."}'
            )

        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            user_id=user_id,
            key=key,
            value=value,
            source_run_id=run_id,
        )
        await memory_repo.save(entry)
        return f"Memory saved: {key} = {value}"

    return (
        "save_memory",
        "Save a key-value pair to persistent memory that persists across runs.",
        '{"key": "string", "value": "string"}',
        handler,
    )


def create_recall_memory_tool(
    memory_repo: IMemoryRepository,
    user_id: str,
) -> tuple[str, str, str, object]:
    """Create a recall_memory tool bound to a specific user.

    Returns:
        Tuple of (name, description, args_schema, handler_fn).
    """
    async def handler(args: str) -> str:
        """Recall a value from persistent memory by key."""
        key = args.strip().strip('"').strip("'")
        if not key:
            return "[ERROR] recall_memory requires a key argument."

        entry = await memory_repo.recall(user_id, key)
        if entry:
            return f"Memory recalled: {entry.key} = {entry.value}"
        return f"No memory found for key: {key}"

    return (
        "recall_memory",
        "Recall a previously saved value from persistent memory by its key.",
        "key (string)",
        handler,
    )

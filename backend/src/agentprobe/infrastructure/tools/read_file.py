"""Read-file tool with workspace sandboxing.

Allows the agent to read files only within a designated workspace
directory, preventing path-traversal attacks via ``..`` sequences
or symlinks that escape the sandbox.
"""

from pathlib import Path

from agentprobe.domain.ports.tool_registry import ToolDefinition
from agentprobe.infrastructure.tools.registry import ToolRegistry

_MAX_READ_BYTES = 50_000


def _create_read_fn(workspace_path: str | None = None):
    """Build the file-read callable, closing over the workspace root.

    Args:
        workspace_path: Absolute path to the allowed workspace
            directory. When ``None``, defaults to the current
            working directory.

    Returns:
        A function that accepts a relative file path and returns
        the file contents or an error message.
    """
    workspace = Path(workspace_path).resolve() if workspace_path else Path.cwd()

    def _read_file(file_path: str) -> str:
        """Read a file from the sandboxed workspace directory.

        Args:
            file_path: Path relative to the workspace root.

        Returns:
            The file contents (truncated to 50 KB), or an error
            message if the path is invalid or outside the sandbox.
        """
        try:
            target = (workspace / file_path).resolve()
        except (OSError, ValueError) as exc:
            return f"[ERROR] Invalid path: {exc}"

        if not str(target).startswith(str(workspace)):
            return (
                "[ERROR] Path traversal denied. "
                "File must be within the workspace directory."
            )

        if not target.is_file():
            return f"[ERROR] File not found: {file_path}"

        try:
            content = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return f"[ERROR] Could not read file: {exc}"

        if len(content) > _MAX_READ_BYTES:
            content = content[:_MAX_READ_BYTES] + "\n... [truncated]"

        return content

    return _read_file


def register_read_file(
    registry: ToolRegistry,
    workspace_path: str | None = None,
) -> None:
    """Register the read-file tool with the given registry.

    Args:
        registry: The tool registry to register into.
        workspace_path: Absolute path to the allowed workspace
            directory. Defaults to the current working directory.
    """
    registry.register(
        ToolDefinition(
            name="read_file",
            description=(
                "Read the contents of a file within the workspace. "
                "Provide a path relative to the workspace root. "
                "Maximum read size is 50 KB."
            ),
            args_schema=(
                '{"file_path": "string (relative path, e.g. \'src/main.py\')"}'
            ),
            fn=_create_read_fn(workspace_path),
        )
    )

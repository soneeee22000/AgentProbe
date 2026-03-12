"""Port interfaces — abstractions the domain depends on."""

from .benchmark_repository import IBenchmarkRepository
from .llm_provider import ILLMProvider, LLMResponse
from .run_repository import IRunRepository
from .tool_registry import IToolRegistry, ToolDefinition

__all__ = [
    "ILLMProvider",
    "LLMResponse",
    "IToolRegistry",
    "ToolDefinition",
    "IRunRepository",
    "IBenchmarkRepository",
]

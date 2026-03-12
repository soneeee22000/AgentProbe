"""Unit tests for tool registry and individual tools."""

from agentprobe.domain.ports.tool_registry import ToolDefinition
from agentprobe.infrastructure.tools import create_default_registry
from agentprobe.infrastructure.tools.registry import ToolRegistry


class TestToolRegistry:
    """Tests for the ToolRegistry implementation."""

    def test_register_and_exists(self) -> None:
        """Registered tools should be findable."""
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="test_tool",
            description="A test",
            args_schema="str",
            fn=lambda x: x,
        )
        registry.register(tool)
        assert registry.exists("test_tool") is True
        assert registry.exists("nonexistent") is False

    def test_dispatch_returns_result(self) -> None:
        """Dispatch should call the tool function and return its result."""
        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="echo",
            description="Echo",
            args_schema="str",
            fn=lambda x: f"echo: {x}",
        ))
        assert registry.dispatch("echo", "hello") == "echo: hello"

    def test_dispatch_nonexistent_tool_returns_error(self) -> None:
        """Dispatching unknown tool should return error string."""
        registry = ToolRegistry()
        result = registry.dispatch("ghost", "args")
        assert "[ERROR]" in result
        assert "ghost" in result

    def test_dispatch_catches_exceptions(self) -> None:
        """Tool exceptions should be caught and returned as errors."""
        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="bad",
            description="Fails",
            args_schema="str",
            fn=lambda x: 1 / 0,
        ))
        result = registry.dispatch("bad", "")
        assert "[ERROR]" in result

    def test_get_tools_prompt_includes_all_tools(self) -> None:
        """Prompt should mention all registered tools."""
        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="a", description="Tool A", args_schema="str", fn=lambda x: x,
        ))
        registry.register(ToolDefinition(
            name="b", description="Tool B", args_schema="str", fn=lambda x: x,
        ))
        prompt = registry.get_tools_prompt()
        assert "a" in prompt
        assert "b" in prompt
        assert "Tool A" in prompt

    def test_list_tools_returns_all(self) -> None:
        """list_tools should return all registered tools."""
        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="x", description="X", args_schema="str", fn=lambda x: x,
        ))
        assert len(registry.list_tools()) == 1


class TestDefaultRegistry:
    """Tests for the default tool registry factory."""

    def test_creates_registry_with_four_tools(self) -> None:
        """Default registry should have calculator, web_search, think, read_file."""
        registry = create_default_registry()
        names = {t.name for t in registry.list_tools()}
        assert names == {"calculator", "web_search", "think", "read_file"}

    def test_calculator_works(self) -> None:
        """Calculator tool should evaluate math expressions."""
        registry = create_default_registry()
        result = registry.dispatch("calculator", "2 ** 10")
        assert "1024" in result

    def test_think_echoes_back(self) -> None:
        """Think tool should echo reasoning back."""
        registry = create_default_registry()
        result = registry.dispatch("think", "some reasoning")
        assert "some reasoning" in result.lower() or "reasoning" in result.lower()

    def test_web_search_mock_without_key(self) -> None:
        """Web search without API key should return mock results."""
        registry = create_default_registry(tavily_api_key=None)
        result = registry.dispatch("web_search", "test query")
        assert "MOCK" in result.upper() or "mock" in result.lower() or "Result" in result

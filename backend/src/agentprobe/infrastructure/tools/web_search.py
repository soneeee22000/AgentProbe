"""Web search tool backed by the Tavily Search API.

Falls back to a mock response when no API key is configured,
allowing development and testing without external dependencies.
"""

import json

import httpx

from agentprobe.domain.ports.tool_registry import ToolDefinition
from agentprobe.infrastructure.tools.registry import ToolRegistry

_TAVILY_SEARCH_URL = "https://api.tavily.com/search"
_REQUEST_TIMEOUT_SECONDS = 15


def _mock_search(query: str) -> str:
    """Return a placeholder result when no API key is available.

    Args:
        query: The search query string.

    Returns:
        A JSON-formatted mock result indicating no API key.
    """
    return json.dumps(
        {
            "query": query,
            "results": [
                {
                    "title": "Mock result (no TAVILY_API_KEY configured)",
                    "url": "https://example.com",
                    "content": (
                        f"This is a mock search result for: {query}. "
                        "Set the TAVILY_API_KEY environment variable "
                        "to enable real web search."
                    ),
                }
            ],
        },
        indent=2,
    )


def _create_search_fn(api_key: str | None = None):
    """Build the search callable, closing over the API key.

    Args:
        api_key: Tavily API key. When ``None`` or empty, the
            returned function produces mock results.

    Returns:
        A function that accepts a query string and returns a
        JSON-formatted search result.
    """

    def _search(query: str) -> str:
        """Execute a web search via Tavily or return mock data.

        Args:
            query: The search query string.

        Returns:
            JSON string containing search results.
        """
        if not api_key:
            return _mock_search(query)

        try:
            response = httpx.post(
                _TAVILY_SEARCH_URL,
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 5,
                },
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            return f"[ERROR] Web search failed: {exc}"

        results = []
        for item in data.get("results", []):
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                }
            )

        return json.dumps(
            {"query": query, "results": results},
            indent=2,
        )

    return _search


def register_web_search(
    registry: ToolRegistry,
    api_key: str | None = None,
) -> None:
    """Register the web search tool with the given registry.

    Args:
        registry: The tool registry to register into.
        api_key: Tavily API key. Falls back to mock results when
            ``None`` or empty.
    """
    registry.register(
        ToolDefinition(
            name="web_search",
            description=(
                "Search the web for current information using the "
                "Tavily API. Returns up to 5 results with titles, "
                "URLs, and content snippets."
            ),
            args_schema='{"query": "string (e.g. \'latest AI research 2026\')"}',
            fn=_create_search_fn(api_key),
        )
    )

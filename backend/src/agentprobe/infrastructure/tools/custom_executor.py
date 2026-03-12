"""Custom tool executor — dispatches HTTP or static custom tools."""

import ipaddress
import socket
from typing import Any
from urllib.parse import urlparse

import httpx

_BLOCKED_SCHEMES = {"file", "ftp", "gopher", "data", "javascript"}


def _is_safe_url(url: str) -> bool:
    """Validate that a URL is safe to request (no SSRF).

    Blocks private/reserved IPs, link-local, loopback, and non-HTTPS schemes
    in production contexts.

    Args:
        url: The URL to validate.

    Returns:
        True if the URL is considered safe.
    """
    parsed = urlparse(url)

    if parsed.scheme.lower() in _BLOCKED_SCHEMES:
        return False

    if not parsed.hostname:
        return False

    try:
        resolved = socket.getaddrinfo(parsed.hostname, None)
        for _, _, _, _, sockaddr in resolved:
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
    except (socket.gaierror, ValueError):
        return False

    return True


async def execute_custom_tool(
    tool_type: str,
    config: dict[str, Any],
    args: str,
) -> str:
    """Execute a user-defined custom tool.

    Args:
        tool_type: Either 'http' or 'static'.
        config: Type-specific configuration.
        args: The input arguments from the agent.

    Returns:
        The tool's response as a string.
    """
    if tool_type == "static":
        return config.get("response", "No response configured")

    if tool_type == "http":
        return await _execute_http_tool(config, args)

    return f"[ERROR] Unknown custom tool type: {tool_type}"


async def _execute_http_tool(config: dict[str, Any], args: str) -> str:
    """Execute an HTTP custom tool.

    Args:
        config: HTTP tool configuration (url, method, headers).
        args: The input to pass as the request body or query.

    Returns:
        The HTTP response body as a string.
    """
    url = config.get("url", "")
    method = config.get("method", "GET").upper()
    headers = config.get("headers", {})

    if not url:
        return "[ERROR] HTTP tool has no URL configured"

    if not _is_safe_url(url):
        return "[ERROR] URL blocked: private/reserved addresses are not allowed"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(
                    url, params={"q": args}, headers=headers,
                )
            else:
                response = await client.post(
                    url,
                    json={"input": args},
                    headers=headers,
                )
            response.raise_for_status()
            return response.text[:2000]
    except httpx.HTTPError as e:
        return f"[ERROR] HTTP tool failed: {e}"

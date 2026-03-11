"""
tools.py — All tools the agent can call.

KEY LEARNING: Tools are just Python functions + a schema the LLM reads.
The schema tells the LLM: "here's what I can do and what args I need."
We manually dispatch based on the LLM's parsed output — no magic.
"""

import os
import math
import json
import httpx
from typing import Any


# ── Tool Registry ────────────────────────────────────────────────────────────
# Each tool has: name, description (what the LLM reads), and a callable.
# The LLM never calls the function directly — it outputs text, we parse + dispatch.

TOOLS: dict[str, dict] = {}

def register_tool(name: str, description: str, args_schema: str):
    """Decorator to register a function as an agent tool."""
    def decorator(fn):
        TOOLS[name] = {
            "name": name,
            "description": description,
            "args_schema": args_schema,
            "fn": fn,
        }
        return fn
    return decorator


def get_tools_prompt() -> str:
    """
    Generates the tools section of the system prompt.
    This is what teaches the LLM what tools exist.
    """
    lines = ["You have access to the following tools:\n"]
    for tool in TOOLS.values():
        lines.append(f"Tool: {tool['name']}")
        lines.append(f"Description: {tool['description']}")
        lines.append(f"Args: {tool['args_schema']}")
        lines.append("")
    return "\n".join(lines)


def dispatch_tool(name: str, args: str) -> str:
    """
    Execute a tool by name with string args.
    Returns a string result (the 'Observation' in ReAct).
    
    FAILURE MODE #1: Tool not found — agent hallucinated a tool name.
    FAILURE MODE #2: Args malformed — agent passed wrong format.
    Both are logged and returned as error observations (agent can recover).
    """
    if name not in TOOLS:
        return f"[ERROR] Tool '{name}' does not exist. Available tools: {list(TOOLS.keys())}"
    
    try:
        result = TOOLS[name]["fn"](args)
        return str(result)
    except Exception as e:
        return f"[ERROR] Tool '{name}' failed with args '{args}': {type(e).__name__}: {e}"


# ── Tool Definitions ──────────────────────────────────────────────────────────

@register_tool(
    name="calculator",
    description="Evaluate a mathematical expression. Use for any arithmetic, algebra, or numeric reasoning.",
    args_schema='A single math expression as a string. Example: "2 ** 10 + sqrt(144)"'
)
def calculator(expression: str) -> Any:
    """
    Safe math evaluator. We only expose math module — no exec() exploits.
    
    LEARNING: Never use eval() on raw user/LLM input in production.
    Build a whitelist or use a proper math parser (e.g. sympy).
    """
    # Whitelist: only math functions + basic operators
    allowed_names = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    allowed_names.update({"abs": abs, "round": round, "min": min, "max": max})
    
    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"{expression} = {result}"
    except SyntaxError:
        raise ValueError(f"Invalid expression syntax: {expression}")
    except NameError as e:
        raise ValueError(f"Unknown function in expression: {e}")


@register_tool(
    name="web_search",
    description="Search the web for current information. Returns top results with title, URL, and snippet.",
    args_schema='A search query string. Example: "latest Llama 3 benchmarks 2024"'
)
def web_search(query: str) -> str:
    """
    Search via Tavily API — designed for LLM agents (returns clean text, not HTML).
    Falls back to a mock if no API key is set, so you can develop offline.
    
    LEARNING: Real agents need grounding in external data.
    Tavily > SerpAPI for agents because it pre-processes results for LLM consumption.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    
    if not api_key:
        # Mock response for development without API key
        return (
            f"[MOCK SEARCH for: '{query}']\n"
            "Result 1: Example result A — snippet about the topic.\n"
            "Result 2: Example result B — more context here.\n"
            "(Set TAVILY_API_KEY in .env to enable real search)"
        )
    
    try:
        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": 3,
                "search_depth": "basic",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        
        results = []
        for i, r in enumerate(data.get("results", []), 1):
            results.append(
                f"Result {i}: {r.get('title', 'No title')}\n"
                f"URL: {r.get('url', '')}\n"
                f"Snippet: {r.get('content', '')[:300]}"
            )
        
        return "\n\n".join(results) if results else "No results found."
    
    except httpx.HTTPError as e:
        return f"[SEARCH ERROR] HTTP error: {e}"


@register_tool(
    name="think",
    description=(
        "Use this tool to reason through a complex sub-problem before acting. "
        "Useful for breaking down multi-step problems, checking logic, or planning next steps. "
        "Does NOT call any external service."
    ),
    args_schema='Your reasoning as a string. This is a private scratchpad — think freely.'
)
def think(reasoning: str) -> str:
    """
    A 'no-op' tool that just echoes reasoning back.
    
    LEARNING: This is surprisingly powerful. Giving the agent an explicit
    'think' action improves multi-step accuracy because it externalizes
    chain-of-thought into the context window as an observation.
    This is the core insight behind scratchpad/chain-of-thought prompting.
    """
    return f"Reasoning logged: {reasoning}"


@register_tool(
    name="read_file",
    description="Read the contents of a text file from the workspace.",
    args_schema='Filename (relative path within workspace). Example: "data/notes.txt"'
)
def read_file(filename: str) -> str:
    """Read a file from the sandboxed workspace directory."""
    workspace = os.getenv("AGENT_WORKSPACE", "./workspace")
    safe_path = os.path.normpath(os.path.join(workspace, filename))
    
    # Security: prevent path traversal attacks
    if not safe_path.startswith(os.path.abspath(workspace)):
        return "[ERROR] Access denied: path traversal attempt detected."
    
    try:
        with open(safe_path, "r") as f:
            content = f.read()
        return f"File '{filename}':\n{content}"
    except FileNotFoundError:
        return f"[ERROR] File '{filename}' not found in workspace."
    except Exception as e:
        return f"[ERROR] Could not read file: {e}"

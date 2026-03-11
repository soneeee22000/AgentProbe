"""
main.py — FastAPI backend for AgentProbe.

Endpoints:
  POST /api/run    — Run the agent, stream steps via SSE
  GET  /api/health — Health check
  GET  /api/tools  — List available tools
"""

import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.core import run_agent
from agent.tools import TOOLS

app = FastAPI(title="AgentProbe", version="0.1.0")

# Allow frontend dev server to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/Response Models ───────────────────────────────────────────────────

class RunRequest(BaseModel):
    query: str
    model: str = "llama-3.1-8b-instant"
    max_steps: int = 10


# ── SSE Streaming ─────────────────────────────────────────────────────────────
# Server-Sent Events: a simple protocol for server → client streaming.
# The client opens a connection, server pushes "data: {...}\n\n" messages.
# Much simpler than WebSockets for unidirectional streaming.

async def event_stream(query: str, model: str, max_steps: int):
    """
    Async generator that wraps the agent loop into SSE format.
    Each agent step becomes: data: <json>\n\n
    """
    async for step in run_agent(query=query, model=model, max_steps=max_steps):
        yield f"data: {json.dumps(step)}\n\n"
    
    # Send a terminal event so the client knows the stream is done
    yield "data: {\"step_type\": \"done\"}\n\n"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/api/run")
async def run(request: RunRequest):
    """
    Start an agent run and stream each step as Server-Sent Events.
    
    The frontend opens this as an EventSource / fetch with streaming,
    and updates the UI in real-time as each step arrives.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY not set. Add it to your .env file."
        )
    
    return StreamingResponse(
        event_stream(
            query=request.query,
            model=request.model,
            max_steps=request.max_steps,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Important for nginx proxies
        }
    )


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "groq_key_set": bool(os.getenv("GROQ_API_KEY")),
        "tavily_key_set": bool(os.getenv("TAVILY_API_KEY")),
    }


@app.get("/api/tools")
async def list_tools():
    """Return available tools (useful for the frontend to display)."""
    return {
        "tools": [
            {
                "name": t["name"],
                "description": t["description"],
                "args_schema": t["args_schema"],
            }
            for t in TOOLS.values()
        ]
    }

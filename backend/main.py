"""Entry point for AgentProbe backend.

Usage:
    uvicorn main:app --reload --port 8000
"""

from dotenv import load_dotenv

load_dotenv()

from agentprobe.infrastructure.api.app import create_app  # noqa: E402

app = create_app()

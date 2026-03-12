"""Domain entity for individual agent steps within a run."""

import time
from dataclasses import asdict, dataclass, field
from enum import Enum


class StepType(str, Enum):
    """Classification of each step in the ReAct loop."""

    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    FINAL = "final_answer"
    ERROR = "error"
    SYSTEM = "system"


class FailureType(str, Enum):
    """Failure taxonomy — the core of AgentProbe's observability.

    Each run is annotated with which failure modes occurred,
    enabling aggregate analytics across models and queries.
    """

    NONE = "none"
    HALLUCINATED_TOOL = "hallucinated_tool"
    MALFORMED_ACTION = "malformed_action"
    TOOL_EXECUTION_ERROR = "tool_execution_error"
    MAX_STEPS_EXCEEDED = "max_steps_exceeded"
    CONTEXT_OVERFLOW = "context_overflow"
    GOAL_DRIFT = "goal_drift"
    REPEATED_ACTION = "repeated_action"
    EMPTY_RESPONSE = "empty_response"


@dataclass
class AgentStep:
    """A single step in an agent's execution trace.

    Captures type, content, tool metadata, failure classification,
    and performance metrics (tokens, latency).
    """

    step_type: StepType
    content: str
    step_index: int
    timestamp: float = field(default_factory=time.time)
    tool_name: str | None = None
    tool_args: str | None = None
    failure_type: FailureType = FailureType.NONE
    token_count: int | None = None
    latency_ms: float | None = None

    def to_dict(self) -> dict:
        """Serialize to dict for JSON/SSE transmission."""
        d = asdict(self)
        d["step_type"] = self.step_type.value
        d["failure_type"] = self.failure_type.value
        return d

    def is_failure(self) -> bool:
        """Check if this step represents a failure condition."""
        return self.failure_type != FailureType.NONE

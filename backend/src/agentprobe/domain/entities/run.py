"""Domain entity for a complete agent run."""

import time
from dataclasses import dataclass, field

from .step import AgentStep, FailureType


@dataclass
class AgentRun:
    """Complete record of a single agent execution.

    Tracks query, model, all steps, performance metrics,
    and failure conditions for post-run analysis.
    """

    query: str
    run_id: str
    model: str
    provider: str = "groq"
    steps: list[AgentStep] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    final_answer: str | None = None
    failures: list[FailureType] = field(default_factory=list)
    total_tokens: int = 0

    def add_step(self, step: AgentStep) -> None:
        """Append a step, updating failure and token accumulators."""
        self.steps.append(step)
        if step.is_failure():
            self.failures.append(step.failure_type)
        if step.token_count:
            self.total_tokens += step.token_count

    def finish(self, final_answer: str | None = None) -> None:
        """Mark the run as completed."""
        self.end_time = time.time()
        self.final_answer = final_answer

    @property
    def duration_ms(self) -> float | None:
        """Total run duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None

    @property
    def succeeded(self) -> bool:
        """Whether the run produced a final answer without exceeding max steps."""
        return (
            self.final_answer is not None
            and FailureType.MAX_STEPS_EXCEEDED not in self.failures
        )

    @property
    def status(self) -> str:
        """Current run status string."""
        if self.end_time is None:
            return "running"
        return "success" if self.succeeded else "failed"

    def summary(self) -> dict:
        """Compact summary for SSE/API responses."""
        return {
            "run_id": self.run_id,
            "query": self.query,
            "model": self.model,
            "provider": self.provider,
            "succeeded": self.succeeded,
            "status": self.status,
            "step_count": len(self.steps),
            "total_tokens": self.total_tokens,
            "duration_ms": self.duration_ms,
            "failures": [f.value for f in self.failures],
            "final_answer": self.final_answer,
        }

    def to_dict(self) -> dict:
        """Full serialization including all steps."""
        return {
            **self.summary(),
            "steps": [s.to_dict() for s in self.steps],
        }

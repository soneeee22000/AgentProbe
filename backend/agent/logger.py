"""
logger.py — Structured logging for every agent step.

KEY LEARNING: This is what transforms a black-box agent into something
you can audit, debug, and build a failure taxonomy from.
Every step is captured with type, content, token count, and timestamp.
"""

import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class StepType(str, Enum):
    THOUGHT     = "thought"       # LLM's internal reasoning
    ACTION      = "action"        # Tool call decided by LLM  
    OBSERVATION = "observation"   # Tool result fed back to LLM
    FINAL       = "final_answer"  # Terminal state
    ERROR       = "error"         # Something went wrong
    SYSTEM      = "system"        # Metadata (start, end, token usage)


class FailureType(str, Enum):
    """
    Your failure taxonomy — this is the core of the portfolio piece.
    Each run will be annotated with which failure modes occurred.
    """
    NONE                  = "none"
    HALLUCINATED_TOOL     = "hallucinated_tool"       # Called a tool that doesn't exist
    MALFORMED_ACTION      = "malformed_action"        # Couldn't parse Action/Action Input
    TOOL_EXECUTION_ERROR  = "tool_execution_error"    # Tool threw an exception
    MAX_STEPS_EXCEEDED    = "max_steps_exceeded"      # Never reached Final Answer
    CONTEXT_OVERFLOW      = "context_overflow"        # Messages getting too long
    GOAL_DRIFT            = "goal_drift"              # Final answer doesn't address query
    REPEATED_ACTION       = "repeated_action"         # Agent looping on same tool call
    EMPTY_RESPONSE        = "empty_response"          # LLM returned nothing useful


@dataclass
class AgentStep:
    step_type:     StepType
    content:       str
    step_index:    int
    timestamp:     float = field(default_factory=time.time)
    tool_name:     Optional[str] = None
    tool_args:     Optional[str] = None
    failure_type:  FailureType = FailureType.NONE
    token_count:   Optional[int] = None
    latency_ms:    Optional[float] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["step_type"]    = self.step_type.value
        d["failure_type"] = self.failure_type.value
        return d

    def is_failure(self) -> bool:
        return self.failure_type != FailureType.NONE


@dataclass  
class AgentRun:
    """Complete record of a single agent execution."""
    query:          str
    run_id:         str
    model:          str
    steps:          list[AgentStep] = field(default_factory=list)
    start_time:     float = field(default_factory=time.time)
    end_time:       Optional[float] = None
    final_answer:   Optional[str] = None
    failures:       list[FailureType] = field(default_factory=list)
    total_tokens:   int = 0

    def add_step(self, step: AgentStep):
        self.steps.append(step)
        if step.is_failure():
            self.failures.append(step.failure_type)
        if step.token_count:
            self.total_tokens += step.token_count

    def finish(self, final_answer: Optional[str] = None):
        self.end_time = time.time()
        self.final_answer = final_answer

    @property
    def duration_ms(self) -> Optional[float]:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None

    @property
    def succeeded(self) -> bool:
        return self.final_answer is not None and FailureType.MAX_STEPS_EXCEEDED not in self.failures

    def summary(self) -> dict:
        return {
            "run_id":        self.run_id,
            "query":         self.query,
            "model":         self.model,
            "succeeded":     self.succeeded,
            "step_count":    len(self.steps),
            "total_tokens":  self.total_tokens,
            "duration_ms":   self.duration_ms,
            "failures":      [f.value for f in self.failures],
            "final_answer":  self.final_answer,
        }

    def to_dict(self) -> dict:
        return {
            **self.summary(),
            "steps": [s.to_dict() for s in self.steps],
        }

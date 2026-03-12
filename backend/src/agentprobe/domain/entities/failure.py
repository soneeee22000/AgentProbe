"""Domain entity for failure records linked to runs and steps."""

from dataclasses import dataclass

from .step import FailureType


@dataclass
class Failure:
    """A recorded failure event within an agent run.

    Links a failure type to the specific run and step where it occurred,
    with optional context for debugging.
    """

    run_id: str
    failure_type: FailureType
    step_id: int | None = None
    context: str | None = None

    def to_dict(self) -> dict:
        """Serialize for API responses."""
        return {
            "run_id": self.run_id,
            "step_id": self.step_id,
            "failure_type": self.failure_type.value,
            "context": self.context,
        }

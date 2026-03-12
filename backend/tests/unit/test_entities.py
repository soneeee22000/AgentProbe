"""Unit tests for domain entities."""

from agentprobe.domain.entities.run import AgentRun
from agentprobe.domain.entities.step import AgentStep, FailureType, StepType


class TestAgentStep:
    """Tests for AgentStep entity."""

    def test_to_dict_serializes_enums(self) -> None:
        """Enums should serialize to their string values."""
        step = AgentStep(
            step_type=StepType.THOUGHT,
            content="thinking...",
            step_index=1,
        )
        d = step.to_dict()
        assert d["step_type"] == "thought"
        assert d["failure_type"] == "none"

    def test_is_failure_returns_false_for_none(self) -> None:
        """Non-failure steps should return False."""
        step = AgentStep(
            step_type=StepType.THOUGHT,
            content="ok",
            step_index=0,
        )
        assert step.is_failure() is False

    def test_is_failure_returns_true_for_error(self) -> None:
        """Steps with failure type should return True."""
        step = AgentStep(
            step_type=StepType.ERROR,
            content="bad",
            step_index=0,
            failure_type=FailureType.HALLUCINATED_TOOL,
        )
        assert step.is_failure() is True


class TestAgentRun:
    """Tests for AgentRun entity."""

    def test_add_step_accumulates_tokens(self) -> None:
        """Token counts should accumulate across steps."""
        run = AgentRun(query="test", run_id="abc", model="llama")
        run.add_step(AgentStep(
            step_type=StepType.THOUGHT,
            content="t",
            step_index=0,
            token_count=50,
        ))
        run.add_step(AgentStep(
            step_type=StepType.THOUGHT,
            content="t",
            step_index=1,
            token_count=30,
        ))
        assert run.total_tokens == 80

    def test_add_step_tracks_failures(self) -> None:
        """Failures should be recorded in the run's failure list."""
        run = AgentRun(query="test", run_id="abc", model="llama")
        run.add_step(AgentStep(
            step_type=StepType.ERROR,
            content="err",
            step_index=0,
            failure_type=FailureType.MALFORMED_ACTION,
        ))
        assert FailureType.MALFORMED_ACTION in run.failures

    def test_succeeded_true_when_final_answer(self) -> None:
        """Run with final answer and no max_steps failure should succeed."""
        run = AgentRun(query="test", run_id="abc", model="llama")
        run.finish(final_answer="done")
        assert run.succeeded is True

    def test_succeeded_false_when_no_answer(self) -> None:
        """Run without final answer should not succeed."""
        run = AgentRun(query="test", run_id="abc", model="llama")
        run.finish()
        assert run.succeeded is False

    def test_succeeded_false_when_max_steps(self) -> None:
        """Run that exceeded max steps should not succeed."""
        run = AgentRun(query="test", run_id="abc", model="llama")
        run.add_step(AgentStep(
            step_type=StepType.ERROR,
            content="timeout",
            step_index=0,
            failure_type=FailureType.MAX_STEPS_EXCEEDED,
        ))
        run.finish(final_answer="partial")
        assert run.succeeded is False

    def test_duration_ms_calculated(self) -> None:
        """Duration should be calculated from start and end times."""
        run = AgentRun(query="test", run_id="abc", model="llama")
        run.start_time = 100.0
        run.end_time = 100.5
        assert run.duration_ms == 500.0

    def test_status_running_before_finish(self) -> None:
        """Status should be 'running' before finish() is called."""
        run = AgentRun(query="test", run_id="abc", model="llama")
        assert run.status == "running"

    def test_summary_returns_expected_keys(self) -> None:
        """Summary dict should contain all expected keys."""
        run = AgentRun(query="test", run_id="abc", model="llama")
        run.finish(final_answer="done")
        s = run.summary()
        expected_keys = {
            "run_id", "query", "model", "provider", "succeeded",
            "status", "step_count", "total_tokens", "duration_ms",
            "failures", "final_answer",
        }
        assert set(s.keys()) == expected_keys

"""EvalHarness — runs benchmark suites against the agent, streaming progress."""

import uuid
from collections.abc import AsyncGenerator, Callable

from agentprobe.application.services.orchestrator import AgentOrchestrator
from agentprobe.application.services.scoring import ScoringEngine
from agentprobe.domain.entities.benchmark import BenchmarkCase, BenchmarkSuite
from agentprobe.domain.entities.run import AgentRun
from agentprobe.domain.entities.step import AgentStep, FailureType, StepType
from agentprobe.domain.ports.benchmark_repository import IBenchmarkRepository


class EvalHarness:
    """Runs benchmark suites and streams progress via SSE.

    Args:
        benchmark_repo: Repository for loading cases and saving results.
        orchestrator_factory: Callable that creates an AgentOrchestrator.
        scoring_engine: Engine for scoring completed runs.
    """

    def __init__(
        self,
        benchmark_repo: IBenchmarkRepository,
        orchestrator_factory: Callable[..., AgentOrchestrator],
        scoring_engine: ScoringEngine | None = None,
    ) -> None:
        self._repo = benchmark_repo
        self._orchestrator_factory = orchestrator_factory
        self._scorer = scoring_engine or ScoringEngine()

    async def run_suite(
        self,
        *,
        model: str,
        provider: str,
        category: str | None = None,
        difficulty: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Run a benchmark suite, yielding progress events.

        Args:
            model: LLM model ID to use for all cases.
            provider: LLM provider name.
            category: Optional category filter for cases.
            difficulty: Optional difficulty filter for cases.

        Yields:
            dict events: suite_start, case_start, case_complete, suite_complete.
        """
        cases = await self._repo.list_cases(
            category=category, difficulty=difficulty
        )

        if not cases:
            yield {"type": "error", "message": "No benchmark cases found."}
            return

        suite = BenchmarkSuite(
            id=str(uuid.uuid4())[:8],
            model_id=model,
            provider=provider,
            status="running",
            total_cases=len(cases),
        )
        await self._repo.save_suite(suite)

        yield {
            "type": "suite_start",
            "suite_id": suite.id,
            "total_cases": len(cases),
            "model": model,
            "provider": provider,
        }

        passed_count = 0
        total_steps = 0
        failure_counts: dict[str, int] = {}

        orchestrator = self._orchestrator_factory(provider_name=provider)

        for idx, case in enumerate(cases):
            yield {
                "type": "case_start",
                "case_index": idx,
                "case_id": case.id,
                "query": case.query,
                "category": case.category.value,
            }

            run = await self._execute_case(orchestrator, case, model)
            result = self._scorer.score_run(case, run)
            result.suite_id = suite.id

            await self._repo.save_result(result)

            if result.passed:
                passed_count += 1
            total_steps += len(run.steps)

            for f in result.failures:
                failure_counts[f] = failure_counts.get(f, 0) + 1

            yield {
                "type": "case_complete",
                "case_index": idx,
                "case_id": case.id,
                "passed": result.passed,
                "score": result.score,
                "answer_correct": result.answer_correct,
                "tools_correct": result.tools_correct,
                "run_id": result.run_id,
                "step_count": len(run.steps),
            }

        completed_count = len(cases)
        suite.status = "completed"
        suite.success_rate = (
            round(passed_count / completed_count, 3)
            if completed_count > 0
            else 0.0
        )
        suite.avg_steps = (
            round(total_steps / completed_count, 1)
            if completed_count > 0
            else 0.0
        )
        suite.failure_summary = failure_counts
        await self._repo.save_suite(suite)

        yield {
            "type": "suite_complete",
            "suite_id": suite.id,
            "total_cases": completed_count,
            "passed": passed_count,
            "failed": completed_count - passed_count,
            "success_rate": suite.success_rate,
            "avg_steps": suite.avg_steps,
            "failure_summary": failure_counts,
        }

    @staticmethod
    async def _execute_case(
        orchestrator: AgentOrchestrator,
        case: BenchmarkCase,
        model: str,
    ) -> AgentRun:
        """Execute a single benchmark case and reconstruct the AgentRun.

        Collects all yielded step dicts from the orchestrator, then
        reconstructs a domain AgentRun for scoring.

        Args:
            orchestrator: The agent orchestrator to use.
            case: The benchmark case to run.
            model: The model ID to use.

        Returns:
            The reconstructed AgentRun with all steps.
        """
        step_dicts: list[dict] = []
        async for step_dict in orchestrator.execute(case.query, model=model):
            step_dicts.append(step_dict)

        run_id = str(uuid.uuid4())[:8]
        final_answer: str | None = None

        for sd in step_dicts:
            if sd.get("step_type") == "system" and sd.get("step_index", 0) == 0:
                content = sd.get("content", "")
                if "Run: " in content:
                    run_id = content.split("Run: ")[1].split(" |")[0]
            if sd.get("step_type") == "final_answer":
                final_answer = sd.get("content")

        steps = [
            AgentStep(
                step_type=StepType(sd["step_type"]),
                content=sd.get("content", ""),
                step_index=sd.get("step_index", 0),
                timestamp=sd.get("timestamp", 0.0),
                tool_name=sd.get("tool_name"),
                tool_args=sd.get("tool_args"),
                failure_type=FailureType(sd.get("failure_type", "none")),
                token_count=sd.get("token_count"),
                latency_ms=sd.get("latency_ms"),
            )
            for sd in step_dicts
            if sd.get("step_type") != "done"
        ]

        run = AgentRun(
            query=case.query,
            run_id=run_id,
            model=model,
            provider="",
        )
        for step in steps:
            run.add_step(step)
        if final_answer:
            run.finish(final_answer=final_answer)
        else:
            run.finish()

        return run

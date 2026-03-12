"""AgentOrchestrator — the core ReAct loop with injected dependencies.

This is the heart of AgentProbe. It runs the ReAct loop
(Thought -> Action -> Observation -> ...) using injected LLM provider,
tool registry, and run repository.

The ReAct pattern (Yao et al., 2022):
  Thought -> Action -> Observation -> Thought -> Action -> ... -> Final Answer

The LLM outputs text. We parse it. We call tools. We feed results back.
"""

import json
import time
import uuid
from collections.abc import AsyncGenerator

from agentprobe.domain.entities.run import AgentRun
from agentprobe.domain.entities.step import AgentStep, FailureType, StepType
from agentprobe.domain.ports.llm_provider import ILLMProvider
from agentprobe.domain.ports.run_repository import IRunRepository
from agentprobe.domain.ports.tool_registry import IToolRegistry

from .parser import detect_repeated_action, parse_llm_output

SYSTEM_PROMPT_TEMPLATE = (
    "You are AgentProbe, a methodical research assistant "
    "that reasons step-by-step before acting.\n\n"
    "{tools_section}\n\n"
    "You MUST follow this exact format for EVERY response. No exceptions:\n\n"
    "Thought: [Your reasoning about what to do next. Be explicit.]\n"
    "Action: [Exactly one tool name from the list above]\n"
    "Action Input: [The input to pass to the tool]\n\n"
    "After receiving an Observation, continue with another "
    "Thought/Action/Action Input cycle.\n"
    "When you have enough information to answer the original question, use:\n\n"
    "Thought: [Your final reasoning]\n"
    "Final Answer: [Your complete, well-structured answer]\n\n"
    "RULES:\n"
    "- Never skip the Thought step\n"
    "- Only use tool names that exist in the tools list\n"
    "- Action Input must be a plain string (no JSON unless the tool requires it)\n"
    "- If a tool errors, reason about why and try a different approach\n"
    "- Never repeat the same Action + Action Input twice in a row\n"
    "- Always end with Final Answer when you have enough information\n"
)


class AgentOrchestrator:
    """Orchestrates the ReAct agent loop with clean dependency injection.

    Args:
        llm_provider: LLM provider for chat completions.
        tool_registry: Registry of available tools.
        run_repository: Optional repository for persisting runs.
        max_steps: Safety limit to prevent infinite loops.
        context_char_limit: Max context chars before overflow detection.
    """

    def __init__(
        self,
        llm_provider: ILLMProvider,
        tool_registry: IToolRegistry,
        run_repository: IRunRepository | None = None,
        max_steps: int = 10,
        context_char_limit: int = 24000,
    ) -> None:
        self._llm = llm_provider
        self._tools = tool_registry
        self._repo = run_repository
        self._max_steps = max_steps
        self._context_char_limit = context_char_limit

    async def execute(
        self,
        query: str,
        *,
        model: str = "llama-3.1-8b-instant",
        max_steps: int | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Run the ReAct loop, yielding each step as it happens for SSE streaming.

        Args:
            query: The user's question.
            model: LLM model ID to use.
            max_steps: Override default max_steps for this run.

        Yields:
            dict — serialized AgentStep for each reasoning step.
        """
        effective_max_steps = max_steps or self._max_steps

        run = AgentRun(
            query=query,
            run_id=str(uuid.uuid4())[:8],
            model=model,
            provider=self._llm.provider_name(),
        )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT_TEMPLATE.format(
                    tools_section=self._tools.get_tools_prompt()
                ),
            },
            {"role": "user", "content": query},
        ]

        # Emit start event
        start_step = AgentStep(
            step_type=StepType.SYSTEM,
            content=(
                f"Starting AgentProbe | Run: {run.run_id} | "
                f"Model: {model} | Provider: {run.provider} | "
                f"Query: {query}"
            ),
            step_index=0,
        )
        run.add_step(start_step)
        yield start_step.to_dict()

        # ReAct Loop
        for step_num in range(1, effective_max_steps + 1):
            # Context overflow check
            total_chars = sum(len(m["content"]) for m in messages)
            if total_chars > self._context_char_limit:
                error_step = AgentStep(
                    step_type=StepType.ERROR,
                    content="Context window approaching limit. Stopping to prevent overflow.",
                    step_index=step_num,
                    failure_type=FailureType.CONTEXT_OVERFLOW,
                )
                run.add_step(error_step)
                yield error_step.to_dict()
                break

            # LLM call
            t0 = time.time()
            try:
                response = await self._llm.complete(
                    messages,
                    model=model,
                    max_tokens=1024,
                    temperature=0.1,
                    stop=["Observation:"],
                )
            except Exception as e:
                error_step = AgentStep(
                    step_type=StepType.ERROR,
                    content=f"LLM API call failed: {e}",
                    step_index=step_num,
                    failure_type=FailureType.EMPTY_RESPONSE,
                )
                run.add_step(error_step)
                yield error_step.to_dict()
                break

            latency = (time.time() - t0) * 1000
            raw_output = response.content
            token_count = response.completion_tokens

            if not raw_output.strip():
                error_step = AgentStep(
                    step_type=StepType.ERROR,
                    content="LLM returned empty response.",
                    step_index=step_num,
                    failure_type=FailureType.EMPTY_RESPONSE,
                    latency_ms=latency,
                )
                run.add_step(error_step)
                yield error_step.to_dict()
                break

            # Parse output
            parsed = parse_llm_output(raw_output)

            # Final Answer
            if parsed.final_answer:
                thought_content = parsed.thought or "(no explicit thought)"
                thought_step = AgentStep(
                    step_type=StepType.THOUGHT,
                    content=thought_content,
                    step_index=step_num,
                    token_count=token_count,
                    latency_ms=latency,
                )
                run.add_step(thought_step)
                yield thought_step.to_dict()

                final_step = AgentStep(
                    step_type=StepType.FINAL,
                    content=parsed.final_answer,
                    step_index=step_num,
                )
                run.add_step(final_step)
                run.finish(final_answer=parsed.final_answer)
                yield final_step.to_dict()

                # Persist run
                await self._persist_run(run)

                # Emit summary
                summary_step = AgentStep(
                    step_type=StepType.SYSTEM,
                    content=json.dumps(run.summary()),
                    step_index=step_num + 1,
                )
                yield summary_step.to_dict()
                return

            # Thought step
            if parsed.thought:
                thought_step = AgentStep(
                    step_type=StepType.THOUGHT,
                    content=parsed.thought,
                    step_index=step_num,
                    token_count=token_count,
                    latency_ms=latency,
                )
                run.add_step(thought_step)
                yield thought_step.to_dict()

            # Action parsing failure
            if not parsed.action:
                error_step = AgentStep(
                    step_type=StepType.ERROR,
                    content=f"Could not parse Action from LLM output. Raw: {raw_output[:200]}",
                    step_index=step_num,
                    failure_type=FailureType.MALFORMED_ACTION,
                )
                run.add_step(error_step)
                yield error_step.to_dict()
                messages.append({"role": "assistant", "content": raw_output})
                messages.append({
                    "role": "user",
                    "content": (
                        "Observation: [FORMAT ERROR] Your response didn't follow "
                        "the required format. Please respond with "
                        "Thought: / Action: / Action Input:"
                    ),
                })
                continue

            action = parsed.action
            action_input = parsed.action_input or ""

            # Failure detection
            failure = FailureType.NONE
            if not self._tools.exists(action):
                failure = FailureType.HALLUCINATED_TOOL
            if detect_repeated_action(run.steps, action, action_input):
                failure = FailureType.REPEATED_ACTION

            action_step = AgentStep(
                step_type=StepType.ACTION,
                content=f"{action}({action_input})",
                step_index=step_num,
                tool_name=action,
                tool_args=action_input,
                failure_type=failure,
            )
            run.add_step(action_step)
            yield action_step.to_dict()

            # Tool dispatch
            if failure == FailureType.REPEATED_ACTION:
                observation = (
                    "[LOOP DETECTED] You've called this exact tool with "
                    "this exact input recently. Try a different approach."
                )
            else:
                observation = self._tools.dispatch(action, action_input)

            obs_failure = FailureType.NONE
            if "[ERROR]" in observation:
                obs_failure = FailureType.TOOL_EXECUTION_ERROR

            obs_step = AgentStep(
                step_type=StepType.OBSERVATION,
                content=observation,
                step_index=step_num,
                failure_type=obs_failure,
            )
            run.add_step(obs_step)
            yield obs_step.to_dict()

            # Feed observation back into context
            messages.append({"role": "assistant", "content": raw_output})
            messages.append({
                "role": "user",
                "content": f"Observation: {observation}",
            })
        else:
            # Max steps exceeded
            timeout_step = AgentStep(
                step_type=StepType.ERROR,
                content=f"Agent did not reach Final Answer within {effective_max_steps} steps.",
                step_index=effective_max_steps + 1,
                failure_type=FailureType.MAX_STEPS_EXCEEDED,
            )
            run.add_step(timeout_step)
            run.finish()
            yield timeout_step.to_dict()

            await self._persist_run(run)

            summary_step = AgentStep(
                step_type=StepType.SYSTEM,
                content=json.dumps(run.summary()),
                step_index=effective_max_steps + 2,
            )
            yield summary_step.to_dict()

    async def _persist_run(self, run: AgentRun) -> None:
        """Save run to repository if one is configured."""
        if self._repo:
            try:
                await self._repo.save(run)
            except Exception:
                pass  # Don't fail the run if persistence fails

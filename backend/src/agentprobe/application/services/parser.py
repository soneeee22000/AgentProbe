"""ReAct output parser — extracts structured fields from LLM text output.

Parsing the LLM's text output is where many real-world failures occur.
An agent that can't parse its own output is a broken agent.
"""

import re
from dataclasses import dataclass


@dataclass
class ParsedOutput:
    """Structured fields extracted from a ReAct-formatted LLM response."""

    thought: str | None = None
    action: str | None = None
    action_input: str | None = None
    final_answer: str | None = None
    raw: str = ""


def parse_llm_output(text: str) -> ParsedOutput:
    """Parse a ReAct-formatted LLM response into structured fields.

    Returns ParsedOutput with extracted thought, action, action_input,
    and final_answer. Some fields may be None if not present.

    Args:
        text: Raw LLM response text in ReAct format.

    Returns:
        ParsedOutput with extracted fields.
    """
    result = ParsedOutput(raw=text)

    # Extract Thought
    thought_match = re.search(
        r"Thought:\s*(.+?)(?=\nAction:|\nFinal Answer:|$)",
        text,
        re.DOTALL,
    )
    if thought_match:
        result.thought = thought_match.group(1).strip()

    # Extract Final Answer (terminal condition)
    final_match = re.search(
        r"Final Answer:\s*(.+?)$",
        text,
        re.DOTALL,
    )
    if final_match:
        result.final_answer = final_match.group(1).strip()
        return result

    # Extract Action
    action_match = re.search(r"Action:\s*(.+?)(?=\n|$)", text)
    if action_match:
        result.action = action_match.group(1).strip()

    # Extract Action Input
    input_match = re.search(
        r"Action Input:\s*(.+?)(?=\nThought:|\nAction:|\nFinal Answer:|$)",
        text,
        re.DOTALL,
    )
    if input_match:
        result.action_input = input_match.group(1).strip()

    return result


def detect_repeated_action(
    steps: list,
    action: str,
    action_input: str,
    lookback: int = 4,
) -> bool:
    """Check if the agent is looping on the same action.

    Catches the 'infinite loop' failure mode before it consumes
    all remaining steps.

    Args:
        steps: List of AgentStep objects from the current run.
        action: The action name to check.
        action_input: The action input to check.
        lookback: Number of recent steps to examine.

    Returns:
        True if a matching action+input pair is found in recent steps.
    """
    from agentprobe.domain.entities.step import StepType

    recent_actions = [
        s for s in steps[-lookback:]
        if s.step_type == StepType.ACTION
    ]
    return any(
        step.tool_name == action and step.tool_args == action_input
        for step in recent_actions
    )

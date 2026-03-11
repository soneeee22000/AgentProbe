"""
core.py — The raw ReAct agent loop. No LangChain. No abstractions.

KEY LEARNING: This is what every agent framework wraps.
Understanding this loop IS understanding how agents work.

ReAct pattern (Yao et al., 2022):
  Thought → Action → Observation → Thought → Action → ...→ Final Answer

The LLM outputs text. We parse it. We call tools. We feed results back.
That's literally it.
"""

import os
import re
import time
import uuid
import json
from typing import AsyncGenerator
from groq import AsyncGroq

from .tools import TOOLS, get_tools_prompt, dispatch_tool
from .logger import AgentRun, AgentStep, StepType, FailureType


# ── System Prompt ─────────────────────────────────────────────────────────────
# This is the most critical part of any agent.
# It defines the ReAct format the LLM MUST follow so we can parse its output.

SYSTEM_PROMPT_TEMPLATE = """You are AgentProbe, a methodical research assistant that reasons step-by-step before acting.

{tools_section}

You MUST follow this exact format for EVERY response. No exceptions:

Thought: [Your reasoning about what to do next. Be explicit.]
Action: [Exactly one tool name from the list above]
Action Input: [The input to pass to the tool]

After receiving an Observation, continue with another Thought/Action/Action Input cycle.
When you have enough information to answer the original question, use:

Thought: [Your final reasoning]
Final Answer: [Your complete, well-structured answer]

RULES:
- Never skip the Thought step
- Only use tool names that exist in the tools list
- Action Input must be a plain string (no JSON unless the tool requires it)
- If a tool errors, reason about why and try a different approach
- Never repeat the same Action + Action Input twice in a row
- Always end with Final Answer when you have enough information
"""


# ── Parser ────────────────────────────────────────────────────────────────────
# Parsing the LLM's text output is where a lot of real-world failures happen.
# An agent that can't parse its own output is a broken agent.

def parse_llm_output(text: str) -> dict:
    """
    Parse a ReAct-formatted LLM response into structured fields.
    
    Returns dict with keys: thought, action, action_input, final_answer
    Some keys may be None if not present in this response.
    
    FAILURE MODE: LLM doesn't follow the format → we return partial parse
    and the caller decides how to handle it (log + retry, or abort).
    """
    result = {
        "thought": None,
        "action": None, 
        "action_input": None,
        "final_answer": None,
        "raw": text,
    }
    
    # Extract Thought
    thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction:|\nFinal Answer:|$)", text, re.DOTALL)
    if thought_match:
        result["thought"] = thought_match.group(1).strip()
    
    # Extract Final Answer (terminal condition)
    final_match = re.search(r"Final Answer:\s*(.+?)$", text, re.DOTALL)
    if final_match:
        result["final_answer"] = final_match.group(1).strip()
        return result  # Done — no need to parse action
    
    # Extract Action
    action_match = re.search(r"Action:\s*(.+?)(?=\n|$)", text)
    if action_match:
        result["action"] = action_match.group(1).strip()
    
    # Extract Action Input
    input_match = re.search(r"Action Input:\s*(.+?)(?=\nThought:|\nAction:|\nFinal Answer:|$)", text, re.DOTALL)
    if input_match:
        result["action_input"] = input_match.group(1).strip()
    
    return result


def detect_repeated_action(steps: list[AgentStep], action: str, action_input: str) -> bool:
    """
    FAILURE DETECTION: Check if agent is looping on the same action.
    This catches the 'infinite loop' failure mode before it happens.
    """
    recent_actions = [
        s for s in steps[-4:]  # Check last 4 steps
        if s.step_type == StepType.ACTION
    ]
    for step in recent_actions:
        if step.tool_name == action and step.tool_args == action_input:
            return True
    return False


# ── Main Agent Loop ───────────────────────────────────────────────────────────

async def run_agent(
    query: str,
    model: str = "llama-3.1-8b-instant",
    max_steps: int = 10,
) -> AsyncGenerator[dict, None]:
    """
    The core ReAct loop. Yields each step as it happens (for SSE streaming).
    
    ARCHITECTURE DECISION: We use async generators so the FastAPI endpoint
    can stream steps to the frontend in real-time. This is important for UX —
    users can see the agent thinking, not just wait for a final answer.
    
    Args:
        query:     The user's question
        model:     Groq model ID
        max_steps: Safety limit — prevents infinite loops
    
    Yields:
        dict — serialized AgentStep for each reasoning step
    """
    run = AgentRun(
        query=query,
        run_id=str(uuid.uuid4())[:8],
        model=model,
    )
    
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    
    # Build the conversation history
    # LEARNING: The LLM has no memory — we manually maintain message history
    # and pass the full context every turn. This is the core of stateful agents.
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT_TEMPLATE.format(
                tools_section=get_tools_prompt()
            )
        },
        {
            "role": "user", 
            "content": query
        }
    ]
    
    # Emit a system start event
    start_step = AgentStep(
        step_type=StepType.SYSTEM,
        content=f"Starting AgentProbe | Run: {run.run_id} | Model: {model} | Query: {query}",
        step_index=0,
    )
    run.add_step(start_step)
    yield start_step.to_dict()
    
    # ── ReAct Loop ────────────────────────────────────────────────────────────
    for step_num in range(1, max_steps + 1):
        
        # Check context length — a real failure mode for long runs
        total_chars = sum(len(m["content"]) for m in messages)
        if total_chars > 24000:  # ~6k tokens, safe for 8k context models
            error_step = AgentStep(
                step_type=StepType.ERROR,
                content="Context window approaching limit. Stopping to prevent overflow.",
                step_index=step_num,
                failure_type=FailureType.CONTEXT_OVERFLOW,
            )
            run.add_step(error_step)
            yield error_step.to_dict()
            break
        
        # ── LLM Call ─────────────────────────────────────────────────────────
        t0 = time.time()
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1024,
                temperature=0.1,  # Low temp = more deterministic format following
                stop=["Observation:"],  # CRITICAL: stop before hallucinating observations
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
        raw_output = response.choices[0].message.content or ""
        token_count = response.usage.completion_tokens if response.usage else None
        
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
        
        # ── Parse Output ──────────────────────────────────────────────────────
        parsed = parse_llm_output(raw_output)
        
        # ── Final Answer ──────────────────────────────────────────────────────
        if parsed["final_answer"]:
            thought_content = parsed["thought"] or "(no explicit thought)"
            
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
                content=parsed["final_answer"],
                step_index=step_num,
            )
            run.add_step(final_step)
            run.finish(final_answer=parsed["final_answer"])
            yield final_step.to_dict()
            
            # Emit run summary as final system event
            summary_step = AgentStep(
                step_type=StepType.SYSTEM,
                content=json.dumps(run.summary()),
                step_index=step_num + 1,
            )
            yield summary_step.to_dict()
            return
        
        # ── Thought Step ──────────────────────────────────────────────────────
        if parsed["thought"]:
            thought_step = AgentStep(
                step_type=StepType.THOUGHT,
                content=parsed["thought"],
                step_index=step_num,
                token_count=token_count,
                latency_ms=latency,
            )
            run.add_step(thought_step)
            yield thought_step.to_dict()
        
        # ── Action Parsing Failure ─────────────────────────────────────────────
        if not parsed["action"]:
            error_step = AgentStep(
                step_type=StepType.ERROR,
                content=f"Could not parse Action from LLM output. Raw: {raw_output[:200]}",
                step_index=step_num,
                failure_type=FailureType.MALFORMED_ACTION,
            )
            run.add_step(error_step)
            yield error_step.to_dict()
            # Feed the error back so the agent can self-correct
            messages.append({"role": "assistant", "content": raw_output})
            messages.append({
                "role": "user",
                "content": "Observation: [FORMAT ERROR] Your response didn't follow the required format. Please respond with Thought: / Action: / Action Input:"
            })
            continue
        
        action = parsed["action"]
        action_input = parsed["action_input"] or ""
        
        # ── Hallucinated Tool Detection ────────────────────────────────────────
        failure = FailureType.NONE
        if action not in TOOLS:
            failure = FailureType.HALLUCINATED_TOOL
        
        # ── Repeated Action Detection ─────────────────────────────────────────
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
        
        if failure == FailureType.REPEATED_ACTION:
            observation = "[LOOP DETECTED] You've called this exact tool with this exact input recently. Try a different approach."
        else:
            # ── Tool Dispatch ─────────────────────────────────────────────────
            observation = dispatch_tool(action, action_input)
        
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
        
        # ── Feed observation back into context ────────────────────────────────
        # LEARNING: This is the key to the ReAct loop.
        # The assistant "said" it wanted to call a tool,
        # we call it, and we inject the result as if it appeared in the conversation.
        messages.append({"role": "assistant", "content": raw_output})
        messages.append({
            "role": "user",
            "content": f"Observation: {observation}"
        })
    
    # ── Max Steps Exceeded ────────────────────────────────────────────────────
    else:
        timeout_step = AgentStep(
            step_type=StepType.ERROR,
            content=f"Agent did not reach Final Answer within {max_steps} steps.",
            step_index=max_steps + 1,
            failure_type=FailureType.MAX_STEPS_EXCEEDED,
        )
        run.add_step(timeout_step)
        run.finish()
        yield timeout_step.to_dict()
        
        summary_step = AgentStep(
            step_type=StepType.SYSTEM,
            content=json.dumps(run.summary()),
            step_index=max_steps + 2,
        )
        yield summary_step.to_dict()

"use client";

import type { AgentStep } from "@/lib/api";

/** Human-readable labels for each step type. */
const TAG_LABELS: Record<string, string> = {
  thought: "Thought",
  action: "Action",
  observation: "Observation",
  final_answer: "Final Answer",
  error: "Error",
  system: "System",
};

/** Badge background colours keyed by step type. */
const TAG_COLORS: Record<string, string> = {
  thought: "#4fc3f7",
  action: "#81c784",
  observation: "#ffb74d",
  final_answer: "#ce93d8",
  error: "#ef5350",
  system: "#546e7a",
};

interface StepCardProps {
  /** The agent step to render. */
  step: AgentStep;
}

/**
 * Renders a single agent step as a styled card.
 * Uses CSS classes defined in globals.css for step-type backgrounds and
 * the animate-step-in entrance animation.
 */
export function StepCard({ step }: StepCardProps) {
  const label = TAG_LABELS[step.step_type] ?? step.step_type;
  const badgeColor = TAG_COLORS[step.step_type] ?? TAG_COLORS.system;
  const hasFailure = step.failure_type && step.failure_type !== "none";

  return (
    <div
      className={`step-${step.step_type} animate-step-in rounded-md px-4 py-3`}
    >
      {/* Header row */}
      <div className="mb-2 flex flex-wrap items-center gap-2">
        {/* Type badge */}
        <span
          className="rounded-sm px-2 py-0.5 text-xs font-medium text-black"
          style={{ backgroundColor: badgeColor }}
        >
          {label}
        </span>

        {/* Failure badge */}
        {hasFailure && (
          <span className="rounded-sm bg-[#ef5350]/20 px-2 py-0.5 text-xs font-medium text-[#ef5350]">
            {step.failure_type}
          </span>
        )}

        {/* Meta info */}
        <span className="ml-auto flex items-center gap-3 text-xs text-muted-foreground">
          {step.latency_ms != null && (
            <span>{step.latency_ms.toFixed(0)}ms</span>
          )}
          {step.token_count != null && <span>{step.token_count} tok</span>}
        </span>
      </div>

      {/* Content */}
      <div className="text-sm leading-relaxed text-foreground/90">
        {step.step_type === "action" ? (
          <div>
            {step.tool_name && (
              <span className="mr-2 font-semibold text-[#81c784]">
                {step.tool_name}
              </span>
            )}
            {step.tool_args && (
              <span className="text-muted-foreground">{step.tool_args}</span>
            )}
            {step.content && !step.tool_name && <p>{step.content}</p>}
          </div>
        ) : (
          <p className="whitespace-pre-wrap">{step.content}</p>
        )}
      </div>
    </div>
  );
}

"use client";

import type { AgentStep } from "@/lib/api";

interface CompareStatsBarProps {
  /** Steps from the left model run. */
  leftSteps: AgentStep[];
  /** Steps from the right model run. */
  rightSteps: AgentStep[];
  /** Execution status of the left run. */
  leftStatus: string;
  /** Execution status of the right run. */
  rightStatus: string;
  /** Display name for the left model. */
  leftLabel: string;
  /** Display name for the right model. */
  rightLabel: string;
}

/**
 * Computes the total token count from a list of agent steps.
 */
function sumTokens(steps: AgentStep[]): number {
  return steps.reduce((sum, step) => sum + (step.token_count ?? 0), 0);
}

/**
 * Computes the total duration in milliseconds from a list of agent steps.
 */
function sumDuration(steps: AgentStep[]): number {
  return steps.reduce((sum, step) => sum + (step.latency_ms ?? 0), 0);
}

/** Color class applied to the metric value that "wins" (lower is better). */
const WIN_COLOR = "text-[#81c784]";

interface MetricProps {
  /** Metric display label. */
  label: string;
  /** Left model value. */
  leftValue: number;
  /** Right model value. */
  rightValue: number;
  /** Unit suffix appended to the numeric value. */
  unit: string;
}

/**
 * Renders a single comparison metric with left and right values.
 * Highlights the lower (winning) value in green.
 */
function Metric({ label, leftValue, rightValue, unit }: MetricProps) {
  const leftWins = leftValue < rightValue;
  const rightWins = rightValue < leftValue;

  return (
    <div className="flex flex-col items-center gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <div className="flex items-center gap-4">
        <span
          className={`text-sm font-medium ${leftWins ? WIN_COLOR : "text-foreground"}`}
        >
          {leftValue}
          {unit}
        </span>
        <span className="text-xs text-muted-foreground">vs</span>
        <span
          className={`text-sm font-medium ${rightWins ? WIN_COLOR : "text-foreground"}`}
        >
          {rightValue}
          {unit}
        </span>
      </div>
    </div>
  );
}

/**
 * Bottom bar showing side-by-side performance metrics for both model runs.
 * Only rendered after both runs have completed.
 * Highlights the "winning" model for each metric in green.
 */
export function CompareStatsBar({
  leftSteps,
  rightSteps,
  leftStatus,
  rightStatus,
  leftLabel,
  rightLabel,
}: CompareStatsBarProps) {
  const bothDone =
    (leftStatus === "complete" || leftStatus === "failed") &&
    (rightStatus === "complete" || rightStatus === "failed");

  if (!bothDone) return null;

  const leftTokens = sumTokens(leftSteps);
  const rightTokens = sumTokens(rightSteps);
  const leftDuration = sumDuration(leftSteps);
  const rightDuration = sumDuration(rightSteps);

  return (
    <div className="border-t border-border bg-card px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Left model label */}
        <span className="text-xs font-medium text-foreground">{leftLabel}</span>

        {/* Metrics */}
        <div className="flex items-center gap-8">
          <Metric
            label="Steps"
            leftValue={leftSteps.length}
            rightValue={rightSteps.length}
            unit=""
          />
          <Metric
            label="Tokens"
            leftValue={leftTokens}
            rightValue={rightTokens}
            unit=""
          />
          <Metric
            label="Duration"
            leftValue={leftDuration}
            rightValue={rightDuration}
            unit="ms"
          />
        </div>

        {/* Right model label */}
        <span className="text-xs font-medium text-foreground">
          {rightLabel}
        </span>
      </div>
    </div>
  );
}

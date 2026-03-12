"use client";

import { StepCard } from "@/components/playground/step-card";
import type { AgentStep } from "@/lib/api";

/** Status color mapping for the run status indicator dot. */
const STATUS_COLORS: Record<string, string> = {
  idle: "#6b7a8d",
  running: "#4fc3f7",
  complete: "#81c784",
  failed: "#ef5350",
};

/** Human-readable labels for each run status. */
const STATUS_LABELS: Record<string, string> = {
  idle: "Idle",
  running: "Running...",
  complete: "Complete",
  failed: "Failed",
};

interface CompareTraceLaneProps {
  /** The list of agent steps to display. */
  steps: AgentStep[];
  /** Current execution status of this lane's run. */
  status: string;
  /** Display label for this lane (e.g. model name). */
  label: string;
}

/**
 * A single trace lane showing streaming agent steps for one model.
 * Displays a status indicator, scrollable step list, and a footer
 * with step count and total token count.
 */
export function CompareTraceLane({
  steps,
  status,
  label,
}: CompareTraceLaneProps) {
  const dotColor = STATUS_COLORS[status] ?? STATUS_COLORS.idle;
  const statusLabel = STATUS_LABELS[status] ?? status;
  const isRunning = status === "running";

  const totalTokens = steps.reduce(
    (sum, step) => sum + (step.token_count ?? 0),
    0,
  );

  return (
    <div className="flex flex-col overflow-hidden rounded-md border border-border bg-card">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <span className="text-sm font-medium text-foreground">{label}</span>
        <div className="flex items-center gap-2">
          <span
            className={`inline-block h-2.5 w-2.5 rounded-full ${isRunning ? "animate-pulse" : ""}`}
            style={{ backgroundColor: dotColor }}
          />
          <span className="text-xs text-muted-foreground">{statusLabel}</span>
        </div>
      </div>

      {/* Steps area */}
      <div className="flex-1 space-y-2 overflow-y-auto p-4">
        {steps.length === 0 && (
          <p className="py-8 text-center text-sm text-muted-foreground/60">
            {status === "idle"
              ? "Waiting for run to start..."
              : status === "running"
                ? "Receiving steps..."
                : "No steps recorded."}
          </p>
        )}
        {steps.map((step, idx) => (
          <StepCard key={`${step.step_index}-${idx}`} step={step} />
        ))}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between border-t border-border px-4 py-2">
        <span className="text-xs text-muted-foreground">
          {steps.length} step{steps.length !== 1 ? "s" : ""}
        </span>
        <span className="text-xs text-muted-foreground">
          {totalTokens} tokens
        </span>
      </div>
    </div>
  );
}

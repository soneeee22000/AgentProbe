"use client";

import { useRunStore } from "@/store/run-store";

/** Step-count row with a coloured dot and label. */
function CountRow({
  label,
  count,
  color,
}: {
  label: string;
  count: number;
  color: string;
}) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="flex items-center gap-2">
        <span
          className="inline-block size-2 rounded-full"
          style={{ backgroundColor: color }}
        />
        {label}
      </span>
      <span className="font-medium text-foreground">{count}</span>
    </div>
  );
}

/**
 * Right sidebar panel displaying run statistics, step breakdown, and failure analysis.
 */
export function RunStatsPanel() {
  const isRunning = useRunStore((s) => s.isRunning);
  const stepCounts = useRunStore((s) => s.stepCounts);
  const failures = useRunStore((s) => s.failures);
  const summary = useRunStore((s) => s.summary);
  const steps = useRunStore((s) => s.steps);

  /** Derive status label. */
  const status = isRunning
    ? "Running"
    : summary?.succeeded
      ? "Success"
      : summary
        ? "Failed"
        : "Idle";

  const statusColor = isRunning
    ? "text-[#ffb74d]"
    : summary?.succeeded
      ? "text-[#81c784]"
      : summary
        ? "text-[#ef5350]"
        : "text-muted-foreground";

  const totalSteps = steps.length;
  const totalTokens = summary?.total_tokens ?? 0;
  const durationMs = summary?.duration_ms;

  /** Unique failure types for display. */
  const uniqueFailures = [...new Set(failures)];

  return (
    <div className="flex w-60 shrink-0 flex-col border-l border-border">
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Run Stats
        </h2>
      </div>

      <div className="flex flex-col gap-4 p-4 text-xs text-muted-foreground">
        {/* Overview */}
        <div className="flex flex-col gap-2">
          <div className="flex justify-between">
            <span>Status</span>
            <span className={`font-medium ${statusColor}`}>{status}</span>
          </div>
          <div className="flex justify-between">
            <span>Steps</span>
            <span className="font-medium text-foreground">{totalSteps}</span>
          </div>
          <div className="flex justify-between">
            <span>Tokens</span>
            <span className="font-medium text-foreground">{totalTokens}</span>
          </div>
          {durationMs != null && (
            <div className="flex justify-between">
              <span>Duration</span>
              <span className="font-medium text-foreground">
                {(durationMs / 1000).toFixed(2)}s
              </span>
            </div>
          )}
        </div>

        {/* Step breakdown */}
        <div className="flex flex-col gap-1.5">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider">
            Step Breakdown
          </p>
          <CountRow
            label="Thoughts"
            count={stepCounts.thought}
            color="#4fc3f7"
          />
          <CountRow label="Actions" count={stepCounts.action} color="#81c784" />
          <CountRow
            label="Observations"
            count={stepCounts.observation}
            color="#ffb74d"
          />
          <CountRow label="Errors" count={stepCounts.error} color="#ef5350" />
        </div>

        {/* Failure analysis */}
        <div className="flex flex-col gap-1.5">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider">
            Failure Analysis
          </p>
          {uniqueFailures.length > 0 ? (
            uniqueFailures.map((f) => (
              <span key={f} className="text-[#ef5350]">
                {f}
              </span>
            ))
          ) : (
            <span>No failures detected</span>
          )}
        </div>
      </div>
    </div>
  );
}

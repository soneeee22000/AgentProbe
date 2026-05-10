"use client";

import { useRunStore } from "@/store/run-store";

interface HeaderProps {
  /**
   * Optional context label for the right-hand side. When omitted on the
   * playground, falls back to the live run model from the store. On other
   * pages, callers can pass page-specific context (e.g. the run's model on
   * the run detail page) to avoid showing a stale/unrelated value.
   */
  context?: { label: string; value: string };
  /**
   * When false, the running indicator is forced to "Idle" regardless of
   * the playground store state. Useful on detail pages that have nothing
   * to do with the live run.
   */
  showLiveStatus?: boolean;
}

/**
 * Application header. Shows a status pill on the left and a contextual
 * key/value on the right. The live "Running/Idle" indicator only reflects
 * playground activity when ``showLiveStatus`` is true (default).
 */
export function Header({ context, showLiveStatus = true }: HeaderProps = {}) {
  const isRunning = useRunStore((state) => state.isRunning);
  const playgroundModel = useRunStore((state) => state.model);
  const liveStatus = showLiveStatus && isRunning;

  const right = context ?? { label: "Model", value: playgroundModel };

  return (
    <header className="flex h-12 items-center justify-between border-b border-border bg-card px-6">
      {/* Status indicator */}
      <div className="flex items-center gap-2">
        <span className="relative flex h-2.5 w-2.5">
          {liveStatus && (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
          )}
          <span
            className={`relative inline-flex h-2.5 w-2.5 rounded-full ${
              liveStatus ? "bg-green-500" : "bg-muted-foreground/40"
            }`}
          />
        </span>
        <span className="text-xs text-muted-foreground">
          {liveStatus ? "Running" : "Idle"}
        </span>
      </div>

      {/* Right-hand context */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">{right.label}:</span>
        <span className="text-xs font-medium text-foreground">
          {right.value}
        </span>
      </div>
    </header>
  );
}

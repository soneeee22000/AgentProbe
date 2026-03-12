"use client";

import { useRunStore } from "@/store/run-store";

/**
 * Application header displaying run status indicator and current model name.
 * Shows a pulsing green dot when an agent run is active, gray when idle.
 */
export function Header() {
  const isRunning = useRunStore((state) => state.isRunning);
  const model = useRunStore((state) => state.model);

  return (
    <header className="flex h-12 items-center justify-between border-b border-border bg-card px-6">
      {/* Status indicator */}
      <div className="flex items-center gap-2">
        <span className="relative flex h-2.5 w-2.5">
          {isRunning && (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
          )}
          <span
            className={`relative inline-flex h-2.5 w-2.5 rounded-full ${
              isRunning ? "bg-green-500" : "bg-muted-foreground/40"
            }`}
          />
        </span>
        <span className="text-xs text-muted-foreground">
          {isRunning ? "Running" : "Idle"}
        </span>
      </div>

      {/* Model name */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">Model:</span>
        <span className="text-xs font-medium text-foreground">{model}</span>
      </div>
    </header>
  );
}

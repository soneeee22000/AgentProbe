"use client";

import { useCallback, type KeyboardEvent } from "react";
import { useRunStore } from "@/store/run-store";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ModelSelector } from "@/components/playground/model-selector";

const SAMPLE_QUERIES = [
  "What is 2^32 + sqrt(1764)?",
  "Search for latest Llama 3 benchmarks and summarize",
  "Break down the steps to learn Rust as a Python dev",
];

interface QueryInputProps {
  /** Callback fired when the user triggers a run. */
  onRun: () => void;
}

/**
 * Top bar with a query text input, model/provider selectors, and a Run button.
 * Displays sample queries when the trace is empty.
 */
export function QueryInput({ onRun }: QueryInputProps) {
  const query = useRunStore((s) => s.query);
  const model = useRunStore((s) => s.model);
  const provider = useRunStore((s) => s.provider);
  const isRunning = useRunStore((s) => s.isRunning);
  const steps = useRunStore((s) => s.steps);
  const setQuery = useRunStore((s) => s.setQuery);
  const setModel = useRunStore((s) => s.setModel);
  const setProvider = useRunStore((s) => s.setProvider);

  /** Trigger run on Enter key. */
  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter" && !isRunning && query.trim()) {
        onRun();
      }
    },
    [isRunning, query, onRun],
  );

  /** Set a sample query and immediately run. */
  const handleSampleClick = useCallback(
    (sample: string) => {
      setQuery(sample);
      // Defer to next tick so the store updates before onRun reads query
      setTimeout(() => onRun(), 0);
    },
    [setQuery, onRun],
  );

  return (
    <div className="flex flex-col gap-3">
      {/* Input row */}
      <div className="flex items-center gap-3">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask the agent anything..."
          className="flex-1 bg-card font-mono text-sm"
          disabled={isRunning}
        />
        <ModelSelector
          model={model}
          provider={provider}
          onModelChange={setModel}
          onProviderChange={setProvider}
        />
        <Button
          variant="outline"
          size="sm"
          disabled={isRunning || !query.trim()}
          onClick={onRun}
          className="border-primary text-primary hover:bg-primary/10"
        >
          {isRunning ? "Running..." : "Run"}
        </Button>
      </div>

      {/* Sample queries — shown only when no steps exist */}
      {steps.length === 0 && (
        <div className="flex flex-wrap gap-2">
          {SAMPLE_QUERIES.map((sample) => (
            <button
              key={sample}
              type="button"
              onClick={() => handleSampleClick(sample)}
              className="rounded-md border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
            >
              {sample}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

"use client";

import { useQuery } from "@tanstack/react-query";
import { useCompareStore } from "@/store/compare-store";
import { streamRun, fetchProviders, type ProviderInfo } from "@/lib/api";
import type { AgentStep } from "@/lib/api";

/** Fallback providers when the API is unavailable. */
const FALLBACK_PROVIDERS: ProviderInfo[] = [
  {
    name: "groq",
    display_name: "Groq",
    available: true,
    models: [
      { id: "llama-3.1-8b-instant", name: "Llama 3.1 8B Instant" },
      { id: "llama-3.1-70b-versatile", name: "Llama 3.1 70B Versatile" },
      { id: "mixtral-8x7b-32768", name: "Mixtral 8x7B" },
      { id: "gemma2-9b-it", name: "Gemma 2 9B IT" },
    ],
  },
  {
    name: "ollama",
    display_name: "Ollama (Local)",
    available: true,
    models: [{ id: "llama3.1:8b", name: "Llama 3.1 8B" }],
  },
];

/**
 * Streams an agent run and feeds each step to the provided callback.
 * Sets the status callback to "complete" on success or "failed" on error.
 */
async function runStream(
  query: string,
  model: string,
  provider: string,
  addStep: (step: AgentStep) => void,
  setStatus: (status: "running" | "complete" | "failed") => void,
): Promise<void> {
  try {
    for await (const step of streamRun(query, model, provider)) {
      addStep(step);
    }
    setStatus("complete");
  } catch {
    setStatus("failed");
  }
}

/**
 * Renders a model/provider selector pair for one side of the comparison.
 */
function SideSelector({
  label,
  model,
  provider,
  onModelChange,
  onProviderChange,
  disabled,
  providers,
}: {
  label: string;
  model: string;
  provider: string;
  onModelChange: (v: string) => void;
  onProviderChange: (v: string) => void;
  disabled: boolean;
  providers: ProviderInfo[];
}) {
  const activeProvider = providers.find((p) => p.name === provider);
  const models = activeProvider?.models ?? [];
  const selectClassName =
    "rounded-md border border-border bg-secondary px-3 py-2 text-sm text-foreground";

  return (
    <div className="flex items-center gap-3">
      <span className="text-xs font-medium text-muted-foreground">
        {label}:
      </span>
      <select
        value={provider}
        onChange={(e) => {
          onProviderChange(e.target.value);
          const newP = providers.find((p) => p.name === e.target.value);
          if (newP?.models.length && !newP.models.some((m) => m.id === model)) {
            onModelChange(newP.models[0].id);
          }
        }}
        disabled={disabled}
        className={selectClassName}
      >
        {providers.map((p) => (
          <option key={p.name} value={p.name}>
            {p.available ? "\u25CF " : "\u25CB "}
            {p.display_name}
          </option>
        ))}
      </select>
      <select
        value={model}
        onChange={(e) => onModelChange(e.target.value)}
        disabled={disabled}
        className={selectClassName}
      >
        {models.map((m) => (
          <option key={m.id} value={m.id}>
            {m.name}
          </option>
        ))}
      </select>
    </div>
  );
}

/**
 * Control panel for the model comparison page.
 * Contains a shared query input, side-by-side model/provider selectors,
 * and Run Both / Reset action buttons.
 */
export function CompareControls() {
  const {
    query,
    setQuery,
    leftModel,
    setLeftModel,
    rightModel,
    setRightModel,
    leftProvider,
    setLeftProvider,
    rightProvider,
    setRightProvider,
    leftStatus,
    rightStatus,
    addLeftStep,
    addRightStep,
    setLeftStatus,
    setRightStatus,
    reset,
  } = useCompareStore();

  const { data: providers = FALLBACK_PROVIDERS } = useQuery({
    queryKey: ["providers"],
    queryFn: fetchProviders,
    staleTime: 60_000,
  });

  const isRunning = leftStatus === "running" || rightStatus === "running";

  /**
   * Kicks off both model runs concurrently.
   * Resets state, sets statuses to running, and launches two
   * independent async stream consumers.
   */
  function handleRunBoth(): void {
    if (!query.trim()) return;

    reset();
    setLeftStatus("running");
    setRightStatus("running");

    runStream(query, leftModel, leftProvider, addLeftStep, setLeftStatus);
    runStream(query, rightModel, rightProvider, addRightStep, setRightStatus);
  }

  /** Resets all comparison state back to initial values. */
  function handleReset(): void {
    reset();
  }

  return (
    <div className="space-y-4 border-b border-border bg-card px-6 py-4">
      {/* Shared query input */}
      <div className="flex gap-3">
        <input
          type="text"
          placeholder="Enter a query to compare models..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !isRunning) handleRunBoth();
          }}
          disabled={isRunning}
          className="flex-1 rounded-md border border-border bg-secondary px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground disabled:opacity-50"
        />
        <button
          onClick={handleRunBoth}
          disabled={isRunning || !query.trim()}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          Run Both
        </button>
        <button
          onClick={handleReset}
          disabled={isRunning}
          className="rounded-md border border-border bg-secondary px-4 py-2 text-sm font-medium text-foreground hover:bg-muted disabled:opacity-50"
        >
          Reset
        </button>
      </div>

      {/* Side-by-side model/provider selectors */}
      <div className="grid grid-cols-2 gap-4">
        <SideSelector
          label="Left"
          model={leftModel}
          provider={leftProvider}
          onModelChange={setLeftModel}
          onProviderChange={setLeftProvider}
          disabled={isRunning}
          providers={providers}
        />
        <SideSelector
          label="Right"
          model={rightModel}
          provider={rightProvider}
          onModelChange={setRightModel}
          onProviderChange={setRightProvider}
          disabled={isRunning}
          providers={providers}
        />
      </div>
    </div>
  );
}

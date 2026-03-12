"use client";

import { useCallback } from "react";
import { useRunStore } from "@/store/run-store";
import { streamRun } from "@/lib/api";
import { QueryInput } from "@/components/playground/query-input";
import { TraceViewer } from "@/components/playground/trace-viewer";
import { ToolPanel } from "@/components/playground/tool-panel";
import { RunStatsPanel } from "@/components/playground/run-stats-panel";

/**
 * Main Playground container — the agent trace viewer page.
 * Composes the query input bar, tool panel, trace viewer, and run stats panel
 * into a responsive 3-column layout.
 */
export function PlaygroundView() {
  const query = useRunStore((s) => s.query);
  const model = useRunStore((s) => s.model);
  const provider = useRunStore((s) => s.provider);
  const startRun = useRunStore((s) => s.startRun);
  const addStep = useRunStore((s) => s.addStep);
  const endRun = useRunStore((s) => s.endRun);

  /**
   * Kicks off an agent run by streaming steps from the API.
   * Each yielded step is pushed into the store; the run ends
   * when the generator completes or an error is caught.
   */
  const handleRun = useCallback(async () => {
    const currentQuery = useRunStore.getState().query;
    const currentModel = useRunStore.getState().model;
    const currentProvider = useRunStore.getState().provider;

    if (!currentQuery.trim()) return;

    startRun();

    try {
      for await (const step of streamRun(
        currentQuery,
        currentModel,
        currentProvider,
      )) {
        addStep(step);
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unknown error occurred";
      addStep({
        step_type: "error",
        content: message,
        step_index: -1,
        timestamp: Date.now(),
        failure_type: "api_error",
      });
    } finally {
      endRun();
    }
  }, [startRun, addStep, endRun]);

  return (
    <div className="flex h-full flex-col">
      {/* Top bar — query input */}
      <div className="border-b border-border bg-card px-4 py-3">
        <QueryInput onRun={handleRun} />
      </div>

      {/* 3-column layout */}
      <div className="flex flex-1 overflow-hidden">
        <ToolPanel />
        <TraceViewer />
        <RunStatsPanel />
      </div>
    </div>
  );
}

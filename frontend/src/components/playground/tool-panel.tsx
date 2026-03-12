"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchTools } from "@/lib/api";
import { useRunStore } from "@/store/run-store";

/**
 * Left sidebar panel that lists tools available to the agent.
 * Fetches tools from the API on mount and highlights the currently active tool.
 */
export function ToolPanel() {
  const activeToolName = useRunStore((s) => s.activeToolName);

  const { data: tools, isLoading } = useQuery({
    queryKey: ["tools"],
    queryFn: fetchTools,
    staleTime: 60_000,
  });

  return (
    <div className="flex w-64 shrink-0 flex-col border-r border-border">
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Available Tools
        </h2>
      </div>

      <div className="flex flex-1 flex-col gap-2 overflow-y-auto p-3">
        {isLoading && (
          <p className="px-1 text-xs text-muted-foreground">Loading tools...</p>
        )}

        {tools?.map((tool) => {
          const isActive = activeToolName === tool.name;

          return (
            <div
              key={tool.name}
              className={`rounded-md border px-3 py-2 text-xs transition-colors ${
                isActive
                  ? "border-[#81c784]/40 bg-[#81c784]/10"
                  : "border-border bg-card"
              }`}
            >
              <p className="font-semibold text-[#81c784]">{tool.name}</p>
              <p className="mt-0.5 text-muted-foreground">{tool.description}</p>
            </div>
          );
        })}

        {!isLoading && tools?.length === 0 && (
          <p className="px-1 text-xs text-muted-foreground">
            No tools registered.
          </p>
        )}
      </div>
    </div>
  );
}

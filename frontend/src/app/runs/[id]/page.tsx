"use client";

import { useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { StepCard } from "@/components/playground/step-card";
import { ExportRunButton } from "@/components/runs/export-run-button";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { fetchRun, replayRun, type AgentStep } from "@/lib/api";

/**
 * Run Detail page — view the full step-by-step trace of a single run.
 * Includes a replay button that animates steps appearing one by one.
 */
export default function RunDetailPage() {
  const params = useParams();
  const router = useRouter();
  const runId = params.id as string;

  const [replaying, setReplaying] = useState(false);
  const [replaySteps, setReplaySteps] = useState<AgentStep[]>([]);

  const {
    data: run,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["run", runId],
    queryFn: () => fetchRun(runId),
  });

  const handleReplay = useCallback(async () => {
    setReplaying(true);
    setReplaySteps([]);
    try {
      for await (const step of replayRun(runId)) {
        setReplaySteps((prev) => [...prev, step]);
      }
    } finally {
      setReplaying(false);
    }
  }, [runId]);

  const displaySteps = replaying ? replaySteps : (run?.steps ?? []);

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex flex-1 flex-col overflow-hidden p-6">
          {/* Back button */}
          <Button
            variant="ghost"
            size="sm"
            className="mb-4 w-fit text-xs text-muted-foreground"
            onClick={() => router.push("/runs")}
          >
            &larr; Back to Runs
          </Button>

          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-8 w-96" />
              <Skeleton className="h-4 w-64" />
              <div className="mt-6 space-y-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-20 w-full" />
                ))}
              </div>
            </div>
          ) : isError || !run ? (
            <div className="flex flex-col items-center justify-center py-20">
              <p className="text-sm text-destructive">
                Run not found or failed to load.
              </p>
            </div>
          ) : (
            <>
              {/* Run header */}
              <div className="mb-4 rounded-md border border-border bg-card p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h1 className="text-lg font-semibold text-foreground">
                      {run.query}
                    </h1>
                    <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="font-mono">{run.run_id}</span>
                      <span>{run.model}</span>
                      <span>{run.provider}</span>
                      <Badge
                        variant={run.succeeded ? "default" : "destructive"}
                        className="text-xs"
                      >
                        {run.succeeded ? "Success" : "Failed"}
                      </Badge>
                      {run.duration_ms && (
                        <span>{run.duration_ms.toFixed(0)}ms</span>
                      )}
                      <span>{run.total_tokens} tokens</span>
                      <span>{run.step_count} steps</span>
                    </div>
                    {run.failures.length > 0 && (
                      <div className="mt-2 flex gap-1">
                        {run.failures.map((f, i) => (
                          <Badge
                            key={i}
                            variant="destructive"
                            className="text-xs"
                          >
                            {f}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <ExportRunButton runId={runId} />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleReplay}
                      disabled={replaying}
                    >
                      {replaying ? "Replaying..." : "Replay"}
                    </Button>
                  </div>
                </div>
              </div>

              {/* Step trace */}
              <ScrollArea className="flex-1 rounded-md border border-border bg-card p-4">
                <div className="space-y-2">
                  {displaySteps.map((step, i) => (
                    <StepCard key={i} step={step} />
                  ))}
                </div>
              </ScrollArea>

              {/* Final answer */}
              {run.final_answer && !replaying && (
                <div className="mt-3 rounded-md border border-[#ce93d8]/30 bg-[#ce93d8]/5 p-4">
                  <p className="text-xs font-medium text-[#ce93d8]">
                    Final Answer
                  </p>
                  <p className="mt-1 text-sm text-foreground">
                    {run.final_answer}
                  </p>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}

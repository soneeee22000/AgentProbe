"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { ExportButtons } from "@/components/benchmarks/export-buttons";
import { ResultGrid } from "@/components/benchmarks/result-grid";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchSuiteDetail } from "@/lib/api";

/**
 * Suite Results page — detailed view of a benchmark suite run.
 * Shows aggregate stats and per-case results with pass/fail and scores.
 */
export default function SuiteDetailPage() {
  const params = useParams();
  const router = useRouter();
  const suiteId = params.suiteId as string;

  const {
    data: suite,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["benchmark-suite", suiteId],
    queryFn: () => fetchSuiteDetail(suiteId),
  });

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex flex-1 flex-col overflow-hidden p-6">
          <Button
            variant="ghost"
            size="sm"
            className="mb-4 w-fit text-xs text-muted-foreground"
            onClick={() => router.push("/benchmarks")}
          >
            &larr; Back to Benchmarks
          </Button>

          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-8 w-64" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-64 w-full" />
            </div>
          ) : isError || !suite ? (
            <div className="flex flex-col items-center justify-center py-20">
              <p className="text-sm text-destructive">
                Suite not found or failed to load.
              </p>
            </div>
          ) : (
            <>
              {/* Suite header */}
              <div className="mb-4">
                <div className="flex items-center gap-3">
                  <h1 className="text-lg font-semibold text-foreground">
                    Suite {suite.id}
                  </h1>
                  <Badge
                    variant={
                      suite.status === "completed" ? "default" : "secondary"
                    }
                    className="text-xs"
                  >
                    {suite.status}
                  </Badge>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">
                  {suite.model_id} via {suite.provider}
                </p>
                <div className="mt-2">
                  <ExportButtons suiteId={suite.id} />
                </div>
              </div>

              {/* Stats cards */}
              <div className="mb-4 grid grid-cols-4 gap-3">
                <Card className="border-border">
                  <CardContent className="p-4">
                    <p className="text-xs text-muted-foreground">Total Cases</p>
                    <p className="text-2xl font-semibold">
                      {suite.total_cases}
                    </p>
                  </CardContent>
                </Card>
                <Card className="border-border">
                  <CardContent className="p-4">
                    <p className="text-xs text-muted-foreground">
                      Success Rate
                    </p>
                    <p className="text-2xl font-semibold text-[#81c784]">
                      {(suite.success_rate * 100).toFixed(1)}%
                    </p>
                  </CardContent>
                </Card>
                <Card className="border-border">
                  <CardContent className="p-4">
                    <p className="text-xs text-muted-foreground">Avg Steps</p>
                    <p className="text-2xl font-semibold">
                      {suite.avg_steps.toFixed(1)}
                    </p>
                  </CardContent>
                </Card>
                <Card className="border-border">
                  <CardContent className="p-4">
                    <p className="text-xs text-muted-foreground">
                      Failure Types
                    </p>
                    <p className="text-2xl font-semibold text-[#ef5350]">
                      {Object.keys(suite.failure_summary).length}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Failure summary */}
              {Object.keys(suite.failure_summary).length > 0 && (
                <div className="mb-4 flex flex-wrap gap-2">
                  {Object.entries(suite.failure_summary).map(
                    ([type, count]) => (
                      <Badge
                        key={type}
                        variant="destructive"
                        className="text-xs"
                      >
                        {type}: {count}
                      </Badge>
                    ),
                  )}
                </div>
              )}

              {/* Results grid */}
              <div className="flex-1 overflow-auto rounded-md border border-border bg-card">
                <ResultGrid results={suite.results} />
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

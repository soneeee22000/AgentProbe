"use client";

import { useQuery } from "@tanstack/react-query";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatsOverview } from "@/components/analytics/stats-overview";
import { FailureDistributionChart } from "@/components/analytics/failure-chart";
import { ModelComparisonChart } from "@/components/analytics/model-comparison-chart";
import { FailureByModelChart } from "@/components/analytics/failure-heatmap";
import { fetchFailureAnalytics, fetchModelAnalytics } from "@/lib/api";

/** Query key constants to avoid magic strings. */
const FAILURE_QUERY_KEY = ["analytics", "failures"] as const;
const MODEL_QUERY_KEY = ["analytics", "models"] as const;

/**
 * Skeleton placeholder for a chart card while data is loading.
 * Renders a card-shaped skeleton with an inner block for chart content.
 */
function ChartSkeleton() {
  return (
    <Card className="border-[#1e2530] bg-[#10141a]">
      <CardHeader>
        <Skeleton className="h-4 w-40 bg-[#1e2530]" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-64 w-full bg-[#1e2530]" />
      </CardContent>
    </Card>
  );
}

/**
 * Empty state displayed when no analytics data exists.
 * Prompts the user to run benchmarks to generate data.
 */
function EmptyState() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 py-20">
      <p className="text-lg font-medium text-foreground">No analytics yet</p>
      <p className="text-sm text-muted-foreground">
        Run some benchmarks to see analytics here.
      </p>
    </div>
  );
}

/**
 * Analytics dashboard page for AgentProbe.
 * Fetches failure and model analytics data, then renders stat cards,
 * a failure distribution chart, model comparison chart, and
 * failure-by-model heatmap in a responsive layout.
 */
export default function AnalyticsPage() {
  const failureQuery = useQuery({
    queryKey: FAILURE_QUERY_KEY,
    queryFn: fetchFailureAnalytics,
  });

  const modelQuery = useQuery({
    queryKey: MODEL_QUERY_KEY,
    queryFn: fetchModelAnalytics,
  });

  const isLoading = failureQuery.isLoading || modelQuery.isLoading;
  const failureData = failureQuery.data;
  const modelData = modelQuery.data;

  /** Determine if we have meaningful data to display. */
  const hasData =
    failureData &&
    modelData &&
    (failureData.total_runs > 0 || Object.keys(modelData.models).length > 0);

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">
          <h1 className="mb-6 text-2xl font-semibold text-foreground">
            Analytics
          </h1>

          {isLoading && (
            <div className="space-y-6">
              {/* Stats skeleton row */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Card key={i} className="border-[#1e2530] bg-[#10141a]">
                    <CardHeader className="pb-1">
                      <Skeleton className="h-3 w-24 bg-[#1e2530]" />
                    </CardHeader>
                    <CardContent>
                      <Skeleton className="h-8 w-20 bg-[#1e2530]" />
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Chart skeletons */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <ChartSkeleton />
                <ChartSkeleton />
              </div>
              <ChartSkeleton />
            </div>
          )}

          {!isLoading && !hasData && <EmptyState />}

          {!isLoading && hasData && failureData && modelData && (
            <div className="space-y-6">
              {/* Stats overview row */}
              <StatsOverview failureData={failureData} modelData={modelData} />

              {/* Two-column chart grid */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <Card className="border-[#1e2530] bg-[#10141a]">
                  <CardHeader>
                    <CardTitle className="text-sm font-medium text-foreground">
                      Failure Distribution
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <FailureDistributionChart data={failureData} />
                  </CardContent>
                </Card>

                <Card className="border-[#1e2530] bg-[#10141a]">
                  <CardHeader>
                    <CardTitle className="text-sm font-medium text-foreground">
                      Model Comparison
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ModelComparisonChart data={modelData} />
                  </CardContent>
                </Card>
              </div>

              {/* Full-width failure-by-model chart */}
              <Card className="border-[#1e2530] bg-[#10141a]">
                <CardHeader>
                  <CardTitle className="text-sm font-medium text-foreground">
                    Failures by Model
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <FailureByModelChart data={failureData} />
                </CardContent>
              </Card>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

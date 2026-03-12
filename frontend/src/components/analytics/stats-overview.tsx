"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { FailureAnalytics, ModelAnalytics } from "@/lib/api";

/** Color constants for stat values. */
const STAT_VALUE_COLOR = "text-[#4fc3f7]";

interface StatsOverviewProps {
  /** Failure analytics data from the API. */
  failureData: FailureAnalytics;
  /** Model analytics data from the API. */
  modelData: ModelAnalytics;
}

/**
 * Finds the model with the highest success rate from model analytics.
 * Returns "N/A" when no models have been evaluated yet.
 */
function getMostReliableModel(modelData: ModelAnalytics): string {
  const entries = Object.entries(modelData.models);
  if (entries.length === 0) return "N/A";

  let bestModel = entries[0][0];
  let bestRate = entries[0][1].success_rate;

  for (const [name, stats] of entries) {
    if (stats.success_rate > bestRate) {
      bestRate = stats.success_rate;
      bestModel = name;
    }
  }

  return bestModel;
}

/**
 * Computes the average number of steps across all models.
 * Returns null when no step data is available.
 */
function getAvgSteps(modelData: ModelAnalytics): number | null {
  const entries = Object.values(modelData.models);
  const stepsValues = entries
    .map((m) => m.avg_steps)
    .filter((v): v is number => v !== null);

  if (stepsValues.length === 0) return null;

  const sum = stepsValues.reduce((a, b) => a + b, 0);
  return sum / stepsValues.length;
}

/**
 * Top-level summary cards displaying key analytics metrics.
 * Shows Total Runs, Failure Rate, Most Reliable Model, and Avg Steps.
 */
export function StatsOverview({ failureData, modelData }: StatsOverviewProps) {
  const avgSteps = getAvgSteps(modelData);

  const stats = [
    {
      label: "Total Runs",
      value: failureData.total_runs.toLocaleString(),
    },
    {
      label: "Failure Rate",
      value: `${(failureData.failure_rate * 100).toFixed(1)}%`,
    },
    {
      label: "Most Reliable Model",
      value: getMostReliableModel(modelData),
    },
    {
      label: "Avg Steps",
      value: avgSteps !== null ? avgSteps.toFixed(1) : "N/A",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.label} className="border-[#1e2530] bg-[#10141a]">
          <CardHeader className="pb-1">
            <CardTitle className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              {stat.label}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className={`text-2xl font-semibold ${STAT_VALUE_COLOR}`}>
              {stat.value}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

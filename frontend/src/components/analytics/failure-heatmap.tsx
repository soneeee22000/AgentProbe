"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { FailureAnalytics } from "@/lib/api";

/** Tick color for axis labels. */
const TICK_COLOR = "#6b7a8d";

/** Color palette for failure type segments. */
const SEGMENT_COLORS = ["#4fc3f7", "#81c784", "#ffb74d", "#ce93d8", "#ef5350"];

interface FailureByModelChartProps {
  /** Failure analytics data from the API. */
  data: FailureAnalytics;
}

interface HeatmapRow {
  model: string;
  [failureType: string]: string | number;
}

/**
 * Custom tooltip for the failure-by-model stacked bar chart.
 * Displays model name and counts per failure type.
 */
function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className="rounded border border-[#1e2530] bg-[#10141a] px-3 py-2 text-sm text-[#c9d4e0]">
      <p className="mb-1 font-medium">{label}</p>
      {payload
        .filter((entry) => entry.value > 0)
        .map((entry) => (
          <p
            key={entry.name}
            className="text-xs"
            style={{ color: entry.color }}
          >
            {entry.name}: {entry.value}
          </p>
        ))}
    </div>
  );
}

/**
 * Stacked bar chart showing failure types broken down by model.
 * Each model is a bar on the X axis, with colored segments for each failure type.
 */
export function FailureByModelChart({ data }: FailureByModelChartProps) {
  const models = Object.keys(data.by_model);

  if (models.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        No failure-by-model data available yet.
      </div>
    );
  }

  /** Collect all unique failure types across models. */
  const failureTypesSet = new Set<string>();
  for (const modelFailures of Object.values(data.by_model)) {
    for (const fType of Object.keys(modelFailures)) {
      failureTypesSet.add(fType);
    }
  }
  const failureTypes = Array.from(failureTypesSet);

  /** Build chart rows: one per model with a key per failure type. */
  const chartData: HeatmapRow[] = models.map((model) => {
    const row: HeatmapRow = { model };
    for (const fType of failureTypes) {
      row[fType] = data.by_model[model][fType] ?? 0;
    }
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart
        data={chartData}
        margin={{ top: 10, right: 20, bottom: 10, left: 0 }}
      >
        <XAxis
          dataKey="model"
          tick={{ fill: TICK_COLOR, fontSize: 12 }}
          axisLine={{ stroke: TICK_COLOR }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: TICK_COLOR, fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={false} />
        <Legend wrapperStyle={{ color: TICK_COLOR, fontSize: 12 }} />
        {failureTypes.map((fType, index) => (
          <Bar
            key={fType}
            dataKey={fType}
            name={fType}
            stackId="failures"
            fill={SEGMENT_COLORS[index % SEGMENT_COLORS.length]}
            radius={
              index === failureTypes.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]
            }
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

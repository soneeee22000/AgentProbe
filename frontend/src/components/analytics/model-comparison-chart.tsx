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
import type { ModelAnalytics } from "@/lib/api";

/** Tick color for axis labels. */
const TICK_COLOR = "#6b7a8d";

/** Bar colors for each metric. */
const METRIC_COLORS = {
  success_rate: "#4fc3f7",
  avg_steps: "#81c784",
  avg_tokens: "#ffb74d",
} as const;

interface ModelComparisonChartProps {
  /** Model analytics data from the API. */
  data: ModelAnalytics;
}

interface ModelRow {
  name: string;
  success_rate: number;
  avg_steps: number;
  avg_tokens: number;
}

/**
 * Custom tooltip for the model comparison chart.
 * Renders a dark-themed tooltip with model name and metric values.
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
      {payload.map((entry) => (
        <p key={entry.name} className="text-xs" style={{ color: entry.color }}>
          {entry.name}: {entry.value.toFixed(1)}
        </p>
      ))}
    </div>
  );
}

/**
 * Grouped bar chart comparing models across three metrics:
 * success rate (%), average steps, and average tokens.
 * Each metric uses a distinct color from the chart palette.
 */
export function ModelComparisonChart({ data }: ModelComparisonChartProps) {
  const chartData: ModelRow[] = Object.entries(data.models).map(
    ([name, stats]) => ({
      name,
      success_rate: stats.success_rate * 100,
      avg_steps: stats.avg_steps ?? 0,
      avg_tokens: stats.avg_tokens ?? 0,
    }),
  );

  if (chartData.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        No model data available yet.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart
        data={chartData}
        margin={{ top: 10, right: 20, bottom: 10, left: 0 }}
      >
        <XAxis
          dataKey="name"
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
        <Bar
          dataKey="success_rate"
          name="Success Rate (%)"
          fill={METRIC_COLORS.success_rate}
          radius={[4, 4, 0, 0]}
          barSize={20}
        />
        <Bar
          dataKey="avg_steps"
          name="Avg Steps"
          fill={METRIC_COLORS.avg_steps}
          radius={[4, 4, 0, 0]}
          barSize={20}
        />
        <Bar
          dataKey="avg_tokens"
          name="Avg Tokens"
          fill={METRIC_COLORS.avg_tokens}
          radius={[4, 4, 0, 0]}
          barSize={20}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}

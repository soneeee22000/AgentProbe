"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { FailureAnalytics } from "@/lib/api";

/** Chart color palette matching CSS variables. */
const CHART_COLORS = ["#4fc3f7", "#81c784", "#ffb74d", "#ce93d8", "#ef5350"];

/** Tick color for axis labels. */
const TICK_COLOR = "#6b7a8d";

interface FailureDistributionChartProps {
  /** Failure analytics data from the API. */
  data: FailureAnalytics;
}

interface FailureRow {
  name: string;
  count: number;
}

/**
 * Custom tooltip for the failure distribution chart.
 * Renders a dark-themed tooltip with failure type and count.
 */
function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ value: number; payload: FailureRow }>;
}) {
  if (!active || !payload || payload.length === 0) return null;

  const row = payload[0].payload;
  return (
    <div className="rounded border border-[#1e2530] bg-[#10141a] px-3 py-2 text-sm text-[#c9d4e0]">
      <p className="font-medium">{row.name}</p>
      <p className="text-xs text-muted-foreground">Count: {row.count}</p>
    </div>
  );
}

/**
 * Horizontal bar chart showing the distribution of failure types.
 * Each bar is color-coded using the chart color palette and sorted by count descending.
 */
export function FailureDistributionChart({
  data,
}: FailureDistributionChartProps) {
  const chartData: FailureRow[] = Object.entries(data.by_type)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);

  if (chartData.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        No failure data available yet.
      </div>
    );
  }

  return (
    <ResponsiveContainer
      width="100%"
      height={Math.max(200, chartData.length * 48)}
    >
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ left: 20, right: 20 }}
      >
        <XAxis
          type="number"
          tick={{ fill: TICK_COLOR, fontSize: 12 }}
          axisLine={{ stroke: TICK_COLOR }}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fill: TICK_COLOR, fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={140}
        />
        <Tooltip content={<CustomTooltip />} cursor={false} />
        <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={24}>
          {chartData.map((_entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={CHART_COLORS[index % CHART_COLORS.length]}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

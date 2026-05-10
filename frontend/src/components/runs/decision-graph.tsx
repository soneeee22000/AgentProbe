"use client";

import { useMemo, useState } from "react";
import type { AgentStep } from "@/lib/api";

interface DecisionGraphProps {
  steps: AgentStep[];
  finalAnswer?: string;
  query?: string;
}

interface GraphNode {
  id: string;
  x: number;
  y: number;
  type:
    | "query"
    | "thought"
    | "action"
    | "observation"
    | "final"
    | "error"
    | "system";
  label: string;
  detail: string;
  toolName?: string;
  failureType?: string;
  latencyMs?: number;
  tokenCount?: number;
  stepIndex: number;
}

interface GraphEdge {
  from: string;
  to: string;
  failed?: boolean;
}

const NODE_COLORS: Record<
  GraphNode["type"],
  { fill: string; stroke: string; text: string }
> = {
  query: { fill: "#1e2530", stroke: "#6b7a8d", text: "#c9d4e0" },
  thought: { fill: "#0d1f2a", stroke: "#4fc3f7", text: "#4fc3f7" },
  action: { fill: "#0d2010", stroke: "#81c784", text: "#81c784" },
  observation: { fill: "#2a1c08", stroke: "#ffb74d", text: "#ffb74d" },
  final: { fill: "#241627", stroke: "#ce93d8", text: "#ce93d8" },
  error: { fill: "#2a0d0d", stroke: "#ef5350", text: "#ef5350" },
  system: { fill: "#10141a", stroke: "#546e7a", text: "#6b7a8d" },
};

const NODE_LABELS: Record<GraphNode["type"], string> = {
  query: "Query",
  thought: "Thought",
  action: "Action",
  observation: "Observation",
  final: "Decision",
  error: "Error",
  system: "System",
};

const COL_X: Record<GraphNode["type"], number> = {
  query: 40,
  thought: 220,
  action: 420,
  observation: 620,
  final: 820,
  error: 420,
  system: 40,
};

const NODE_WIDTH = 170;
const NODE_HEIGHT = 64;
const ROW_GAP = 100;
const TOP_PAD = 32;

function buildGraph(
  steps: AgentStep[],
  query: string | undefined,
  finalAnswer: string | undefined,
): { nodes: GraphNode[]; edges: GraphEdge[]; width: number; height: number } {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];

  // Filter out system summary blobs (JSON), keep real steps
  const visible = steps.filter(
    (s) => !(s.step_type === "system" && s.content.startsWith("{")),
  );

  // Query node (entry point)
  if (query) {
    nodes.push({
      id: "query",
      x: COL_X.query,
      y: TOP_PAD,
      type: "query",
      label: "Query",
      detail: query,
      stepIndex: -1,
    });
  }

  // Group thought + action + observation into one row.
  // Each row represents one ReAct cycle.
  type Row = {
    rowIdx: number;
    thought?: AgentStep;
    action?: AgentStep;
    observation?: AgentStep;
    failure?: AgentStep;
    final?: AgentStep;
  };
  const rows: Row[] = [];
  let current: Row | null = null;

  for (const step of visible) {
    if (step.step_type === "thought") {
      if (current) rows.push(current);
      current = { rowIdx: rows.length, thought: step };
    } else if (step.step_type === "action") {
      if (!current) current = { rowIdx: rows.length };
      current.action = step;
    } else if (step.step_type === "observation") {
      if (!current) current = { rowIdx: rows.length };
      current.observation = step;
    } else if (step.step_type === "final_answer") {
      if (!current) current = { rowIdx: rows.length };
      current.final = step;
    } else if (step.step_type === "error") {
      if (!current) current = { rowIdx: rows.length };
      current.failure = step;
    }
  }
  if (current) rows.push(current);

  // Lay out rows
  rows.forEach((row, idx) => {
    const y = TOP_PAD + idx * ROW_GAP;
    let prevId: string | null = null;
    if (idx === 0 && query) prevId = "query";
    else if (idx > 0) {
      // chain to previous row's last node
      const prev = rows[idx - 1];
      prevId =
        (prev.observation && `obs-${prev.rowIdx}`) ||
        (prev.action && `act-${prev.rowIdx}`) ||
        (prev.thought && `thought-${prev.rowIdx}`) ||
        null;
    }

    if (row.thought) {
      const id = `thought-${row.rowIdx}`;
      nodes.push({
        id,
        x: COL_X.thought,
        y,
        type: "thought",
        label: NODE_LABELS.thought,
        detail: row.thought.content,
        failureType:
          row.thought.failure_type !== "none"
            ? row.thought.failure_type
            : undefined,
        latencyMs: row.thought.latency_ms,
        tokenCount: row.thought.token_count,
        stepIndex: row.thought.step_index,
      });
      if (prevId) edges.push({ from: prevId, to: id });
      prevId = id;
    }

    if (row.action) {
      const id = `act-${row.rowIdx}`;
      const isFailure = row.action.failure_type !== "none";
      nodes.push({
        id,
        x: COL_X.action,
        y,
        type: isFailure ? "error" : "action",
        label: NODE_LABELS.action,
        detail: row.action.tool_args || row.action.content,
        toolName: row.action.tool_name,
        failureType: isFailure ? row.action.failure_type : undefined,
        latencyMs: row.action.latency_ms,
        tokenCount: row.action.token_count,
        stepIndex: row.action.step_index,
      });
      if (prevId) edges.push({ from: prevId, to: id, failed: isFailure });
      prevId = id;
    }

    if (row.observation) {
      const id = `obs-${row.rowIdx}`;
      const isFailure = row.observation.failure_type !== "none";
      nodes.push({
        id,
        x: COL_X.observation,
        y,
        type: isFailure ? "error" : "observation",
        label: NODE_LABELS.observation,
        detail: row.observation.content,
        failureType: isFailure ? row.observation.failure_type : undefined,
        latencyMs: row.observation.latency_ms,
        tokenCount: row.observation.token_count,
        stepIndex: row.observation.step_index,
      });
      if (prevId) edges.push({ from: prevId, to: id, failed: isFailure });
      prevId = id;
    }

    if (row.final) {
      const id = `final-${row.rowIdx}`;
      const isFailure = row.final.failure_type !== "none";
      nodes.push({
        id,
        x: COL_X.final,
        y,
        type: "final",
        label: NODE_LABELS.final,
        detail: row.final.content || finalAnswer || "(no final answer)",
        failureType: isFailure ? row.final.failure_type : undefined,
        latencyMs: row.final.latency_ms,
        tokenCount: row.final.token_count,
        stepIndex: row.final.step_index,
      });
      if (prevId) edges.push({ from: prevId, to: id, failed: isFailure });
    }
  });

  // Add a trailing decision node if the run reached a final answer that
  // wasn't already absorbed into a row above
  const hasFinalNode = nodes.some((n) => n.type === "final");
  if (!hasFinalNode && finalAnswer) {
    const lastRow = rows[rows.length - 1];
    const lastId = lastRow
      ? (lastRow.observation && `obs-${lastRow.rowIdx}`) ||
        (lastRow.action && `act-${lastRow.rowIdx}`) ||
        (lastRow.thought && `thought-${lastRow.rowIdx}`)
      : "query";
    const y = TOP_PAD + rows.length * ROW_GAP;
    const id = "final-terminal";
    nodes.push({
      id,
      x: COL_X.final,
      y,
      type: "final",
      label: NODE_LABELS.final,
      detail: finalAnswer,
      stepIndex: 9999,
    });
    if (lastId) edges.push({ from: lastId, to: id });
  }

  const width = COL_X.final + NODE_WIDTH + 60;
  const height = TOP_PAD + Math.max(rows.length, 1) * ROW_GAP + 60;

  return { nodes, edges, width, height };
}

/**
 * Smooth cubic-bezier path between two node anchors.
 *
 * Two routing modes so backward links between rows don't loop with
 * negative control points:
 *   - Forward (target is to the right): exit right edge of source,
 *     enter left edge of target. Symmetric horizontal cubic.
 *   - Backward (target is to the left, e.g. the last node of one
 *     ReAct cycle feeding the first node of the next): exit the
 *     bottom of the source, enter the left of the target. The cubic
 *     stays inside the canvas.
 */
function edgePath(from: GraphNode, to: GraphNode): string {
  const sourceRight = from.x + NODE_WIDTH;
  const sourceMidY = from.y + NODE_HEIGHT / 2;
  const targetLeft = to.x;
  const targetMidY = to.y + NODE_HEIGHT / 2;

  if (targetLeft >= sourceRight) {
    // Forward: standard horizontal cubic.
    const dx = targetLeft - sourceRight;
    const cx1 = sourceRight + dx * 0.5;
    const cx2 = targetLeft - dx * 0.5;
    return `M ${sourceRight} ${sourceMidY} C ${cx1} ${sourceMidY}, ${cx2} ${targetMidY}, ${targetLeft} ${targetMidY}`;
  }

  // Backward: exit from bottom of source, curve down-and-left into
  // the left edge of target.
  const sourceBottomX = from.x + NODE_WIDTH / 2;
  const sourceBottomY = from.y + NODE_HEIGHT;
  const dy = targetMidY - sourceBottomY;
  const cy1 = sourceBottomY + dy * 0.6;
  const cx2 = Math.max(targetLeft - 60, 0);
  return `M ${sourceBottomX} ${sourceBottomY} C ${sourceBottomX} ${cy1}, ${cx2} ${targetMidY}, ${targetLeft} ${targetMidY}`;
}

function truncate(s: string, n: number): string {
  if (!s) return "";
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

/**
 * DecisionGraph — renders an agent run as a directed graph of reasoning steps.
 *
 * Each ReAct cycle (Thought -> Action -> Observation) is laid out as one row.
 * Failures are surfaced inline on the failing node with a red border + badge.
 * Hovering a node reveals full content in the side panel.
 */
export function DecisionGraph({
  steps,
  finalAnswer,
  query,
}: DecisionGraphProps) {
  const { nodes, edges, width, height } = useMemo(
    () => buildGraph(steps, query, finalAnswer),
    [steps, query, finalAnswer],
  );

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = nodes.find((n) => n.id === selectedId) ?? null;

  const nodeById = useMemo(() => {
    const m = new Map<string, GraphNode>();
    for (const n of nodes) m.set(n.id, n);
    return m;
  }, [nodes]);

  if (nodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        No reasoning steps to graph yet.
      </div>
    );
  }

  return (
    <div className="flex h-full gap-3">
      {/* Graph canvas */}
      <div className="flex-1 overflow-auto rounded-md border border-border bg-[#070a0e]">
        <svg
          width={width}
          height={height}
          className="block"
          style={{ minWidth: "100%" }}
        >
          <defs>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7a8d" />
            </marker>
            <marker
              id="arrow-fail"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef5350" />
            </marker>
            <pattern
              id="grid"
              width="24"
              height="24"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M 24 0 L 0 0 0 24"
                fill="none"
                stroke="#1a2030"
                strokeWidth="0.5"
              />
            </pattern>
          </defs>

          {/* Grid background */}
          <rect width={width} height={height} fill="url(#grid)" />

          {/* Edges */}
          {edges.map((e, i) => {
            const from = nodeById.get(e.from);
            const to = nodeById.get(e.to);
            if (!from || !to) return null;
            return (
              <path
                key={i}
                d={edgePath(from, to)}
                fill="none"
                stroke={e.failed ? "#ef5350" : "#6b7a8d"}
                strokeWidth={e.failed ? 2 : 1.5}
                strokeDasharray={e.failed ? "6 3" : undefined}
                markerEnd={e.failed ? "url(#arrow-fail)" : "url(#arrow)"}
                opacity={0.85}
              />
            );
          })}

          {/* Nodes */}
          {nodes.map((n) => {
            const colors = NODE_COLORS[n.type];
            const isSelected = n.id === selectedId;
            const hasFailure = !!n.failureType && n.failureType !== "none";
            return (
              <g
                key={n.id}
                transform={`translate(${n.x}, ${n.y})`}
                onClick={() => setSelectedId(n.id)}
                style={{ cursor: "pointer" }}
              >
                <rect
                  width={NODE_WIDTH}
                  height={NODE_HEIGHT}
                  rx={6}
                  ry={6}
                  fill={colors.fill}
                  stroke={hasFailure ? "#ef5350" : colors.stroke}
                  strokeWidth={isSelected ? 2.5 : 1.5}
                  opacity={isSelected ? 1 : 0.95}
                />
                <text
                  x={10}
                  y={18}
                  fill={hasFailure ? "#ef5350" : colors.text}
                  fontSize={11}
                  fontWeight={600}
                  fontFamily="ui-sans-serif, system-ui, sans-serif"
                  letterSpacing={0.4}
                  style={{ textTransform: "uppercase" }}
                >
                  {n.label}
                  {n.toolName ? ` · ${n.toolName}` : ""}
                </text>
                <text
                  x={10}
                  y={36}
                  fill="#c9d4e0"
                  fontSize={11}
                  fontFamily="ui-monospace, SFMono-Regular, monospace"
                >
                  {truncate(n.detail.replace(/\s+/g, " "), 28)}
                </text>
                <text
                  x={10}
                  y={54}
                  fill="#6b7a8d"
                  fontSize={10}
                  fontFamily="ui-sans-serif, system-ui, sans-serif"
                >
                  {n.latencyMs != null ? `${n.latencyMs.toFixed(0)}ms` : ""}
                  {n.tokenCount != null
                    ? `${n.latencyMs != null ? "  ·  " : ""}${n.tokenCount} tok`
                    : ""}
                </text>
                {hasFailure && (
                  <g transform={`translate(${NODE_WIDTH - 8}, 0)`}>
                    <circle r={5} fill="#ef5350" />
                    <text
                      x={0}
                      y={3}
                      textAnchor="middle"
                      fill="#fff"
                      fontSize={8}
                      fontWeight={700}
                    >
                      !
                    </text>
                  </g>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Side detail panel */}
      <div className="hidden w-[260px] flex-col gap-2 rounded-md border border-border bg-card p-4 lg:flex">
        {selected ? (
          <>
            <div className="flex items-center justify-between">
              <span
                className="rounded-sm px-2 py-0.5 text-xs font-semibold uppercase tracking-wide"
                style={{
                  backgroundColor: NODE_COLORS[selected.type].stroke + "22",
                  color: NODE_COLORS[selected.type].stroke,
                }}
              >
                {selected.label}
              </span>
              {selected.failureType && (
                <span className="rounded-sm bg-[#ef5350]/20 px-2 py-0.5 text-xs font-semibold text-[#ef5350]">
                  {selected.failureType}
                </span>
              )}
            </div>
            {selected.toolName && (
              <p className="text-xs text-muted-foreground">
                Tool:{" "}
                <span className="font-mono text-[#81c784]">
                  {selected.toolName}
                </span>
              </p>
            )}
            <div className="mt-1 max-h-[280px] overflow-auto whitespace-pre-wrap rounded bg-background/50 p-2 text-xs leading-relaxed text-foreground/90">
              {selected.detail}
            </div>
            <div className="mt-1 flex flex-wrap gap-3 text-xs text-muted-foreground">
              {selected.latencyMs != null && (
                <span>{selected.latencyMs.toFixed(0)}ms</span>
              )}
              {selected.tokenCount != null && (
                <span>{selected.tokenCount} tokens</span>
              )}
              {selected.stepIndex >= 0 && selected.stepIndex < 9999 && (
                <span>step #{selected.stepIndex}</span>
              )}
            </div>
          </>
        ) : (
          <div className="flex flex-1 flex-col items-center justify-center gap-2 text-center">
            <div className="text-xs uppercase tracking-wide text-muted-foreground">
              Decision Graph
            </div>
            <p className="text-xs leading-relaxed text-muted-foreground">
              Click a node to inspect its reasoning, tool call, or failure
              context.
            </p>
            <div className="mt-3 grid grid-cols-2 gap-1 text-[10px]">
              <Legend color="#4fc3f7" label="Thought" />
              <Legend color="#81c784" label="Action" />
              <Legend color="#ffb74d" label="Observation" />
              <Legend color="#ce93d8" label="Decision" />
              <Legend color="#ef5350" label="Failure" />
              <Legend color="#6b7a8d" label="Query" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span
        className="inline-block h-2 w-2 rounded-full"
        style={{ backgroundColor: color }}
      />
      <span className="text-muted-foreground">{label}</span>
    </div>
  );
}

"use client";

import type { RunSummary } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface RunTableProps {
  /** List of run summaries to display. */
  runs: RunSummary[];
  /** Callback when a row is clicked. */
  onRowClick: (runId: string) => void;
}

/**
 * Sortable table displaying agent run history.
 * Shows run ID, query, model, status, steps, duration, and timestamp.
 */
export function RunTable({ runs, onRowClick }: RunTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-20">ID</TableHead>
          <TableHead className="min-w-[200px]">Query</TableHead>
          <TableHead>Model</TableHead>
          <TableHead className="w-24">Status</TableHead>
          <TableHead className="w-16 text-right">Steps</TableHead>
          <TableHead className="w-24 text-right">Duration</TableHead>
          <TableHead className="w-16 text-right">Tokens</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {runs.map((run) => (
          <TableRow
            key={run.run_id}
            className="cursor-pointer hover:bg-muted/50"
            onClick={() => onRowClick(run.run_id)}
          >
            <TableCell className="font-mono text-xs text-muted-foreground">
              {run.run_id}
            </TableCell>
            <TableCell className="max-w-[300px] truncate text-sm">
              {run.query}
            </TableCell>
            <TableCell className="text-xs text-muted-foreground">
              {run.model}
            </TableCell>
            <TableCell>
              <Badge
                variant={run.succeeded ? "default" : "destructive"}
                className="text-xs"
              >
                {run.succeeded ? "Success" : "Failed"}
              </Badge>
            </TableCell>
            <TableCell className="text-right text-sm">
              {run.step_count}
            </TableCell>
            <TableCell className="text-right text-xs text-muted-foreground">
              {run.duration_ms ? `${run.duration_ms.toFixed(0)}ms` : "—"}
            </TableCell>
            <TableCell className="text-right text-xs text-muted-foreground">
              {run.total_tokens}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

"use client";

import type { BenchmarkResult } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface ResultGridProps {
  /** List of benchmark results to display. */
  results: BenchmarkResult[];
}

/**
 * Grid showing benchmark results with pass/fail status and score breakdowns.
 */
export function ResultGrid({ results }: ResultGridProps) {
  if (results.length === 0) {
    return (
      <p className="py-10 text-center text-sm text-muted-foreground">
        No results yet.
      </p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-24">Status</TableHead>
          <TableHead>Case ID</TableHead>
          <TableHead className="w-20 text-right">Score</TableHead>
          <TableHead className="w-20 text-center">Answer</TableHead>
          <TableHead className="w-20 text-center">Tools</TableHead>
          <TableHead>Failures</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {results.map((r, i) => (
          <TableRow key={i}>
            <TableCell>
              <Badge
                variant={r.passed ? "default" : "destructive"}
                className="text-xs"
              >
                {r.passed ? "PASS" : "FAIL"}
              </Badge>
            </TableCell>
            <TableCell className="font-mono text-xs">{r.case_id}</TableCell>
            <TableCell className="text-right text-sm">
              {r.score.toFixed(2)}
            </TableCell>
            <TableCell className="text-center">
              {r.answer_correct ? (
                <span className="text-[#81c784]">Yes</span>
              ) : (
                <span className="text-[#ef5350]">No</span>
              )}
            </TableCell>
            <TableCell className="text-center">
              {r.tools_correct ? (
                <span className="text-[#81c784]">Yes</span>
              ) : (
                <span className="text-[#ef5350]">No</span>
              )}
            </TableCell>
            <TableCell>
              <div className="flex flex-wrap gap-1">
                {r.failures.map((f, j) => (
                  <Badge key={j} variant="destructive" className="text-xs">
                    {f}
                  </Badge>
                ))}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

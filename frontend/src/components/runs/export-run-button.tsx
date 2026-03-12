"use client";

import { Button } from "@/components/ui/button";
import { getExportUrl } from "@/lib/api";

interface ExportRunButtonProps {
  /** The run ID to export. */
  runId: string;
}

/**
 * Export button for downloading a run's steps as CSV.
 */
export function ExportRunButton({ runId }: ExportRunButtonProps) {
  function handleDownload() {
    const url = getExportUrl("run-csv", runId);
    window.open(url, "_blank");
  }

  return (
    <Button variant="outline" size="sm" onClick={handleDownload}>
      Export CSV
    </Button>
  );
}

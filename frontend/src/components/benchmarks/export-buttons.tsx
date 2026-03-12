"use client";

import { Button } from "@/components/ui/button";
import { getExportUrl } from "@/lib/api";

interface ExportButtonsProps {
  /** The benchmark suite ID to export. */
  suiteId: string;
}

/**
 * Export buttons for downloading benchmark suite results as CSV or PDF.
 */
export function ExportButtons({ suiteId }: ExportButtonsProps) {
  function handleDownload(format: "benchmark-csv" | "benchmark-pdf") {
    const url = getExportUrl(format, suiteId);
    window.open(url, "_blank");
  }

  return (
    <div className="flex gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleDownload("benchmark-csv")}
      >
        Export CSV
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleDownload("benchmark-pdf")}
      >
        Export PDF
      </Button>
    </div>
  );
}

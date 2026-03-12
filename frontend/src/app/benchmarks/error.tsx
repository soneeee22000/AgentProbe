"use client";

import { useEffect } from "react";

/**
 * Error boundary for the /benchmarks route.
 * Displays a recovery UI when the benchmarks section fails to load.
 */
export default function BenchmarksError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}): React.JSX.Element {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="max-w-md text-center">
        <h2 className="mb-4 text-2xl font-bold text-[#c9d4e0]">
          Failed to load benchmarks
        </h2>
        <p className="mb-6 text-sm text-[#c9d4e0]/60">{error.message}</p>
        <button
          onClick={reset}
          className="rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          Try again
        </button>
      </div>
    </div>
  );
}

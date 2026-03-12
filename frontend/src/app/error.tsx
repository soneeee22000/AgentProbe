"use client";

import { useEffect } from "react";

/**
 * Root error boundary for the application.
 * Catches unhandled errors at the top level and displays a recovery UI.
 */
export default function RootError({
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
    <div className="flex min-h-screen items-center justify-center bg-[#0a0c0f] px-4">
      <div className="max-w-md text-center">
        <h2 className="mb-4 text-2xl font-bold text-[#c9d4e0]">
          Something went wrong
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

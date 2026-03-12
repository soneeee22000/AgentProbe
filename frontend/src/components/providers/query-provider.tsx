"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

const STALE_TIME_MS = 30_000;

interface QueryProviderProps {
  children: React.ReactNode;
}

/**
 * Provides a React Query client to the application tree.
 * Configured with a 30-second stale time for cached queries.
 */
export function QueryProvider({ children }: QueryProviderProps) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: STALE_TIME_MS,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

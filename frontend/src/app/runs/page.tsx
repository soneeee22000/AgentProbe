"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { RunTable } from "@/components/runs/run-table";
import { RunFilters } from "@/components/runs/run-filters";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchRuns } from "@/lib/api";

const PAGE_SIZES = [10, 25, 50];

/**
 * Run History page — browse, filter, and inspect past agent runs.
 */
export default function RunsPage() {
  const router = useRouter();
  const [model, setModel] = useState("all");
  const [status, setStatus] = useState("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["runs", model, status, page, pageSize],
    queryFn: () =>
      fetchRuns({
        limit: pageSize,
        offset: page * pageSize,
        model: model === "all" ? undefined : model,
        status: status === "all" ? undefined : status,
      }),
    refetchInterval: 10000,
  });

  const runs = data?.runs ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / pageSize);

  const filteredRuns = search
    ? runs.filter((r) => r.query.toLowerCase().includes(search.toLowerCase()))
    : runs;

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex flex-1 flex-col overflow-hidden p-6">
          {/* Header row */}
          <div className="mb-4 flex items-center justify-between">
            <h1 className="text-xl font-semibold text-foreground">
              Run History
            </h1>
            <RunFilters
              model={model}
              status={status}
              search={search}
              onModelChange={(v) => {
                setModel(v);
                setPage(0);
              }}
              onStatusChange={(v) => {
                setStatus(v);
                setPage(0);
              }}
              onSearchChange={setSearch}
            />
          </div>

          {/* Content */}
          <div className="flex-1 overflow-auto rounded-md border border-border bg-card">
            {isLoading ? (
              <div className="space-y-2 p-4">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </div>
            ) : isError ? (
              <div className="flex flex-col items-center justify-center py-20">
                <p className="text-sm text-destructive">
                  Failed to load runs. Is the backend running?
                </p>
              </div>
            ) : filteredRuns.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20">
                <p className="text-lg font-medium text-foreground">
                  No runs yet
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Run your first query in the playground.
                </p>
                <Link href="/">
                  <Button className="mt-4" variant="default" size="sm">
                    Go to Playground
                  </Button>
                </Link>
              </div>
            ) : (
              <RunTable
                runs={filteredRuns}
                onRowClick={(id) => router.push(`/runs/${id}`)}
              />
            )}
          </div>

          {/* Pagination */}
          {total > 0 && (
            <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
              <span>
                Showing {page * pageSize + 1}–
                {Math.min((page + 1) * pageSize, total)} of {total} runs
              </span>
              <div className="flex items-center gap-2">
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setPage(0);
                  }}
                  className="rounded border border-border bg-card px-2 py-1 text-xs"
                >
                  {PAGE_SIZES.map((s) => (
                    <option key={s} value={s}>
                      {s} / page
                    </option>
                  ))}
                </select>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 0}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Prev
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

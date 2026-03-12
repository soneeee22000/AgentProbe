"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { CaseBrowser } from "@/components/benchmarks/case-browser";
import { SuiteRunner } from "@/components/benchmarks/suite-runner";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchSuites } from "@/lib/api";

type Tab = "cases" | "suites";

/**
 * Benchmark Dashboard — browse test cases and run/view benchmark suites.
 */
export default function BenchmarksPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>("cases");

  const { data: suitesData, isLoading: suitesLoading } = useQuery({
    queryKey: ["benchmark-suites"],
    queryFn: fetchSuites,
    refetchInterval: 5000,
  });

  const suites = suitesData?.suites ?? [];

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex flex-1 flex-col overflow-hidden p-6">
          <h1 className="mb-4 text-xl font-semibold text-foreground">
            Benchmarks
          </h1>

          {/* Tabs */}
          <div className="mb-4 flex gap-1 border-b border-border">
            {(["cases", "suites"] as Tab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === tab
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                {tab === "cases" ? "Cases" : "Suites"}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-auto">
            {activeTab === "cases" ? (
              <CaseBrowser />
            ) : (
              <div className="space-y-6">
                {/* Suite runner */}
                <div className="rounded-md border border-border bg-card p-4">
                  <h2 className="mb-3 text-sm font-medium text-foreground">
                    Run New Suite
                  </h2>
                  <SuiteRunner />
                </div>

                {/* Past suites */}
                <div>
                  <h2 className="mb-3 text-sm font-medium text-foreground">
                    Past Suites
                  </h2>
                  {suitesLoading ? (
                    <div className="space-y-2">
                      {Array.from({ length: 3 }).map((_, i) => (
                        <Skeleton key={i} className="h-16 w-full" />
                      ))}
                    </div>
                  ) : suites.length === 0 ? (
                    <p className="py-6 text-center text-sm text-muted-foreground">
                      No suites run yet. Configure and run your first suite
                      above.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {suites.map((s) => (
                        <div
                          key={s.id}
                          onClick={() => router.push(`/benchmarks/${s.id}`)}
                          className="flex cursor-pointer items-center justify-between rounded-md border border-border bg-card p-3 transition-colors hover:bg-muted/50"
                        >
                          <div className="flex items-center gap-3">
                            <span className="font-mono text-xs text-muted-foreground">
                              {s.id}
                            </span>
                            <span className="text-sm">{s.model_id}</span>
                            <Badge
                              variant={
                                s.status === "completed"
                                  ? "default"
                                  : "secondary"
                              }
                              className="text-xs"
                            >
                              {s.status}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span>{s.total_cases} cases</span>
                            <span>
                              {(s.success_rate * 100).toFixed(1)}% pass
                            </span>
                            <span>{s.avg_steps.toFixed(1)} avg steps</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchBenchmarkCases, type BenchmarkCase } from "@/lib/api";

const CATEGORIES = [
  { value: "", label: "All" },
  { value: "math", label: "Math" },
  { value: "search", label: "Search" },
  { value: "reasoning", label: "Reasoning" },
  { value: "multi_tool", label: "Multi-Tool" },
  { value: "edge_cases", label: "Edge Cases" },
];

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: "bg-[#81c784]/20 text-[#81c784]",
  medium: "bg-[#ffb74d]/20 text-[#ffb74d]",
  hard: "bg-[#ef5350]/20 text-[#ef5350]",
};

/**
 * Browse and filter benchmark test cases by category and difficulty.
 * Displays case cards with query, expected answer (toggleable), and expected tools.
 */
export function CaseBrowser() {
  const [category, setCategory] = useState("");
  const [showAnswers, setShowAnswers] = useState<Set<string>>(new Set());

  const { data: cases, isLoading } = useQuery({
    queryKey: ["benchmark-cases", category],
    queryFn: () =>
      fetchBenchmarkCases({
        category: category || undefined,
      }),
  });

  const toggleAnswer = (caseId: string) => {
    setShowAnswers((prev) => {
      const next = new Set(prev);
      if (next.has(caseId)) {
        next.delete(caseId);
      } else {
        next.add(caseId);
      }
      return next;
    });
  };

  return (
    <div>
      {/* Category tabs */}
      <div className="mb-4 flex gap-1">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.value}
            onClick={() => setCategory(cat.value)}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              category === cat.value
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Cases grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      ) : !cases || cases.length === 0 ? (
        <p className="py-10 text-center text-sm text-muted-foreground">
          No benchmark cases found. Seed the database first.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {cases.map((c) => (
            <CaseCard
              key={c.id}
              benchmarkCase={c}
              showAnswer={showAnswers.has(c.id)}
              onToggleAnswer={() => toggleAnswer(c.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface CaseCardProps {
  /** The benchmark case to display. */
  benchmarkCase: BenchmarkCase;
  /** Whether to show the expected answer. */
  showAnswer: boolean;
  /** Toggle answer visibility. */
  onToggleAnswer: () => void;
}

/**
 * Individual benchmark case card.
 */
function CaseCard({
  benchmarkCase: c,
  showAnswer,
  onToggleAnswer,
}: CaseCardProps) {
  return (
    <Card className="border-border">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <span className="font-mono text-xs text-muted-foreground">
            {c.id}
          </span>
          <Badge
            className={`text-xs ${DIFFICULTY_COLORS[c.difficulty] ?? ""}`}
            variant="outline"
          >
            {c.difficulty}
          </Badge>
        </div>
        <CardTitle className="text-sm font-normal leading-snug">
          {c.query || "(empty query)"}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 pt-0">
        {/* Expected tools */}
        {c.expected_tools.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {c.expected_tools.map((t) => (
              <Badge key={t} variant="secondary" className="text-xs">
                {t}
              </Badge>
            ))}
          </div>
        )}

        {/* Answer toggle */}
        <button
          onClick={onToggleAnswer}
          className="text-xs text-primary hover:underline"
        >
          {showAnswer ? "Hide answer" : "Show answer"}
        </button>
        {showAnswer && (
          <p className="rounded bg-muted p-2 text-xs text-foreground">
            {c.expected_answer}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

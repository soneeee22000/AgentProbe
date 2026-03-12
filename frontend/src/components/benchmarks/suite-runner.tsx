"use client";

import { useState, useCallback } from "react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { startBenchmarkSuite, type SuiteProgressEvent } from "@/lib/api";

const MODELS = [
  { value: "llama-3.1-8b-instant", label: "Llama 3.1 8B Instant" },
  { value: "llama-3.1-70b-versatile", label: "Llama 3.1 70B Versatile" },
  { value: "mixtral-8x7b-32768", label: "Mixtral 8x7B" },
  { value: "gemma2-9b-it", label: "Gemma 2 9B IT" },
];

const PROVIDERS = [
  { value: "groq", label: "Groq" },
  { value: "ollama", label: "Ollama" },
];

const CATEGORIES = [
  { value: "", label: "All Categories" },
  { value: "math", label: "Math" },
  { value: "search", label: "Search" },
  { value: "reasoning", label: "Reasoning" },
  { value: "multi_tool", label: "Multi-Tool" },
  { value: "edge_cases", label: "Edge Cases" },
];

interface CaseResult {
  caseId: string;
  passed: boolean;
  score: number;
  answerCorrect: boolean;
  toolsCorrect: boolean;
  query: string;
}

/**
 * Suite runner component — configure and run a benchmark suite with live progress.
 */
export function SuiteRunner() {
  const [model, setModel] = useState("llama-3.1-8b-instant");
  const [provider, setProvider] = useState("groq");
  const [category, setCategory] = useState("");
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [totalCases, setTotalCases] = useState(0);
  const [results, setResults] = useState<CaseResult[]>([]);
  const [suiteId, setSuiteId] = useState<string | null>(null);
  const [summary, setSummary] = useState<SuiteProgressEvent | null>(null);
  const [currentQuery, setCurrentQuery] = useState("");

  const handleRun = useCallback(async () => {
    setRunning(true);
    setProgress(0);
    setResults([]);
    setSuiteId(null);
    setSummary(null);
    setCurrentQuery("");

    try {
      for await (const event of startBenchmarkSuite({
        model,
        provider,
        category: category || undefined,
      })) {
        switch (event.type) {
          case "suite_start":
            setSuiteId(event.suite_id ?? null);
            setTotalCases(event.total_cases ?? 0);
            break;
          case "case_start":
            setCurrentQuery(event.query ?? "");
            break;
          case "case_complete":
            setProgress((event.case_index ?? 0) + 1);
            setResults((prev) => [
              ...prev,
              {
                caseId: event.case_id ?? "",
                passed: event.passed ?? false,
                score: event.score ?? 0,
                answerCorrect: event.answer_correct ?? false,
                toolsCorrect: event.tools_correct ?? false,
                query: currentQuery,
              },
            ]);
            break;
          case "suite_complete":
            setSummary(event);
            break;
        }
      }
    } finally {
      setRunning(false);
    }
  }, [model, provider, category, currentQuery]);

  const passedCount = results.filter((r) => r.passed).length;
  const progressPercent = totalCases > 0 ? (progress / totalCases) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-end gap-3">
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">
            Provider
          </label>
          <Select value={provider} onValueChange={(v) => v && setProvider(v)}>
            <SelectTrigger size="sm" className="w-28 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>Provider</SelectLabel>
                {PROVIDERS.map((p) => (
                  <SelectItem key={p.value} value={p.value}>
                    {p.label}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>

        <div>
          <label className="mb-1 block text-xs text-muted-foreground">
            Model
          </label>
          <Select value={model} onValueChange={(v) => v && setModel(v)}>
            <SelectTrigger size="sm" className="w-52 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>Model</SelectLabel>
                {MODELS.map((m) => (
                  <SelectItem key={m.value} value={m.value}>
                    {m.label}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>

        <div>
          <label className="mb-1 block text-xs text-muted-foreground">
            Category
          </label>
          <Select value={category} onValueChange={(v) => setCategory(v ?? "")}>
            <SelectTrigger size="sm" className="w-40 text-xs">
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>Category</SelectLabel>
                {CATEGORIES.map((c) => (
                  <SelectItem key={c.value} value={c.value}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>

        <Button onClick={handleRun} disabled={running} size="sm">
          {running ? "Running..." : "Run Suite"}
        </Button>
      </div>

      {/* Progress */}
      {(running || results.length > 0) && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              {progress} / {totalCases} cases
            </span>
            <span>
              {passedCount} passed, {progress - passedCount} failed
            </span>
          </div>
          <Progress value={progressPercent} className="h-2" />
          {running && currentQuery && (
            <p className="truncate text-xs text-muted-foreground">
              Running: {currentQuery}
            </p>
          )}
        </div>
      )}

      {/* Summary */}
      {summary && (
        <Card className="border-primary/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Suite Complete</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground text-xs">Success Rate</p>
                <p className="text-lg font-semibold">
                  {((summary.success_rate ?? 0) * 100).toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs">Avg Steps</p>
                <p className="text-lg font-semibold">
                  {summary.avg_steps?.toFixed(1)}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs">Passed</p>
                <p className="text-lg font-semibold text-[#81c784]">
                  {passedCount}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs">Failed</p>
                <p className="text-lg font-semibold text-[#ef5350]">
                  {totalCases - passedCount}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results feed */}
      {results.length > 0 && (
        <div className="max-h-64 space-y-1 overflow-auto">
          {results.map((r, i) => (
            <div
              key={i}
              className="flex items-center gap-2 rounded px-3 py-1.5 text-xs"
            >
              <Badge
                variant={r.passed ? "default" : "destructive"}
                className="w-12 justify-center text-xs"
              >
                {r.passed ? "PASS" : "FAIL"}
              </Badge>
              <span className="font-mono text-muted-foreground">
                {r.caseId}
              </span>
              <span className="text-muted-foreground">
                score: {r.score.toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AgentStep {
  step_type:
    | "thought"
    | "action"
    | "observation"
    | "final_answer"
    | "error"
    | "system"
    | "done";
  content: string;
  step_index: number;
  timestamp: number;
  tool_name?: string;
  tool_args?: string;
  failure_type: string;
  token_count?: number;
  latency_ms?: number;
}

export interface RunSummary {
  run_id: string;
  query: string;
  model: string;
  provider: string;
  succeeded: boolean;
  status: string;
  step_count: number;
  total_tokens: number;
  duration_ms?: number;
  failures: string[];
  final_answer?: string;
}

export interface RunDetail extends RunSummary {
  steps: AgentStep[];
}

export interface RunListResponse {
  runs: RunSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface ToolInfo {
  name: string;
  description: string;
  args_schema: string;
}

/* ---------- Provider types ---------- */

export interface ProviderModel {
  id: string;
  name: string;
}

export interface ProviderInfo {
  name: string;
  display_name: string;
  available: boolean;
  models: ProviderModel[];
}

async function apiFetch(url: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(detail || `Request failed: ${res.status}`);
  }
  return res;
}

export async function fetchProviders(): Promise<ProviderInfo[]> {
  const res = await apiFetch(`${API_BASE}/api/v1/providers`);
  return res.json();
}

export async function fetchTools(): Promise<ToolInfo[]> {
  const res = await apiFetch(`${API_BASE}/api/v1/tools`);
  const data = await res.json();
  return data.tools;
}

export async function fetchRuns(params?: {
  limit?: number;
  offset?: number;
  model?: string;
  status?: string;
}): Promise<RunListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  if (params?.model) searchParams.set("model", params.model);
  if (params?.status) searchParams.set("status", params.status);
  const res = await apiFetch(`${API_BASE}/api/v1/runs?${searchParams}`);
  return res.json();
}

export async function fetchRun(runId: string): Promise<RunDetail> {
  const res = await fetch(`${API_BASE}/api/v1/runs/${runId}`);
  if (!res.ok) throw new Error(`Run ${runId} not found`);
  return res.json();
}

export async function deleteRun(runId: string): Promise<void> {
  await fetch(`${API_BASE}/api/v1/runs/${runId}`, { method: "DELETE" });
}

/* ---------- Benchmark types ---------- */

export interface BenchmarkCase {
  id: string;
  query: string;
  category: string;
  difficulty: string;
  expected_answer: string;
  expected_tools: string[];
  is_builtin: boolean;
}

export interface BenchmarkResult {
  suite_id: string;
  case_id: string;
  run_id: string;
  passed: boolean;
  score: number;
  answer_correct: boolean;
  tools_correct: boolean;
  failures: string[];
}

export interface BenchmarkSuite {
  id: string;
  model_id: string;
  provider: string;
  status: string;
  total_cases: number;
  success_rate: number;
  avg_steps: number;
  failure_summary: Record<string, number>;
  results: BenchmarkResult[];
}

export interface FailureAnalytics {
  total_runs: number;
  failed_runs: number;
  failure_rate: number;
  by_type: Record<string, number>;
  by_model: Record<string, Record<string, number>>;
}

export interface ModelAnalytics {
  models: Record<
    string,
    {
      total_runs: number;
      successes: number;
      success_rate: number;
      avg_duration_ms: number | null;
      avg_tokens: number | null;
      avg_steps: number | null;
    }
  >;
}

export interface SuiteProgressEvent {
  type: string;
  suite_id?: string;
  total_cases?: number;
  case_index?: number;
  case_id?: string;
  query?: string;
  category?: string;
  passed?: boolean;
  score?: number;
  answer_correct?: boolean;
  tools_correct?: boolean;
  run_id?: string;
  step_count?: number;
  model?: string;
  provider?: string;
  success_rate?: number;
  avg_steps?: number;
  failure_summary?: Record<string, number>;
  message?: string;
}

/* ---------- Custom Tools API ---------- */

export interface CustomToolInfo {
  id: string;
  name: string;
  description: string;
  args_schema: string;
  tool_type: string;
  config: Record<string, unknown>;
}

export async function fetchCustomTools(): Promise<CustomToolInfo[]> {
  const res = await apiFetch(`${API_BASE}/api/v1/tools/custom`);
  return res.json();
}

export async function createCustomTool(tool: {
  name: string;
  description: string;
  args_schema?: string;
  tool_type: string;
  config: Record<string, unknown>;
}): Promise<CustomToolInfo> {
  const res = await fetch(`${API_BASE}/api/v1/tools/custom`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(tool),
  });
  if (!res.ok) throw new Error("Failed to create custom tool");
  return res.json();
}

export async function deleteCustomTool(toolId: string): Promise<void> {
  await fetch(`${API_BASE}/api/v1/tools/custom/${toolId}`, {
    method: "DELETE",
  });
}

/* ---------- Prompt Templates API ---------- */

export interface PromptTemplate {
  id: string;
  name: string;
  system_prompt: string;
  is_default: boolean;
}

export async function fetchPromptTemplates(): Promise<PromptTemplate[]> {
  const res = await apiFetch(`${API_BASE}/api/v1/prompts`);
  return res.json();
}

export async function createPromptTemplate(template: {
  name: string;
  system_prompt: string;
  is_default?: boolean;
}): Promise<PromptTemplate> {
  const res = await fetch(`${API_BASE}/api/v1/prompts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(template),
  });
  if (!res.ok) throw new Error("Failed to create prompt template");
  return res.json();
}

export async function updatePromptTemplate(
  id: string,
  template: { name?: string; system_prompt?: string; is_default?: boolean },
): Promise<PromptTemplate> {
  const res = await fetch(`${API_BASE}/api/v1/prompts/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(template),
  });
  if (!res.ok) throw new Error("Failed to update prompt template");
  return res.json();
}

export async function deletePromptTemplate(id: string): Promise<void> {
  await fetch(`${API_BASE}/api/v1/prompts/${id}`, { method: "DELETE" });
}

/* ---------- Export helpers ---------- */

export function getExportUrl(
  type: "benchmark-csv" | "benchmark-pdf" | "run-csv",
  id: string,
): string {
  if (type === "benchmark-csv") {
    return `${API_BASE}/api/v1/exports/benchmarks/${id}/csv`;
  }
  if (type === "benchmark-pdf") {
    return `${API_BASE}/api/v1/exports/benchmarks/${id}/pdf`;
  }
  return `${API_BASE}/api/v1/exports/runs/${id}/csv`;
}

/* ---------- Streaming helpers ---------- */

/**
 * Generic SSE stream reader. Yields parsed JSON objects from SSE data lines.
 */
async function* readSSEStream<T>(res: Response): AsyncGenerator<T> {
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const raw = line.slice(6).trim();
      if (!raw) continue;
      const parsed: Record<string, unknown> = JSON.parse(raw);
      if (parsed.type === "done" || parsed.step_type === "done") return;
      yield parsed as T;
    }
  }
}

export async function* streamRun(
  query: string,
  model: string,
  provider: string = "groq",
  maxSteps: number = 10,
): AsyncGenerator<AgentStep> {
  const res = await fetch(`${API_BASE}/api/v1/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, model, provider, max_steps: maxSteps }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "API error");
  }
  yield* readSSEStream<AgentStep>(res);
}

/* ---------- Run replay ---------- */

export async function* replayRun(runId: string): AsyncGenerator<AgentStep> {
  const res = await fetch(`${API_BASE}/api/v1/runs/${runId}/replay`);
  if (!res.ok) throw new Error(`Replay failed for run ${runId}`);
  yield* readSSEStream<AgentStep>(res);
}

/* ---------- Benchmark API ---------- */

export async function fetchBenchmarkCases(params?: {
  category?: string;
  difficulty?: string;
}): Promise<BenchmarkCase[]> {
  const searchParams = new URLSearchParams();
  if (params?.category) searchParams.set("category", params.category);
  if (params?.difficulty) searchParams.set("difficulty", params.difficulty);
  const res = await apiFetch(
    `${API_BASE}/api/v1/benchmarks/cases?${searchParams}`,
  );
  return res.json();
}

export async function fetchBenchmarkCase(
  caseId: string,
): Promise<BenchmarkCase> {
  const res = await fetch(`${API_BASE}/api/v1/benchmarks/cases/${caseId}`);
  if (!res.ok) throw new Error(`Case ${caseId} not found`);
  return res.json();
}

export async function* startBenchmarkSuite(params: {
  model: string;
  provider: string;
  category?: string;
  difficulty?: string;
}): AsyncGenerator<SuiteProgressEvent> {
  const res = await fetch(`${API_BASE}/api/v1/benchmarks/suites`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error("Failed to start benchmark suite");
  yield* readSSEStream<SuiteProgressEvent>(res);
}

export async function fetchSuites(): Promise<{ suites: BenchmarkSuite[] }> {
  const res = await apiFetch(`${API_BASE}/api/v1/benchmarks/suites`);
  return res.json();
}

export async function fetchSuiteDetail(
  suiteId: string,
): Promise<BenchmarkSuite> {
  const res = await fetch(`${API_BASE}/api/v1/benchmarks/suites/${suiteId}`);
  if (!res.ok) throw new Error(`Suite ${suiteId} not found`);
  return res.json();
}

/* ---------- Analytics API ---------- */

export async function fetchFailureAnalytics(): Promise<FailureAnalytics> {
  const res = await apiFetch(`${API_BASE}/api/v1/analytics/failures`);
  return res.json();
}

export async function fetchModelAnalytics(): Promise<ModelAnalytics> {
  const res = await apiFetch(`${API_BASE}/api/v1/analytics/models`);
  return res.json();
}

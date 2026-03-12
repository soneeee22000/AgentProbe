/**
 * Mock server fixture for deterministic E2E testing.
 *
 * Intercepts API requests and returns deterministic SSE responses
 * so tests don't require a running backend.
 */
import type { Page } from "@playwright/test";

/** Mock step data for SSE streaming. */
const MOCK_STEPS = [
  {
    step_type: "system",
    content:
      "Starting AgentProbe | Run: test-001 | Model: test | Provider: mock",
    step_index: 0,
    timestamp: Date.now() / 1000,
    failure_type: "none",
  },
  {
    step_type: "thought",
    content: "I need to calculate this.",
    step_index: 1,
    timestamp: Date.now() / 1000,
    failure_type: "none",
    token_count: 10,
    latency_ms: 50,
  },
  {
    step_type: "action",
    content: "calculator(2+2)",
    step_index: 1,
    timestamp: Date.now() / 1000,
    tool_name: "calculator",
    tool_args: "2+2",
    failure_type: "none",
  },
  {
    step_type: "observation",
    content: "4",
    step_index: 1,
    timestamp: Date.now() / 1000,
    failure_type: "none",
  },
  {
    step_type: "final_answer",
    content: "The answer is 4.",
    step_index: 2,
    timestamp: Date.now() / 1000,
    failure_type: "none",
  },
  { step_type: "done" },
];

/**
 * Set up route interception for mock SSE responses.
 */
export async function setupMockServer(page: Page): Promise<void> {
  // Mock run endpoint
  await page.route("**/api/v1/run", async (route) => {
    const sseBody = MOCK_STEPS.map(
      (step) => `data: ${JSON.stringify(step)}\n\n`,
    ).join("");

    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: sseBody,
    });
  });

  // Mock health endpoint
  await page.route("**/api/v1/health", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "ok",
        groq_key_set: true,
        tavily_key_set: true,
        providers: ["groq", "ollama"],
      }),
    });
  });

  // Mock tools endpoint
  await page.route("**/api/v1/tools", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        tools: [
          {
            name: "calculator",
            description: "Safe math evaluator",
            args_schema: "mathematical expression",
          },
          {
            name: "web_search",
            description: "Search the web",
            args_schema: "search query",
          },
        ],
      }),
    });
  });
}

# AgentProbe — Product Requirements Document

## Vision

AgentProbe is a **ReAct Agent Observatory** — a platform for observing, debugging, and benchmarking LLM agents. It provides deep visibility into agent reasoning loops, systematic failure classification, and cross-model performance comparison.

## Target Users

AI engineers evaluating agent reliability, debugging failure modes, and benchmarking LLM providers against structured test suites.

## Core Features (All Phases Complete)

### Playground

- Interactive ReAct agent execution with real-time SSE streaming
- Step-by-step trace viewer (Thought → Action → Observation → Final Answer)
- Dynamic model/provider selector with availability indicators
- Tool reference panel with custom tool support
- Prompt template selector for system prompt customization
- Run statistics (tokens, duration, steps)

### Run History

- Paginated run browser with model/status filters
- Run detail view with full step trace
- Run replay (SSE re-stream of persisted steps)
- CSV export for individual runs
- Run deletion

### Benchmarks

- 50+ built-in test cases across 5 categories (math, search, reasoning, multi-step, edge cases)
- EvalHarness: automated suite execution with real-time progress streaming
- ScoringEngine: composite scoring (40% answer + 20% tools + 20% efficiency + 20% reliability)
- Suite results with pass/fail grid, per-case scores, failure breakdown
- CSV and PDF export for benchmark suites

### Analytics

- Failure distribution pie chart (8 failure types)
- Model × Failure heatmap
- Cross-model performance comparison (success rate, tokens, duration, steps)
- KPI overview cards

### Model Compare

- Dual-model parallel execution on same query
- Side-by-side trace lanes with dynamic provider selection
- Comparative statistics bar

### Custom Tools

- User-defined HTTP and static tools via builder UI
- Custom tool executor (HTTP calls with args or static responses)
- CRUD management with per-user scoping

### Prompt Engineering

- Customizable system prompt templates
- Prompt editor with create/edit/delete
- Prompt selector in playground for A/B testing different prompts

### Agent Memory

- Persistent key-value memory across runs
- `save_memory` and `recall_memory` tools available to the agent
- Per-user scoped memory entries

### Authentication & Multi-Tenancy

- User registration and login (bcrypt + JWT)
- API key authentication (`ap_` prefixed keys)
- Feature-flagged auth middleware (`auth_enabled`)
- Per-user data scoping for runs, benchmarks, tools, prompts, memory

### Infrastructure

- Clean Architecture (domain → application → infrastructure)
- 5 LLM providers (Groq, Ollama, OpenAI, Anthropic, Google)
- 5+ tools (calculator, web_search, think, read_file, save_memory, recall_memory)
- 11 database tables, 30+ API endpoints
- PostgreSQL (prod) with asyncpg + Alembic migrations, SQLite (dev/test)
- Token-bucket rate limiting by IP
- Request validation middleware with security headers
- Docker Compose with PostgreSQL service
- GitHub Actions CI/CD (lint, test, build, E2E, deploy)
- Vercel (frontend) + Railway (backend) deployment
- Playwright E2E test suite with mock server fixtures

## Failure Taxonomy (Key Differentiator)

| Type                   | Description                         |
| ---------------------- | ----------------------------------- |
| `hallucinated_tool`    | LLM calls a tool that doesn't exist |
| `malformed_action`     | Can't parse Action/Action Input     |
| `tool_execution_error` | Tool throws an exception            |
| `max_steps_exceeded`   | Never reached Final Answer          |
| `context_overflow`     | Context approaching window limit    |
| `goal_drift`           | Final answer doesn't address query  |
| `repeated_action`      | Same tool+args called twice         |
| `empty_response`       | LLM returned nothing                |

## Scoring Engine

Composite score per run (0–100):

- **40% Answer Quality** — correctness of final answer vs expected
- **20% Tool Usage** — appropriate tool selection and execution
- **20% Efficiency** — steps taken relative to optimal
- **20% Reliability** — absence of failures during execution

## Non-Goals

- Not a production agent framework (use LangChain/LangGraph for that)
- Not a LangChain replacement — this is an observatory, not a runtime
- Not a general-purpose chatbot — focused on ReAct agent analysis

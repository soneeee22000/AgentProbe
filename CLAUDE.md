# AgentProbe — Project Instructions for Claude Code

## Project Overview

**AgentProbe** is a ReAct Agent Observatory for observing, debugging, and benchmarking LLM agents.
Built with Clean Architecture (Python/FastAPI backend) and Next.js 16 (TypeScript frontend).

## Directory Structure

```
backend/           # FastAPI backend (Clean Architecture)
  src/agentprobe/
    domain/        # Entities, enums, port interfaces (zero deps)
    application/   # Services (orchestrator, eval, auth, export), Pydantic schemas
    infrastructure/# Providers, persistence, tools, API routes, middleware
  tests/           # pytest: unit/, integration/, api/
  alembic/         # Database migrations (3 files: initial, users, phase7)

frontend/          # Next.js 16 + React 19 + TypeScript
  src/app/         # App Router pages (7 routes)
  src/components/  # UI components (playground, analytics, benchmarks, compare, tools, prompts, runs)
  src/lib/         # API client, SSE streaming helpers
  src/store/       # Zustand stores
  e2e/             # Playwright E2E tests
```

## Build / Test / Lint Commands

### Backend

```bash
cd backend
ruff check src/ tests/           # Lint
ruff format src/ tests/          # Format
mypy src/                        # Type check
pytest                           # Run all tests (aiosqlite in-memory)
pytest --cov=src/agentprobe      # With coverage
alembic upgrade head             # Run migrations (PostgreSQL)
```

### Frontend

```bash
cd frontend
npm run dev                      # Dev server (port 3000)
npm run build                    # Production build
npm run lint                     # ESLint
npm run e2e                      # Playwright E2E tests
```

## Code Conventions

- **Backend layers:** Domain (no deps) -> Application (business logic) -> Infrastructure (external)
- **Frontend state:** Zustand for client state, TanStack Query for server state
- **File naming:** kebab-case for frontend components, snake_case for backend modules
- **Testing:** pytest + aiosqlite in-memory for backend, Playwright for frontend E2E
- **Streaming:** SSE via `readSSEStream<T>()` in frontend, `AsyncGenerator` in backend
- **DI:** `@lru_cache` singletons in `dependencies.py`
- **Auth:** Feature-flagged via `AUTH_ENABLED` env var. When off, all routes are public.

## Key Patterns

- ReAct loop in `application/services/orchestrator.py`
- Provider interface: `domain/ports/llm_provider.py` -> `ILLMProvider`
- Repository pattern: `domain/ports/run_repository.py` -> `IRunRepository`
- Tool dispatch: `domain/ports/tool_registry.py` -> `IToolRegistry`
- Auth: `application/services/auth.py` -> `AuthService` (bcrypt + JWT)
- Export: `application/services/exporter.py` -> `ExportService` (CSV + PDF)

## LLM Providers (5)

- **Groq** — AsyncGroq client, 4 models
- **Ollama** — httpx async, local inference
- **OpenAI** — AsyncOpenAI client, gpt-4o / gpt-4o-mini
- **Anthropic** — AsyncAnthropic, system prompt as separate param
- **Google** — google-genai SDK, Gemini models

## Database

- 9 tables: runs, steps, failures, benchmark_cases, benchmark_suites, benchmark_results, users, api_keys, custom_tools, prompt_templates, memory_entries
- SQLite for dev/test (auto-created), PostgreSQL for production (Alembic migrations)

## Middleware Stack (in order)

1. CORS (configured origins)
2. Rate Limiter (token bucket by IP, configurable RPM)
3. Request Validator (body size limit, security headers)
4. Auth (JWT + API key, feature-flagged)

## Environment

- `.env` at `backend/` root with API keys
- `DATABASE_URL` — defaults to SQLite, use `postgresql+asyncpg://` in production
- `AUTH_ENABLED=false` — set to `true` to require authentication
- `RATE_LIMIT_RPM=60` — requests per minute per IP

# AgentProbe

**A from-scratch ReAct Agent Observatory** — observe, debug, and benchmark LLM agents with a built-in failure taxonomy, cross-model comparison, and production-grade evaluation harness.

[![CI](https://github.com/pyaesone/agentprobe/actions/workflows/ci.yml/badge.svg)](https://github.com/pyaesone/agentprobe/actions)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776ab.svg)
![TypeScript](https://img.shields.io/badge/typescript-strict-3178c6.svg)
![Next.js 16](https://img.shields.io/badge/next.js-16-000000.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)

---

## Why This Exists

Most "AI agent" demos are thin wrappers around LangChain. **AgentProbe builds the entire ReAct loop from scratch** — the parser, the tool dispatch, the failure detection, the streaming — so every layer is transparent and observable.

The **failure taxonomy** is the differentiator: every run is annotated with _exactly which failure modes occurred, at which step, and why._ This transforms agent debugging from "it didn't work" into quantified, actionable diagnostics.

---

## Features

| Feature                      | Description                                                                                             |
| ---------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Real-time Playground**     | Type a query, watch the agent reason step-by-step via SSE streaming                                     |
| **8-Type Failure Taxonomy**  | Automatic classification: hallucinated tools, malformed actions, context overflow, goal drift, and more |
| **Multi-Model Benchmarking** | 50+ test cases across 5 categories with composite scoring (answer + tools + efficiency + reliability)   |
| **Cross-Model Compare**      | Side-by-side dual-trace execution on the same query                                                     |
| **5 LLM Providers**          | Groq, Ollama, OpenAI, Anthropic, Google — with dynamic availability detection                           |
| **Analytics Dashboard**      | Failure distributions, model performance heatmaps, KPI overview cards                                   |
| **Custom Tools**             | Build HTTP or static tools via the UI — agent uses them in real-time                                    |
| **Prompt Engineering**       | Create, save, and A/B test custom system prompts                                                        |
| **Agent Memory**             | Persistent key-value memory across runs via save/recall tools                                           |
| **Auth System**              | JWT + API key authentication with per-user data scoping                                                 |
| **Export**                   | CSV and PDF export for benchmark results and run traces                                                 |

---

## Architecture

```mermaid
graph TB
    subgraph Frontend["Next.js 16 Frontend"]
        P[Playground]
        R[Run History]
        B[Benchmarks]
        A[Analytics]
        C[Model Compare]
        PR[Prompts]
    end

    subgraph Backend["FastAPI Backend"]
        subgraph Domain["Domain Layer"]
            E[Entities]
            PO[Ports / Interfaces]
        end
        subgraph Application["Application Layer"]
            O[AgentOrchestrator]
            EH[EvalHarness]
            AN[AnalyticsService]
            SE[ScoringEngine]
            AU[AuthService]
            EX[ExportService]
        end
        subgraph Infrastructure["Infrastructure Layer"]
            PRV[LLM Providers]
            DB[(PostgreSQL)]
            T[Tool Registry]
            MW[Middleware]
        end
    end

    Frontend -->|SSE / REST| Backend
    O --> PRV
    O --> T
    O --> DB
    EH --> O
    AN --> DB
    AU --> DB

    style Frontend fill:#1a1a2e,stroke:#4fc3f7,color:#e0e0e0
    style Domain fill:#0d1b2a,stroke:#81c784,color:#e0e0e0
    style Application fill:#0d1b2a,stroke:#ffb74d,color:#e0e0e0
    style Infrastructure fill:#0d1b2a,stroke:#ef5350,color:#e0e0e0
```

### Clean Architecture Layers

```mermaid
graph LR
    D[Domain] -->|depends on nothing| D
    A[Application] -->|depends on| D
    I[Infrastructure] -->|depends on| A
    I -->|depends on| D

    style D fill:#1b5e20,stroke:#81c784,color:#fff
    style A fill:#e65100,stroke:#ffb74d,color:#fff
    style I fill:#b71c1c,stroke:#ef5350,color:#fff
```

- **Domain** — Entities (`AgentRun`, `AgentStep`, `User`, `CustomTool`, `MemoryEntry`), enums (`FailureType`, `StepType`), port interfaces (zero external dependencies)
- **Application** — `AgentOrchestrator` (ReAct loop), `EvalHarness`, `ScoringEngine`, `AnalyticsService`, `AuthService`, `ExportService`, Pydantic schemas
- **Infrastructure** — 5 LLM providers, SQLAlchemy persistence (9 tables), tool registry, FastAPI routes, middleware (rate limiter, auth, request validator)

---

## ReAct Agent Loop

```mermaid
flowchart TD
    Start([User Query]) --> SYS[Emit System Step]
    SYS --> LOOP{Step < Max?}
    LOOP -->|Yes| CTX{Context OK?}
    CTX -->|Overflow| ERR1[Context Overflow Error]
    CTX -->|OK| LLM[Call LLM Provider]
    LLM --> PARSE[Parse Output]
    PARSE -->|Final Answer| FINAL[Persist Run + Return]
    PARSE -->|Action| CHECK{Tool Exists?}
    CHECK -->|No| FAIL1[Hallucinated Tool]
    CHECK -->|Yes| DUP{Repeated?}
    DUP -->|Yes| FAIL2[Repeated Action]
    DUP -->|No| EXEC[Execute Tool]
    EXEC --> OBS[Observation]
    OBS --> LOOP
    PARSE -->|Malformed| FAIL3[Malformed Action]
    FAIL1 --> LOOP
    FAIL2 --> LOOP
    FAIL3 --> LOOP
    LOOP -->|No| TIMEOUT[Max Steps Exceeded]

    style Start fill:#4fc3f7,stroke:#4fc3f7,color:#000
    style FINAL fill:#81c784,stroke:#81c784,color:#000
    style FAIL1 fill:#ef5350,stroke:#ef5350,color:#fff
    style FAIL2 fill:#ef5350,stroke:#ef5350,color:#fff
    style FAIL3 fill:#ef5350,stroke:#ef5350,color:#fff
    style TIMEOUT fill:#ef5350,stroke:#ef5350,color:#fff
    style ERR1 fill:#ef5350,stroke:#ef5350,color:#fff
```

Every failure is recorded with its type, step index, and context — enabling the aggregate analytics that power the dashboard.

---

## Failure Taxonomy

The core differentiator. Every run is annotated with exactly which failure modes occurred:

```mermaid
mindmap
  root((Failure Types))
    Tool Failures
      hallucinated_tool
      tool_execution_error
    Parse Failures
      malformed_action
      empty_response
    Loop Failures
      max_steps_exceeded
      context_overflow
      repeated_action
    Quality Failures
      goal_drift
```

| Failure                | What Happened                      | How It's Detected               |
| ---------------------- | ---------------------------------- | ------------------------------- |
| `hallucinated_tool`    | LLM invented a tool name           | Tool name not in registry       |
| `malformed_action`     | Can't parse Action/Action Input    | Regex parse failure             |
| `tool_execution_error` | Tool threw an exception            | `[ERROR]` prefix in observation |
| `max_steps_exceeded`   | Agent never reached Final Answer   | Step counter >= limit           |
| `context_overflow`     | Context window approaching limit   | Character count check           |
| `repeated_action`      | Same tool + args called twice      | Dedup check on recent steps     |
| `empty_response`       | LLM returned nothing               | Empty string check              |
| `goal_drift`           | Final answer doesn't address query | Keyword overlap analysis        |

---

## Tech Stack

```mermaid
graph LR
    subgraph Frontend
        NX[Next.js 16]
        RE[React 19]
        TS[TypeScript 5]
        TW[Tailwind CSS 4]
        SH[shadcn/ui]
        ZU[Zustand]
        TQ[TanStack Query]
        RC[Recharts]
        PW[Playwright]
    end

    subgraph Backend
        FA[FastAPI]
        PY[Python 3.10+]
        SA[SQLAlchemy]
        AL[Alembic]
        PD[Pydantic v2]
    end

    subgraph Providers
        GR[Groq]
        OL[Ollama]
        OA[OpenAI]
        AN[Anthropic]
        GO[Google Gemini]
    end

    subgraph Data
        PG[(PostgreSQL)]
        SQ[(SQLite dev)]
    end

    subgraph DevOps
        DK[Docker Compose]
        GA[GitHub Actions]
        VE[Vercel]
        RW[Railway]
    end

    style Frontend fill:#1a1a2e,stroke:#4fc3f7,color:#e0e0e0
    style Backend fill:#1a1a2e,stroke:#81c784,color:#e0e0e0
    style Providers fill:#1a1a2e,stroke:#ffb74d,color:#e0e0e0
    style Data fill:#1a1a2e,stroke:#ce93d8,color:#e0e0e0
    style DevOps fill:#1a1a2e,stroke:#ef5350,color:#e0e0e0
```

---

## Quick Start

### Docker (recommended)

```bash
# Clone and configure
git clone https://github.com/pyaesone/agentprobe.git
cd agentprobe

# Set API keys
cat > .env << EOF
GROQ_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
EOF

# Launch full stack (PostgreSQL + Backend + Frontend)
docker-compose up --build

# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

<details>
<summary>Backend</summary>

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env    # Add your API keys
mkdir workspace
uvicorn main:app --reload --port 8000
```

</details>

<details>
<summary>Frontend</summary>

```bash
cd frontend
npm install
npm run dev              # http://localhost:3000
```

</details>

### API Keys

| Provider  | Free Tier | URL                           |
| --------- | --------- | ----------------------------- |
| Groq      | Yes       | https://console.groq.com      |
| Tavily    | Yes       | https://tavily.com            |
| Ollama    | Local     | https://ollama.com            |
| OpenAI    | Paid      | https://platform.openai.com   |
| Anthropic | Paid      | https://console.anthropic.com |
| Google    | Free      | https://aistudio.google.com   |

---

## API Reference

### Agent Execution

| Method | Endpoint      | Description                  |
| ------ | ------------- | ---------------------------- |
| `POST` | `/api/v1/run` | Start agent run (SSE stream) |

### Run Management

| Method   | Endpoint                   | Description                       |
| -------- | -------------------------- | --------------------------------- |
| `GET`    | `/api/v1/runs`             | List runs (paginated, filterable) |
| `GET`    | `/api/v1/runs/{id}`        | Run detail with full step trace   |
| `DELETE` | `/api/v1/runs/{id}`        | Delete a run                      |
| `GET`    | `/api/v1/runs/{id}/replay` | Replay run as SSE stream          |

### Benchmarking

| Method | Endpoint                         | Description                          |
| ------ | -------------------------------- | ------------------------------------ |
| `GET`  | `/api/v1/benchmarks/cases`       | List benchmark test cases            |
| `POST` | `/api/v1/benchmarks/cases`       | Create custom test case              |
| `POST` | `/api/v1/benchmarks/suites`      | Start benchmark suite (SSE progress) |
| `GET`  | `/api/v1/benchmarks/suites`      | List completed suites                |
| `GET`  | `/api/v1/benchmarks/suites/{id}` | Suite detail with per-case results   |

### Analytics & Providers

| Method | Endpoint                     | Description                       |
| ------ | ---------------------------- | --------------------------------- |
| `GET`  | `/api/v1/analytics/failures` | Failure type breakdown            |
| `GET`  | `/api/v1/analytics/models`   | Cross-model performance stats     |
| `GET`  | `/api/v1/providers`          | Available providers + models      |
| `GET`  | `/api/v1/tools`              | Built-in tool list                |
| `GET`  | `/api/v1/health`             | Health check with provider status |

### Custom Tools & Prompts

| Method   | Endpoint                    | Description            |
| -------- | --------------------------- | ---------------------- |
| `POST`   | `/api/v1/tools/custom`      | Create custom tool     |
| `GET`    | `/api/v1/tools/custom`      | List custom tools      |
| `DELETE` | `/api/v1/tools/custom/{id}` | Delete custom tool     |
| `POST`   | `/api/v1/prompts`           | Create prompt template |
| `GET`    | `/api/v1/prompts`           | List prompt templates  |
| `PUT`    | `/api/v1/prompts/{id}`      | Update prompt template |
| `DELETE` | `/api/v1/prompts/{id}`      | Delete prompt template |

### Auth & Export

| Method | Endpoint                              | Description             |
| ------ | ------------------------------------- | ----------------------- |
| `POST` | `/auth/register`                      | Register new user       |
| `POST` | `/auth/login`                         | Login (returns JWT)     |
| `POST` | `/auth/api-keys`                      | Generate API key        |
| `GET`  | `/auth/me`                            | Current user info       |
| `GET`  | `/api/v1/exports/runs/{id}/csv`       | Export run as CSV       |
| `GET`  | `/api/v1/exports/benchmarks/{id}/csv` | Export benchmark as CSV |
| `GET`  | `/api/v1/exports/benchmarks/{id}/pdf` | Export benchmark as PDF |

---

## Database Schema

```mermaid
erDiagram
    users ||--o{ api_keys : has
    users ||--o{ runs : owns
    users ||--o{ custom_tools : creates
    users ||--o{ prompt_templates : creates
    users ||--o{ memory_entries : stores
    runs ||--o{ steps : contains
    runs ||--o{ failures : records
    benchmark_suites ||--o{ benchmark_results : contains
    benchmark_cases ||--o{ benchmark_results : tested_by
    runs ||--o{ benchmark_results : produces

    users {
        string id PK
        string email UK
        string hashed_password
        datetime created_at
    }
    runs {
        string id PK
        string query
        string model_id
        string provider
        string status
        string final_answer
        int total_tokens
        float duration_ms
        bool succeeded
        string user_id FK
    }
    steps {
        int id PK
        string run_id FK
        int step_index
        string step_type
        string content
        string tool_name
        string failure_type
    }
    failures {
        int id PK
        string run_id FK
        int step_id FK
        string failure_type
        string context
    }
    benchmark_cases {
        string id PK
        string query
        string category
        string difficulty
    }
    benchmark_suites {
        string id PK
        string model_id
        string provider
        float success_rate
    }
    custom_tools {
        string id PK
        string user_id FK
        string name
        string tool_type
    }
    memory_entries {
        string id PK
        string user_id FK
        string key
        string value
    }
```

9 tables total. SQLite for local development, PostgreSQL for production. Alembic manages migrations.

---

## Project Structure

```
agentprobe/
├── backend/
│   ├── src/agentprobe/
│   │   ├── domain/                  # Zero-dependency core
│   │   │   ├── entities/            # AgentRun, Step, User, CustomTool, Memory, Prompt
│   │   │   └── ports/               # ILLMProvider, IRunRepository, IUserRepository, ...
│   │   ├── application/             # Business logic
│   │   │   ├── services/            # Orchestrator, EvalHarness, Auth, Analytics, Export
│   │   │   └── schemas/             # Pydantic v2 request/response models
│   │   └── infrastructure/          # External integrations
│   │       ├── api/                 # FastAPI app, routes (10 modules), middleware (3)
│   │       ├── providers/           # Groq, Ollama, OpenAI, Anthropic, Google
│   │       ├── persistence/         # SQLAlchemy ORM (9 tables), 4 repositories
│   │       └── tools/               # calculator, web_search, think, read_file, memory, custom
│   ├── tests/                       # 81+ tests (unit, integration, API)
│   ├── alembic/                     # 3 migration files
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── app/                     # 7 routes (/, /runs, /benchmarks, /analytics, /compare, /prompts, dynamic)
│   │   ├── components/              # 30+ components across 8 modules
│   │   ├── store/                   # Zustand (run-store, compare-store)
│   │   └── lib/                     # API client with SSE streaming
│   ├── e2e/                         # Playwright E2E tests (4 specs)
│   └── playwright.config.ts
│
├── .github/workflows/               # CI (lint, test, build, E2E) + Deploy
├── docker-compose.yml               # PostgreSQL + Backend + Frontend
├── CLAUDE.md                        # Project instructions
└── PRD.md                           # Product requirements
```

---

## Development

```bash
# Backend lint + test + type check
cd backend
ruff check src/ tests/
pytest --cov=src/agentprobe
mypy src/

# Frontend lint + build + E2E
cd frontend
npm run lint
npm run build
npm run e2e
```

---

## Scoring Engine

Benchmark cases are scored with a weighted composite:

```mermaid
pie title Composite Score Weights
    "Answer Correctness" : 40
    "Tool Usage" : 20
    "Efficiency" : 20
    "Reliability" : 20
```

- **Answer Correctness (40%)** — Keyword overlap between agent's answer and expected answer
- **Tool Usage (20%)** — Did the agent use the expected tools?
- **Efficiency (20%)** — Fewer steps = higher score
- **Reliability (20%)** — No failures = full score; each failure type deducts proportionally

---

## Roadmap

- [x] **Phase 1** — Clean Architecture, Groq + Ollama, SSE streaming, 6 tables
- [x] **Phase 2** — Benchmarking (50+ cases), analytics dashboard, composite scoring
- [x] **Phase 3** — Multi-model compare, Docker Compose, 81 tests
- [x] **Phase 4** — PostgreSQL + Alembic, rate limiting, request validation
- [x] **Phase 5** — OpenAI, Anthropic, Google providers + dynamic discovery
- [x] **Phase 6** — Auth (JWT + API keys), GitHub Actions CI/CD
- [x] **Phase 7** — Custom tools, prompt engineering UI, agent memory
- [x] **Phase 8** — Vercel + Railway deploy, Playwright E2E, CSV/PDF export

---

## License

MIT

# AgentProbe

A from-scratch ReAct agent with a built-in failure taxonomy and evaluation harness.

**Stack:** Groq (Llama 3) · FastAPI · SSE streaming · Vanilla JS

---

## Why This Exists

Anyone can wrap LangChain around an API and call it an agent.
This project builds the loop manually — so you understand what every framework is actually doing.

The failure analysis framework is the real differentiator:
every run is annotated with *exactly which failure modes occurred and why.*

---

## Architecture

```
User Query (frontend)
      │
      ▼ POST /api/run (SSE stream)
 FastAPI (main.py)
      │
      ▼
 ReAct Loop (agent/core.py)
      │
      ├── System prompt with tools schema
      ├── LLM call (Groq API, raw)
      ├── Output parser (regex → thought/action/answer)
      ├── Tool dispatcher (agent/tools.py)
      ├── Failure detector (per-step)
      └── Step logger (agent/logger.py)
             │
             ▼ SSE events → frontend
```

---

## Failure Taxonomy

| Failure | Description | Detection Method |
|---|---|---|
| `hallucinated_tool` | LLM calls a tool that doesn't exist | Tool name not in registry |
| `malformed_action` | Can't parse Action/Action Input | Regex match fails |
| `tool_execution_error` | Tool throws an exception | `[ERROR]` in observation |
| `max_steps_exceeded` | Never reached Final Answer | Step counter >= max |
| `context_overflow` | Context approaching window limit | Character count check |
| `repeated_action` | Same tool+args called twice | Dedup check on recent steps |
| `empty_response` | LLM returned nothing | Empty string check |

---

## Running Locally

```bash
# 1. Clone and navigate
cd agentprobe/backend

# 2. Create virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure keys
cp .env.example .env
# Edit .env with your GROQ_API_KEY

# 5. Create workspace dir
mkdir workspace

# 6. Start backend
uvicorn main:app --reload --port 8000

# 7. Open frontend
open ../frontend/index.html
```

Get a free Groq API key: https://console.groq.com
Get a free Tavily API key: https://tavily.com

---

## Tools

| Tool | Description |
|---|---|
| `calculator` | Safe math evaluator (whitelist-based, no exec exploits) |
| `web_search` | Tavily search optimized for LLM agents |
| `think` | Private scratchpad — externalizes chain-of-thought |
| `read_file` | Sandboxed file reader (path traversal protected) |

---

## What's Next (Week 2+)

- [ ] Benchmark dataset: 50 queries across 5 categories
- [ ] Eval harness: automated failure rate measurement
- [ ] Write-file tool + multi-turn memory
- [ ] Failure visualization dashboard
- [ ] Technical write-up: "Building an Agent That Fails Gracefully"

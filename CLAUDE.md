# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Supply Chain AI Agent System** — A multi-agent supermarket replenishment workflow built with **LangGraph**. The system orchestrates 8 specialist agents that move demand predictions through to purchase order execution, with human approval gates for high-risk orders.

The workflow: **Predict (demand) → Check Stock → Draft Order → Pick Supplier → Plan Delivery → Check Exceptions → Human Approval → Execute → Evaluate**

This is a **production-ready reference architecture** demonstrating:
- LangGraph state graphs with conditional routing
- Structured outputs from LLM calls
- Human-in-the-loop via `interrupt()` and `Command(resume=...)`
- Per-agent rationale capture (audit trail)
- Pluggable LLM providers (OpenRouter, Anthropic, OpenAI, mock)

## Core Architecture

### The State Machine (`app/state.py`)
All agent decisions flow through `SupplyChainState` — a TypedDict that accumulates structured outputs. Every agent produces:
- A **payload** (e.g., `DemandForecast`, `StockSignal`) with Pydantic validation
- A **Decision** record (agent name + summary + rationale for the audit trail)

The `decisions` field uses `operator.add` to grow the list; `exceptions` does the same. This ensures a complete audit trail at the end.

### The Graph (`app/graph.py`)
Built with `StateGraph` and routed by conditional edges:
1. **START** → `demand` → `inventory`
2. `inventory` branches: if stock needs reorder → `procurement` path, else → `evaluator` (skip ordering)
3. Ordering path (procurement → supplier → delivery → exception → human_approval → execute) runs only if reorder is needed
4. Both paths merge at `evaluator` → **END**

**Critical pattern:** `human_approval_node()` uses `interrupt()` to pause the graph. The approval is resumed from the API layer by calling `graph.invoke(Command(resume=...))` with the same `thread_id`.

### The Agent Pattern (`app/agents/*.py`)
Every agent follows this 4-step design:
1. **Deterministic proposal** — use tools/data to compute the "obvious" answer (e.g., mean sales × horizon = forecast)
2. **Fallback dict** — the proposal as a dict that satisfies the agent's Pydantic schema
3. **LLM decision** — call `get_client().decide(Schema, system, context, fallback)` to get LLM judgment + rationale
4. **Return decision** — emit both the schema instance and a Decision record for the audit trail

In **mock mode** (LLM_PROVIDER=mock), the LLM call is skipped; the fallback is returned verbatim. This makes the full graph runnable with zero credentials — ideal for CI and demos.

### LLM Abstraction (`app/llm.py`)
`LLMClient.decide()` wraps structured output for multiple providers:
- **openrouter** — OpenAI-compatible gateway; primes with fallback (broadest model compatibility)
- **anthropic** — native Anthropic API
- **openai** — native OpenAI API
- **mock** — no API call; returns the fallback proposal

Each agent in the graph runs independently; the LLM sees only its own context (demand forecast sees POS sales, supplier agent sees catalog, etc.). This isolation keeps prompts focused and deterministic fallbacks realistic.

### Configuration (`app/config.py`)
Environment-driven via `.env`:
- `LLM_PROVIDER` (openrouter | anthropic | openai | mock)
- `LLM_MODEL` (e.g., anthropic/claude-sonnet-4.5)
- `APPROVAL_QTY_THRESHOLD` (default 500 units)
- `APPROVAL_COST_THRESHOLD` (default $10,000)

Approval thresholds determine when `human_approval_node()` pauses the graph vs. auto-approves.

### The API (`app/main.py`)
Four endpoints:
- `GET /health` — liveness + provider info
- `GET /skus` — list known SKUs
- `POST /run` — kick off a graph run; returns interrupt struct if approval needed, or result if complete
- `POST /approve` — resume a paused run by thread_id with human decision

Each run gets a unique UUID `thread_id` for state isolation (via MemorySaver checkpointer).

## Development

### Install & Setup
```bash
# Clone and install
pip install -r requirements.txt
cp .env.example .env

# Run with mock LLM (no API keys needed)
echo "LLM_PROVIDER=mock" >> .env
python run_demo.py

# Run with OpenRouter (set API key in .env)
export OPENROUTER_API_KEY=sk-or-...
python run_demo.py
```

### Commands

| Task | Command |
|------|---------|
| Install dependencies | `pip install -r requirements.txt` |
| Run mock demo (all SKUs) | `python run_demo.py` |
| Run one SKU | `python run_demo.py SKU-MILK-1L` |
| Demo with auto-reject at approval | `AUTO_APPROVE=0 python run_demo.py` |
| Start API server | `uvicorn app.main:app --reload` |
| Run tests (requires mock provider) | `LLM_PROVIDER=mock pytest -v` |
| Run one test | `LLM_PROVIDER=mock pytest tests/test_graph.py::test_low_stock_triggers_order -v` |
| Lint (if adopted) | `ruff check app/ tests/` |

### Docker

```bash
# With mock LLM (zero credentials)
docker compose up --build

# With OpenRouter
LLM_PROVIDER=openrouter OPENROUTER_API_KEY=sk-or-... \
  LLM_MODEL=anthropic/claude-sonnet-4.5 docker compose up --build
```

API is at `http://localhost:8000`.

## Testing Strategy

Tests in `tests/test_graph.py` use **LLM_PROVIDER=mock** to eliminate API calls. Each test builds a fresh graph and invokes it with a unique thread_id.

**Key patterns:**
- Use `_run(sku, approved=True/False)` helper to run a full SKU end-to-end
- After `graph.invoke()`, check for `res.get("__interrupt__")` to detect approval pauses
- If interrupted, resume with `graph.invoke(Command(resume={...}), config)`
- Assert on specific fields in the structured outputs (e.g., `res["stock_signal"]["needs_reorder"]`)

Tests are organized by concern (Demand, Inventory, Supplier, etc.) with edge cases (empty SKU, unknown SKU, high-cost orders).

## Key Architectural Decisions

1. **Structured outputs (Pydantic)** — Every agent returns a validated schema, not free text. This ensures consistent audit trails and lets the graph reason about decisions downstream.

2. **Deterministic proposals + LLM review** — Agents compute a defensible proposal from tools, then ask the LLM to validate and add reasoning. This keeps LLM calls focused and makes mock mode realistic.

3. **Audit trail via decisions list** — Every agent emits a `Decision` record. The full `decisions` list at the end shows exactly which agents ran, in what order, and their reasoning. This is essential for supply chain compliance.

4. **Human-in-the-loop via interrupt** — Orders over threshold pause at `human_approval_node()` via `interrupt()`. The approval flows back from the API layer via `Command(resume=...)`. No threading or queues needed — the graph checkpointer handles thread safety.

5. **Pluggable data sources** — `app/data/mock_data.py` simulates POS, inventory, suppliers, and fleet. Replace functions there with real API or MCP calls; agents and graph don't change.

6. **MemorySaver checkpointer** — Each run is isolated by `thread_id`. Long-running or repeated approvals use the same thread_id to resume from the last interrupt.

## Important Files

| File | Purpose |
|------|---------|
| `app/state.py` | Pydantic schemas for every agent output + the graph state |
| `app/graph.py` | LangGraph wiring, conditional edges, human approval interrupt |
| `app/agents/*.py` | 8 agent implementations (demand, inventory, procurement, supplier, delivery, exception, evaluator) |
| `app/llm.py` | Multi-provider LLM client with structured output and mock mode |
| `app/config.py` | Environment-driven settings (provider, thresholds, API keys) |
| `app/data/mock_data.py` | Simulated POS, inventory, supplier, and delivery data |
| `app/main.py` | FastAPI service exposing /run and /approve endpoints |
| `run_demo.py` | End-to-end CLI demo with approval gate |
| `tests/test_graph.py` | Comprehensive smoke tests (40+ test cases covering all agents and edge cases) |

## Common Workflows

### Adding a New Decision Point
1. Add a new Pydantic schema in `app/state.py`
2. Create `app/agents/new_agent.py` following the 4-step pattern (proposal → fallback → LLM decide → Decision)
3. Add the node and edge in `app/graph.py` (e.g., `g.add_node("new_agent", new_agent_func)`)
4. Add a test in `tests/test_graph.py` to verify the new schema fields

### Switching LLM Providers
Set `LLM_PROVIDER` and credentials in `.env`, e.g.:
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-3-5-sonnet-20241022
```
No code changes needed — the `llm.py` module handles routing.

### Replacing Mock Data with Real APIs
In `app/data/mock_data.py`, replace `get_pos_sales()`, `get_inventory()`, `get_suppliers()`, etc. with calls to real APIs or MCP servers. Agents import from `mock_data` and don't need changes.

### Running a Single Approval Flow
```python
from app.graph import build_graph
from langgraph.types import Command
import uuid

graph = build_graph()
cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}

# First run — may interrupt at approval
result = graph.invoke({"sku": "SKU-MILK-1L"}, cfg)
if result.get("__interrupt__"):
    # Resume with approval
    result = graph.invoke(Command(resume={"approved": True, "approver": "me"}), cfg)
print(result["purchase_order"])
```

## Notes on Modifications

- **Agent logic** — Keep agents stateless; put all state in Pydantic schemas passed through the graph state.
- **New LLM-powered decisions** — Follow the 4-step pattern (deterministic → fallback → LLM → Decision); test with mock mode first.
- **Approval thresholds** — These live in `app/config.py` and are driven by env vars, not hardcoded.
- **Audit compliance** — Never lose the `decisions` list; it's the audit trail that justifies every order.
